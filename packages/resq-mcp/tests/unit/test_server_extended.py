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

"""Extended tests for server module — lifespan, processing, capacity."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.exceptions import FastMCPError

from resq_mcp.server import (
    _process_simulation,
    _processing_tasks,
    lifespan,
    simulations,
)


@pytest.fixture(autouse=True)
def clear_state():
    simulations.clear()
    _processing_tasks.clear()
    yield
    simulations.clear()
    _processing_tasks.clear()


class TestProcessSimulation:
    @pytest.mark.asyncio
    async def test_completed_simulation(self) -> None:
        server = AsyncMock()
        server.notify_resource_updated = AsyncMock()
        sim_id = "SIM-001"
        data = {"status": "processing", "progress": 0.5}
        simulations[sim_id] = data

        await _process_simulation(server, sim_id, data)

        assert data["status"] == "completed"
        assert data["progress"] == 1.0
        assert "result_url" in data

    @pytest.mark.asyncio
    async def test_evicted_simulation_skips_update(self) -> None:
        server = AsyncMock()
        sim_id = "SIM-002"
        data = {"status": "processing", "progress": 0.5}
        # Don't put data in simulations — simulate eviction
        simulations[sim_id] = {"status": "different_object"}

        await _process_simulation(server, sim_id, data)

        # Original data should not be modified to completed
        assert simulations[sim_id]["status"] == "different_object"

    @pytest.mark.asyncio
    async def test_notify_failure_logged(self) -> None:
        server = AsyncMock()
        server.notify_resource_updated = AsyncMock(side_effect=Exception("notify failed"))
        sim_id = "SIM-003"
        data = {"status": "processing", "progress": 0.5}
        simulations[sim_id] = data

        await _process_simulation(server, sim_id, data)

        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_cancelled_sets_failed(self) -> None:
        server = AsyncMock()
        sim_id = "SIM-004"
        data = {"status": "processing", "progress": 0.5}
        simulations[sim_id] = data

        async def cancel_during_sleep(*args):
            raise asyncio.CancelledError()

        with (
            patch("resq_mcp.server.asyncio.sleep", side_effect=cancel_during_sleep),
            pytest.raises(asyncio.CancelledError),
        ):
            await _process_simulation(server, sim_id, data)

        assert data["status"] == "failed"
        assert data["progress"] == 0.0


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_starts_and_stops_task(self) -> None:
        server = AsyncMock()

        with patch("resq_mcp.server.simulation_processor", new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value = None
            async with lifespan(server):
                pass  # lifespan is running

    @pytest.mark.asyncio
    async def test_lifespan_flushes_telemetry_on_shutdown(self) -> None:
        """Buffered spans/metrics must be flushed when the server exits.

        setup_telemetry() runs at import time but nothing called its counterpart,
        so anything still buffered was dropped on exit. Only observable once a
        backend is configured (RESQ_TELEMETRY_BACKEND defaults to "none"), which
        is why it went unnoticed.
        """
        server = AsyncMock()

        with (
            patch("resq_mcp.server.simulation_processor", new_callable=AsyncMock) as mock_proc,
            patch("resq_mcp.server.shutdown_telemetry") as mock_shutdown,
        ):
            mock_proc.return_value = None
            async with lifespan(server):
                # Still running: shutdown must not have been called yet.
                mock_shutdown.assert_not_called()

        mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_flushes_telemetry_after_task_cleanup(self) -> None:
        """The flush happens last, so shutdown work itself is recorded."""
        server = AsyncMock()
        call_order: list[str] = []

        async def fake_processor(_server: object) -> None:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                call_order.append("task_cancelled")
                raise

        with (
            patch("resq_mcp.server.simulation_processor", fake_processor),
            patch(
                "resq_mcp.server.shutdown_telemetry",
                side_effect=lambda: call_order.append("flush"),
            ),
        ):
            async with lifespan(server):
                await asyncio.sleep(0)

        assert call_order == ["task_cancelled", "flush"]


class TestDtsopRunSimulationCapacity:
    @pytest.mark.asyncio
    async def test_capacity_reached_raises_error(self) -> None:
        from resq_mcp.dtsop.models import SimulationRequest
        from resq_mcp.dtsop.tools import MAX_SIMULATIONS, run_simulation

        for i in range(MAX_SIMULATIONS):
            simulations[f"SIM-{i}"] = {"status": "processing"}

        req = SimulationRequest(
            scenario_id="TEST-CAP",
            sector_id="SECTOR-1",
            disaster_type="earthquake",
            parameters={"wind_speed": 10.0},
            strategy=None,
        )
        with pytest.raises(FastMCPError, match="capacity reached"):
            await run_simulation(req)


class TestResourcesFailedSimulation:
    @pytest.mark.asyncio
    async def test_failed_simulation_status(self) -> None:
        from resq_mcp.resources import get_simulation_status

        simulations["SIM-FAIL"] = {
            "status": "failed",
            "progress": 0.0,
            "request": {"scenario_id": "TEST"},
        }
        result = await get_simulation_status("SIM-FAIL")
        assert "FAILED" in result
