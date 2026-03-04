from gcpclaw.tools.files import read_file, write_file


def test_write_and_read_within_workspace(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    monkeypatch.setenv("WORKSPACE_DIR", str(workspace))

    written = write_file("notes/todo.txt", "secure")
    assert written["status"] == "written"

    loaded = read_file("notes/todo.txt")
    assert loaded["content"] == "secure"


def test_path_traversal_is_blocked(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    monkeypatch.setenv("WORKSPACE_DIR", str(workspace))

    result = write_file("../workspace2/escape.txt", "bad")
    assert "error" in result
    assert "escapes the workspace directory" in result["error"]
