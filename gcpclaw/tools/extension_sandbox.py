"""Container sandbox execution helpers for extension tools."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from ..config import extension_container_enabled, extension_container_image


def build_runner_command(
    ext_dir: Path,
    runner_path: Path,
    function_name: str,
    payload: dict[str, object],
) -> list[str]:
    args = [
        "--tool-file",
        str(ext_dir / "tool.py"),
        "--function",
        function_name,
        "--args-json",
        json.dumps(payload),
    ]
    if extension_container_enabled() and shutil.which("docker"):
        return [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cpus",
            "1",
            "--memory",
            "256m",
            "--pids-limit",
            "128",
            "--security-opt",
            "no-new-privileges:true",
            "-u",
            "65532:65532",
            "-v",
            f"{ext_dir}:{ext_dir}:ro",
            "-v",
            f"{runner_path}:{runner_path}:ro",
            "-w",
            str(ext_dir),
            extension_container_image(),
            "python",
            "-I",
            str(runner_path),
            *args,
        ]
    return [sys.executable, "-I", str(runner_path), *args]


def run_in_sandbox(
    command: list[str],
    cwd: Path,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
        shell=False,
    )  # nosec B603
