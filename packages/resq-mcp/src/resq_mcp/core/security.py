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

"""Security utilities for the ResQ MCP server.

Provides API key verification for authenticated endpoints using FastAPI's
HTTPBearer security scheme for token extraction.

Note:
    This implementation uses a simple comparison against the configured API_KEY.
    Production deployments should use secure token storage and validation.
"""

from __future__ import annotations

import logging
import secrets
import threading
import time

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from fastmcp.exceptions import FastMCPError

from resq_mcp.core.config import settings

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


class KeyRing:
    """Holds the active bearer token plus a grace-windowed previous token.

    Supports zero-downtime rotation: :meth:`rotate` promotes a freshly generated
    (or supplied) token to active and demotes the prior active token to a
    ``previous`` slot that stays valid for ``grace_seconds``. In-flight clients
    can keep using the old token until they pick up the new one, after which the
    previous token silently expires. This addresses the token-lifecycle gaps
    (rotation/revocation) flagged in NSA PP-26-1834.

    All comparisons use :func:`secrets.compare_digest` for constant-time matching.
    """

    def __init__(self, active: str, previous: str = "", grace_seconds: int = 3600) -> None:
        """Initialise the ring.

        Args:
            active: The currently active bearer token.
            previous: An optional previously active token to honour during a grace
                window (empty disables the previous slot).
            grace_seconds: How long a rotated-out token remains acceptable.
        """
        self._active = active
        self._previous = previous or ""
        self._grace_seconds = grace_seconds
        self._previous_expires_at: float | None = (
            time.monotonic() + grace_seconds if self._previous else None
        )
        self._lock = threading.Lock()

    @property
    def active(self) -> str:
        """The currently active bearer token."""
        return self._active

    def rotate(self, new_key: str | None = None) -> str:
        """Rotate the active token, keeping the prior one valid during the grace window.

        Args:
            new_key: The replacement token. When omitted, a cryptographically
                secure URL-safe token is generated.

        Returns:
            The new active token.
        """
        with self._lock:
            new = new_key or secrets.token_urlsafe(32)
            self._previous = self._active
            self._previous_expires_at = time.monotonic() + self._grace_seconds
            self._active = new
            logger.info("Bearer token rotated; previous token valid for %ds", self._grace_seconds)
            return new

    def verify(self, token: str) -> bool:
        """Return True if ``token`` matches the active or (unexpired) previous token.

        Reads are taken under the lock so a concurrent :meth:`rotate` cannot expose
        a torn view of the active/previous slots (which would transiently 403 a
        valid token).
        """
        if not token:
            return False
        with self._lock:
            if secrets.compare_digest(token, self._active):
                return True
            deadline = self._previous_expires_at
            if self._previous and deadline is not None and time.monotonic() < deadline:
                return secrets.compare_digest(token, self._previous)
        return False


#: Process-wide key ring seeded from configuration. Rotation at runtime is done
#: via ``key_ring.rotate(...)`` (e.g. from an operator endpoint or signal handler).
key_ring = KeyRing(
    active=settings.API_KEY,
    previous=settings.API_KEY_PREVIOUS,
    grace_seconds=settings.API_KEY_GRACE_SECONDS,
)


def require_mutation_allowed(action: str) -> None:
    """Block side-effecting tools while Safe Mode is enabled.

    Safe Mode (``RESQ_SAFE_MODE=true``) is the secure default. It lets agents plan
    and reason over high-impact tools without triggering real-world consequences —
    the confused-deputy mitigation in NSA PP-26-1834. Disable it deliberately
    (``RESQ_SAFE_MODE=false``) only when autonomous execution is intended.

    Args:
        action: The mutating tool name, used in the error message.

    Raises:
        FastMCPError: If Safe Mode is enabled.
    """
    if settings.SAFE_MODE:
        raise FastMCPError(
            f"Refusing to execute mutating tool '{action}': RESQ_SAFE_MODE is enabled "
            "(the secure default). Set RESQ_SAFE_MODE=false to permit side-effecting "
            "operations such as starting simulations or dispatching drones."
        )


def verify_api_key(request: Request) -> str:
    """Verify the Bearer token against the configured API_KEY.

    Used as a dependency for SSE endpoints if wrapping in FastAPI.
    For FastMCP's SSE adapter, authentication may need to be handled
    at the deployment level (Ingress/Gateway) for strict OAuth.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The validated API token.

    Raises:
        HTTPException: 401 if missing/invalid auth scheme, 403 if invalid key.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        if settings.DEBUG:
            logger.warning("No Authorization header found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header",
        )

    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authentication Scheme",
        )

    if not key_ring.verify(token):
        logger.warning("Invalid token attempt from request")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return token
