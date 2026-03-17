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

"""ResQ MCP Server - Model Context Protocol server for disaster response coordination.

This module provides the main FastMCP server implementation for ResQ, offering:
- Simulation management via resources and tools
- Drone fleet status and deployment
- Incident validation and response planning

The server uses a lifespan context manager to manage background tasks for
simulation processing and notification delivery.
"""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here
# because FastMCP/Pydantic needs to resolve the type annotations at runtime
# for tool parameter validation. Using PEP 563 postponed annotations causes
# NameError when FastMCP tries to evaluate the forward references.

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastmcp import Context, FastMCP
from fastmcp.exceptions import FastMCPError

from .config import settings
from .dtsop import get_optimization_strategy
from .dtsop import run_simulation as trigger_sim
from .models import (
    IncidentValidation,
    OptimizationStrategy,
    SimulationRequest,
)
from .telemetry import setup_telemetry

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger("resq-mcp")

# Initialize Telemetry
setup_telemetry()

# --- Mock Data Store ---
simulations: "dict[str, dict[str, Any]]" = {}


@asynccontextmanager
async def lifespan(server: FastMCP) -> "AsyncGenerator[None, None]":
    """Lifespan context manager for the MCP server with background tasks.

    Manages the lifecycle of background processing tasks that run for the
    duration of the server. Ensures clean startup and shutdown with proper
    task cancellation and resource cleanup.

    Background Tasks Started:
        - simulation_processor: Mock simulation state machine that transitions
          simulations from pending → processing → completed and sends SSE
          notifications to subscribed clients.

    Lifecycle:
        1. Startup: Log initialization, create background tasks
        2. Running: Yield control to FastMCP server
        3. Shutdown: Cancel tasks, suppress CancelledError, log shutdown

    Args:
        server: The FastMCP server instance for notification dispatch.

    Yields:
        None: Control returns to FastMCP for request handling.

    Note:
        In production, background tasks would interface with actual
        simulation clusters, message queues (Redis/RabbitMQ), and
        maintain persistent connections to drone telemetry streams.
    """
    logger.info("Starting resQ MCP Server...")
    task = asyncio.create_task(simulation_processor(server))
    yield
    logger.info("Shutting down resQ MCP Server...")
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


