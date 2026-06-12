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

"""Pytest configuration and fixtures for ResQ MCP tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from resq_mcp.core.models import Coordinates
from resq_mcp.drone.models import SectorAnalysis
from resq_mcp.dtsop.models import SimulationRequest
from resq_mcp.hce.models import IncidentReport, IncidentValidation

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


@pytest.fixture(autouse=True)
def reset_random_seed() -> None:
    """Reset random seed for reproducible tests where needed.

    Note: Many tests rely on random behavior to verify probability,
    so we don't actually set a seed globally. Individual tests can
    set seeds if needed for specific reproducibility.
    """


@pytest.fixture(autouse=True)
def _reset_security_state() -> Iterator[None]:
    """Isolate per-test security state for the hardened tool wrappers.

    - Clears the process-wide per-tool rate limiter so call counts do not leak
      across tests (a shared sliding window would otherwise cause flaky limits).
    - Disables Safe Mode for the duration of each test so mutating tool wrappers
      exercise their real execution paths. Tests that specifically assert the
      Safe Mode gate re-enable it explicitly via monkeypatch.

    The original ``SAFE_MODE`` value is restored afterwards.
    """
    from resq_mcp.core.config import settings
    from resq_mcp.core.ratelimit import rate_limiter

    rate_limiter.reset()
    original_safe_mode = settings.SAFE_MODE
    settings.SAFE_MODE = False
    try:
        yield
    finally:
        settings.SAFE_MODE = original_safe_mode
        rate_limiter.reset()


@pytest.fixture
def sample_sector_id() -> str:
    """Provide a sample sector ID for tests."""
    return "Sector-1"


@pytest.fixture
def sample_incident_id() -> str:
    """Provide a sample incident ID for tests."""
    return "INC-TEST-001"


@pytest.fixture
def make_incident_report() -> Callable[..., IncidentReport]:
    """Factory fixture for creating IncidentReport instances with defaults."""

    def _factory(
        incident_id: str = "INC-TEST-001",
        source: str = "edge_ai",
        sector_id: str = "Sector-1",
        detected_type: str = "wildfire",
        confidence: float = 0.92,
        evidence_url: str | None = None,
    ) -> IncidentReport:
        return IncidentReport(
            incident_id=incident_id,
            source=source,
            sector_id=sector_id,
            detected_type=detected_type,
            confidence=confidence,
            evidence_url=evidence_url,
        )

    return _factory


@pytest.fixture
def make_incident_validation() -> Callable[..., IncidentValidation]:
    """Factory fixture for creating IncidentValidation instances with defaults."""

    def _factory(
        incident_id: str = "INC-TEST-001",
        is_confirmed: bool = True,
        validation_source: str = "SpoonOS-HCE-Validator",
        correlated_pre_alert_id: str | None = None,
        notes: str = "Auto-confirmed via test fixture",
    ) -> IncidentValidation:
        return IncidentValidation(
            incident_id=incident_id,
            is_confirmed=is_confirmed,
            validation_source=validation_source,
            correlated_pre_alert_id=correlated_pre_alert_id,
            notes=notes,
        )

    return _factory


@pytest.fixture
def make_simulation_request() -> Callable[..., SimulationRequest]:
    """Factory fixture for creating SimulationRequest instances with defaults."""

    def _factory(
        scenario_id: str = "TEST-SCENARIO-001",
        sector_id: str = "Sector-1",
        disaster_type: str = "flood",
        parameters: dict[str, float | str] | None = None,
        priority: str = "standard",
    ) -> SimulationRequest:
        return SimulationRequest(
            scenario_id=scenario_id,
            sector_id=sector_id,
            disaster_type=disaster_type,
            parameters={"water_level": 5.0} if parameters is None else parameters,
            priority=priority,
        )

    return _factory


@pytest.fixture
def make_sector_analysis() -> Callable[..., SectorAnalysis]:
    """Factory fixture for creating SectorAnalysis instances with defaults."""

    def _factory(
        sector_id: str = "Sector-1",
        status: str = "clear",
        detected_object: str = "None",
        confidence: float = 0.0,
        description: str = "No anomalies detected",
    ) -> SectorAnalysis:
        return SectorAnalysis(
            sector_id=sector_id,
            status=status,
            detected_object=detected_object,
            confidence=confidence,
            description=description,
            coordinates=Coordinates(lat=37.3417, lng=-121.9751, status="clear"),
            recommended_action="CONTINUE_MONITORING",
        )

    return _factory
