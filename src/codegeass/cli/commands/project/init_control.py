"""Project control commands (enable, disable, set-default, update).

Note: The 'init' command has been merged into 'codegeass init'.
Use 'codegeass init [PATH]' to initialize and register a project.
"""

import click
from rich.console import Console

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
