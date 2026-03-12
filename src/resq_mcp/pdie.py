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

"""PDIE - Predictive Disaster Intelligence Engine.

This module provides predictive disaster intelligence:
- Vulnerability mapping for sectors (population, infrastructure, risks)
- Probabilistic forecasts for disaster events
- Pre-alert generation based on LSTM/GNN model outputs

The current implementation is stubbed with mock data for development.
"""

from __future__ import annotations

import random
import uuid
from typing import Final

from .models import ErrorResponse, PreAlert, VulnerabilityMap

# Probability thresholds for alert generation
_FIRE_RISK_THRESHOLD: Final[float] = 0.5
_FLOOD_RISK_THRESHOLD: Final[float] = 0.5
_ALERT_TRIGGER_PROBABILITY: Final[float] = 0.4

# Mock database of vulnerabilities
VULNERABILITY_DB: Final[dict[str, VulnerabilityMap]] = {
    "Sector-1": VulnerabilityMap(
        sector_id="Sector-1",
        population_density="high",
        critical_infrastructure=["hospital", "power-substation"],
        flood_risk=0.1,
        fire_risk=0.8,
    ),
    "Sector-2": VulnerabilityMap(
        sector_id="Sector-2",
        population_density="medium",
        critical_infrastructure=["school"],
        flood_risk=0.7,
        fire_risk=0.2,
    ),
    "Sector-3": VulnerabilityMap(
        sector_id="Sector-3",
        population_density="low",
        critical_infrastructure=["bridge"],
        flood_risk=0.9,
        fire_risk=0.1,
    ),
    "Sector-4": VulnerabilityMap(
        sector_id="Sector-4",
        population_density="medium",
        critical_infrastructure=["warehouse-district"],
        flood_risk=0.3,
        fire_risk=0.6,
    ),
}


def get_vulnerability_map(sector_id: str) -> VulnerabilityMap | ErrorResponse:
    """Retrieve precomputed vulnerability assessment for a sector.

    Part of PDIE (Predictive Disaster Intelligence Engine) system.
    Provides static infrastructure and risk data used as input to
    predictive models for disaster forecasting.

    Vulnerability Data Includes:
        - Population density classification (low/medium/high)
        - Critical infrastructure inventory (hospitals, bridges, etc.)
        - Flood risk score (0.0-1.0) from terrain and drainage analysis
        - Fire risk score (0.0-1.0) from fuel load and climate data

    Args:
        sector_id: Sector identifier (e.g., "Sector-1" through "Sector-4").

    Returns:
        VulnerabilityMap: Comprehensive vulnerability data if sector exists.
        ErrorResponse: Error message if sector_id is unknown.

    Example:
        >>> vuln = get_vulnerability_map("Sector-1")
        >>> if isinstance(vuln, VulnerabilityMap):
        ...     if vuln.fire_risk > 0.7:
        ...         print(f"High fire risk: {vuln.fire_risk}")
        ...         print(f"Infrastructure: {vuln.critical_infrastructure}")

    Note:
        Production systems would integrate with GIS databases and update
        vulnerability maps periodically based on infrastructure changes
        and seasonal risk factors.
    """
    if sector_id not in VULNERABILITY_DB:
        return ErrorResponse(message=f"No vulnerability data for {sector_id}")
    return VULNERABILITY_DB[sector_id]


def get_predictive_alerts(sector_id: str) -> list[PreAlert] | ErrorResponse:
    """Generate probabilistic disaster forecasts for a sector.

    Part of PDIE system. Simulates the output of LSTM/GNN predictive models
    that analyze weather patterns, sensor trends, and historical data to
    forecast disasters before they occur.

    Prediction Logic (Simulated):
        - Checks vulnerability map for sector risk factors
        - Fire alert: Triggered if fire_risk > 0.5 (40% probability)
          - Probability: 0.75-0.95
          - Horizon: 4-24 hours
        - Flood alert: Triggered if flood_risk > 0.5 (40% probability)
          - Probability: 0.80-0.95
          - Horizon: 12-48 hours
        - Returns empty list if no alerts generated

    Args:
        sector_id: Sector identifier to generate forecasts for.

    Returns:
        list[PreAlert]: Zero or more pre-alerts with disaster forecasts
                        if sector is valid.
        ErrorResponse: Error message if sector_id is unknown.

    Example:
        >>> alerts = get_predictive_alerts("Sector-1")
        >>> if isinstance(alerts, list):
        ...     for alert in alerts:
        ...         print(f"Predicted: {alert.predicted_disaster_type}")
        ...         print(f"Probability: {alert.probability:.0%}")
        ...         print(f"Time horizon: {alert.forecast_horizon_hours}h")

    Integration Note:
        Production PDIE would run continuously with:
        - Weather API integration (NOAA, MeteoBlue)
        - IoT sensor stream processing (water levels, smoke detectors)
        - Historical incident database for pattern matching
        - LSTM models for time-series forecasting
        - GNN models for spatial correlation analysis
    """
    if sector_id not in VULNERABILITY_DB:
        return ErrorResponse(message=f"Sector {sector_id} unknown")

    vuln = VULNERABILITY_DB[sector_id]
    alerts: list[PreAlert] = []

    # Simulate predictive model logic based on risk factors
    if (
        vuln.fire_risk > _FIRE_RISK_THRESHOLD and random.random() < _ALERT_TRIGGER_PROBABILITY  # noqa: S311
    ):
        alerts.append(
            PreAlert(
                alert_id=f"PRE-{uuid.uuid4().hex[:8].upper()}",
                sector_id=sector_id,
                predicted_disaster_type="wildfire",
                probability=0.75 + (random.random() * 0.2),  # noqa: S311
                forecast_horizon_hours=random.randint(4, 24),  # noqa: S311
                vulnerability_context=vuln,
            )
        )

    if (
        vuln.flood_risk > _FLOOD_RISK_THRESHOLD and random.random() < _ALERT_TRIGGER_PROBABILITY  # noqa: S311
    ):
        alerts.append(
            PreAlert(
                alert_id=f"PRE-{uuid.uuid4().hex[:8].upper()}",
                sector_id=sector_id,
                predicted_disaster_type="flood",
                probability=0.80 + (random.random() * 0.15),  # noqa: S311
                forecast_horizon_hours=random.randint(12, 48),  # noqa: S311
                vulnerability_context=vuln,
            )
        )

    return alerts