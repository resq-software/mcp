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

"""Tests for structured error handling."""

from __future__ import annotations

import json


class TestMCPErrorFormatter:
    def test_format_basic_error(self) -> None:
        from resq_mcp.errors import MCPErrorFormatter

        result = MCPErrorFormatter.format_error(
            error_type="validation_error", message="Sector not found"
        )
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["error"]["type"] == "validation_error"
        assert parsed["error"]["message"] == "Sector not found"

    def test_format_error_with_details_and_suggestion(self) -> None:
        from resq_mcp.errors import MCPErrorFormatter

        result = MCPErrorFormatter.format_error(
            error_type="not_found",
            message="Simulation SIM-XYZ not found",
            details={"sim_id": "SIM-XYZ"},
            suggestion="Check the simulation ID and try again",
        )
        parsed = json.loads(result)
        assert parsed["error"]["details"]["sim_id"] == "SIM-XYZ"
        assert "Check the simulation" in parsed["error"]["suggestion"]

    def test_format_error_without_optionals(self) -> None:
        from resq_mcp.errors import MCPErrorFormatter

        result = MCPErrorFormatter.format_error(
            error_type="internal_error", message="Something went wrong"
        )
        parsed = json.loads(result)
        assert "details" not in parsed["error"]
        assert "suggestion" not in parsed["error"]
        assert "http_status" not in parsed["error"]

    def test_from_exception(self) -> None:
        from resq_mcp.errors import MCPErrorFormatter

        try:
            raise ValueError("Invalid sector_id format")
        except ValueError as e:
            result = MCPErrorFormatter.from_exception(e, "scan sector")
        parsed = json.loads(result)
        assert parsed["error"]["type"] == "validation_error"
        assert "scan sector" in parsed["error"]["message"]
        assert parsed["error"]["details"]["exception_type"] == "ValueError"
