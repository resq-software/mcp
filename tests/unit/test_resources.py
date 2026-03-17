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
