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

"""Read-only endpoints for drone fleet composition and health."""

from fastapi import APIRouter, HTTPException, status

from fleet_api.dependencies import StoreDep
from fleet_api.models import DroneUnit, FleetStatus

router = APIRouter(tags=["drones"])


@router.get("/drones", response_model=list[DroneUnit], summary="List the fleet roster")
def list_drones(store: StoreDep) -> list[DroneUnit]:
    """Return every drone in the fleet.

    Args:
        store: Injected fleet store.

    Returns:
        list[DroneUnit]: All drones, ordered by identifier.
    """
    return store.list_drones()


@router.get("/drones/{drone_id}", response_model=DroneUnit, summary="Fetch one drone")
def get_drone(drone_id: str, store: StoreDep) -> DroneUnit:
    """Return a single drone by identifier.

    Args:
        drone_id: The drone to fetch.
        store: Injected fleet store.

    Returns:
        DroneUnit: The requested drone.

    Raises:
        HTTPException: 404 if no drone with that identifier exists.
    """
    drone = store.get_drone(drone_id)
    if drone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drone {drone_id} is not in the fleet",
        )
    return drone


@router.get("/fleet/status", response_model=FleetStatus, summary="Aggregate fleet health")
def get_fleet_status(store: StoreDep) -> FleetStatus:
    """Return an aggregate health snapshot for the whole fleet.

    Derived from the same records ``GET /drones`` serves, so the two can never
    report a different fleet.

    Args:
        store: Injected fleet store.

    Returns:
        FleetStatus: Totals, active count, mean battery, and mesh health.
    """
    return store.fleet_status()
