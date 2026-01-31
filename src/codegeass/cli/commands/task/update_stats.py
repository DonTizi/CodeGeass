"""Task update and stats commands."""

import click
from rich.console import Console
from rich.panel import Panel

from codegeass.cli.main import Context, pass_context
from codegeass.scheduling.cron_parser import CronParser

console = Console()


@click.command("update")
@click.argument("name")
@click.option("--schedule", "-s", help="New CRON expression")
@click.option("--prompt", "-p", help="New prompt")
@click.option("--skill", "-k", help="New skill")
@click.option("--model", "-m", help="New model (haiku, sonnet, opus)")
@click.option("--timeout", "-t", type=int, help="New timeout in seconds")
@click.option("--max-turns", type=int, help="New max agentic turns")
@click.option("--autonomous/--no-autonomous", default=None, help="Enable/disable autonomous mode")
@click.option("--plan-mode/--no-plan-mode", default=None, help="Enable/disable plan mode")
@click.option("--plan-timeout", type=int, help="Plan approval timeout in seconds")
@click.option("--plan-max-iterations", type=int, help="Max discuss iterations")
@click.option("--code-source", "-cs", help="Code execution provider (claude, codex)")
@pass_context
def update_task(
    ctx: Context,
    name: str,
    schedule: str | None,
    prompt: str | None,
    skill: str | None,
    model: str | None,
    timeout: int | None,
    max_turns: int | None,
    autonomous: bool | None,
    plan_mode: bool | None,
    plan_timeout: int | None,
    plan_max_iterations: int | None,
    code_source: str | None,
) -> None:
    """Update an existing task."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    if schedule:
        if not CronParser.validate(schedule):
            console.print(f"[red]Error: Invalid CRON expression: {schedule}[/red]")
            raise SystemExit(1)
        t.schedule = schedule

    _update_basic_fields(t, prompt, skill, model, timeout, max_turns, autonomous)
    _update_plan_mode_fields(t, plan_mode, plan_timeout, plan_max_iterations)
    _update_code_source(t, code_source)
    _validate_final_plan_mode(t)

    ctx.task_repo.update(t)
    console.print(f"[green]Task updated: {name}[/green]")


def _update_basic_fields(
    t, prompt, skill, model, timeout, max_turns, autonomous
) -> None:
    """Update basic task fields."""
    if prompt is not None:
        t.prompt = prompt
    if skill is not None:
        t.skill = skill
    if model is not None:
        t.model = model
    if timeout is not None:
        t.timeout = timeout
    if max_turns is not None:
        t.max_turns = max_turns
    if autonomous is not None:
        t.autonomous = autonomous


def _update_plan_mode_fields(
    t, plan_mode, plan_timeout, plan_max_iterations
) -> None:
    """Update plan mode related fields."""
    if plan_mode is not None:
        t.plan_mode = plan_mode
    if plan_timeout is not None:
        t.plan_timeout = plan_timeout
    if plan_max_iterations is not None:
        t.plan_max_iterations = plan_max_iterations


def _update_code_source(t, code_source: str | None) -> None:
    """Update code source with validation."""
    if code_source is None:
        return

    from codegeass.providers import ProviderNotFoundError, get_provider_registry

    registry = get_provider_registry()
    try:
        provider = registry.get(code_source)
        capabilities = provider.get_capabilities()

        if t.plan_mode and not capabilities.plan_mode:
            console.print(
                f"[yellow]Warning: Provider '{code_source}' doesn't support plan mode. "
                f"Disabling plan mode.[/yellow]"
            )
            t.plan_mode = False

        t.code_source = code_source
    except ProviderNotFoundError:
        console.print(f"[red]Error: Unknown provider: {code_source}[/red]")
        console.print(f"Available providers: {', '.join(registry.list_providers())}")
        raise SystemExit(1)


def _validate_final_plan_mode(t) -> None:
    """Final validation of plan mode compatibility."""
    if not t.plan_mode:
        return

    from codegeass.providers import get_provider_registry

    registry = get_provider_registry()
    provider = registry.get(t.code_source)
    if not provider.get_capabilities().plan_mode:
        console.print(
            f"[red]Error: Provider '{t.code_source}' does not support plan mode[/red]"
        )
        raise SystemExit(1)


@click.command("stats")
@click.argument("name")
@pass_context
def stats_task(ctx: Context, name: str) -> None:
    """Show execution statistics for a task."""
    t = ctx.task_repo.find_by_name(name)

    if not t:
        console.print(f"[red]Task not found: {name}[/red]")
        raise SystemExit(1)

    stats = ctx.log_repo.get_task_stats(t.id)

    if stats["total_runs"] == 0:
        console.print(f"[yellow]No execution history for task: {name}[/yellow]")
        return

    rate_color = (
        "green"
        if stats["success_rate"] >= 90
        else "yellow"
        if stats["success_rate"] >= 70
        else "red"
    )

    details = f"""[bold]Task:[/bold] {name}
[bold]Total Runs:[/bold] {stats["total_runs"]}
[bold]Successful:[/bold] {stats["success_count"]}
[bold]Failed:[/bold] {stats["failure_count"]}
[bold]Timeouts:[/bold] {stats.get("timeout_count", 0)}
[bold]Success Rate:[/bold] [{rate_color}]{stats["success_rate"]:.1f}%[/{rate_color}]
[bold]Avg Duration:[/bold] {stats["avg_duration"]:.1f}s
[bold]Last Run:[/bold] {stats["last_run"][:19] if stats["last_run"] else "never"}
[bold]Last Status:[/bold] {stats["last_status"] or "-"}"""

    console.print(Panel(details, title=f"Statistics: {name}"))
