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

"""Drone feed tools for the ResQ MCP server.

This module provides simulated drone feed functionality for development and testing.
It generates pseudo-random telemetry and analysis data for drone network sectors.

The simulation includes:
- 4 monitored sectors with predefined coordinates
- Random disaster scenario detection (fire, flood, medical, debris)
- Swarm status with variable battery and connectivity
- Drone deployment request handling
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Final

from .models import (
    Coordinates,
    DeploymentStatus,
    DisasterScenario,
    ErrorResponse,
    NetworkStatus,
    SectorAnalysis,
    SectorStatusSummary,
    SwarmStatus,
)

# Simulated drone feed database
DRONE_SECTORS: Final[dict[str, dict[str, object]]] = {
    "Sector-1": {"lat": 37.3417, "lng": -121.9751, "status": "clear"},
    "Sector-2": {"lat": 37.3425, "lng": -121.9760, "status": "clear"},
    "Sector-3": {"lat": 37.3410, "lng": -121.9740, "status": "clear"},
    "Sector-4": {"lat": 37.3430, "lng": -121.9770, "status": "clear"},
}

# Disaster scenarios for simulation
DISASTER_SCENARIOS: Final[list[DisasterScenario]] = [
    DisasterScenario(
        type="wildfire",
        name="Active Wildfire",
        confidence=0.98,
        description="Large fire detected with smoke plume",
    ),
    DisasterScenario(
        type="flood",
        name="Flash Flood",
        confidence=0.92,
        description="Water overflow in low-lying area",
    ),
    DisasterScenario(
        type="accident",
        name="Multi-Vehicle Collision",
        confidence=0.88,
        description="Major traffic incident detected",
    ),
    DisasterScenario(
        type="mass_casualty",
        name="Mass Casualty Event",
        confidence=0.85,
        description="Large gathering with emergency response needed",
    ),
]

# Probability of detecting a disaster in simulation
_DISASTER_DETECTION_PROBABILITY: Final[float] = 0.3


def scan_current_sector(sector_id: str = "Sector-1") -> SectorAnalysis | ErrorResponse:
    """Scan a specific sector for anomalies using simulated drone sensors.

    Simulates drone-based surveillance with probabilistic disaster detection.
    In production, this would integrate with actual drone telemetry and
    edge AI processing results from the MCP drone feed server.

    Detection Logic:
        - 30% probability of detecting a disaster scenario per scan
        - Randomly selects from predefined disaster templates
        - Generates NeoFS evidence URL for blockchain submission
        - Returns "clear" status if no anomalies detected

    Args:
        sector_id: The sector to scan ("Sector-1" through "Sector-4").
                   Default is "Sector-1".

    Returns:
        SectorAnalysis: Complete scan results with detection data and
                        recommended actions if sector exists.
        ErrorResponse: Error message if sector_id is invalid.

    Example:
        >>> result = scan_current_sector("Sector-2")
        >>> if isinstance(result, SectorAnalysis):
        ...     if result.status == "CRITICAL_ALERT":
        ...         print(f"Alert: {result.detected_object}")
        ...         print(f"Action: {result.recommended_action}")

    Note:
        This is a simulation function. Production deployment would replace
        random detection with actual ML model inference on drone imagery.
    """
    if sector_id not in DRONE_SECTORS:
        return ErrorResponse(message=f"Sector {sector_id} not found")

    raw_coords = DRONE_SECTORS[sector_id]
    coords = Coordinates(
        lat=float(raw_coords["lat"]),  # type: ignore[arg-type]
        lng=float(raw_coords["lng"]),  # type: ignore[arg-type]
        status=str(raw_coords["status"]),
    )

    # Random chance of detecting a disaster
    if random.random() < _DISASTER_DETECTION_PROBABILITY:  # noqa: S311
        disaster = random.choice(DISASTER_SCENARIOS)  # noqa: S311
        timestamp = datetime.now(UTC).timestamp()
        return SectorAnalysis(
            sector_id=sector_id,
            status="CRITICAL_ALERT",
            detected_object=disaster.name,
            disaster_type=disaster.type,
            confidence=disaster.confidence,
            description=disaster.description,
            coordinates=coords,
            video_proof_url=f"neofs://neoguard/incident_{sector_id}_{timestamp}.mp4",
            recommended_action="IMMEDIATE_REPORT_TO_BLOCKCHAIN",
        )

    return SectorAnalysis(
        sector_id=sector_id,
        status="clear",
        detected_object="None",
        confidence=0.0,
        description="No anomalies detected",
        coordinates=coords,
        recommended_action="CONTINUE_MONITORING",
    )


def get_all_sectors_status() -> NetworkStatus:
    """Get the status of all monitored sectors in the surveillance network.

    Aggregates scan results across all configured sectors to provide
    network-wide situational awareness for operator dashboards.

    Returns:
        NetworkStatus: Complete network status including:
            - Total sector count
            - Per-sector status summaries (detected objects, confidence)
            - Critical alert count for priority filtering
            - Timestamp of status generation

    Example:
        >>> status = get_all_sectors_status()
        >>> print(f"Network: {status.total_sectors} sectors")
        >>> print(f"Critical Alerts: {status.critical_alerts}")
        >>> for sector_id, summary in status.sectors.items():
        ...     if summary.status == "CRITICAL_ALERT":
        ...         print(f"{sector_id}: {summary.detected_object}")

    Note:
        Calls scan_current_sector() for each sector, so inherits its
        simulation behavior (random detection).
    """
    sectors_map: dict[str, SectorStatusSummary] = {}

    for sector_id in DRONE_SECTORS:
        scan_result = scan_current_sector(sector_id)

        if isinstance(scan_result, ErrorResponse):
            continue

        sectors_map[sector_id] = SectorStatusSummary(
            status=scan_result.status,
            detected_object=scan_result.detected_object,
            confidence=scan_result.confidence,
        )

    critical_count = sum(1 for s in sectors_map.values() if s.status == "CRITICAL_ALERT")

    return NetworkStatus(
        total_sectors=len(DRONE_SECTORS),
        sectors=sectors_map,
        critical_alerts=critical_count,
    )


def get_drone_swarm_status() -> SwarmStatus:
    """Get the overall operational status of the drone swarm.

    Provides fleet-wide health metrics for monitoring drone readiness
    and availability. Used by operators to assess deployment capacity.

    Simulation Behavior:
        - Total drones: Fixed at 3 for development
        - Active drones: Random 2-3 (some may be charging/maintenance)
        - Average battery: Random 60-100% (simulated degradation)
        - Network status: Always "operational" in dev mode

    Returns:
        SwarmStatus: Fleet metrics including:
            - Total and active drone counts
            - Fleet-wide average battery percentage
            - Network connectivity status
            - Last sync timestamp (auto-generated)

    Example:
        >>> swarm = get_drone_swarm_status()
        >>> if swarm.average_battery < 30:
        ...     print("WARNING: Low fleet battery")
        >>> print(f"{swarm.active_drones}/{swarm.total_drones} drones active")

    Note:
        Production would aggregate real telemetry from the MCP drone feed
        server, reporting actual battery, GPS lock, and link quality.
    """
    return SwarmStatus(
        total_drones=3,
        active_drones=random.randint(2, 3),  # noqa: S311
        average_battery=random.randint(60, 100),  # noqa: S311
        network_status="operational",
    )


def request_drone_deployment(
    sector_id: str,
    priority: str = "high",
) -> DeploymentStatus | ErrorResponse:
    """Request deployment of a drone to a specific sector.

    Simulates drone dispatch request handling with immediate assignment.
    In production, this would interface with the drone control module
    and mission planning system to allocate resources.

    Simulation Behavior:
        - Assigns random drone unit (UNIT-001 through UNIT-003)
        - Generates random ETA (30-120 seconds)
        - Always returns "deployed" status if sector valid

    Args:
        sector_id: The target sector for deployment (e.g., "Sector-1").
        priority: Deployment urgency level. Higher priority missions
                  preempt lower priority tasks. Valid values:
                  - "low": Routine surveillance
                  - "medium": Follow-up investigation
                  - "high" (default): Active incident response
                  - "critical": Immediate life-threatening situation

    Returns:
        DeploymentStatus: Confirmation with assigned drone and ETA if
                          sector is valid.
        ErrorResponse: Error message if sector_id is invalid.

    Example:
        >>> status = request_drone_deployment("Sector-3", priority="critical")
        >>> if isinstance(status, DeploymentStatus):
        ...     print(f"Drone {status.drone_id} dispatched")
        ...     print(f"ETA: {status.eta_seconds} seconds")

    Note:
        Production would check drone availability, battery levels, and
        weather conditions before confirming deployment.
    """
    if sector_id not in DRONE_SECTORS:
        return ErrorResponse(message=f"Sector {sector_id} not found")

    return DeploymentStatus(
        status="deployed",
        sector_id=sector_id,
        priority=priority,
        drone_id=f"UNIT-{random.randint(1, 3):03d}",  # noqa: S311
        eta_seconds=random.randint(30, 120),  # noqa: S311
    )