# CHANGELOG


## v1.0.0 (2026-03-18)

### Features

- 🚀 implement telemetry and harden tool security guards
  ([`48edde3`](https://github.com/resq-software/mcp/commit/48edde32aaae939d28f7d57299933178840ab3ac))

- Integrate OpenTelemetry SDK with OTLP and console backend support - Add TTL-based eviction for
  incidents, missions, and simulations - Implement capacity, conflict, and idempotency guards for
  tools - Harden prompts against injection using incident ID validation - Switch to explicit urgency
  flags for mission risk tolerance

BREAKING CHANGE: get_deployment_strategy now requires incidents to be validated via
  validate_incident before a strategy can be requested.

### Breaking Changes

- Get_deployment_strategy now requires incidents to be validated via validate_incident before a
  strategy can be requested.


## v0.4.0 (2026-03-18)

### Continuous Integration

- Drop Python 3.14-dev from test matrix (not yet supported by uv)
  ([`b41ff8c`](https://github.com/resq-software/mcp/commit/b41ff8c0da34b878d7bc66ada96325544cb16654))

### Features

- **core**: 📡 implement telemetry subsystem and enhance server safety
  ([`46e558b`](https://github.com/resq-software/mcp/commit/46e558b71f0289c27e0696d5500a1a68f35ea2b5))

Implement a comprehensive OpenTelemetry-based telemetry subsystem and strengthen server-side
  operational guards.

- Implement OpenTelemetry subsystem with PII scrubbing and async decorators - Add mission parameter
  tools and idempotency guards for incident validation - Refactor simulation processor for
  concurrent execution and orphan recovery - Introduce capacity limits and TTL-based eviction for
  simulation state - Improve security using timing-attack resistant credential comparison - Overhaul
  documentation including README, AGENTS.md, and CLAUDE.md - Add environment variable validation on
  server startup


## v0.3.4 (2026-03-17)

### Bug Fixes

- **ci**: Use GitHub API directly for release asset uploads (avoids immutable release error)
  ([`92fc25f`](https://github.com/resq-software/mcp/commit/92fc25fb01fb557d0fbfceb03f3063bb4c199d62))


## v0.3.3 (2026-03-17)

### Bug Fixes

- **ci**: Use softprops/action-gh-release for asset uploads
  ([`ba8a0cd`](https://github.com/resq-software/mcp/commit/ba8a0cd0e135d8b2be5933706b95ab29e7b4d4b4))


## v0.3.2 (2026-03-17)

### Bug Fixes

- **ci**: Use --clobber for release asset uploads to handle re-runs
  ([`9390cf2`](https://github.com/resq-software/mcp/commit/9390cf2fe0098301c612d09472b5b4faa353c0a4))


## v0.3.1 (2026-03-17)

### Bug Fixes

- **ci**: Use PYPI_TOKEN for publishing, pin sigstore action version
  ([`39d50cd`](https://github.com/resq-software/mcp/commit/39d50cdd05444c5c0dbbfd6d23476d4b61a39a5a))

- Fall back to PYPI_TOKEN secret until Trusted Publisher is configured on pypi.org for the
  resq-software org - Pin sigstore/gh-action-sigstore-python to v3.2.0 (v3 major tag doesn't exist)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>


## v0.3.0 (2026-03-17)

### Chores

- **deps**: Bump astral-sh/setup-uv from 5 to 7 ([#4](https://github.com/resq-software/mcp/pull/4),
  [`f0a2b99`](https://github.com/resq-software/mcp/commit/f0a2b99025d58d1bb9c5b0f9cf73121cc6b4f492))

Bumps [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv) from 5 to 7. - [Release
  notes](https://github.com/astral-sh/setup-uv/releases) -
  [Commits](https://github.com/astral-sh/setup-uv/compare/v5...v7)

--- updated-dependencies: - dependency-name: astral-sh/setup-uv dependency-version: '7'

dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump codecov/codecov-action from 4 to 5
  ([#6](https://github.com/resq-software/mcp/pull/6),
  [`68dc997`](https://github.com/resq-software/mcp/commit/68dc997a7dbcecbe47e720704bbd52ed9510de16))

Bumps [codecov/codecov-action](https://github.com/codecov/codecov-action) from 4 to 5. - [Release
  notes](https://github.com/codecov/codecov-action/releases) -
  [Changelog](https://github.com/codecov/codecov-action/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/codecov/codecov-action/compare/v4...v5)

--- updated-dependencies: - dependency-name: codecov/codecov-action dependency-version: '5'

dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump docker/login-action from 3 to 4 ([#5](https://github.com/resq-software/mcp/pull/5),
  [`8fc2f3a`](https://github.com/resq-software/mcp/commit/8fc2f3ade2778ac00533cbb88744434ae173c1d5))

Bumps [docker/login-action](https://github.com/docker/login-action) from 3 to 4. - [Release
  notes](https://github.com/docker/login-action/releases) -
  [Commits](https://github.com/docker/login-action/compare/v3...v4)

--- updated-dependencies: - dependency-name: docker/login-action dependency-version: '4'

dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Documentation

- Update README with AI-generated content
  ([`03842df`](https://github.com/resq-software/mcp/commit/03842df248556abcab6ecb85d7602143f5729920))

- Update README with AI-generated content
  ([`81ace88`](https://github.com/resq-software/mcp/commit/81ace886419536b925e7b8d4adabceb669ea2dab))

- Update README with AI-generated content
  ([`1af74e4`](https://github.com/resq-software/mcp/commit/1af74e4af68848d6c277d2c3ca219aafa3c24814))

### Features

- Enterprise-grade publishing, CI hardening, test quality & domain restructure
  ([`9de8b21`](https://github.com/resq-software/mcp/commit/9de8b214974bb68693907f88af1e99d8709e2400))

## What changed

### CI/CD & Publishing - OIDC Trusted Publisher for PyPI (no API tokens) - Sigstore artifact signing
  + build attestation with verification - CycloneDX SBOM generation attached to GitHub Releases - CI
  matrix: Python 3.11, 3.12, 3.13, 3.14-dev - Separate lint, typecheck, security gates → test →
  build-verify pipeline - TestPyPI publish on PRs after full pipeline passes - py.typed marker (PEP
  561)

### Test Quality - 94 → 156 tests, 85% → 92% coverage with enforced gate - Hypothesis property-based
  testing for Pydantic models - Integration tests: 3 cross-module workflows - Probabilistic
  distribution tests for drone tools - Edge case tests across all domain modules - Factory fixtures
  in conftest.py

### Domain Restructure - Flat 13-file package → 5 domain packages (core, drone, dtsop, hce, pdie) -
  server.py split into server + resources + prompts - models.py split into domain-specific model
  files - Tests reorganized into unit/, integration/, property/

### Enterprise Utilities - MCPErrorFormatter: structured JSON errors with context redaction -
  Centralized timeout config with env-var override and exponential backoff

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>


## v0.2.0 (2026-03-15)

### Bug Fixes

- **ci**: Harden release and docker publish
  ([`138107f`](https://github.com/resq-software/mcp/commit/138107f2411081b8ab417bccbe2a124036cc3fa4))

- **ci**: Use main branch in release workflow and semantic-release config
  ([`76327fc`](https://github.com/resq-software/mcp/commit/76327fc124d4a6928bdb40497aafff83568b1dd5))

- **release**: Install uv in PSR Docker container before building
  ([`412b17b`](https://github.com/resq-software/mcp/commit/412b17bed10388e959c957967c6214a5957c7828))

The python-semantic-release action runs in an isolated Docker container where the uv binary (set up
  by setup-uv on the runner) is not available. Prepend `pip install uv` to the build_command so uv
  is present at build time.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Chores

- Add dev tooling — hooks, skills, agents, codecov, dependabot
  ([`98740d8`](https://github.com/resq-software/mcp/commit/98740d873f7bd20ce17918de432931e79e68d70a))

- Add .git-hooks/ (pre-commit, commit-msg, prepare-commit-msg, post-checkout, post-merge, pre-push)
  with resq-cli delegation, OSV scan, secrets scan, and ruff check/format - Add scripts/setup.sh
  with core.hooksPath wiring and Nix bootstrap - Add bootstrap.sh root alias for scripts/setup.sh -
  Add flake.nix devShell with osv-scanner, Python 3.12, and uv - Add .github/skills/
  (feynman-auditor, nemesis-auditor, state-inconsistency-auditor) - Add .github/agents/,
  .github/commands/, .github/rules/ for FastMCP context - Add .github/dependabot.yml with pip +
  github-actions and minor/patch grouping - Add .github/workflows/auto-merge.yml for Dependabot PRs
  - Update .github/workflows/ci.yml with pytest --cov and Codecov upload - Add CLAUDE.md + AGENTS.md
  agent guide - Add agent-sync.sh to keep AGENTS.md and CLAUDE.md in sync

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **deps**: Bump actions/checkout from 4 to 6 ([#3](https://github.com/resq-software/mcp/pull/3),
  [`13a86b1`](https://github.com/resq-software/mcp/commit/13a86b13e086db79ef7d05cf666e3ebf7e2ca6cf))

Bumps [actions/checkout](https://github.com/actions/checkout) from 4 to 6. - [Release
  notes](https://github.com/actions/checkout/releases) -
  [Changelog](https://github.com/actions/checkout/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/actions/checkout/compare/v4...v6)

--- updated-dependencies: - dependency-name: actions/checkout dependency-version: '6'

dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump docker/build-push-action from 6 to 7
  ([#2](https://github.com/resq-software/mcp/pull/2),
  [`ddd2abf`](https://github.com/resq-software/mcp/commit/ddd2abf47d4fe2176b148eec939a9d6e1ded82f7))

Bumps [docker/build-push-action](https://github.com/docker/build-push-action) from 6 to 7. -
  [Release notes](https://github.com/docker/build-push-action/releases) -
  [Commits](https://github.com/docker/build-push-action/compare/v6...v7)

--- updated-dependencies: - dependency-name: docker/build-push-action dependency-version: '7'

dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump python-semantic-release/publish-action from 9 to 10
  ([#1](https://github.com/resq-software/mcp/pull/1),
  [`9744bdc`](https://github.com/resq-software/mcp/commit/9744bdcc28d70c3eff3fe77aac045d365c7336ec))

Bumps
  [python-semantic-release/publish-action](https://github.com/python-semantic-release/publish-action)
  from 9 to 10. - [Release
  notes](https://github.com/python-semantic-release/publish-action/releases) -
  [Changelog](https://github.com/python-semantic-release/publish-action/blob/main/releaserc.toml) -
  [Commits](https://github.com/python-semantic-release/publish-action/compare/v9...v10)

--- updated-dependencies: - dependency-name: python-semantic-release/publish-action
  dependency-version: '10'

dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Continuous Integration

- Add PR labeler and label-sync workflows
  ([`e9a8f64`](https://github.com/resq-software/mcp/commit/e9a8f64e599debf453ba916ca9d8b7ba79927d80))

- .github/labels.yml — standardized label definitions - .github/labeler.yml — path-based PR labels
  per area - workflows/labeler.yml — actions/labeler@v6 on PR open/sync - workflows/label-sync.yml —
  EndBug/label-sync@v2 on labels.yml change - workflows/pr-size-labeler.yml — XS/S/M/L/XL size
  labels ignoring uv.lock

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Auto-release with python-semantic-release on push to master
  ([`5f64574`](https://github.com/resq-software/mcp/commit/5f64574e726f53d8b694edef7f7cf3701851ba45))

### Features

- **ci**: Inbound sync — create PR in resQ monorepo on push to main
  ([`7feb7c6`](https://github.com/resq-software/mcp/commit/7feb7c6393b4172a22e03c60dc642055914275f0))

Requires SYNC_TOKEN secret with repo write access to resq-software/resQ.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.1.0 (2026-03-12)

### Bug Fixes

- **ci**: Remove invalid job-level if conditions using secrets context
  ([`f873a67`](https://github.com/resq-software/mcp/commit/f873a6788890553cf6311f2d90debcc1e39688ff))

secrets.* is not supported in job-level if: conditions for push-triggered workflows — it causes a
  workflow parse error. Reverted to plain jobs; publish will fail with auth errors until secrets are
  configured.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ci**: Remove monorepo-internal dep, fix Dockerfile README copy
  ([`dd69e1b`](https://github.com/resq-software/mcp/commit/dd69e1b468fedfe6f85d0bbeedd91488f87a0b51))

- **ci**: Replace monorepo resq.exceptions with local ConfigurationError
  ([`424eb76`](https://github.com/resq-software/mcp/commit/424eb76f2a02b3a1620cbd358621f270212f3757))

- **ci**: Skip publish jobs when secrets are not configured
  ([`2a37638`](https://github.com/resq-software/mcp/commit/2a37638b0a17df3229d89b3aa7d8c0caac5aa3dc))

Guard publish-pypi and publish-docker jobs with if conditions so the workflow doesn't fail when
  PYPI_TOKEN / DOCKERHUB credentials haven't been added as repo secrets yet.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tests**: Replace deprecated FastMCP .fn attribute with direct calls
  ([`20dfc4e`](https://github.com/resq-software/mcp/commit/20dfc4e226e33b90b7e172fe3dcf98d93c062732))

FastMCP no longer wraps decorated functions with a .fn attribute — the decorators now return the
  original async function unchanged, so calling .fn raised AttributeError. Updated
  TestGetSimulationStatus and TestValidateIncident to call functions directly.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Continuous Integration

- Test, docker build, and PyPI + Docker Hub publish workflows
  ([`aff9460`](https://github.com/resq-software/mcp/commit/aff9460c6b5dc8b25363ce72248e5b1c8ba05b15))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Initial ResQ MCP server
  ([`ccdb37a`](https://github.com/resq-software/mcp/commit/ccdb37a0387ef8aae3e4465c079341085eed585f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
