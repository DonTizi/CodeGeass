"""Project management CLI commands for multi-project support."""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context
from codegeass.core.entities import Project
from codegeass.storage.project_repository import ProjectRepository

console = Console()


def _get_project_repo(ctx: Context) -> ProjectRepository:
    """Get project repository from context or create new one."""
    if hasattr(ctx, "_project_repo") and ctx._project_repo is not None:
        return ctx._project_repo
    return ProjectRepository()


@click.group()
def project() -> None:
    """Manage registered projects."""
    pass


@project.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all projects including disabled")
@pass_context
def list_projects(ctx: Context, show_all: bool) -> None:
    """List all registered projects."""
    repo = _get_project_repo(ctx)

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

        # Count skills
        skill_count = 0
        if p.skills_dir.exists():
            skill_count = len(
                [d for d in p.skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
            )

        # Show path status
        path_status = str(p.path)
        if not p.exists():
            path_status = f"[red]{path_status} (not found)[/red]"

        table.add_row(
            p.name,
            path_status,
            status,
            is_default,
            str(skill_count),
        )

    console.print(table)


@project.command("add")
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--name", "-n", help="Project name (defaults to directory name)")
@click.option("--description", "-d", default="", help="Project description")
@click.option("--model", "-m", default="sonnet", help="Default model (haiku, sonnet, opus)")
@click.option("--timeout", "-t", default=300, type=int, help="Default timeout in seconds")
@click.option("--autonomous", is_flag=True, help="Enable autonomous mode by default")
@click.option("--no-shared-skills", is_flag=True, help="Disable shared skills for this project")
@click.option("--set-default", is_flag=True, help="Set as default project")
@pass_context
def add_project(
    ctx: Context,
    path: Path,
    name: str | None,
    description: str,
    model: str,
    timeout: int,
    autonomous: bool,
    no_shared_skills: bool,
    set_default: bool,
) -> None:
    """Register a project with CodeGeass.

    PATH is the path to the project directory. It should contain a CodeGeass
    structure (config/ and .claude/skills/) or you can run 'codegeass project init'
    to create it.
    """
    repo = _get_project_repo(ctx)

    path = path.resolve()

    # Check if already registered
    existing = repo.find_by_path(path)
    if existing:
        console.print(f"[yellow]Project already registered: {existing.name}[/yellow]")
        console.print(f"ID: {existing.id}")
        return

    # Get project name
    project_name = name or path.name

    # Check for name collision
    existing_name = repo.find_by_name(project_name)
    if existing_name:
        console.print(f"[red]Error: Project with name '{project_name}' already exists[/red]")
        console.print("Use --name to specify a different name")
        raise SystemExit(1)

    # Try to get git remote
    git_remote = None
    git_config = path / ".git" / "config"
    if git_config.exists():
        try:
            import configparser

            config = configparser.ConfigParser()
            config.read(git_config)
            if 'remote "origin"' in config:
                git_remote = config['remote "origin"'].get("url")
        except Exception:
            pass

    # Create project
    new_project = Project.create(
        name=project_name,
        path=path,
        description=description,
        default_model=model,
        default_timeout=timeout,
        default_autonomous=autonomous,
        git_remote=git_remote,
        use_shared_skills=not no_shared_skills,
    )

    repo.save(new_project)

    # Set as default if requested or if first project
    if set_default or repo.is_empty():
        repo.set_default_project(new_project.id)
        console.print("[cyan]Set as default project[/cyan]")

    console.print(f"[green]Project registered: {project_name}[/green]")
    console.print(f"ID: {new_project.id}")
    console.print(f"Path: {path}")

    # Check if initialized
    if not new_project.is_initialized():
        console.print("\n[yellow]Note: Project is not initialized.[/yellow]")
        console.print(f"Run: codegeass project init {path}")


@project.command("remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def remove_project(ctx: Context, name: str, yes: bool) -> None:
    """Unregister a project.

    This only removes the project from the registry. Project files are not deleted.
    """
    repo = _get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    if not yes:
        if not click.confirm(f"Unregister project '{p.name}'?"):
            console.print("Cancelled")
            return

    repo.delete(p.id)
    console.print(f"[yellow]Project unregistered: {p.name}[/yellow]")
    console.print("Note: Project files were not deleted")


@project.command("show")
@click.argument("name")
@pass_context
def show_project(ctx: Context, name: str) -> None:
    """Show details of a registered project."""
    repo = _get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    default_id = repo.get_default_project_id()
    is_default = p.id == default_id

    # Count skills
    skill_count = 0
    skill_names = []
    if p.skills_dir.exists():
        for skill_dir in p.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skill_count += 1
                skill_names.append(skill_dir.name)

    # Count tasks
    task_count = 0
    if p.schedules_file.exists():
        try:
            from codegeass.storage.task_repository import TaskRepository

            task_repo = TaskRepository(p.schedules_file)
            task_count = len(task_repo.find_all())
        except Exception:
            pass

    # Build details panel
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

    console.print(Panel(details, title=f"Project: {p.name}"))


@project.command("set-default")
@click.argument("name")
@pass_context
def set_default_project(ctx: Context, name: str) -> None:
    """Set a project as the default.

    The default project is used when no --project flag is specified.
    """
    repo = _get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    repo.set_default_project(p.id)
    console.print(f"[green]Default project set: {p.name}[/green]")


@project.command("init")
@click.argument("path", type=click.Path(path_type=Path), default=".")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
@pass_context
def init_project(ctx: Context, path: Path, force: bool) -> None:
    """Initialize CodeGeass project structure.

    Creates the config/, data/, and .claude/skills/ directories and default
    configuration files.
    """
    path = path.resolve()

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    config_dir = path / "config"
    data_dir = path / "data"
    skills_dir = path / ".claude" / "skills"

    # Create directories
    dirs_to_create = [
        config_dir,
        data_dir / "logs",
        data_dir / "sessions",
        skills_dir,
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"Created: {dir_path}")

    # Create default settings
    settings_file = config_dir / "settings.yaml"
    if not settings_file.exists() or force:
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

    # Create default schedules
    schedules_file = config_dir / "schedules.yaml"
    if not schedules_file.exists() or force:
        default_schedules = """# CodeGeass Scheduled Tasks
# Add your tasks here

tasks: []
"""
        schedules_file.write_text(default_schedules)
        console.print(f"Created: {schedules_file}")

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


@project.command("enable")
@click.argument("name")
@pass_context
def enable_project(ctx: Context, name: str) -> None:
    """Enable a project."""
    repo = _get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    repo.enable(p.id)
    console.print(f"[green]Project enabled: {p.name}[/green]")


@project.command("disable")
@click.argument("name")
@pass_context
def disable_project(ctx: Context, name: str) -> None:
    """Disable a project."""
    repo = _get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    repo.disable(p.id)
    console.print(f"[yellow]Project disabled: {p.name}[/yellow]")


@project.command("update")
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
    repo = _get_project_repo(ctx)

    p = repo.find_by_id_or_name(name)

    if not p:
        console.print(f"[red]Project not found: {name}[/red]")
        raise SystemExit(1)

    # Check for name collision if renaming
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
