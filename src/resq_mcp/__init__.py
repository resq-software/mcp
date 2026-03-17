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

from resq_mcp.core.config import Settings, settings
from resq_mcp.core.models import (
    Coordinates,
    DetectedObject,
    DisasterScenario,
    ErrorResponse,
    Sector,
)
from resq_mcp.drone.models import (
    DeploymentRequest,
    DeploymentStatus,
    NetworkStatus,
    SectorAnalysis,
    SectorStatusSummary,
    SwarmStatus,
)
from resq_mcp.drone.service import (
    get_all_sectors_status,
    get_drone_swarm_status,
    request_drone_deployment,
    scan_current_sector,
)
from resq_mcp.dtsop.models import OptimizationStrategy, SimulationRequest
from resq_mcp.dtsop.service import get_optimization_strategy, run_simulation
from resq_mcp.hce.models import IncidentReport, IncidentValidation, MissionParameters
from resq_mcp.hce.service import update_mission_params, validate_incident
from resq_mcp.pdie.models import PreAlert, VulnerabilityMap
from resq_mcp.pdie.service import get_predictive_alerts, get_vulnerability_map
from resq_mcp.server import mcp

__version__ = "2.0.0"

__all__ = [  # noqa: RUF022 - Organized by category for readability
    # Server
    "mcp",
    # Config
    "Settings",
    "settings",
    # Models - Common
    "Coordinates",
    "DetectedObject",
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
