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

"""Telemetry setup for the ResQ MCP server.

Provides initialization hooks for OpenTelemetry tracing and metrics.
Currently operates in no-op mode with structured logging as a fallback.

Future integration path:
    1. Install: opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp
    2. Configure TracerProvider with appropriate exporters
    3. Configure MeterProvider for Prometheus metrics
    4. Add trace decorators to key operations
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import settings

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    F = TypeVar("F", bound=Callable[..., object])

logger = logging.getLogger(__name__)


def setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing and metrics.

    Currently operates in no-op mode. When DEBUG is enabled, logs the
    initialization for visibility.
    """
    if settings.DEBUG:
        logger.info("Telemetry hooks initialized (no-op mode)")


def trace(name: str | None = None) -> Callable[[F], F]:
    """Decorator stub for tracing function execution.

    Args:
        name: Optional span name. Defaults to the function name.

    Returns:
        A no-op decorator that returns the original function.

    Example:
        @trace("custom.operation.name")
        def my_function():
            ...
    """
    del name  # Unused in no-op mode

    def decorator(func: F) -> F:
        return func

    return decorator