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

"""Input bounding and identifier validation for ResQ MCP tools.

Implements the "Validate parameters" recommendation from NSA Cybersecurity
Information sheet *Model Context Protocol (MCP): Security Design Considerations*
(PP-26-1834, May 2026): every tool invocation should validate its inputs against
well-defined schemas, expected ranges, character allow-lists, and size bounds to
guard against malformed inputs, prompt-injection, and denial-of-service attempts.

These helpers are deliberately framework-agnostic and raise plain ``ValueError`` so
they compose with both Pydantic ``field_validator`` hooks (which convert
``ValueError`` into a clean ``ValidationError``) and direct calls from tool wrappers.
"""

from __future__ import annotations

import re

# --- Size bounds (named constants — no magic numbers at call sites) ---
MAX_IDENTIFIER_LENGTH: int = 64
"""Maximum length for identifier-shaped fields (IDs, sector names, types)."""

MAX_TEXT_LENGTH: int = 2000
"""Maximum length for free-text fields (notes, descriptions)."""

MAX_SOURCE_LENGTH: int = 128
"""Maximum length for actor/source labels (e.g. ``validation_source``)."""

MAX_PARAMETERS: int = 32
"""Maximum number of entries allowed in a tool ``parameters`` mapping."""

MAX_PARAM_KEY_LENGTH: int = 64
"""Maximum length of a single ``parameters`` key."""

MAX_PARAM_VALUE_LENGTH: int = 256
"""Maximum length of a single string ``parameters`` value."""

# Identifiers must start with an alphanumeric and may then contain a small,
# explicitly enumerated set of separators. This allow-list rejects whitespace,
# path separators, quotes, shell metacharacters, and control characters that are
# the building blocks of injection (CWE-77/78/94/95) and traversal payloads.
_IDENTIFIER_RE = re.compile(rf"^[A-Za-z0-9][A-Za-z0-9._:\-]{{0,{MAX_IDENTIFIER_LENGTH - 1}}}$")


def validate_identifier(value: str, *, field: str = "identifier") -> str:
    """Validate that ``value`` is a safe, bounded identifier.

    Args:
        value: The candidate identifier (e.g. ``"INC-123"``, ``"DRONE-Alpha"``).
        field: Human-readable field name used in error messages.

    Returns:
        The validated value, unchanged (so it is usable inline).

    Raises:
        ValueError: If the value is empty, too long, or contains characters
            outside the allow-list ``[A-Za-z0-9._:-]`` (must start alphanumeric).

    Example:
        >>> validate_identifier("INC-123", field="incident_id")
        'INC-123'
    """
    if not value:
        raise ValueError(f"{field} must not be empty")
    if len(value) > MAX_IDENTIFIER_LENGTH:
        raise ValueError(
            f"{field} exceeds the maximum length of {MAX_IDENTIFIER_LENGTH} characters"
        )
    if _IDENTIFIER_RE.match(value) is None:
        raise ValueError(
            f"{field} contains disallowed characters; only letters, digits, and "
            "'.', '_', '-', ':' are permitted, and it must start with a letter or digit"
        )
    return value


def validate_parameters(params: dict[str, float | str]) -> dict[str, float | str]:
    """Validate a tool ``parameters`` mapping for size and per-value bounds.

    Caps the number of entries, the length of each key, and the length of each
    string value. Numeric values are accepted as-is (range checks belong to the
    domain layer), but unbounded strings — a vector for memory-exhaustion and
    injection — are rejected.

    Args:
        params: The parameters mapping to validate.

    Returns:
        The validated mapping, unchanged.

    Raises:
        ValueError: If the mapping exceeds ``MAX_PARAMETERS`` entries, a key
            exceeds ``MAX_PARAM_KEY_LENGTH``, or a string value exceeds
            ``MAX_PARAM_VALUE_LENGTH``.
    """
    if len(params) > MAX_PARAMETERS:
        raise ValueError(
            f"parameters mapping has {len(params)} entries; the maximum is {MAX_PARAMETERS}"
        )
    for key, raw_value in params.items():
        if len(key) > MAX_PARAM_KEY_LENGTH:
            raise ValueError(
                f"parameter key '{key[:16]}…' exceeds the maximum length of "
                f"{MAX_PARAM_KEY_LENGTH} characters"
            )
        if isinstance(raw_value, str) and len(raw_value) > MAX_PARAM_VALUE_LENGTH:
            raise ValueError(
                f"parameter '{key}' value exceeds the maximum length of "
                f"{MAX_PARAM_VALUE_LENGTH} characters"
            )
    return params
