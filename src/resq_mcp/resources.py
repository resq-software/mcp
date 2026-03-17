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

"""MCP resource endpoints for the ResQ server."""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here
# because FastMCP/Pydantic needs to resolve the type annotations at runtime
# for tool parameter validation. Using PEP 563 postponed annotations causes
# NameError when FastMCP tries to evaluate the forward references.

from fastmcp.exceptions import FastMCPError

from resq_mcp.server import mcp, simulations


@mcp.resource("resq://simulations/{sim_id}")
async def get_simulation_status(sim_id: str) -> str:
    """Get the current status of a physics simulation job.

    Resource endpoint that provides real-time simulation progress and results.
    Supports SSE subscriptions for push notifications on state changes.

    URI Pattern:
        resq://simulations/{sim_id}

    Subscription Behavior:
        Clients can subscribe to this resource to receive automatic updates
        when simulation state transitions (pending -> processing -> completed).
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
        1. Call run_simulation tool -> get sim_id
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
