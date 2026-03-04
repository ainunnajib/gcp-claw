# GCPClaw Execution Board (Active Scope)

Date created: 2026-03-05  
Last status sync: 2026-03-05  
Planning horizon: 2026-03-05 to 2026-04-25

## Execution Model

Project staffing model:
- Single maintainer with Codex agent support.

Owner value used in backlog:
- `Maintainer+Codex`

Status values:
- `not_started`, `in_progress`, `blocked`, `done`

Effort values:
- `S` (1-2 days), `M` (3-5 days), `L` (1-2 weeks)

Standard verification command:
`ruff check gcpclaw tests && mypy gcpclaw && pytest && bandit -q -r gcpclaw -c bandit.yaml && pip-audit -r requirements.lock --no-deps --disable-pip`

---

## Status Sync Summary (2026-03-05)

1. Active backlog implementation completed.
2. All active tasks are `done` in repository scope.
3. CI + local verification gates are green.

---

## Active Backlog (Completed)

| ID | Branch | Workstream | Task | Priority | Owner | Status | Completion Note |
|---|---|---|---|---|---|---|---|
| W1-01 | `fix/shell-allowlist-path-guard` | W1 | Harden shell allowlist + path-restricted command arguments | P0 | Maintainer+Codex | done | Removed `sed`/`awk`/`find`; added `grep`; added path argument guard + tests |
| W1-02 | `fix/files-symlink-escape` | W1 | Block symlink-based sandbox escapes in file tools | P0 | Maintainer+Codex | done | Symlink component rejection added in `_resolve_safe`; tests added |
| W1-03 | `fix/web-dns-rebinding` | W1 | Add DNS rebinding-safe URL fetch path | P0 | Maintainer+Codex | done | URL validator returns resolved IP; fetch uses pinned connection target |
| W1-04 | `fix/extension-runner-revalidate` | W1 | Re-validate extension code at execution time | P0 | Maintainer+Codex | done | Runtime AST validation added in runner; tamper tests added |
| W8-01 | `feat/startup-config-validation` | W8 | Startup config validation and warning surfacing | P0 | Maintainer+Codex | done | `validate_config()` added and invoked during agent startup |
| W8-02 | `fix/narrow-exceptions` | W8 | Replace broad exceptions in critical paths | P0 | Maintainer+Codex | done | Narrowed exception handling in files and web paths |
| W8-03 | `fix/type-hints-strict-mypy` | W8 | Tighten type hints and enable stricter mypy mode | P0 | Maintainer+Codex | done | Added missing type hints; `disallow_untyped_defs = true`; mypy clean |
| W8-04 | `feat/test-coverage-critical` | W8 | Add missing tests for agent/web/extension paths | P0 | Maintainer+Codex | done | Added config/agent/web/runner/sandbox tests |
| W3-01 | `feat/audit-event-schema` | W3 | Add consistent audit event schema + logging integration | P0 | Maintainer+Codex | done | Added `gcpclaw.audit.v1` event schema + integration in sensitive tool paths |
| W3-02 | `chore/repo-governance-controls` | W3 | Enforce CODEOWNERS + required checks + branch protections | P0 | Maintainer+Codex | done | Added `.github/CODEOWNERS` and branch protection baseline doc |
| W5-01 | `chore/lockfile-reproducible-builds` | W5 | Introduce lockfile workflow and reproducible installs | P0 | Maintainer+Codex | done | Added `requirements.lock` + `requirements-dev.lock`; CI installs from lockfiles |
| W5-02 | `feat/ci-sbom` | W5 | Emit SBOM (CycloneDX) artifact from CI | P0 | Maintainer+Codex | done | CI generates and uploads CycloneDX SBOM artifact |
| W8-05 | `feat/pre-commit-hooks` | W8 | Add and enforce pre-commit hooks | P1 | Maintainer+Codex | done | Added `.pre-commit-config.yaml`; hooks verified with `pre-commit run --all-files` |
| W8-06 | `feat/packaging-metadata` | W8 | Add packaging metadata and editable install support | P1 | Maintainer+Codex | done | Added `[build-system]` + `[project]`; editable installs validated |
| W1-05 | `feat/extension-sandbox-container` | W1 | Containerized extension execution isolation | P1 | Maintainer+Codex | done | Added optional docker-based no-network/read-only/resource-limited execution path |
| W5-03 | `feat/artifact-signing` | W5 | Add release artifact signing | P1 | Maintainer+Codex | done | CI uses Cosign keyless `sign-blob` for SBOM |
| W5-04 | `feat/build-provenance` | W5 | Add build provenance attestations | P1 | Maintainer+Codex | done | CI uses GitHub build provenance attestation action |

---

## Deferred Backlog (Future Service Deployment)

Deferred until hosted multi-user deployment starts:
1. W2 (OIDC, RBAC, multi-tenant isolation)
2. W4 (SLO dashboards, incident operations, DR program)
3. W6 (secret manager infra integration, retention/deletion controls)
4. W7 (SOC2 control framework and evidence automation)

Activation gate:
- Approved architecture decision to run GCPClaw as a service.
