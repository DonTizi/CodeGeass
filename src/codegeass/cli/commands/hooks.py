"""Hook management CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from codegeass.cli.main import Context, pass_context

console = Console()


@click.group()
def hooks() -> None:
    """Manage Claude Code hooks for tasks."""
    pass


@hooks.command("list")
@pass_context
def list_hooks(ctx: Context) -> None:
    """List all available hook tags."""
    tags = ctx.hook_repo.list_tags()

    if not tags:
        console.print("[yellow]No hooks configured.[/yellow]")
        console.print("\nInitialize with built-in templates:")
        console.print("  codegeass hooks init")
        console.print("\nOr create a new hook:")
        console.print("  codegeass hooks create <tag-name>")
        return

    table = Table(title="Hook Tags")
    table.add_column("Tag", style="cyan")
    table.add_column("Description")
    table.add_column("Location", style="dim")
    table.add_column("Events")

    for tag in tags:
        tag_hooks = ctx.hook_repo.get_tag(tag)
        if not tag_hooks:
            continue

        location = ctx.hook_repo.get_tag_location(tag) or "unknown"
        events = ", ".join(sorted(tag_hooks.hooks.keys())) or "-"

        desc = tag_hooks.description
        desc_display = desc[:50] + "..." if len(desc) > 50 else desc
        table.add_row(tag, desc_display, location, events)

    console.print(table)
    console.print("\nUse 'codegeass hooks show <tag>' for details")


@hooks.command("show")
@click.argument("tag")
@pass_context
def show_hook(ctx: Context, tag: str) -> None:
    """Show details of a hook tag."""
    tag_hooks = ctx.hook_repo.get_tag(tag)

    if not tag_hooks:
        console.print(f"[red]Hook tag not found: {tag}[/red]")
        console.print("Available tags:", ", ".join(ctx.hook_repo.list_tags()) or "none")
        raise SystemExit(1)

    # Build details
    location = ctx.hook_repo.get_tag_location(tag) or "unknown"
    details = f"""[bold]Tag:[/bold] {tag_hooks.tag}
