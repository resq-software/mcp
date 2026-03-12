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

"""ResQ MCP - Model Context Protocol server for disaster response coordination.

This package provides:
- PDIE (Predictive Disaster Intelligence Engine)
- DTSOP (Digital Twin Simulation & Optimization Platform)
- HCE (Hybrid Coordination Engine)

Example:
    from resq_mcp import mcp
    mcp.run()
"""

from __future__ import annotations

from .config import Settings, settings
from .dtsop import get_optimization_strategy, run_simulation
from .hce import update_mission_params, validate_incident
from .models import (
    Coordinates,
    DeploymentRequest,
    DeploymentStatus,
    DisasterScenario,
    ErrorResponse,
    IncidentReport,
    IncidentValidation,
    MissionParameters,
    NetworkStatus,
    OptimizationStrategy,
    PreAlert,
    Sector,
    SectorAnalysis,
    SectorStatusSummary,
    SimulationRequest,
    SwarmStatus,
    VulnerabilityMap,
)
from .pdie import get_predictive_alerts, get_vulnerability_map
from .server import mcp
from .tools import (
    get_all_sectors_status,
    get_drone_swarm_status,
    request_drone_deployment,
    scan_current_sector,
)

__version__ = "2.0.0"

__all__ = [  # noqa: RUF022 - Organized by category for readability
    # Server
    "mcp",
    # Config
    "Settings",
    "settings",
    # Models - Common
    "Coordinates",
    "Sector",
    "ErrorResponse",
    # Models - Drone Feed
    "DisasterScenario",
    "SectorAnalysis",
    "SectorStatusSummary",
    "NetworkStatus",
    "SwarmStatus",
    "DeploymentRequest",
    "DeploymentStatus",
    # Models - PDIE
    "VulnerabilityMap",
    "PreAlert",
    # Models - DTSOP
    "SimulationRequest",
    "OptimizationStrategy",
    # Models - HCE
    "IncidentReport",
    "IncidentValidation",
    "MissionParameters",
    # Tools
    "scan_current_sector",
    "get_all_sectors_status",
    "get_drone_swarm_status",
    "request_drone_deployment",
    # PDIE
    "get_vulnerability_map",
    "get_predictive_alerts",
    # DTSOP
    "run_simulation",
    "get_optimization_strategy",
    # HCE
    "validate_incident",
    "update_mission_params",
]