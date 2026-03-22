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

"""Extended tests for telemetry module covering sanitization, tracing, and metrics."""

from __future__ import annotations

import logging

import pytest


class TestSanitizeAttrs:
    def test_coarsens_float_lat_lon(self) -> None:
        from resq_mcp.core.telemetry import _sanitize_attrs

        result = _sanitize_attrs({"lat": 40.12345678, "count": 5})
        assert result["lat"] == 40.12  # rounds to 2 decimal places
        assert result["count"] == 5

    def test_redacts_sensitive_keys(self) -> None:
        from resq_mcp.core.telemetry import _sanitize_attrs

        result = _sanitize_attrs(
            {
                "api_key": "sk-12345",
                "auth_token": "abc",
                "safe": "hello world",
            }
        )
        assert result["api_key"] == "[REDACTED]"
        assert result["auth_token"] == "[REDACTED]"  # noqa: S105
        assert result["safe"] == "hello world"

    def test_redacts_bearer_in_string_values(self) -> None:
        from resq_mcp.core.telemetry import _sanitize_attrs

        result = _sanitize_attrs(
            {
                "header": "Bearer eyJhbGci.payload.sig",
            }
        )
        assert "eyJhbGci" not in result["header"]


class TestRedactLogMessage:
    def test_redacts_bearer_tokens(self) -> None:
        from resq_mcp.core.telemetry import _redact_log_message

        result = _redact_log_message("Auth: Bearer eyJhbGci.secret.stuff")
        assert "eyJhbGci" not in result


class TestTruncate:
    def test_truncates_long_string(self) -> None:
        from resq_mcp.core.telemetry import _truncate

        result = _truncate("a" * 500, 100)
        assert len(result) <= 120

    def test_short_string_unchanged(self) -> None:
        from resq_mcp.core.telemetry import _truncate

        assert _truncate("hello", 100) == "hello"


class TestBuildResource:
    def test_builds_resource(self) -> None:
        from resq_mcp.core.telemetry import _build_resource

        resource = _build_resource()
        # May return None if OTel SDK not installed
        if resource is not None:
            attrs = dict(resource.attributes)
            assert attrs["service.name"] == "resq-mcp"


class TestNoOpClasses:
    def test_noop_span_methods(self) -> None:
        from resq_mcp.core.telemetry import _NoOpSpan

        span = _NoOpSpan()
        span.set_attribute("key", "value")
        span.set_status("ok")
        span.record_exception(Exception("test"))
        span.end()
        # Context manager protocol
        with span:
            pass

    def test_noop_tracer_start_as_current_span(self) -> None:
        from resq_mcp.core.telemetry import _NoOpTracer

        tracer = _NoOpTracer()
        span = tracer.start_as_current_span("test")
        assert span is not None

    def test_noop_tracer_start_span(self) -> None:
        from resq_mcp.core.telemetry import _NoOpTracer

        tracer = _NoOpTracer()
        with tracer.start_span("test") as s:
            assert s is not None


class TestMetricsLazyInit:
    def test_metrics_properties(self) -> None:
        from resq_mcp.core.telemetry import _Metrics

        m = _Metrics()
        assert m.tool_invocations is not None
        assert m.tool_duration is not None
        assert m.tool_errors is not None


class TestTraceDecorator:
    def test_trace_sync_function(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace
        def my_func(x: int) -> int:
            return x * 2

        assert my_func(5) == 10

    @pytest.mark.asyncio
    async def test_trace_async_function(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace
        async def my_async_func(x: int) -> int:
            return x * 3

        assert await my_async_func(5) == 15

    def test_trace_sync_exception(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace
        def failing_func() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_func()

    @pytest.mark.asyncio
    async def test_trace_async_exception(self) -> None:
        from resq_mcp.core.telemetry import trace

        @trace
        async def failing_async() -> None:
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError, match="async error"):
            await failing_async()


class TestSpanContextManager:
    def test_span_context_manager(self) -> None:
        from resq_mcp.core.telemetry import span

        with span("test-span", {"key": "value"}) as s:
            assert s is not None

    def test_span_records_exception(self) -> None:
        from resq_mcp.core.telemetry import span

        with pytest.raises(ValueError), span("error-span"):
            raise ValueError("boom")


class TestLogEvent:
    def test_log_event_runs(self) -> None:
        from resq_mcp.core.telemetry import log_event

        log_event("test.event", level=logging.INFO, key="value")


class TestGetTraceContext:
    def test_returns_dict(self) -> None:
        from resq_mcp.core.telemetry import _get_trace_context

        ctx = _get_trace_context()
        assert isinstance(ctx, dict)


class TestShutdownTelemetry:
    def test_shutdown_runs(self) -> None:
        from resq_mcp.core.telemetry import shutdown_telemetry

        shutdown_telemetry()
