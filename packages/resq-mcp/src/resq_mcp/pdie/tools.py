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

"""MCP tool wrappers for the PDIE domain."""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here
# because FastMCP/Pydantic needs to resolve the type annotations at runtime
# for tool parameter validation. Using PEP 563 postponed annotations causes
# NameError when FastMCP tries to evaluate the forward references.

import logging

from fastmcp.exceptions import FastMCPError

from resq_mcp.core.audit import audit_log
from resq_mcp.core.guards import preflight
from resq_mcp.core.models import ErrorResponse
from resq_mcp.pdie.models import PreAlert, VulnerabilityMap
from resq_mcp.pdie.service import get_predictive_alerts as _get_predictive_alerts
from resq_mcp.pdie.service import get_vulnerability_map as _get_vulnerability_map
from resq_mcp.server import mcp

logger = logging.getLogger("resq-mcp")


@mcp.tool()
async def get_vulnerability_map(sector_id: str) -> VulnerabilityMap:
    """Retrieve the precomputed vulnerability assessment for a sector.

    Part of PDIE (Predictive Disaster Intelligence Engine). Returns the static
    infrastructure and risk profile that predictive models consume as input.
    Read-only: this tool never mutates platform state and is therefore
    permitted under Safe Mode.

    Args:
        sector_id: Sector identifier (e.g. "Sector-1" through "Sector-4").

    Returns:
        VulnerabilityMap: Vulnerability data for the sector, containing:
            - population_density: "low" | "medium" | "high"
            - critical_infrastructure: Named assets in the sector
            - flood_risk: Score 0.0-1.0 from terrain and drainage analysis
            - fire_risk: Score 0.0-1.0 from fuel load and climate data

    Raises:
        FastMCPError: If the rate limit is exceeded, the sector_id fails the
            identifier allow-list, or no vulnerability data exists for it.

    Example:
        >>> vuln = await get_vulnerability_map("Sector-1")
        >>> if vuln.fire_risk > 0.7:
        ...     print(f"High fire risk in {vuln.sector_id}")

    Workflow:
        1. Agent inspects sector vulnerability before planning
        2. High risk scores motivate get_predictive_alerts for forecasts
        3. Confirmed incidents flow to get_deployment_strategy
    """
    # Preflight: rate-limit and validate the raw sector_id argument against the
    # identifier allow-list before it is used for a store lookup. Non-mutating,
    # so Safe Mode does not block it.
    preflight(
        "get_vulnerability_map",
        mutating=False,
        identifiers={"sector_id": sector_id},
    )

    result = _get_vulnerability_map(sector_id)
    if isinstance(result, ErrorResponse):
        audit_log(
            "get_vulnerability_map",
            status="denied",
            parameters={"sector_id": sector_id},
            sector_id=sector_id,
            reason="sector_not_found",
        )
        raise FastMCPError(result.message)

    audit_log(
        "get_vulnerability_map",
        status="accepted",
        parameters={"sector_id": sector_id},
        result=result.model_dump(mode="json"),
        sector_id=sector_id,
    )
    return result


@mcp.tool()
async def get_predictive_alerts(sector_id: str) -> list[PreAlert]:
    """Generate probabilistic disaster forecasts for a sector.

    Part of PDIE. Surfaces the output of the predictive models that analyse
    weather patterns, sensor trends, and historical data to forecast disasters
    before they occur. Read-only: permitted under Safe Mode.

    An empty list is a valid, meaningful result — it means the sector currently
    has no forecast disasters, not that the lookup failed.

    Args:
        sector_id: Sector identifier to generate forecasts for.

    Returns:
        list[PreAlert]: Zero or more pre-alerts, each carrying the predicted
            disaster type, probability, and time horizon.

    Raises:
        FastMCPError: If the rate limit is exceeded, the sector_id fails the
            identifier allow-list, or the sector is unknown.

    Example:
        >>> alerts = await get_predictive_alerts("Sector-1")
        >>> for a in alerts:
        ...     print(f"{a.disaster_type}: p={a.probability}")

    Workflow:
        1. Agent polls sectors for pre-alerts
        2. A high-probability alert can be correlated into validate_incident
           via correlated_pre_alert_id
        3. Confirmed incidents flow to get_deployment_strategy
    """
    # Preflight: rate-limit and validate the raw sector_id argument against the
    # identifier allow-list before it is used for a store lookup. Non-mutating,
    # so Safe Mode does not block it.
    preflight(
        "get_predictive_alerts",
        mutating=False,
        identifiers={"sector_id": sector_id},
    )

    result = _get_predictive_alerts(sector_id)
    if isinstance(result, ErrorResponse):
        audit_log(
            "get_predictive_alerts",
            status="denied",
            parameters={"sector_id": sector_id},
            sector_id=sector_id,
            reason="sector_not_found",
        )
        raise FastMCPError(result.message)

    audit_log(
        "get_predictive_alerts",
        status="accepted",
        parameters={"sector_id": sector_id},
        # Hash the full alert payload, not just a count, so the digest can later
        # verify exactly what was returned.
        result=[alert.model_dump(mode="json") for alert in result],
        sector_id=sector_id,
    )
    return result
