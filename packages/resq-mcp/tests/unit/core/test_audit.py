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

"""Tests for structured, hash-anchored audit logging."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from resq_mcp.core.audit import audit_log, hash_payload

if TYPE_CHECKING:
    import pytest
    from _pytest.logging import LogCaptureFixture


class TestHashPayload:
    def test_is_deterministic_and_key_order_independent(self) -> None:
        assert hash_payload({"a": 1, "b": 2}) == hash_payload({"b": 2, "a": 1})

    def test_distinct_payloads_differ(self) -> None:
        assert hash_payload({"a": 1}) != hash_payload({"a": 2})

    def test_is_sha256_hex(self) -> None:
        digest = hash_payload({"x": "y"})
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_non_serialisable_falls_back_to_str(self) -> None:
        # object() is not JSON-serialisable; default=str must keep hashing total.
        assert len(hash_payload({"obj": object()})) == 64

    def test_set_values_hash_deterministically(self) -> None:
        # Sets have no inherent order; the digest must not depend on insertion order.
        assert hash_payload({"s": {3, 1, 2}}) == hash_payload({"s": {2, 3, 1}})
        assert hash_payload({"s": frozenset({"b", "a"})}) == hash_payload({"s": {"a", "b"}})


class TestAuditLog:
    def test_emits_record_with_hashes(self, caplog: LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="resq-mcp.audit"):
            audit_log(
                "run_simulation",
                status="accepted",
                actor="agent-1",
                parameters={"scenario_id": "S1"},
                result={"sim_id": "SIM-1"},
                scenario_id="S1",
            )
        record = json.loads(caplog.records[-1].getMessage())
        assert record["action"] == "run_simulation"
        assert record["status"] == "accepted"
        assert record["actor"] == "agent-1"
        assert record["scenario_id"] == "S1"
        assert record["parameters_hash"] == hash_payload({"scenario_id": "S1"})
        assert record["result_hash"] == hash_payload({"sim_id": "SIM-1"})

    def test_actor_defaults_to_unknown(self, caplog: LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="resq-mcp.audit"):
            audit_log("validate_incident", status="recorded")
        record = json.loads(caplog.records[-1].getMessage())
        assert record["actor"] == "unknown"
        assert "parameters_hash" not in record

    def test_noop_when_disabled(
        self, caplog: LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from resq_mcp.core import audit

        monkeypatch.setattr(audit.settings, "AUDIT_ENABLED", False)
        with caplog.at_level(logging.INFO, logger="resq-mcp.audit"):
            audit_log("run_simulation", status="accepted")
        assert caplog.records == []
