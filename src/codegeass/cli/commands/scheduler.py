"""Scheduler CLI commands."""

import asyncio
import signal
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context

console = Console()


@click.group()
def scheduler() -> None:
    """Manage the task scheduler."""
    pass


@scheduler.command("status")
@pass_context
def scheduler_status(ctx: Context) -> None:
    """Show scheduler status."""
    status = ctx.scheduler.status()

    details = f"""[bold]Current Time:[/bold] {status["current_time"][:19]}

[bold]Tasks:[/bold]
  Enabled: {status["enabled_tasks"]}
  Disabled: {status["disabled_tasks"]}

[bold]Due Now:[/bold] {", ".join(status["due_tasks"]) or "none"}"""

    console.print(Panel(details, title="Scheduler Status"))

    # Show next runs
    if status["next_runs"]:
        console.print("\n[bold]Next Scheduled Runs:[/bold]")
        table = Table()
        table.add_column("Task")
        table.add_column("Next Run")

        for task_name, next_run in sorted(status["next_runs"].items(), key=lambda x: x[1]):
            table.add_row(task_name, next_run[:19])

        console.print(table)


@scheduler.command("run")
@click.option("--force", "-f", is_flag=True, help="Run all enabled tasks regardless of schedule")
@click.option("--dry-run", is_flag=True, help="Show what would run without executing")
@click.option(
    "--window", "-w", default=60, help="Time window in seconds for due tasks (default: 60)"
)
@pass_context
def run_scheduler(ctx: Context, force: bool, dry_run: bool, window: int) -> None:
    """Run due tasks (or all tasks with --force)."""
    if force:
        tasks = ctx.task_repo.find_enabled()
        console.print(f"[bold]Running all {len(tasks)} enabled task(s)...[/bold]")
    else:
        tasks = ctx.scheduler.find_due_tasks(window)
        if not tasks:
            console.print("[yellow]No tasks due for execution.[/yellow]")
            return
        console.print(f"[bold]Running {len(tasks)} due task(s)...[/bold]")

    results = []
    for task in tasks:
        console.print(f"\n[cyan]Running: {task.name}[/cyan]")
        result = ctx.scheduler.run_task(task, dry_run=dry_run)
        results.append(result)

        if result.is_success:
            console.print(f"  [green]✓ Success[/green] ({result.duration_seconds:.1f}s)")
        else:
            console.print(f"  [red]✗ {result.status.value}[/red]")
            if result.error:
                console.print(f"    Error: {result.error[:100]}")

    # Summary
    success_count = sum(1 for r in results if r.is_success)
    console.print(f"\n[bold]Summary:[/bold] {success_count}/{len(results)} succeeded")


@scheduler.command("upcoming")
@click.option("--hours", "-h", default=24, help="Hours to look ahead (default: 24)")
@pass_context
def upcoming_tasks(ctx: Context, hours: int) -> None:
    """Show tasks scheduled to run soon."""
    upcoming = ctx.scheduler.get_upcoming(hours)

    if not upcoming:
        console.print(f"[yellow]No tasks scheduled in the next {hours} hour(s).[/yellow]")
        return

    table = Table(title=f"Upcoming Tasks (next {hours}h)")
    table.add_column("Time", style="green")
    table.add_column("Task")
    table.add_column("Schedule")

    for item in upcoming:
        scheduled_at = item["scheduled_at"][:16].replace("T", " ")
        table.add_row(
            scheduled_at,
            item["task_name"],
            item["schedule_desc"],
        )

    console.print(table)


@scheduler.command("due")
@click.option("--window", "-w", default=60, help="Time window in seconds (default: 60)")
@pass_context
def due_tasks(ctx: Context, window: int) -> None:
    """Show tasks that are currently due for execution."""
    tasks = ctx.scheduler.find_due_tasks(window)

    if not tasks:
        console.print(f"[yellow]No tasks due within {window} second window.[/yellow]")
        return

    table = Table(title=f"Due Tasks (window: {window}s)")
    table.add_column("Name", style="cyan")
    table.add_column("Schedule")
    table.add_column("Last Run")

    from codegeass.scheduling.cron_parser import CronParser

    for t in tasks:
        last_run = t.last_run[:16] if t.last_run else "never"
        table.add_row(
            t.name,
            f"{t.schedule} ({CronParser.describe(t.schedule)})",
            last_run,
        )

    console.print(table)
    console.print(f"\n[bold]{len(tasks)} task(s) due.[/bold] Run with: codegeass scheduler run")


