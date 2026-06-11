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

"""Structured, hash-anchored audit logging for ResQ MCP tool invocations.

Implements the "Instrument for logging and detection" recommendation from NSA
PP-26-1834 (May 2026): all tool and model invocations should be logged with the
exact parameters, identities involved, and — where feasible — cryptographic
hashes of results or output, forming the backbone of forensic response.

Records are emitted as single-line JSON on the dedicated ``resq-mcp.audit`` logger
so they can be routed to a SIEM independently of operational logs. Raw parameter
and result payloads are *hashed* (SHA-256) rather than logged verbatim so the
trail stays tamper-evident without persisting sensitive content (PII, evidence
URLs, mission detail) into log storage.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from resq_mcp.core.config import settings

audit_logger = logging.getLogger("resq-mcp.audit")


def _stable_default(obj: Any) -> Any:
    """Serialiser fallback that keeps the digest deterministic.

    Sets and frozensets have no inherent order, so their ``str`` repr varies
    across processes (hash randomisation). Sorting them yields a stable encoding;
    everything else falls back to ``str`` so hashing never raises.
    """
    if isinstance(obj, (set, frozenset)):
        return sorted(obj, key=repr)
    return str(obj)


def hash_payload(payload: Any) -> str:
    """Return a stable SHA-256 hex digest of a JSON-serialisable payload.

    Keys are sorted so the digest is deterministic regardless of dict ordering,
    sets are sorted, and any other non-serialisable value falls back to ``str``
    so hashing never raises.

    Args:
        payload: Any JSON-serialisable object (dict, list, scalar).

    Returns:
        The 64-character hex SHA-256 digest of the canonical JSON encoding.
    """
    serialised = json.dumps(payload, sort_keys=True, default=_stable_default)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def audit_log(
    action: str,
    *,
    status: str,
    actor: str | None = None,
    parameters: Any | None = None,
    result: Any | None = None,
    **extra: Any,
) -> None:
    """Emit a structured audit record for a tool invocation.

    No-op when ``RESQ_AUDIT_ENABLED`` is false. Parameter and result payloads are
    recorded only as SHA-256 digests; pass small, non-sensitive identifiers via
    ``**extra`` when they should appear in clear text for correlation.

    Args:
        action: The tool or operation name (e.g. ``"run_simulation"``).
        status: Outcome marker (e.g. ``"accepted"``, ``"denied"``, ``"error"``).
        actor: Identity that triggered the call, when known.
        parameters: Input payload to hash into ``parameters_hash``.
        result: Output payload to hash into ``result_hash``.
        **extra: Additional non-sensitive fields merged into the record verbatim
            (e.g. ``incident_id="INC-123"``).
    """
    if not settings.AUDIT_ENABLED:
        return

    record: dict[str, Any] = {
        "event": "mcp.tool.invocation",
        "action": action,
        "status": status,
        "actor": actor or "unknown",
        "transport": settings.TRANSPORT,
        "safe_mode": settings.SAFE_MODE,
    }
    if parameters is not None:
        record["parameters_hash"] = hash_payload(parameters)
    if result is not None:
        record["result_hash"] = hash_payload(result)
    record.update(extra)

    audit_logger.info(json.dumps(record, sort_keys=True, default=str))
