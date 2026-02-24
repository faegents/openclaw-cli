import sys
import click
import anthropic
from rich.prompt import Prompt
from rich.markdown import Markdown

from .config import load_config, save_config, Config
from .workspace import WorkspaceFetcher
from .chat import build_system_prompt, stream_chat
from .display import (
    console,
    make_header,
    make_projects_panel,
    make_todo_panel,
    make_activity_panel,
    make_dashboard,
)


def _get_fetcher(config: Config) -> WorkspaceFetcher:
    return WorkspaceFetcher(config.github_token, config.github_repo, config.github_branch)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """OpenClaw — command center for your AI agent workspace."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(dashboard)


@cli.command()
def dashboard() -> None:
    """Show a static TUI dashboard (projects, todos, activity)."""
    config = load_config()
    if not config.github_token:
        console.print("[red]Error: GITHUB_TOKEN not configured. Run: oc configure[/red]")
        sys.exit(1)

    console.print("[dim]Fetching workspace state...[/dim]")
    fetcher = _get_fetcher(config)
    state = fetcher.get_workspace_state()
    layout = make_dashboard(state)
    console.print(layout)


@cli.command()
@click.argument("message", required=False)
def chat(message: str | None) -> None:
    """Chat with OpenClaw via the Claude API.

    Provide a MESSAGE argument for a one-shot query, or omit it to enter
    an interactive REPL session.
    """
    config = load_config()
    if not config.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not configured. Run: oc configure[/red]")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    console.print("[dim]Loading workspace context...[/dim]")
    fetcher = _get_fetcher(config)
    state = fetcher.get_workspace_state()
    system = build_system_prompt(state)

    conversation: list[dict] = []

    def _send(user_msg: str) -> str:
        conversation.append({"role": "user", "content": user_msg})
        console.print("\n[bold green]OpenClaw:[/bold green] ", end="")
        response_text = ""
        for chunk in stream_chat(client, conversation, system):
            console.print(chunk, end="")
            response_text += chunk
        console.print("\n")
        conversation.append({"role": "assistant", "content": response_text})
        return response_text

    if message:
        console.print(f"[bold cyan]You:[/bold cyan] {message}")
        _send(message)
    else:
        console.print(make_header("Interactive Chat"))
        console.print("[dim]Type your message and press Enter. Type 'exit' or Ctrl-C to quit.[/dim]\n")
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Goodbye.[/dim]")
                break
            if user_input.strip().lower() in ("exit", "quit", "q", "bye"):
                console.print("[dim]Goodbye.[/dim]")
                break
            if not user_input.strip():
                continue
            _send(user_input)


@cli.command()
def status() -> None:
    """Show current open items and blocked tasks."""
    config = load_config()
    fetcher = _get_fetcher(config)
    todo_md = fetcher.get_file("memory/todo.md")
    console.print(make_todo_panel(todo_md))


@cli.command()
def errors() -> None:
    """List open errors and USER-ACTION-REQUIRED items from todo.md."""
    config = load_config()
    fetcher = _get_fetcher(config)
    todo_md = fetcher.get_file("memory/todo.md")
    console.print(make_todo_panel(todo_md))


@cli.command()
def projects() -> None:
    """List active projects from workspace MEMORY.md."""
    config = load_config()
    fetcher = _get_fetcher(config)
    memory_md = fetcher.get_file("memory/MEMORY.md")
    console.print(make_projects_panel(memory_md))


@cli.command()
@click.option("--lines", "-n", default=50, show_default=True, help="Number of log lines to display.")
def logs(lines: int) -> None:
    """Show recent monitor activity logs."""
    config = load_config()
    fetcher = _get_fetcher(config)
    monitor_logs = fetcher.get_file("memory/monitor_logs.md")
    console.print(make_activity_panel(monitor_logs, n=lines))


@cli.command()
def configure() -> None:
    """Interactive configuration wizard — set API keys and workspace repo."""
    config = load_config()

    console.print("[bold]OpenClaw Configuration[/bold]\n")
    console.print("Press Enter to keep existing values.\n")

    api_key = Prompt.ask(
        "Anthropic API key",
        default=config.anthropic_api_key or "",
        password=True,
    )
    github_token = Prompt.ask(
        "GitHub token (repo scope)",
        default=config.github_token or "",
        password=True,
    )
    github_repo = Prompt.ask(
        "GitHub repo (owner/name)",
        default=config.github_repo,
    )

    new_config = Config(
        anthropic_api_key=api_key or config.anthropic_api_key,
        github_token=github_token or config.github_token,
        github_repo=github_repo,
    )
    save_config(new_config)
    console.print("\n[green]Configuration saved to ~/.openclaw/config.json[/green]")


def main() -> None:
    cli()
