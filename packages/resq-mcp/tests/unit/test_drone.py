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

"""Unit tests for the drone feed module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from resq_mcp.core.models import ErrorResponse
from resq_mcp.drone.models import (
    DeploymentStatus,
    NetworkStatus,
    SectorAnalysis,
    SwarmStatus,
)
from resq_mcp.drone.service import (
    DRONE_SECTORS,
    FLEET_ROSTER,
    get_all_sectors_status,
    get_drone_swarm_status,
    get_fleet_roster,
    request_drone_deployment,
    scan_current_sector,
)


class TestGetFleetRoster:
    """Tests for the get_fleet_roster function."""

    def test_returns_the_module_roster(self) -> None:
        """The accessor exposes FLEET_ROSTER without copying or reordering it."""
        assert get_fleet_roster() == FLEET_ROSTER

    def test_roster_is_not_empty(self) -> None:
        """A deployment with no drones would make every fleet metric meaningless."""
        assert len(get_fleet_roster()) > 0

    def test_drone_ids_are_unique(self) -> None:
        """Duplicate IDs would make per-drone telemetry ambiguous."""
        ids = [unit.drone_id for unit in get_fleet_roster()]

        assert len(ids) == len(set(ids))

    def test_every_home_sector_is_a_monitored_sector(self) -> None:
        """A drone stationed outside the monitored network could never be tasked."""
        for unit in get_fleet_roster():
            assert unit.home_sector in DRONE_SECTORS


class TestScanCurrentSector:
    """Tests for the scan_current_sector function."""

    def test_scan_valid_sector_returns_analysis(self) -> None:
        """Test scanning a valid sector returns SectorAnalysis."""
        result = scan_current_sector("Sector-1")

        assert isinstance(result, SectorAnalysis)
        assert result.sector_id == "Sector-1"
        assert result.coordinates.lat == pytest.approx(37.3417)
        assert result.coordinates.lng == pytest.approx(-121.9751)

    def test_scan_invalid_sector_returns_error(self) -> None:
        """Test scanning an invalid sector returns ErrorResponse."""
        result = scan_current_sector("Invalid-Sector")

        assert isinstance(result, ErrorResponse)
        assert "not found" in result.message

    def test_scan_returns_clear_or_alert_status(self) -> None:
        """Test that scan returns either clear or alert status."""
        # Test clear status (random > 0.3)
        with patch("resq_mcp.drone.service.random.random", return_value=0.5):
            result = scan_current_sector("Sector-1")
            assert isinstance(result, SectorAnalysis)
            assert result.status == "clear"

        # Test critical status (random < 0.3)
        with patch("resq_mcp.drone.service.random.random", return_value=0.1):
            result = scan_current_sector("Sector-1")
            assert isinstance(result, SectorAnalysis)
            assert result.status == "CRITICAL_ALERT"

    def test_critical_alert_has_disaster_type(self) -> None:
        """Test that critical alerts include disaster type."""
        # Run until we get a critical alert
        for _ in range(100):
            result = scan_current_sector("Sector-2")
            if isinstance(result, SectorAnalysis) and result.status == "CRITICAL_ALERT":
                assert result.disaster_type is not None
                assert result.video_proof_url is not None
                assert result.confidence > 0.8
                break


class TestGetAllSectorsStatus:
    """Tests for the get_all_sectors_status function."""

    def test_returns_network_status(self) -> None:
        """Test that function returns NetworkStatus."""
        result = get_all_sectors_status()

        assert isinstance(result, NetworkStatus)
        assert result.total_sectors == len(DRONE_SECTORS)

    def test_includes_all_sectors(self) -> None:
        """Test that all sectors are included in status."""
        result = get_all_sectors_status()

        # All sectors should be present
        for sector_id in DRONE_SECTORS:
            assert sector_id in result.sectors

    def test_critical_alerts_count_matches(self) -> None:
        """Test that critical_alerts count matches actual alerts."""
        result = get_all_sectors_status()

        actual_critical = sum(1 for s in result.sectors.values() if s.status == "CRITICAL_ALERT")
        assert result.critical_alerts == actual_critical


class TestGetDroneSwarmStatus:
    """Tests for the get_drone_swarm_status function."""

    def test_returns_swarm_status(self) -> None:
        """Test that function returns SwarmStatus."""
        result = get_drone_swarm_status()

        assert isinstance(result, SwarmStatus)

    def test_total_drones_tracks_the_fleet_roster(self) -> None:
        """total_drones is derived from FLEET_ROSTER, not a hardcoded literal."""
        result = get_drone_swarm_status()

        assert result.total_drones == len(FLEET_ROSTER)

    def test_swarm_has_valid_drone_counts(self) -> None:
        """Test that drone counts are valid."""
        result = get_drone_swarm_status()

        assert result.total_drones == 3
        assert 2 <= result.active_drones <= 3

    def test_swarm_has_valid_battery(self) -> None:
        """Test that battery level is within expected range."""
        result = get_drone_swarm_status()

        assert 60 <= result.average_battery <= 100

    def test_swarm_network_is_operational(self) -> None:
        """Test that network status is operational."""
        result = get_drone_swarm_status()

        assert result.network_status == "operational"


class TestRequestDroneDeployment:
    """Tests for the request_drone_deployment function."""

    def test_deploy_to_valid_sector_succeeds(self) -> None:
        """Test deployment to valid sector returns DeploymentStatus."""
        result = request_drone_deployment("Sector-1")

        assert isinstance(result, DeploymentStatus)
        assert result.status == "deployed"
        assert result.sector_id == "Sector-1"
        assert result.priority == "high"

    def test_deploy_to_invalid_sector_returns_error(self) -> None:
        """Test deployment to invalid sector returns ErrorResponse."""
        result = request_drone_deployment("Invalid-Sector")

        assert isinstance(result, ErrorResponse)
        assert "not found" in result.message

    def test_deploy_with_custom_priority(self) -> None:
        """Test deployment with custom priority."""
        result = request_drone_deployment("Sector-2", priority="critical")

        assert isinstance(result, DeploymentStatus)
        assert result.priority == "critical"

    def test_deploy_assigns_drone_id(self) -> None:
        """Test that deployment assigns a valid drone ID."""
        result = request_drone_deployment("Sector-3")

        assert isinstance(result, DeploymentStatus)
        assert result.drone_id.startswith("UNIT-")

    def test_deploy_has_valid_eta(self) -> None:
        """Test that deployment has valid ETA."""
        result = request_drone_deployment("Sector-4")

        assert isinstance(result, DeploymentStatus)
        assert 30 <= result.eta_seconds <= 120


class TestDroneToolWrappers:
    """Tests for the MCP tool wrappers exposing the drone fleet service."""

    @pytest.mark.asyncio
    async def test_scan_tool_returns_analysis(self) -> None:
        from resq_mcp.drone.tools import scan_current_sector as scan_tool

        result = await scan_tool("Sector-1")

        assert isinstance(result, SectorAnalysis)

    @pytest.mark.asyncio
    async def test_scan_tool_unknown_sector_raises(self) -> None:
        """Unknown sectors surface as FastMCPError, not an ErrorResponse payload."""
        from fastmcp.exceptions import FastMCPError

        from resq_mcp.drone.tools import scan_current_sector as scan_tool

        with pytest.raises(FastMCPError):
            await scan_tool("Sector-999")

    @pytest.mark.asyncio
    async def test_network_and_swarm_tools_return_models(self) -> None:
        from resq_mcp.drone.tools import (
            get_all_sectors_status as network_tool,
        )
        from resq_mcp.drone.tools import (
            get_drone_swarm_status as swarm_tool,
        )

        assert isinstance(await network_tool(), NetworkStatus)
        assert isinstance(await swarm_tool(), SwarmStatus)

    @pytest.mark.asyncio
    async def test_deployment_tool_returns_status(self) -> None:
        """Safe Mode is disabled by the autouse fixture, so the mutation runs."""
        from resq_mcp.drone.tools import request_drone_deployment as deploy_tool

        result = await deploy_tool("Sector-1", priority="critical")

        assert isinstance(result, DeploymentStatus)
        assert result.priority == "critical"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad_sector",
        ["../../etc/passwd", "Sector 1", "bad;semi", "A" * 300],
        ids=["path-traversal", "space", "semicolon", "over-length"],
    )
    async def test_tools_reject_malformed_identifiers(self, bad_sector: str) -> None:
        """Raw sector_id arguments are checked against the identifier allow-list.

        The drone models carry no identifier field_validator (unlike the HCE
        models), so preflight() is the only allow-list check in front of the
        lookup. Both the read and the mutating path must reject the same inputs.
        """
        from fastmcp.exceptions import FastMCPError

        from resq_mcp.drone.tools import request_drone_deployment as deploy_tool
        from resq_mcp.drone.tools import scan_current_sector as scan_tool

        with pytest.raises(FastMCPError):
            await scan_tool(bad_sector)
        with pytest.raises(FastMCPError):
            await deploy_tool(bad_sector)
