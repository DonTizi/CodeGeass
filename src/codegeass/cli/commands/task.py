"""Task management CLI commands."""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context
from codegeass.core.entities import Task
from codegeass.scheduling.cron_parser import CronParser

console = Console()


@click.group()
def task() -> None:
    """Manage scheduled tasks."""
    pass


@task.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all tasks including disabled")
@pass_context
def list_tasks(ctx: Context, show_all: bool) -> None:
    """List all scheduled tasks."""
    tasks = ctx.task_repo.find_all()

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        console.print("Create a task with: codegeass task create")
        return

    if not show_all:
        tasks = [t for t in tasks if t.enabled]

    table = Table(title="Scheduled Tasks")
    table.add_column("Name", style="cyan")
    table.add_column("Schedule", style="green")
    table.add_column("Description")
    table.add_column("Status")
    table.add_column("Last Run")

    for t in tasks:
        status = "[green]enabled[/green]" if t.enabled else "[red]disabled[/red]"
        schedule_desc = CronParser.describe(t.schedule)
        last_run = t.last_run[:16] if t.last_run else "-"
        last_status = t.last_status or "-"

        skill_or_prompt = t.skill or (t.prompt[:30] + "..." if t.prompt and len(t.prompt) > 30 else t.prompt or "-")

        table.add_row(
            t.name,
            f"{t.schedule}\n({schedule_desc})",
            skill_or_prompt,
            status,
            f"{last_run}\n{last_status}",
        )

    console.print(table)


@task.command("show")
@click.argument("name")
@pass_context
def show_task(ctx: Context, name: str) -> None:
    """Show details of a specific task."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    # Build details panel
    details = f"""[bold]ID:[/bold] {t.id}
