"""Tag management commands for tasks."""

import click
from rich.console import Console
from rich.table import Table

from codegeass.cli.main import Context, pass_context

console = Console()


@click.group("tag")
def tag() -> None:
    """Manage task tags."""


@tag.command("list")
@pass_context
def list_tags(ctx: Context) -> None:
    """List all tags used across tasks."""
    tasks = ctx.task_repo.find_all()

    # Collect all unique tags with their counts
    tag_counts: dict[str, int] = {}
    for task in tasks:
        for t in task.tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    if not tag_counts:
        console.print("[yellow]No tags found.[/yellow]")
        console.print("Add tags with: codegeass task tag add <task-name> <tag>")
        return

    table = Table(title="Tags")
    table.add_column("Tag", style="magenta")
    table.add_column("Count", style="cyan", justify="right")

    for t, count in sorted(tag_counts.items()):
        table.add_row(t, str(count))

    console.print(table)


@tag.command("show")
@click.argument("task_name")
@pass_context
def show_tags(ctx: Context, task_name: str) -> None:
    """Show tags for a specific task."""
    task = ctx.task_repo.find_by_name(task_name)

    if not task:
        console.print(f"[red]Task not found: {task_name}[/red]")
        raise SystemExit(1)

    if not task.tags:
        console.print(f"[yellow]Task '{task_name}' has no tags.[/yellow]")
        return

    console.print(f"[bold]Tags for '{task_name}':[/bold]")
    for t in task.tags:
        console.print(f"  • [magenta]{t}[/magenta]")


@tag.command("add")
@click.argument("task_name")
@click.argument("tags", nargs=-1, required=True)
@pass_context
def add_tags(ctx: Context, task_name: str, tags: tuple[str, ...]) -> None:
    """Add tags to a task.

    Examples:
        codegeass task tag add my-task deploy production
        codegeass task tag add backup-task urgent
    """
    task = ctx.task_repo.find_by_name(task_name)

    if not task:
        console.print(f"[red]Task not found: {task_name}[/red]")
        raise SystemExit(1)

    # Add new tags (avoid duplicates)
    existing = set(task.tags)
    added = []
    for t in tags:
        if t not in existing:
            task.tags.append(t)
            added.append(t)

    if added:
        ctx.task_repo.update(task)
        console.print(f"[green]Added tags to '{task_name}':[/green]")
        for t in added:
            console.print(f"  • [magenta]{t}[/magenta]")
    else:
        console.print(f"[yellow]All tags already exist on '{task_name}'.[/yellow]")


@tag.command("remove")
@click.argument("task_name")
@click.argument("tags", nargs=-1, required=True)
@pass_context
def remove_tags(ctx: Context, task_name: str, tags: tuple[str, ...]) -> None:
    """Remove tags from a task.

    Examples:
        codegeass task tag remove my-task production
        codegeass task tag remove backup-task urgent deprecated
    """
    task = ctx.task_repo.find_by_name(task_name)

    if not task:
        console.print(f"[red]Task not found: {task_name}[/red]")
        raise SystemExit(1)

    removed = []
    for t in tags:
        if t in task.tags:
            task.tags.remove(t)
            removed.append(t)

    if removed:
        ctx.task_repo.update(task)
        console.print(f"[green]Removed tags from '{task_name}':[/green]")
        for t in removed:
            console.print(f"  • [magenta]{t}[/magenta]")
    else:
        console.print(f"[yellow]None of the specified tags exist on '{task_name}'.[/yellow]")


@tag.command("clear")
@click.argument("task_name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def clear_tags(ctx: Context, task_name: str, yes: bool) -> None:
    """Remove all tags from a task."""
    task = ctx.task_repo.find_by_name(task_name)

    if not task:
        console.print(f"[red]Task not found: {task_name}[/red]")
        raise SystemExit(1)

    if not task.tags:
        console.print(f"[yellow]Task '{task_name}' has no tags.[/yellow]")
        return

    if not yes:
        console.print(f"[yellow]This will remove {len(task.tags)} tag(s) from '{task_name}'.")
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    removed_count = len(task.tags)
    task.tags = []
    ctx.task_repo.update(task)
    console.print(f"[green]Removed {removed_count} tag(s) from '{task_name}'.[/green]")
