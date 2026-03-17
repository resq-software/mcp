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

"""Unit tests for the PDIE module (Predictive Disaster Intelligence Engine)."""

from __future__ import annotations

import pytest

from resq_mcp.models import ErrorResponse, PreAlert, VulnerabilityMap
from resq_mcp.pdie import (
    VULNERABILITY_DB,
    get_predictive_alerts,
    get_vulnerability_map,
)


class TestGetVulnerabilityMap:
    """Tests for the get_vulnerability_map function."""

    def test_get_valid_sector_returns_vulnerability_map(self) -> None:
        """Test getting vulnerability map for valid sector."""
        result = get_vulnerability_map("Sector-1")

        assert isinstance(result, VulnerabilityMap)
        assert result.sector_id == "Sector-1"
        assert result.population_density == "high"

    def test_get_invalid_sector_returns_error(self) -> None:
        """Test getting vulnerability map for invalid sector."""
        result = get_vulnerability_map("Invalid-Sector")

        assert isinstance(result, ErrorResponse)
        assert "No vulnerability data" in result.message

    def test_sector_1_has_high_fire_risk(self) -> None:
        """Test that Sector-1 has high fire risk."""
        result = get_vulnerability_map("Sector-1")

        assert isinstance(result, VulnerabilityMap)
        assert result.fire_risk == pytest.approx(0.8)
        assert result.flood_risk == pytest.approx(0.1)

    def test_sector_3_has_high_flood_risk(self) -> None:
        """Test that Sector-3 has high flood risk."""
        result = get_vulnerability_map("Sector-3")

        assert isinstance(result, VulnerabilityMap)
        assert result.flood_risk == pytest.approx(0.9)
        assert result.fire_risk == pytest.approx(0.1)

    def test_all_sectors_in_db_are_retrievable(self) -> None:
        """Test that all sectors in the database are retrievable."""
        for sector_id in VULNERABILITY_DB:
            result = get_vulnerability_map(sector_id)
            assert isinstance(result, VulnerabilityMap)
            assert result.sector_id == sector_id


class TestGetPredictiveAlerts:
    """Tests for the get_predictive_alerts function."""

    def test_invalid_sector_returns_error(self) -> None:
        """Test that invalid sector returns ErrorResponse."""
        result = get_predictive_alerts("Invalid-Sector")

        assert isinstance(result, ErrorResponse)
        assert "unknown" in result.message

    def test_returns_list_of_alerts(self) -> None:
        """Test that function returns a list."""
        result = get_predictive_alerts("Sector-1")

        assert isinstance(result, list)
        for alert in result:
            assert isinstance(alert, PreAlert)

    def test_fire_alerts_for_high_fire_risk_sector(self) -> None:
        """Test that high fire risk sectors can generate fire alerts."""
        # Sector-1 has 0.8 fire risk
        fire_alerts = []
        for _ in range(50):  # Run multiple times due to randomness
            result = get_predictive_alerts("Sector-1")
            if isinstance(result, list):
                fire_alerts.extend(a for a in result if a.predicted_disaster_type == "wildfire")

        # Should get at least some fire alerts
        assert len(fire_alerts) > 0

    def test_flood_alerts_for_high_flood_risk_sector(self) -> None:
        """Test that high flood risk sectors can generate flood alerts."""
        # Sector-3 has 0.9 flood risk
        flood_alerts = []
        for _ in range(50):  # Run multiple times due to randomness
            result = get_predictive_alerts("Sector-3")
            if isinstance(result, list):
                flood_alerts.extend(a for a in result if a.predicted_disaster_type == "flood")

        # Should get at least some flood alerts
        assert len(flood_alerts) > 0

    def test_alerts_have_valid_probability(self) -> None:
        """Test that alerts have probability in valid range."""
        for _ in range(20):
            result = get_predictive_alerts("Sector-1")
            if isinstance(result, list):
                for alert in result:
                    assert 0.0 <= alert.probability <= 1.0

    def test_alerts_include_vulnerability_context(self) -> None:
        """Test that alerts include vulnerability context."""
        for _ in range(20):
            result = get_predictive_alerts("Sector-2")
            if isinstance(result, list) and result:
                alert = result[0]
                assert alert.vulnerability_context is not None
                assert alert.vulnerability_context.sector_id == "Sector-2"
                break

    def test_low_risk_sector_generates_few_alerts(self) -> None:
        """Test that low risk sectors generate fewer alerts."""
        # Sector-1: fire 0.8, flood 0.1
        # Since flood risk is low, should rarely get flood alerts
        flood_alerts = []
        for _ in range(50):
            result = get_predictive_alerts("Sector-1")
            if isinstance(result, list):
                flood_alerts.extend(a for a in result if a.predicted_disaster_type == "flood")

        # Should get very few or no flood alerts
        assert len(flood_alerts) == 0
