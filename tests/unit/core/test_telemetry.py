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

"""Tests for telemetry utilities."""

from __future__ import annotations

import logging

import pytest


class TestSetupTelemetry:
    """Tests for the setup_telemetry function."""

    def test_setup_completes_without_error(self) -> None:
        from resq_mcp.core.telemetry import setup_telemetry

        # Should not raise
        setup_telemetry()

    def test_setup_logs_in_debug_mode(self, caplog: logging.LogCaptureFixture) -> None:
        from unittest.mock import patch

        with patch("resq_mcp.core.telemetry.settings") as mock_settings:
            mock_settings.DEBUG = True
            from resq_mcp.core import telemetry

            # Re-import to pick up patched settings at module level doesn't work,
            # but calling setup_telemetry which reads settings at call time does.
            with caplog.at_level(logging.INFO, logger="resq_mcp.core.telemetry"):
                telemetry.setup_telemetry()
            assert "no-op" in caplog.text.lower() or "telemetry" in caplog.text.lower()


class TestTraceDecorator:
    """Tests for the trace decorator stub."""

    def test_trace_returns_original_function(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace("test.span")
        def my_func(x: int) -> int:
            return x * 2

        assert my_func(5) == 10

    def test_trace_without_name(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace()
        def my_func() -> str:
            return "hello"

        assert my_func() == "hello"

    def test_trace_preserves_function_identity(self) -> None:
        from resq_mcp.core.telemetry import trace

        def original(x: int) -> int:
            return x

        decorated = trace("span")(original)
        # In no-op mode, the decorator returns the original function
        assert decorated is original

    def test_trace_preserves_function_name(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace("test.span")
        def my_named_func() -> None:
            # intentionally empty: only the function name is under test
            pass

        assert my_named_func.__name__ == "my_named_func"

    @pytest.mark.asyncio
    async def test_trace_works_with_async_functions(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace("async.span")
        async def my_async_func(x: int) -> int:
            return x * 3

        result = await my_async_func(7)
        assert result == 21
