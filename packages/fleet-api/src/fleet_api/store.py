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

"""In-memory persistence for fleet state.

The store is deliberately the only place that holds mutable state, and it knows
nothing about HTTP. Routes translate its return values into status codes; swapping
this class for a SQLite or Postgres implementation should not require touching a
single route.

Lookups that cannot be satisfied return ``None`` rather than raising, so the HTTP
layer decides what a miss means (usually 404).
"""

from __future__ import annotations

import threading
import uuid
from typing import Final

from fleet_api.models import Deployment, DeploymentPriority, DroneUnit, FleetStatus

MONITORED_SECTORS: Final[frozenset[str]] = frozenset(
    {"Sector-1", "Sector-2", "Sector-3", "Sector-4"}
)

# Seed fleet. Mirrors the roster in resq-mcp's drone service so that package can
# be pointed at this API without its callers observing a different fleet.
_SEED_FLEET: Final[tuple[DroneUnit, ...]] = (
    DroneUnit(
        drone_id="DRONE-Alpha",
        role="Surveillance",
        home_sector="Sector-4",
        battery_percent=78,
        is_active=True,
    ),
    DroneUnit(
        drone_id="DRONE-Beta",
        role="Payload",
        home_sector="Sector-2",
        battery_percent=64,
        is_active=True,
    ),
    DroneUnit(
        drone_id="DRONE-Gamma",
        role="Relay",
        home_sector="Sector-4",
        battery_percent=92,
        is_active=True,
    ),
)

# A drone below this charge is not eligible for a new mission.
MIN_DEPLOYABLE_BATTERY: Final[int] = 20

# A deployment in one of these states no longer occupies its drone.
_TERMINAL_STATUSES: Final[frozenset[str]] = frozenset({"completed", "cancelled"})

# Rough travel-time model: same sector is quick, cross-sector costs more.
_ETA_SAME_SECTOR_SECONDS: Final[int] = 30
_ETA_CROSS_SECTOR_SECONDS: Final[int] = 90


