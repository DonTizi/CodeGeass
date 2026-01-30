"""Notification management CLI commands."""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context
from codegeass.notifications.registry import get_provider_registry

console = Console()


def _get_channel_repo(ctx: Context):
    """Get channel repository from context."""
    from codegeass.storage.channel_repository import ChannelRepository

    notifications_file = ctx.config_dir / "notifications.yaml"
    return ChannelRepository(notifications_file)


def _get_notification_service(ctx: Context):
    """Get notification service from context."""
    from codegeass.notifications.service import NotificationService

    channel_repo = _get_channel_repo(ctx)
    return NotificationService(channel_repo)


@click.group()
def notification() -> None:
    """Manage notification channels."""
    pass


@notification.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all channels including disabled")
@pass_context
def list_channels(ctx: Context, show_all: bool) -> None:
    """List all notification channels."""
    channel_repo = _get_channel_repo(ctx)
    channels = channel_repo.find_all()

    if not channels:
        console.print("[yellow]No notification channels configured.[/yellow]")
        console.print(
            "Add a channel with: codegeass notification add --provider telegram --name 'My Channel'"
        )
        return

    if not show_all:
        channels = [ch for ch in channels if ch.enabled]

    if not channels:
        console.print(
            "[yellow]No enabled channels found. Use --all to see disabled channels.[/yellow]"
        )
        return

    table = Table(title="Notification Channels")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Provider")
    table.add_column("Status")
    table.add_column("Created")

    for ch in channels:
        status = "[green]enabled[/green]" if ch.enabled else "[red]disabled[/red]"
        created = ch.created_at[:10] if ch.created_at else "-"
        table.add_row(ch.id, ch.name, ch.provider, status, created)

    console.print(table)


@notification.command("show")
@click.argument("channel_id")
@pass_context
def show_channel(ctx: Context, channel_id: str) -> None:
    """Show details of a notification channel."""
    channel_repo = _get_channel_repo(ctx)
    channel = channel_repo.find_by_id(channel_id)

    if not channel:
        # Try to find by name
        channel = channel_repo.find_by_name(channel_id)

    if not channel:
        console.print(f"[red]Channel not found: {channel_id}[/red]")
        raise SystemExit(1)

    details = f"""[bold]ID:[/bold] {channel.id}
[bold]Name:[/bold] {channel.name}
[bold]Provider:[/bold] {channel.provider}
[bold]Enabled:[/bold] {channel.enabled}
[bold]Credential Key:[/bold] {channel.credential_key}
[bold]Created:[/bold] {channel.created_at or "unknown"}"""

    if channel.config:
        config_str = "\n".join(f"  {k}: {v}" for k, v in channel.config.items())
        details += f"\n[bold]Config:[/bold]\n{config_str}"

    console.print(Panel(details, title=f"Channel: {channel.name}"))


@notification.command("add")
@click.option(
    "--provider",
    "-p",
    required=True,
    type=click.Choice(["telegram", "discord", "teams"]),
    help="Provider type",
)
@click.option("--name", "-n", required=True, help="Channel display name")
@pass_context
def add_channel(ctx: Context, provider: str, name: str) -> None:
    """Add a new notification channel (interactive)."""
    service = _get_notification_service(ctx)
    registry = get_provider_registry()

    # Get provider config schema
    provider_info = registry.get_provider_info(provider)

    console.print(f"\n[bold]Setting up {provider_info.display_name} channel: {name}[/bold]\n")

    # Collect credentials
    credentials = {}
    for cred_field in provider_info.required_credentials:
        field_name = cred_field["name"]
        field_desc = cred_field.get("description", field_name)
        is_sensitive = cred_field.get("sensitive", True)

        console.print(f"[cyan]{field_desc}[/cyan]")
        value = click.prompt(f"  {field_name}", hide_input=is_sensitive)
        credentials[field_name] = value

    # Collect non-secret config
    config = {}
    for config_field in provider_info.required_config:
        field_name = config_field["name"]
        field_desc = config_field.get("description", field_name)

        console.print(f"[cyan]{field_desc}[/cyan]")
        value = click.prompt(f"  {field_name}")
        config[field_name] = value

    # Optional config
    if provider_info.optional_config:
        if click.confirm("\nConfigure optional settings?", default=False):
            for opt_field in provider_info.optional_config:
                field_name = opt_field["name"]
                field_desc = opt_field.get("description", field_name)
                default = opt_field.get("default")

                console.print(f"[cyan]{field_desc}[/cyan]")
                value = click.prompt(f"  {field_name}", default=str(default) if default else "")
                if value:
                    config[field_name] = value

    # Generate credential key
    credential_key = f"{provider}_{name.lower().replace(' ', '_')}"

    try:
        channel = service.create_channel(
            name=name,
            provider=provider,
            credential_key=credential_key,
            credentials=credentials,
            config=config,
        )

        console.print("\n[green]Channel created successfully![/green]")
        console.print(f"ID: {channel.id}")
        console.print(f"Name: {channel.name}")
        console.print(f"Provider: {channel.provider}")
        console.print("\nCredentials stored in: ~/.codegeass/credentials.yaml")
        console.print(f"\nTest it with: codegeass notification test {channel.id}")

    except Exception as e:
        console.print(f"\n[red]Error creating channel: {e}[/red]")
        raise SystemExit(1)