[bold]Name:[/bold] {t.name}
[bold]Schedule:[/bold] {t.schedule} ({CronParser.describe(t.schedule)})
[bold]Working Dir:[/bold] {t.working_dir}
[bold]Skill:[/bold] {t.skill or '-'}
[bold]Prompt:[/bold] {t.prompt or '-'}
[bold]Model:[/bold] {t.model}
[bold]Autonomous:[/bold] {t.autonomous}
[bold]Timeout:[/bold] {t.timeout}s
[bold]Max Turns:[/bold] {t.max_turns or 'unlimited'}
[bold]Enabled:[/bold] {t.enabled}
[bold]Last Run:[/bold] {t.last_run or 'never'}
[bold]Last Status:[/bold] {t.last_status or '-'}"""

    if t.allowed_tools:
        details += f"\n[bold]Allowed Tools:[/bold] {', '.join(t.allowed_tools)}"

    if t.variables:
        details += f"\n[bold]Variables:[/bold] {t.variables}"

    if t.notifications:
        notif = t.notifications
        channels = ", ".join(notif.get("channels", []))
        events = ", ".join(notif.get("events", []))
        details += f"\n[bold]Notifications:[/bold]"
        details += f"\n  Channels: {channels or 'none'}"
        details += f"\n  Events: {events or 'none'}"
        if notif.get("include_output"):
            details += "\n  Include output: yes"

    # Show next scheduled runs
    next_runs = CronParser.get_next_n(t.schedule, 3)
    next_runs_str = "\n".join([f"  - {r.strftime('%Y-%m-%d %H:%M')}" for r in next_runs])
    details += f"\n\n[bold]Next Runs:[/bold]\n{next_runs_str}"

    console.print(Panel(details, title=f"Task: {t.name}"))


@task.command("create")
@click.option("--name", "-n", required=True, help="Task name")
@click.option("--schedule", "-s", required=True, help="CRON expression (e.g., '0 9 * * 1-5')")
@click.option("--working-dir", "-w", required=True, type=click.Path(path_type=Path), help="Working directory")
@click.option("--skill", "-k", help="Skill to invoke")
@click.option("--prompt", "-p", help="Direct prompt (if no skill)")
@click.option("--model", "-m", default="sonnet", help="Model (haiku, sonnet, opus)")
@click.option("--autonomous", is_flag=True, help="Enable autonomous mode")
@click.option("--timeout", "-t", default=300, help="Timeout in seconds")
@click.option("--max-turns", type=int, help="Max agentic turns")
@click.option("--tools", help="Comma-separated list of allowed tools")
@click.option("--disabled", is_flag=True, help="Create task as disabled")
@click.option("--notify", multiple=True, help="Channel IDs to notify (can specify multiple)")
@click.option(
    "--notify-on",
    multiple=True,
    type=click.Choice(["start", "complete", "success", "failure"]),
    help="Events to notify on (can specify multiple)",
)
@click.option("--notify-include-output", is_flag=True, help="Include task output in notifications")
@pass_context
def create_task(
    ctx: Context,
    name: str,
    schedule: str,
    working_dir: Path,
    skill: str | None,
    prompt: str | None,
    model: str,
    autonomous: bool,
    timeout: int,
    max_turns: int | None,
    tools: str | None,
    disabled: bool,
    notify: tuple[str, ...],
    notify_on: tuple[str, ...],
    notify_include_output: bool,
) -> None:
    """Create a new scheduled task."""
    # Validate inputs
    if not skill and not prompt:
        console.print("[red]Error: Either --skill or --prompt is required[/red]")
        raise SystemExit(1)

    if not CronParser.validate(schedule):
        console.print(f"[red]Error: Invalid CRON expression: {schedule}[/red]")
        raise SystemExit(1)

    working_dir = working_dir.resolve()
    if not working_dir.exists():
        console.print(f"[red]Error: Working directory does not exist: {working_dir}[/red]")
        raise SystemExit(1)

    # Check for duplicate name
    existing = ctx.task_repo.find_by_name(name)
    if existing:
        console.print(f"[red]Error: Task with name '{name}' already exists[/red]")
        raise SystemExit(1)

    # Validate skill exists if specified
    if skill:
        if not ctx.skill_registry.exists(skill):
            console.print(f"[yellow]Warning: Skill '{skill}' not found in registry[/yellow]")
            console.print("Available skills:", ", ".join(s.name for s in ctx.skill_registry.get_all()) or "none")

    # Parse tools
    allowed_tools = [t.strip() for t in tools.split(",")] if tools else []

    # Build notification config if specified
    notifications = None
    if notify:
        events = [f"task_{e}" for e in notify_on] if notify_on else ["task_failure"]
        notifications = {
            "channels": list(notify),
            "events": events,
            "include_output": notify_include_output,
        }

    # Create task
    new_task = Task.create(
        name=name,
        schedule=schedule,
        working_dir=working_dir,
        skill=skill,
        prompt=prompt,
        model=model,
        autonomous=autonomous,
        timeout=timeout,
        max_turns=max_turns,
        allowed_tools=allowed_tools,
        enabled=not disabled,
        notifications=notifications,
    )

    ctx.task_repo.save(new_task)

    console.print(f"[green]Task created: {name}[/green]")
    console.print(f"ID: {new_task.id}")
    console.print(f"Schedule: {schedule} ({CronParser.describe(schedule)})")
    console.print(f"Next run: {CronParser.get_next(schedule).strftime('%Y-%m-%d %H:%M')}")


@task.command("run")
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
        console.print(f"[yellow]Dry run - would execute:[/yellow]")
        console.print(" ".join(command))
        return

    result = ctx.scheduler.run_task(t)

    if result.is_success:
        console.print(f"[green]Task completed successfully[/green]")
        console.print(f"Duration: {result.duration_seconds:.1f}s")
    else:
        console.print(f"[red]Task failed: {result.status.value}[/red]")
        if result.error:
            console.print(f"Error: {result.error}")

    if result.output:
        console.print("\n[bold]Output:[/bold]")
        console.print(result.output[:2000])


@task.command("enable")
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


@task.command("disable")
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


@task.command("delete")
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
