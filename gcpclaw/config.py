"""GCPClaw configuration module."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from google.adk.models.lite_llm import LiteLlm

load_dotenv(Path(__file__).parent.parent / ".env")


def get_model() -> str | LiteLlm:
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


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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


def dangerous_tools_enabled() -> bool:
    """Whether risky tools (shell + extension creation/removal) are enabled."""
    return _env_bool("ENABLE_DANGEROUS_TOOLS", default=False)


def extension_execution_enabled() -> bool:
    """Whether runtime execution of user-generated extension tools is enabled."""
    return _env_bool("ENABLE_EXTENSION_EXECUTION", default=False)


def extension_container_enabled() -> bool:
    """Whether extensions should execute inside a container sandbox."""
    return _env_bool("ENABLE_EXTENSION_CONTAINER", default=False)


def extension_container_image() -> str:
    """Container image used for extension runner execution."""
    return os.getenv("EXTENSION_CONTAINER_IMAGE", "python:3.11-slim")


def validate_config() -> list[str]:
    """Validate configuration and return warning messages."""
    warnings: list[str] = []
    model = os.getenv("AGENT_MODEL", "gemini-2.0-flash")
    if "/" in model:
        provider = model.split("/", 1)[0]
        key_map = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
        expected_key = key_map.get(provider)
        if expected_key and not os.getenv(expected_key):
            warnings.append(f"AGENT_MODEL uses {provider} but {expected_key} is not set")
    elif not os.getenv("GOOGLE_API_KEY"):
        warnings.append("AGENT_MODEL uses Gemini but GOOGLE_API_KEY is not set")

    workspace = get_workspace_dir()
    try:
        test_file = workspace / ".config_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
    except OSError as exc:
        warnings.append(f"Workspace directory is not writable: {exc}")
    return warnings
