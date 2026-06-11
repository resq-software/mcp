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

"""End-to-end hardening tests at the tool and model boundaries (NSA PP-26-1834).

Covers the Safe Mode mutation gate on side-effecting tools and the bounded-input
/ identifier validation enforced by the Pydantic request models.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import FastMCPError
from pydantic import ValidationError

from resq_mcp.core.validation import MAX_TEXT_LENGTH
from resq_mcp.dtsop.models import SimulationRequest
from resq_mcp.hce.models import IncidentValidation


def _enable_safe_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-enable Safe Mode (the autouse fixture disables it for most tests)."""
    from resq_mcp.core import security

    monkeypatch.setattr(security.settings, "SAFE_MODE", True)


class TestSafeModeGate:
    """run_simulation and update_mission_params must refuse to mutate in Safe Mode."""

    @pytest.mark.asyncio
    async def test_run_simulation_blocked_in_safe_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from resq_mcp.dtsop.tools import run_simulation

        _enable_safe_mode(monkeypatch)
        request = SimulationRequest(
            scenario_id="SCEN-1",
            sector_id="Sector-1",
            disaster_type="flood",
            parameters={"water_level": 2.0},
        )
        with pytest.raises(FastMCPError, match="RESQ_SAFE_MODE"):
            await run_simulation(request)

    @pytest.mark.asyncio
    async def test_update_mission_params_blocked_in_safe_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from resq_mcp.hce.tools import update_mission_params

        _enable_safe_mode(monkeypatch)
        with pytest.raises(FastMCPError, match="RESQ_SAFE_MODE"):
            await update_mission_params("DRONE-1", "STRAT-1")

    @pytest.mark.asyncio
    async def test_run_simulation_succeeds_when_disabled(self) -> None:
        # Safe Mode is off via the autouse fixture; the tool queues normally.
        from resq_mcp.dtsop.tools import run_simulation

        request = SimulationRequest(
            scenario_id="SCEN-OK",
            sector_id="Sector-1",
            disaster_type="flood",
            parameters={"water_level": 2.0},
        )
        result = await run_simulation(request)
        assert "Simulation queued" in result


class TestBoundedIdentifierInputs:
    """Request models reject out-of-policy identifiers and oversized fields."""

    def test_simulation_request_rejects_bad_identifier(self) -> None:
        with pytest.raises(ValidationError):
            SimulationRequest(
                scenario_id="../../etc/passwd",
                sector_id="Sector-1",
                disaster_type="flood",
                parameters={"water_level": 2.0},
            )

    def test_simulation_request_rejects_oversized_parameters(self) -> None:
        with pytest.raises(ValidationError):
            SimulationRequest(
                scenario_id="SCEN-1",
                sector_id="Sector-1",
                disaster_type="flood",
                parameters={f"k{i}": float(i) for i in range(64)},
            )

    def test_incident_validation_rejects_bad_incident_id(self) -> None:
        with pytest.raises(ValidationError):
            IncidentValidation(
                incident_id="INC 123; DROP TABLE",
                is_confirmed=True,
                validation_source="Operator",
                notes="ok",
            )

    def test_incident_validation_rejects_oversized_notes(self) -> None:
        with pytest.raises(ValidationError):
            IncidentValidation(
                incident_id="INC-1",
                is_confirmed=True,
                validation_source="Operator",
                notes="x" * (MAX_TEXT_LENGTH + 1),
            )

    def test_incident_validation_accepts_well_formed_input(self) -> None:
        val = IncidentValidation(
            incident_id="INC-1",
            is_confirmed=True,
            validation_source="Human-Operator-Alice",
            correlated_pre_alert_id="PRE-9",
            notes="Confirmed via video evidence",
        )
        assert val.incident_id == "INC-1"
