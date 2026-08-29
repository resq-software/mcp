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

"""ResQ Fleet API — authoritative HTTP service for drone fleet state.

Example:
    from fleet_api.main import create_app
    app = create_app()
"""

from fleet_api.models import (
    Deployment,
    DeploymentRequest,
    DroneUnit,
    FleetStatus,
    HealthResponse,
)
from fleet_api.store import FleetStore

__version__ = "0.1.0"

__all__ = [
    "Deployment",
    "DeploymentRequest",
    "DroneUnit",
    "FleetStatus",
    "FleetStore",
    "HealthResponse",
]
