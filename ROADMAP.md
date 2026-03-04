# GCPClaw Enterprise Roadmap (Right-Sized)

Date: 2026-03-05

## Scope

GCPClaw is currently a local-first assistant (`adk run` / `adk web`) and not yet a hosted SaaS platform.

This roadmap is split into:
1. Active scope (now): controls that materially improve enterprise-grade engineering quality for the current local-first architecture.
2. Future scope (service deployment): controls that become mandatory when GCPClaw is deployed as a multi-user service.

---

## Enterprise Objectives (Current Phase)

1. Eliminate known high-risk local attack paths.
2. Enforce reproducible, auditable, secure delivery.
3. Raise code quality bar with strict validation, tests, and typing.
4. Keep roadmap executable by a solo maintainer + Codex agents.

---

## Active Workstreams (Now)

## W1: Runtime and AppSec Hardening (Active)

### W1-P0 (Blockers)
1. Shell allowlist hardening and path-restricted read commands.
2. Symlink-safe file sandbox.
3. DNS rebinding-safe fetch transport.
4. Extension runner execution-time revalidation.

Dependency rule:
- W1-P0 tasks are independent and can run in parallel.

### W1-P1
1. Extension container isolation (rootless, no network, resource caps).
2. Threat model and abuse-case tests in CI.

Exit criteria:
- All W1-P0 acceptance tests pass.
- No known policy-bypass regressions in security test suite.

## W3: Auditability and Governance (Active subset)

### W3-P0
1. Structured, attributable audit events for tool invocation and policy decisions.
2. Repo governance hardening (`CODEOWNERS`, branch protections, required checks).

Exit criteria:
- Every dangerous action has actor, action, timestamp, result.
- Main branch protected by mandatory checks/review.

## W5: Supply Chain and Release Security (Active)

### W5-P0
1. Lockfile-based reproducible dependency flow.
2. CI security gates remain mandatory (`ruff`, `mypy`, `pytest`, `bandit`, `pip-audit`).
3. SBOM generation for builds.

### W5-P1
1. Artifact signing.
2. Provenance attestations.

Exit criteria:
- Reproducible dependency installs in CI.
- SBOM artifact emitted per release.

## W8: Developer Guardrails (Active)

### W8-P0
1. Startup config validation.
2. Exception narrowing.
3. Strict mypy rollout.
4. Test coverage expansion for critical modules.

### W8-P1
1. Pre-commit enforcement.
2. Packaging metadata modernization.

Exit criteria:
- Mandatory quality/security checks pass for every PR.

---

## Future Scope (When Deploying as Service)

These are intentionally deferred until service deployment architecture exists.

1. W2: OIDC, RBAC, multi-tenant isolation.
2. W4: SLO dashboards, on-call alerting, DR operations.
3. W6: Secret manager integration at infrastructure layer, retention/deletion workflows.
4. W7: SOC 2 control catalog and evidence automation.

Trigger to activate future scope:
- Public or internal multi-user hosted deployment plan is approved.

---

## Milestones (Active Scope)

1. Milestone A (2026-03-05 to 2026-03-19)
- W1-P0 + W8-P0 security-critical items + W5-P0 CI enforcement.

2. Milestone B (2026-03-20 to 2026-04-03)
- W3-P0 + remaining W8-P0 + W5-P0 lockfile/SBOM.

3. Milestone C (2026-04-06 to 2026-04-25)
- W1-P1 + W8-P1 + W5-P1.

---

## Immediate PR Queue

1. `fix/shell-allowlist-path-guard`
- Scope: W1 shell hardening
- Verify: `ruff check gcpclaw tests && mypy gcpclaw && pytest && bandit -q -r gcpclaw -c bandit.yaml && pip-audit -r requirements.txt --no-deps --disable-pip`

2. `fix/files-symlink-escape`
- Scope: W1 file sandbox symlink protections
- Verify: same command set

3. `fix/web-dns-rebinding`
- Scope: W1 DNS pinning / rebinding defense
- Verify: same command set

4. `fix/extension-runner-revalidate`
- Scope: W1 runtime revalidation + tests
- Verify: same command set

5. `feat/startup-config-validation`
- Scope: W8 config checks
- Verify: same command set

6. `chore/lockfile-and-sbom`
- Scope: W5 reproducibility + SBOM output in CI
- Verify: same command set + CI artifact assertion

---

## KPI Baselines and Targets

Current baselines (to confirm in Week 1 report):
1. CI pass rate baseline: `TBD` (measure from last 30 runs by 2026-03-12).
2. Security-critical test coverage baseline: `TBD` (measure by 2026-03-12).
3. Mean PR cycle time baseline: `TBD` (measure by 2026-03-12).

Targets (active scope):
1. CI pass rate >= 95%.
2. Security-critical module coverage >= 90%.
3. Critical vulnerability remediation SLA <= 24h; High <= 7d.

---

## Definition of Done (Current Phase)

GCPClaw reaches current enterprise baseline when:
1. All active W1-P0, W3-P0, W5-P0, W8-P0 tasks are complete with tests.
2. Required CI/security gates are enforced and green.
3. Reproducible dependency process and SBOM generation are in CI.
4. Future scope is explicitly deferred and not mixed into active milestone commitments.

---

## Implementation Detail Reference

Concrete code-level implementation specs are in:
- `TASKS.md`

Use `ROADMAP.md` for strategy and sequencing, and `TASKS.md` for execution details.
