from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box
from datetime import datetime

console = Console()


def parse_todo_items(todo_md: str) -> list[dict]:
    """Parse todo.md markdown into structured items."""
    items = []
    if not todo_md:
        return items
    for line in todo_md.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- [ ]"):
            items.append({"status": "open", "text": stripped[6:].strip()})
        elif stripped.startswith("- [x]") or stripped.startswith("- [X]"):
            items.append({"status": "done", "text": stripped[6:].strip()})
        elif "[USER-ACTION-REQUIRED]" in stripped or "[OPEN INFRA" in stripped or "[PENDING" in stripped:
            items.append({"status": "blocked", "text": stripped.lstrip("- ").strip()})
    return items[:25]


def parse_projects(memory_md: str) -> list[str]:
    """Extract project names from MEMORY.md ## Projects section."""
    projects = []
    if not memory_md:
        return projects
    in_projects = False
    for line in memory_md.splitlines():
        if "## Projects" in line:
            in_projects = True
            continue
        if in_projects and line.startswith("## "):
            break
        if in_projects and line.startswith("- **"):
            parts = line.split("**")
            if len(parts) >= 2:
                projects.append(parts[1])
    return projects


def make_header(extra: str = "") -> Panel:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    content = Text.assemble(
        ("OpenClaw", "bold white"),
        "  Command Center  ",
        (now, "dim"),
        ("  " + extra if extra else "", "green"),
    )
    return Panel(content, style="white on blue", padding=(0, 1))


def make_projects_panel(memory_md: str) -> Panel:
    projects = parse_projects(memory_md)
    if not projects:
        body = "[dim]No projects found[/dim]"
    else:
        body = "\n".join(f"[cyan]•[/cyan] [bold]{p}[/bold]" for p in projects)
    return Panel(body, title="[bold blue]Projects[/bold blue]", border_style="blue", padding=(1, 1))


def make_todo_panel(todo_md: str) -> Panel:
    items = parse_todo_items(todo_md)
    open_items = [i for i in items if i["status"] in ("open", "blocked")]

    if not items:
        return Panel(
            "[green]All clear — no open items[/green]",
            title="[bold yellow]TODO[/bold yellow]",
            border_style="yellow",
        )

    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Icon", width=3, no_wrap=True)
    table.add_column("Item")

    for item in items[:20]:
        if item["status"] == "open":
            icon = "[yellow]⬜[/yellow]"
        elif item["status"] == "blocked":
            icon = "[red]🚫[/red]"
        else:
            icon = "[green]✅[/green]"
        text = item["text"]
        if len(text) > 70:
            text = text[:67] + "..."
        table.add_row(icon, text)

    title = f"[bold yellow]TODO ({len(open_items)} open / {len(items)} total)[/bold yellow]"
    return Panel(table, title=title, border_style="yellow", padding=(0, 1))


def make_activity_panel(monitor_logs: str, n: int = 20) -> Panel:
    if not monitor_logs:
        body = "[dim]No activity logs available[/dim]"
    else:
        lines = monitor_logs.splitlines()[-n:]
        body = "\n".join(lines)
    return Panel(body, title="[bold green]Recent Activity[/bold green]", border_style="green", padding=(0, 1))


def make_dashboard(state: dict) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
    )
    layout["body"].split_row(
        Layout(name="projects", ratio=1),
        Layout(name="main", ratio=3),
    )
    layout["main"].split_column(
        Layout(name="todo", ratio=1),
        Layout(name="activity", ratio=1),
    )

    layout["header"].update(make_header())
    layout["projects"].update(make_projects_panel(state.get("memory")))
    layout["todo"].update(make_todo_panel(state.get("todo")))
    layout["activity"].update(make_activity_panel(state.get("monitor_logs")))
    return layout
