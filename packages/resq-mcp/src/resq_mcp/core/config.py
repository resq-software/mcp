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
        default="resq-dev-token",
        description="Bearer token for mock auth",
    )
    # TODO(wombocombo): API_KEY should be required in production - currently has dev fallback

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

    Raises:
        ConfigurationError: If any required environment variable is missing or invalid.

    Example:
        >>> from resq_mcp.core.config import validate_environment
        >>> validate_environment(require_api_key=True)
    """
    s = settings

    if require_api_key and (not s.API_KEY or s.API_KEY == "resq-dev-token"):
        raise ConfigurationError(
            "RESQ_API_KEY must be set to a non-default value in production. "
            "Please set the RESQ_API_KEY environment variable."
        )
