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

"""Request and response models for the fleet API.

These are the wire contract. They are intentionally close to the drone models in
``resq-mcp`` so that package can deserialise responses directly once it is
refactored to call this service over HTTP.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

DroneRole = Literal["Surveillance", "Payload", "Relay"]
DeploymentPriority = Literal["low", "medium", "high", "critical"]


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime.

    Used as a Pydantic ``default_factory`` so each model instance gets its own
    timestamp, rather than freezing one value at import time.

    Returns:
        datetime: The current time in UTC.
    """
    return datetime.now(UTC)


class DroneUnit(BaseModel):
    """Identity and standing assignment of a single drone.

    Describes fleet composition — the facts about a drone that do not change
    between telemetry samples.

    Attributes:
        drone_id: Unique drone identifier (e.g. "DRONE-Alpha").
        role: Airframe capability class.
        home_sector: Sector the drone is normally stationed in.
        battery_percent: Last reported battery charge, 0-100.
        is_active: Whether the drone is currently deployed and operational.
    """

    drone_id: str = Field(..., min_length=1, max_length=64)
    role: DroneRole
    home_sector: str = Field(..., min_length=1, max_length=64)
    battery_percent: int = Field(..., ge=0, le=100)
    is_active: bool = True


class FleetStatus(BaseModel):
    """Aggregate health snapshot across the whole fleet.

    Every field is computed from the drone records held by the store, so this
    can never disagree with what ``GET /drones`` returns.

    Attributes:
        timestamp: When the snapshot was taken.
        total_drones: Number of drones in the fleet.
        active_drones: How many of them are currently operational.
        average_battery: Mean battery charge across the fleet, 0-100.
        network_status: Overall mesh health.
    """

    timestamp: datetime = Field(default_factory=_utc_now)
    total_drones: int = Field(..., ge=0)
    active_drones: int = Field(..., ge=0)
    average_battery: int = Field(..., ge=0, le=100)
    network_status: Literal["operational", "degraded", "offline"]


class DeploymentRequest(BaseModel):
    """Client request to dispatch a drone to a sector.

    Attributes:
        sector_id: Target sector for the deployment.
        priority: Urgency of the mission; higher priorities preempt lower ones.
    """

    sector_id: str = Field(..., min_length=1, max_length=64)
    priority: DeploymentPriority = "high"


class Deployment(BaseModel):
    """A dispatch record created in response to a deployment request.

    Attributes:
        deployment_id: Unique identifier for this dispatch.
        drone_id: The drone assigned to the mission.
        sector_id: Target sector.
        priority: Urgency the mission was filed under.
        status: Lifecycle state of the dispatch.
        eta_seconds: Estimated seconds until the drone reaches the sector.
        created_at: When the dispatch was recorded.
    """

    deployment_id: str
    drone_id: str
    sector_id: str
    priority: DeploymentPriority
    status: Literal["deployed", "en_route", "completed", "cancelled"] = "deployed"
    eta_seconds: int = Field(..., gt=0)
    created_at: datetime = Field(default_factory=_utc_now)


class HealthResponse(BaseModel):
    """Liveness probe payload.

    Attributes:
        status: Always "ok" when the process can serve requests.
        service: Service name, useful when several APIs sit behind one gateway.
        version: Running version of the service.
    """

    status: Literal["ok"] = "ok"
    service: str
    version: str
