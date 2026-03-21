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

from resq_mcp.dtsop.models import OptimizationStrategy, SimulationRequest
from resq_mcp.dtsop.service import run_simulation as trigger_sim
from resq_mcp.resources import get_simulation_status
from resq_mcp.server import simulations


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


class TestCleanupState:
    """Tests for the _cleanup_state TTL eviction logic."""

    @pytest.fixture(autouse=True)
    def clear_all_stores(self) -> None:
        from resq_mcp.server import incidents, missions, simulations

        simulations.clear()
        incidents.clear()
        missions.clear()

    def test_completed_sim_evicted_after_ttl(self) -> None:
        import time

        from resq_mcp.server import COMPLETED_TTL_SECONDS, _cleanup_state, simulations

        simulations["SIM-EVICT-001"] = {
            "status": "completed",
            "completed_at": time.monotonic() - COMPLETED_TTL_SECONDS - 1,
        }
        _cleanup_state()
        assert "SIM-EVICT-001" not in simulations

    def test_completed_sim_kept_before_ttl(self) -> None:
        import time

        from resq_mcp.server import _cleanup_state, simulations

        simulations["SIM-KEEP-001"] = {
            "status": "completed",
            "completed_at": time.monotonic() - 10,
        }
        _cleanup_state()
        assert "SIM-KEEP-001" in simulations

    def test_failed_sim_evicted_after_ttl(self) -> None:
        import time

        from resq_mcp.server import FAILED_TTL_SECONDS, _cleanup_state, simulations

        simulations["SIM-FAIL-001"] = {
            "status": "failed",
            "failed_at": time.monotonic() - FAILED_TTL_SECONDS - 1,
        }
        _cleanup_state()
        assert "SIM-FAIL-001" not in simulations

    def test_rejected_incident_evicted_after_ttl(self) -> None:
        import time

        from resq_mcp.server import INCIDENT_TTL_SECONDS, _cleanup_state, incidents

        incidents["INC-OLD-REJECT"] = {
            "is_confirmed": False,
            "validated_at_mono": time.monotonic() - INCIDENT_TTL_SECONDS - 1,
        }
        _cleanup_state()
        assert "INC-OLD-REJECT" not in incidents

    def test_confirmed_incident_kept_within_24h(self) -> None:
        import time

        from resq_mcp.server import INCIDENT_TTL_SECONDS, _cleanup_state, incidents

        # Beyond rejected TTL but within confirmed TTL (24h)
        incidents["INC-CONF-KEEP"] = {
            "is_confirmed": True,
            "validated_at_mono": time.monotonic() - INCIDENT_TTL_SECONDS - 1,
        }
        _cleanup_state()
        assert "INC-CONF-KEEP" in incidents

    def test_confirmed_incident_evicted_after_24h(self) -> None:
        import time

        from resq_mcp.server import CONFIRMED_INCIDENT_TTL_SECONDS, _cleanup_state, incidents

        incidents["INC-CONF-OLD"] = {
            "is_confirmed": True,
            "validated_at_mono": time.monotonic() - CONFIRMED_INCIDENT_TTL_SECONDS - 1,
        }
        _cleanup_state()
        assert "INC-CONF-OLD" not in incidents

    def test_stale_mission_evicted_after_ttl(self) -> None:
        import time

        from resq_mcp.server import MISSION_TTL_SECONDS, _cleanup_state, missions

        missions["DRONE-OLD"] = {
            "strategy_id": "STRAT-X",
            "is_urgent": False,
            "params": {
                "mission_id": "MISS-00000001",
                "strategy_hash": "0xdeadbeef",
                "target_sector": "Dynamic-Assigned",
                "authorized_actions": [],
                "risk_tolerance": 0.5,
            },
            "dispatched_at": "2026-01-01T00:00:00+00:00",
            "dispatched_at_mono": time.monotonic() - MISSION_TTL_SECONDS - 1,
        }
        _cleanup_state()
        assert "DRONE-OLD" not in missions

    def test_active_mission_kept_within_ttl(self) -> None:
        import time

        from resq_mcp.server import _cleanup_state, missions

        missions["DRONE-ACTIVE"] = {
            "strategy_id": "STRAT-Y",
            "is_urgent": False,
            "params": {
                "mission_id": "MISS-00000002",
                "strategy_hash": "0xcafebabe",
                "target_sector": "Dynamic-Assigned",
                "authorized_actions": [],
                "risk_tolerance": 0.5,
            },
            "dispatched_at": "2026-01-01T00:00:00+00:00",
            "dispatched_at_mono": time.monotonic() - 60,
        }
        _cleanup_state()
        assert "DRONE-ACTIVE" in missions

    def test_incident_with_missing_is_confirmed_not_evicted_early(self) -> None:
        """Malformed incident record (missing is_confirmed) is not evicted under rejected TTL."""
        import time

        from resq_mcp.server import INCIDENT_TTL_SECONDS, _cleanup_state, incidents

        incidents["INC-MALFORMED"] = {
            # No is_confirmed key — should not match either eviction branch
            "validated_at_mono": time.monotonic() - INCIDENT_TTL_SECONDS - 1,
        }
        _cleanup_state()
        # Malformed record stays put — neither True nor False, so neither branch fires
        assert "INC-MALFORMED" in incidents
