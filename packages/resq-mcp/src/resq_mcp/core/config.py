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

"""Configuration management for the ResQ MCP server.

Settings are loaded from environment variables with sensible defaults.
Use a .env file or export environment variables to override.

Environment variables:
    RESQ_PROJECT_NAME: Display name for the MCP server
    RESQ_VERSION: Version string for the server
    RESQ_DEBUG: Enable debug logging (true/false)
    RESQ_API_KEY: API key for authenticated endpoints
    RESQ_TRANSPORT: MCP transport — stdio (default), http, sse, or streamable-http
    RESQ_PORT: Port for HTTP/SSE server
    RESQ_HOST: Host to bind to (HTTP/SSE transports)
    RESQ_SAFE_MODE: If True, side-effecting tools are disabled or mocked safely
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

#: The shipped development fallback token. Treated as "unset" for any deployment
#: that requires real authentication (see :func:`validate_environment`).
DEFAULT_DEV_API_KEY = "resq-dev-token"

#: Transports that open a network listener and therefore must not run with the
#: default development token. ``stdio`` is excluded — it is spawned by a local
#: MCP client over the process's stdin/stdout and is not network-reachable.
NETWORK_TRANSPORTS: frozenset[str] = frozenset({"http", "sse", "streamable-http"})


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


class Settings(BaseSettings):
    """Application configuration via environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="RESQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Info
    PROJECT_NAME: str = "resQ MCP Server"
    VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, description="Enable debug logging")

    # Auth
    API_KEY: str = Field(
        default=DEFAULT_DEV_API_KEY,
        description="Active bearer token. Required (non-default) for network transports.",
    )
    API_KEY_PREVIOUS: str = Field(
        default="",
        description=(
            "Previously active bearer token, accepted during a rotation grace window "
            "so in-flight clients can migrate without a hard cutover. Empty = disabled."
        ),
    )
    API_KEY_GRACE_SECONDS: int = Field(
        default=3600,
        ge=0,
        description="Seconds a rotated-out (previous) bearer token remains valid.",
    )

    # Deployment
    TRANSPORT: Literal["stdio", "http", "sse", "streamable-http"] = Field(
        default="stdio",
        description=(
            "MCP transport. 'stdio' (default) is spawned by an MCP client; "
            "'http'/'sse'/'streamable-http' bind a network listener on HOST:PORT."
        ),
    )
    PORT: int = Field(default=8000, description="Port for HTTP/SSE server")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to (HTTP/SSE transports)")

    # Feature Flags
    SAFE_MODE: bool = Field(
        default=True,
        description="If True, side-effecting tools are disabled or mocked safely",
    )

    # Audit & Detection (NSA PP-26-1834: Instrument for logging and detection)
    AUDIT_ENABLED: bool = Field(
        default=True,
        description="Emit structured, hash-anchored audit records for tool invocations.",
    )

    # Rate Limiting (NSA PP-26-1834: Denial of service / fatigue mitigation)
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enforce per-tool call-rate limits to resist prompt storms.",
    )
    RATE_LIMIT_MAX_CALLS: int = Field(
        default=60,
        ge=1,
        description="Maximum calls per tool within the rate-limit window.",
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60,
        ge=1,
        description="Width of the per-tool rate-limit sliding window, in seconds.",
    )

    # Telemetry
    TELEMETRY_BACKEND: Literal["console", "jaeger", "otlp", "none"] = Field(
        default="none",
        description="Telemetry backend to use",
    )
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        description="OTLP exporter endpoint",
    )
    OTEL_SERVICE_NAME: str = Field(
        default="resq-mcp",
        description="Service name for telemetry",
    )


settings = Settings()


def validate_environment(require_api_key: bool = False) -> None:
    """Validate required environment variables at startup.

    This function performs fail-fast validation by raising ConfigurationError
    if any required environment variables are missing.

    Args:
        require_api_key: If True, API_KEY must be set and not be the default dev token.
            Authentication is *also* required automatically whenever a network
            transport (``http``/``sse``/``streamable-http``) is selected, since such
            transports expose a listener that random traffic can reach.

    Raises:
        ConfigurationError: If any required environment variable is missing or invalid.

    Example:
        >>> from resq_mcp.core.config import validate_environment
        >>> validate_environment(require_api_key=True)
    """
    s = settings

    # A network listener with the default dev token is an unauthenticated open
    # MCP server — exactly the exposure NSA PP-26-1834 warns about. Require a real
    # token for network transports even when the caller did not ask explicitly.
    auth_required = require_api_key or s.TRANSPORT in NETWORK_TRANSPORTS

    if auth_required and (not s.API_KEY or s.API_KEY == DEFAULT_DEV_API_KEY):
        raise ConfigurationError(
            "RESQ_API_KEY must be set to a non-default value when authentication is "
            f"required (transport={s.TRANSPORT!r}). Generate one with "
            '`python -c "import secrets; print(secrets.token_urlsafe(32))"` and set '
            "the RESQ_API_KEY environment variable."
        )
