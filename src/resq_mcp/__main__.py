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

"""Command-line entry point for the ResQ MCP Server.

This module provides the main entry point for running the ResQ MCP server
directly from the command line:

    python -m resq_mcp

The server initializes:
    - FastMCP server with Model Context Protocol support
    - Three main subsystems (PDIE, DTSOP, HCE)
    - Background simulation processor
    - SSE notification system for resource subscriptions

Configuration:
    Settings loaded from environment variables (RESQ_*) or .env file.
    See config.py for available configuration options.

Default Settings:
    - Host: 0.0.0.0 (all interfaces)
    - Port: 8000
    - Debug: False
    - Safe Mode: True (side-effects disabled)

Usage:
    # Development:
    python -m resq_mcp

    # With custom config:
    RESQ_PORT=9000 RESQ_DEBUG=true python -m resq_mcp

    # Production:
    RESQ_SAFE_MODE=false RESQ_API_KEY=prod-token python -m resq_mcp

See Also:
    - server.py: Main server implementation
    - config.py: Configuration settings
    - README.md: Complete documentation
"""

from .server import mcp

if __name__ == "__main__":
    mcp.run()
