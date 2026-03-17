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

"""ResQ MCP Server - Model Context Protocol server for disaster response coordination.

This module provides the main FastMCP server implementation for ResQ, offering:
- Simulation management via resources and tools
- Drone fleet status and deployment
- Incident validation and response planning

The server uses a lifespan context manager to manage background tasks for
simulation processing and notification delivery.
"""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here
# because FastMCP/Pydantic needs to resolve the type annotations at runtime
# for tool parameter validation. Using PEP 563 postponed annotations causes
# NameError when FastMCP tries to evaluate the forward references.

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from resq_mcp.core.config import settings
from resq_mcp.core.telemetry import setup_telemetry

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger("resq-mcp")

# Initialize Telemetry
setup_telemetry()

# --- Mock Data Store ---
simulations: "dict[str, dict[str, Any]]" = {}


@asynccontextmanager
async def lifespan(server: FastMCP) -> "AsyncGenerator[None, None]":
    """Lifespan context manager for the MCP server with background tasks.

    Manages the lifecycle of background processing tasks that run for the
    duration of the server. Ensures clean startup and shutdown with proper
    task cancellation and resource cleanup.

    Background Tasks Started:
        - simulation_processor: Mock simulation state machine that transitions
          simulations from pending -> processing -> completed and sends SSE
          notifications to subscribed clients.

    Lifecycle:
        1. Startup: Log initialization, create background tasks
        2. Running: Yield control to FastMCP server
        3. Shutdown: Cancel tasks, suppress CancelledError, log shutdown

    Args:
        server: The FastMCP server instance for notification dispatch.

    Yields:
        None: Control returns to FastMCP for request handling.

    Note:
        In production, background tasks would interface with actual
        simulation clusters, message queues (Redis/RabbitMQ), and
        maintain persistent connections to drone telemetry streams.
    """
    logger.info("Starting resQ MCP Server...")
    task = asyncio.create_task(simulation_processor(server))
    yield
    logger.info("Shutting down resQ MCP Server...")
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


# Initialize FastMCP
mcp = FastMCP(
    settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


# --- Background Tasks ---


async def simulation_processor(server: FastMCP) -> None:
    """Background processor for simulation state transitions and notifications.

    Simulates async physics simulation job processing with state machine:
    - pending -> processing (immediate, 50% progress)
    - processing -> completed (after 3s delay, 100% progress, generates result URL)

    Notifications:
        Sends SSE resource update notifications to clients subscribed to
        resq://simulations/{sim_id} whenever simulation state changes.

    Args:
        server: FastMCP server instance for notification dispatch.

    State Machine:
        pending: Job queued, waiting for processing
          | (2s poll)
        processing: Simulation running (progress=0.5)
          | (3s delay)
        completed: Results available (progress=1.0, result_url set)

    Notification Protocol:
        Uses FastMCP resource update notifications:
        - Clients subscribe to simulation URI
        - Server pushes SSE events on state change
        - Clients can poll or wait for completion

    Error Handling:
        Notification failures are logged at DEBUG level but don't crash
        the processor. Simulation state updates continue regardless.

    Note:
        Production would replace this with actual job queue integration
        (Celery/RQ) and Unity/Unreal Engine status polling.
    """
    while True:
        await asyncio.sleep(2)
        for sim_id, data in list(simulations.items()):
            if data["status"] == "pending":
                data["status"] = "processing"
                data["progress"] = 0.5
                logger.info("Simulation %s moved to PROCESSING", sim_id)
                try:
                    await server.notify_resource_updated(f"resq://simulations/{sim_id}")  # type: ignore[attr-defined]  # valid FastMCP API, missing from type stubs
                except Exception:
                    logger.debug("Failed to notify for %s", sim_id, exc_info=True)

            elif data["status"] == "processing":
                await asyncio.sleep(3)
                data["status"] = "completed"
                data["progress"] = 1.0
                data["result_url"] = f"neofs://sim_results/{sim_id}.json"
                logger.info("Simulation %s COMPLETED", sim_id)
                try:
                    await server.notify_resource_updated(f"resq://simulations/{sim_id}")  # type: ignore[attr-defined]  # valid FastMCP API, missing from type stubs
                except Exception:
                    logger.debug("Failed to notify for %s", sim_id, exc_info=True)


# Register tools, resources, and prompts
import resq_mcp.dtsop.tools  # noqa: E402
import resq_mcp.hce.tools  # noqa: E402
import resq_mcp.prompts  # noqa: E402
import resq_mcp.resources  # noqa: F401, E402


def main() -> None:
    """Console script entry point for the ResQ MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
