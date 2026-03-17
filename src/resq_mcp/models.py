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

"""Domain models for the ResQ MCP server.

These Pydantic models define the core data contracts for the three main subsystems:
- PDIE (Predictive Disaster Intelligence Engine)
- DTSOP (Digital Twin Simulation & Optimization Platform)
- HCE (Hybrid Coordination Engine)

All datetime fields use timezone-aware UTC timestamps for consistency across
distributed systems and audit logging.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware).

    Helper function for Pydantic Field default_factory to ensure all
    timestamps are timezone-aware and use UTC for consistency across
    distributed systems.

    Returns:
        datetime: Current time in UTC with timezone info.

    Note:
        Using timezone-aware datetimes prevents ambiguity in logs and
        ensures correct serialization across different time zones.
    """
    return datetime.now(UTC)


# --- Shared / Common Models ---


class Coordinates(BaseModel):
    """Geographic coordinates with status indicator.

    Represents a geographic point in decimal degrees (WGS84 datum)
    with an associated status flag for monitoring.

    Attributes:
        lat: Latitude in decimal degrees (-90 to +90).
        lng: Longitude in decimal degrees (-180 to +180).
        status: Current status indicator (e.g., "clear", "critical").

    Example:
        >>> coords = Coordinates(lat=37.3417, lng=-121.9751, status="clear")
        >>> print(f"Position: {coords.lat}, {coords.lng}")
    """

    lat: float
    lng: float
    status: str


class Sector(BaseModel):
    """A monitored geographic sector in the drone surveillance network.

    Sectors are predefined geographic zones monitored by the drone fleet
    for disaster detection and response coordination.

    Attributes:
        id: Unique sector identifier (e.g., "Sector-1").
        coordinates: Center point coordinates with status.
    """

    id: str
    coordinates: Coordinates


# --- Core/Legacy Models (Drone Feed) ---


class DetectedObject(BaseModel):
    """An object detected by drone sensors during surveillance.

    Represents the output of edge AI object detection running on drone
    hardware or ground processing stations.

    Attributes:
        name: Human-readable name of detected object (default: "None").
        type: Classification type (e.g., "fire", "vehicle", "person").
        confidence: Detection confidence score (0.0 to 1.0).
        description: Detailed description of the detection.
    """

    name: str = "None"
    type: str = "unknown"
    confidence: float = 0.0
    description: str = "No anomalies detected"


class DisasterScenario(BaseModel):
    """A disaster scenario template for simulation and detection.

    Defines the characteristics of a disaster type that can be detected
    by drone surveillance or used as input for digital twin simulations.

    Attributes:
        type: Disaster category (e.g., "wildfire", "flood", "earthquake").
        name: Human-readable scenario name.
        confidence: Detection confidence or scenario likelihood (0.0 to 1.0).
        description: Detailed scenario description including characteristics.
    """

    type: str
    name: str
    confidence: float
    description: str


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


# --- PDIE: Predictive Disaster Intelligence Engine ---


class VulnerabilityMap(BaseModel):
    """Static vulnerability assessment data for a geographic sector.

    Part of PDIE (Predictive Disaster Intelligence Engine) system.
    Contains precomputed risk factors, infrastructure data, and population
    metrics used for predictive disaster modeling and resource allocation.

    Attributes:
        sector_id: Sector identifier this map applies to.
        population_density: Human population density category.
        critical_infrastructure: List of critical facilities (e.g., "hospital", "power-substation").
        flood_risk: Flood vulnerability score (0.0 to 1.0).
        fire_risk: Fire vulnerability score (0.0 to 1.0).
        last_updated: UTC timestamp of last data update (auto-generated).

    Note:
        Risk scores are precomputed from historical data, terrain analysis,
        and infrastructure density. Updated periodically via GIS integration.
    """

    sector_id: str
    population_density: Literal["low", "medium", "high"]
    critical_infrastructure: list[str]
    flood_risk: float
    fire_risk: float
    last_updated: datetime = Field(default_factory=_utc_now)


