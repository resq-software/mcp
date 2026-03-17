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

"""Drone feed domain models for the ResQ MCP server."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from resq_mcp.core.models import Coordinates, _utc_now


class SectorAnalysis(BaseModel):
    """Complete analysis result from a sector surveillance scan.

    Contains all detection data, evidence links, and recommended actions
    from a drone sector scan. Used for incident reporting and blockchain
    evidence submission.

    Attributes:
        sector_id: Identifier of the scanned sector.
        timestamp: UTC timestamp of the analysis (auto-generated).
        status: Overall status (e.g., "clear", "CRITICAL_ALERT").
        detected_object: Primary object or hazard detected.
        disaster_type: Classified disaster type if applicable.
        confidence: Detection confidence score (0.0 to 1.0).
        description: Detailed analysis description.
        coordinates: Geographic coordinates of the detection.
        video_proof_url: NeoFS/IPFS URL for video evidence.
        recommended_action: Suggested next action (e.g., "IMMEDIATE_REPORT_TO_BLOCKCHAIN").
    """

    sector_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    status: str
    detected_object: str
    disaster_type: str | None = None
    confidence: float
    description: str
    coordinates: Coordinates
    video_proof_url: str | None = None
    recommended_action: str


class SectorStatusSummary(BaseModel):
    """Condensed status summary for network-wide sector monitoring.

    Lightweight representation used in network status dashboards and
    overview displays. Excludes detailed evidence and coordinates.

    Attributes:
        status: Current sector status indicator.
        detected_object: Primary detected object or "None".
        confidence: Overall confidence score for the status.
    """

    status: str
    detected_object: str
    confidence: float


class NetworkStatus(BaseModel):
    """Aggregate status of the entire drone surveillance network.

    Provides a network-wide view of all monitored sectors and critical
    alert counts for operator dashboards and system health monitoring.

    Attributes:
        timestamp: UTC timestamp of the status snapshot (auto-generated).
        total_sectors: Total number of monitored sectors.
        sectors: Mapping of sector IDs to their status summaries.
        critical_alerts: Count of sectors with critical alerts active.
    """

    timestamp: datetime = Field(default_factory=_utc_now)
    total_sectors: int
    sectors: dict[str, SectorStatusSummary]
    critical_alerts: int


class SwarmStatus(BaseModel):
    """Real-time operational status of the drone swarm.

    Aggregates health metrics across all drones in the fleet including
    battery levels, connectivity status, and deployment state.

    Attributes:
        timestamp: UTC timestamp of the status snapshot (auto-generated).
        total_drones: Total number of drones in the fleet.
        active_drones: Number of drones currently deployed and operational.
        average_battery: Fleet-wide average battery percentage (0-100).
        network_status: Overall network health (e.g., "operational", "degraded").
        last_sync: UTC timestamp of last successful sync with ground station.
    """

    timestamp: datetime = Field(default_factory=_utc_now)
    total_drones: int
    active_drones: int
    average_battery: int
    network_status: str
    last_sync: datetime = Field(default_factory=_utc_now)


class DeploymentRequest(BaseModel):
    """Request for immediate drone deployment to a specific sector.

    Used by operators or automated systems to request drone dispatch
    to sectors requiring surveillance or emergency response.

    Attributes:
        sector_id: Target sector identifier for deployment.
        priority: Deployment urgency level (low/medium/high/critical).
                  Higher priority requests preempt lower priority missions.
    """

    sector_id: str
    priority: Literal["low", "medium", "high", "critical"] = "high"


class DeploymentStatus(BaseModel):
    """Response status for a drone deployment request.

    Provides confirmation and tracking information for a deployment request
    including assigned drone and estimated arrival time.

    Attributes:
        status: Deployment state (e.g., "deployed", "en_route", "completed").
        sector_id: Target sector identifier.
        priority: Assigned priority level.
        drone_id: Identifier of the assigned drone unit.
        eta_seconds: Estimated time to arrival in seconds.
        timestamp: UTC timestamp of the status update (auto-generated).
    """

    status: str
    sector_id: str
    priority: str
    drone_id: str
    eta_seconds: int
    timestamp: datetime = Field(default_factory=_utc_now)
