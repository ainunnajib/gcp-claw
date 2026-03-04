from gcpclaw.tools.shell import run_command


def test_shell_tool_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_DANGEROUS_TOOLS", raising=False)
    result = run_command("pwd")
    assert "error" in result
    assert "disabled" in result["error"]


def test_shell_blocks_non_allowlisted_command(monkeypatch):
    monkeypatch.setenv("ENABLE_DANGEROUS_TOOLS", "true")
    result = run_command("uname -a")
    assert result["error"] == "Command 'uname' is not permitted"


def test_shell_allows_safe_read_command(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_DANGEROUS_TOOLS", "true")
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path))
    result = run_command("pwd")
    assert result["returncode"] == 0
    assert str(tmp_path) in result["stdout"].strip()
