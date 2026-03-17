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

"""Unit tests for the config module."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from resq_mcp.config import Settings


class TestSettings:
    """Tests for the Settings configuration class."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        settings = Settings()

        assert settings.PROJECT_NAME == "resQ MCP Server"
        assert settings.VERSION == "0.1.0"
        assert settings.DEBUG is False
        assert settings.SAFE_MODE is True

    def test_env_prefix(self) -> None:
        """Test that RESQ_ prefix is used for environment variables."""
        with patch.dict(os.environ, {"RESQ_DEBUG": "true"}):
            settings = Settings()
            assert settings.DEBUG is True

    def test_debug_mode_can_be_enabled(self) -> None:
        """Test that debug mode can be enabled via environment."""
        with patch.dict(os.environ, {"RESQ_DEBUG": "true"}, clear=False):
            settings = Settings()
            assert settings.DEBUG is True

    def test_custom_port(self) -> None:
        """Test that custom port can be set."""
        with patch.dict(os.environ, {"RESQ_PORT": "9000"}):
            settings = Settings()
            assert settings.PORT == 9000

    def test_custom_api_key(self) -> None:
        """Test that custom API key can be set."""
        with patch.dict(os.environ, {"RESQ_API_KEY": "custom-token"}):
            settings = Settings()
            assert settings.API_KEY == "custom-token"

    def test_safe_mode_can_be_disabled(self) -> None:
        """Test that safe mode can be disabled."""
        with patch.dict(os.environ, {"RESQ_SAFE_MODE": "false"}):
            settings = Settings()
            assert settings.SAFE_MODE is False


class TestValidateEnvironment:
    """Tests for the validate_environment function."""

    def test_require_api_key_raises_with_default_token(self) -> None:
        """Default dev token raises ConfigurationError."""
        from resq_mcp.config import ConfigurationError, validate_environment

        with pytest.raises(ConfigurationError, match="non-default"):
            validate_environment(require_api_key=True)

    def test_require_api_key_raises_with_empty_string(self) -> None:
        """Empty API key raises ConfigurationError."""
        from resq_mcp.config import ConfigurationError, settings, validate_environment

        with (
            patch.object(settings, "API_KEY", ""),
            pytest.raises(ConfigurationError, match="RESQ_API_KEY"),
        ):
            validate_environment(require_api_key=True)

    def test_require_api_key_passes_with_custom_token(self) -> None:
        """Custom API key passes validation."""
        from resq_mcp.config import settings, validate_environment

        with patch.object(settings, "API_KEY", "my-production-token-123"):
            validate_environment(require_api_key=True)

    def test_no_require_api_key_passes_with_default(self) -> None:
        """Validation passes when api key not required."""
        from resq_mcp.config import validate_environment

        validate_environment(require_api_key=False)
