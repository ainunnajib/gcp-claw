"""Isolated extension execution worker."""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import traceback
from pathlib import Path

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
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "input",
}


def _safe_import(
    name: str,
    globals_: dict | None = None,
    locals_: dict | None = None,
    fromlist: tuple | list = (),
    level: int = 0,
) -> object:
    root = name.split(".")[0]
    if root not in ALLOWED_IMPORTS:
        raise ImportError(f"Blocked import: {name}")
    return importlib.__import__(name, globals_, locals_, fromlist, level)


def _safe_builtins() -> dict[str, object]:
    return {
        "__import__": _safe_import,
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "max": max,
        "min": min,
        "range": range,
        "round": round,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
    }


def _validate_extension_code_runtime(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise ImportError(f"Blocked import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                raise ImportError("Relative imports are not allowed")
            root = node.module.split(".")[0]
            if root not in ALLOWED_IMPORTS:
                raise ImportError(f"Blocked import: {node.module}")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise ValueError("Dunder attribute access is not allowed")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
                raise ValueError(f"Blocked call: {node.func.id}")


def _load_namespace(tool_file: Path) -> dict[str, object]:
    code = tool_file.read_text(encoding="utf-8")
    _validate_extension_code_runtime(code)
    namespace: dict[str, object] = {"__builtins__": _safe_builtins()}
    exec(compile(code, str(tool_file), "exec"), namespace, namespace)  # nosec B102
    return namespace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool-file", required=True)
    parser.add_argument("--function", required=True)
    parser.add_argument("--args-json", required=True)
    args = parser.parse_args()

    try:
        payload = json.loads(args.args_json)
        if not isinstance(payload, dict):
            raise ValueError("args-json must be an object")
        namespace = _load_namespace(Path(args.tool_file))
        fn = namespace.get(args.function)
        if not callable(fn):
            raise ValueError(f"Function not found: {args.function}")
        result = fn(**payload)
        print(json.dumps({"result": result}, ensure_ascii=True))
        return 0
    except Exception as exc:
        err = {"error": str(exc), "traceback": traceback.format_exc(limit=3)}
        print(json.dumps(err, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