class PreAlert(BaseModel):
    """Probabilistic disaster forecast from LSTM/GNN predictive models.

    Part of PDIE system. Generated by machine learning models that analyze
    weather patterns, sensor data, and historical trends to predict potential
    disasters before they occur. Enables proactive resource positioning.

    Attributes:
        alert_id: Unique alert identifier (e.g., "PRE-A1B2C3D4").
        sector_id: Target sector for the prediction.
        predicted_disaster_type: Expected disaster type (e.g., "wildfire", "flood").
        probability: Forecast confidence (0.0 to 1.0).
        forecast_horizon_hours: Time until predicted event (hours from now).
        vulnerability_context: Associated sector vulnerability data.
        generated_at: UTC timestamp of forecast generation (auto-generated).

    Example:
        >>> alert = PreAlert(
        ...     alert_id="PRE-123ABC",
        ...     sector_id="Sector-1",
        ...     predicted_disaster_type="wildfire",
        ...     probability=0.85,
        ...     forecast_horizon_hours=12,
        ...     vulnerability_context=vuln_map
        ... )
    """

    alert_id: str
    sector_id: str
    predicted_disaster_type: str
    probability: float
    forecast_horizon_hours: int
    vulnerability_context: VulnerabilityMap
    generated_at: datetime = Field(default_factory=_utc_now)


# --- DTSOP: Digital Twin Simulation & Optimization Platform ---


class SimulationRequest(BaseModel):
    """Request for high-fidelity physics simulation in digital twin.

    Part of DTSOP system. Triggers physics-based simulation in Unity/Unreal
    Engine for accurate disaster propagation modeling and strategy validation.

    Attributes:
        scenario_id: Unique scenario identifier for this simulation.
        sector_id: Geographic sector to simulate.
        disaster_type: Type of disaster to model (e.g., "flood", "wildfire").
        parameters: Simulation parameters (e.g., {"wind_speed": 15.5, "water_level": 2.3}).
        priority: Processing priority (standard queued, urgent fast-tracked).

    Note:
        Simulations run asynchronously. Monitor progress via the returned
        simulation ID and resource subscription (resq://simulations/{id}).
    """

    scenario_id: str
    sector_id: str
    disaster_type: str
    parameters: dict[str, float | str]  # e.g., wind_speed, water_level
    priority: Literal["standard", "urgent"] = "standard"


class OptimizationStrategy(BaseModel):
    """Reinforcement learning-optimized deployment and evacuation strategy.

    Part of DTSOP system. Generated by RL agents trained on thousands of
    simulated disaster scenarios to optimize resource allocation and
    evacuation routing under various constraints.

    Attributes:
        strategy_id: Unique strategy identifier (e.g., "STRAT-X1Y2Z3W4").
        related_alert_id: Pre-alert or incident ID this strategy addresses.
        recommended_deployment: Mapping of drone types to recommended counts
                                (e.g., {"surveillance": 2, "payload": 1}).
        evacuation_routes: Ordered list of recommended evacuation routes.
        estimated_success_rate: Predicted success probability (0.0 to 1.0)
                                based on simulation outcomes.
        simulation_proof_url: NeoFS/IPFS URL for simulation evidence and logs.

    Note:
        Success rate derived from Monte Carlo simulations across varying
        disaster intensities and communication scenarios.
    """

    strategy_id: str
    related_alert_id: str | None = None
    recommended_deployment: dict[str, int]  # drone_type -> count
    evacuation_routes: list[str]
    estimated_success_rate: float
    simulation_proof_url: str | None = None


# --- HCE: Hybrid Coordination Engine ---


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


class ErrorResponse(BaseModel):
    """Standard error response for failed operations.

    Used across all subsystems to provide consistent error messaging.
    Returned instead of raising exceptions for expected error conditions
    (e.g., invalid sector ID, missing data).

    Attributes:
        status: Always "error" to distinguish from success responses.
        message: Human-readable error description.

    Example:
        >>> error = ErrorResponse(message="Sector not found")
        >>> if isinstance(result, ErrorResponse):
        ...     print(f"Error: {result.message}")
    """

    status: Literal["error"] = "error"
    message: str
