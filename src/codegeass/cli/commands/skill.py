"""Skill management CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from codegeass.cli.main import Context, pass_context

console = Console()


@click.group()
def skill() -> None:
    """Manage Claude Code skills."""
    pass


@skill.command("list")
@pass_context
def list_skills(ctx: Context) -> None:
    """List all available skills."""
    skills = ctx.skill_registry.get_all()

    if not skills:
        console.print("[yellow]No skills found.[/yellow]")
        console.print(f"Add skills to: {ctx.skills_dir}")
        return

    table = Table(title="Available Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Context")
    table.add_column("Agent")
    table.add_column("Tools")

    for s in skills:
        tools = ", ".join(s.allowed_tools[:3])
        if len(s.allowed_tools) > 3:
            tools += f" (+{len(s.allowed_tools) - 3})"

        table.add_row(
            s.name,
            s.description[:50] + "..." if len(s.description) > 50 else s.description,
            s.context,
            s.agent or "-",
            tools or "-",
        )

    console.print(table)


@skill.command("show")
@click.argument("name")
@pass_context
def show_skill(ctx: Context, name: str) -> None:
    """Show details of a specific skill."""
    try:
        s = ctx.skill_registry.get(name)
    except Exception:
        console.print(f"[red]Skill not found: {name}[/red]")
        console.print(
            "Available skills:", ", ".join(sk.name for sk in ctx.skill_registry.get_all()) or "none"
        )
        raise SystemExit(1)

    # Build details
    details = f"""[bold]Name:[/bold] {s.name}
[bold]Path:[/bold] {s.path}
[bold]Description:[/bold] {s.description}
[bold]Context:[/bold] {s.context}
[bold]Agent:[/bold] {s.agent or "-"}
[bold]Disable Model Invocation:[/bold] {s.disable_model_invocation}
[bold]Allowed Tools:[/bold] {", ".join(s.allowed_tools) or "-"}"""

    console.print(Panel(details, title=f"Skill: {s.name}"))

    # Show dynamic commands if any
    dynamic_cmds = s.get_dynamic_commands()
    if dynamic_cmds:
        console.print("\n[bold]Dynamic Context Commands:[/bold]")
        for cmd in dynamic_cmds:
            console.print(f"  - {cmd}")

    # Show content preview
    if s.content:
        console.print("\n[bold]Content Preview:[/bold]")
        preview = s.content[:500] + "..." if len(s.content) > 500 else s.content
        console.print(Panel(preview, title="SKILL.md"))


@skill.command("validate")
@click.argument("name")
@pass_context
def validate_skill(ctx: Context, name: str) -> None:
    """Validate a skill's SKILL.md format."""
    try:
        s = ctx.skill_registry.get(name)
    except Exception:
        console.print(f"[red]Skill not found: {name}[/red]")
        raise SystemExit(1)

    issues = []

    # Check required fields
    if not s.description:
        issues.append("Missing description in frontmatter")

    if not s.content:
        issues.append("Missing content (instructions) after frontmatter")

    # Check for $ARGUMENTS placeholder
    if "$ARGUMENTS" not in s.content:
        issues.append("Missing $ARGUMENTS placeholder in content")

    # Check dynamic commands syntax
    import re

    dynamic_pattern = r"!\`[^`]+\`"
    dynamic_matches = re.findall(dynamic_pattern, s.content)
    for match in dynamic_matches:
        # Check for common issues
        if match.count("`") != 2:
            issues.append(f"Malformed dynamic command: {match}")

    # Check allowed tools format
    if s.allowed_tools:
        for tool in s.allowed_tools:
            if not tool.strip():
                issues.append("Empty tool in allowed-tools list")

    if issues:
        console.print(f"[yellow]Validation issues for {name}:[/yellow]")
        for issue in issues:
            console.print(f"  - {issue}")
    else:
        console.print(f"[green]Skill '{name}' is valid[/green]")


@skill.command("render")
@click.argument("name")
@click.argument("arguments", default="")
@pass_context
def render_skill(ctx: Context, name: str, arguments: str) -> None:
    """Render a skill with arguments (for debugging)."""
    try:
        s = ctx.skill_registry.get(name)
    except Exception:
        console.print(f"[red]Skill not found: {name}[/red]")
        raise SystemExit(1)

    rendered = s.render_content(arguments)

    console.print(f"[bold]Skill:[/bold] {name}")
    console.print(f"[bold]Arguments:[/bold] {arguments or '(none)'}")
    console.print()

    syntax = Syntax(rendered, "markdown", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Rendered Content"))


@skill.command("reload")
@pass_context
def reload_skills(ctx: Context) -> None:
    """Reload skills from disk."""
    ctx.skill_registry.reload()
    skills = ctx.skill_registry.get_all()
    console.print(f"[green]Reloaded {len(skills)} skill(s)[/green]")
    for s in skills:
        console.print(f"  - {s.name}")
