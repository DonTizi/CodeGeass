"""Project add and remove commands."""

from pathlib import Path

import click
from rich.console import Console

from codegeass.cli.commands.project.utils import get_project_repo
from codegeass.cli.main import Context, pass_context
from codegeass.core.entities import Project

console = Console()


@click.command("add")
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
    """Register a project with CodeGeass."""
    repo = get_project_repo(ctx)

    path = path.resolve()

    existing = repo.find_by_path(path)
    if existing:
        console.print(f"[yellow]Project already registered: {existing.name}[/yellow]")
        console.print(f"ID: {existing.id}")
        return

    project_name = name or path.name

    existing_name = repo.find_by_name(project_name)
    if existing_name:
        console.print(f"[red]Error: Project with name '{project_name}' already exists[/red]")
        console.print("Use --name to specify a different name")
        raise SystemExit(1)

    git_remote = _get_git_remote(path)

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

    if set_default or repo.is_empty():
        repo.set_default_project(new_project.id)
        console.print("[cyan]Set as default project[/cyan]")

    console.print(f"[green]Project registered: {project_name}[/green]")
    console.print(f"ID: {new_project.id}")
    console.print(f"Path: {path}")

    if not new_project.is_initialized():
        console.print("\n[yellow]Note: Project is not initialized.[/yellow]")
        console.print(f"Run: codegeass project init {path}")


@click.command("remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def remove_project(ctx: Context, name: str, yes: bool) -> None:
    """Unregister a project."""
    repo = get_project_repo(ctx)

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


def _get_git_remote(path: Path) -> str | None:
    """Try to get git remote URL from project."""
    git_config = path / ".git" / "config"
    if not git_config.exists():
        return None

    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(git_config)
        if 'remote "origin"' in config:
            return config['remote "origin"'].get("url")
    except Exception:
        pass

    return None
