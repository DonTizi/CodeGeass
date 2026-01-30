"""Log viewing CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context

console = Console()


@click.group()
def logs() -> None:
    """View execution logs."""
    pass


@logs.command("list")
@click.option("--limit", "-l", default=20, help="Number of entries to show")
@click.option("--status", "-s", help="Filter by status (success, failure, timeout)")
@pass_context
def list_logs(ctx: Context, limit: int, status: str | None) -> None:
    """List recent execution logs."""
    if status:
        results = ctx.log_repo.find_by_status(status, limit=limit)
    else:
        results = ctx.log_repo.find_all(limit=limit)

    if not results:
        console.print("[yellow]No execution logs found.[/yellow]")
        return

    table = Table(title="Execution Logs")
    table.add_column("Time", style="dim")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Duration")
    table.add_column("Error")

    for r in results:
        # Color status
        if r.status.value == "success":
            status_str = "[green]success[/green]"
        elif r.status.value == "failure":
            status_str = "[red]failure[/red]"
        elif r.status.value == "timeout":
            status_str = "[yellow]timeout[/yellow]"
        else:
            status_str = r.status.value

        error = r.error[:30] + "..." if r.error and len(r.error) > 30 else (r.error or "-")

        table.add_row(
            r.started_at.strftime("%Y-%m-%d %H:%M"),
            r.task_id,
            status_str,
            f"{r.duration_seconds:.1f}s",
            error,
        )

    console.print(table)


@logs.command("show")
@click.argument("task_name")
@click.option("--limit", "-l", default=10, help="Number of entries to show")
@pass_context
def show_logs(ctx: Context, task_name: str, limit: int) -> None:
    """Show logs for a specific task."""
    # Get task ID
    task = ctx.task_repo.find_by_name(task_name)
    if not task:
        console.print(f"[red]Task not found: {task_name}[/red]")
        raise SystemExit(1)

    results = ctx.log_repo.find_by_task_id(task.id, limit=limit)

    if not results:
        console.print(f"[yellow]No logs found for task: {task_name}[/yellow]")
        return

    # Show stats first
    stats = ctx.log_repo.get_task_stats(task.id)
    stats_panel = f"""[bold]Total Runs:[/bold] {stats["total_runs"]}
[bold]Success Rate:[/bold] {stats["success_rate"]:.1f}%
[bold]Avg Duration:[/bold] {stats["avg_duration"]:.1f}s
[bold]Last Run:[/bold] {stats["last_run"][:19] if stats["last_run"] else "never"}
[bold]Last Status:[/bold] {stats["last_status"] or "-"}"""

    console.print(Panel(stats_panel, title=f"Stats: {task_name}"))

    # Show recent logs
    console.print(f"\n[bold]Recent Logs (last {limit}):[/bold]")

    for r in results:
        # Color status
        if r.status.value == "success":
            status_str = "[green]✓[/green]"
        elif r.status.value == "failure":
            status_str = "[red]✗[/red]"
        else:
            status_str = f"[yellow]{r.status.value}[/yellow]"

        console.print(
            f"{status_str} {r.started_at.strftime('%Y-%m-%d %H:%M')} ({r.duration_seconds:.1f}s)"
        )

        if r.error:
            console.print(f"    [red]Error:[/red] {r.error[:80]}")


@logs.command("tail")
@click.argument("task_name")
@click.option("--lines", "-n", default=5, help="Number of lines to show")
@click.option("--output", "-o", is_flag=True, help="Show output content")
@pass_context
def tail_logs(ctx: Context, task_name: str, lines: int, output: bool) -> None:
    """Show most recent log entries for a task."""
    task = ctx.task_repo.find_by_name(task_name)
    if not task:
        console.print(f"[red]Task not found: {task_name}[/red]")
        raise SystemExit(1)

    results = ctx.log_repo.tail(task.id, lines=lines)

    if not results:
        console.print(f"[yellow]No logs found for task: {task_name}[/yellow]")
        return

    for r in results:
        # Status color
        if r.status.value == "success":
            status_str = "[green]SUCCESS[/green]"
        elif r.status.value == "failure":
            status_str = "[red]FAILURE[/red]"
        else:
            status_str = f"[yellow]{r.status.value.upper()}[/yellow]"

        console.print(f"\n[bold]{r.started_at.strftime('%Y-%m-%d %H:%M:%S')}[/bold] {status_str}")
        console.print(f"  Duration: {r.duration_seconds:.1f}s")
        console.print(f"  Session: {r.session_id or '-'}")

        if r.error:
            console.print(f"  [red]Error:[/red] {r.error}")

        if output and r.clean_output:
            console.print("  [bold]Output:[/bold]")
            # Truncate long output
            out = r.clean_output[:500] + "..." if len(r.clean_output) > 500 else r.clean_output
            console.print(Panel(out, border_style="dim"))


@logs.command("clear")
@click.argument("task_name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def clear_logs(ctx: Context, task_name: str, yes: bool) -> None:
    """Clear logs for a specific task."""
    task = ctx.task_repo.find_by_name(task_name)
    if not task:
        console.print(f"[red]Task not found: {task_name}[/red]")
        raise SystemExit(1)

    if not yes:
        if not click.confirm(f"Clear all logs for task '{task_name}'?"):
            console.print("Cancelled")
            return

    if ctx.log_repo.clear_task_logs(task.id):
        console.print(f"[green]Logs cleared for: {task_name}[/green]")
    else:
        console.print(f"[yellow]No logs to clear for: {task_name}[/yellow]")


@logs.command("stats")
@pass_context
def stats_logs(ctx: Context) -> None:
    """Show overall execution statistics."""
    tasks = ctx.task_repo.find_all()

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    table = Table(title="Task Statistics")
    table.add_column("Task")
    table.add_column("Runs", justify="right")
    table.add_column("Success", justify="right")
    table.add_column("Failed", justify="right")
    table.add_column("Rate", justify="right")
    table.add_column("Avg Time", justify="right")

    total_runs = 0
    total_success = 0
    total_failures = 0

    for task in tasks:
        stats = ctx.log_repo.get_task_stats(task.id)

        if stats["total_runs"] == 0:
            table.add_row(task.name, "0", "-", "-", "-", "-")
            continue

        total_runs += stats["total_runs"]
        total_success += stats["success_count"]
        total_failures += stats["failure_count"]

        rate_color = (
            "green"
            if stats["success_rate"] >= 90
            else "yellow"
            if stats["success_rate"] >= 70
            else "red"
        )

        table.add_row(
            task.name,
            str(stats["total_runs"]),
            str(stats["success_count"]),
            str(stats["failure_count"]),
            f"[{rate_color}]{stats['success_rate']:.0f}%[/{rate_color}]",
            f"{stats['avg_duration']:.1f}s",
        )

    console.print(table)

    # Overall summary
    if total_runs > 0:
        overall_rate = total_success / total_runs * 100
        console.print(
            f"\n[bold]Overall:[/bold] {total_runs} runs, {overall_rate:.0f}% success rate"
        )
