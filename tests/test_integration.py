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

"""Integration tests for cross-module workflows."""

from __future__ import annotations

import random

import pytest

from resq_mcp.dtsop import get_optimization_strategy
from resq_mcp.hce import update_mission_params, validate_incident
from resq_mcp.models import (
    DeploymentStatus,
    ErrorResponse,
    IncidentReport,
    IncidentValidation,
    MissionParameters,
    OptimizationStrategy,
    SectorAnalysis,
)
from resq_mcp.pdie import get_predictive_alerts
from resq_mcp.tools import request_drone_deployment, scan_current_sector


class TestIncidentToMissionFlow:
    def test_confirmed_incident_produces_mission_params(self) -> None:
        report = IncidentReport(
            incident_id="INC-INTEG-001",
            source="edge_ai",
            sector_id="Sector-1",
            detected_type="wildfire",
            confidence=0.95,
            evidence_url="neofs://evidence/fire.mp4",
        )
        validation = validate_incident(report)
        assert isinstance(validation, IncidentValidation)
        assert validation.is_confirmed is True

        strategy = get_optimization_strategy(report.incident_id)
        assert isinstance(strategy, OptimizationStrategy)
        assert strategy.related_alert_id == "INC-INTEG-001"

        params = update_mission_params("DRONE-Alpha", strategy.strategy_id)
        assert isinstance(params, MissionParameters)
        assert params.strategy_hash.startswith("0x")
        assert len(params.authorized_actions) > 0

    def test_rejected_incident_does_not_trigger_response(self) -> None:
        report = IncidentReport(
            incident_id="INC-INTEG-002",
            source="sensor_network",
            sector_id="Sector-2",
            detected_type="flooding",
            confidence=0.3,
        )
        validation = validate_incident(report)
        assert isinstance(validation, IncidentValidation)
        assert validation.is_confirmed is False


class TestSurveillanceToDeploymentFlow:
    def test_critical_scan_triggers_deployment(self) -> None:
        random.seed(0)
        detection = None
        for _ in range(20):
            result = scan_current_sector("Sector-1")
            if isinstance(result, SectorAnalysis) and result.status == "CRITICAL_ALERT":
                detection = result
                break
        if detection is None:
            pytest.skip("No detection generated with current seed")
        assert detection.disaster_type is not None
        alerts = get_predictive_alerts(detection.sector_id)
        assert not isinstance(alerts, ErrorResponse)
        deployment = request_drone_deployment(detection.sector_id, "critical")
        assert isinstance(deployment, DeploymentStatus)
        assert deployment.sector_id == detection.sector_id
        assert deployment.status == "deployed"


class TestSimulationLifecycle:
    @pytest.mark.asyncio
    async def test_simulation_end_to_end(self) -> None:
        from fastmcp.exceptions import FastMCPError

        from resq_mcp.dtsop import run_simulation
        from resq_mcp.models import SimulationRequest
        from resq_mcp.server import get_simulation_status, simulations

        simulations.clear()

        request = SimulationRequest(
            scenario_id="integ-sim-001",
            sector_id="Sector-1",
            disaster_type="flood",
            parameters={"water_level": 3.0},
            priority="urgent",
        )
        sim_id = run_simulation(request)
        simulations[sim_id] = {
            "status": "pending",
            "request": request.model_dump(),
            "created_at": "now",
        }

        status_str = await get_simulation_status(sim_id)
        assert sim_id in status_str
        assert "pending" in status_str

        simulations[sim_id]["status"] = "completed"
        simulations[sim_id]["progress"] = 1.0
        simulations[sim_id]["result_url"] = f"neofs://sim_results/{sim_id}.json"

        status_str = await get_simulation_status(sim_id)
        assert "completed" in status_str
        assert "100%" in status_str

        strategy = get_optimization_strategy(sim_id)
        assert isinstance(strategy, OptimizationStrategy)
        assert strategy.related_alert_id == sim_id

        with pytest.raises(FastMCPError):
            await get_simulation_status("SIM-NONEXISTENT")

        simulations.clear()
