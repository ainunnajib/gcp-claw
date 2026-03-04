from pathlib import Path

from gcpclaw.tools.extend import (
    _load_extension_functions,
    _validate_extension_code,
    create_extension,
)

VALID_CODE = '''
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b
'''


MALICIOUS_CODE = '''
import importlib

def pwn():
    """attempt breakout"""
    os = importlib.import_module("os")
    return os.listdir("/")
'''


def test_validator_blocks_non_allowlisted_imports():
    valid, reason = _validate_extension_code(MALICIOUS_CODE)
    assert not valid
    assert "not allowed" in reason


def test_create_extension_requires_dangerous_flag(monkeypatch):
    monkeypatch.delenv("ENABLE_DANGEROUS_TOOLS", raising=False)
    result = create_extension("safe-ext", "desc", VALID_CODE)
    assert "error" in result
    assert "disabled" in result["error"]


def test_create_extension_success(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_DANGEROUS_TOOLS", "true")
    monkeypatch.setenv("ENABLE_EXTENSION_EXECUTION", "false")
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path / "workspace"))

    from gcpclaw import config

    ext_dir = Path(config.get_extensions_dir())
    target = ext_dir / "math-ext"
    if target.exists():
        for path in sorted(target.glob("**/*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                path.rmdir()
        target.rmdir()

    result = create_extension("math-ext", "math helpers", VALID_CODE)
    assert result["status"] == "created"
    assert result["functions"] == ["add"]

    # cleanup
    for path in sorted(target.glob("**/*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            path.rmdir()
    if target.exists():
        target.rmdir()


def test_load_extension_functions_returns_empty_when_execution_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_EXTENSION_EXECUTION", "false")
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    (ext_dir / "tool.py").write_text(VALID_CODE, encoding="utf-8")

    assert _load_extension_functions(ext_dir) == []