@scheduler.command("install-cron")
@click.option("--script", type=click.Path(path_type=Path), help="Path to cron-runner.sh")
@pass_context
def install_cron(ctx: Context, script: Path | None) -> None:
    """Install crontab entry for scheduler."""
    runner_script = script or ctx.project_dir / "scripts" / "cron-runner.sh"

    if not runner_script.exists():
        console.print(f"[red]Runner script not found: {runner_script}[/red]")
        console.print("Create it first or specify path with --script")
        raise SystemExit(1)

    # Make executable
    import os

    os.chmod(runner_script, 0o755)

    entry = ctx.scheduler.generate_crontab_entry(runner_script)
    console.print("[bold]Crontab entry:[/bold]")
    console.print(f"  {entry}")

    if click.confirm("\nInstall this entry to crontab?"):
        success = ctx.scheduler.install_crontab(runner_script)
        if success:
            console.print("[green]Crontab entry installed successfully[/green]")
        else:
            console.print("[red]Failed to install crontab entry[/red]")
    else:
        console.print("\nTo install manually, run:")
        console.print(f"  (crontab -l 2>/dev/null; echo '{entry}') | crontab -")


@scheduler.command("show-cron")
@pass_context
def show_cron(ctx: Context) -> None:
    """Show current crontab entries."""
    import subprocess

    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0:
            if result.stdout.strip():
                console.print("[bold]Current crontab:[/bold]")
                console.print(result.stdout)
            else:
                console.print("[yellow]Crontab is empty[/yellow]")
        else:
            console.print("[yellow]No crontab for current user[/yellow]")
    except FileNotFoundError:
        console.print("[red]crontab command not found[/red]")


@scheduler.command("test-cron")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@pass_context
def test_cron(ctx: Context, verbose: bool) -> None:
    """Test cron environment (check ANTHROPIC_API_KEY is not set)."""
    import os

    console.print("[bold]Testing CRON environment...[/bold]")

    # Check ANTHROPIC_API_KEY
    if "ANTHROPIC_API_KEY" in os.environ:
        console.print("[red]✗ ANTHROPIC_API_KEY is set[/red]")
        console.print("  This will use API credits instead of subscription")
        console.print("  Make sure cron-runner.sh runs: unset ANTHROPIC_API_KEY")
    else:
        console.print("[green]✓ ANTHROPIC_API_KEY is not set (subscription will be used)[/green]")

    # Check claude command
    import shutil

    if shutil.which("claude"):
        console.print("[green]✓ claude command found[/green]")
    else:
        console.print("[red]✗ claude command not found in PATH[/red]")

    # Check project structure
    checks = [
        (ctx.config_dir.exists(), f"Config dir: {ctx.config_dir}"),
        (ctx.schedules_file.exists(), f"Schedules file: {ctx.schedules_file}"),
        (ctx.skills_dir.exists(), f"Skills dir: {ctx.skills_dir}"),
    ]

    for passed, description in checks:
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"{status} {description}")

    if verbose:
        console.print("\n[bold]Environment variables:[/bold]")
        for key in ["PATH", "HOME", "USER"]:
            console.print(f"  {key}={os.environ.get(key, 'not set')}")


@scheduler.command("daemon")
@click.option(
    "--poll-interval", "-p", default=1.0, help="Polling interval in seconds (default: 1.0)"
)
@pass_context
def daemon_mode(ctx: Context, poll_interval: float) -> None:
    """Run daemon that handles Telegram callbacks for plan approvals.

    This command runs continuously and polls Telegram for button clicks
    (Approve/Discuss/Cancel) on plan approval messages.

    Use Ctrl+C to stop.
    """
    from codegeass.execution.plan_service import PlanApprovalService
    from codegeass.notifications.callback_handler import (
        CallbackHandler,
        TelegramCallbackServer,
    )

    # Check prerequisites
    if ctx.channel_repo is None:
        console.print("[red]No notification channels configured.[/red]")
        console.print("Run 'codegeass notification add' first.")
        raise SystemExit(1)

    if ctx.approval_repo is None:
        console.print("[red]Could not initialize approval repository.[/red]")
        raise SystemExit(1)

    # Initialize services
    plan_service = PlanApprovalService(ctx.approval_repo, ctx.channel_repo)
    callback_handler = CallbackHandler(plan_service, ctx.channel_repo)
    callback_server = TelegramCallbackServer(
        callback_handler,
        ctx.channel_repo,
        poll_interval=poll_interval,
    )

    console.print("[bold green]CodeGeass Daemon Starting...[/bold green]")
    console.print(f"Polling interval: {poll_interval}s")
    console.print("Listening for Telegram callbacks (Approve/Discuss/Cancel)")
    console.print("Press Ctrl+C to stop.\n")

    # Handle graceful shutdown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def signal_handler(sig, frame):
        console.print("\n[yellow]Shutting down daemon...[/yellow]")
        callback_server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        loop.run_until_complete(callback_server.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Daemon stopped.[/yellow]")
    finally:
        callback_server.stop()
        loop.close()
