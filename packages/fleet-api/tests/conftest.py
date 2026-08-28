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

"""Pytest fixtures for the fleet API test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from fleet_api.dependencies import get_store
from fleet_api.main import create_app
from fleet_api.store import FleetStore

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def store() -> FleetStore:
    """Provide a freshly seeded store, isolated from every other test."""
    return FleetStore()


@pytest.fixture
def client(store: FleetStore) -> Iterator[TestClient]:
    """Provide a TestClient whose app is wired to the per-test store.

    Overriding ``get_store`` is what keeps cases independent: the app under test
    never touches the process-wide store, so a deployment created in one test is
    invisible to the next.
    """
    app = create_app()
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
