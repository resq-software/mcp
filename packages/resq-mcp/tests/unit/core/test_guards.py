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

"""Tests for the composed tool preflight guard."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import FastMCPError

from resq_mcp.core.guards import preflight


class TestPreflight:
    def test_passes_for_benign_call(self) -> None:
        # Safe Mode is disabled by the autouse fixture; identifiers are valid.
        preflight("get_deployment_strategy", identifiers={"incident_id": "INC-1"})

    def test_safe_mode_blocks_mutating_tool(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from resq_mcp.core import security

        monkeypatch.setattr(security.settings, "SAFE_MODE", True)
        with pytest.raises(FastMCPError, match="RESQ_SAFE_MODE"):
            preflight("update_mission_params", mutating=True)

    def test_non_mutating_tool_ignores_safe_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from resq_mcp.core import security

        monkeypatch.setattr(security.settings, "SAFE_MODE", True)
        # Read-only tools are not gated by Safe Mode.
        preflight("get_deployment_strategy", mutating=False)

    def test_invalid_identifier_raises_fastmcp_error(self) -> None:
        with pytest.raises(FastMCPError, match="disallowed characters"):
            preflight("update_mission_params", identifiers={"drone_id": "bad id; rm -rf"})

    def test_rate_limit_breach_raises_fastmcp_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from resq_mcp.core import ratelimit

        monkeypatch.setattr(ratelimit.settings, "RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr(ratelimit.rate_limiter, "max_calls", 1)
        preflight("run_simulation", mutating=True)
        with pytest.raises(FastMCPError, match="Rate limit exceeded"):
            preflight("run_simulation", mutating=True)