@notification.command("remove")
@click.argument("channel_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--keep-credentials", is_flag=True, help="Keep credentials in ~/.codegeass/")
@pass_context
def remove_channel(ctx: Context, channel_id: str, yes: bool, keep_credentials: bool) -> None:
    """Remove a notification channel."""
    service = _get_notification_service(ctx)
    channel = service.get_channel(channel_id)

    if not channel:
        console.print(f"[red]Channel not found: {channel_id}[/red]")
        raise SystemExit(1)

    if not yes:
        if not click.confirm(f"Delete channel '{channel.name}' ({channel_id})?"):
            console.print("Cancelled")
            return

    if service.delete_channel(channel_id, delete_credentials=not keep_credentials):
        console.print(f"[green]Channel deleted: {channel.name}[/green]")
        if not keep_credentials:
            console.print("Credentials also removed from ~/.codegeass/credentials.yaml")
    else:
        console.print("[red]Failed to delete channel[/red]")
        raise SystemExit(1)


@notification.command("update")
@click.argument("channel_id")
@click.option("--name", "-n", help="New display name")
@click.option("--enabled/--disabled", default=None, help="Enable or disable channel")
@click.option("--config", "-c", multiple=True, help="Update config values (format: key=value)")
@pass_context
def update_channel(
    ctx: Context, channel_id: str, name: str | None, enabled: bool | None, config: tuple[str, ...]
) -> None:
    """Update a notification channel."""
    channel_repo = _get_channel_repo(ctx)
    channel = channel_repo.find_by_id(channel_id)

    if not channel:
        console.print(f"[red]Channel not found: {channel_id}[/red]")
        raise SystemExit(1)

    updated = False

    if name is not None:
        channel.name = name
        updated = True

    if enabled is not None:
        channel.enabled = enabled
        updated = True

    if config:
        if channel.config is None:
            channel.config = {}
        for item in config:
            if "=" not in item:
                console.print(f"[red]Invalid config format: {item} (expected key=value)[/red]")
                raise SystemExit(1)
            key, value = item.split("=", 1)
            channel.config[key] = value
            updated = True

    if not updated:
        console.print("[yellow]No updates specified.[/yellow]")
        return

    channel_repo.update(channel)
    console.print(f"[green]Channel updated: {channel_id}[/green]")


@notification.command("test")
@click.argument("channel_id")
@click.option("--message", "-m", default=None, help="Custom test message")
@pass_context
def test_channel(ctx: Context, channel_id: str, message: str | None) -> None:
    """Send a test notification to a channel."""
    service = _get_notification_service(ctx)

    console.print(f"Testing channel {channel_id}...")

    async def _test():
        # First test connection
        success, status_msg = await service.test_channel(channel_id)
        if not success:
            console.print(f"[red]Connection test failed: {status_msg}[/red]")
            return False

        console.print(f"[green]Connection OK: {status_msg}[/green]")

        # Send test message
        if message:
            test_msg = message
        else:
            test_msg = "Test notification from CodeGeass!"

        if await service.send_test_message(channel_id, test_msg):
            console.print("[green]Test message sent successfully![/green]")
            return True
        else:
            console.print("[red]Failed to send test message[/red]")
            return False

    success = asyncio.run(_test())
    if not success:
        raise SystemExit(1)


@notification.command("enable")
@click.argument("channel_id")
@pass_context
def enable_channel(ctx: Context, channel_id: str) -> None:
    """Enable a notification channel."""
    service = _get_notification_service(ctx)

    if service.enable_channel(channel_id):
        console.print(f"[green]Channel enabled: {channel_id}[/green]")
    else:
        console.print(f"[red]Channel not found: {channel_id}[/red]")
        raise SystemExit(1)


@notification.command("disable")
@click.argument("channel_id")
@pass_context
def disable_channel(ctx: Context, channel_id: str) -> None:
    """Disable a notification channel."""
    service = _get_notification_service(ctx)

    if service.disable_channel(channel_id):
        console.print(f"[yellow]Channel disabled: {channel_id}[/yellow]")
    else:
        console.print(f"[red]Channel not found: {channel_id}[/red]")
        raise SystemExit(1)


@notification.command("providers")
def list_providers() -> None:
    """List available notification providers."""
    registry = get_provider_registry()

    table = Table(title="Available Notification Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="green")
    table.add_column("Description")
    table.add_column("Required Credentials")
    table.add_column("Required Config")

    for provider_name in registry.list_providers():
        try:
            info = registry.get_provider_info(provider_name)
            creds = ", ".join(f["name"] for f in info.required_credentials)
            config = ", ".join(f["name"] for f in info.required_config) or "-"
            table.add_row(info.name, info.display_name, info.description, creds, config)
        except Exception as e:
            table.add_row(provider_name, "-", f"[red]Error: {e}[/red]", "-", "-")

    console.print(table)
