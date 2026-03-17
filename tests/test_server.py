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

"""Unit tests for the ResQ MCP server module."""

from __future__ import annotations

import asyncio
import contextlib

import pytest
from fastmcp.exceptions import FastMCPError
from pydantic import ValidationError

from resq_mcp.dtsop import run_simulation as trigger_sim
from resq_mcp.models import OptimizationStrategy, SimulationRequest
from resq_mcp.server import get_simulation_status, simulations


@pytest.fixture(autouse=True)
def clear_simulations() -> None:
    """Clear the simulations store before each test."""
    simulations.clear()


class TestRunSimulation:
    """Tests for the run_simulation functionality.

    Note: We test the underlying trigger_sim function directly since
    the server's run_simulation is a FastMCP tool that wraps this logic.
    """

    def test_simulation_creates_unique_id(self) -> None:
        """Test that trigger_sim returns a unique simulation ID."""
        req = SimulationRequest(
            scenario_id="TEST-SCENARIO-001",
            sector_id="SECTOR-alpha",
            disaster_type="flood",
            parameters={"water_level": 5.0},
        )

        sim_id = trigger_sim(req)

        assert sim_id is not None
        assert isinstance(sim_id, str)
        assert len(sim_id) > 0

    def test_simulation_ids_are_unique(self) -> None:
        """Test that consecutive simulation IDs are unique."""
        req = SimulationRequest(
            scenario_id="TEST-002",
            sector_id="SECTOR-beta",
            disaster_type="wildfire",
            parameters={"wind_speed": 25.0},
        )

        id1 = trigger_sim(req)
        id2 = trigger_sim(req)

        assert id1 != id2


class TestOptimizationStrategyModel:
    """Tests for the OptimizationStrategy model."""

    def test_valid_strategy_creation(self) -> None:
        """Test creating a valid OptimizationStrategy."""
        strat = OptimizationStrategy(
            strategy_id="STRAT-123",
            recommended_deployment={"drone_a": 5},
            evacuation_routes=["Route A"],
            estimated_success_rate=0.95,
        )

        assert strat.estimated_success_rate == 0.95
        assert strat.strategy_id == "STRAT-123"
        assert strat.recommended_deployment == {"drone_a": 5}

    def test_invalid_deployment_type_raises_error(self) -> None:
        """Test that invalid deployment type raises ValidationError."""
        with pytest.raises(ValidationError):
            OptimizationStrategy(
                strategy_id="bad",
                recommended_deployment=[],  # type: ignore[arg-type]
                evacuation_routes=[],
                estimated_success_rate=0.95,
            )

    def test_optional_fields_default_to_none(self) -> None:
        """Test that optional fields default to None."""
        strat = OptimizationStrategy(
            strategy_id="STRAT-456",
            recommended_deployment={"drone_b": 2},
            evacuation_routes=["Route B"],
            estimated_success_rate=0.88,
        )

        assert strat.related_alert_id is None
        assert strat.simulation_proof_url is None


class TestGetSimulationStatus:
    """Tests for the get_simulation_status resource."""

    @pytest.mark.asyncio
    async def test_get_simulation_status_success(self) -> None:
        """Test retrieving status for an existing simulation."""
        sim_id = "SIM-TEST-001"
        simulations[sim_id] = {
            "status": "processing",
            "progress": 0.5,
            "request": {"scenario_id": "scen-1"},
            "created_at": "now",
        }

        result = await get_simulation_status(sim_id)

        assert sim_id in result
        assert "processing" in result
        assert "50%" in result
        assert "scen-1" in result

    @pytest.mark.asyncio
    async def test_get_simulation_status_completed(self) -> None:
        """Test retrieving status for a completed simulation."""
        sim_id = "SIM-TEST-DONE"
        simulations[sim_id] = {
            "status": "completed",
            "progress": 1.0,
            "result_url": "neofs://results/123",
            "request": {},
        }

        result = await get_simulation_status(sim_id)

        assert "completed" in result
        assert "100%" in result
        assert "neofs://results/123" in result

    @pytest.mark.asyncio
    async def test_get_simulation_status_not_found(self) -> None:
        """Test that non-existent ID raises FastMCPError."""
        with pytest.raises(FastMCPError) as exc_info:
            await get_simulation_status("SIM-NON-EXISTENT")

        assert "not found" in str(exc_info.value)


class TestSimulationProcessor:
    """Tests for the simulation_processor background task."""

    @pytest.mark.asyncio
    async def test_pending_transitions_to_processing(self) -> None:
        from unittest.mock import AsyncMock

        from resq_mcp.server import simulation_processor, simulations

        simulations["SIM-BG-001"] = {"status": "pending", "request": {}, "created_at": "now"}
        mock_server = AsyncMock()
        mock_server.notify_resource_updated = AsyncMock()
        task = asyncio.create_task(simulation_processor(mock_server))
        await asyncio.sleep(2.5)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert simulations["SIM-BG-001"]["status"] == "processing"
        assert simulations["SIM-BG-001"]["progress"] == 0.5
        mock_server.notify_resource_updated.assert_called()

    @pytest.mark.asyncio
    async def test_processing_transitions_to_completed(self) -> None:
        from unittest.mock import AsyncMock

        from resq_mcp.server import simulation_processor, simulations

        simulations["SIM-BG-002"] = {
            "status": "processing",
            "progress": 0.5,
            "request": {},
            "created_at": "now",
        }
        mock_server = AsyncMock()
        mock_server.notify_resource_updated = AsyncMock()
        task = asyncio.create_task(simulation_processor(mock_server))
        await asyncio.sleep(6)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert simulations["SIM-BG-002"]["status"] == "completed"
        assert simulations["SIM-BG-002"]["progress"] == 1.0
        assert "result_url" in simulations["SIM-BG-002"]

    @pytest.mark.asyncio
    async def test_notification_failure_does_not_crash_processor(self) -> None:
        from unittest.mock import AsyncMock

        from resq_mcp.server import simulation_processor, simulations

        simulations["SIM-BG-003"] = {"status": "pending", "request": {}, "created_at": "now"}
        mock_server = AsyncMock()
        mock_server.notify_resource_updated = AsyncMock(side_effect=RuntimeError("SSE down"))
        task = asyncio.create_task(simulation_processor(mock_server))
        await asyncio.sleep(2.5)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert simulations["SIM-BG-003"]["status"] == "processing"


class TestListActiveDrones:
    def test_returns_fleet_status(self) -> None:
        from resq_mcp.server import list_active_drones

        result = list_active_drones()
        assert "DRONE-Alpha" in result
        assert "DRONE-Beta" in result
        assert "DRONE-Gamma" in result

    def test_includes_all_drone_types(self) -> None:
        from resq_mcp.server import list_active_drones

        result = list_active_drones()
        assert "Surveillance" in result
        assert "Payload" in result
        assert "Relay" in result


class TestIncidentResponsePlan:
    def test_prompt_includes_incident_id(self) -> None:
        from resq_mcp.server import incident_response_plan

        result = incident_response_plan("INC-999")
        assert "INC-999" in result

    def test_prompt_references_tools(self) -> None:
        from resq_mcp.server import incident_response_plan

        result = incident_response_plan("INC-001")
        assert "get_deployment_strategy" in result
        assert "resq://drones/active" in result

    def test_prompt_includes_output_format(self) -> None:
        from resq_mcp.server import incident_response_plan

        result = incident_response_plan("INC-001")
        assert "Situation Summary" in result
        assert "Asset Allocation" in result
        assert "Risk Assessment" in result
