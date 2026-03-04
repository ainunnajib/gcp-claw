# GCPClaw

A self-extending personal AI assistant built on [Google Cloud Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

GCPClaw combines ADK's agent runtime with multi-model support and Pi-style self-extension — the agent can write new tools for itself at runtime.

## Features

- **Multi-model** — Gemini (native), Claude, GPT-4o, or any LiteLLM-compatible model
- **Self-extending** — Agent creates new tools at runtime via `create_extension`, persisted to disk
- **Sandboxed extensions** — AST-validated code, blocked dangerous imports/builtins
- **SKILL.md discovery** — Portable skill format compatible with the open Agent Skills spec
- **Built-in tools** — Web search, URL fetch, file ops (sandboxed), shell commands
- **CLI + Web UI** — Powered by ADK's built-in `adk run` and `adk web`

## Quick Start

```bash
# Clone
git clone https://github.com/ainunnajib/gcp-claw.git
cd gcp-claw

# Install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env — add at least one API key (Google, Anthropic, or OpenAI)

# Run
adk web gcpclaw    # Web UI at http://localhost:8000
adk run gcpclaw    # CLI mode
```

## Configuration

Set your preferred model in `.env`:

```bash
# Native Gemini (default)
AGENT_MODEL=gemini-2.0-flash

# Claude via LiteLLM
AGENT_MODEL=anthropic/claude-sonnet-4-6

# GPT-4o via LiteLLM
AGENT_MODEL=openai/gpt-4o
```

## Architecture

```
gcp-claw/
├── gcpclaw/
│   ├── agent.py           # Root agent + skill discovery
│   ├── config.py          # Multi-model config, paths
│   ├── tools/
│   │   ├── web.py         # search_web, fetch_url
│   │   ├── files.py       # read_file, write_file, list_files (sandboxed)
│   │   ├── shell.py       # run_command (safety-controlled)
│   │   └── extend.py      # create_extension, list_extensions, remove_extension
│   ├── skills/            # SKILL.md-compatible skills
│   └── extensions/        # Agent-generated extensions (runtime)
├── .env.example
└── requirements.txt
```

## Self-Extension

Ask the agent to create a tool it doesn't have:

> "Create a tool that converts CSV to a markdown table"

The agent will:
1. Write Python code defining the tool function
2. Validate it against sandbox rules (no network, no subprocess, no dangerous ops)
3. Save it to `extensions/` with a `SKILL.md` for discoverability
4. Load it immediately — the new tool is available in the same session
5. Auto-load it on future startups

## Tools

| Tool | Description |
|---|---|
| `search_web` | Web search via Google CSE or SerpAPI |
| `fetch_url` | Fetch and extract text from web pages |
| `read_file` | Read files from sandboxed workspace |
| `write_file` | Write files to sandboxed workspace |
| `list_files` | List workspace directory contents |
| `run_command` | Execute shell commands (dangerous commands blocked) |
| `create_extension` | Create new tool extensions at runtime |
| `list_extensions` | List installed extensions |
| `remove_extension` | Remove an extension |

## License

MIT
