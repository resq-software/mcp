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

"""Tests for the drone and fleet-status endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from fleet_api.store import FleetStore


class TestHealth:
    def test_health_reports_ok(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "fleet-api"


class TestListDrones:
    def test_returns_the_seeded_fleet(self, client: TestClient) -> None:
        response = client.get("/drones")

        assert response.status_code == 200
        ids = [drone["drone_id"] for drone in response.json()]
        assert ids == ["DRONE-Alpha", "DRONE-Beta", "DRONE-Gamma"]

    def test_every_drone_carries_the_full_contract(self, client: TestClient) -> None:
        response = client.get("/drones")

        for drone in response.json():
            assert set(drone) == {
                "drone_id",
                "role",
                "home_sector",
                "battery_percent",
                "is_active",
            }


class TestGetDrone:
    def test_known_drone_returns_200(self, client: TestClient) -> None:
        response = client.get("/drones/DRONE-Alpha")

        assert response.status_code == 200
        assert response.json()["role"] == "Surveillance"
        assert response.json()["home_sector"] == "Sector-4"

    def test_unknown_drone_returns_404_with_guidance(self, client: TestClient) -> None:
        response = client.get("/drones/DRONE-Nope")

        assert response.status_code == 404
        assert "not in the fleet" in response.json()["detail"]

    def test_lookup_is_case_sensitive(self, client: TestClient) -> None:
        """Identifiers are exact; a lowercase variant is a different drone."""
        assert client.get("/drones/drone-alpha").status_code == 404


class TestFleetStatus:
    def test_totals_match_the_roster(self, client: TestClient) -> None:
        roster = client.get("/drones").json()
        status_body = client.get("/fleet/status").json()

        assert status_body["total_drones"] == len(roster)

    def test_active_never_exceeds_total(self, client: TestClient) -> None:
        body = client.get("/fleet/status").json()

        assert body["active_drones"] <= body["total_drones"]

    def test_average_battery_is_the_mean_of_the_roster(self, client: TestClient) -> None:
        roster = client.get("/drones").json()
        expected = sum(drone["battery_percent"] for drone in roster) // len(roster)

        assert client.get("/fleet/status").json()["average_battery"] == expected

    def test_deactivating_a_drone_lowers_the_active_count(
        self, client: TestClient, store: FleetStore
    ) -> None:
        """The aggregate is computed live, not cached at seed time."""
        before = client.get("/fleet/status").json()["active_drones"]

        drone = store.get_drone("DRONE-Beta")
        assert drone is not None
        drone.is_active = False

        after = client.get("/fleet/status").json()["active_drones"]
        assert after == before - 1

    def test_fleet_with_no_active_drones_is_degraded(
        self, client: TestClient, store: FleetStore
    ) -> None:
        for drone in store.list_drones():
            drone.is_active = False

        assert client.get("/fleet/status").json()["network_status"] == "degraded"
