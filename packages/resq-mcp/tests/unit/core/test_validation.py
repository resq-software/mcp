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

"""Tests for identifier and parameter input validation."""

from __future__ import annotations

import pytest

from resq_mcp.core.validation import (
    MAX_IDENTIFIER_LENGTH,
    MAX_PARAM_VALUE_LENGTH,
    MAX_PARAMETERS,
    validate_identifier,
    validate_parameters,
)


class TestValidateIdentifier:
    @pytest.mark.parametrize(
        "value",
        ["INC-123", "DRONE-Alpha", "Sector-1", "PRE-ABC123", "a", "flood", "scope.v1:2"],
    )
    def test_accepts_well_formed_identifiers(self, value: str) -> None:
        assert validate_identifier(value) == value

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            validate_identifier("", field="incident_id")

    def test_rejects_overlong(self) -> None:
        with pytest.raises(ValueError, match="maximum length"):
            validate_identifier("A" * (MAX_IDENTIFIER_LENGTH + 1))

    @pytest.mark.parametrize(
        "value",
        ["../etc/passwd", "rm -rf /", "INC 123", "INC;DROP", "name`whoami`", "-leading", "ünïcode"],
    )
    def test_rejects_injection_and_traversal_payloads(self, value: str) -> None:
        with pytest.raises(ValueError, match="disallowed characters"):
            validate_identifier(value)

    def test_error_includes_field_name(self) -> None:
        with pytest.raises(ValueError, match="drone_id"):
            validate_identifier("bad id", field="drone_id")


class TestValidateParameters:
    def test_accepts_bounded_mapping(self) -> None:
        params: dict[str, float | str] = {"water_level": 2.5, "label": "north"}
        assert validate_parameters(params) == params

    def test_rejects_too_many_entries(self) -> None:
        params: dict[str, float | str] = {f"k{i}": float(i) for i in range(MAX_PARAMETERS + 1)}
        with pytest.raises(ValueError, match="maximum is"):
            validate_parameters(params)

    def test_rejects_overlong_string_value(self) -> None:
        params: dict[str, float | str] = {"note": "x" * (MAX_PARAM_VALUE_LENGTH + 1)}
        with pytest.raises(ValueError, match="value exceeds"):
            validate_parameters(params)

    def test_numeric_values_are_unbounded(self) -> None:
        params: dict[str, float | str] = {"huge": 1e308}
        assert validate_parameters(params) == params
