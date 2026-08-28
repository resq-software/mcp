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

"""Application entry point for the ResQ fleet API.

Builds the FastAPI app, mounts the routers, and exposes a console script that
serves it with uvicorn.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from fleet_api import __version__
from fleet_api.models import HealthResponse
from fleet_api.routers import deployments, drones

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

SERVICE_NAME = "fleet-api"

logger = logging.getLogger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Log service start and shutdown around the application's lifetime.

    Args:
        _app: The application being started. Unused, but required by the protocol.

    Yields:
        None: Control returns to the server for request handling.
    """
    logger.info("%s %s starting", SERVICE_NAME, __version__)
    yield
    logger.info("%s shutting down", SERVICE_NAME)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    A factory rather than a module-level singleton so tests can build isolated
    instances without import-order side effects.

    Returns:
        FastAPI: The configured application with all routers mounted.
    """
    app = FastAPI(
        title="ResQ Fleet API",
        description="Authoritative store for ResQ drone fleet composition and dispatch.",
        version=__version__,
        lifespan=lifespan,
    )

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        """Report that the service is up.

        Returns:
            HealthResponse: Service name and version.
        """
        return HealthResponse(service=SERVICE_NAME, version=__version__)

    app.include_router(drones.router)
    app.include_router(deployments.router)
    return app


app = create_app()


def run() -> None:
    """Serve the application with uvicorn.

    Reads ``FLEET_API_HOST`` and ``FLEET_API_PORT`` from the environment, falling
    back to ``127.0.0.1:8080``.
    """
    import uvicorn

    uvicorn.run(
        "fleet_api.main:app",
        host=os.getenv("FLEET_API_HOST", "127.0.0.1"),
        port=int(os.getenv("FLEET_API_PORT", "8080")),
    )


if __name__ == "__main__":
    run()