[bold]Description:[/bold] {tag_hooks.description}
[bold]Location:[/bold] {location}
[bold]Events:[/bold] {", ".join(sorted(tag_hooks.hooks.keys())) or "none"}"""

    console.print(Panel(details, title=f"Hook: {tag}"))

    # Show hooks by event
    for event in sorted(tag_hooks.hooks.keys()):
        console.print(f"\n[bold]{event}:[/bold]")
        matchers = tag_hooks.hooks[event]
        for i, matcher in enumerate(matchers):
            matcher_pattern = matcher.get("matcher", "(all tools)")
            console.print(f"  [{i+1}] Matcher: {matcher_pattern}")
            for handler in matcher.get("hooks", []):
                handler_type = handler.get("type", "unknown")
                if handler_type == "command":
                    cmd = handler.get("command", "?")
                    # Truncate long commands
                    if len(cmd) > 60:
                        cmd = cmd[:57] + "..."
                    console.print(f"      → command: {cmd}")
                elif handler_type == "prompt":
                    prompt = handler.get("prompt", "?")[:40]
                    console.print(f"      → prompt: {prompt}...")
                else:
                    console.print(f"      → {handler_type}")


@hooks.command("init")
@click.option("--overwrite", is_flag=True, help="Overwrite existing hooks")
@pass_context
def init_hooks(ctx: Context, overwrite: bool) -> None:
    """Initialize hooks from built-in templates."""
    initialized = ctx.hook_repo.init_from_templates(overwrite=overwrite)

    if not initialized:
        if overwrite:
            console.print("[yellow]No templates available[/yellow]")
        else:
            console.print("[yellow]All templates already exist[/yellow]")
            console.print("Use --overwrite to replace")
        return

    console.print(f"[green]Initialized {len(initialized)} hook template(s):[/green]")
    for tag in initialized:
        console.print(f"  • {tag}")

    console.print("\nAvailable templates:")
    for tag in ctx.hook_repo.get_templates():
        console.print(f"  • {tag}")


@hooks.command("create")
@click.argument("tag")
@click.option("--description", "-d", default="", help="Hook description")
@click.option("--global", "is_global", is_flag=True, help="Create as global hook")
@pass_context
def create_hook(ctx: Context, tag: str, description: str, is_global: bool) -> None:
    """Create a new hook tag."""
    from codegeass.hooks.models import TagHooks

    if ctx.hook_repo.exists(tag):
        console.print(f"[red]Hook tag already exists: {tag}[/red]")
        console.print("Use 'codegeass hooks show' to view it")
        raise SystemExit(1)

    # Create empty hook
    tag_hooks = TagHooks(
        tag=tag,
        description=description or f"Custom hooks for {tag}",
        hooks={},
    )

    ctx.hook_repo.save_tag(tag_hooks, global_scope=is_global)

    location = "global" if is_global else "project"
    console.print(f"[green]Created hook tag: {tag} ({location})[/green]")

    # Show where to edit
    if is_global:
        hook_path = ctx.hook_repo.global_hooks_dir / f"{tag}.yaml"
    elif ctx.hook_repo.project_hooks_dir:
        hook_path = ctx.hook_repo.project_hooks_dir / f"{tag}.yaml"
    else:
        hook_path = ctx.hook_repo.global_hooks_dir / f"{tag}.yaml"

    console.print("\nEdit the hook configuration at:")
    console.print(f"  {hook_path}")


@hooks.command("delete")
@click.argument("tag")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def delete_hook(ctx: Context, tag: str, yes: bool) -> None:
    """Delete a hook tag."""
    if not ctx.hook_repo.exists(tag):
        console.print(f"[red]Hook tag not found: {tag}[/red]")
        raise SystemExit(1)

    if not yes:
        if not click.confirm(f"Delete hook tag '{tag}'?"):
            console.print("Cancelled")
            return

    if ctx.hook_repo.delete_tag(tag):
        console.print(f"[red]Deleted hook tag: {tag}[/red]")
    else:
        console.print(f"[yellow]Could not delete: {tag}[/yellow]")


@hooks.command("validate")
@click.argument("tag", required=False)
@pass_context
def validate_hooks(ctx: Context, tag: str | None) -> None:
    """Validate hook configurations."""
    tags_to_check = [tag] if tag else ctx.hook_repo.list_tags()

    if not tags_to_check:
        console.print("[yellow]No hooks to validate[/yellow]")
        return

    all_valid = True

    for t in tags_to_check:
        tag_hooks = ctx.hook_repo.get_tag(t)
        if not tag_hooks:
            console.print(f"[red]✗ {t}: Not found[/red]")
            all_valid = False
            continue

        errors = tag_hooks.validate()
        if errors:
            console.print(f"[red]✗ {t}:[/red]")
            for error in errors:
                console.print(f"    {error}")
            all_valid = False
        else:
            console.print(f"[green]✓ {t}: Valid[/green]")

    if all_valid:
        console.print("\n[green]All hooks are valid[/green]")
    else:
        console.print("\n[red]Some hooks have issues[/red]")
        raise SystemExit(1)


@hooks.command("preview")
@click.argument("tags", nargs=-1, required=True)
@pass_context
def preview_hooks(ctx: Context, tags: tuple[str, ...]) -> None:
    """Preview merged hooks for given tags."""
    from codegeass.hooks.resolver import HookResolver

    resolver = HookResolver(ctx.hook_repo)

    # Validate tags
    valid, invalid = resolver.validate_tags(list(tags))

    if invalid:
        console.print(f"[yellow]Unknown tags: {', '.join(invalid)}[/yellow]")

    if not valid:
        console.print("[red]No valid tags to preview[/red]")
        raise SystemExit(1)

    preview = resolver.get_preview(valid)
    console.print(Panel(preview, title=f"Merged hooks for: {', '.join(valid)}"))

    # Show the JSON that would be passed to --settings
    settings = resolver.resolve(valid)
    if settings:
        import json
        json_str = json.dumps(settings, indent=2)
        console.print("\n[bold]Settings JSON:[/bold]")
        console.print(Syntax(json_str, "json", theme="monokai"))


@hooks.command("test")
@click.argument("tag")
@click.option("--event", "-e", default="PreToolUse", help="Hook event to test")
@click.option("--tool", "-t", default="Bash", help="Tool name to simulate")
@pass_context
def test_hook(ctx: Context, tag: str, event: str, tool: str) -> None:
    """Test a hook by simulating an event."""
    tag_hooks = ctx.hook_repo.get_tag(tag)

    if not tag_hooks:
        console.print(f"[red]Hook tag not found: {tag}[/red]")
        raise SystemExit(1)

    if event not in tag_hooks.hooks:
        console.print(f"[yellow]No {event} hooks configured for {tag}[/yellow]")
        console.print(f"Available events: {', '.join(tag_hooks.hooks.keys()) or 'none'}")
        return

    import json
    import re
    import subprocess
    import tempfile

    console.print(f"Testing {event} hook for {tag} (tool: {tool})...\n")

    matchers = tag_hooks.hooks[event]
    for i, matcher_data in enumerate(matchers):
        matcher_pattern = matcher_data.get("matcher")
        if matcher_pattern and not re.match(matcher_pattern, tool):
            console.print(f"[dim]Matcher [{i+1}] '{matcher_pattern}' - skipped (no match)[/dim]")
            continue

        console.print(f"[bold]Matcher [{i+1}] '{matcher_pattern or '(all)'}' - matched[/bold]")

        for j, handler in enumerate(matcher_data.get("hooks", [])):
            handler_type = handler.get("type")
            if handler_type != "command":
                console.print(f"  [{j+1}] {handler_type}: (not testable)")
                continue

            command = handler.get("command")
            if not command:
                continue

            # Create test input
            test_input = json.dumps({
                "tool_name": tool,
                "tool_input": {"command": "echo 'test command'"},
            })

            console.print(f"  [{j+1}] Running command handler...")

            # Write command to temp script
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
                f.write(command)
                script_path = f.name

            try:
                result = subprocess.run(
                    ["bash", script_path],
                    input=test_input,
                    capture_output=True,
                    text=True,
                    timeout=handler.get("timeout", 10),
                )

                if result.returncode == 0:
                    console.print("      [green]✓ Exit code 0 (allow)[/green]")
                elif result.returncode == 2:
                    console.print("      [red]✗ Exit code 2 (block)[/red]")
                else:
                    console.print(f"      [yellow]? Exit code {result.returncode}[/yellow]")

                if result.stdout.strip():
                    console.print(f"      stdout: {result.stdout.strip()[:100]}")
                if result.stderr.strip():
                    console.print(f"      stderr: {result.stderr.strip()[:100]}")

            except subprocess.TimeoutExpired:
                console.print("      [red]✗ Timed out[/red]")
            except Exception as e:
                console.print(f"      [red]✗ Error: {e}[/red]")
            finally:
                import os
                os.unlink(script_path)


@hooks.command("templates")
@pass_context
def list_templates(ctx: Context) -> None:
    """List available built-in templates."""
    templates = ctx.hook_repo.get_templates()

    if not templates:
        console.print("[yellow]No built-in templates available[/yellow]")
        return

    console.print("[bold]Available templates:[/bold]")
    for template in templates:
        console.print(f"  • {template}")

    console.print("\nInstall with: codegeass hooks init")
