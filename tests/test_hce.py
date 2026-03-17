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

"""Unit tests for the HCE module (Hybrid Coordination Engine)."""

from __future__ import annotations

import pytest

from resq_mcp.hce import update_mission_params, validate_incident
from resq_mcp.models import IncidentReport, IncidentValidation, MissionParameters


class TestValidateIncident:
    """Tests for the validate_incident function."""

    def test_high_confidence_report_is_confirmed(self) -> None:
        """Test that high confidence reports are auto-confirmed."""
        report = IncidentReport(
            incident_id="INC-001",
            source="edge_ai",
            sector_id="Sector-1",
            detected_type="wildfire",
            confidence=0.95,
        )

        result = validate_incident(report)

        assert isinstance(result, IncidentValidation)
        assert result.is_confirmed is True
        assert result.incident_id == "INC-001"

    def test_low_confidence_report_is_rejected(self) -> None:
        """Test that low confidence reports are not confirmed."""
        report = IncidentReport(
            incident_id="INC-002",
            source="sensor_network",
            sector_id="Sector-2",
            detected_type="flood",
            confidence=0.5,
        )

        result = validate_incident(report)

        assert isinstance(result, IncidentValidation)
        assert result.is_confirmed is False

    def test_borderline_confidence_is_rejected(self) -> None:
        """Test that borderline confidence (0.85) is rejected."""
        report = IncidentReport(
            incident_id="INC-003",
            source="human_report",
            sector_id="Sector-3",
            detected_type="accident",
            confidence=0.85,
        )

        result = validate_incident(report)

        # Exactly 0.85 is not > 0.85, so should be rejected
        assert result.is_confirmed is False

    def test_above_threshold_is_confirmed(self) -> None:
        """Test that just above threshold is confirmed."""
        report = IncidentReport(
            incident_id="INC-004",
            source="edge_ai",
            sector_id="Sector-4",
            detected_type="wildfire",
            confidence=0.86,
        )

        result = validate_incident(report)

        assert result.is_confirmed is True

    def test_validation_source_is_set(self) -> None:
        """Test that validation source is properly set."""
        report = IncidentReport(
            incident_id="INC-005",
            source="edge_ai",
            sector_id="Sector-1",
            detected_type="flood",
            confidence=0.9,
        )

        result = validate_incident(report)

        assert result.validation_source == "SpoonOS-HCE-Validator"

    def test_notes_include_confidence(self) -> None:
        """Test that notes include the confidence level."""
        report = IncidentReport(
            incident_id="INC-006",
            source="edge_ai",
            sector_id="Sector-2",
            detected_type="wildfire",
            confidence=0.92,
        )

        result = validate_incident(report)

        assert "0.92" in result.notes


class TestUpdateMissionParams:
    """Tests for the update_mission_params function."""

    def test_returns_mission_parameters(self) -> None:
        """Test that function returns MissionParameters."""
        result = update_mission_params("DRONE-001", "STRAT-ABC")

        assert isinstance(result, MissionParameters)

    def test_mission_id_format(self) -> None:
        """Test that mission ID has correct format."""
        result = update_mission_params("DRONE-002", "STRAT-DEF")

        assert isinstance(result, MissionParameters)
        assert result.mission_id.startswith("MISS-")

    def test_strategy_hash_is_blockchain_format(self) -> None:
        """Test that strategy hash starts with 0x."""
        result = update_mission_params("DRONE-003", "STRAT-GHI")

        assert isinstance(result, MissionParameters)
        assert result.strategy_hash.startswith("0x")

    def test_urgent_strategy_has_high_risk_tolerance(self) -> None:
        """Test that urgent strategies have high risk tolerance."""
        result = update_mission_params("DRONE-004", "URGENT-STRAT-001")

        assert isinstance(result, MissionParameters)
        assert result.risk_tolerance == pytest.approx(0.9)

    def test_normal_strategy_has_low_risk_tolerance(self) -> None:
        """Test that normal strategies have lower risk tolerance."""
        result = update_mission_params("DRONE-005", "STRAT-NORMAL")

        assert isinstance(result, MissionParameters)
        assert result.risk_tolerance == pytest.approx(0.5)

    def test_authorized_actions_are_set(self) -> None:
        """Test that authorized actions are properly set."""
        result = update_mission_params("DRONE-006", "STRAT-JKL")

        assert isinstance(result, MissionParameters)
        assert "autonomous_flight" in result.authorized_actions
        assert "payload_release_authorized" in result.authorized_actions

    def test_target_sector_is_set(self) -> None:
        """Test that target sector is set."""
        result = update_mission_params("DRONE-007", "STRAT-MNO")

        assert isinstance(result, MissionParameters)
        assert result.target_sector == "Dynamic-Assigned"
