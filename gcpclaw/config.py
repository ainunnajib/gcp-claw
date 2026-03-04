"""GCPClaw configuration module."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def get_model():
    """Get the configured model, supporting both native Gemini and LiteLLM models.

    Set AGENT_MODEL env var to control which model is used:
    - "gemini-2.0-flash" (default) — native Gemini
    - "anthropic/claude-sonnet-4-6" — Claude via LiteLLM
    - "openai/gpt-4o" — GPT-4o via LiteLLM
    - Any LiteLLM-compatible model string with provider/ prefix
    """
    model_id = os.getenv("AGENT_MODEL", "gemini-2.0-flash")
    if "/" in model_id:
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model=model_id)
    return model_id


def get_workspace_dir() -> Path:
    """Get the workspace directory for sandboxed file operations."""
    workspace = os.getenv("WORKSPACE_DIR", str(_package_dir() / "workspace"))
    path = Path(workspace).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _package_dir() -> Path:
    """Get the gcpclaw package directory."""
    return Path(__file__).parent


def get_extensions_dir() -> Path:
    """Get the extensions directory."""
    path = _package_dir() / "extensions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_skills_dirs() -> list[Path]:
    """Get all directories to scan for SKILL.md files."""
    pkg = _package_dir()
    return [pkg / "skills", pkg / "extensions"]
