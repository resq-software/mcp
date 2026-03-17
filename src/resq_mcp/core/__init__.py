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

"""Core cross-cutting utilities for the ResQ MCP server."""

from __future__ import annotations

from resq_mcp.core.config import ConfigurationError, Settings, settings, validate_environment
from resq_mcp.core.errors import MCPErrorFormatter
from resq_mcp.core.models import (
    Coordinates,
    DetectedObject,
    DisasterScenario,
    ErrorResponse,
    Sector,
)
from resq_mcp.core.security import verify_api_key
from resq_mcp.core.telemetry import setup_telemetry, trace
from resq_mcp.core.timeout import (
    TimeoutConfig,
    get_default_timeout,
    get_max_polling_attempts,
    get_polling_interval,
)

__all__ = [
    "ConfigurationError",
    "Coordinates",
    "DetectedObject",
    "DisasterScenario",
    "ErrorResponse",
    "MCPErrorFormatter",
    "Sector",
    "Settings",
    "TimeoutConfig",
    "get_default_timeout",
    "get_max_polling_attempts",
    "get_polling_interval",
    "settings",
    "setup_telemetry",
    "trace",
    "validate_environment",
    "verify_api_key",
]
