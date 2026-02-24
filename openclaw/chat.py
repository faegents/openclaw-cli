from typing import Generator, Iterator
import anthropic


SYSTEM_TEMPLATE = """You are OpenClaw, an autonomous AI orchestrator managing a developer workspace running in a Docker container on a remote VPS. You coordinate multiple AI agents (HEARTBEAT, Engineering, Self-Improvement, Todo, Code Hygiene, Dashboard) that maintain projects, monitor system health, and perform self-improvement.

You have access to the following live workspace context:

## MEMORY.md (Architecture, Projects & Infrastructure)
{memory}

## Open TODO Items
{todo}

## Recent Monitor Activity (last 60 lines)
{monitor_logs}

Answer questions accurately and concisely. You know the full system architecture, active projects, open issues, and infrastructure state. For actions that require container access (restarting processes, running git commands, etc.), explain what would need to be done but clarify that direct execution requires container access."""


def build_system_prompt(workspace_state: dict) -> str:
    memory = (workspace_state.get("memory") or "Unavailable")[:4000]
    todo = (workspace_state.get("todo") or "Unavailable")[:2000]
    monitor_logs_raw = workspace_state.get("monitor_logs") or ""
    monitor_logs = "\n".join(monitor_logs_raw.splitlines()[-60:])
    return SYSTEM_TEMPLATE.format(memory=memory, todo=todo, monitor_logs=monitor_logs)


def stream_chat(
    client: anthropic.Anthropic,
    messages: list,
    system: str,
) -> Generator[str, None, None]:
    """Stream a Claude response, yielding text chunks."""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=system,
        messages=messages,
        thinking={"type": "adaptive"},
    ) as stream:
        for text in stream.text_stream:
            yield text
