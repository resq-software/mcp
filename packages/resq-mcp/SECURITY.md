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

# Security Policy & Threat Model

## Threat Model

### Components
- **MCP Client**: Untrusted agent/LLM.
- **MCP Server**: This service.
- **Backend (Mocked)**: Internal trusted networks.

### Threats & Mitigations
1.  **Prompt Injection**:
    - **Risk**: malicious input manipulating backend commands.
    - **Mitigation**: Strict Pydantic schemas. Inputs are typed, length-bounded, and
      identifier fields are constrained to an allow-list. No raw shell execution.

2.  **Unauthorized Access**:
    - **Risk**: Random internet traffic accessing a network (HTTP/SSE) endpoint.
    - **Mitigation**: Bearer-token auth via `RESQ_API_KEY`, with constant-time
      comparison and rotation support. Network transports refuse to start with the
      default development token. In prod, terminate OIDC at the gateway.

3.  **Confused Deputy**:
    - **Risk**: LLM tricked into performing actions the user didn't intend.
    - **Mitigation**: "Safe Mode" is the default and blocks side-effecting tools
      (`run_simulation`, `update_mission_params`) until explicitly disabled. Urgency
      is never inferred from identifier strings.

4.  **SSRF (Server Side Request Forgery)**:
    - **Risk**: Server calling arbitrary URLs.
    - **Mitigation**: Outbound URLs generated are strictly internal schemas
      (`neofs://`). No user-supplied URLs are fetched.

5.  **Denial of Service / Fatigue**:
    - **Risk**: Prompt storms or recursive task requests exhausting resources.
    - **Mitigation**: Per-tool sliding-window rate limiting plus bounded in-memory
      stores with TTL eviction.

## Mapping to NSA PP-26-1834

This package is hardened against the concerns in NSA Cybersecurity Information sheet
*Model Context Protocol (MCP): Security Design Considerations* (PP-26-1834, May 2026).
The table maps each guidance area to the concrete control in this codebase.

| NSA concern / recommendation | Control in resq-mcp | Where |
| --- | --- | --- |
| **Access control** — sessions unbound to identity; no auth on many servers | Bearer-token auth; network transports require a non-default token to start | `core/security.py`, `core/config.py` (`validate_environment`, `NETWORK_TRANSPORTS`) |
| **Token / session security** — no lifecycle (rotation/revocation) in spec | `KeyRing` rotation with a grace window for prior tokens; constant-time compare | `core/security.py` (`KeyRing`, `key_ring`) |
| **Validate parameters** — schemas, ranges, size bounds, no blind forwarding | Length-bounded fields, identifier allow-list, parameter-map size caps | `core/validation.py`, `dtsop/models.py`, `hce/models.py` |
| **Constrain & sandbox tool execution** — treat tool calls as high-risk | Safe Mode gate blocks mutating tools by default; capacity caps | `core/security.py` (`require_mutation_allowed`), `core/guards.py`, `server.py` |
| **Poor approval workflows / confused deputy** | Mutations require explicit `RESQ_SAFE_MODE=false`; urgency never inferred | `hce/tools.py`, `dtsop/tools.py` |
| **Instrument for logging and detection** — log params, identities, result hashes | Structured JSON audit log on `resq-mcp.audit` with SHA-256 param/result hashes | `core/audit.py` (`audit_log`, `hash_payload`) |
| **DoS / fatigue-based techniques** | Per-tool sliding-window rate limiter | `core/ratelimit.py`, `core/guards.py` |
| **Insecure serialization / injection (CWE-77/78/94/95)** | No `eval`/shell; identifier allow-list rejects shell/path metacharacters | `core/validation.py` |
| **Filter & monitor output / chained execution** | Outbound URLs are internal-schema only; results bound to typed models | `dtsop/service.py`, `hce/service.py` |
| **Track & patch MCP vulnerabilities** | Pinned, audited dependencies; semantic-release + CHANGELOG | `pyproject.toml`, `CHANGELOG.md` |

### Residual gaps / operator responsibilities

- **Transport encryption (TLS)** and **OIDC** are expected to be terminated at an
  ingress/gateway in front of the server; the protocol cannot enforce them.
- **Audit sink**: route the `resq-mcp.audit` logger to your SIEM; this package emits
  records but does not ship them.
- **Distributed rate limiting**: the limiter is process-local. Back it with a shared
  store (e.g. Redis) for multi-replica deployments.

## Reporting
Report vulnerabilities to `security@resq.internal`.
