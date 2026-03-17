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

"""Structured error handling for ResQ MCP tools.

Provides consistent, AI-client-friendly error responses with actionable
context. Inspired by Archon MCP server error handling patterns.
"""

from __future__ import annotations

import json
from typing import Any


class MCPErrorFormatter:
    """Formats errors consistently for MCP AI clients."""

    @staticmethod
    def format_error(
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
        http_status: int | None = None,
    ) -> str:
        """Format a structured error response as JSON."""
        error_response: dict[str, Any] = {
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
            },
        }
        if details:
            error_response["error"]["details"] = details
        if suggestion:
            error_response["error"]["suggestion"] = suggestion
        if http_status:
            error_response["error"]["http_status"] = http_status
        return json.dumps(error_response)

    @staticmethod
    def from_exception(
        exception: Exception,
        operation: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Format error from a Python exception."""
        error_type = "unknown_error"
        suggestion = None
        if isinstance(exception, ValueError):
            error_type = "validation_error"
            suggestion = "Check that all input parameters are valid"
        elif isinstance(exception, KeyError):
            error_type = "missing_data"
            suggestion = "The requested resource was not found"
        elif isinstance(exception, TimeoutError):
            error_type = "timeout"
            suggestion = "The operation timed out. Try again"

        details: dict[str, Any] = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
        }
        if context:
            details["context"] = context
        return MCPErrorFormatter.format_error(
            error_type=error_type,
            message=f"Failed to {operation}: {exception}",
            details=details,
            suggestion=suggestion,
        )
