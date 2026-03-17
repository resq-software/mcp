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

"""Shared domain models for the ResQ MCP server.

These Pydantic models define the core data contracts shared across all subsystems.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel


def _utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware).

    Helper function for Pydantic Field default_factory to ensure all
    timestamps are timezone-aware and use UTC for consistency across
    distributed systems.

    Returns:
        datetime: Current time in UTC with timezone info.

    Note:
        Using timezone-aware datetimes prevents ambiguity in logs and
        ensures correct serialization across different time zones.
    """
    return datetime.now(UTC)


class Coordinates(BaseModel):
    """Geographic coordinates with status indicator.

    Represents a geographic point in decimal degrees (WGS84 datum)
    with an associated status flag for monitoring.

    Attributes:
        lat: Latitude in decimal degrees (-90 to +90).
        lng: Longitude in decimal degrees (-180 to +180).
        status: Current status indicator (e.g., "clear", "critical").

    Example:
        >>> coords = Coordinates(lat=37.3417, lng=-121.9751, status="clear")
        >>> print(f"Position: {coords.lat}, {coords.lng}")
    """

    lat: float
    lng: float
    status: str


class Sector(BaseModel):
    """A monitored geographic sector in the drone surveillance network.

    Sectors are predefined geographic zones monitored by the drone fleet
    for disaster detection and response coordination.

    Attributes:
        id: Unique sector identifier (e.g., "Sector-1").
        coordinates: Center point coordinates with status.
    """

    id: str
    coordinates: Coordinates


class DetectedObject(BaseModel):
    """An object detected by drone sensors during surveillance.

    Represents the output of edge AI object detection running on drone
    hardware or ground processing stations.

    Attributes:
        name: Human-readable name of detected object (default: "None").
        type: Classification type (e.g., "fire", "vehicle", "person").
        confidence: Detection confidence score (0.0 to 1.0).
        description: Detailed description of the detection.
    """

    name: str = "None"
    type: str = "unknown"
    confidence: float = 0.0
    description: str = "No anomalies detected"


class DisasterScenario(BaseModel):
    """A disaster scenario template for simulation and detection.

    Defines the characteristics of a disaster type that can be detected
    by drone surveillance or used as input for digital twin simulations.

    Attributes:
        type: Disaster category (e.g., "wildfire", "flood", "earthquake").
        name: Human-readable scenario name.
        confidence: Detection confidence or scenario likelihood (0.0 to 1.0).
        description: Detailed scenario description including characteristics.
    """

    type: str
    name: str
    confidence: float
    description: str


class ErrorResponse(BaseModel):
    """Standard error response for failed operations.

    Used across all subsystems to provide consistent error messaging.
    Returned instead of raising exceptions for expected error conditions
    (e.g., invalid sector ID, missing data).

    Attributes:
        status: Always "error" to distinguish from success responses.
        message: Human-readable error description.

    Example:
        >>> error = ErrorResponse(message="Sector not found")
        >>> if isinstance(result, ErrorResponse):
        ...     print(f"Error: {result.message}")
    """

    status: Literal["error"] = "error"
    message: str
