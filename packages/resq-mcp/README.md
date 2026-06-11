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

# ResQ MCP: Disaster Response Intelligence for AI

[![CI](https://img.shields.io/github/actions/workflow/status/resq-software/pypi/ci.yml?branch=main&label=ci&style=flat-square)](https://github.com/resq-software/pypi/actions)
[![PyPI](https://img.shields.io/pypi/v/resq-mcp?style=flat-square)](https://pypi.org/project/resq-mcp/)
[![Docker](https://img.shields.io/docker/v/resqsoftware/mcp?label=docker&style=flat-square)](https://hub.docker.com/r/resqsoftware/mcp)
[![GHCR](https://img.shields.io/badge/ghcr.io-resq--software%2Fmcp-blue?style=flat-square)](https://github.com/resq-software/pypi/pkgs/container/mcp)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg?style=flat-square)](./LICENSE)

A production-ready Model Context Protocol (MCP) server that connects AI agents to the ResQ platform's robotics, physics simulations, and disaster telemetry.

### Key Features

- **Drone Fleet Command** — Real-time telemetry, sector scanning, and autonomous swarm deployment via the Hybrid Coordination Engine (HCE).
- **Predictive Intelligence** — Probabilistic disaster forecasting and sector-level vulnerability mapping (PDIE).
- **Digital Twin Simulations** — Physics-based RL optimization strategies for incident response (DTSOP).
- **Safe-Mode Execution** — Built-in protection prevents destructive platform mutations by default.

### Requirements

- Python 3.11 or newer
- VS Code, Cursor, Claude Desktop, or any other MCP client

---

## Getting Started

Install the ResQ MCP server with your client. The **standard config** works in most tools:

```json
{
  "mcpServers": {
    "resq": {
      "command": "uvx",
      "args": ["resq-mcp"],
      "env": {
        "RESQ_SAFE_MODE": "true"
      }
    }
  }
}
```

<details>
<summary>VS Code</summary>

A pre-configured [`.vscode/mcp.json`](.vscode/mcp.json) is included in this repo — just open the project and the server is available.

Or install manually. Add to your user or workspace `mcp.json`:

```json
{
  "servers": {
    "resq-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["resq-mcp"],
      "env": {
        "RESQ_SAFE_MODE": "true"
      }
    }
  }
}
```

For local development (from a cloned repo), replace `"command": "uvx"` and `"args"` with `"command": "uv"` and `"args": ["run", "resq-mcp"]`.

</details>

<details>
<summary>Claude Desktop</summary>

Add to your `claude_desktop_config.json` ([MCP install guide](https://modelcontextprotocol.io/quickstart/user)):

```json
{
  "mcpServers": {
    "resq": {
      "command": "uvx",
      "args": ["resq-mcp"],
      "env": {
        "RESQ_API_KEY": "your-prod-token",
        "RESQ_SAFE_MODE": "true"
      }
    }
  }
}
```

</details>

<details>
<summary>Claude Code</summary>

```bash
claude mcp add resq -- uvx resq-mcp
```

</details>

<details>
<summary>Cursor</summary>

Go to `Cursor Settings` → `MCP` → `Add new MCP Server`. Use `command` type with the command `uvx resq-mcp`.

Or add manually to your MCP config:

```json
{
  "mcpServers": {
    "resq": {
      "command": "uvx",
      "args": ["resq-mcp"]
    }
  }
}
```

</details>

<details>
<summary>Windsurf</summary>

Follow Windsurf MCP [documentation](https://docs.windsurf.com/windsurf/cascade/mcp). Use the standard config above.

</details>

<details>
<summary>Docker</summary>

Run the server as a container in SSE mode:

```json
{
  "mcpServers": {
    "resq": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--init",
        "-e", "RESQ_SAFE_MODE=true",
        "resqsoftware/mcp"
      ]
    }
  }
}
```

Or pull from GitHub Container Registry:

```bash
docker pull ghcr.io/resq-software/pypi:latest
```

To run as a long-lived SSE service:

```bash
docker run -d --rm --init \
  --name resq-mcp \
  -p 8000:8000 \
  -e RESQ_SAFE_MODE=true \
  resqsoftware/mcp
```

Then point your MCP client at the HTTP endpoint:

```json
{
  "mcpServers": {
    "resq": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

You can also build the image yourself:

```bash
docker build -t resq-mcp .
```

</details>

<details>
<summary>Local development</summary>

```bash
git clone https://github.com/resq-software/pypi.git
cd pypi/packages/resq-mcp
uv sync
uv run resq-mcp
```

</details>

---

## Configuration

Control server behavior via environment variables or a `.env` file:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `RESQ_API_KEY` | Active bearer token (required, non-default, for network transports) | `resq-dev-token` |
| `RESQ_API_KEY_PREVIOUS` | Prior token honored during a rotation grace window | `` (disabled) |
| `RESQ_API_KEY_GRACE_SECONDS` | Seconds a rotated-out token stays valid | `3600` |
| `RESQ_SAFE_MODE` | Prevents destructive mutations | `true` |
| `RESQ_TRANSPORT` | Transport: `stdio`, `http`, `sse`, `streamable-http` | `stdio` |
| `RESQ_PORT` | Port for network (HTTP/SSE) mode | `8000` |
| `RESQ_HOST` | Host to bind the network server | `0.0.0.0` |
| `RESQ_AUDIT_ENABLED` | Emit hash-anchored audit records (`resq-mcp.audit`) | `true` |
| `RESQ_RATE_LIMIT_ENABLED` | Enforce per-tool call-rate limits | `true` |
| `RESQ_RATE_LIMIT_MAX_CALLS` | Max calls per tool per window | `60` |
| `RESQ_RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window width (seconds) | `60` |
| `RESQ_DEBUG` | Enable verbose logging | `false` |
| `RESQ_TELEMETRY_BACKEND` | Observability backend (`none`, `console`, `jaeger`, `otlp`) | `none` |
| `RESQ_OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP exporter endpoint (when backend is `otlp`) | `http://localhost:4317` |
| `RESQ_OTEL_SERVICE_NAME` | Service name reported to the telemetry backend | `resq-mcp` |

> **Note**: `RESQ_API_KEY` defaults to `resq-dev-token` for local `stdio` use — it works out of the box. **Network transports (`http`/`sse`/`streamable-http`) refuse to start** with the default token; set a real one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

---

## Security & Safety

resq-mcp is hardened against the concerns in NSA Cybersecurity Information sheet
*Model Context Protocol (MCP): Security Design Considerations* (PP-26-1834, May 2026).
See [SECURITY.md](./SECURITY.md) for the full control-by-control mapping.

- **Safe Mode** (`RESQ_SAFE_MODE=true`, default) — side-effecting tools
  (`run_simulation`, `update_mission_params`) raise a `FastMCPError` so agents can
  plan missions without real-world consequences. Disable only for autonomous execution.
- **Authenticated network transports** — bearer-token auth with constant-time
  comparison and zero-downtime rotation (`RESQ_API_KEY_PREVIOUS`); a default token on
  a network listener is refused at startup.
- **Bounded, validated inputs** — every identifier is checked against an allow-list
  (rejecting shell/path metacharacters) and all string/parameter fields are length-capped.
- **Hash-anchored audit logging** — each tool invocation emits a structured JSON record
  on the `resq-mcp.audit` logger with SHA-256 digests of parameters and results; route it
  to your SIEM.
- **Per-tool rate limiting** — a sliding-window limiter resists prompt storms and
  recursive-call fatigue.

---

## Tools

### Mission Control (HCE)

- **validate_incident** — Submit a confirmation or rejection for an incident report. Supports idempotent re-submission and conflict detection for opposing validations.
  - Parameters: `incident_id`, `is_confirmed`, `validation_source`, `correlated_pre_alert_id` (optional), `notes`

- **update_mission_params** — Push authorized mission parameters to a specific drone for an approved strategy. Includes urgency escalation, conflict guards, and idempotent re-dispatch.
  - Parameters: `drone_id`, `strategy_id`, `is_urgent` (optional, default `false`)

### Simulation (DTSOP)

- **run_simulation** — Queue a high-fidelity Digital Twin physics simulation (flood, wildfire, earthquake). Returns a job ID — subscribe to the resource URI for progress updates.
  - Parameters: `scenario_id`, `sector_id`, `disaster_type`, `parameters`, `priority`

- **get_deployment_strategy** — Generate an RL-optimized drone deployment and evacuation strategy for a confirmed incident or PDIE pre-alert.
  - Parameters: `incident_id`

### Resources

| URI | Description |
| :--- | :--- |
| `resq://drones/active` | Real-time fleet status — drone types, battery levels, sector assignments. |
| `resq://simulations/{sim_id}` | Simulation progress and results. Supports SSE subscriptions for push updates on state transitions. |

### Prompts

| Prompt | Description |
| :--- | :--- |
| `incident_response_plan` | Structured crisis coordination template that guides an AI agent through situation analysis, asset allocation, and risk assessment for a given incident. |

---

## Example Workflows

### Run a Flood Simulation

```
You:   "Run a flood simulation for Sector-3 with water level 4.2m"
Agent: Calls run_simulation → receives SIM-ABCD1234
       Subscribes to resq://simulations/SIM-ABCD1234
       Waits for status: completed
       Returns result URL and analysis
```

### Full Incident Response

```
You:   "Validate incident INC-789 and deploy drones"
Agent: 1. Calls validate_incident(INC-789, confirmed=True)
       2. Calls get_deployment_strategy("INC-789")
       3. Reviews strategy with operator
       4. Calls update_mission_params("DRONE-Alpha", "STRAT-XYZ", urgent=True)
       5. Returns mission parameters and audit hash
```

### Crisis Planning with Prompts

```
You:   Use the incident_response_plan prompt for INC-456
Agent: Receives structured template → calls tools → produces:
       - Situation Summary
       - Asset Allocation
       - Risk Assessment
```

---

## Architecture

```mermaid
graph TB
    AI["AI Client<br/><i>Claude / VS Code / Cursor</i>"]

    subgraph "resq-mcp Server"
        SERVER["server.py<br/>FastMCP + Lifespan"]
        RES["resources.py<br/>Drone fleet, sim status"]
        PROMPTS["prompts.py<br/>Crisis response templates"]

        subgraph "Domain Engines"
            HCE["HCE<br/>Hybrid Coordination<br/><i>Incidents & Missions</i>"]
            DTSOP["DTSOP<br/>Digital Twin<br/><i>Physics Simulations</i>"]
            PDIE["PDIE<br/>Predictive Intel<br/><i>Vulnerability & Alerts</i>"]
            DRONE["Drone Fleet<br/><i>Telemetry & Swarm</i>"]
        end

        subgraph "Core"
            CFG[Config]
            SEC[Security]
            TEL[Telemetry]
        end
    end

    AI -->|"MCP (stdio / SSE)"| SERVER
    SERVER --> HCE
    SERVER --> DTSOP
    SERVER --> PDIE
    SERVER --> DRONE
    SERVER --> RES
    SERVER --> PROMPTS
    HCE --> CFG
    DTSOP --> CFG
    SERVER --> SEC
    SERVER --> TEL
```

### Request Flow

```mermaid
sequenceDiagram
    participant AI as AI Agent
    participant MCP as resq-mcp
    participant HCE as HCE Engine
    participant DTSOP as DTSOP Engine

    AI->>MCP: validate_incident(INC-789)
    MCP->>HCE: Process validation
    HCE-->>MCP: IncidentValidation
    MCP-->>AI: Confirmed + audit log

    AI->>MCP: run_simulation(flood, Sector-3)
    MCP->>DTSOP: Queue simulation
    DTSOP-->>MCP: SIM-ABCD (pending)
    MCP-->>AI: Job ID

    loop SSE subscription
        AI->>MCP: resq://simulations/SIM-ABCD
        MCP-->>AI: status: running / completed
    end

    AI->>MCP: get_deployment_strategy(INC-789)
    MCP->>DTSOP: RL optimization
    DTSOP-->>MCP: OptimizationStrategy
    MCP-->>AI: Deployment plan
```

### Module Layout

```
src/resq_mcp/
├── server.py              # FastMCP init, lifespan, background tasks
├── resources.py           # @mcp.resource() endpoints (drones, sims)
├── prompts.py             # @mcp.prompt() templates (incident response)
├── core/                  # Cross-cutting: config, errors, security, telemetry, timeout
├── drone/                 # Drone feed: scan, swarm, deployment (models + service)
├── dtsop/                 # Digital Twin: simulation, optimization (models + service + tools)
├── hce/                   # Hybrid Coordination: incidents, missions (models + service + tools)
└── pdie/                  # Predictive Intelligence: vulnerability, alerts (models + service)
```

---

## Contributing

We use `uv` for dependency management and `ruff` for linting.

1.  **Setup**: `uv sync` (installs all dependencies including dev group).
2.  **Test**: `uv run pytest`
3.  **Lint**: `uv run ruff check .`

Distributed under the Apache-2.0 License. Copyright 2026 ResQ.
