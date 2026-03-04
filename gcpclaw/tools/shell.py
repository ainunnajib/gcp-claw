"""Shell command execution tool with safety controls."""

import subprocess


# Commands that are always blocked
BLOCKED_COMMANDS = {
    "rm -rf /", "rm -rf ~", "mkfs", "dd if=", ":(){ :|:& };:",
    "chmod -R 777 /", "shutdown", "reboot", "halt", "poweroff",
}


def run_command(command: str, timeout: int = 30) -> dict:
    """Execute a shell command and return its output.

    The command runs with a timeout and output size limit.
    Dangerous commands (rm -rf /, shutdown, etc.) are blocked.

    Args:
        command: The shell command to execute.
        timeout: Maximum execution time in seconds (default 30, max 120).

    Returns:
        dict with 'stdout', 'stderr', and 'returncode', or 'error'.
    """
    # Safety checks
    cmd_lower = command.lower().strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return {"error": f"Blocked dangerous command: {command}"}

    timeout = min(timeout, 120)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,
        )
        # Truncate very long outputs
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
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}
