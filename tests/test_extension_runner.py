import json
import subprocess
import sys
import textwrap
from pathlib import Path

RUNNER = Path(__file__).resolve().parent.parent / "gcpclaw" / "tools" / "extension_runner.py"


def test_runner_executes_valid_code(tmp_path):
    code = textwrap.dedent(
        '''
        def greet(name: str) -> str:
            """Say hello."""
            return f"Hello, {name}!"
        '''
    )
    tool_file = tmp_path / "tool.py"
    tool_file.write_text(code, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(RUNNER),
            "--tool-file",
            str(tool_file),
            "--function",
            "greet",
            "--args-json",
            '{"name": "World"}',
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["result"] == "Hello, World!"


def test_runner_blocks_tampered_code(tmp_path):
    code = "import os\ndef evil():\n    \"\"\"bad\"\"\"\n    return os.listdir('/')"
    tool_file = tmp_path / "tool.py"
    tool_file.write_text(code, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(RUNNER),
            "--tool-file",
            str(tool_file),
            "--function",
            "evil",
            "--args-json",
            "{}",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "Blocked import" in output["error"]
