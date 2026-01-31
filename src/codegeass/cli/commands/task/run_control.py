"""Task run and control commands (enable, disable, delete, stop)."""

from pathlib import Path

import click
from rich.console import Console

from codegeass.cli.main import Context, pass_context

console = Console()


@click.command("run")
@click.argument("name")
@click.option("--dry-run", is_flag=True, help="Show what would be executed without running")
@pass_context
def run_task(ctx: Context, name: str, dry_run: bool) -> None:
    """Run a task manually."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    console.print(f"Running task: {name}...")

    if dry_run:
        from codegeass.execution.executor import ClaudeExecutor

        executor = ClaudeExecutor(
            skill_registry=ctx.skill_registry,
            session_manager=ctx.session_manager,
            log_repository=ctx.log_repo,
        )
        command = executor.get_command(t)
        console.print("[yellow]Dry run - would execute:[/yellow]")
        console.print(" ".join(command))
        return

    result = ctx.scheduler.run_task(t)

    if result.is_success:
        console.print("[green]Task completed successfully[/green]")
        console.print(f"Duration: {result.duration_seconds:.1f}s")
    else:
        console.print(f"[red]Task failed: {result.status.value}[/red]")
        if result.error:
            console.print(f"Error: {result.error}")

    if result.clean_output:
        console.print("\n[bold]Output:[/bold]")
        console.print(result.clean_output[:2000])


@click.command("enable")
@click.argument("name")
@pass_context
def enable_task(ctx: Context, name: str) -> None:
    """Enable a task."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    t.enabled = True
    ctx.task_repo.update(t)
    console.print(f"[green]Task enabled: {name}[/green]")


@click.command("disable")
@click.argument("name")
@pass_context
def disable_task(ctx: Context, name: str) -> None:
    """Disable a task."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    t.enabled = False
    ctx.task_repo.update(t)
    console.print(f"[yellow]Task disabled: {name}[/yellow]")


@click.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def delete_task(ctx: Context, name: str, yes: bool) -> None:
    """Delete a task."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    if not yes:
        if not click.confirm(f"Delete task '{name}'?"):
            console.print("Cancelled")
            return

    ctx.task_repo.delete_by_name(name)
    console.print(f"[red]Task deleted: {name}[/red]")


@click.command("stop")
@click.argument("name")
@pass_context
def stop_task(ctx: Context, name: str) -> None:
    """Stop a running task execution."""
    from codegeass.execution.tracker import get_execution_tracker

    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    data_dir = Path.cwd() / "data"
    tracker = get_execution_tracker(data_dir)

    execution = tracker.get_by_task(t.id)

    if not execution:
        console.print(f"[yellow]No active execution found for task: {name}[/yellow]")
        return

    console.print(f"Stopping execution {execution.execution_id} for task: {name}...")

    stopped = tracker.stop_execution(execution.execution_id)

    if stopped:
        console.print("[green]Task execution stopped successfully[/green]")
    else:
        console.print("[yellow]Could not stop execution (may have already finished)[/yellow]")