class FleetStore:
    """Thread-safe in-memory store for drones and deployments.

    A single instance is shared by the running application. Tests construct their
    own instance per test so state never leaks between cases.
    """

    def __init__(self) -> None:
        """Create a store seeded with the default fleet and no deployments."""
        self._lock = threading.Lock()
        self._drones: dict[str, DroneUnit] = {}
        self._deployments: dict[str, Deployment] = {}
        self.reset()

    def reset(self) -> None:
        """Restore the store to its seeded state, discarding all deployments."""
        with self._lock:
            self._drones = {unit.drone_id: unit.model_copy() for unit in _SEED_FLEET}
            self._deployments = {}

    def list_drones(self) -> list[DroneUnit]:
        """Return every drone in the fleet, ordered by identifier.

        Returns:
            list[DroneUnit]: All known drones. Empty only if the fleet was cleared.
        """
        with self._lock:
            return [self._drones[key].model_copy() for key in sorted(self._drones)]

    def get_drone(self, drone_id: str) -> DroneUnit | None:
        """Look up a single drone.

        Args:
            drone_id: The identifier to look up. Matched case-sensitively.

        Returns:
            DroneUnit | None: The drone, or ``None`` if no such drone exists.
        """
        with self._lock:
            unit = self._drones.get(drone_id)
            return unit.model_copy() if unit is not None else None

    def fleet_status(self) -> FleetStatus:
        """Compute an aggregate snapshot from the current drone records.

        Every figure is derived from the stored drones, so the aggregate can never
        contradict what ``list_drones`` reports.

        Returns:
            FleetStatus: Totals, active count, mean battery, and mesh health. An
            empty fleet reports zeroes and ``"offline"``.
        """
        with self._lock:
            drones = list(self._drones.values())

        if not drones:
            return FleetStatus(
                total_drones=0,
                active_drones=0,
                average_battery=0,
                network_status="offline",
            )

        active = [unit for unit in drones if unit.is_active]
        average_battery = sum(unit.battery_percent for unit in drones) // len(drones)
        return FleetStatus(
            total_drones=len(drones),
            active_drones=len(active),
            average_battery=average_battery,
            network_status="operational" if active else "degraded",
        )

    def set_active(self, drone_id: str, active: bool) -> None:
        """Set a drone's operational flag.

        ``is_active`` means "online and airworthy" — it is not a busy flag. A drone
        flying a mission stays active; engagement is tracked through deployments.

        Args:
            drone_id: The drone to update. Unknown identifiers are ignored.
            active: The new operational state.
        """
        with self._lock:
            unit = self._drones.get(drone_id)
            if unit is not None:
                self._drones[drone_id] = unit.model_copy(update={"is_active": active})

    def set_battery(self, drone_id: str, percent: int) -> None:
        """Set a drone's charge level.

        Args:
            drone_id: The drone to update. Unknown identifiers are ignored.
            percent: New charge, 0-100.
        """
        with self._lock:
            unit = self._drones.get(drone_id)
            if unit is not None:
                self._drones[drone_id] = unit.model_copy(update={"battery_percent": percent})

    def _engaged_drone_ids(self) -> set[str]:
        """Return drones currently flying a non-terminal mission.

        Caller must hold ``self._lock``.
        """
        return {
            record.drone_id
            for record in self._deployments.values()
            if record.status not in _TERMINAL_STATUSES
        }

    def dispatch(
        self,
        sector_id: str,
        priority: DeploymentPriority,
    ) -> Deployment | None:
        """Select an eligible drone, engage it, and record the dispatch.

        Selection and recording happen under a single lock, so two concurrent
        callers can never be handed the same drone. A drone is eligible when it is
        active, charged to at least ``MIN_DEPLOYABLE_BATTERY``, and not already
        flying a mission that has yet to reach a terminal state.

        Preference order: a drone already stationed in the target sector, then the
        most-charged candidate elsewhere, then lowest identifier for stability.

        Args:
            sector_id: The sector to send a drone to.
            priority: Urgency the mission is filed under.

        Returns:
            Deployment | None: The stored dispatch record, or ``None`` when no
            drone is currently eligible.
        """
        with self._lock:
            engaged = self._engaged_drone_ids()
            eligible = [
                unit
                for unit in self._drones.values()
                if unit.is_active
                and unit.battery_percent >= MIN_DEPLOYABLE_BATTERY
                and unit.drone_id not in engaged
            ]
            if not eligible:
                return None

            eligible.sort(
                key=lambda unit: (
                    unit.home_sector != sector_id,
                    -unit.battery_percent,
                    unit.drone_id,
                )
            )
            drone = eligible[0]
            eta = (
                _ETA_SAME_SECTOR_SECONDS
                if drone.home_sector == sector_id
                else _ETA_CROSS_SECTOR_SECONDS
            )
            deployment = Deployment(
                deployment_id=f"DEP-{uuid.uuid4().hex[:8].upper()}",
                drone_id=drone.drone_id,
                sector_id=sector_id,
                priority=priority,
                eta_seconds=eta,
            )
            self._deployments[deployment.deployment_id] = deployment
            return deployment

    def complete_deployment(self, deployment_id: str) -> Deployment | None:
        """Move a dispatch to ``completed``, releasing its drone for reuse.

        Engagement is derived from deployment status, so completing a mission is
        what frees the drone — there is no separate busy flag to clear.

        Args:
            deployment_id: The dispatch to close out.

        Returns:
            Deployment | None: The updated record, or ``None`` if unknown.
        """
        with self._lock:
            record = self._deployments.get(deployment_id)
            if record is None:
                return None
            updated = record.model_copy(update={"status": "completed"})
            self._deployments[deployment_id] = updated
            return updated

    def get_deployment(self, deployment_id: str) -> Deployment | None:
        """Look up a single deployment.

        Args:
            deployment_id: The dispatch identifier.

        Returns:
            Deployment | None: The record, or ``None`` if unknown.
        """
        with self._lock:
            return self._deployments.get(deployment_id)

    def list_deployments(self) -> list[Deployment]:
        """Return every recorded deployment, newest first.

        Returns:
            list[Deployment]: All dispatch records.
        """
        with self._lock:
            records = list(self._deployments.values())
        return sorted(records, key=lambda record: record.created_at, reverse=True)
