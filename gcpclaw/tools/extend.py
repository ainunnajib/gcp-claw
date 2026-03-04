"""Self-extension tool — allows the agent to create new tools at runtime.

Extensions are sandboxed: blocked from using dangerous imports like subprocess,
socket, ctypes, etc. They persist to disk and auto-load on next startup.
Each extension gets a SKILL.md file for discoverability.
"""

import ast
import importlib.util
import sys
from pathlib import Path

from ..config import get_extensions_dir

# Imports that are blocked in extension code
SANDBOX_BLOCKED_IMPORTS = {
    "subprocess", "socket", "http.client", "http.server",
    "urllib.request", "urllib.parse", "urllib.error",
    "ctypes", "multiprocessing", "threading",
    "shutil", "signal", "pty", "fcntl", "termios",
    "webbrowser", "xmlrpc", "ftplib", "smtplib", "poplib", "imaplib",
}

# Builtins that are blocked in extension code
SANDBOX_BLOCKED_BUILTINS = {"exec", "eval", "compile", "__import__", "open"}


def _validate_extension_code(code: str) -> tuple[bool, str]:
    """Validate extension code against sandbox rules using AST analysis.

    Returns (is_valid, reason).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        # Check import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if alias.name in SANDBOX_BLOCKED_IMPORTS or module in SANDBOX_BLOCKED_IMPORTS:
                    return False, f"Blocked import: {alias.name}"

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                if node.module in SANDBOX_BLOCKED_IMPORTS or module in SANDBOX_BLOCKED_IMPORTS:
                    return False, f"Blocked import: {node.module}"

        # Check for blocked builtins
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in SANDBOX_BLOCKED_BUILTINS:
                return False, f"Blocked builtin: {node.func.id}"

        # Check for os.system, os.popen, etc.
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                if node.attr in ("system", "popen", "exec", "execvp", "fork", "kill"):
                    return False, f"Blocked os.{node.attr}"

    return True, "OK"


def _load_extension_functions(ext_dir: Path) -> list:
    """Dynamically load functions from an extension's tool.py."""
    tool_file = ext_dir / "tool.py"
    if not tool_file.exists():
        return []

    module_name = f"gcpclaw_ext_{ext_dir.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, tool_file)
    if spec is None or spec.loader is None:
        return []

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Extract public callable functions (not starting with _)
    functions = []
    for name in dir(module):
        if not name.startswith("_"):
            obj = getattr(module, name)
            if callable(obj) and hasattr(obj, "__doc__"):
                functions.append(obj)
    return functions


def create_extension(name: str, description: str, code: str) -> dict:
    """Create a new tool extension that expands your capabilities.

    Write Python code that defines functions. Each function becomes a new tool.
    Extensions are sandboxed — no network, no subprocess, no dangerous operations.
    Allowed: math, string ops, json, csv, re, datetime, collections, itertools, etc.

    Args:
        name: Extension name (lowercase letters, numbers, hyphens).
        description: What this extension does.
        code: Python source code defining one or more functions with docstrings.

    Returns:
        dict with creation status, or error details.
    """
    # Validate name
    import re
    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name) or "--" in name:
        return {"error": f"Invalid name '{name}'. Use lowercase letters, numbers, hyphens. No leading/trailing hyphens."}

    # Validate code
    is_valid, reason = _validate_extension_code(code)
    if not is_valid:
        return {"error": f"Code validation failed: {reason}"}

    ext_dir = get_extensions_dir() / name
    ext_dir.mkdir(parents=True, exist_ok=True)

    # Write the tool code
    (ext_dir / "tool.py").write_text(code, encoding="utf-8")

    # Write SKILL.md
    skill_md = f"""---
name: {name}
description: {description}
metadata:
  generated-by: gcpclaw
  type: extension
---

# {name}

{description}

Auto-generated extension by GCPClaw.
"""
    (ext_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # Try loading to verify it works
    try:
        functions = _load_extension_functions(ext_dir)
        func_names = [f.__name__ for f in functions]
    except Exception as e:
        # Clean up on failure
        (ext_dir / "tool.py").unlink(missing_ok=True)
        (ext_dir / "SKILL.md").unlink(missing_ok=True)
        ext_dir.rmdir()
        return {"error": f"Extension failed to load: {e}"}

    return {
        "status": "created",
        "name": name,
        "path": str(ext_dir),
        "functions": func_names,
        "note": "Extension is saved and will auto-load on next startup. Functions are available now.",
    }


def list_extensions() -> dict:
    """List all installed extensions and their tools.

    Returns:
        dict with 'extensions' list containing name, description, and function names.
    """
    ext_dir = get_extensions_dir()
    extensions = []

    for child in sorted(ext_dir.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        tool_py = child / "tool.py"

        info = {"name": child.name, "has_code": tool_py.exists()}

        # Parse description from SKILL.md
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("description:"):
                    info["description"] = line.split(":", 1)[1].strip()
                    break

        # List function names
        if tool_py.exists():
            try:
                tree = ast.parse(tool_py.read_text(encoding="utf-8"))
                info["functions"] = [
                    node.name for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
                ]
            except SyntaxError:
                info["functions"] = []
                info["error"] = "syntax error in tool.py"

        extensions.append(info)

    return {"extensions": extensions, "count": len(extensions)}


def remove_extension(name: str) -> dict:
    """Remove an installed extension by name.

    Args:
        name: The extension name to remove.

    Returns:
        dict with removal status.
    """
    ext_dir = get_extensions_dir() / name
    if not ext_dir.exists():
        return {"error": f"Extension '{name}' not found"}

    import shutil
    shutil.rmtree(ext_dir)

    # Remove from sys.modules if loaded
    module_name = f"gcpclaw_ext_{name.replace('-', '_')}"
    sys.modules.pop(module_name, None)

    return {"status": "removed", "name": name}
