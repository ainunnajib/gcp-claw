"""Shell command execution tool with strict safety controls."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path

from ..config import dangerous_tools_enabled, get_workspace_dir
from ..logging_utils import emit_audit_event

LOGGER = logging.getLogger(__name__)

READ_ONLY_GIT_SUBCOMMANDS = {
    "status",
    "log",
    "show",
    "diff",
    "branch",
    "rev-parse",
}

ALLOWED_BASE_COMMANDS = {
    "pwd",
    "ls",
    "cat",
    "echo",
    "head",
    "tail",
    "wc",
    "sort",
    "uniq",
    "cut",
    "grep",
    "rg",
    "pytest",
    "git",
}

PATH_RESTRICTED_COMMANDS = {"rg", "cat", "head", "tail", "grep"}


def _command_policy_error(args: list[str]) -> str | None:
    if not args:
        return "Command is empty"

    base = args[0]
    if base not in ALLOWED_BASE_COMMANDS:
        return f"Command '{base}' is not permitted"

    if base == "git":
        if len(args) < 2:
            return "A git subcommand is required"
        if args[1] not in READ_ONLY_GIT_SUBCOMMANDS:
            return f"git subcommand '{args[1]}' is not permitted"

    return None


def _safe_env() -> dict[str, str]:
    # Do not forward application secrets into child process execution.
    base_env = {
        "PATH": os.getenv("PATH", ""),
        "HOME": str(Path.home()),
        "LANG": os.getenv("LANG", "C.UTF-8"),
    }
    return base_env


def _validate_path_args(args: list[str], workspace: Path) -> str | None:
    if not args:
        return "Command is empty"
    base = args[0]
    if base not in PATH_RESTRICTED_COMMANDS:
        return None

    positional = [arg for arg in args[1:] if not arg.startswith("-")]
    file_args = positional
    if base in {"grep", "rg"} and positional:
        # first positional argument is the search pattern
        file_args = positional[1:]
    for file_arg in file_args:
        resolved = (workspace / file_arg).resolve()
        try:
            resolved.relative_to(workspace)
        except ValueError:
            return f"Path argument escapes workspace: {file_arg}"
    return None


def run_command(command: str, timeout: int = 30) -> dict:
    """Execute an allowlisted shell command and return output.

    This tool is disabled by default. Set ENABLE_DANGEROUS_TOOLS=true to use it.
    """
    if not dangerous_tools_enabled():
        emit_audit_event(
            LOGGER,
            action="run_command",
            actor="system",
            status="blocked",
            details={"reason": "dangerous_tools_disabled"},
        )
        return {
            "error": (
                "run_command is disabled. Set ENABLE_DANGEROUS_TOOLS=true "
                "to enable high-risk tools."
            )
        }

    timeout = min(max(timeout, 1), 120)
    try:
        args = shlex.split(command, posix=True)
    except ValueError as exc:
        return {"error": f"Invalid command: {exc}"}

    policy_error = _command_policy_error(args)
    if policy_error:
        LOGGER.warning("shell_command_blocked", extra={"event": "shell_command_blocked"})
        emit_audit_event(
            LOGGER,
            action="run_command",
            actor="system",
            status="blocked",
            details={"reason": policy_error, "command": command},
        )
        return {"error": policy_error}
    workspace = get_workspace_dir()
    path_error = _validate_path_args(args, workspace)
    if path_error:
        LOGGER.warning(
            "shell_command_path_blocked",
            extra={"event": "shell_command_path_blocked"},
        )
        emit_audit_event(
            LOGGER,
            action="run_command",
            actor="system",
            status="blocked",
            details={"reason": path_error, "command": command},
        )
        return {"error": path_error}

    try:
        result = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workspace,
            env=_safe_env(),
        )  # nosec B603
    except subprocess.TimeoutExpired:
        emit_audit_event(
            LOGGER,
            action="run_command",
            actor="system",
            status="error",
            details={"reason": "timeout", "command": command, "timeout": timeout},
        )
        return {"error": f"Command timed out after {timeout}s"}
    except Exception as exc:
        LOGGER.exception("shell_command_failed")
        emit_audit_event(
            LOGGER,
            action="run_command",
            actor="system",
            status="error",
            details={"reason": str(exc), "command": command},
        )
        return {"error": str(exc)}

    max_output = 50_000
    stdout = result.stdout[:max_output]
    stderr = result.stderr[:max_output]
    if len(result.stdout) > max_output:
        stdout += f"\n... (truncated, total {len(result.stdout)} chars)"
    if len(result.stderr) > max_output:
        stderr += f"\n... (truncated, total {len(result.stderr)} chars)"

    response = {
        "stdout": stdout,
        "stderr": stderr,
        "returncode": result.returncode,
    }
    emit_audit_event(
        LOGGER,
        action="run_command",
        actor="system",
        status="success" if result.returncode == 0 else "error",
        details={"command": command, "returncode": result.returncode},
    )
    return response