# Initialize FastMCP
mcp = FastMCP(
    settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


# --- Background Tasks ---


async def simulation_processor(server: FastMCP) -> None:
    """Background processor for simulation state transitions and notifications.

    Simulates async physics simulation job processing with state machine:
    - pending → processing (immediate, 50% progress)
    - processing → completed (after 3s delay, 100% progress, generates result URL)

    Notifications:
        Sends SSE resource update notifications to clients subscribed to
        resq://simulations/{sim_id} whenever simulation state changes.

    Args:
        server: FastMCP server instance for notification dispatch.

    State Machine:
        pending: Job queued, waiting for processing
          ↓ (2s poll)
        processing: Simulation running (progress=0.5)
          ↓ (3s delay)
        completed: Results available (progress=1.0, result_url set)

    Notification Protocol:
        Uses FastMCP resource update notifications:
        - Clients subscribe to simulation URI
        - Server pushes SSE events on state change
        - Clients can poll or wait for completion

    Error Handling:
        Notification failures are logged at DEBUG level but don't crash
        the processor. Simulation state updates continue regardless.

    Note:
        Production would replace this with actual job queue integration
        (Celery/RQ) and Unity/Unreal Engine status polling.
    """
    while True:
        await asyncio.sleep(2)
        for sim_id, data in simulations.items():
            if data["status"] == "pending":
                data["status"] = "processing"
                data["progress"] = 0.5
                logger.info("Simulation %s moved to PROCESSING", sim_id)
                try:
                    await server.notify_resource_updated(f"resq://simulations/{sim_id}")
                except Exception:
                    logger.debug("Failed to notify for %s", sim_id, exc_info=True)

            elif data["status"] == "processing":
                await asyncio.sleep(3)
                data["status"] = "completed"
                data["progress"] = 1.0
                data["result_url"] = f"neofs://sim_results/{sim_id}.json"
                logger.info("Simulation %s COMPLETED", sim_id)
                try:
                    await server.notify_resource_updated(f"resq://simulations/{sim_id}")
                except Exception:
                    logger.debug("Failed to notify for %s", sim_id, exc_info=True)


# --- Resources ---


@mcp.resource("resq://simulations/{sim_id}")
async def get_simulation_status(sim_id: str) -> str:
    """Get the current status of a physics simulation job.

    Resource endpoint that provides real-time simulation progress and results.
    Supports SSE subscriptions for push notifications on state changes.

    URI Pattern:
        resq://simulations/{sim_id}

    Subscription Behavior:
        Clients can subscribe to this resource to receive automatic updates
        when simulation state transitions (pending → processing → completed).
        Server sends resource_updated notifications via SSE.

    Args:
        sim_id: Unique simulation job identifier (e.g., "SIM-A1B2C3D4").

    Returns:
        str: Formatted string with simulation details:
            - Simulation ID
            - Current status (pending/processing/completed)
            - Progress percentage (0-100%)
            - Result URL (NeoFS CID) when completed
            - Original request parameters

    Raises:
        FastMCPError: If sim_id not found in simulation registry.

    Example:
        Client workflow:
        1. Call run_simulation tool → get sim_id
        2. Subscribe to resq://simulations/{sim_id}
        3. Receive updates as simulation progresses
        4. Fetch result_url when status=completed

    Response Format:
        Simulation ID: SIM-A1B2C3D4
        Status: processing
        Progress: 50%
        Result: N/A (or neofs://sim_results/SIM-xxx.json)
        Parameters: {scenario_id: ..., sector_id: ..., ...}
    """
    sim = simulations.get(sim_id)
    if not sim:
        msg = f"Simulation {sim_id} not found"
        raise FastMCPError(msg)

    return f"""
    Simulation ID: {sim_id}
    Status: {sim["status"]}
    Progress: {int(sim.get("progress", 0) * 100)}%
    Result: {sim.get("result_url", "N/A")}
    Parameters: {sim.get("request", {})}
    """


@mcp.resource("resq://drones/active")
def list_active_drones() -> str:
    """List currently deployed drones in the active fleet.

    Resource endpoint providing real-time fleet status for operator awareness.
    Shows current deployment locations, battery levels, and operational modes.

    URI Pattern:
        resq://drones/active

    Returns:
        str: Formatted string with active drone details:
            - Drone identifier
            - Drone type/capability (Surveillance/Payload/Relay)
            - Operational status (ACTIVE/RETURNING/CHARGING)
            - Battery percentage
            - Current sector assignment

    Example Response:
        [Active Fleet Status]
        - DRONE-Alpha (Surveillance): ACTIVE | Battery 78% | Sector 4
        - DRONE-Beta (Payload): RETURNING | Battery 12% | Sector 2
        - DRONE-Gamma (Relay): ACTIVE | Battery 92% | Sector 4

    Use Cases:
        - Operator dashboard fleet overview
        - Resource availability checking before deployment
        - Low battery alert monitoring
        - Sector coverage assessment

    Note:
        Current implementation returns static mock data. Production would
        query live telemetry from MCP drone feed server and aggregate
        real-time positions, battery, and mission status.
    """
    return """
    [Active Fleet Status]
    - DRONE-Alpha (Surveillance): ACTIVE | Battery 78% | Sector 4
    - DRONE-Beta (Payload): RETURNING | Battery 12% | Sector 2
    - DRONE-Gamma (Relay): ACTIVE | Battery 92% | Sector 4
    """


# --- Tools ---


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
        6. Background processor updates status → processing → completed
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
        >>> from resq_mcp.models import SimulationRequest
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
        ctx.info(f"Simulation {sim_id} queued. Monitor at resq://simulations/{sim_id}")

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


@mcp.tool()
async def validate_incident(val: IncidentValidation) -> str:
    """Submit validation result for an incident report.

    Used by human operators or automated validation systems (HCE) to
    confirm or reject incident reports before triggering full response.

    Args:
        val: IncidentValidation with:
            - incident_id: ID of incident being validated
            - is_confirmed: True=confirmed, False=rejected/false positive
            - validation_source: Who/what validated (e.g., "Human-Operator")
            - correlated_pre_alert_id: Optional linked PDIE alert
            - notes: Validation reasoning and evidence

    Returns:
        str: Confirmation message indicating action taken:
            "Incident {id} successfully CONFIRMED." or
            "Incident {id} successfully REJECTED."

    Example:
        >>> from resq_mcp.models import IncidentValidation
        >>> validation = IncidentValidation(
        ...     incident_id="INC-123",
        ...     is_confirmed=True,
        ...     validation_source="Human-Operator-Alice",
        ...     notes="Confirmed via video evidence and ground reports"
        ... )
        >>> result = await validate_incident(validation)
        >>> print(result)  # "Incident INC-123 successfully CONFIRMED."

    Workflow:
        1. Edge AI detects incident (low confidence)
        2. HCE cross-references with PDIE/sensors
        3. If ambiguous → human review required
        4. Operator submits validation via this tool
        5. If confirmed → trigger response strategy
        6. If rejected → log as false positive, update ML model

    Audit Trail:
        All validations logged with timestamp, source, and reasoning
        for post-incident analysis and ML model refinement.
    """
    action = "CONFIRMED" if val.is_confirmed else "REJECTED"
    logger.info(
        "Incident %s %s by %s. Notes: %s",
        val.incident_id,
        action,
        val.validation_source,
        val.notes,
    )
    return f"Incident {val.incident_id} successfully {action}."


# --- Prompts ---


@mcp.prompt()
def incident_response_plan(incident_id: str) -> str:
    """Generate a structured prompt template for incident response planning.

    Provides a framework for AI agents or human operators to systematically
    analyze incidents and develop comprehensive response plans using
    available MCP tools and resources.

    Template Sections:
        1. Situation Summary: Analyze current state and severity
        2. Asset Allocation: Review and assign available resources
        3. Risk Assessment: Evaluate hazards and constraints

    Args:
        incident_id: The incident identifier to analyze (e.g., "INC-123").

    Returns:
        str: Formatted prompt template with:
            - Analysis instructions
            - Tool references (get_deployment_strategy, resq://drones/active)
            - Expected output format

    Example:
        >>> prompt = incident_response_plan("INC-456")
        >>> # Use with LLM:
        >>> response = llm.complete(prompt)
        >>> # LLM will call tools and produce structured response

    Use Cases:
        - AI-assisted crisis coordination (Spoon OS agent)
        - Human operator decision support
        - Training scenario generation
        - Post-incident plan review

    Integration:
        Prompt references MCP tools and resources that the LLM can call:
        - get_deployment_strategy(incident_id) → OptimizationStrategy
        - resq://drones/active → Fleet status
        - Additional sector/swarm status tools as needed
    """
    return f"""
    As a Crisis Coordinator, analyze Incident {incident_id}.

    1. Check `get_deployment_strategy` for this incident.
    2. Review available assets in `resq://drones/active`.
    3. Propose a step-by-step containment plan.

    Output format:
    - Situation Summary
    - Asset Allocation
    - Risk Assessment
    """


def main() -> None:
    """Console script entry point for the ResQ MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
