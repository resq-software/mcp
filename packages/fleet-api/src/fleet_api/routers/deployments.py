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

"""Endpoints for dispatching drones and inspecting dispatch records."""

from fastapi import APIRouter, HTTPException, status

from fleet_api.dependencies import StoreDep
from fleet_api.models import Deployment, DeploymentRequest
from fleet_api.store import MIN_DEPLOYABLE_BATTERY, MONITORED_SECTORS

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post(
    "",
    response_model=Deployment,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch a drone to a sector",
)
def create_deployment(request: DeploymentRequest, store: StoreDep) -> Deployment:
    """Assign an available drone to the requested sector.

    Unlike a synthetic dispatcher, the assigned ``drone_id`` always names a drone
    that exists in the fleet, so callers can follow up with ``GET /drones/{id}``.

    Args:
        request: Target sector and mission priority.
        store: Injected fleet store.

    Returns:
        Deployment: The dispatch record, with a 201 response.

    A dispatched drone is engaged until its deployment reaches a terminal state,
    so two calls never return the same ``drone_id`` while both missions are live.

    Raises:
        HTTPException: 404 if the sector is not monitored; 409 if no drone is
            currently eligible to fly the mission.
    """
    if request.sector_id not in MONITORED_SECTORS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Sector {request.sector_id} is not monitored. "
                f"Known sectors: {', '.join(sorted(MONITORED_SECTORS))}"
            ),
        )

    deployment = store.dispatch(request.sector_id, request.priority)
    if deployment is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No drone is available for dispatch: every drone is already flying a "
                f"mission, inactive, or below the {MIN_DEPLOYABLE_BATTERY}% minimum "
                "battery."
            ),
        )

    return deployment


@router.get("", response_model=list[Deployment], summary="List dispatch records")
def list_deployments(store: StoreDep) -> list[Deployment]:
    """Return every recorded dispatch, newest first.

    Args:
        store: Injected fleet store.

    Returns:
        list[Deployment]: All dispatch records.
    """
    return store.list_deployments()


@router.get("/{deployment_id}", response_model=Deployment, summary="Fetch one dispatch")
def get_deployment(deployment_id: str, store: StoreDep) -> Deployment:
    """Return a single dispatch record.

    Args:
        deployment_id: The dispatch identifier.
        store: Injected fleet store.

    Returns:
        Deployment: The requested record.

    Raises:
        HTTPException: 404 if no dispatch with that identifier exists.
    """
    deployment = store.get_deployment(deployment_id)
    if deployment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )
    return deployment
