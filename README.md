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

# resQ MCP Server

A Staff+ engineered Model Context Protocol (MCP) server for the resQ emergency response system.
Integrates with Digital Twin Simulations (DTSOP) and Hybrid Coordination Engine (HCE).

## Features
- **Tools**: Trigger simulations, Get deployment strategies, Validate incidents.
- **Resources**: Real-time drone status (`resq://drones/active`), Simulation monitoring (`resq://simulations/{id}`).
- **Prompts**: Standardized incident response analysis.
- **Async Notifications**: Subscriptions for long-running simulation jobs.
- **Security**: Mock Bearer token auth, Pydantic validation.

## Development

### Prerequisites
- Python 3.11+
- `uv` or `pip`

### Setup
```bash
cd packages/python/mcp
pip install -e .
```

### Running Locally (STDIO)
Ideal for testing with Claude Desktop or MCP Inspector.
```bash
# Set env var if needed, or rely on defaults
python -m resq_mcp.server
```

### Running Locally (SSE / HTTP)
```bash
# Starts SSE server on port 8000
python -m resq_mcp.server --transport sse --port 8000
```
*Note: FastMCP CLI args might vary slightly depending on version.*

## Configuration
See `.env.example` or `src/resq_mcp/config.py`.
- `RESQ_API_KEY`: Bearer token for auth (default: `resq-dev-token`).
- `RESQ_SAFE_MODE`: Disable side-effects (default: `True`).

## Deployment
Dockerized for Kubernetes.
```bash
docker build -t resq-mcp .
kubectl apply -f deployment/k8s.yaml
```

## Security
See [SECURITY.md](SECURITY.md) for threat model and details.
