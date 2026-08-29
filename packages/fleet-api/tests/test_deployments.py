# Copyright 2026 ResQ
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the deployment endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from fleet_api.store import FleetStore


class TestCreateDeployment:
    def test_dispatch_returns_201_and_a_record(self, client: TestClient) -> None:
        response = client.post("/deployments", json={"sector_id": "Sector-2"})

        assert response.status_code == 201
        body = response.json()
        assert body["deployment_id"].startswith("DEP-")
        assert body["sector_id"] == "Sector-2"
        assert body["status"] == "deployed"

    def test_assigned_drone_actually_exists_in_the_fleet(self, client: TestClient) -> None:
        """Regression: dispatch must not invent drone IDs the fleet has never heard of."""
        assigned = client.post("/deployments", json={"sector_id": "Sector-2"}).json()["drone_id"]

        assert client.get(f"/drones/{assigned}").status_code == 200

    def test_prefers_a_drone_stationed_in_the_target_sector(self, client: TestClient) -> None:
        body = client.post("/deployments", json={"sector_id": "Sector-2"}).json()

        assert body["drone_id"] == "DRONE-Beta"
        assert body["eta_seconds"] == 30

    def test_falls_back_to_the_best_charged_drone_elsewhere(self, client: TestClient) -> None:
        """Sector-1 hosts no drone, so the fullest battery wins and ETA is longer."""
        body = client.post("/deployments", json={"sector_id": "Sector-1"}).json()

        assert body["drone_id"] == "DRONE-Gamma"
        assert body["eta_seconds"] == 90

    def test_priority_defaults_to_high(self, client: TestClient) -> None:
        body = client.post("/deployments", json={"sector_id": "Sector-3"}).json()

        assert body["priority"] == "high"

    def test_explicit_priority_is_honoured(self, client: TestClient) -> None:
        body = client.post(
            "/deployments", json={"sector_id": "Sector-3", "priority": "critical"}
        ).json()

        assert body["priority"] == "critical"

    def test_unmonitored_sector_returns_404(self, client: TestClient) -> None:
        response = client.post("/deployments", json={"sector_id": "Sector-99"})

        assert response.status_code == 404
        assert "not monitored" in response.json()["detail"]

    def test_invalid_priority_returns_422(self, client: TestClient) -> None:
        """Pydantic rejects values outside the Literal before the handler runs."""
        response = client.post(
            "/deployments", json={"sector_id": "Sector-1", "priority": "extremely-urgent"}
        )

        assert response.status_code == 422

    def test_missing_sector_returns_422(self, client: TestClient) -> None:
        assert client.post("/deployments", json={}).status_code == 422

    def test_no_eligible_drone_returns_409(self, client: TestClient, store: FleetStore) -> None:
        for drone in store.list_drones():
            store.set_active(drone.drone_id, False)

        response = client.post("/deployments", json={"sector_id": "Sector-1"})

        assert response.status_code == 409
        assert "No drone is available" in response.json()["detail"]

    def test_flat_battery_drones_are_not_dispatched(
        self, client: TestClient, store: FleetStore
    ) -> None:
        for drone in store.list_drones():
            store.set_battery(drone.drone_id, 5)

        assert client.post("/deployments", json={"sector_id": "Sector-1"}).status_code == 409

    def test_two_dispatches_use_different_drones(self, client: TestClient) -> None:
        """A drone flying a mission must not be handed out again."""
        first = client.post("/deployments", json={"sector_id": "Sector-1"}).json()
        second = client.post("/deployments", json={"sector_id": "Sector-1"}).json()

        assert first["drone_id"] != second["drone_id"]

    def test_fleet_is_exhausted_once_every_drone_is_engaged(
        self, client: TestClient, store: FleetStore
    ) -> None:
        """The 409 is reachable through the API, not only by editing the store."""
        for _ in range(len(store.list_drones())):
            assert client.post("/deployments", json={"sector_id": "Sector-1"}).status_code == 201

        response = client.post("/deployments", json={"sector_id": "Sector-1"})

        assert response.status_code == 409
        assert "already flying a mission" in response.json()["detail"]

    def test_completing_a_mission_frees_its_drone(
        self, client: TestClient, store: FleetStore
    ) -> None:
        """Engagement is derived from deployment status, not a permanent flag."""
        first = client.post("/deployments", json={"sector_id": "Sector-1"}).json()
        for _ in range(len(store.list_drones()) - 1):
            client.post("/deployments", json={"sector_id": "Sector-1"})
        assert client.post("/deployments", json={"sector_id": "Sector-1"}).status_code == 409

        assert store.complete_deployment(first["deployment_id"]) is not None

        reused = client.post("/deployments", json={"sector_id": "Sector-1"})
        assert reused.status_code == 201
        assert reused.json()["drone_id"] == first["drone_id"]


class TestCompleteDeployment:
    def test_completing_an_unknown_deployment_returns_none(self, store: FleetStore) -> None:
        assert store.complete_deployment("DEP-NOPE") is None


class TestStoreEncapsulation:
    def test_reads_return_copies_not_live_records(self, store: FleetStore) -> None:
        """Mutating a returned drone must not reach into the store.

        Guards the regression this PR fixed: reads used to hand out the stored
        object, so a caller could corrupt fleet state outside the lock.
        """
        handed_out = store.get_drone("DRONE-Alpha")
        assert handed_out is not None
        handed_out.battery_percent = 1
        handed_out.is_active = False

        stored = store.get_drone("DRONE-Alpha")
        assert stored is not None
        assert stored.battery_percent == 78
        assert stored.is_active is True

    def test_list_drones_returns_copies(self, store: FleetStore) -> None:
        for drone in store.list_drones():
            drone.battery_percent = 1

        assert all(unit.battery_percent != 1 for unit in store.list_drones())


class TestReadDeployments:
    def test_created_deployment_is_retrievable(self, client: TestClient) -> None:
        created = client.post("/deployments", json={"sector_id": "Sector-4"}).json()

        response = client.get(f"/deployments/{created['deployment_id']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_unknown_deployment_returns_404(self, client: TestClient) -> None:
        response = client.get("/deployments/DEP-NOTREAL")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_list_starts_empty(self, client: TestClient) -> None:
        assert client.get("/deployments").json() == []

    def test_list_accumulates_dispatches(self, client: TestClient) -> None:
        client.post("/deployments", json={"sector_id": "Sector-1"})
        client.post("/deployments", json={"sector_id": "Sector-2"})

        assert len(client.get("/deployments").json()) == 2

    def test_deployments_do_not_leak_between_tests(self, client: TestClient) -> None:
        """Paired with the previous test: a fresh store means a fresh list."""
        assert client.get("/deployments").json() == []
