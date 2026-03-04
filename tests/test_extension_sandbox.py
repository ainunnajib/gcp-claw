from pathlib import Path

from gcpclaw.tools.extension_sandbox import build_runner_command


def test_build_runner_command_local(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_EXTENSION_CONTAINER", "false")
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    command = build_runner_command(
        ext_dir=ext_dir,
        runner_path=Path("/tmp/runner.py"),
        function_name="add",
        payload={"a": 1, "b": 2},
    )
    assert command[1] == "-I"
    assert "--function" in command


def test_build_runner_command_container(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_EXTENSION_CONTAINER", "true")
    monkeypatch.setattr("gcpclaw.tools.extension_sandbox.shutil.which", lambda _: "/usr/bin/docker")
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    command = build_runner_command(
        ext_dir=ext_dir,
        runner_path=Path("/tmp/runner.py"),
        function_name="add",
        payload={"a": 1},
    )
    assert command[0] == "docker"
    assert "--network" in command
    assert "none" in command
