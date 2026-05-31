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

"""Tests for the console entry point transport selection (issue #52).

``main()`` must honour ``RESQ_TRANSPORT``/``RESQ_HOST``/``RESQ_PORT`` so the
server can be deployed as an HTTP/SSE network service, not only as a
client-spawned stdio process.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import resq_mcp.server as server


class TestMainTransportSelection:
    """main() routes to the correct FastMCP transport based on settings."""

    def test_stdio_runs_without_host_or_port(self) -> None:
        """Default stdio transport calls mcp.run() with no host/port kwargs.

        stdio does not accept host/port; passing them would raise, so the
        default path must stay argument-free (preserves prior behaviour).
        """
        run = MagicMock()
        with (
            patch.object(server.mcp, "run", run),
            patch.object(server.settings, "TRANSPORT", "stdio"),
        ):
            server.main()

        run.assert_called_once_with()

    def test_http_transport_binds_host_and_port(self) -> None:
        """A network transport forwards transport, host, and port to mcp.run()."""
        run = MagicMock()
        with (
            patch.object(server.mcp, "run", run),
            patch.object(server.settings, "TRANSPORT", "http"),
            patch.object(server.settings, "HOST", "127.0.0.1"),
            patch.object(server.settings, "PORT", 9001),
        ):
            server.main()

        run.assert_called_once_with(transport="http", host="127.0.0.1", port=9001)

    def test_sse_transport_binds_host_and_port(self) -> None:
        """The sse transport is also wired to host/port."""
        run = MagicMock()
        with (
            patch.object(server.mcp, "run", run),
            patch.object(server.settings, "TRANSPORT", "sse"),
            patch.object(server.settings, "HOST", "0.0.0.0"),
            patch.object(server.settings, "PORT", 8000),
        ):
            server.main()

        run.assert_called_once_with(transport="sse", host="0.0.0.0", port=8000)

    def test_main_validates_environment_before_running(self) -> None:
        """validate_environment() runs before the server starts."""
        run = MagicMock()
        with (
            patch.object(server.mcp, "run", run),
            patch.object(server.settings, "TRANSPORT", "stdio"),
            patch("resq_mcp.server.validate_environment") as validate,
        ):
            server.main()

        validate.assert_called_once()
        run.assert_called_once_with()


class TestModuleEntryPoint:
    """`python -m resq_mcp` must go through main(), not a bare mcp.run()."""

    def test_dunder_main_delegates_to_main(self) -> None:
        """__main__ imports the same main() that applies transport handling."""
        import resq_mcp.__main__ as dunder_main

        assert dunder_main.main is server.main
