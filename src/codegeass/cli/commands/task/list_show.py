"""Task list and show commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context
from codegeass.factory.filter_service import FilterService, TaskFilter
from codegeass.scheduling.cron_parser import CronParser

console = Console()


@click.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all tasks including disabled")
@click.option("--search", "-s", help="Search in name, prompt, skill, and tags")
@click.option("--tag", "-t", "tags", multiple=True, help="Filter by tag (can specify multiple)")
@click.option("--status", type=click.Choice(["success", "failed", "never_run"]),
              help="Filter by last execution status")
@click.option("--model", "-m", type=click.Choice(["sonnet", "haiku", "opus"]),
              help="Filter by model")
@click.option("--enabled/--disabled", "enabled_filter", default=None,
              help="Filter by enabled state")
@pass_context
def list_tasks(
    ctx: Context,
    show_all: bool,
    search: str | None,
    tags: tuple[str, ...],
    status: str | None,
    model: str | None,
    enabled_filter: bool | None,
) -> None:
    """List all scheduled tasks.

    Supports filtering by search term, tags, status, model, and enabled state.
    Multiple filters are combined with AND logic.

    Examples:
        codegeass task list --search backup
        codegeass task list --tag production --enabled
        codegeass task list --model sonnet --status success
    """
    all_tasks = ctx.task_repo.find_all()

    if not all_tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        console.print("Create a task with: codegeass task create")
        return

    # Build filter criteria
    filter_criteria = TaskFilter(
        search=search,
        tags=list(tags),
        status=status,
        model=model,
    )

    # Handle enabled filter: use explicit filter if provided, otherwise use show_all logic
    if enabled_filter is not None:
        filter_criteria.enabled = enabled_filter
    elif not show_all:
        filter_criteria.enabled = True

    # Apply filters
    filter_service = FilterService()
    tasks = filter_service.filter_tasks(all_tasks, filter_criteria)

    if not tasks:
        console.print("[yellow]No tasks match the filter criteria.[/yellow]")
        return

    table = Table(title="Scheduled Tasks")
    table.add_column("Name", style="cyan")
    table.add_column("Tags", style="magenta")
    table.add_column("Schedule", style="green")
    table.add_column("Description")
    table.add_column("Model", style="blue")
    table.add_column("Status")
    table.add_column("Last Run")

    for t in tasks:
        status_str = "[green]enabled[/green]" if t.enabled else "[red]disabled[/red]"
        schedule_desc = CronParser.describe(t.schedule)
        last_run = t.last_run[:16] if t.last_run else "-"
        last_status = t.last_status or "-"
        tags_str = ", ".join(t.tags) if t.tags else "-"

        skill_or_prompt = t.skill or (
            t.prompt[:30] + "..." if t.prompt and len(t.prompt) > 30 else t.prompt or "-"
        )

        table.add_row(
            t.name,
            tags_str,
            f"{t.schedule}\n({schedule_desc})",
            skill_or_prompt,
            t.model,
            status_str,
            f"{last_run}\n{last_status}",
        )

    console.print(table)

    # Show filter summary if any filters were applied
    active_filters = []
    if search:
        active_filters.append(f"search='{search}'")
    if tags:
        active_filters.append(f"tags={list(tags)}")
    if status:
        active_filters.append(f"status={status}")
    if model:
        active_filters.append(f"model={model}")
    if enabled_filter is not None:
        active_filters.append(f"enabled={enabled_filter}")

    if active_filters:
        console.print(f"\n[dim]Filters: {', '.join(active_filters)}[/dim]")
        console.print(f"[dim]Showing {len(tasks)} of {len(all_tasks)} tasks[/dim]")


@click.command("show")
@click.argument("name")
@pass_context
def show_task(ctx: Context, name: str) -> None:
    """Show details of a specific task."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    details = _build_task_details(t)
    console.print(Panel(details, title=f"Task: {t.name}"))


def _build_task_details(t) -> str:
    """Build the details string for a task."""
    tags_str = ", ".join(t.tags) if t.tags else "-"
    details = f"""[bold]ID:[/bold] {t.id}
[bold]Name:[/bold] {t.name}
[bold]Tags:[/bold] {tags_str}
[bold]Schedule:[/bold] {t.schedule} ({CronParser.describe(t.schedule)})
[bold]Working Dir:[/bold] {t.working_dir}
[bold]Skill:[/bold] {t.skill or "-"}
[bold]Prompt:[/bold] {t.prompt or "-"}
[bold]Model:[/bold] {t.model}
[bold]Code Source:[/bold] {t.code_source}
[bold]Autonomous:[/bold] {t.autonomous}
[bold]Plan Mode:[/bold] {t.plan_mode}"""

    if t.plan_mode:
        details += f" (timeout: {t.plan_timeout}s, max iterations: {t.plan_max_iterations})"

    details += f"""
[bold]Timeout:[/bold] {t.timeout}s
[bold]Max Turns:[/bold] {t.max_turns or "unlimited"}
[bold]Enabled:[/bold] {t.enabled}
[bold]Last Run:[/bold] {t.last_run or "never"}
[bold]Last Status:[/bold] {t.last_status or "-"}"""

    if t.allowed_tools:
        details += f"\n[bold]Allowed Tools:[/bold] {', '.join(t.allowed_tools)}"

    if t.variables:
        details += f"\n[bold]Variables:[/bold] {t.variables}"

    if t.notifications:
        details += _format_notifications(t.notifications)

    next_runs = CronParser.get_next_n(t.schedule, 3)
    next_runs_str = "\n".join([f"  - {r.strftime('%Y-%m-%d %H:%M')}" for r in next_runs])
    details += f"\n\n[bold]Next Runs:[/bold]\n{next_runs_str}"

    return details


def _format_notifications(notif: dict) -> str:
    """Format notification configuration."""
    channels = ", ".join(notif.get("channels", []))
    events = ", ".join(notif.get("events", []))
    result = "\n[bold]Notifications:[/bold]"
    result += f"\n  Channels: {channels or 'none'}"
    result += f"\n  Events: {events or 'none'}"
    if notif.get("include_output"):
        result += "\n  Include output: yes"
    return result
