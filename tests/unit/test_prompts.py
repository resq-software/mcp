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

"""Unit tests for the ResQ MCP prompts module."""

from __future__ import annotations

from resq_mcp.prompts import incident_response_plan


class TestIncidentResponsePlan:
    def test_prompt_includes_incident_id(self) -> None:
        result = incident_response_plan("INC-999")
        assert "INC-999" in result

    def test_prompt_references_tools(self) -> None:
        result = incident_response_plan("INC-001")
        assert "get_deployment_strategy" in result
        assert "resq://drones/active" in result

    def test_prompt_includes_output_format(self) -> None:
        result = incident_response_plan("INC-001")
        assert "Situation Summary" in result
        assert "Asset Allocation" in result
        assert "Risk Assessment" in result
