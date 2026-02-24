# openclaw-cli

Command center CLI for the OpenClaw AI agent workspace. Connects to your workspace GitHub repo and the Claude API to give you a live view of projects, agents, and open issues — from anywhere.

## Features

- **Dashboard** — side-by-side panels: active projects, open issues, agent activity
- **Live watch mode** — auto-refreshing full-screen TUI (`--watch`)
- **Chat** — interactive or one-shot Claude conversation with full workspace context
- **Projects** — list all active projects from MEMORY.md
- **Agents** — tail recent monitor activity logs
- **Errors/Status** — show open issues and blocked tasks from todo.md

## Installation

```bash
pip install -e .
# or
pip install -r requirements.txt && python -m openclaw
```

## Configuration

Run the interactive setup wizard:

```bash
oc configure
```

This creates `~/.openclaw/config.json` with your API keys. You can also use environment variables:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (for `chat`) |
| `GITHUB_TOKEN` | GitHub personal access token (repo scope) |
| `OPENCLAW_REPO` | Workspace repo, default `faegents/conductor-workspace` |
| `OPENCLAW_BRANCH` | Branch, default `main` |

## Commands

```
oc                      # Show static dashboard (default)
oc dashboard            # Same as above
oc dashboard --watch    # Live-refreshing full-screen dashboard
oc dashboard -w -i 60   # Live, refresh every 60s

oc chat                 # Interactive REPL with Claude + workspace context
oc chat "What's broken?"# One-shot query

oc projects             # List active projects
oc agents               # Show recent agent activity logs
oc errors               # Show open issues / blocked tasks
oc status               # Same as errors

oc configure            # Set API keys and repo
```

## Data Sources

All data is pulled from your workspace GitHub repo (configured via `OPENCLAW_REPO`):

| Data | File |
|---|---|
| Projects / architecture | `memory/MEMORY.md` |
| Open issues | `memory/todo.md` |
| Agent activity | `memory/monitor_logs.md` |
| Lessons learned | `memory/lessons_learned.md` |

Chat mode injects all of the above as context into Claude Opus 4.6 with adaptive thinking enabled.

## Requirements

- Python 3.10+
- `anthropic`, `rich`, `click`, `httpx`
