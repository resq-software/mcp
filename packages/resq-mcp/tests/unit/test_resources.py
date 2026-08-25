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

"""Unit tests for the ResQ MCP resources module."""

from __future__ import annotations

import re

from resq_mcp.drone.service import get_fleet_roster
from resq_mcp.resources import list_active_drones


class TestListActiveDrones:
    def test_returns_fleet_status(self) -> None:
        result = list_active_drones()
        assert "DRONE-Alpha" in result
        assert "DRONE-Beta" in result
        assert "DRONE-Gamma" in result

    def test_includes_all_drone_types(self) -> None:
        result = list_active_drones()
        assert "Surveillance" in result
        assert "Payload" in result
        assert "Relay" in result

    def test_lists_every_drone_in_the_service_roster(self) -> None:
        """The rendered roster is derived from the service, not hardcoded here."""
        result = list_active_drones()
        roster = get_fleet_roster()

        assert roster, "fleet roster must not be empty"
        for unit in roster:
            assert unit.drone_id in result
            assert unit.role in result
            assert unit.home_sector in result

    def test_reports_live_fleet_summary(self) -> None:
        """The summary line carries real swarm metrics, not fabricated ones."""
        result = list_active_drones()

        assert "network operational" in result
        assert re.search(r"Fleet: \d+/\d+ active", result)
        assert re.search(r"average battery \d+%", result)

    def test_active_count_never_exceeds_the_roster_size(self) -> None:
        """Regression: the resource must not claim more drones than the fleet has."""
        for _ in range(20):
            result = list_active_drones()
            match = re.search(r"Fleet: (\d+)/(\d+) active", result)
            assert match is not None
            active, total = int(match.group(1)), int(match.group(2))
            assert total == len(get_fleet_roster())
            assert active <= total
