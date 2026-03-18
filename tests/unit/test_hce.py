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

import logging
from typing import TYPE_CHECKING

import pytest

from resq_mcp.hce.models import IncidentReport, IncidentValidation, MissionParameters
from resq_mcp.hce.service import update_mission_params, validate_incident
from resq_mcp.hce.tools import update_mission_params as update_mission_params_tool
from resq_mcp.hce.tools import validate_incident as validate_incident_tool
from resq_mcp.server import incidents, missions

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


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
        """Test that urgent flag produces high risk tolerance (not string injection)."""
        result = update_mission_params("DRONE-004", "STRAT-001", is_urgent=True)

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


class TestEdgeCases:
    def test_validate_incident_with_zero_confidence(self) -> None:
        report = IncidentReport(
            incident_id="INC-ZERO",
            source="edge_ai",
            sector_id="Sector-1",
            detected_type="test",
            confidence=0.0,
        )
        result = validate_incident(report)
        assert not result.is_confirmed

    def test_validate_incident_with_max_confidence(self) -> None:
        report = IncidentReport(
            incident_id="INC-MAX",
            source="edge_ai",
            sector_id="Sector-1",
            detected_type="test",
            confidence=1.0,
        )
        result = validate_incident(report)
        assert result.is_confirmed

    def test_mission_params_urgent_strategy_has_high_risk_tolerance(self) -> None:
        params = update_mission_params("DRONE-X", "STRAT-FIRE-001", is_urgent=True)
        assert isinstance(params, MissionParameters)
        assert params.risk_tolerance == pytest.approx(0.9)

    def test_mission_params_standard_strategy_has_low_risk_tolerance(self) -> None:
        params = update_mission_params("DRONE-Y", "STRAT-STANDARD-001")
        assert isinstance(params, MissionParameters)
        assert params.risk_tolerance == pytest.approx(0.5)

    def test_mission_params_strategy_hash_format(self) -> None:
        import re

        params = update_mission_params("DRONE-Z", "STRAT-TEST")
        assert isinstance(params, MissionParameters)
        assert re.match(r"^0x[a-f0-9]{64}$", params.strategy_hash)


class TestValidateIncidentTool:
    """Tests for the validate_incident tool functionality."""

    @pytest.mark.asyncio
    async def test_validate_incident_confirms(self, caplog: LogCaptureFixture) -> None:
        """Test that validate_incident correctly confirms an incident."""
        val = IncidentValidation(
            incident_id="INC-CONFIRM-001",
            is_confirmed=True,
            validation_source="Human-Operator",
            notes="Confirmed via visual evidence",
        )

        with caplog.at_level(logging.INFO):
            result = await validate_incident_tool(val)

        assert "successfully CONFIRMED" in result
        assert "INC-CONFIRM-001" in result

        # Verify logging (notes moved to DEBUG level for PII safety)
        assert "Incident INC-CONFIRM-001 CONFIRMED by Human-Operator" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_incident_rejects(self, caplog: LogCaptureFixture) -> None:
        """Test that validate_incident correctly rejects an incident."""
        val = IncidentValidation(
            incident_id="INC-REJECT-002",
            is_confirmed=False,
            validation_source="Auto-Validator",
            notes="Rejected due to low confidence",
        )

        with caplog.at_level(logging.INFO):
            result = await validate_incident_tool(val)

        assert "successfully REJECTED" in result
        assert "INC-REJECT-002" in result

        # Verify logging
        assert "Incident INC-REJECT-002 REJECTED by Auto-Validator" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_with_correlated_pre_alert(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-CORR-003",
            is_confirmed=True,
            validation_source="PDIE-Correlation-Engine",
            correlated_pre_alert_id="PRE-ALERT-789",
            notes="Correlated with predictive alert PRE-ALERT-789",
        )
        with caplog.at_level(logging.INFO):
            result = await validate_incident_tool(val)
        assert "successfully CONFIRMED" in result

    @pytest.mark.asyncio
    async def test_validate_with_sensor_network_source(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-SENSOR-004",
            is_confirmed=True,
            validation_source="Sensor-Network-Validator",
            notes="Multiple ground sensors triggered",
        )
        with caplog.at_level(logging.INFO):
            result = await validate_incident_tool(val)
        assert "successfully CONFIRMED" in result
        assert "Sensor-Network-Validator" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_reject_with_detailed_notes(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-FP-005",
            is_confirmed=False,
            validation_source="Human-Operator-Bob",
            notes="False positive: construction activity, not fire",
        )
        with caplog.at_level(logging.DEBUG):
            result = await validate_incident_tool(val)
        assert "successfully REJECTED" in result
        assert "construction activity" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_log_format_contains_all_fields(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-LOG-006",
            is_confirmed=True,
            validation_source="Audit-Test-Source",
            notes="Testing log format completeness",
        )
        with caplog.at_level(logging.DEBUG):
            await validate_incident_tool(val)
        log_text = caplog.text
        assert "INC-LOG-006" in log_text
        assert "CONFIRMED" in log_text
        assert "Audit-Test-Source" in log_text
        assert "Testing log format completeness" in log_text


