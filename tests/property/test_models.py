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

"""Property-based tests for ResQ MCP models using Hypothesis."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st
from pydantic import ValidationError

from resq_mcp.core.models import Coordinates
from resq_mcp.drone.models import DeploymentRequest
from resq_mcp.hce.models import IncidentReport


class TestModelsPropertyBased:
    """Property-based tests using Hypothesis."""

    @given(
        lat=st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False),
        lng=st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False),
        status=st.text(min_size=1, max_size=50),
    )
    def test_coordinates_accepts_valid_ranges(self, lat: float, lng: float, status: str) -> None:
        coords = Coordinates(lat=lat, lng=lng, status=status)
        assert coords.lat == lat
        assert coords.lng == lng

    @given(
        lat=st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False),
        lng=st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False),
    )
    def test_coordinates_round_trip(self, lat: float, lng: float) -> None:
        coords = Coordinates(lat=lat, lng=lng, status="test")
        data = coords.model_dump()
        restored = Coordinates(**data)
        assert restored.lat == coords.lat
        assert restored.lng == coords.lng

    @given(priority=st.sampled_from(["low", "medium", "high", "critical"]))
    def test_deployment_request_valid_priorities(self, priority: str) -> None:
        req = DeploymentRequest(sector_id="Sector-1", priority=priority)
        assert req.priority == priority

    @given(
        priority=st.text(min_size=1).filter(
            lambda x: x not in {"low", "medium", "high", "critical"}
        )
    )
    @hyp_settings(max_examples=20)
    def test_deployment_request_rejects_invalid_priorities(self, priority: str) -> None:
        with pytest.raises(ValidationError):
            DeploymentRequest(sector_id="Sector-1", priority=priority)

    @given(source=st.sampled_from(["edge_ai", "human_report", "sensor_network"]))
    def test_incident_report_valid_sources(self, source: str) -> None:
        report = IncidentReport(
            incident_id="INC-HYP",
            source=source,
            sector_id="Sector-1",
            detected_type="test",
            confidence=0.5,
        )
        assert report.source == source

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    def test_incident_report_round_trip(self, confidence: float) -> None:
        report = IncidentReport(
            incident_id="INC-RT",
            source="edge_ai",
            sector_id="Sector-1",
            detected_type="test",
            confidence=confidence,
        )
        data = report.model_dump()
        restored = IncidentReport(**data)
        assert restored.confidence == report.confidence
