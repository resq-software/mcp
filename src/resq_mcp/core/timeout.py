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

"""Centralized timeout configuration for ResQ MCP server.

Provides consistent, env-var-configurable timeout values across all tools.
Inspired by Archon MCP server timeout patterns.

Environment variables:
    RESQ_REQUEST_TIMEOUT: Total request timeout in seconds (default: 30)
    RESQ_CONNECT_TIMEOUT: Connection timeout in seconds (default: 5)
    RESQ_READ_TIMEOUT: Read timeout in seconds (default: 20)
    RESQ_POLLING_BASE_INTERVAL: Base polling interval in seconds (default: 1)
    RESQ_POLLING_MAX_INTERVAL: Max polling interval in seconds (default: 5)
    RESQ_MAX_POLLING_ATTEMPTS: Max polling attempts (default: 30)
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeoutConfig:
    """Immutable timeout configuration."""

    total: float
    connect: float
    read: float


def _safe_float(env_var: str, default: str) -> float:
    """Parse a positive float from an env var, falling back to default."""
    try:
        val = float(os.getenv(env_var, default))
    except (ValueError, TypeError):
        val = float(default)
    import math

    if val <= 0 or math.isnan(val) or math.isinf(val):
        return float(default)
    return val


def get_default_timeout() -> TimeoutConfig:
    """Get default timeout configuration from environment or defaults."""
    return TimeoutConfig(
        total=_safe_float("RESQ_REQUEST_TIMEOUT", "30.0"),
        connect=_safe_float("RESQ_CONNECT_TIMEOUT", "5.0"),
        read=_safe_float("RESQ_READ_TIMEOUT", "20.0"),
    )


def get_max_polling_attempts() -> int:
    """Get maximum number of polling attempts."""
    try:
        return int(os.getenv("RESQ_MAX_POLLING_ATTEMPTS", "30"))
    except ValueError:
        return 30


def get_polling_interval(attempt: int) -> float:
    """Get polling interval with exponential backoff.

    Args:
        attempt: Current attempt number (0-based).

    Returns:
        Sleep interval in seconds.
    """
    base = _safe_float("RESQ_POLLING_BASE_INTERVAL", "1.0")
    cap = _safe_float("RESQ_POLLING_MAX_INTERVAL", "5.0")
    return float(min(base * (2**attempt), cap))