@pytest.fixture(autouse=True)
def clear_incident_and_mission_stores() -> None:
    """Clear shared state stores before each test to prevent cross-test pollution."""
    incidents.clear()
    missions.clear()


class TestValidateIncidentToolGuards:
    """Tests for validate_incident idempotency, conflict, and capacity guards."""

    @pytest.mark.asyncio
    async def test_idempotent_revalidation_same_result(self) -> None:
        """Re-submitting the same validation returns an idempotent message."""
        val = IncidentValidation(
            incident_id="INC-IDEM-001",
            is_confirmed=True,
            validation_source="Operator",
            notes="First validation",
        )
        await validate_incident_tool(val)
        result = await validate_incident_tool(val)
        assert "already CONFIRMED" in result
        assert "idempotent" in result

    @pytest.mark.asyncio
    async def test_conflict_guard_blocks_opposite_result(self) -> None:
        """Re-validating with the opposite result is blocked as a conflict."""
        confirm = IncidentValidation(
            incident_id="INC-CONF-002",
            is_confirmed=True,
            validation_source="Operator-A",
            notes="Confirmed",
        )
        reject = IncidentValidation(
            incident_id="INC-CONF-002",
            is_confirmed=False,
            validation_source="Operator-B",
            notes="Rejected",
        )
        await validate_incident_tool(confirm)
        result = await validate_incident_tool(reject)
        assert "Conflict" in result
        assert "INC-CONF-002" in result

    @pytest.mark.asyncio
    async def test_capacity_guard_blocks_new_incidents(self) -> None:
        """Raises FastMCPError when the incident store is at capacity."""
        from fastmcp.exceptions import FastMCPError

        from resq_mcp.server import MAX_INCIDENTS

        # Fill the store to capacity with synthetic records
        for i in range(MAX_INCIDENTS):
            incidents[f"INC-FILL-{i:05d}"] = {
                "is_confirmed": True,
                "validation_source": "test",
                "notes": "",
                "validated_at": "2026-01-01T00:00:00+00:00",
                "validated_at_mono": 0.0,
            }

        val = IncidentValidation(
            incident_id="INC-OVERFLOW",
            is_confirmed=True,
            validation_source="test",
            notes="overflow test",
        )
        with pytest.raises(FastMCPError, match="capacity reached"):
            await validate_incident_tool(val)

    @pytest.mark.asyncio
    async def test_case_insensitive_incident_key_idempotency(self) -> None:
        """Lower-case and upper-case incident IDs refer to the same record."""
        lower_val = IncidentValidation(
            incident_id="inc-case-001",
            is_confirmed=True,
            validation_source="Operator",
            notes="Lowercase submission",
        )
        upper_val = IncidentValidation(
            incident_id="INC-CASE-001",
            is_confirmed=True,
            validation_source="Operator",
            notes="Uppercase re-submission",
        )
        await validate_incident_tool(lower_val)
        result = await validate_incident_tool(upper_val)
        assert "already CONFIRMED" in result or "idempotent" in result


