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

"""MCP tool wrappers for DTSOP domain."""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here
# because FastMCP/Pydantic needs to resolve the type annotations at runtime
# for tool parameter validation. Using PEP 563 postponed annotations causes
# NameError when FastMCP tries to evaluate the forward references.

import logging

from fastmcp import Context

from resq_mcp.dtsop.models import OptimizationStrategy, SimulationRequest
from resq_mcp.dtsop.service import get_optimization_strategy
from resq_mcp.dtsop.service import run_simulation as trigger_sim
from resq_mcp.server import mcp, simulations

logger = logging.getLogger("resq-mcp")


@mcp.tool()
async def run_simulation(request: SimulationRequest, ctx: Context | None = None) -> str:
    """Trigger a Digital Twin physics simulation for disaster scenario modeling.

    Queues a high-fidelity simulation job and returns immediately with a
    job ID. Clients should subscribe to the simulation resource URI for
    real-time progress updates and result notification.

    Workflow:
        1. Validate simulation request parameters
        2. Generate unique simulation ID
        3. Queue job to DTSOP backend (Unity/Unreal Engine)
        4. Store job metadata in simulation registry
        5. Return simulation ID and subscription URI
        6. Background processor updates status -> processing -> completed
        7. Client fetches results from NeoFS when completed

    Args:
        request: SimulationRequest with:
            - scenario_id: Unique scenario identifier
            - sector_id: Geographic sector to simulate
            - disaster_type: Physics model (flood/wildfire/earthquake)
            - parameters: Scenario params (wind_speed, water_level, etc.)
            - priority: "standard" or "urgent"
        ctx: Optional FastMCP context for logging.

    Returns:
        str: Message with simulation ID and subscription instructions:
            "Simulation queued with ID: SIM-XXXXXXXX.
             Subscribe to resq://simulations/SIM-XXXXXXXX for updates."

    Example:
        >>> from resq_mcp.dtsop.models import SimulationRequest
        >>> request = SimulationRequest(
        ...     scenario_id="flood-001",
        ...     sector_id="Sector-1",
        ...     disaster_type="flood",
        ...     parameters={"water_level": 2.5},
        ...     priority="urgent"
        ... )
        >>> result = await run_simulation(request)
        >>> print(result)  # "Simulation queued with ID: SIM-ABCD1234..."

    Integration:
        Production would:
        - Validate request against simulation templates
        - Check cluster capacity and queue position
        - Store job in Redis with priority
        - Submit to Unity/Unreal Engine processing cluster
        - Return estimated completion time
    """
    logger.info("Received Simulation Request: %s", request.scenario_id)

    sim_id = trigger_sim(request)

    simulations[sim_id] = {
        "status": "pending",
        "request": request.model_dump(),
        "created_at": "now",
    }

    if ctx:
        await ctx.info(f"Simulation {sim_id} queued. Monitor at resq://simulations/{sim_id}")

    return (
        f"Simulation queued with ID: {sim_id}. "
        f"Subscribe to resq://simulations/{sim_id} for updates."
    )


@mcp.tool()
async def get_deployment_strategy(incident_id: str) -> OptimizationStrategy:
    """Generate an RL-optimized drone deployment and evacuation strategy.

    Uses reinforcement learning models trained on thousands of simulated
    disasters to recommend optimal resource allocation, routing, and
    risk parameters for a specific incident or pre-alert.

    Args:
        incident_id: Incident identifier (INC-XXX) or pre-alert ID (PRE-XXX)
                     to generate strategy for.

    Returns:
        OptimizationStrategy: Complete strategy recommendation with:
            - strategy_id: Unique identifier
            - related_alert_id: Original incident/alert ID
            - recommended_deployment: Drone type counts
            - evacuation_routes: Prioritized route list
            - estimated_success_rate: Predicted success (0.0-1.0)
            - simulation_proof_url: NeoFS evidence link

    Example:
        >>> strategy = await get_deployment_strategy("PRE-ABC123")
        >>> print(strategy.strategy_id)
        >>> print(strategy.recommended_deployment)  # {"surveillance": 2, ...}
        >>> print(f"Success rate: {strategy.estimated_success_rate:.0%}")

    Use Cases:
        - Pre-positioning drones before predicted disasters (PDIE alerts)
        - Active response optimization for confirmed incidents
        - Multi-objective optimization (speed, safety, resource efficiency)
        - Scenario comparison and sensitivity analysis

    Integration:
        Strategy linked to blockchain for immutable audit trail.
        After approval, use update_mission_params to push to drones.
    """
    return get_optimization_strategy(incident_id)
