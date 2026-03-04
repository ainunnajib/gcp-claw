"""GCPClaw — A self-extending personal AI assistant built on Google Cloud ADK."""

import yaml
from pathlib import Path

from google.adk.agents import LlmAgent

from .config import get_model, get_skills_dirs
from .tools.web import search_web, fetch_url
from .tools.files import read_file, write_file, list_files
from .tools.shell import run_command
from .tools.extend import (
    create_extension,
    list_extensions,
    remove_extension,
    _load_extension_functions,
)


def _parse_skill_frontmatter(skill_md_path: Path) -> dict | None:
    """Parse YAML frontmatter from a SKILL.md file."""
    content = skill_md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        meta = yaml.safe_load(parts[1])
        return meta if isinstance(meta, dict) else None
    except yaml.YAMLError:
        return None


def discover_skills(skills_dirs: list[Path]) -> list[dict]:
    """Scan directories for SKILL.md files and return skill metadata."""
    skills = []
    for d in skills_dirs:
        if not d.exists():
            continue
        for skill_md in d.rglob("SKILL.md"):
            meta = _parse_skill_frontmatter(skill_md)
            if meta and "name" in meta and "description" in meta:
                skills.append({
                    "name": meta["name"],
                    "description": meta["description"],
                    "path": str(skill_md.parent),
                })
    return skills


def load_extension_tools() -> list:
    """Load all extension tools from the extensions directory."""
    from .config import get_extensions_dir
    ext_dir = get_extensions_dir()
    all_functions = []
    for child in sorted(ext_dir.iterdir()):
        if child.is_dir() and (child / "tool.py").exists():
            try:
                functions = _load_extension_functions(child)
                all_functions.extend(functions)
            except Exception:
                pass  # Skip broken extensions
    return all_functions


def format_skills_index(skills: list[dict]) -> str:
    """Format skills into a readable index for the system prompt."""
    if not skills:
        return "(no skills installed)"
    lines = []
    for s in skills:
        lines.append(f"- **{s['name']}**: {s['description']}")
    return "\n".join(lines)


# Discover skills and load extensions
skills = discover_skills(get_skills_dirs())
skills_index = format_skills_index(skills)
extension_tools = load_extension_tools()

# Core tools
core_tools = [
    search_web, fetch_url,
    read_file, write_file, list_files,
    run_command,
    create_extension, list_extensions, remove_extension,
]

root_agent = LlmAgent(
    name="gcpclaw",
    model=get_model(),
    description="A self-extending personal AI assistant powered by Google Cloud ADK.",
    instruction=f"""You are GCPClaw, a self-extending personal AI assistant.

## Core Capabilities
- **Web**: Search the web and fetch/read web pages
- **Files**: Read, write, and list files in the workspace directory
- **Shell**: Run shell commands with safety controls
- **Self-extend**: Create new tool extensions to expand your own capabilities
- **Skills**: Use installed skills (listed below)

## Self-Extension
When a user asks you to do something you can't do yet, use `create_extension` to write
a new Python tool for yourself. The extension code must be self-contained and can use
standard library modules (json, csv, re, datetime, math, collections, etc.).
Extensions are sandboxed — no network, no subprocess, no dangerous operations.

After creating an extension, its functions are immediately available as tools.
Extensions persist to disk and auto-load on restart.

## Available Skills
{skills_index}

## Guidelines
- Be concise and helpful
- Ask for clarification when the request is ambiguous
- When creating extensions, write clean code with docstrings so your functions work well as tools
- Always explain what you're doing before taking actions
""",
    tools=core_tools + extension_tools,
)
