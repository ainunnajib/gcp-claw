"""Isolated extension execution worker."""

from __future__ import annotations

import argparse
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


def _safe_import(name: str, globals_=None, locals_=None, fromlist=(), level=0):
    root = name.split(".")[0]
    if root not in ALLOWED_IMPORTS:
        raise ImportError(f"Blocked import: {name}")
    return importlib.__import__(name, globals_, locals_, fromlist, level)


def _safe_builtins() -> dict:
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


def _load_namespace(tool_file: Path) -> dict:
    code = tool_file.read_text(encoding="utf-8")
    namespace = {"__builtins__": _safe_builtins()}
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