class TestUpdateMissionParamsTool:
    """Tests for update_mission_params tool guards and idempotency."""

    @pytest.mark.asyncio
    async def test_dispatch_stores_mission(self) -> None:
        """Dispatching a mission stores it in the missions dict."""
        await update_mission_params_tool("DRONE-T1", "STRAT-001")
        assert "DRONE-T1" in missions
        assert missions["DRONE-T1"]["strategy_id"] == "STRAT-001"

    @pytest.mark.asyncio
    async def test_idempotent_redispatch_returns_identical_params(self) -> None:
        """Idempotent re-dispatch returns byte-identical MissionParameters."""
        params1 = await update_mission_params_tool("DRONE-T2", "STRAT-002")
        params2 = await update_mission_params_tool("DRONE-T2", "STRAT-002")
        assert params1.mission_id == params2.mission_id
        assert params1.strategy_hash == params2.strategy_hash
        assert params1.risk_tolerance == pytest.approx(params2.risk_tolerance)
        assert params1.authorized_actions == params2.authorized_actions

    @pytest.mark.asyncio
    async def test_conflict_guard_blocks_different_strategy(self) -> None:
        """Raises FastMCPError if drone already has an active mission for a different strategy."""
        from fastmcp.exceptions import FastMCPError

        await update_mission_params_tool("DRONE-T3", "STRAT-A")
        with pytest.raises(FastMCPError, match="already has an active mission"):
            await update_mission_params_tool("DRONE-T3", "STRAT-B")

    @pytest.mark.asyncio
    async def test_is_urgent_escalation_via_redispatch_is_blocked(self) -> None:
        """Re-dispatching with is_urgent=True after is_urgent=False is blocked."""
        from fastmcp.exceptions import FastMCPError

        await update_mission_params_tool("DRONE-T4", "STRAT-C", is_urgent=False)
        with pytest.raises(FastMCPError, match="urgency"):
            await update_mission_params_tool("DRONE-T4", "STRAT-C", is_urgent=True)

    @pytest.mark.asyncio
    async def test_capacity_guard_blocks_new_missions(self) -> None:
        """Raises FastMCPError when the mission store is at capacity."""
        from fastmcp.exceptions import FastMCPError

        from resq_mcp.server import MAX_MISSIONS

        for i in range(MAX_MISSIONS):
            missions[f"DRONE-FILL-{i:04d}"] = {
                "strategy_id": "STRAT-X",
                "is_urgent": False,
                "params": {
                    "mission_id": f"MISS-{i:08X}",
                    "target_sector": "Dynamic-Assigned",
                    "authorized_actions": ["autonomous_flight"],
                    "risk_tolerance": 0.5,
                    "strategy_hash": "0xdeadbeef",
                },
                "dispatched_at": "2026-01-01T00:00:00+00:00",
                "dispatched_at_mono": 0.0,
            }

        with pytest.raises(FastMCPError, match="capacity reached"):
            await update_mission_params_tool("DRONE-OVERFLOW", "STRAT-NEW")

    def test_urgent_string_in_strategy_id_does_not_set_high_risk(self) -> None:
        """Regression: URGENT in strategy_id must NOT inject high risk_tolerance."""
        params = update_mission_params("DRONE-INJ", "STRAT-URGENT-FIRE")
        assert params.risk_tolerance == pytest.approx(0.5)

    def test_urgent_flag_sets_high_risk_tolerance(self) -> None:
        """Explicit is_urgent=True sets risk_tolerance=0.9."""
        params = update_mission_params("DRONE-URG", "STRAT-FIRE", is_urgent=True)
        assert params.risk_tolerance == pytest.approx(0.9)
