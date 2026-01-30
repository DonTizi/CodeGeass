"""CRON expression utilities CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.scheduling.cron_parser import CronParser

console = Console()


@click.group()
def cron() -> None:
    """CRON expression utilities."""
    pass


@cron.command("validate")
@click.argument("expression")
def validate_cron(expression: str) -> None:
    """Validate a CRON expression.

    Examples:
        codegeass cron validate "0 9 * * *"
        codegeass cron validate "@daily"
        codegeass cron validate "*/15 * * * *"
    """
    # Normalize the expression
    normalized = CronParser.normalize(expression)

    if CronParser.validate(expression):
        console.print("[green]✓ Valid CRON expression[/green]")
        console.print(f"\n[bold]Expression:[/bold] {expression}")
        if normalized != expression:
            console.print(f"[bold]Normalized:[/bold] {normalized}")
        console.print(f"[bold]Description:[/bold] {CronParser.describe(expression)}")
    else:
        console.print(f"[red]✗ Invalid CRON expression: {expression}[/red]")
        console.print("\n[dim]CRON format: minute hour day-of-month month day-of-week[/dim]")
        console.print("[dim]Example: 0 9 * * 1-5 (weekdays at 9am)[/dim]")
        raise SystemExit(1)


@cron.command("describe")
@click.argument("expression")
def describe_cron(expression: str) -> None:
    """Get human-readable description of a CRON expression.

    Examples:
        codegeass cron describe "0 9 * * 1-5"
        codegeass cron describe "@hourly"
    """
    if not CronParser.validate(expression):
        console.print(f"[red]Invalid CRON expression: {expression}[/red]")
        raise SystemExit(1)

    normalized = CronParser.normalize(expression)
    description = CronParser.describe(expression)

    console.print(f"[bold]Expression:[/bold] {expression}")
    if normalized != expression:
        console.print(f"[bold]Normalized:[/bold] {normalized}")
    console.print(f"[bold]Description:[/bold] {description}")

    # Break down the parts
    parts = normalized.split()
    if len(parts) == 5:
        console.print("\n[bold]Components:[/bold]")
        labels = ["Minute", "Hour", "Day of Month", "Month", "Day of Week"]
        for label, part in zip(labels, parts):
            console.print(f"  {label}: [cyan]{part}[/cyan]")


@cron.command("next")
@click.argument("expression")
@click.option("--count", "-n", default=5, help="Number of upcoming runs to show")
def next_runs(expression: str, count: int) -> None:
    """Show next N scheduled run times for a CRON expression.

    Examples:
        codegeass cron next "0 9 * * *"
        codegeass cron next "*/15 * * * *" --count 10
    """
    if not CronParser.validate(expression):
        console.print(f"[red]Invalid CRON expression: {expression}[/red]")
        raise SystemExit(1)

    console.print(f"[bold]Expression:[/bold] {expression}")
    console.print(f"[bold]Description:[/bold] {CronParser.describe(expression)}")
    console.print(f"\n[bold]Next {count} runs:[/bold]")

    next_times = CronParser.get_next_n(expression, count)

    table = Table(show_header=True)
    table.add_column("#", style="dim")
    table.add_column("Date")
    table.add_column("Time")
    table.add_column("Day")

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i, dt in enumerate(next_times, 1):
        table.add_row(
            str(i),
            dt.strftime("%Y-%m-%d"),
            dt.strftime("%H:%M:%S"),
            day_names[dt.weekday()],
        )

    console.print(table)


@cron.command("check")
@click.argument("expression")
@click.option("--window", "-w", default=60, help="Time window in seconds")
def check_due(expression: str, window: int) -> None:
    """Check if a CRON expression is due within a time window.

    Examples:
        codegeass cron check "0 9 * * *"
        codegeass cron check "*/5 * * * *" --window 300
    """
    if not CronParser.validate(expression):
        console.print(f"[red]Invalid CRON expression: {expression}[/red]")
        raise SystemExit(1)

    is_due = CronParser.is_due(expression, window)
    prev_run = CronParser.get_prev(expression)
    next_run = CronParser.get_next(expression)

    from datetime import datetime

    now = datetime.now()
    seconds_since = (now - prev_run).total_seconds()

    console.print(f"[bold]Expression:[/bold] {expression}")
    console.print(f"[bold]Description:[/bold] {CronParser.describe(expression)}")
    console.print(f"\n[bold]Current time:[/bold] {now.strftime('%Y-%m-%d %H:%M:%S')}")
    prev_str = prev_run.strftime('%Y-%m-%d %H:%M:%S')
    next_str = next_run.strftime('%Y-%m-%d %H:%M:%S')
    console.print(f"[bold]Last scheduled:[/bold] {prev_str} ({seconds_since:.0f}s ago)")
    console.print(f"[bold]Next scheduled:[/bold] {next_str}")
    console.print(f"\n[bold]Window:[/bold] {window} seconds")

    if is_due:
        console.print("[green]✓ Due for execution[/green] (last run was within window)")
    else:
        console.print(f"[yellow]○ Not due[/yellow] ({seconds_since:.0f}s ago, window={window}s)")


@cron.command("aliases")
def show_aliases() -> None:
    """Show all supported CRON aliases.

    CRON aliases are shortcuts like @daily, @hourly, etc.
    """
    table = Table(title="CRON Aliases")
    table.add_column("Alias")
    table.add_column("Expression")
    table.add_column("Description")

    for alias, expression in CronParser.PATTERNS.items():
        table.add_row(
            f"[cyan]{alias}[/cyan]",
            expression,
            CronParser.describe(expression),
        )

    console.print(table)


@cron.command("help")
def cron_help() -> None:
    """Show CRON expression format help."""
    help_text = """[bold]CRON Expression Format[/bold]

A CRON expression consists of 5 fields:

  ┌───────── minute (0-59)
  │ ┌─────── hour (0-23)
  │ │ ┌───── day of month (1-31)
  │ │ │ ┌─── month (1-12)
  │ │ │ │ ┌─ day of week (0-6, 0=Sunday)
  │ │ │ │ │
  * * * * *

[bold]Special Characters:[/bold]
  *       Any value
  ,       Value list separator (e.g., 1,3,5)
  -       Range of values (e.g., 1-5)
  /       Step values (e.g., */15)

[bold]Common Examples:[/bold]
  0 9 * * *       Daily at 9:00 AM
  0 9 * * 1-5     Weekdays at 9:00 AM
  */15 * * * *    Every 15 minutes
  0 */2 * * *     Every 2 hours
  0 0 1 * *       First day of month at midnight
  30 4 * * 0      Sundays at 4:30 AM

[bold]Aliases:[/bold]
  @yearly, @annually    Once a year (Jan 1st)
  @monthly              Once a month (1st at midnight)
  @weekly               Once a week (Sunday at midnight)
  @daily, @midnight     Once a day (at midnight)
  @hourly               Once an hour (at minute 0)

Use 'codegeass cron aliases' to see all aliases."""

    console.print(Panel(help_text, title="CRON Help", border_style="blue"))
