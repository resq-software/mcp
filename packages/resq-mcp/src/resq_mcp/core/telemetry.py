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

"""Telemetry subsystem for the ResQ MCP server.

Provides unified OpenTelemetry tracing, Prometheus-compatible metrics,
and structured logging with automatic PII redaction.
"""

from __future__ import annotations

import functools
import logging
import re
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from resq_mcp.core.config import settings

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

# ---------------------------------------------------------------------------
# Type variables
# ---------------------------------------------------------------------------

P = ParamSpec("P")
R = TypeVar("R")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("resq_mcp.telemetry")

# ---------------------------------------------------------------------------
# PII / secret patterns
# ---------------------------------------------------------------------------

_REDACT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|private[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+\S+"),
    re.compile(r"(-?\d{1,3}\.\d{3,})\s*,\s*(-?\d{1,3}\.\d{3,})"),
    re.compile(r"(?i)(?:lat(?:itude)?|lon(?:gitude)?|lng)\s*[:=]\s*(-?\d{1,3}\.\d{3,})"),
)

_SENSITIVE_ATTR_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "token",
        "secret",
        "password",
        "private_key",
        "authorization",
        "credential",
        "resq.api_key",
    }
)

# ---------------------------------------------------------------------------
# Lazy OTel imports
# ---------------------------------------------------------------------------

try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.metrics import get_meter_provider, set_meter_provider
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.composite import CompositePropagator
    from opentelemetry.sdk.metrics import MeterProvider as SdkMeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.trace import StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    _HAS_OTEL_SDK = True
except ImportError:
    _HAS_OTEL_SDK = False

    class _NoOpStatusCode:
        """Stand-in for ``opentelemetry.trace.StatusCode`` when the SDK is absent.

        Mirrors the three members the tracing helpers reference so span status
        calls type-check and run without OpenTelemetry installed.
        """

        OK = "OK"
        ERROR = "ERROR"
        UNSET = "UNSET"

    StatusCode = _NoOpStatusCode  # type: ignore[assignment,misc]

try:
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )

    _HAS_OTLP = True
except ImportError:
    _HAS_OTLP = False

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_initialized: bool = False
tracer: Any = None
meter: Any = None


def _sanitize_attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    """Strip secrets and coarsen PII from attributes."""
    clean: dict[str, Any] = {}
    for key, value in attrs.items():
        key_lower = key.lower().replace(".", "_").replace("-", "_")
        if key_lower in _SENSITIVE_ATTR_KEYS or any(
            s in key_lower for s in ("key", "token", "secret", "password", "credential")
        ):
            clean[key] = "[REDACTED]"
            continue
        if key_lower in ("latitude", "longitude", "lat", "lon", "lng") and isinstance(value, float):
            clean[key] = round(value, 2)
            continue
        if isinstance(value, str):
            sanitized = value
            for pattern in _REDACT_PATTERNS:
                sanitized = pattern.sub("[REDACTED]", sanitized)
            clean[key] = sanitized
            continue
        clean[key] = value
    return clean


def _redact_log_message(msg: str) -> str:
    """Apply redaction to a log string."""
    for pattern in _REDACT_PATTERNS:
        msg = pattern.sub("[REDACTED]", msg)
    return msg


def _build_resource() -> Any:
    """Build an OTel Resource."""
    if not _HAS_OTEL_SDK:
        return None
    return Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.VERSION,
            "deployment.environment": "development" if settings.DEBUG else "production",
            "resq.safe_mode": str(settings.SAFE_MODE),
        }
    )


def setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing and metrics."""
    global _initialized, tracer, meter
    if _initialized:
        return
    _initialized = True

    if _HAS_OTEL_SDK:
        resource = _build_resource()
        provider = SdkTracerProvider(resource=resource)

        backend = settings.TELEMETRY_BACKEND
        endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT

        if backend in ("otlp", "jaeger") and _HAS_OTLP:
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("Tracing \u2192 OTLP exporter (%s) at %s", backend, endpoint)
        elif backend == "console" or (backend != "none" and settings.DEBUG):
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            logger.info("Tracing \u2192 console exporter")

        otel_trace.set_tracer_provider(provider)

        metric_reader = None
        if backend in ("otlp", "jaeger") and _HAS_OTLP:
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=endpoint, insecure=True),
                export_interval_millis=15_000,
            )
        elif backend == "console":
            metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=30_000,
            )

        if metric_reader is not None:
            meter_provider = SdkMeterProvider(
                resource=resource,
                metric_readers=[metric_reader],
            )
            set_meter_provider(meter_provider)

        set_global_textmap(CompositePropagator([TraceContextTextMapPropagator()]))
        tracer = otel_trace.get_tracer("resq-mcp", settings.VERSION)
        meter = get_meter_provider().get_meter("resq-mcp", settings.VERSION)
    else:
        try:
            from opentelemetry import trace as _api_trace
            from opentelemetry.metrics import get_meter_provider as _get_mp

            tracer = _api_trace.get_tracer("resq-mcp", settings.VERSION)
            meter = _get_mp().get_meter("resq-mcp", settings.VERSION)
        except ImportError:
            tracer = _NoOpTracer()
            meter = _NoOpMeter()


class _NoOpSpan:
    """Span that discards everything written to it.

    Returned by :class:`_NoOpTracer` so instrumented code paths run unchanged
    when no telemetry backend is configured (``RESQ_TELEMETRY_BACKEND=none``,
    the default) or the OpenTelemetry SDK is not installed.
    """

    def set_attribute(self, _key: str, _value: Any) -> None:
        """Discard an attribute."""

    def set_status(self, _status: Any, _description: str | None = None) -> None:
        """Discard a status update."""

    def record_exception(self, _exception: BaseException) -> None:
        """Discard a recorded exception."""

    def end(self) -> None:
        """End the span; nothing to flush."""

    def __enter__(self) -> _NoOpSpan:
        return self

    def __exit__(self, *args: object) -> None: ...


class _NoOpTracer:
    """Tracer that hands out :class:`_NoOpSpan` instances."""

    def start_as_current_span(self, _name: str, **_kwargs: Any) -> _NoOpSpan:
        """Return a no-op span usable as a context manager."""
        return _NoOpSpan()

    @contextmanager
    def start_span(self, _name: str, **_kwargs: Any) -> Generator[_NoOpSpan]:
        """Yield a no-op span for the duration of the block."""
        yield _NoOpSpan()


class _NoOpMeter:
    """Meter that hands out discarding instruments."""

    def create_counter(self, _name: str, **_kw: Any) -> _NoOpCounter:
        """Return a counter that discards additions."""
        return _NoOpCounter()

    def create_histogram(self, _name: str, **_kw: Any) -> _NoOpHistogram:
        """Return a histogram that discards recordings."""
        return _NoOpHistogram()

    def create_up_down_counter(self, _name: str, **_kw: Any) -> _NoOpCounter:
        """Return an up-down counter that discards additions."""
        return _NoOpCounter()


class _NoOpCounter:
    """Counter instrument that discards every addition."""

    def add(self, _amount: int | float, _attributes: dict[str, Any] | None = None) -> None:
        """Discard a counter increment."""


class _NoOpHistogram:
    """Histogram instrument that discards every recording."""

    def record(self, _amount: int | float, _attributes: dict[str, Any] | None = None) -> None:
        """Discard a histogram observation."""


class _Metrics:
    """Lazily-created holder for the server's OpenTelemetry instruments.

    Instruments are built on first access rather than at import time, so
    :func:`setup_telemetry` can install a real meter before any are created.
    Falls back to the no-op instruments above when no backend is configured.
    """

    def __init__(self) -> None:
        self._tool_invocations: Any = None
        self._tool_errors: Any = None
        self._tool_duration: Any = None
        self._active_spans: Any = None

    @property
    def tool_invocations(self) -> Any:
        if self._tool_invocations is None:
            self._tool_invocations = meter.create_counter("resq.mcp.tool.invocations", unit="1")
        return self._tool_invocations

    @property
    def tool_errors(self) -> Any:
        if self._tool_errors is None:
            self._tool_errors = meter.create_counter("resq.mcp.tool.errors", unit="1")
        return self._tool_errors

    @property
    def tool_duration(self) -> Any:
        if self._tool_duration is None:
            self._tool_duration = meter.create_histogram("resq.mcp.tool.duration", unit="s")
        return self._tool_duration

    @property
    def active_spans(self) -> Any:
        if self._active_spans is None:
            self._active_spans = meter.create_up_down_counter("resq.mcp.spans.active", unit="1")
        return self._active_spans


metrics = _Metrics()


def trace(
    _func_or_name: Callable[P, R] | str | None = None,
    name: str | None = None,
    *,
    record_args: bool = False,
    record_result: bool = False,
) -> Any:
    """Instrument a function with an OpenTelemetry span."""
    # Bare @trace usage (no parentheses)
    if callable(_func_or_name):
        return _apply_trace(None, False, False, _func_or_name)

    # Called with arguments: @trace("name") or @trace(record_args=True)
    span_name = _func_or_name or name

    def decorator(func: Callable[P, R]) -> Any:
        return _apply_trace(span_name, record_args, record_result, func)

    return decorator


def _apply_trace(
    span_name: str | None,
    record_args: bool,
    record_result: bool,
    func: Callable[P, R],
) -> Any:
    """Wrap ``func`` in a span, choosing a sync or async wrapper to match it.

    Args:
        span_name: Explicit span name, or None to derive ``module.qualname``.
        record_args: Whether to attach sanitized keyword arguments as attributes.
        record_result: Whether to attach the (truncated) return value.
        func: The callable to instrument.

    Returns:
        A wrapper preserving ``func``'s signature that opens a span, records
        duration and error metrics, and re-raises any exception unchanged.
    """
    resolved_name = span_name or f"{func.__module__}.{func.__qualname__}"
    import inspect

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Await the wrapped coroutine inside an active span."""
            with tracer.start_as_current_span(resolved_name) as span_obj:
                metrics.active_spans.add(1)
                start = time.monotonic()
                try:
                    _set_entry_attrs(span_obj, func, record_args, kwargs)
                    result = await func(*args, **kwargs)
                    _set_exit_attrs(span_obj, result, record_result)
                    span_obj.set_status(StatusCode.OK)
                    return result  # type: ignore[no-any-return]
                except Exception as exc:
                    span_obj.set_status(StatusCode.ERROR, str(exc))
                    span_obj.record_exception(exc)
                    metrics.tool_errors.add(
                        1, {"tool": resolved_name, "error.type": type(exc).__name__}
                    )
                    raise
                finally:
                    metrics.tool_duration.record(time.monotonic() - start, {"tool": resolved_name})
                    metrics.tool_invocations.add(1, {"tool": resolved_name})
                    metrics.active_spans.add(-1)

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with tracer.start_as_current_span(resolved_name) as span_obj:
            metrics.active_spans.add(1)
            start = time.monotonic()
            try:
                _set_entry_attrs(span_obj, func, record_args, kwargs)
                result = func(*args, **kwargs)
                _set_exit_attrs(span_obj, result, record_result)
                span_obj.set_status(StatusCode.OK)
                return result
            except Exception as exc:
                span_obj.set_status(StatusCode.ERROR, str(exc))
                span_obj.record_exception(exc)
                metrics.tool_errors.add(
                    1, {"tool": resolved_name, "error.type": type(exc).__name__}
                )
                raise
            finally:
                metrics.tool_duration.record(time.monotonic() - start, {"tool": resolved_name})
                metrics.tool_invocations.add(1, {"tool": resolved_name})
                metrics.active_spans.add(-1)

    return sync_wrapper


