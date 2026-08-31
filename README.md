# ResQ PyPI Packages

[![CI](https://img.shields.io/github/actions/workflow/status/resq-software/pypi/ci.yml?branch=main&label=CI&style=flat-square)](https://github.com/resq-software/pypi/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square)](LICENSE)

Python packages for the [ResQ](https://github.com/resq-software) disaster response platform, published to PyPI under the [`resq-software`](https://pypi.org/org/resq-software/) organization.

## Packages

| Package | Description | Version |
|---------|-------------|---------|
| [`resq-mcp`](packages/resq-mcp/) | FastMCP server -- connects AI agents to drone fleet, simulations, and disaster intelligence | [![PyPI](https://img.shields.io/pypi/v/resq-mcp?style=flat-square)](https://pypi.org/project/resq-mcp/) |
| [`resq-dsa`](packages/resq-dsa/) | Zero-dependency data structures & algorithms for search, rescue, and geospatial ops | [![PyPI](https://img.shields.io/pypi/v/resq-dsa?style=flat-square)](https://pypi.org/project/resq-dsa/) |

## Architecture

```mermaid
graph TB
    subgraph "resq-software/pypi"
        subgraph "packages/resq-mcp"
            MCP[resq-mcp<br/><i>FastMCP Server</i>]
            DTSOP[DTSOP<br/>Digital Twin Simulations]
            HCE[HCE<br/>Hybrid Coordination]
            PDIE[PDIE<br/>Predictive Intelligence]
            DRONE[Drone Fleet<br/>Telemetry & Control]
            MCP --> DTSOP
            MCP --> HCE
            MCP --> PDIE
            MCP --> DRONE
        end
        subgraph "packages/resq-dsa"
            DSA[resq-dsa<br/><i>Zero-Dep DSA</i>]
            BF[BloomFilter]
            CMS[CountMinSketch]
            GR[Graph + A*]
            HP[BoundedHeap]
            TR[Trie]
            DSA --> BF
            DSA --> CMS
            DSA --> GR
            DSA --> HP
            DSA --> TR
        end
    end

    AI[AI Clients<br/>Claude / VS Code / Cursor] -->|MCP protocol| MCP
    APP[Python Applications] -->|pip install| DSA
```

## Quick Start

```bash
# Install a package
pip install resq-mcp   # MCP server for AI agents
pip install resq-dsa   # Data structures (zero dependencies)
```

## Development

```bash
# Clone and setup
git clone https://github.com/resq-software/pypi.git && cd pypi
./bootstrap.sh

# Work on a package
cd packages/resq-mcp && uv sync && uv run pytest
cd packages/resq-dsa && uv sync && uv run pytest
```

### Release Flow

```mermaid
graph LR
    DISPATCH[Manual dispatch<br/><i>Actions tab</i>] --> SR[Semantic Release]
    SR -->|feat: / fix:| BUMP[Version Bump + Changelog]
    BUMP --> BUILD[Build sdist + wheel]
    BUILD --> ATTEST[Sigstore Attestation]
    ATTEST --> PYPI[Publish to PyPI]
    PYPI --> DOCKER[Docker Image<br/><i>resq-mcp only</i>]
```

The two published packages use [python-semantic-release](https://python-semantic-release.readthedocs.io/) with [Trusted Publisher](https://docs.pypi.org/trusted-publishers/) OIDC. Conventional commits determine the version bump, but **releases are triggered manually** from the Actions tab — the branch ruleset rejects the bot's version commit, so the workflow is `workflow_dispatch` only.

## License

[Apache-2.0](LICENSE) -- Copyright 2025 ResQ Software
