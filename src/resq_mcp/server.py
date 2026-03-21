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
import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from resq_mcp.core.config import settings, validate_environment
from resq_mcp.core.telemetry import setup_telemetry

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger("resq-mcp")

# Initialize Telemetry
setup_telemetry()

# --- Capacity & TTL limits ---
MAX_SIMULATIONS: int = 500
MAX_INCIDENTS: int = 1000
MAX_MISSIONS: int = 200  # active missions per session
COMPLETED_TTL_SECONDS: int = 300  # evict completed sims after 5 minutes
FAILED_TTL_SECONDS: int = 60  # evict failed sims sooner
INCIDENT_TTL_SECONDS: int = 3600  # evict rejected incident records after 1 hour
CONFIRMED_INCIDENT_TTL_SECONDS: int = 86400  # confirmed incidents retained for 24h
MISSION_TTL_SECONDS: int = 7200  # evict stale mission records after 2h

# --- Mock Data Store ---
# NOTE: created_at uses wall-clock ISO strings (human-visible in resource output).
#       completed_at / failed_at / validated_at_mono use time.monotonic() floats
#       (internal TTL bookkeeping only; not exposed to callers).
simulations: "dict[str, dict[str, Any]]" = {}
incidents: "dict[str, dict[str, Any]]" = {}
missions: "dict[str, dict[str, Any]]" = {}  # keyed by drone_id

# Maps sim_id -> active asyncio.Task, serving as both a strong task reference
# (prevents GC) and the authoritative record of which sims have completion tasks
# (used for orphan recovery in the poll loop).  Single structure replaces the
# prior _sim_tasks set + _active_processing set dual-channel pattern.
_processing_tasks: "dict[str, asyncio.Task[None]]" = {}


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
    # Cancel any in-flight per-simulation tasks so they don't write to the
    # (now-stale) simulations dict after the processor has stopped.
    for sim_task in list(_processing_tasks.values()):
        sim_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sim_task


# Initialize FastMCP
mcp = FastMCP(
    settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


# --- Background Tasks ---


def _cleanup_state() -> None:
    """Evict stale entries from all in-memory stores.

    Simulations:
        - completed → evict after COMPLETED_TTL_SECONDS
        - failed    → evict after FAILED_TTL_SECONDS (shorter; clients should not retry)
    Incidents:
        - rejected  → evict after INCIDENT_TTL_SECONDS (1h — false positives, low value)
        - confirmed → evict after CONFIRMED_INCIDENT_TTL_SECONDS (24h — must persist
                      long enough for get_deployment_strategy to cross-validate them)
    Missions:
        - evict after MISSION_TTL_SECONDS (2h), freeing the drone for new dispatches.
    """
    now = time.monotonic()

    for sid, data in list(simulations.items()):
        status = data.get("status")
        if status == "completed" and now - data.get("completed_at", now) > COMPLETED_TTL_SECONDS:
            del simulations[sid]
            logger.debug("Evicted completed simulation %s", sid)
        elif status == "failed" and now - data.get("failed_at", now) > FAILED_TTL_SECONDS:
            del simulations[sid]
            logger.debug("Evicted failed simulation %s", sid)

    for iid, data in list(incidents.items()):
        age = now - data.get("validated_at_mono", now)
        # Rejected incidents (false positives) are low-value — evict quickly.
        # Confirmed incidents must persist so get_deployment_strategy can validate
        # them across a full response workflow; give them a 24h window.
        if data.get("is_confirmed") is False and age > INCIDENT_TTL_SECONDS:
            del incidents[iid]
            logger.debug("Evicted rejected incident %s", iid)
        elif data.get("is_confirmed") is True and age > CONFIRMED_INCIDENT_TTL_SECONDS:
            del incidents[iid]
            logger.debug("Evicted old confirmed incident %s", iid)

    for did, data in list(missions.items()):
        if now - data.get("dispatched_at_mono", now) > MISSION_TTL_SECONDS:
            del missions[did]
            logger.debug("Evicted stale mission for drone %s", did)


async def _process_simulation(server: FastMCP, sim_id: str, data: "dict[str, Any]") -> None:
    """Async task: complete one simulation after a processing delay.

    Runs concurrently per simulation so the main poll loop is never blocked
    by a single job's 3-second processing window (fixes the sequential-sleep DoS).

    State Machine:
        processing -> completed (after 3 s, sets completed_at for TTL eviction)
        processing -> failed    (on CancelledError — sets failed_at for TTL eviction,
                                 clears progress so clients see 0% not a stuck 50%)
    """
    try:
        await asyncio.sleep(3)
        # Guard: entry may have been evicted while we slept
        if simulations.get(sim_id) is not data:
            return
        data["status"] = "completed"
        data["progress"] = 1.0
        data["result_url"] = f"neofs://sim_results/{sim_id}.json"
        data["completed_at"] = time.monotonic()  # monotonic float; TTL use only
        logger.info("Simulation %s COMPLETED", sim_id)
        try:
            await server.notify_resource_updated(f"resq://simulations/{sim_id}")  # type: ignore[attr-defined]
        except Exception:
            logger.debug("Failed to notify for %s", sim_id, exc_info=True)
    except asyncio.CancelledError:
        if simulations.get(sim_id) is data:
            data["status"] = "failed"
            data["progress"] = 0.0  # clear stuck 50% so clients see correct state
            data["failed_at"] = time.monotonic()
        raise
    finally:
        _processing_tasks.pop(sim_id, None)


async def simulation_processor(server: FastMCP) -> None:
    """Background processor for simulation state transitions and notifications.

    Polls for pending simulations every 2 s and spawns an independent async
    task per simulation so that no single job's delay blocks the others.

    State Machine:
        pending    -> processing (immediate, 50% progress, task spawned)
        processing -> completed  (after 3 s inside _process_simulation)
        processing -> failed     (on server shutdown mid-run)

    Notifications:
        SSE resource update notifications are sent on each state transition.

    Note:
        Production would replace this with a real job queue integration
        (Celery / RQ) and Unity/Unreal Engine status polling.
    """
    while True:
        await asyncio.sleep(2)
        _cleanup_state()
        for sim_id, data in list(simulations.items()):
            if data["status"] == "pending":
                data["status"] = "processing"
                data["progress"] = 0.5
                logger.info("Simulation %s moved to PROCESSING", sim_id)
                task = asyncio.create_task(_process_simulation(server, sim_id, data))
                _processing_tasks[sim_id] = task
                try:
                    await server.notify_resource_updated(f"resq://simulations/{sim_id}")  # type: ignore[attr-defined]
                except Exception:
                    logger.debug("Failed to notify for %s", sim_id, exc_info=True)
            elif data["status"] == "processing" and sim_id not in _processing_tasks:
                # Orphan recovery: sim is "processing" with no active task
                # (e.g. created directly in tests or after partial-state replay).
                logger.debug("Recovering orphaned processing simulation %s", sim_id)
                task = asyncio.create_task(_process_simulation(server, sim_id, data))
                _processing_tasks[sim_id] = task


# Register tools, resources, and prompts
import resq_mcp.dtsop.tools  # noqa: E402
import resq_mcp.hce.tools  # noqa: E402
import resq_mcp.prompts  # noqa: E402
import resq_mcp.resources  # noqa: F401, E402


def main() -> None:
    """Console script entry point for the ResQ MCP server."""
    validate_environment()
    mcp.run()


if __name__ == "__main__":
    main()
