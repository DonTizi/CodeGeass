"""Project init and control commands (enable, disable, set-default, update)."""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from codegeass.cli.commands.project.utils import get_project_repo
from codegeass.cli.main import Context, pass_context

console = Console()


@click.command("set-default")
@click.argument("name")
@pass_context
def set_default_project(ctx: Context, name: str) -> None:
    """Set a project as the default."""
    repo = get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    repo.set_default_project(p.id)
    console.print(f"[green]Default project set: {p.name}[/green]")


@click.command("init")
@click.argument("path", type=click.Path(path_type=Path), default=".")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
@pass_context
def init_project(ctx: Context, path: Path, force: bool) -> None:
    """Initialize CodeGeass project structure."""
    path = path.resolve()

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    config_dir = path / "config"
    data_dir = path / "data"
    skills_dir = path / ".claude" / "skills"

    dirs_to_create = [
        config_dir,
        data_dir / "logs",
        data_dir / "sessions",
        skills_dir,
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"Created: {dir_path}")

    _create_settings_file(config_dir / "settings.yaml", force)
    _create_schedules_file(config_dir / "schedules.yaml", force)

    console.print(
        Panel.fit(
            f"[green]Project initialized at: {path}[/green]\n\n"
            "Next steps:\n"
            f"1. Register: codegeass project add {path}\n"
            "2. Create skills in .claude/skills/\n"
            "3. Add tasks with: codegeass task create",
            title="Initialized",
        )
    )


@click.command("enable")
@click.argument("name")
@pass_context
def enable_project(ctx: Context, name: str) -> None:
    """Enable a project."""
    repo = get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    repo.enable(p.id)
    console.print(f"[green]Project enabled: {p.name}[/green]")


@click.command("disable")
@click.argument("name")
@pass_context
def disable_project(ctx: Context, name: str) -> None:
    """Disable a project."""
    repo = get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    repo.disable(p.id)
    console.print(f"[yellow]Project disabled: {p.name}[/yellow]")


@click.command("update")
@click.argument("name")
@click.option("--new-name", help="New project name")
@click.option("--description", "-d", help="New description")
@click.option("--model", "-m", help="New default model")
@click.option("--timeout", "-t", type=int, help="New default timeout")
@click.option(
    "--autonomous/--no-autonomous", default=None, help="Enable/disable autonomous by default"
)
@click.option(
    "--shared-skills/--no-shared-skills", default=None, help="Enable/disable shared skills"
)
@pass_context
def update_project(
    ctx: Context,
    name: str,
    new_name: str | None,
    description: str | None,
    model: str | None,
    timeout: int | None,
    autonomous: bool | None,
    shared_skills: bool | None,
) -> None:
    """Update a project's configuration."""
    repo = get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    if new_name and new_name.lower() != p.name.lower():
        existing = repo.find_by_name(new_name)
        if existing:
            console.print(f"[red]Error: Project with name '{new_name}' already exists[/red]")
            raise SystemExit(1)
        p.name = new_name

    if description is not None:
        p.description = description
    if model is not None:
        p.default_model = model
    if timeout is not None:
        p.default_timeout = timeout
    if autonomous is not None:
        p.default_autonomous = autonomous
    if shared_skills is not None:
        p.use_shared_skills = shared_skills

    repo.save(p)
    console.print(f"[green]Project updated: {p.name}[/green]")


def _create_settings_file(settings_file: Path, force: bool) -> None:
    """Create default settings file."""
    if settings_file.exists() and not force:
        return

    default_settings = """# CodeGeass Settings
claude:
  default_model: sonnet
  default_timeout: 300
  unset_api_key: true

paths:
  skills: .claude/skills/
  logs: data/logs/
  sessions: data/sessions/

scheduler:
  check_interval: 60
  max_concurrent: 1
"""
    settings_file.write_text(default_settings)
    console.print(f"Created: {settings_file}")


def _create_schedules_file(schedules_file: Path, force: bool) -> None:
    """Create default schedules file."""
    if schedules_file.exists() and not force:
        return

    default_schedules = """# CodeGeass Scheduled Tasks
# Add your tasks here

tasks: []
"""
    schedules_file.write_text(default_schedules)
    console.print(f"Created: {schedules_file}")
