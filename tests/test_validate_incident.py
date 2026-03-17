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

"""Tests for the validate_incident tool."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from resq_mcp.models import IncidentValidation
from resq_mcp.server import validate_incident

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


class TestValidateIncident:
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
            result = await validate_incident(val)

        assert "successfully CONFIRMED" in result
        assert "INC-CONFIRM-001" in result

        # Verify logging
        assert "Incident INC-CONFIRM-001 CONFIRMED by Human-Operator" in caplog.text
        assert "Notes: Confirmed via visual evidence" in caplog.text

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
            result = await validate_incident(val)

        assert "successfully REJECTED" in result
        assert "INC-REJECT-002" in result

        # Verify logging
        assert "Incident INC-REJECT-002 REJECTED by Auto-Validator" in caplog.text
        assert "Notes: Rejected due to low confidence" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_with_correlated_pre_alert(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-CORR-003", is_confirmed=True,
            validation_source="PDIE-Correlation-Engine",
            correlated_pre_alert_id="PRE-ALERT-789",
            notes="Correlated with predictive alert PRE-ALERT-789",
        )
        with caplog.at_level(logging.INFO):
            result = await validate_incident(val)
        assert "successfully CONFIRMED" in result

    @pytest.mark.asyncio
    async def test_validate_with_sensor_network_source(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-SENSOR-004", is_confirmed=True,
            validation_source="Sensor-Network-Validator",
            notes="Multiple ground sensors triggered",
        )
        with caplog.at_level(logging.INFO):
            result = await validate_incident(val)
        assert "successfully CONFIRMED" in result
        assert "Sensor-Network-Validator" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_reject_with_detailed_notes(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-FP-005", is_confirmed=False,
            validation_source="Human-Operator-Bob",
            notes="False positive: construction activity, not fire",
        )
        with caplog.at_level(logging.INFO):
            result = await validate_incident(val)
        assert "successfully REJECTED" in result
        assert "construction activity" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_log_format_contains_all_fields(self, caplog: LogCaptureFixture) -> None:
        val = IncidentValidation(
            incident_id="INC-LOG-006", is_confirmed=True,
            validation_source="Audit-Test-Source",
            notes="Testing log format completeness",
        )
        with caplog.at_level(logging.INFO):
            await validate_incident(val)
        log_text = caplog.text
        assert "INC-LOG-006" in log_text
        assert "CONFIRMED" in log_text
        assert "Audit-Test-Source" in log_text
        assert "Testing log format completeness" in log_text
