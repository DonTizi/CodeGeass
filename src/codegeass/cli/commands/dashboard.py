"""Dashboard command for CodeGeass CLI."""

import click
from rich.console import Console

console = Console()


@click.command("dashboard")
@click.option("--port", "-p", default=8001, help="Port to run the dashboard on")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
def dashboard(port: int, host: str) -> None:
    """Start the CodeGeass web dashboard.

    The dashboard provides a web interface for:
    - Managing tasks
    - Viewing execution logs
    - Monitoring scheduled runs
    - Configuring notifications
    """
    try:
        from codegeass.dashboard.main import run_server

        console.print("[bold green]Starting CodeGeass Dashboard...[/bold green]")
        console.print(f"[dim]Open http://{host}:{port} in your browser[/dim]\n")
        run_server(host=host, port=port)

    except ImportError as e:
        console.print("[red]Dashboard dependencies not installed.[/red]")
        console.print("[dim]Install with: pip install 'codegeass[dashboard]'[/dim]")
        console.print(f"[dim]Error: {e}[/dim]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Failed to start dashboard: {e}[/red]")
        raise SystemExit(1)
