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
