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

"""Tests for the per-tool sliding-window rate limiter."""

from __future__ import annotations

import pytest

from resq_mcp.core.ratelimit import RateLimiter, RateLimitExceeded, enforce_rate_limit


class TestRateLimiter:
    def test_allows_up_to_limit_then_blocks(self) -> None:
        limiter = RateLimiter(max_calls=3, window_seconds=60)
        for _ in range(3):
            limiter.check("tool")
        with pytest.raises(RateLimitExceeded) as exc:
            limiter.check("tool")
        assert exc.value.tool == "tool"
        assert exc.value.limit == 3

    def test_window_slides_with_injected_clock(self) -> None:
        limiter = RateLimiter(max_calls=2, window_seconds=10)
        limiter.check("t", now=100.0)
        limiter.check("t", now=105.0)
        # Third call within the window is rejected...
        with pytest.raises(RateLimitExceeded):
            limiter.check("t", now=109.0)
        # ...but once the first two calls age out, capacity frees up again.
        limiter.check("t", now=116.0)

    def test_keys_are_isolated(self) -> None:
        limiter = RateLimiter(max_calls=1, window_seconds=60)
        limiter.check("tool_a")
        limiter.check("tool_b")  # different key, not blocked
        with pytest.raises(RateLimitExceeded):
            limiter.check("tool_a")

    def test_reset_clears_one_key(self) -> None:
        limiter = RateLimiter(max_calls=1, window_seconds=60)
        limiter.check("tool")
        limiter.reset("tool")
        limiter.check("tool")  # no raise after reset

    def test_rejected_call_is_not_recorded(self) -> None:
        limiter = RateLimiter(max_calls=1, window_seconds=60)
        limiter.check("tool", now=1.0)
        with pytest.raises(RateLimitExceeded):
            limiter.check("tool", now=2.0)
        # The rejected call must not consume a slot; after the window it succeeds.
        limiter.check("tool", now=100.0)


class TestEnforceRateLimit:
    def test_noop_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from resq_mcp.core import ratelimit

        monkeypatch.setattr(ratelimit.settings, "RATE_LIMIT_ENABLED", False)
        monkeypatch.setattr(ratelimit.rate_limiter, "max_calls", 1)
        # Even far past the limit, a disabled limiter never raises.
        for _ in range(5):
            enforce_rate_limit("noisy_tool")

    def test_enforces_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from resq_mcp.core import ratelimit

        monkeypatch.setattr(ratelimit.settings, "RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr(ratelimit.rate_limiter, "max_calls", 2)
        enforce_rate_limit("tool")
        enforce_rate_limit("tool")
        with pytest.raises(RateLimitExceeded):
            enforce_rate_limit("tool")
