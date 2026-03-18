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

"""MCP prompt templates for the ResQ server."""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here
# because FastMCP/Pydantic needs to resolve the type annotations at runtime
# for tool parameter validation. Using PEP 563 postponed annotations causes
# NameError when FastMCP tries to evaluate the forward references.

import re

from fastmcp.exceptions import FastMCPError

from resq_mcp.server import mcp

# Allowlist pattern for incident IDs injected into LLM prompt templates.
# Prevents prompt injection via crafted incident_id values.
_INCIDENT_ID_RE = re.compile(r"^[A-Z0-9\-]{1,64}$")


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
        - get_deployment_strategy(incident_id) -> OptimizationStrategy
        - resq://drones/active -> Fleet status
        - Additional sector/swarm status tools as needed
    """
    safe_id = incident_id.upper().strip()
    if not _INCIDENT_ID_RE.match(safe_id):
        raise FastMCPError(
            f"Invalid incident_id format: {incident_id!r}. "
            "Expected alphanumeric characters and hyphens only (e.g. INC-001)."
        )
    return f"""
    As a Crisis Coordinator, analyze Incident {safe_id}.

    1. Check `get_deployment_strategy` for this incident.
    2. Review available assets in `resq://drones/active`.
    3. Propose a step-by-step containment plan.

    Output format:
    - Situation Summary
    - Asset Allocation
    - Risk Assessment
    """