def _set_entry_attrs(
    span_obj: Any,
    func: Callable[..., object],
    record_args: bool,
    kwargs: dict[str, Any],
) -> None:
    """Attach call-site attributes to a span as the wrapped function is entered.

    Always records ``code.function`` and ``code.namespace``. Keyword arguments
    are attached as ``resq.arg.*`` only when ``record_args`` is set, and are
    sanitized and truncated first so secrets and oversized values do not reach
    the exporter.
    """
    span_obj.set_attribute("code.function", func.__qualname__)
    span_obj.set_attribute("code.namespace", func.__module__)
    if record_args and kwargs:
        safe = _sanitize_attrs({f"resq.arg.{k}": _truncate(v) for k, v in kwargs.items()})
        for k, v in safe.items():
            span_obj.set_attribute(k, v)


def _set_exit_attrs(span_obj: Any, result: Any, record_result: bool) -> None:
    """Attach the wrapped function's return value to the span, if requested.

    No-ops when ``record_result`` is false or the result is None. The value is
    truncated so a large payload cannot bloat the span.
    """
    if record_result and result is not None:
        span_obj.set_attribute("resq.result", _truncate(result))


def _truncate(value: Any, max_len: int = 1024) -> str:
    """Stringify ``value``, capping it at ``max_len`` characters.

    Args:
        value: Any object; coerced with ``str()``.
        max_len: Maximum characters to keep before eliding.

    Returns:
        str: The string form, suffixed with "..." when it was shortened.
    """
    s = str(value)
    return s[:max_len] + "..." if len(s) > max_len else s


