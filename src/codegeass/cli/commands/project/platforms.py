"""Platform management commands for multi-platform skill support."""

import click
from rich.console import Console
from rich.table import Table

from codegeass.cli.commands.project.utils import get_project_repo
from codegeass.cli.main import Context, pass_context
from codegeass.factory.skill_resolver import PLATFORMS, Platform

console = Console()


@click.command("platforms")
@pass_context
def list_platforms(ctx: Context) -> None:
    """List all platforms and their status."""
    repo = get_project_repo(ctx)
    enabled = repo.get_enabled_platforms()

    table = Table(title="AI Agent Platforms")
    table.add_column("Platform", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Global Skills", style="dim")
    table.add_column("Project Skills", style="dim")

    for platform in Platform:
        config = PLATFORMS[platform]
        status = "[green]enabled[/green]" if platform.value in enabled else "[dim]disabled[/dim]"

        global_path = config.global_dir
        global_exists = global_path.exists()
        global_info = str(global_path) if global_exists else f"[dim]{global_path} (not found)[/dim]"

        project_path = ctx.project_dir / config.project_subdir
        project_exists = project_path.exists()
        project_info = (
            str(project_path) if project_exists else f"[dim]{project_path} (not found)[/dim]"
        )

        table.add_row(platform.value.capitalize(), status, global_info, project_info)

    console.print(table)
    console.print()
    console.print("[dim]Skill resolution order: project-claude → project-codex → "
                  "global-claude → global-codex[/dim]")


@click.command("enable-platform")
@click.argument("platform")
@pass_context
def enable_platform_cmd(ctx: Context, platform: str) -> None:
    """Enable a platform for skill resolution.

    PLATFORM: Platform name (claude, codex)
    """
    # Validate platform name
    try:
        Platform(platform.lower())
    except ValueError:
        valid = [p.value for p in Platform]
        console.print(f"[red]Invalid platform: {platform}[/red]")
        console.print(f"Valid platforms: {', '.join(valid)}")
        raise SystemExit(1)

    repo = get_project_repo(ctx)
    if repo.enable_platform(platform):
        console.print(f"[green]Platform enabled: {platform}[/green]")
    else:
        console.print(f"[yellow]Platform already enabled: {platform}[/yellow]")


@click.command("disable-platform")
@click.argument("platform")
@pass_context
def disable_platform_cmd(ctx: Context, platform: str) -> None:
    """Disable a platform for skill resolution.

    PLATFORM: Platform name (claude, codex)
    """
    # Validate platform name
    try:
        Platform(platform.lower())
    except ValueError:
        valid = [p.value for p in Platform]
        console.print(f"[red]Invalid platform: {platform}[/red]")
        console.print(f"Valid platforms: {', '.join(valid)}")
        raise SystemExit(1)

    repo = get_project_repo(ctx)
    enabled = repo.get_enabled_platforms()

    # Warn if this is the last platform
    if len(enabled) == 1 and platform.lower() in enabled:
        console.print("[red]Error: Cannot disable the last platform[/red]")
        console.print("At least one platform must remain enabled.")
        raise SystemExit(1)

    if repo.disable_platform(platform):
        console.print(f"[yellow]Platform disabled: {platform}[/yellow]")
    else:
        console.print(f"[dim]Platform not enabled: {platform}[/dim]")
