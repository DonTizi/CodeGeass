"""Project remove command.

Note: The 'add' command has been merged into 'codegeass init'.
Use 'codegeass init [PATH]' to initialize and register a project.
"""

import click
from rich.console import Console

from codegeass.cli.commands.project.utils import get_project_repo
from codegeass.cli.main import Context, pass_context

console = Console()


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
