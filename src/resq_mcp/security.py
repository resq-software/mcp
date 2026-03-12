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

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from .config import settings

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


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

    if token != settings.API_KEY:
        logger.warning("Invalid token attempt: %s***", token[:4])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return token