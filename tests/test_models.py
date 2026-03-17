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

"""Unit tests for the ResQ MCP models module."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st
from pydantic import ValidationError

from resq_mcp.models import (
    Coordinates,
    DeploymentRequest,
    ErrorResponse,
    IncidentReport,
    IncidentValidation,
    MissionParameters,
    PreAlert,
    Sector,
    SectorAnalysis,
    SimulationRequest,
    SwarmStatus,
    VulnerabilityMap,
)


class TestCoordinates:
    """Tests for the Coordinates model."""

    def test_create_valid_coordinates(self) -> None:
        """Test creating valid coordinates."""
        coords = Coordinates(lat=37.7749, lng=-122.4194, status="active")

        assert coords.lat == pytest.approx(37.7749)
        assert coords.lng == pytest.approx(-122.4194)
        assert coords.status == "active"

    def test_coordinates_requires_all_fields(self) -> None:
        """Test that all fields are required."""
        with pytest.raises(ValidationError):
            Coordinates(lat=37.7749, lng=-122.4194)  # type: ignore[call-arg]


class TestSector:
    """Tests for the Sector model."""

    def test_create_sector_with_coordinates(self) -> None:
        """Test creating a sector with nested coordinates."""
        coords = Coordinates(lat=37.7749, lng=-122.4194, status="clear")
        sector = Sector(id="Sector-1", coordinates=coords)

        assert sector.id == "Sector-1"
        assert sector.coordinates.lat == pytest.approx(37.7749)


class TestSectorAnalysis:
    """Tests for the SectorAnalysis model."""

    def test_sector_analysis_with_all_fields(self) -> None:
        """Test creating a complete sector analysis."""
        coords = Coordinates(lat=37.7749, lng=-122.4194, status="alert")
        analysis = SectorAnalysis(
            sector_id="Sector-1",
            status="CRITICAL_ALERT",
            detected_object="Active Wildfire",
            disaster_type="wildfire",
            confidence=0.98,
            description="Large fire detected",
            coordinates=coords,
            video_proof_url="neofs://example.mp4",
            recommended_action="IMMEDIATE_REPORT_TO_BLOCKCHAIN",
        )

        assert analysis.sector_id == "Sector-1"
        assert analysis.disaster_type == "wildfire"
        assert analysis.confidence == pytest.approx(0.98)

    def test_sector_analysis_timestamp_is_utc(self) -> None:
        """Test that timestamp is timezone-aware UTC."""
        coords = Coordinates(lat=37.7749, lng=-122.4194, status="clear")
        analysis = SectorAnalysis(
            sector_id="Sector-1",
            status="clear",
            detected_object="None",
            confidence=0.0,
            description="No anomalies",
            coordinates=coords,
            recommended_action="CONTINUE_MONITORING",
        )

        assert analysis.timestamp.tzinfo is not None
        # Timestamp should be recent
        assert datetime.now(UTC) - analysis.timestamp < timedelta(seconds=1)


class TestSwarmStatus:
    """Tests for the SwarmStatus model."""

    def test_swarm_status_defaults(self) -> None:
        """Test SwarmStatus with required fields only."""
        status = SwarmStatus(
            total_drones=5,
            active_drones=4,
            average_battery=85,
            network_status="operational",
        )

        assert status.total_drones == 5
        assert status.active_drones == 4
        assert status.timestamp.tzinfo is not None
        assert status.last_sync.tzinfo is not None


class TestDeploymentRequest:
    """Tests for the DeploymentRequest model."""

    def test_deployment_request_defaults_to_high_priority(self) -> None:
        """Test that priority defaults to 'high'."""
        request = DeploymentRequest(sector_id="Sector-1")

        assert request.priority == "high"

    def test_deployment_request_with_critical_priority(self) -> None:
        """Test deployment request with critical priority."""
        request = DeploymentRequest(sector_id="Sector-2", priority="critical")

        assert request.priority == "critical"


class TestVulnerabilityMap:
    """Tests for the VulnerabilityMap model."""

    def test_vulnerability_map_creation(self) -> None:
        """Test creating a vulnerability map."""
        vuln = VulnerabilityMap(
            sector_id="Sector-1",
            population_density="high",
            critical_infrastructure=["hospital", "school"],
            flood_risk=0.3,
            fire_risk=0.7,
        )

        assert vuln.sector_id == "Sector-1"
        assert vuln.population_density == "high"
        assert len(vuln.critical_infrastructure) == 2

    def test_vulnerability_map_invalid_density(self) -> None:
        """Test that invalid population density raises error."""
        with pytest.raises(ValidationError):
            VulnerabilityMap(
                sector_id="Sector-1",
                population_density="very_high",  # type: ignore[arg-type]
                critical_infrastructure=[],
                flood_risk=0.5,
                fire_risk=0.5,
            )


class TestPreAlert:
    """Tests for the PreAlert model."""

    def test_pre_alert_with_vulnerability_context(self) -> None:
        """Test creating a pre-alert with nested vulnerability map."""
        vuln = VulnerabilityMap(
            sector_id="Sector-1",
            population_density="medium",
            critical_infrastructure=["bridge"],
            flood_risk=0.8,
            fire_risk=0.2,
        )
        alert = PreAlert(
            alert_id="PRE-12345678",
            sector_id="Sector-1",
            predicted_disaster_type="flood",
            probability=0.85,
            forecast_horizon_hours=24,
            vulnerability_context=vuln,
        )

        assert alert.alert_id == "PRE-12345678"
        assert alert.probability == pytest.approx(0.85)
        assert alert.vulnerability_context.flood_risk == pytest.approx(0.8)


class TestSimulationRequest:
    """Tests for the SimulationRequest model."""

    def test_simulation_request_defaults_to_standard_priority(self) -> None:
        """Test that priority defaults to 'standard'."""
        request = SimulationRequest(
            scenario_id="SCN-001",
            sector_id="Sector-1",
            disaster_type="flood",
            parameters={"water_level": 5.0},
        )

        assert request.priority == "standard"

    def test_simulation_request_with_urgent_priority(self) -> None:
        """Test simulation request with urgent priority."""
        request = SimulationRequest(
            scenario_id="SCN-002",
            sector_id="Sector-2",
            disaster_type="wildfire",
            parameters={"wind_speed": 30.0, "humidity": "low"},
            priority="urgent",
        )

        assert request.priority == "urgent"
        assert request.parameters["wind_speed"] == pytest.approx(30.0)


class TestIncidentReport:
    """Tests for the IncidentReport model."""

    def test_incident_report_from_edge_ai(self) -> None:
        """Test creating an incident report from edge AI."""
        report = IncidentReport(
            incident_id="INC-001",
            source="edge_ai",
            sector_id="Sector-1",
            detected_type="wildfire",
            confidence=0.92,
        )

        assert report.source == "edge_ai"
        assert report.evidence_url is None

    def test_incident_report_invalid_source(self) -> None:
        """Test that invalid source raises validation error."""
        with pytest.raises(ValidationError):
            IncidentReport(
                incident_id="INC-002",
                source="invalid_source",  # type: ignore[arg-type]
                sector_id="Sector-1",
                detected_type="flood",
                confidence=0.8,
            )


class TestIncidentValidation:
    """Tests for the IncidentValidation model."""

    def test_confirmed_incident_validation(self) -> None:
        """Test creating a confirmed validation."""
        validation = IncidentValidation(
            incident_id="INC-001",
            is_confirmed=True,
            validation_source="SpoonOS-HCE-Validator",
            notes="Auto-confirmed due to high confidence",
        )

        assert validation.is_confirmed is True
        assert validation.correlated_pre_alert_id is None


class TestMissionParameters:
    """Tests for the MissionParameters model."""

    def test_mission_parameters_with_blockchain_hash(self) -> None:
        """Test creating mission parameters with strategy hash."""
        params = MissionParameters(
            mission_id="MISS-12345678",
            target_sector="Sector-1",
            authorized_actions=["autonomous_flight", "payload_release_authorized"],
            risk_tolerance=0.9,
            strategy_hash="0xabcdef1234567890",
        )

        assert params.mission_id == "MISS-12345678"
        assert len(params.authorized_actions) == 2
        assert params.strategy_hash.startswith("0x")


class TestErrorResponse:
    """Tests for the ErrorResponse model."""

    def test_error_response_defaults_to_error_status(self) -> None:
        """Test that status defaults to 'error'."""
        error = ErrorResponse(message="Sector not found")

        assert error.status == "error"
        assert error.message == "Sector not found"


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

    @given(priority=st.text(min_size=1).filter(lambda x: x not in {"low", "medium", "high", "critical"}))
    @hyp_settings(max_examples=20)
    def test_deployment_request_rejects_invalid_priorities(self, priority: str) -> None:
        with pytest.raises(ValidationError):
            DeploymentRequest(sector_id="Sector-1", priority=priority)

    @given(source=st.sampled_from(["edge_ai", "human_report", "sensor_network"]))
    def test_incident_report_valid_sources(self, source: str) -> None:
        report = IncidentReport(
            incident_id="INC-HYP", source=source, sector_id="Sector-1",
            detected_type="test", confidence=0.5,
        )
        assert report.source == source

    @given(confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    def test_incident_report_round_trip(self, confidence: float) -> None:
        report = IncidentReport(
            incident_id="INC-RT", source="edge_ai", sector_id="Sector-1",
            detected_type="test", confidence=confidence,
        )
        data = report.model_dump()
        restored = IncidentReport(**data)
        assert restored.confidence == report.confidence
