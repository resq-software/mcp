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

"""Tests for security utilities."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException


class TestVerifyApiKey:
    """Tests for the verify_api_key function."""

    def _make_request(self, auth_header: str | None = None) -> MagicMock:
        """Create a mock FastAPI Request with optional Authorization header."""
        request = MagicMock()
        headers: dict[str, str] = {}
        if auth_header is not None:
            headers["Authorization"] = auth_header
        request.headers = headers
        return request

    def test_missing_auth_header_raises_401(self) -> None:
        from resq_mcp.core.security import verify_api_key

        request = self._make_request()
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        assert exc_info.value.status_code == 401
        assert "Missing" in str(exc_info.value.detail)

    def test_invalid_scheme_raises_401(self) -> None:
        from resq_mcp.core.security import verify_api_key

        request = self._make_request("Basic some-token")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        assert exc_info.value.status_code == 401
        assert "Scheme" in str(exc_info.value.detail)

    def test_invalid_token_raises_403(self) -> None:
        from resq_mcp.core.security import verify_api_key

        request = self._make_request("Bearer wrong-token-value")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        assert exc_info.value.status_code == 403
        assert "Invalid API Key" in str(exc_info.value.detail)

    def test_valid_token_returns_token(self) -> None:
        from resq_mcp.core.config import settings
        from resq_mcp.core.security import verify_api_key

        valid_token = settings.API_KEY
        request = self._make_request(f"Bearer {valid_token}")
        result = verify_api_key(request)
        assert result == valid_token

    def test_bearer_scheme_is_case_insensitive(self) -> None:
        from resq_mcp.core.config import settings
        from resq_mcp.core.security import verify_api_key

        valid_token = settings.API_KEY
        request = self._make_request(f"BEARER {valid_token}")
        result = verify_api_key(request)
        assert result == valid_token

    def test_empty_bearer_value_raises_403(self) -> None:
        from resq_mcp.core.security import verify_api_key

        request = self._make_request("Bearer ")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        assert exc_info.value.status_code == 403

    def test_multi_space_separator(self) -> None:
        from resq_mcp.core.config import settings
        from resq_mcp.core.security import verify_api_key

        request = self._make_request(f"Bearer  {settings.API_KEY}")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        assert exc_info.value.status_code == 403

    def test_only_scheme_no_space(self) -> None:
        from resq_mcp.core.security import verify_api_key

        request = self._make_request("Bearer")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        assert exc_info.value.status_code == 403


class TestKeyRing:
    """Tests for bearer-token rotation with a grace window."""

    def test_active_token_verifies(self) -> None:
        from resq_mcp.core.security import KeyRing

        ring = KeyRing(active="primary-token")
        assert ring.active == "primary-token"
        assert ring.verify("primary-token") is True
        assert ring.verify("nope") is False
        assert ring.verify("") is False

    def test_rotation_keeps_previous_valid_during_grace(self) -> None:
        from resq_mcp.core.security import KeyRing

        ring = KeyRing(active="old-token", grace_seconds=3600)
        new = ring.rotate("new-token")
        assert new == "new-token"
        assert ring.active == "new-token"
        assert ring.verify("new-token") is True
        # The rotated-out token stays valid within the grace window.
        assert ring.verify("old-token") is True

    def test_previous_token_expires_after_grace(self) -> None:
        from resq_mcp.core.security import KeyRing

        # Zero-second grace means the previous token is invalid immediately.
        ring = KeyRing(active="old-token", grace_seconds=0)
        ring.rotate("new-token")
        assert ring.verify("new-token") is True
        assert ring.verify("old-token") is False

    def test_rotate_generates_token_when_none_supplied(self) -> None:
        from resq_mcp.core.security import KeyRing

        ring = KeyRing(active="seed")
        generated = ring.rotate()
        assert generated != "seed"
        assert len(generated) >= 32
        assert ring.verify(generated) is True

    def test_seeded_previous_token_is_honoured(self) -> None:
        from resq_mcp.core.security import KeyRing

        ring = KeyRing(active="active", previous="prior", grace_seconds=3600)
        assert ring.verify("prior") is True


class TestRequireMutationAllowed:
    """Tests for the Safe Mode mutation gate."""

    def test_raises_when_safe_mode_enabled(self) -> None:
        from fastmcp.exceptions import FastMCPError

        from resq_mcp.core import security

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(security.settings, "SAFE_MODE", True)
            with pytest.raises(FastMCPError, match="RESQ_SAFE_MODE"):
                security.require_mutation_allowed("run_simulation")

    def test_passes_when_safe_mode_disabled(self) -> None:
        from resq_mcp.core import security

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(security.settings, "SAFE_MODE", False)
            security.require_mutation_allowed("run_simulation")
