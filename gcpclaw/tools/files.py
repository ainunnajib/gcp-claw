"""File operation tools — sandboxed to the configured workspace directory."""

from pathlib import Path

from ..config import get_workspace_dir


def _resolve_safe(path: str) -> Path:
    """Resolve a path within the workspace, preventing directory traversal."""
    workspace = get_workspace_dir()
    resolved = (workspace / path).resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError:
        raise ValueError(f"Path '{path}' escapes the workspace directory") from None
    return resolved


def read_file(path: str) -> dict:
    """Read a file from the workspace.

    Args:
        path: Relative path within the workspace directory.

    Returns:
        dict with 'content' on success or 'error' on failure.
    """
    try:
        resolved = _resolve_safe(path)
        if not resolved.is_file():
            return {"error": f"File not found: {path}"}
        content = resolved.read_text(encoding="utf-8", errors="replace")
        return {"path": path, "content": content, "size": len(content)}
    except Exception as e:
        return {"error": str(e)}


def write_file(path: str, content: str) -> dict:
    """Write content to a file in the workspace. Creates parent directories if needed.

    Args:
        path: Relative path within the workspace directory.
        content: The text content to write.

    Returns:
        dict with 'status' on success or 'error' on failure.
    """
    try:
        resolved = _resolve_safe(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return {"status": "written", "path": path, "size": len(content)}
    except Exception as e:
        return {"error": str(e)}


def list_files(directory: str = ".") -> dict:
    """List files and directories in a workspace subdirectory.

    Args:
        directory: Relative path within the workspace. Defaults to workspace root.

    Returns:
        dict with 'entries' list on success or 'error' on failure.
    """
    try:
        resolved = _resolve_safe(directory)
        if not resolved.is_dir():
            return {"error": f"Not a directory: {directory}"}
        entries = []
        for item in sorted(resolved.iterdir()):
            rel = item.relative_to(get_workspace_dir())
            entries.append({
                "name": item.name,
                "path": str(rel),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"directory": directory, "entries": entries}
    except Exception as e:
        return {"error": str(e)}
