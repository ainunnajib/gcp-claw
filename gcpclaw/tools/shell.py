"""Shell command execution tool with strict safety controls."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path

from ..config import dangerous_tools_enabled, get_workspace_dir

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
    "sed",
    "awk",
    "find",
    "rg",
    "pytest",
    "git",
}


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


def run_command(command: str, timeout: int = 30) -> dict:
    """Execute an allowlisted shell command and return output.

    This tool is disabled by default. Set ENABLE_DANGEROUS_TOOLS=true to use it.
    """
    if not dangerous_tools_enabled():
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
        return {"error": policy_error}

    try:
        result = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=get_workspace_dir(),
            env=_safe_env(),
        )  # nosec B603
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except Exception as exc:
        LOGGER.exception("shell_command_failed")
        return {"error": str(exc)}

    max_output = 50_000
    stdout = result.stdout[:max_output]
    stderr = result.stderr[:max_output]
    if len(result.stdout) > max_output:
        stdout += f"\n... (truncated, total {len(result.stdout)} chars)"
    if len(result.stderr) > max_output:
        stderr += f"\n... (truncated, total {len(result.stderr)} chars)"

    return {
        "stdout": stdout,
        "stderr": stderr,
        "returncode": result.returncode,
    }
