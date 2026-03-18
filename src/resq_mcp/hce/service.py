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

"""HCE - Hybrid Coordination Engine.

This module provides incident validation and mission parameter management:
- Cross-reference Edge AI reports with other data sources
- Push authorized actions and risk parameters to drones
- Generate blockchain-linked strategy hashes for audit trails

The current implementation is stubbed for development and returns simulated data.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import TYPE_CHECKING, Final

from resq_mcp.hce.models import IncidentReport, IncidentValidation, MissionParameters

if TYPE_CHECKING:
    from resq_mcp.core.models import ErrorResponse

# Confidence threshold for auto-confirmation
_AUTO_CONFIRM_THRESHOLD: Final[float] = 0.85


def validate_incident(report: IncidentReport) -> IncidentValidation:
    """Cross-reference and validate an incident report from Edge AI or other sources.

    Part of HCE (Hybrid Coordination Engine) system. Prevents false positives
    by validating reports against multiple data sources before triggering
    full response protocols.

    Validation Process:
        1. Check report confidence level
           - If confidence > 0.85: Auto-confirm (high-quality detection)
           - If confidence <= 0.85: Cross-reference required
        2. Cross-reference with (production):
           - PDIE pre-alerts (was disaster predicted?)
           - Other sector scans (spatial correlation)
           - Historical incident patterns
           - Ground sensor networks
        3. Generate validation result with reasoning

    Auto-Confirmation Threshold:
        Reports with confidence > 0.85 are auto-confirmed because:
        - High-quality edge AI models (>95% precision on test set)
        - Multi-sensor fusion (visual + thermal + LiDAR)
        - Onboard confidence calibration

    Args:
        report: Incident report containing:
            - incident_id: Unique identifier
            - source: Detection origin (edge_ai/human_report/sensor_network)
            - sector_id: Geographic location
            - detected_type: Incident classification
            - confidence: Detection confidence (0.0-1.0)
            - evidence_url: Optional IPFS/NeoFS evidence link

    Returns:
        IncidentValidation: Validation result with:
            - incident_id: Original incident ID
            - is_confirmed: True if validated, False if rejected
            - validation_source: System that performed validation
            - notes: Detailed reasoning for decision

    Example:
        >>> from resq_mcp.hce.models import IncidentReport
        >>> report = IncidentReport(
        ...     incident_id="INC-123",
        ...     source="edge_ai",
        ...     sector_id="Sector-1",
        ...     detected_type="wildfire",
        ...     confidence=0.92,
        ...     evidence_url="neofs://evidence/fire_123.mp4"
        ... )
        >>> validation = validate_incident(report)
        >>> if validation.is_confirmed:
        ...     print("Incident confirmed - trigger response")

    Note:
        Current implementation uses simple threshold logic. Production
        would integrate with PDIE correlation engine and multi-source fusion.
    """
    is_valid = report.confidence > _AUTO_CONFIRM_THRESHOLD

    return IncidentValidation(
        incident_id=report.incident_id,
        is_confirmed=is_valid,
        validation_source="SpoonOS-HCE-Validator",
        notes=f"Validation logic applied. Edge confidence: {report.confidence}",
    )


def update_mission_params(
    drone_id: str,
    strategy_id: str,
    is_urgent: bool = False,
) -> MissionParameters | ErrorResponse:
    """Push new authorized mission parameters to a specific drone.

    Part of HCE system. Defines the authorized action space and risk
    parameters for autonomous drone operations following strategy approval.

    Security Model:
        - Each mission linked to blockchain strategy record (immutable audit)
        - Authorized actions validated by ResQ-OS security layer on drone
        - Risk tolerance enforced by flight controller firmware
        - Unauthorized actions rejected before execution

    Mission Parameters Include:
        - Authorized actions: What the drone is permitted to do autonomously
          (e.g., "autonomous_flight", "payload_release_authorized")
        - Risk tolerance: Maximum acceptable risk (0.0-1.0)
          - 0.9 = Urgent missions (aggressive routing, higher speeds)
          - 0.5 = Standard missions (conservative, safety-first)
        - Strategy hash: Blockchain transaction linking to strategy record
          (format: "0x" + SHA256 hex digest)

    Args:
        drone_id: Target drone identifier (e.g., "DRONE-Alpha").
                  Used in production to route parameters to specific unit.
        strategy_id: Approved strategy identifier from DTSOP (e.g., "STRAT-X1Y2Z3").
                     Used to generate blockchain hash and determine risk level.

    Returns:
        MissionParameters: Complete parameter set with:
            - mission_id: Unique mission identifier
            - target_sector: Assigned operational area
            - authorized_actions: List of permitted autonomous actions
            - risk_tolerance: Risk threshold (0.0-1.0)
            - strategy_hash: Blockchain link (0xHEXDIGITS)
        ErrorResponse: Error if drone unavailable or strategy invalid (future).

    Example:
        >>> params = update_mission_params(
        ...     drone_id="DRONE-Alpha",
        ...     strategy_id="STRAT-URGENT-FIRE"
        ... )
        >>> if isinstance(params, MissionParameters):
        ...     print(f"Mission: {params.mission_id}")
        ...     print(f"Actions: {params.authorized_actions}")
        ...     print(f"Risk: {params.risk_tolerance}")
        ...     print(f"Blockchain: {params.strategy_hash}")

    Blockchain Integration:
        Strategy hash links to Neo N3 transaction containing:
        - Strategy JSON (deployment plan, routes, success rate)
        - Simulation proof CID (IPFS/NeoFS evidence)
        - Timestamp and approving authority
        - Provides immutable audit trail for post-incident review

    Note:
        Current implementation generates mock blockchain hash. Production
        would submit actual transaction to Neo N3 testnet/mainnet.
    """
    del drone_id  # Unused in stub - would be used to target specific drone

    mission_id_raw = uuid.uuid4().hex[:8].upper()
    # Hash is deterministic given (strategy_id, mission_id) — reproducible for audit lookups.
    # Previously included datetime.now() which made the hash non-deterministic and
    # impossible to verify against any real blockchain record.
    strategy_hash = hashlib.sha256(
        f"{strategy_id}:{mission_id_raw}".encode()
    ).hexdigest()

    # Risk tolerance is determined by the explicit is_urgent flag, not the
    # strategy_id string.  The previous substring check ("URGENT" in strategy_id)
    # allowed callers to inject high-risk tolerance via a crafted strategy ID.
    risk_tolerance = 0.9 if is_urgent else 0.5

    return MissionParameters(
        mission_id=f"MISS-{mission_id_raw}",
        target_sector="Dynamic-Assigned",
        authorized_actions=["autonomous_flight", "payload_release_authorized"],
        risk_tolerance=risk_tolerance,
        strategy_hash=f"0x{strategy_hash}",
    )
