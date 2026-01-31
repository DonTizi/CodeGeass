"""Data management CLI commands."""

import click
from rich.console import Console
from rich.table import Table

from codegeass.cli.main import Context, pass_context
from codegeass.storage.data_manager import CleanupResult, DataManager, DataStats

console = Console()


@click.group()
def data():
    """Manage execution data and cleanup.

    Execution data (logs, sessions, approvals) is stored globally at
    ~/.codegeass/data/{project-id}/ to avoid polluting project directories.

    Default retention periods:
      - Sessions: 7 days
      - Logs: 30 days
      - Approvals: 90 days
    """
    pass


@data.command("stats")
@click.option(
    "--all-projects",
    is_flag=True,
    help="Show stats for all projects",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as JSON",
)
@pass_context
def data_stats(ctx: Context, all_projects: bool, as_json: bool) -> None:
    """Show data usage statistics."""
    import json

    manager = DataManager()

    if all_projects:
        stats_list = manager.get_stats()
        if not isinstance(stats_list, list):
            stats_list = [stats_list]
    else:
        # Get current project ID
        project_id = None
        if ctx.current_project:
            project_id = ctx.current_project.id
        else:
            # Use path hash for unregistered projects
            project_id = manager.hash_path(ctx.project_dir)

        stats_result = manager.get_stats(project_id)
        stats_list = [stats_result] if isinstance(stats_result, DataStats) else []

    if not stats_list:
        console.print("[yellow]No data found.[/yellow]")
        return

    if as_json:
        output = [s.to_dict() for s in stats_list]
        console.print(json.dumps(output, indent=2))
        return

    # Display as table
    table = Table(title="Data Usage Statistics")
    table.add_column("Project ID", style="cyan")
    table.add_column("Logs", justify="right")
    table.add_column("Sessions", justify="right")
    table.add_column("Approvals", justify="right")
    table.add_column("Total Size", justify="right", style="green")

    total_size = 0
    for stats in stats_list:
        table.add_row(
            stats.project_id,
            f"{stats.logs_count} files",
            f"{stats.sessions_count} files",
            f"{stats.approvals_count} entries",
            f"{stats.total_size_mb:.2f} MB",
        )
        total_size += stats.total_size_bytes

    if len(stats_list) > 1:
        table.add_section()
        table.add_row(
            "[bold]Total[/bold]",
            "",
            "",
            "",
            f"[bold]{total_size / (1024 * 1024):.2f} MB[/bold]",
        )

    console.print(table)


@data.command("cleanup")
@click.option(
    "--sessions",
    default=7,
    type=int,
    help="Keep sessions for N days (default: 7)",
)
@click.option(
    "--logs",
    default=30,
    type=int,
    help="Keep logs for N days (default: 30)",
)
@click.option(
    "--approvals",
    default=90,
    type=int,
    help="Keep approvals for N days (default: 90)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without deleting",
)
@click.option(
    "--all-projects",
    is_flag=True,
    help="Clean all projects",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as JSON",
)
@pass_context
def data_cleanup(
    ctx: Context,
    sessions: int,
    logs: int,
    approvals: int,
    dry_run: bool,
    all_projects: bool,
    as_json: bool,
) -> None:
    """Clean up old execution data.

    Remove data older than the specified retention periods:

    \b
      --sessions N: Keep sessions for N days (default: 7)
      --logs N: Keep logs for N days (default: 30)
      --approvals N: Keep approvals for N days (default: 90)

    Use --dry-run to preview what would be deleted.
    """
    import json as json_module

    manager = DataManager()

    if all_projects:
        results = manager.cleanup(
            project_id=None,
            sessions_days=sessions,
            logs_days=logs,
            approvals_days=approvals,
            dry_run=dry_run,
        )
        if not isinstance(results, list):
            results = [results]
        project_ids = manager.list_project_ids()
    else:
        # Get current project ID
        project_id = None
        if ctx.current_project:
            project_id = ctx.current_project.id
        else:
            project_id = manager.hash_path(ctx.project_dir)

        result = manager.cleanup(
            project_id=project_id,
            sessions_days=sessions,
            logs_days=logs,
            approvals_days=approvals,
            dry_run=dry_run,
        )
        results = [result] if isinstance(result, CleanupResult) else []
        project_ids = [project_id]

    if as_json:
        output = []
        for pid, r in zip(project_ids, results):
            d = r.to_dict()
            d["project_id"] = pid
            output.append(d)
        console.print(json_module.dumps(output, indent=2))
        return

    # Display results
    action = "Would remove" if dry_run else "Removed"
    if dry_run:
        console.print("[yellow]Dry run - no data will be deleted[/yellow]\n")

    title = f"Cleanup Results (sessions: {sessions}d, logs: {logs}d, approvals: {approvals}d)"
    table = Table(title=title)
    table.add_column("Project ID", style="cyan")
    table.add_column("Sessions", justify="right")
    table.add_column("Log Entries", justify="right")
    table.add_column("Approvals", justify="right")
    table.add_column("Space Freed", justify="right", style="green")

    total_removed = 0
    total_bytes = 0
    for pid, result in zip(project_ids, results):
        table.add_row(
            pid,
            str(result.sessions_removed),
            str(result.logs_removed),
            str(result.approvals_removed),
            f"{result.bytes_freed_mb:.2f} MB",
        )
        total_removed += result.total_removed
        total_bytes += result.bytes_freed

    if len(results) > 1:
        table.add_section()
        table.add_row(
            "[bold]Total[/bold]",
            "",
            "",
            f"[bold]{total_removed}[/bold]",
            f"[bold]{total_bytes / (1024 * 1024):.2f} MB[/bold]",
        )

    console.print(table)

    if total_removed == 0:
        console.print("\n[green]No old data to clean up![/green]")
    elif not dry_run:
        freed_mb = total_bytes / (1024 * 1024)
        console.print(f"\n[green]{action} {total_removed} items, freed {freed_mb:.2f} MB[/green]")


