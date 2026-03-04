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


def test_shell_blocks_sed(monkeypatch):
    monkeypatch.setenv("ENABLE_DANGEROUS_TOOLS", "true")
    result = run_command("sed -e 's/a/b/' /etc/passwd")
    assert "error" in result
    assert "not permitted" in result["error"]


def test_shell_blocks_awk(monkeypatch):
    monkeypatch.setenv("ENABLE_DANGEROUS_TOOLS", "true")
    result = run_command("awk 'BEGIN{print 1}'")
    assert "error" in result


def test_shell_blocks_rg_outside_workspace(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_DANGEROUS_TOOLS", "true")
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path))
    result = run_command("rg pattern /etc/passwd")
    assert "error" in result
    assert "escapes workspace" in result["error"]


def test_shell_allows_grep_in_workspace(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_DANGEROUS_TOOLS", "true")
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path))
    (tmp_path / "test.txt").write_text("hello world", encoding="utf-8")
    result = run_command("grep hello test.txt")
    assert result["returncode"] == 0
