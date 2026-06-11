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

"""Tool preflight guards for the ResQ MCP server.

A single ``preflight`` entry point composes the per-invocation security controls
recommended by NSA PP-26-1834 and normalises their failures into ``FastMCPError``
so tool wrappers stay terse and consistent:

1. **Rate limiting** — bound the per-tool call rate (DoS / fatigue mitigation).
2. **Safe Mode gate** — block mutating tools unless execution is explicitly enabled
   (confused-deputy mitigation).
3. **Identifier validation** — reject raw string arguments that fall outside the
   identifier allow-list (injection / traversal / parameter-forwarding mitigation).

Pydantic-modelled tool inputs are validated at the model boundary; ``preflight`` is
for the raw scalar arguments that arrive outside a model.
"""

from __future__ import annotations

from collections.abc import Mapping

from fastmcp.exceptions import FastMCPError

from resq_mcp.core.ratelimit import RateLimitExceeded, enforce_rate_limit
from resq_mcp.core.security import require_mutation_allowed
from resq_mcp.core.validation import validate_identifier


def preflight(
    tool: str,
    *,
    mutating: bool = False,
    identifiers: Mapping[str, str] | None = None,
) -> None:
    """Run the standard preflight security checks for a tool invocation.

    Args:
        tool: The tool name (used as the rate-limit key and in error messages).
        mutating: If True, enforce the Safe Mode gate (the tool has side effects).
        identifiers: Optional mapping of ``field_name -> value`` raw string
            arguments to validate against the identifier allow-list.

    Raises:
        FastMCPError: If the rate limit is exceeded, Safe Mode blocks a mutating
            tool, or an identifier fails validation. The underlying ``ValueError``
            / ``RateLimitExceeded`` is normalised so clients see one error type.
    """
    try:
        enforce_rate_limit(tool)
    except RateLimitExceeded as exc:
        raise FastMCPError(str(exc)) from exc

    if mutating:
        # require_mutation_allowed already raises FastMCPError when Safe Mode is on.
        require_mutation_allowed(tool)

    if identifiers:
        for field, value in identifiers.items():
            try:
                validate_identifier(value, field=field)
            except ValueError as exc:
                raise FastMCPError(str(exc)) from exc
