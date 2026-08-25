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

from resq_mcp.drone.service import get_drone_swarm_status, get_fleet_roster
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

    status = sim["status"]
    progress = int((sim.get("progress") or 0) * 100)
    if status == "failed":
        result_info = (
            "FAILED — simulation was cancelled or encountered an error. "
            "Do not retry without resubmitting."
        )
    else:
        result_info = sim.get("result_url", "N/A")

    return f"""
    Simulation ID: {sim_id}
    Status: {status}
    Progress: {progress}%
    Result: {result_info}
    Parameters: {sim.get("request", {})}
    """


@mcp.resource("resq://drones/active")
def list_active_drones() -> str:
    """List currently deployed drones in the active fleet.

    Resource endpoint providing real-time fleet status for operator awareness.
    Shows current deployment locations, battery levels, and operational modes.

    URI Pattern:
        resq://drones/active

    Composition comes from the drone service's fleet roster and the live metrics
    come from get_drone_swarm_status(), so this resource and the
    get_drone_swarm_status tool always report the same fleet.

    Returns:
        str: Formatted string with:
            - One line per drone: identifier, capability, home sector
            - A fleet summary: active/total counts, average battery,
              network health, and last ground-station sync

    Example Response:
        [Active Fleet Status]
        - DRONE-Alpha (Surveillance): home Sector-4
        - DRONE-Beta (Payload): home Sector-2
        - DRONE-Gamma (Relay): home Sector-4

        Fleet: 3/3 active | average battery 82% | network operational
        Last sync: 2026-08-25T20:44:01.123456+00:00

    Use Cases:
        - Operator dashboard fleet overview
        - Resource availability checking before deployment
        - Low battery alert monitoring
        - Sector coverage assessment

    Note:
        Fleet metrics are still simulated. Production would query live telemetry
        from the MCP drone feed server for per-drone position, battery, and
        mission status rather than fleet-level aggregates.
    """
    swarm = get_drone_swarm_status()
    roster = "\n".join(
        f"    - {unit.drone_id} ({unit.role}): home {unit.home_sector}"
        for unit in get_fleet_roster()
    )
    summary = (
        f"    Fleet: {swarm.active_drones}/{swarm.total_drones} active | "
        f"average battery {swarm.average_battery}% | network {swarm.network_status}"
    )
    return f"""
    [Active Fleet Status]
{roster}

{summary}
    Last sync: {swarm.last_sync.isoformat()}
    """
