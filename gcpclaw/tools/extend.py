"""Self-extension tool with strict validation and isolated execution."""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from ..config import (
    dangerous_tools_enabled,
    extension_execution_enabled,
    get_extensions_dir,
)

LOGGER = logging.getLogger(__name__)

ALLOWED_IMPORTS = {
    "json",
    "csv",
    "re",
    "math",
    "datetime",
    "decimal",
    "statistics",
    "string",
    "itertools",
    "collections",
    "functools",
    "operator",
    "typing",
    "fractions",
    "random",
}

BLOCKED_CALLS = {
    "exec",
    "eval",
    "compile",
    "open",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
}

NAME_RE = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")
RUNNER_PATH = Path(__file__).with_name("extension_runner.py")


def _public_function_names(tree: ast.Module) -> list[str]:
    return [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]


def _validate_extension_code(code: str) -> tuple[bool, str]:
    """Validate extension code against strict static safety rules."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Syntax error: {exc}"

    if any(isinstance(node, ast.ClassDef) for node in tree.body):
        return False, "Class definitions are not allowed"

    functions = _public_function_names(tree)
    if not functions:
        return False, "At least one public top-level function is required"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    return False, f"Import '{alias.name}' is not allowed"

        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                return False, "Relative imports are not allowed"
            root = node.module.split(".")[0]
            if root not in ALLOWED_IMPORTS:
                return False, f"Import '{node.module}' is not allowed"

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
                return False, f"Blocked function call: {node.func.id}"

        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                return False, "Dunder attribute access is not allowed"

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            if ast.get_docstring(node) is None:
                return False, f"Function '{node.name}' must have a docstring"
    return True, "OK"


def _safe_env() -> dict[str, str]:
    return {
        "PATH": os.getenv("PATH", ""),
        "LANG": os.getenv("LANG", "C.UTF-8"),
    }


def _build_function_wrapper(ext_dir: Path, function_name: str):
    def _tool(payload_json: str = "{}") -> dict[str, object]:
        """Execute extension function with JSON arguments in isolated subprocess."""
        try:
            payload = json.loads(payload_json)
            if not isinstance(payload, dict):
                return {"error": "payload_json must decode to a JSON object"}
        except json.JSONDecodeError as exc:
            return {"error": f"Invalid JSON payload: {exc}"}

        command = [
            sys.executable,
            "-I",
            str(RUNNER_PATH),
            "--tool-file",
            str(ext_dir / "tool.py"),
            "--function",
            function_name,
            "--args-json",
            json.dumps(payload),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=ext_dir,
                env=_safe_env(),
                shell=False,
            )  # nosec B603
        except subprocess.TimeoutExpired:
            return {"error": "Extension execution timed out"}
        except Exception as exc:
            LOGGER.exception("extension_execution_failed")
            return {"error": f"Extension execution failed: {exc}"}

        if result.returncode != 0:
            stderr = result.stderr.strip() or "unknown error"
            return {"error": f"Extension subprocess failed: {stderr}"}

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Extension subprocess returned invalid JSON"}
        if not isinstance(output, dict):
            return {"error": "Extension subprocess output must be a JSON object"}
        return output

    _tool.__name__ = function_name
    _tool.__doc__ = (
        f"Execute extension function '{function_name}'. "
        "Pass arguments as JSON in `payload_json`."
    )
    return _tool


def _load_extension_functions(ext_dir: Path) -> list:
    """Load extension function wrappers from an extension's tool.py."""
    if not extension_execution_enabled():
        return []
    tool_file = ext_dir / "tool.py"
    if not tool_file.exists():
        return []
    code = tool_file.read_text(encoding="utf-8")
    is_valid, reason = _validate_extension_code(code)
    if not is_valid:
        raise ValueError(f"Invalid extension code in {ext_dir.name}: {reason}")

    tree = ast.parse(code)
    functions = []
    for name in _public_function_names(tree):
        functions.append(_build_function_wrapper(ext_dir, name))
    return functions


def create_extension(name: str, description: str, code: str) -> dict:
    """Create a new tool extension.

    This tool is disabled by default. Set ENABLE_DANGEROUS_TOOLS=true to use it.
    """
    if not dangerous_tools_enabled():
        return {
            "error": (
                "create_extension is disabled. Set ENABLE_DANGEROUS_TOOLS=true "
                "to enable high-risk tools."
            )
        }

    if not NAME_RE.match(name) or "--" in name:
        return {
            "error": (
                f"Invalid name '{name}'. Use lowercase letters, numbers, hyphens. "
                "No leading/trailing hyphens."
            )
        }

    is_valid, reason = _validate_extension_code(code)
    if not is_valid:
        return {"error": f"Code validation failed: {reason}"}

    ext_dir = get_extensions_dir() / name
    ext_dir.mkdir(parents=True, exist_ok=True)
    (ext_dir / "tool.py").write_text(code, encoding="utf-8")

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

    tree = ast.parse(code)
    func_names = _public_function_names(tree)
    return {
        "status": "created",
        "name": name,
        "path": str(ext_dir),
        "functions": func_names,
        "note": (
            "Extension is saved. Set ENABLE_EXTENSION_EXECUTION=true and restart "
            "to make extension tools callable."
        ),
    }


def list_extensions() -> dict:
    """List all installed extensions and function names."""
    ext_dir = get_extensions_dir()
    extensions = []
    for child in sorted(ext_dir.iterdir()):
        if not child.is_dir():
            continue
        tool_py = child / "tool.py"
        skill_md = child / "SKILL.md"
        info = {
            "name": child.name,
            "has_code": tool_py.exists(),
            "execution_enabled": extension_execution_enabled(),
        }
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("description:"):
                    info["description"] = line.split(":", 1)[1].strip()
                    break
        if tool_py.exists():
            try:
                tree = ast.parse(tool_py.read_text(encoding="utf-8"))
                info["functions"] = _public_function_names(tree)
            except SyntaxError:
                info["functions"] = []
                info["error"] = "syntax error in tool.py"
        extensions.append(info)
    return {"extensions": extensions, "count": len(extensions)}


def remove_extension(name: str) -> dict:
    """Remove an installed extension by name."""
    if not dangerous_tools_enabled():
        return {
            "error": (
                "remove_extension is disabled. Set ENABLE_DANGEROUS_TOOLS=true "
                "to enable high-risk tools."
            )
        }
    if not NAME_RE.match(name) or "--" in name:
        return {"error": "Invalid extension name"}
    ext_dir = get_extensions_dir() / name
    if not ext_dir.exists():
        return {"error": f"Extension '{name}' not found"}

    for path in sorted(ext_dir.glob("**/*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            path.rmdir()
    ext_dir.rmdir()
    return {"status": "removed", "name": name}
