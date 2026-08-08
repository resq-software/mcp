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

"""MCP tool wrappers for the drone fleet domain."""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here
# because FastMCP/Pydantic needs to resolve the type annotations at runtime
# for tool parameter validation. Using PEP 563 postponed annotations causes
# NameError when FastMCP tries to evaluate the forward references.

import logging
from typing import Literal

from fastmcp.exceptions import FastMCPError

from resq_mcp.core.audit import audit_log
from resq_mcp.core.guards import preflight
from resq_mcp.core.models import ErrorResponse
from resq_mcp.drone.models import (
    DeploymentStatus,
    NetworkStatus,
    SectorAnalysis,
    SwarmStatus,
)
from resq_mcp.drone.service import get_all_sectors_status as _get_all_sectors_status
from resq_mcp.drone.service import get_drone_swarm_status as _get_drone_swarm_status
from resq_mcp.drone.service import request_drone_deployment as _request_drone_deployment
from resq_mcp.drone.service import scan_current_sector as _scan_current_sector
from resq_mcp.server import mcp

logger = logging.getLogger("resq-mcp")


@mcp.tool()
async def scan_current_sector(sector_id: str = "Sector-1") -> SectorAnalysis:
    """Run a drone sensor sweep of a sector and return detected objects.

    Read-only: reports what the fleet currently observes without commanding
    any drone, so it remains available under Safe Mode.

    Args:
        sector_id: Sector identifier to scan (e.g. "Sector-1").

    Returns:
        SectorAnalysis: Detected objects, hazard assessment, and scan metadata.

    Raises:
        FastMCPError: If the rate limit is exceeded, the sector_id fails the
            identifier allow-list, or the sector is unknown.

    Example:
        >>> analysis = await scan_current_sector("Sector-1")
        >>> print(analysis.detected_object, analysis.confidence)
        >>> print(analysis.recommended_action)
    """
    # Preflight: rate-limit and validate the raw sector_id argument. The drone
    # models carry no identifier field_validator (unlike the HCE models), so this
    # is the only allow-list check standing in front of the lookup.
    preflight(
        "scan_current_sector",
        mutating=False,
        identifiers={"sector_id": sector_id},
    )

    result = _scan_current_sector(sector_id)
    if isinstance(result, ErrorResponse):
        audit_log(
            "scan_current_sector",
            status="denied",
            parameters={"sector_id": sector_id},
            sector_id=sector_id,
            reason="sector_not_found",
        )
        raise FastMCPError(result.message)

    audit_log(
        "scan_current_sector",
        status="accepted",
        parameters={"sector_id": sector_id},
        result=result.model_dump(mode="json"),
        sector_id=sector_id,
    )
    return result


@mcp.tool()
async def get_all_sectors_status() -> NetworkStatus:
    """Report mesh-network status across every monitored sector.

    Read-only: available under Safe Mode. Takes no arguments, so there is no
    identifier to validate.

    Returns:
        NetworkStatus: Per-sector summaries plus aggregate network health.

    Raises:
        FastMCPError: If the rate limit is exceeded.

    Example:
        >>> status = await get_all_sectors_status()
        >>> print(status.total_sectors, status.critical_alerts)
    """
    preflight("get_all_sectors_status", mutating=False)

    result = _get_all_sectors_status()
    audit_log(
        "get_all_sectors_status",
        status="accepted",
        result=result.model_dump(mode="json"),
    )
    return result


@mcp.tool()
async def get_drone_swarm_status() -> SwarmStatus:
    """Report live drone fleet telemetry: counts, battery, and assignments.

    Read-only: available under Safe Mode. Takes no arguments, so there is no
    identifier to validate.

    Returns:
        SwarmStatus: Total and active drone counts with fleet-level telemetry.

    Raises:
        FastMCPError: If the rate limit is exceeded.

    Example:
        >>> swarm = await get_drone_swarm_status()
        >>> print(f"{swarm.active_drones}/{swarm.total_drones} active")
    """
    preflight("get_drone_swarm_status", mutating=False)

    result = _get_drone_swarm_status()
    audit_log(
        "get_drone_swarm_status",
        status="accepted",
        result=result.model_dump(mode="json"),
    )
    return result


@mcp.tool()
async def request_drone_deployment(
    sector_id: str,
    priority: Literal["low", "medium", "high", "critical"] = "high",
) -> DeploymentStatus:
    """Dispatch a drone to a sector.

    **This is a mutating tool.** It commands real fleet movement, so Safe Mode
    (``RESQ_SAFE_MODE=true``, the default) refuses it. Disable Safe Mode only
    when autonomous execution is intended.

    Args:
        sector_id: Target sector identifier for the deployment.
        priority: Deployment urgency. One of "low", "medium", "high", "critical".
            Constrained at the tool boundary, so invalid values are rejected
            before reaching the service.

    Returns:
        DeploymentStatus: Assigned drone, ETA, and acknowledged priority.

    Raises:
        FastMCPError: If Safe Mode is enabled, the rate limit is exceeded, the
            sector_id fails the identifier allow-list, or the sector is unknown.

    Example:
        >>> status = await request_drone_deployment("Sector-1", priority="critical")
        >>> print(status.drone_id, status.eta_seconds)

    Workflow:
        1. scan_current_sector / get_predictive_alerts establish the need
        2. Operator approves the dispatch
        3. This tool commands the drone (Safe Mode must be off)
    """
    # Preflight: rate-limit, validate the raw sector_id, and enforce the Safe Mode
    # gate. This is the only drone tool with side effects.
    preflight(
        "request_drone_deployment",
        mutating=True,
        identifiers={"sector_id": sector_id},
    )

    result = _request_drone_deployment(sector_id, priority)
    if isinstance(result, ErrorResponse):
        audit_log(
            "request_drone_deployment",
            status="denied",
            parameters={"sector_id": sector_id, "priority": priority},
            sector_id=sector_id,
            reason="sector_not_found",
        )
        raise FastMCPError(result.message)

    audit_log(
        "request_drone_deployment",
        # "dispatched" matches update_mission_params (hce/tools.py), the other
        # side-effecting dispatch action, rather than the generic "accepted".
        status="dispatched",
        parameters={"sector_id": sector_id, "priority": priority},
        result=result.model_dump(mode="json"),
        sector_id=sector_id,
        drone_id=result.drone_id,
    )
    return result
