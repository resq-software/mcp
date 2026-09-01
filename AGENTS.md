# ResQ PyPI Packages — Agent Guide

## Mission
Registry workspace for ResQ Python packages published to PyPI.

## Stack
- Runtime: Python 3.11+
- Build: Hatchling
- Package Manager: uv
- Testing: pytest (+ hypothesis for property-based tests in resq-mcp)
- Linting: ruff + mypy (strict)
- Release: python-semantic-release for both published packages. Triggered manually via
  `workflow_dispatch` — the branch ruleset rejects the release commit, so pushes do not publish.

## Repo Map
- `packages/resq-mcp/` — FastMCP server for AI agent integration (drone fleet, PDIE, DTSOP)
- `packages/resq-dsa/` — Zero-dependency data structures & algorithms (Bloom, CountMin, Graph, Heap, Trie, Rabin-Karp)

## Commands
```bash
# resq-mcp
cd packages/resq-mcp && uv sync && uv run pytest
uv run ruff check src/ tests/
uv run mypy src/

# resq-dsa
cd packages/resq-dsa && uv sync && uv run pytest
uv run ruff check src/ tests/
```

## Rules
- `resq-dsa` must have zero runtime dependencies — stdlib only
- Each package has its own `pyproject.toml` and virtual environment
- Python 3.11+ minimum across all packages
- ruff for linting, mypy for type checking (strict mode)
- All source files must include Apache-2.0 license header
- `AGENTS.md` is the source of truth for `CLAUDE.md` — never edit `CLAUDE.md` directly

## Safety
- Don't add runtime dependencies to `resq-dsa`
- Don't publish without running full test suite and linting
- `resq-mcp` safe mode (`RESQ_SAFE_MODE=true`) is default — mutations raise errors

## Workflow
1. `cd` into the specific package directory
2. `uv sync` to install dependencies
3. `uv run pytest` to test
4. `uv run ruff check src/ tests/` to lint
5. Summarize: files changed, behavior change, tests run

## References
- [resq-mcp README](packages/resq-mcp/README.md) — Full MCP server documentation
- [resq-dsa README](packages/resq-dsa/README.md) — DSA library documentation
- [README](README.md) — Package overview

## Git hooks

Canonical hooks from [`resq-software/dev`](https://github.com/resq-software/dev).
Install:

```sh
curl -fsSL https://raw.githubusercontent.com/resq-software/dev/main/scripts/install-hooks.sh | sh
```

Contract: [dev/AGENTS.md#git-hooks](https://github.com/resq-software/dev/blob/main/AGENTS.md#git-hooks). This repo's `.git-hooks/local-pre-push` runs `ruff check` (lint only — formatting is already handled by `resq pre-commit`).
