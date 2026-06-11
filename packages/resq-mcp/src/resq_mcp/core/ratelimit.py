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

"""Per-tool rate limiting for the ResQ MCP server.

Implements the "Denial of service and fatigue-based techniques" mitigation from
NSA PP-26-1834 (May 2026): MCP servers acting as agent orchestrators are
susceptible to prompt storms and recursive task requests that exhaust resources.
A sliding-window limiter keyed per tool bounds the call rate so a single tool
cannot be hammered into a denial-of-service condition.

The limiter is process-local and in-memory. A multi-replica production deployment
would back it with a shared store (e.g. Redis) so limits hold across instances.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from resq_mcp.core.config import settings


class RateLimitExceeded(Exception):
    """Raised when a tool exceeds its allowed call rate within the window."""

    def __init__(self, tool: str, limit: int, window_seconds: int) -> None:
        self.tool = tool
        self.limit = limit
        self.window_seconds = window_seconds
        super().__init__(
            f"Rate limit exceeded for '{tool}': at most {limit} calls per "
            f"{window_seconds}s are permitted. Slow down and retry shortly."
        )


class RateLimiter:
    """Thread-safe sliding-window rate limiter keyed by an arbitrary string.

    Each key (typically a tool name) tracks the monotonic timestamps of recent
    calls. On ``check`` the window is pruned and the call rejected if the number
    of in-window calls has reached the limit.
    """

    def __init__(self, max_calls: int, window_seconds: int) -> None:
        """Initialise the limiter.

        Args:
            max_calls: Maximum number of calls permitted per key per window.
            window_seconds: Width of the sliding window, in seconds.
        """
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, *, now: float | None = None) -> None:
        """Record a call for ``key`` and raise if it breaches the limit.

        Args:
            key: The bucket key (e.g. a tool name).
            now: Optional monotonic timestamp override (for deterministic tests).

        Raises:
            RateLimitExceeded: If the limit for ``key`` has already been reached
                within the current window. The call is *not* recorded in that case.
        """
        current = time.monotonic() if now is None else now
        cutoff = current - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.max_calls:
                raise RateLimitExceeded(key, self.max_calls, self.window_seconds)
            events.append(current)

    def reset(self, key: str | None = None) -> None:
        """Clear recorded calls for one key, or all keys when ``key`` is ``None``."""
        with self._lock:
            if key is None:
                self._events.clear()
            else:
                self._events.pop(key, None)


# Module-level singleton configured from settings. Tests reset it between cases
# via the autouse fixture in tests/conftest.py.
rate_limiter = RateLimiter(
    max_calls=settings.RATE_LIMIT_MAX_CALLS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


def enforce_rate_limit(tool: str) -> None:
    """Enforce the configured per-tool rate limit, honouring the feature flag.

    Args:
        tool: The tool name used as the limiter key.

    Raises:
        RateLimitExceeded: If the tool has exceeded its limit and rate limiting
            is enabled (``RESQ_RATE_LIMIT_ENABLED``).
    """
    if not settings.RATE_LIMIT_ENABLED:
        return
    rate_limiter.check(tool)