@data.command("purge")
@click.argument("project_id", required=False)
@click.option(
    "--yes",
    is_flag=True,
    help="Skip confirmation prompt",
)
@pass_context
def data_purge(ctx: Context, project_id: str | None, yes: bool) -> None:
    """Delete all data for a project.

    If PROJECT_ID is not provided, uses the current project.

    WARNING: This permanently deletes all logs, sessions, and approvals!
    """
    manager = DataManager()

    # Resolve project ID
    if not project_id:
        if ctx.current_project:
            project_id = ctx.current_project.id
        else:
            project_id = manager.hash_path(ctx.project_dir)

    # Check if data exists
    project_dir = manager.get_project_data_dir(project_id)
    if not project_dir.exists():
        console.print(f"[yellow]No data found for project: {project_id}[/yellow]")
        return

    # Get stats before purge
    stats = manager.get_stats(project_id)
    if isinstance(stats, list):
        stats = stats[0] if stats else None

    if stats:
        console.print(f"\n[bold]Data to be deleted for project: {project_id}[/bold]")
        console.print(f"  Logs: {stats.logs_count} files")
        console.print(f"  Sessions: {stats.sessions_count} files")
        console.print(f"  Approvals: {stats.approvals_count} entries")
        console.print(f"  Total size: {stats.total_size_mb:.2f} MB")
        console.print()

    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete ALL data for project '{project_id}'?"
        ):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    # Perform purge
    if manager.purge(project_id):
        console.print(f"[green]Purged all data for project: {project_id}[/green]")
    else:
        console.print(f"[yellow]No data found for project: {project_id}[/yellow]")


@data.command("migrate")
@click.option(
    "--remove-old",
    is_flag=True,
    help="Remove old data after migration",
)
@click.option(
    "--all-projects",
    is_flag=True,
    help="Migrate all registered projects",
)
@pass_context
def data_migrate(ctx: Context, remove_old: bool, all_projects: bool) -> None:
    """Migrate data from project-local to global storage.

    Moves data from {project}/data/ to ~/.codegeass/data/{project-id}/

    Use --remove-old to delete the old project-local data after migration.
    """
    manager = DataManager()

    if all_projects:
        # Migrate all registered projects
        projects = ctx.project_repo.find_all()
        if not projects:
            console.print("[yellow]No registered projects found.[/yellow]")
            return

        migrated = 0
        for project in projects:
            if manager.migrate_project_data(project.path, project.id, remove_old):
                console.print(f"[green]Migrated: {project.name} ({project.id})[/green]")
                migrated += 1
            else:
                console.print(f"[dim]No local data: {project.name}[/dim]")

        console.print(f"\n[green]Migrated {migrated} project(s)[/green]")
    else:
        # Migrate current project
        if ctx.current_project:
            project_id = ctx.current_project.id
            project_path = ctx.current_project.path
        else:
            project_id = manager.hash_path(ctx.project_dir)
            project_path = ctx.project_dir

        if manager.migrate_project_data(project_path, project_id, remove_old):
            console.print(f"[green]Migrated data to ~/.codegeass/data/{project_id}/[/green]")
            if remove_old:
                console.print("[dim]Old data removed from project directory[/dim]")
        else:
            console.print("[yellow]No local data to migrate.[/yellow]")


@data.command("location")
@pass_context
def data_location(ctx: Context) -> None:
    """Show where data is stored for the current project."""
    manager = DataManager()

    if ctx.current_project:
        project_id = ctx.current_project.id
        project_name = ctx.current_project.name
    else:
        project_id = manager.hash_path(ctx.project_dir)
        project_name = "(unregistered)"

    data_dir = manager.get_project_data_dir(project_id)

    console.print("\n[bold]Data Location[/bold]")
    console.print(f"  Project: {project_name}")
    console.print(f"  Project ID: {project_id}")
    console.print(f"  Data directory: {data_dir}")
    console.print(f"  Logs: {data_dir / 'logs'}")
    console.print(f"  Sessions: {data_dir / 'sessions'}")
    console.print(f"  Approvals: {data_dir / 'approvals.yaml'}")

    if data_dir.exists():
        stats = manager.get_stats(project_id)
        if isinstance(stats, DataStats):
            console.print(f"\n  [dim]Total size: {stats.total_size_mb:.2f} MB[/dim]")
    else:
        console.print("\n  [yellow]Data directory does not exist yet[/yellow]")
