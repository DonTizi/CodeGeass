"""Execution monitoring CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context

console = Console()


@click.group()
def execution() -> None:
    """Monitor active executions."""
    pass


@execution.command("list")
@pass_context
def list_executions(ctx: Context) -> None:
    """List all active executions."""
    from codegeass.execution.tracker import get_execution_tracker

    tracker = get_execution_tracker(ctx.data_dir)
    active = tracker.get_active()

    if not active:
        console.print("[yellow]No active executions.[/yellow]")
        return

    table = Table(title="Active Executions")
    table.add_column("ID", style="cyan")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Phase")
    table.add_column("Started")
    table.add_column("Duration")

    from datetime import datetime

    now = datetime.now()

    for ex in active:
        duration = (now - ex.started_at).total_seconds()

        # Color status
        status_color = {
            "starting": "yellow",
            "running": "green",
            "finishing": "blue",
        }.get(ex.status, "white")

        table.add_row(
            ex.execution_id,
            ex.task_name,
            f"[{status_color}]{ex.status}[/{status_color}]",
            ex.current_phase[:30],
            ex.started_at.strftime("%H:%M:%S"),
            f"{duration:.0f}s",
        )

    console.print(table)
    console.print(f"\n[bold]Total active:[/bold] {len(active)}")


@execution.command("show")
@click.argument("execution_id", required=False)
@click.option("--task", "-t", help="Find execution by task ID or name")
@pass_context
def show_execution(ctx: Context, execution_id: str | None, task: str | None) -> None:
    """Show details for a specific execution."""
    from codegeass.execution.tracker import get_execution_tracker

    if not execution_id and not task:
        console.print("[red]Specify either EXECUTION_ID or --task[/red]")
        raise SystemExit(1)

    tracker = get_execution_tracker(ctx.data_dir)

    if task:
        # Find by task
        execution = tracker.get_by_task(task)
        if not execution:
            # Try to find task by name
            task_obj = ctx.task_repo.find_by_name(task)
            if task_obj:
                execution = tracker.get_by_task(task_obj.id)
    else:
        execution = tracker.get_execution(execution_id)

    if not execution:
        console.print(f"[red]Execution not found: {execution_id}[/red]")
        console.print("[dim]Note: Only active executions are tracked.[/dim]")
        raise SystemExit(1)

    from datetime import datetime

    now = datetime.now()
    duration = (now - execution.started_at).total_seconds()

    # Build info panel
    status_color = {
        "starting": "yellow",
        "running": "green",
        "finishing": "blue",
    }.get(execution.status, "white")

    info = f"""[bold]Execution ID:[/bold] {execution.execution_id}
[bold]Task:[/bold] {execution.task_name} ({execution.task_id})
[bold]Session ID:[/bold] {execution.session_id or "-"}
[bold]Status:[/bold] [{status_color}]{execution.status}[/{status_color}]
[bold]Phase:[/bold] {execution.current_phase}
[bold]Started:[/bold] {execution.started_at.strftime("%Y-%m-%d %H:%M:%S")}
[bold]Duration:[/bold] {duration:.0f}s"""

    console.print(Panel(info, title=f"Execution: {execution.execution_id}"))

    # Show recent output
    if execution.output_lines:
        console.print(f"\n[bold]Recent Output ({len(execution.output_lines)} lines):[/bold]")
        # Show last 20 lines
        recent = execution.output_lines[-20:]
        for line in recent:
            # Truncate long lines
            if len(line) > 100:
                line = line[:100] + "..."
            console.print(f"  [dim]{line}[/dim]")


@execution.command("watch")
@click.argument("execution_id", required=False)
@click.option("--task", "-t", help="Watch execution for a specific task")
@pass_context
def watch_execution(ctx: Context, execution_id: str | None, task: str | None) -> None:
    """Watch an execution in real-time.

    This command shows live output from an active execution.
    Press Ctrl+C to stop watching.
    """
    import time

    from codegeass.execution.tracker import get_execution_tracker

    tracker = get_execution_tracker(ctx.data_dir)

    # Find the execution
    if execution_id:
        execution = tracker.get_execution(execution_id)
    elif task:
        # Find execution by task name
        active = tracker.get_active()
        execution = None
        for ex in active:
            if ex.task_name == task or ex.task_id == task:
                execution = ex
                break
        if not execution:
            console.print(f"[red]No active execution for task: {task}[/red]")
            raise SystemExit(1)
    else:
        # Get any active execution
        active = tracker.get_active()
        if not active:
            console.print("[yellow]No active executions to watch.[/yellow]")
            return
        execution = active[0]
        if len(active) > 1:
            console.print(
                f"[yellow]Multiple executions active. Watching: {execution.task_name}[/yellow]"
            )

    console.print(f"[bold]Watching:[/bold] {execution.task_name} ({execution.execution_id})")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    last_line_count = 0

    try:
        while True:
            # Re-fetch execution to get latest state
            execution = tracker.get_execution(execution.execution_id)

            if not execution:
                console.print("\n[green]Execution completed.[/green]")
                break

            # Print new output lines
            if len(execution.output_lines) > last_line_count:
                for line in execution.output_lines[last_line_count:]:
                    console.print(line)
                last_line_count = len(execution.output_lines)

            time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped watching.[/yellow]")


@execution.command("clear")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def clear_executions(ctx: Context, yes: bool) -> None:
    """Clear all tracked executions.

    This is useful if executions got stuck due to a crash.
    """
    from codegeass.execution.tracker import get_execution_tracker

    tracker = get_execution_tracker(ctx.data_dir)
    active = tracker.get_active()

    if not active:
        console.print("[yellow]No active executions to clear.[/yellow]")
        return

    if not yes:
        console.print(f"[bold]Active executions:[/bold] {len(active)}")
        for ex in active:
            console.print(f"  - {ex.task_name} ({ex.execution_id})")

        if not click.confirm("\nClear all tracked executions?"):
            console.print("Cancelled")
            return

    tracker.clear_all()
    console.print(f"[green]Cleared {len(active)} execution(s).[/green]")
