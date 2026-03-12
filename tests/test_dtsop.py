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

"""Unit tests for the DTSOP module (Digital Twin Simulation & Optimization)."""

from __future__ import annotations

from resq_mcp.dtsop import get_optimization_strategy, run_simulation
from resq_mcp.models import OptimizationStrategy, SimulationRequest


class TestRunSimulation:
    """Tests for the run_simulation function."""

    def test_returns_simulation_id(self) -> None:
        """Test that run_simulation returns a valid simulation ID."""
        request = SimulationRequest(
            scenario_id="TEST-001",
            sector_id="Sector-1",
            disaster_type="flood",
            parameters={"water_level": 5.0},
        )

        result = run_simulation(request)

        assert result.startswith("SIM-")
        assert len(result) == 12  # "SIM-" + 8 hex chars

    def test_simulation_ids_are_unique(self) -> None:
        """Test that simulation IDs are unique."""
        request = SimulationRequest(
            scenario_id="TEST-002",
            sector_id="Sector-2",
            disaster_type="wildfire",
            parameters={"wind_speed": 30.0},
        )

        ids = {run_simulation(request) for _ in range(100)}

        assert len(ids) == 100  # All unique


class TestGetOptimizationStrategy:
    """Tests for the get_optimization_strategy function."""

    def test_returns_optimization_strategy(self) -> None:
        """Test that function returns OptimizationStrategy."""
        result = get_optimization_strategy("INC-001")

        assert isinstance(result, OptimizationStrategy)

    def test_strategy_has_valid_id(self) -> None:
        """Test that strategy has a valid ID format."""
        result = get_optimization_strategy("INC-002")

        assert result.strategy_id.startswith("STRAT-")

    def test_strategy_links_to_incident(self) -> None:
        """Test that strategy is linked to the incident."""
        incident_id = "INC-003"
        result = get_optimization_strategy(incident_id)

        assert result.related_alert_id == incident_id

    def test_strategy_has_deployment_recommendations(self) -> None:
        """Test that strategy includes deployment recommendations."""
        result = get_optimization_strategy("INC-004")

        assert result.recommended_deployment is not None
        assert len(result.recommended_deployment) > 0

    def test_strategy_has_evacuation_routes(self) -> None:
        """Test that strategy includes evacuation routes."""
        result = get_optimization_strategy("INC-005")

        assert result.evacuation_routes is not None
        assert len(result.evacuation_routes) > 0

    def test_strategy_has_valid_success_rate(self) -> None:
        """Test that success rate is in valid range."""
        for _ in range(20):
            result = get_optimization_strategy("INC-TEST")
            assert 0.0 <= result.estimated_success_rate <= 1.0

    def test_strategy_has_proof_url(self) -> None:
        """Test that strategy has simulation proof URL."""
        result = get_optimization_strategy("INC-006")

        assert result.simulation_proof_url is not None
        assert result.simulation_proof_url.startswith("neofs://")