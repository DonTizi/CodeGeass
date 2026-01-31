"""Task create command."""

from pathlib import Path

import click
from rich.console import Console

from codegeass.cli.main import Context, pass_context
from codegeass.core.entities import Task
from codegeass.scheduling.cron_parser import CronParser

console = Console()


@click.command("create")
@click.option("--name", "-n", required=True, help="Task name")
@click.option("--schedule", "-s", required=True, help="CRON expression (e.g., '0 9 * * 1-5')")
@click.option(
    "--working-dir", "-w", required=True, type=click.Path(path_type=Path), help="Working directory"
)
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
@click.option(
    "--plan-mode", is_flag=True, help="Enable plan mode (requires approval before execution)"
)
@click.option(
    "--plan-timeout",
    type=int,
    default=3600,
    help="Plan approval timeout in seconds (default: 3600)",
)
@click.option(
    "--plan-max-iterations", type=int, default=5, help="Max discuss iterations (default: 5)"
)
@click.option(
    "--code-source",
    "-cs",
    default="claude",
    help="Code execution provider (claude, codex)",
)
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
    plan_mode: bool,
    plan_timeout: int,
    plan_max_iterations: int,
    code_source: str,
) -> None:
    """Create a new scheduled task."""
    _validate_inputs(skill, prompt, schedule, code_source, plan_mode)

    working_dir = working_dir.resolve()
    if not working_dir.exists():
        console.print(f"[red]Error: Working directory does not exist: {working_dir}[/red]")
        raise SystemExit(1)

    existing = ctx.task_repo.find_by_name(name)
    if existing:
        console.print(f"[red]Error: Task with name '{name}' already exists[/red]")
        raise SystemExit(1)

    if skill and not ctx.skill_registry.exists(skill):
        console.print(f"[yellow]Warning: Skill '{skill}' not found in registry[/yellow]")
        console.print(
            "Available skills:",
            ", ".join(s.name for s in ctx.skill_registry.get_all()) or "none",
        )

    allowed_tools = [t.strip() for t in tools.split(",")] if tools else []
    notifications = _build_notifications(notify, notify_on, notify_include_output)

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
        code_source=code_source,
        enabled=not disabled,
        notifications=notifications,
        plan_mode=plan_mode,
        plan_timeout=plan_timeout,
        plan_max_iterations=plan_max_iterations,
    )

    ctx.task_repo.save(new_task)

    console.print(f"[green]Task created: {name}[/green]")
    console.print(f"ID: {new_task.id}")
    console.print(f"Schedule: {schedule} ({CronParser.describe(schedule)})")
    console.print(f"Next run: {CronParser.get_next(schedule).strftime('%Y-%m-%d %H:%M')}")
    console.print(f"Code Source: {code_source}")
    if plan_mode:
        console.print(f"[cyan]Plan Mode: timeout={plan_timeout}s, iter={plan_max_iterations}[/]")


def _validate_inputs(
    skill: str | None,
    prompt: str | None,
    schedule: str,
    code_source: str,
    plan_mode: bool,
) -> None:
    """Validate create command inputs."""
    from codegeass.providers import ProviderNotFoundError, get_provider_registry

    if not skill and not prompt:
        console.print("[red]Error: Either --skill or --prompt is required[/red]")
        raise SystemExit(1)

    if not CronParser.validate(schedule):
        console.print(f"[red]Error: Invalid CRON expression: {schedule}[/red]")
        raise SystemExit(1)

    registry = get_provider_registry()
    try:
        provider = registry.get(code_source)
        capabilities = provider.get_capabilities()

        if plan_mode and not capabilities.plan_mode:
            console.print(
                f"[red]Error: Provider '{code_source}' does not support plan mode[/red]"
            )
            console.print("Plan mode is only available with: claude")
            raise SystemExit(1)

    except ProviderNotFoundError:
        console.print(f"[red]Error: Unknown provider: {code_source}[/red]")
        console.print(f"Available providers: {', '.join(registry.list_providers())}")
        raise SystemExit(1)


def _build_notifications(
    notify: tuple[str, ...],
    notify_on: tuple[str, ...],
    include_output: bool,
) -> dict | None:
    """Build notification config from options."""
    if not notify:
        return None

    events = [f"task_{e}" for e in notify_on] if notify_on else ["task_failure"]
    return {
        "channels": list(notify),
        "events": events,
        "include_output": include_output,
    }
