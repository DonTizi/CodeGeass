"""Provider management CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context
from codegeass.providers import ProviderNotFoundError, get_provider_registry

console = Console()


@click.group()
def provider() -> None:
    """Manage code execution providers."""
    pass


@provider.command("list")
@click.option("--available", "-a", is_flag=True, help="Show only available providers")
@pass_context
def list_providers(ctx: Context, available: bool) -> None:
    """List all registered code execution providers."""
    registry = get_provider_registry()
    providers = registry.list_provider_info()

    if available:
        providers = [p for p in providers if p.is_available]

    if not providers:
        console.print("[yellow]No providers found.[/yellow]")
        return

    table = Table(title="Code Execution Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name")
    table.add_column("Available", justify="center")
    table.add_column("Capabilities")

    for p in providers:
        # Build capabilities string
        caps = []
        if p.capabilities.plan_mode:
            caps.append("plan")
        if p.capabilities.resume:
            caps.append("resume")
        if p.capabilities.autonomous:
            caps.append("auto")
        if p.capabilities.streaming:
            caps.append("stream")
        caps_str = ", ".join(caps) if caps else "-"

        # Availability status
        avail_str = "[green]yes[/green]" if p.is_available else "[red]no[/red]"

        table.add_row(
            p.name,
            p.display_name,
            avail_str,
            caps_str,
        )

    console.print(table)

    # Show legend
    console.print("\n[dim]Capabilities: plan=plan mode, resume=session resume, "
                  "auto=autonomous mode, stream=streaming output[/dim]")


@provider.command("info")
@click.argument("name")
@pass_context
def provider_info(ctx: Context, name: str) -> None:
    """Show detailed information about a provider."""
    registry = get_provider_registry()

    try:
        info = registry.get_provider_info(name)
    except ProviderNotFoundError:
        console.print(f"[red]Provider not found: {name}[/red]")
        console.print("Available providers:", ", ".join(registry.list_providers()))
        raise SystemExit(1)

    # Build capabilities list
    caps = info.capabilities
    caps_lines = [
        f"  Plan Mode: {'[green]yes[/green]' if caps.plan_mode else '[red]no[/red]'}",
        f"  Session Resume: {'[green]yes[/green]' if caps.resume else '[red]no[/red]'}",
        f"  Streaming: {'[green]yes[/green]' if caps.streaming else '[red]no[/red]'}",
        f"  Autonomous: {'[green]yes[/green]' if caps.autonomous else '[red]no[/red]'}",
    ]
    if caps.autonomous and caps.autonomous_flag:
        caps_lines.append(f"  Autonomous Flag: {caps.autonomous_flag}")
    if caps.models:
        caps_lines.append(f"  Models: {', '.join(caps.models)}")

    # Build details
    avail_str = "[green]available[/green]" if info.is_available else "[red]not available[/red]"
    details = f"""[bold]Name:[/bold] {info.name}
[bold]Display Name:[/bold] {info.display_name}
[bold]Description:[/bold] {info.description}
[bold]Status:[/bold] {avail_str}
[bold]Executable:[/bold] {info.executable_path or 'not found'}

[bold]Capabilities:[/bold]
{chr(10).join(caps_lines)}"""

    console.print(Panel(details, title=f"Provider: {info.display_name}"))


@provider.command("check")
@pass_context
def check_providers(ctx: Context) -> None:
    """Check availability of all providers."""
    registry = get_provider_registry()
    providers = registry.list_provider_info()

    console.print("[bold]Checking provider availability...[/bold]\n")

    for p in providers:
        if p.is_available:
            console.print(f"[green]✓[/green] {p.display_name}: {p.executable_path}")
        else:
            console.print(f"[red]✗[/red] {p.display_name}: not available")

    # Summary
    available_count = sum(1 for p in providers if p.is_available)
    console.print(f"\n[bold]{available_count}/{len(providers)}[/bold] providers available")
