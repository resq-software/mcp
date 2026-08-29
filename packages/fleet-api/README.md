<!--
  Copyright 2026 ResQ

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# ResQ Fleet API

A small FastAPI service that owns drone fleet state — composition, health, and
dispatch — behind a real HTTP boundary.

Today `resq-mcp` keeps fleet state in module-level Python dicts, which means the
MCP server *is* the database. This service exists so that state can live behind a
network boundary instead, the way it would in a real deployment. It is a
deliberately small Python stand-in for the platform's Coordination API.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Quick start

```bash
cd packages/fleet-api
uv sync
uv run fleet-api          # serves on http://127.0.0.1:8080
```

Then open <http://127.0.0.1:8080/docs> for the generated OpenAPI UI, which lets
you call every endpoint from the browser.

Host and port are read from `FLEET_API_HOST` and `FLEET_API_PORT`.

## Endpoints

| Method | Path | Purpose | Notable responses |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Liveness probe | `200` |
| `GET` | `/drones` | Full fleet roster | `200` |
| `GET` | `/drones/{drone_id}` | One drone | `200`, `404` unknown drone |
| `GET` | `/fleet/status` | Aggregate fleet health | `200` |
| `POST` | `/deployments` | Dispatch a drone to a sector | `201`, `404` unknown sector, `409` none available, `422` bad body |
| `GET` | `/deployments` | All dispatch records, newest first | `200` |
| `GET` | `/deployments/{deployment_id}` | One dispatch | `200`, `404` unknown |

### Example

```bash
curl -s localhost:8080/fleet/status
curl -s -X POST localhost:8080/deployments \
  -H 'content-type: application/json' \
  -d '{"sector_id": "Sector-2", "priority": "critical"}'
```

## Design notes

**Aggregates are computed, never stored.** `GET /fleet/status` derives every
figure from the drone records the store holds, so it cannot contradict
`GET /drones`. This is the same class of bug that was fixed in `resq-mcp`'s
`resq://drones/active` resource, avoided here by construction.

**Dispatch assigns real drones.** `POST /deployments` picks from the actual
roster — preferring a drone already stationed in the target sector, then the
best-charged one elsewhere — so the returned `drone_id` always resolves via
`GET /drones/{drone_id}`. Drones that are inactive or under 20% battery are not
eligible, which is what produces the `409`.

**The store knows nothing about HTTP.** `FleetStore` returns `None` for misses
and lets the routers decide what a miss means. Replacing it with SQLite should
not require touching a route.

**Routes receive the store by injection.** Handlers take `store: StoreDep`
rather than importing a global, which is what lets the test suite give every
test a private store through `app.dependency_overrides`.

## Development

```bash
uv run pytest                    # tests + coverage
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format
uv run mypy src/                 # strict type checking
uv run interrogate               # docstring coverage
```

## Status

Fleet data is seeded in memory and resets on restart. Persistence, authentication,
and live telemetry ingestion are not implemented.
