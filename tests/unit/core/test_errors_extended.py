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

"""Extended tests for MCPErrorFormatter covering uncovered branches."""

from __future__ import annotations

import json


class TestMCPErrorFormatterExtended:
    def test_format_error_with_http_status(self) -> None:
        from resq_mcp.core.errors import MCPErrorFormatter

        result = MCPErrorFormatter.format_error(
            error_type="not_found",
            message="Resource not found",
            http_status=404,
        )
        parsed = json.loads(result)
        assert parsed["error"]["http_status"] == 404

    def test_from_exception_key_error(self) -> None:
        from resq_mcp.core.errors import MCPErrorFormatter

        result = MCPErrorFormatter.from_exception(KeyError("missing_field"), "fetch data")
        parsed = json.loads(result)
        assert parsed["error"]["type"] == "missing_data"
        assert parsed["error"]["suggestion"] == "The requested resource was not found"

    def test_from_exception_timeout_error(self) -> None:
        from resq_mcp.core.errors import MCPErrorFormatter

        result = MCPErrorFormatter.from_exception(
            TimeoutError("connection timed out"), "connect to HCE"
        )
        parsed = json.loads(result)
        assert parsed["error"]["type"] == "timeout"
        assert "timed out" in parsed["error"]["suggestion"]

    def test_from_exception_unknown_error(self) -> None:
        from resq_mcp.core.errors import MCPErrorFormatter

        result = MCPErrorFormatter.from_exception(RuntimeError("unexpected"), "process request")
        parsed = json.loads(result)
        assert parsed["error"]["type"] == "unknown_error"
        assert "suggestion" not in parsed["error"]

    def test_from_exception_with_context_redaction(self) -> None:
        from resq_mcp.core.errors import MCPErrorFormatter

        result = MCPErrorFormatter.from_exception(
            ValueError("bad input"),
            "validate",
            context={
                "sector": "SECTOR-1",
                "authorization": "Bearer secret123",
                "token": "tok_abc",
                "password": "hunter2",
                "secret": "mysecret",
                "api_key": "sk-123",
                "cookie": "session=abc",
                "safe_field": "visible",
            },
        )
        parsed = json.loads(result)
        ctx = parsed["error"]["details"]["context"]
        assert "sector" in ctx
        assert "safe_field" in ctx
        assert "authorization" not in ctx
        assert "token" not in ctx
        assert "password" not in ctx
        assert "secret" not in ctx
        assert "api_key" not in ctx
        assert "cookie" not in ctx
