# GCPClaw Active Task Specs (Concrete)

Date: 2026-03-05

This file contains concrete implementation specs for active roadmap tasks.
Use this file for coding execution. Use `ROADMAP.md` for strategy.

## Global Verification Command

```bash
ruff check gcpclaw tests && mypy gcpclaw && pytest && bandit -q -r gcpclaw -c bandit.yaml && pip-audit -r requirements.txt --no-deps --disable-pip
```

---

## Task A1: Harden shell allowlist and file argument paths

Branch: `fix/shell-allowlist-path-guard`  
Files: `gcpclaw/tools/shell.py`, `tests/test_shell_tool.py`

### Requirements
1. Remove code-execution-capable utilities from allowlist (`sed`, `awk`, `find`).
2. Add `grep` to allowlist.
3. Add `PATH_RESTRICTED_COMMANDS = {"rg", "cat", "head", "tail", "grep"}`.
4. Add `_validate_path_args(args: list[str], workspace: Path) -> str | None`:
- For commands in `PATH_RESTRICTED_COMMANDS`, inspect non-flag args.
- Resolve each path relative to `workspace`.
- Reject if resolved path escapes workspace.
5. Call `_validate_path_args` in `run_command` after base policy checks.

### Tests
Add:
```python
def test_shell_blocks_sed(monkeypatch): ...
def test_shell_blocks_awk(monkeypatch): ...
def test_shell_blocks_rg_outside_workspace(monkeypatch, tmp_path): ...
def test_shell_allows_grep_in_workspace(monkeypatch, tmp_path): ...
```

### Acceptance
- Unsafe commands rejected.
- Out-of-workspace file args rejected.
- In-workspace grep works.

---

## Task A2: Block symlink sandbox escapes

Branch: `fix/files-symlink-escape`  
Files: `gcpclaw/tools/files.py`, `tests/test_files_tool.py`

### Requirements
In `_resolve_safe(path: str)`:
1. Walk each path component from workspace root.
2. If any existing component is a symlink, reject path.
3. Keep ancestry check with `relative_to(workspace)`.

### Suggested implementation
```python
def _resolve_safe(path: str) -> Path:
    workspace = get_workspace_dir()
    candidate = workspace / path
    check = workspace
    for part in Path(path).parts:
        check = check / part
        if check.exists() and check.is_symlink():
            raise ValueError(f"Symlinks are not allowed in path: {path}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError:
        raise ValueError(f"Path '{path}' escapes the workspace directory") from None
    return resolved
```

### Tests
Add:
```python
def test_symlink_is_rejected(monkeypatch, tmp_path): ...
```

### Acceptance
- Symlink traversal blocked for read/write/list.
- Existing traversal protections remain intact.

---

## Task A3: DNS rebinding-safe fetch

Branch: `fix/web-dns-rebinding`  
Files: `gcpclaw/tools/web.py`, `tests/test_web_tool.py`

### Requirements
1. Change `_validate_public_http_url` to return `(is_valid, reason, resolved_ip)`.
2. Ensure `fetch_url` uses resolved IP for connection path (no second independent DNS lookup).
3. Preserve TLS hostname verification semantics.
4. Continue blocking private/link-local/loopback targets and redirects.

### Test additions
```python
def test_validate_returns_resolved_ip(monkeypatch): ...
def test_fetch_uses_pinned_resolution(monkeypatch): ...
```

### Acceptance
- Rebinding window is closed by design.
- Existing SSRF tests still pass.

---

## Task A4: Re-validate extension code at execution time

Branch: `fix/extension-runner-revalidate`  
Files: `gcpclaw/tools/extension_runner.py`, `tests/test_extension_runner.py`

### Requirements
1. Parse extension source with AST in runner before `exec`.
2. Enforce import allowlist and blocked-call checks at execution time.
3. Reject dunder attribute access.
4. Keep isolated execution contract unchanged.

### Tests
Add file `tests/test_extension_runner.py` with:
1. valid code executes and returns result.
2. tampered code with blocked import fails with error.

### Acceptance
- Tampered extension file cannot execute.
- Valid extension still executes.

---

## Task A5: Startup config validation

Branch: `feat/startup-config-validation`  
Files: `gcpclaw/config.py`, `gcpclaw/agent.py`, `tests/test_config.py`

### Requirements
1. Add `validate_config() -> list[str]` in config.
2. Check model/provider key consistency.
3. Check workspace writability.
4. In `agent.py`, log warnings at startup.

### Tests
Add:
```python
def test_env_bool_true(monkeypatch): ...
def test_env_bool_false(monkeypatch): ...
def test_env_bool_default(): ...
def test_validate_config_warns_missing_key(monkeypatch, tmp_path): ...
```

### Acceptance
- Missing key/writable issues warn, do not crash startup.

---

## Task A6: Narrow exceptions in critical modules

Branch: `fix/narrow-exceptions`  
Files: `gcpclaw/tools/files.py`, `gcpclaw/tools/web.py`

### Requirements
1. Replace broad `except Exception` where practical with specific exceptions.
2. In `files.py`, use `(ValueError, OSError)`.
3. In search helpers in `web.py`, use `(requests.RequestException, KeyError, ValueError)`.

### Acceptance
- No broad catch in targeted paths.
- Tests unchanged/green.

---

## Task A7: Strict typing hardening

Branch: `fix/type-hints-strict-mypy`  
Files: `gcpclaw/config.py`, `gcpclaw/tools/extend.py`, `pyproject.toml`

### Requirements
1. Add explicit return type for `get_model`.
2. Add callable return type for extension wrapper factory.
3. Enable stricter mypy mode (`disallow_untyped_defs = true`) and fix resulting errors.

### Acceptance
- `mypy gcpclaw` has zero errors.

---

## Task A8: Missing tests for critical paths

Branch: `feat/test-coverage-critical`  
Files: `tests/test_web_tool.py`, `tests/test_extend_tool.py`, `tests/test_agent.py`

### Requirements
1. Add positive fetch-url extraction test.
2. Add no-search-api-configured test.
3. Add agent skill discovery/index formatting tests.

### Acceptance
- `pytest -v` green with added cases.
- No skipped/xfailed tests.

---

## Task A9: Packaging metadata modernization

Branch: `feat/packaging-metadata`  
File: `pyproject.toml`

### Requirements
1. Add `[build-system]` and `[project]` metadata.
2. Preserve existing tool configurations.
3. Ensure editable installs work.

### Acceptance
- `pip install -e .` works.
- `pip install -e ".[dev]"` works.

---

## Task A10: Pre-commit enforcement

Branch: `feat/pre-commit-hooks`  
Files: `.pre-commit-config.yaml`, `requirements-dev.txt`

### Requirements
1. Add hooks for ruff, mypy, bandit.
2. Add `pre-commit` dependency.
3. Document hook usage.

### Acceptance
- `pre-commit run --all-files` passes.

---

## Task A11: Lockfile and reproducible dependency flow

Branch: `chore/lockfile-reproducible-builds`  
Files: `requirements.in`/lock outputs, CI workflow docs

### Requirements
1. Adopt lockfile flow (recommended: `pip-tools`).
2. Ensure deterministic installs in CI.
3. Document update workflow.

### Acceptance
- CI installs from lockfile successfully.
- Dependency update process is documented.

---

## Task A12: SBOM generation in CI

Branch: `feat/ci-sbom`  
Files: `.github/workflows/ci.yml` (+ optional helper config)

### Requirements
1. Generate CycloneDX SBOM artifact on CI runs.
2. Store SBOM as build artifact.
3. Fail job if SBOM generation fails.

### Acceptance
- CI artifacts include SBOM for successful runs.

