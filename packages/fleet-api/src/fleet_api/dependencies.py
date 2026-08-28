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

"""Shared FastAPI dependencies.

Routes ask for the store through :func:`get_store` rather than importing the
module-level instance directly. That indirection is what lets tests swap in a
fresh store per case via ``app.dependency_overrides`` instead of mutating global
state and hoping it gets cleaned up.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from fleet_api.store import FleetStore

_store = FleetStore()


def get_store() -> FleetStore:
    """Return the process-wide fleet store.

    Returns:
        FleetStore: The shared store instance.
    """
    return _store


StoreDep = Annotated[FleetStore, Depends(get_store)]
"""Reusable annotation so routes can write ``store: StoreDep`` instead of repeating
``Depends(get_store)`` on every handler."""
