from datetime import datetime

from rich.columns import Columns
from rich.console import Console, Group as RenderGroup
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


# ── Parsers ──────────────────────────────────────────────────────────────────

def parse_projects(memory_md: str) -> list[dict]:
    """Extract project names and status lines from MEMORY.md ## Projects section."""
    projects = []
    if not memory_md:
        return projects
    in_projects = False
    for line in memory_md.splitlines():
        if line.strip().startswith("## Projects"):
            in_projects = True
            continue
        if in_projects and line.startswith("## "):
            break
        if in_projects and line.strip().startswith("- **"):
            parts = line.split("**")
            name = parts[1] if len(parts) >= 2 else line.strip()
            desc = parts[2].lstrip(":").strip()[:60] if len(parts) >= 3 else ""
            projects.append({"name": name, "desc": desc})
    return projects


def parse_todo_items(todo_md: str) -> list[dict]:
    """Parse todo.md markdown into structured items (open/done/blocked)."""
    items = []
    if not todo_md:
        return items
    for line in todo_md.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("- [ ]"):
            items.append({"status": "open", "text": s[6:].strip()})
        elif s.startswith("- [x]") or s.startswith("- [X]"):
            items.append({"status": "done", "text": s[6:].strip()})
        elif any(tag in s for tag in ("[USER-ACTION-REQUIRED]", "[PENDING", "[OPEN INFRA")):
            items.append({"status": "blocked", "text": s.lstrip("- ").strip()})
    return items[:30]


def parse_monitor_lines(monitor_md: str, n: int = 20) -> list[str]:
    """Return the last n non-empty lines from monitor_logs.md."""
    if not monitor_md:
        return []
    lines = [ln for ln in monitor_md.splitlines() if ln.strip()]
    return lines[-n:]


# ── Panel builders ────────────────────────────────────────────────────────────

def make_header_panel(subtitle: str = "") -> Panel:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    content = Text.assemble(
        ("OpenClaw", "bold white"),
        "  ·  Command Center  ·  ",
        (now, "dim"),
        ("  " + subtitle if subtitle else "", "green bold"),
    )
    return Panel(content, style="white on #003060", padding=(0, 2))


def make_projects_panel(memory_md: str) -> Panel:
    projects = parse_projects(memory_md)
    if not projects:
        body: str | Table = "[dim]No projects found[/dim]"
    else:
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Bullet", width=2, no_wrap=True)
        table.add_column("Name")
        table.add_column("Desc", style="dim")
        for p in projects:
            table.add_row("[cyan]•[/cyan]", f"[bold]{p['name']}[/bold]", p["desc"])
        body = table
    return Panel(body, title="[bold cyan]Projects[/bold cyan]", border_style="cyan", padding=(0, 1))


def make_todo_panel(todo_md: str) -> Panel:
    items = parse_todo_items(todo_md)
    open_items = [i for i in items if i["status"] in ("open", "blocked")]

    if not items:
        return Panel(
            "[green]All clear — no items tracked[/green]",
            title="[bold yellow]Open Issues[/bold yellow]",
            border_style="yellow",
        )

    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Icon", width=3, no_wrap=True)
    table.add_column("Item")

    icons = {"open": "[yellow]☐[/yellow]", "blocked": "[red]⛔[/red]", "done": "[green]✓[/green]"}
    for item in items[:20]:
        icon = icons.get(item["status"], "?")
        text = item["text"]
        if len(text) > 72:
            text = text[:69] + "..."
        style = "dim" if item["status"] == "done" else ""
        table.add_row(icon, f"[{style}]{text}[/{style}]" if style else text)

    title = f"[bold yellow]Open Issues[/bold yellow] [dim]({len(open_items)} open / {len(items)} total)[/dim]"
    return Panel(table, title=title, border_style="yellow", padding=(0, 1))


def make_activity_panel(monitor_md: str, n: int = 20) -> Panel:
    lines = parse_monitor_lines(monitor_md, n)
    if not lines:
        body = "[dim]No monitor activity available[/dim]"
    else:
        body = "\n".join(f"[dim]{ln}[/dim]" if ln.startswith("#") else ln for ln in lines)
    return Panel(
        body,
        title="[bold green]Agent Activity[/bold green]",
        border_style="green",
        padding=(0, 1),
    )


# ── Dashboard composers ───────────────────────────────────────────────────────

def make_dashboard_static(state: dict) -> RenderGroup:
    """Static render: stack header + columns + activity."""
    top = Columns(
        [
            make_projects_panel(state.get("memory")),
            make_todo_panel(state.get("todo")),
        ],
        expand=True,
        equal=True,
    )
    return RenderGroup(
        make_header_panel(),
        top,
        make_activity_panel(state.get("monitor_logs")),
    )


def make_live_layout(state: dict) -> Layout:
    """Full-screen Layout for Rich Live watch mode."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="top", ratio=1),
        Layout(name="activity", ratio=1),
    )
    layout["top"].split_row(
        Layout(name="projects"),
        Layout(name="issues"),
    )
    layout["header"].update(make_header_panel("● LIVE"))
    layout["projects"].update(make_projects_panel(state.get("memory")))
    layout["issues"].update(make_todo_panel(state.get("todo")))
    layout["activity"].update(make_activity_panel(state.get("monitor_logs"), n=15))
    return layout


# Re-export legacy name used by CLI
def make_header(subtitle: str = "") -> Panel:
    return make_header_panel(subtitle)


def make_dashboard(state: dict) -> RenderGroup:
    return make_dashboard_static(state)