@contextmanager
def span(name: str, attributes: dict[str, Any] | None = None) -> Generator[Any]:
    """Open a named span around a block of code.

    Args:
        name: Span name.
        attributes: Optional attributes; sanitized before being attached.

    Yields:
        The active span, or a :class:`_NoOpSpan` when telemetry is disabled.

    Example:
        >>> with span("mission.plan", {"sector_id": "Sector-1"}):
        ...     ...
    """
    safe = _sanitize_attrs(attributes) if attributes else {}
    with tracer.start_as_current_span(name, attributes=safe) as s:
        yield s


def log_event(event: str, level: int = logging.INFO, **attrs: Any) -> None:
    """Emit a structured log record correlated with the active trace.

    Attributes are sanitized and the message redacted before emission, and the
    current ``trace_id``/``span_id`` are attached when a trace is active so log
    lines can be joined to spans in the backend.

    Args:
        event: Event name, used as the log message and the ``event`` field.
        level: Logging level (default ``logging.INFO``).
        **attrs: Extra structured fields.
    """
    safe = _sanitize_attrs(attrs)
    trace_ctx = _get_trace_context()
    extra = {**safe, **trace_ctx, "event": event}
    logger.log(level, _redact_log_message(event), extra=extra)


def _get_trace_context() -> dict[str, str]:
    """Return the active trace and span IDs as hex strings.

    Returns:
        dict[str, str]: ``{"trace_id": ..., "span_id": ...}`` when a span is
        active, otherwise an empty dict. Never raises — any SDK error yields {}.
    """
    if not _HAS_OTEL_SDK:
        return {}
    try:
        ctx = otel_trace.get_current_span().get_span_context()
        if ctx and ctx.trace_id:
            return {
                "trace_id": format(ctx.trace_id, "032x"),
                "span_id": format(ctx.span_id, "016x"),
            }
    except Exception:  # noqa: S110
        pass
    return {}


def shutdown_telemetry(timeout_ms: int = 5_000) -> None:
    """Flush and shut down the tracer and meter providers.

    Call once on server shutdown so buffered spans and metrics are exported
    rather than dropped. Invoked from the ``lifespan`` exit path in
    ``server.py``, after background tasks are cancelled.

    Safe to call unconditionally: returns immediately when the OpenTelemetry
    SDK is absent, and any exporter failure is logged rather than raised, so a
    misbehaving backend cannot break server shutdown.

    Args:
        timeout_ms: Milliseconds allowed for the meter provider to flush.
    """
    if not _HAS_OTEL_SDK:
        return
    try:
        provider = otel_trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
        mp = get_meter_provider()
        if hasattr(mp, "shutdown"):
            mp.shutdown(timeout_millis=timeout_ms)
    except Exception:
        logger.warning("Telemetry shutdown error", exc_info=True)
