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

"""HCE domain models for the ResQ MCP server."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

from resq_mcp.core.models import _utc_now

if TYPE_CHECKING:
    from datetime import datetime


class IncidentReport(BaseModel):
    """Initial incident report from Edge AI, human observers, or sensors.

    Part of HCE (Hybrid Coordination Engine) system. Represents unvalidated
    incident detection requiring cross-reference and validation before
    triggering full response protocols.

    Attributes:
        incident_id: Unique incident identifier.
        source: Detection source (edge_ai=onboard processing, human_report=operator,
                sensor_network=ground sensors).
        sector_id: Geographic sector of the incident.
        detected_type: Incident classification (e.g., "fire", "collision", "flooding").
        confidence: Detection confidence from source (0.0 to 1.0).
        evidence_url: Optional URL to evidence (video, photos) on IPFS/NeoFS.
        timestamp: UTC timestamp of detection (auto-generated).

    Note:
        High-confidence reports (>0.85) may auto-confirm. Lower confidence
        reports cross-referenced with PDIE predictions and other sources.
    """

    incident_id: str
    source: Literal["edge_ai", "human_report", "sensor_network"]
    sector_id: str
    detected_type: str
    confidence: float
    evidence_url: str | None = None
    timestamp: datetime = Field(default_factory=_utc_now)


class IncidentValidation(BaseModel):
    """Validation result after cross-referencing an incident report.

    Part of HCE system. Produced after comparing incident reports against
    PDIE predictions, sensor networks, and historical data to confirm
    authenticity and trigger appropriate response protocols.

    Attributes:
        incident_id: ID of the incident being validated.
        is_confirmed: Whether the incident is confirmed as genuine.
        validation_source: System or agent that performed validation
                           (e.g., "SpoonOS-HCE-Validator", "Human-Operator").
        correlated_pre_alert_id: Related PDIE pre-alert if correlation found.
        notes: Detailed validation reasoning and cross-reference results.

    Example:
        >>> validation = IncidentValidation(
        ...     incident_id="INC-123",
        ...     is_confirmed=True,
        ...     validation_source="SpoonOS-HCE-Validator",
        ...     notes="Confirmed via PDIE correlation and sensor data"
        ... )
    """

    incident_id: str
    is_confirmed: bool
    validation_source: str  # e.g., "SpoonOS-Validator"
    correlated_pre_alert_id: str | None = None
    notes: str


class MissionParameters(BaseModel):
    """Authorized mission parameters pushed to drone via HCE.

    Part of HCE system. Defines the authorized action space and risk
    parameters for autonomous drone operations. Includes blockchain hash
    for immutable audit trail of mission authorizations.

    Attributes:
        mission_id: Unique mission identifier (e.g., "MISS-A1B2C3D4").
        target_sector: Assigned operational sector.
        authorized_actions: List of permitted autonomous actions
                           (e.g., ["autonomous_flight", "payload_release_authorized"]).
        risk_tolerance: Maximum acceptable risk level (0.0 to 1.0).
                        Lower values restrict aggressive maneuvers.
        strategy_hash: Blockchain transaction hash linking to strategy record
                       for immutable audit trail (format: "0xHEXDIGITS").
        timestamp: UTC timestamp of parameter push (auto-generated).

    Security Note:
        Authorized actions are validated against drone firmware capabilities.
        Unauthorized actions are rejected by ResQ-OS security layer.
    """

    mission_id: str
    target_sector: str
    authorized_actions: list[str]
    risk_tolerance: float
    strategy_hash: str  # blockchain link
    timestamp: datetime = Field(default_factory=_utc_now)
