"""Project list and show commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.commands.project.utils import get_project_repo
from codegeass.cli.main import Context, pass_context

console = Console()


@click.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all projects including disabled")
@pass_context
def list_projects(ctx: Context, show_all: bool) -> None:
    """List all registered projects."""
    repo = get_project_repo(ctx)

    if not repo.exists():
        console.print("[yellow]No projects registry found.[/yellow]")
        console.print("Register a project with: codegeass project add /path/to/project")
        return

    projects = repo.find_all()

    if not projects:
        console.print("[yellow]No projects registered.[/yellow]")
        console.print("Register a project with: codegeass project add /path/to/project")
        return

    if not show_all:
        projects = [p for p in projects if p.enabled]

    default_id = repo.get_default_project_id()

    table = Table(title="Registered Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Path")
    table.add_column("Status")
    table.add_column("Default", justify="center")
    table.add_column("Skills", justify="right")

    for p in projects:
        status = "[green]enabled[/green]" if p.enabled else "[red]disabled[/red]"
        is_default = "[green]\u2713[/green]" if p.id == default_id else ""

        skill_count = _count_skills(p)
        path_status = _format_path_status(p)

        table.add_row(p.name, path_status, status, is_default, str(skill_count))

    console.print(table)


@click.command("show")
@click.argument("name")
@pass_context
def show_project(ctx: Context, name: str) -> None:
    """Show details of a registered project."""
    repo = get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    default_id = repo.get_default_project_id()
    is_default = p.id == default_id

    skill_count, skill_names = _get_skills_info(p)
    task_count = _get_task_count(p)

    details = _build_project_details(p, is_default, skill_count, skill_names, task_count)
    console.print(Panel(details, title=f"Project: {p.name}"))


def _count_skills(p) -> int:
    """Count skills in a project."""
    if not p.skills_dir.exists():
        return 0
    return len(
        [d for d in p.skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    )


def _format_path_status(p) -> str:
    """Format path with existence status."""
    path_status = str(p.path)
    if not p.exists():
        path_status = f"[red]{path_status} (not found)[/red]"
    return path_status


def _get_skills_info(p) -> tuple[int, list[str]]:
    """Get skill count and names for a project."""
    skill_count = 0
    skill_names = []
    if p.skills_dir.exists():
        for skill_dir in p.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skill_count += 1
                skill_names.append(skill_dir.name)
    return skill_count, skill_names


def _get_task_count(p) -> int:
    """Get task count for a project."""
    if not p.schedules_file.exists():
        return 0
    try:
        from codegeass.storage.task_repository import TaskRepository
        task_repo = TaskRepository(p.schedules_file)
        return len(task_repo.find_all())
    except Exception:
        return 0


def _build_project_details(
    p, is_default: bool, skill_count: int, skill_names: list[str], task_count: int
) -> str:
    """Build the details string for a project."""
    details = f"""[bold]ID:[/bold] {p.id}
[bold]Name:[/bold] {p.name}
[bold]Path:[/bold] {p.path}
[bold]Exists:[/bold] {"[green]yes[/green]" if p.exists() else "[red]no[/red]"}
[bold]Initialized:[/bold] {"[green]yes[/green]" if p.is_initialized() else "[yellow]no[/yellow]"}
[bold]Enabled:[/bold] {"[green]yes[/green]" if p.enabled else "[red]no[/red]"}
[bold]Default:[/bold] {"[green]yes[/green]" if is_default else "no"}
[bold]Description:[/bold] {p.description or "-"}

[bold]Defaults:[/bold]
  Model: {p.default_model}
  Timeout: {p.default_timeout}s
  Autonomous: {p.default_autonomous}

[bold]Skills:[/bold] {skill_count} project skill(s)"""

    if skill_names:
        details += f"\n  {', '.join(skill_names[:5])}"
        if len(skill_names) > 5:
            details += f" (+{len(skill_names) - 5} more)"

    details += f"""

[bold]Tasks:[/bold] {task_count} task(s)
[bold]Use Shared Skills:[/bold] {"yes" if p.use_shared_skills else "no"}"""

    if p.git_remote:
        details += f"\n\n[bold]Git Remote:[/bold] {p.git_remote}"

    if p.created_at:
        details += f"\n[bold]Registered:[/bold] {p.created_at[:19]}"

    return details
