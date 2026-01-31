"""Setup command - One-command installation with 24/7 scheduler."""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def get_codegeass_path() -> str:
    """Get the path to the codegeass executable."""
    # Try to find codegeass in PATH
    codegeass_path = shutil.which("codegeass")
    if codegeass_path:
        return codegeass_path

    # Fall back to common locations
    home = Path.home()
    candidates = [
        home / ".local" / "bin" / "codegeass",
        home / ".local" / "pipx" / "venvs" / "codegeass" / "bin" / "codegeass",
        Path(sys.prefix) / "bin" / "codegeass",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    # Last resort: use python -m
    return f"{sys.executable} -m codegeass"


def is_scheduler_installed() -> tuple[bool, str]:
    """Check if the scheduler is already installed.

    Returns:
        Tuple of (is_installed, scheduler_type)
    """
    system = platform.system()
    home = Path.home()

    if system == "Darwin":
        plist_path = home / "Library" / "LaunchAgents" / "com.codegeass.scheduler.plist"
        if plist_path.exists():
            # Check if it's actually running
            result = subprocess.run(
                ["launchctl", "list"],
                capture_output=True,
                text=True,
            )
            if "com.codegeass.scheduler" in result.stdout:
                return True, "launchd (running)"
            return True, "launchd (installed but not running)"
        return False, ""

    elif system == "Linux":
        timer_path = home / ".config" / "systemd" / "user" / "codegeass-scheduler.timer"
        if timer_path.exists():
            # Check if it's actually running
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "codegeass-scheduler.timer"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True, "systemd (running)"
            return True, "systemd (installed but not running)"

        # Check cron
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0 and "codegeass" in result.stdout:
            return True, "cron"

        return False, ""

    return False, ""


def install_launchd_macos() -> tuple[bool, str]:
    """Install launchd service on macOS for 24/7 scheduling."""
    home = Path.home()
    launch_agents_dir = home / "Library" / "LaunchAgents"
    plist_path = launch_agents_dir / "com.codegeass.scheduler.plist"

    codegeass_path = get_codegeass_path()

    # Create LaunchAgents directory if needed
    launch_agents_dir.mkdir(parents=True, exist_ok=True)

    # Create plist content
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.codegeass.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>{codegeass_path}</string>
        <string>scheduler</string>
        <string>run-due</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/codegeass-scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/codegeass-scheduler.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:{home}/.local/bin</string>
    </dict>
</dict>
</plist>
"""

    try:
        # Unload existing service if present
        if plist_path.exists():
            subprocess.run(
                ["launchctl", "unload", str(plist_path)],
                capture_output=True,
                check=False,
            )

        # Write plist file
        plist_path.write_text(plist_content)

        # Load the service
        result = subprocess.run(
            ["launchctl", "load", str(plist_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return False, f"Failed to load launchd service: {result.stderr}"

        return True, str(plist_path)

    except Exception as e:
        return False, str(e)


def install_systemd_linux() -> tuple[bool, str]:
    """Install systemd user service on Linux for 24/7 scheduling."""
    home = Path.home()
    systemd_dir = home / ".config" / "systemd" / "user"
    service_path = systemd_dir / "codegeass-scheduler.service"
    timer_path = systemd_dir / "codegeass-scheduler.timer"

    codegeass_path = get_codegeass_path()

    # Create systemd user directory if needed
    systemd_dir.mkdir(parents=True, exist_ok=True)

    # Create service unit
    service_content = f"""[Unit]
Description=CodeGeass Scheduler - Run due tasks
After=network.target

[Service]
Type=oneshot
ExecStart={codegeass_path} scheduler run-due
Environment="PATH=/usr/local/bin:/usr/bin:/bin:{home}/.local/bin"

[Install]
WantedBy=default.target
"""

    # Create timer unit (runs every minute)
    timer_content = """[Unit]
Description=CodeGeass Scheduler Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
AccuracySec=1s

[Install]
WantedBy=timers.target
"""

    try:
        # Stop existing timer if running
        subprocess.run(
            ["systemctl", "--user", "stop", "codegeass-scheduler.timer"],
            capture_output=True,
            check=False,
        )

        # Write unit files
        service_path.write_text(service_content)
        timer_path.write_text(timer_content)

        # Reload systemd
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
            check=True,
        )

        # Enable and start timer
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", "codegeass-scheduler.timer"],
            capture_output=True,
            check=True,
        )

        return True, str(timer_path)

    except subprocess.CalledProcessError as e:
        return False, f"systemctl failed: {e.stderr if e.stderr else str(e)}"
    except Exception as e:
        return False, str(e)


def install_cron_fallback() -> tuple[bool, str]:
    """Install cron job as fallback."""
    codegeass_path = get_codegeass_path()
    cron_line = f"* * * * * {codegeass_path} scheduler run-due >> /tmp/codegeass.log 2>&1"

    try:
        # Get current crontab
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
        )
        current_crontab = result.stdout if result.returncode == 0 else ""

        # Check if already installed
        if "codegeass scheduler run-due" in current_crontab:
            return True, "Already installed in crontab"

        # Add new cron line
        new_crontab = current_crontab.rstrip() + "\n" + cron_line + "\n"

        # Install new crontab
        process = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            text=True,
        )
        process.communicate(input=new_crontab)

        if process.returncode != 0:
            return False, "Failed to install crontab"

        return True, "Installed in crontab"

    except Exception as e:
        return False, str(e)


def remove_scheduler_silent() -> None:
    """Remove scheduler without output (used during uninstall)."""
    system = platform.system()
    home = Path.home()

    if system == "Darwin":
        plist_path = home / "Library" / "LaunchAgents" / "com.codegeass.scheduler.plist"
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
            plist_path.unlink(missing_ok=True)

    elif system == "Linux":
        timer_path = home / ".config" / "systemd" / "user" / "codegeass-scheduler.timer"
        service_path = home / ".config" / "systemd" / "user" / "codegeass-scheduler.service"

        if timer_path.exists():
            subprocess.run(
                ["systemctl", "--user", "disable", "--now", "codegeass-scheduler.timer"],
                capture_output=True,
            )
            timer_path.unlink(missing_ok=True)
            service_path.unlink(missing_ok=True)
            subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)

    # Remove cron entries
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0 and "codegeass" in result.stdout:
            new_crontab = "\n".join(
                line for line in result.stdout.splitlines() if "codegeass" not in line
            )
            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab + "\n")
    except Exception:
        pass


@click.command()
@click.option(
    "--scheduler/--no-scheduler",
    default=True,
    help="Install 24/7 scheduler (default: yes)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force reinstall scheduler even if already installed",
)
def setup(scheduler: bool, force: bool) -> None:
    """One-command setup: initialize project + install 24/7 scheduler.

    This command will:
    1. Detect your operating system
    2. Install the appropriate background scheduler:
       - macOS: launchd (recommended)
       - Linux: systemd user service
       - Fallback: cron

    The scheduler runs every minute and executes any due tasks automatically.

    Examples:
        codegeass setup              # Full setup with scheduler
        codegeass setup --force      # Reinstall scheduler
        codegeass setup --no-scheduler  # Setup without scheduler
    """
    console.print("\n[bold cyan]CodeGeass Setup[/bold cyan]\n")

    # Step 1: Detect OS
    system = platform.system()
    console.print(f"[dim]Detected OS:[/dim] {system}")

    # Step 2: Check codegeass is accessible
    codegeass_path = get_codegeass_path()
    console.print(f"[dim]CodeGeass path:[/dim] {codegeass_path}")

    # Step 3: Check if scheduler is already installed
    already_installed, current_type = is_scheduler_installed()

    if already_installed and not force and scheduler:
        console.print(f"\n[green]\u2713 Scheduler already installed ({current_type})[/green]")
        console.print("[dim]Use --force to reinstall[/dim]")

        # Set variables for the summary panel
        if system == "Darwin":
            scheduler_type = "launchd"
            check_cmd = "launchctl list | grep codegeass"
            stop_cmd = "codegeass uninstall-scheduler"
        else:
            scheduler_type = "systemd" if "systemd" in current_type else "cron"
            check_cmd = "systemctl --user status codegeass-scheduler.timer"
            stop_cmd = "codegeass uninstall-scheduler"

    elif scheduler:
        if already_installed:
            console.print(f"\n[yellow]Reinstalling scheduler (was: {current_type})...[/yellow]")
        else:
            console.print("\n[bold]Installing 24/7 scheduler...[/bold]")

        if system == "Darwin":
            console.print("[dim]Using launchd (macOS native)[/dim]")
            success, message = install_launchd_macos()
            scheduler_type = "launchd"
            check_cmd = "launchctl list | grep codegeass"
            stop_cmd = "codegeass uninstall-scheduler"

        elif system == "Linux":
            console.print("[dim]Using systemd user service[/dim]")
            success, message = install_systemd_linux()
            scheduler_type = "systemd"
            check_cmd = "systemctl --user status codegeass-scheduler.timer"
            stop_cmd = "codegeass uninstall-scheduler"

            if not success:
                console.print("[yellow]systemd failed, falling back to cron[/yellow]")
                success, message = install_cron_fallback()
                scheduler_type = "cron"
                check_cmd = "crontab -l | grep codegeass"
                stop_cmd = "codegeass uninstall-scheduler"

        else:
            console.print("[dim]Using cron (fallback)[/dim]")
            success, message = install_cron_fallback()
            scheduler_type = "cron"
            check_cmd = "crontab -l | grep codegeass"
            stop_cmd = "codegeass uninstall-scheduler"

        if success:
            action = "Reinstalled" if already_installed else "Installed"
            console.print(f"[green]\u2713 Scheduler {action.lower()} ({scheduler_type})[/green]")
        else:
            console.print(f"[red]\u2717 Scheduler installation failed: {message}[/red]")
            console.print("\n[yellow]You can try again or install manually.[/yellow]")
            return
    else:
        scheduler_type = None
        check_cmd = None
        stop_cmd = None

    # Final summary
    scheduler_info = ""
    if scheduler and scheduler_type:
        scheduler_info = (
            f"[cyan]24/7 Scheduler:[/cyan] Running ({scheduler_type})\n"
            f"[dim]Check status:[/dim] {check_cmd}\n"
            f"[dim]Uninstall:[/dim] {stop_cmd}\n\n"
        )

    console.print(
        Panel.fit(
            "[green bold]\u2713 CodeGeass is ready![/green bold]\n\n"
            + scheduler_info
            + "[cyan]Next steps:[/cyan]\n"
            "1. Create a project:  [bold]codegeass init[/bold]\n"
            "2. Create a task:     [bold]codegeass task create[/bold]\n"
            "3. View dashboard:    [bold]codegeass dashboard[/bold]\n\n"
            "[dim]Logs: /tmp/codegeass-scheduler.log[/dim]",
            title="Setup Complete",
            border_style="green",
        )
    )


def _remove_scheduler() -> bool:
    """Remove the scheduler and return True if something was removed."""
    system = platform.system()
    home = Path.home()
    removed_something = False

    if system == "Darwin":
        plist_path = home / "Library" / "LaunchAgents" / "com.codegeass.scheduler.plist"
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
            plist_path.unlink()
            console.print("[green]\u2713 Scheduler service removed[/green]")
            removed_something = True

    elif system == "Linux":
        timer_path = home / ".config" / "systemd" / "user" / "codegeass-scheduler.timer"
        service_path = home / ".config" / "systemd" / "user" / "codegeass-scheduler.service"

        if timer_path.exists():
            subprocess.run(
                ["systemctl", "--user", "disable", "--now", "codegeass-scheduler.timer"],
                capture_output=True,
            )
            timer_path.unlink(missing_ok=True)
            service_path.unlink(missing_ok=True)
            subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
            console.print("[green]\u2713 Scheduler service removed[/green]")
            removed_something = True

    # Check cron too
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0 and "codegeass" in result.stdout:
            new_crontab = "\n".join(
                line for line in result.stdout.splitlines() if "codegeass" not in line
            )
            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab + "\n")
            console.print("[green]\u2713 Cron entry removed[/green]")
            removed_something = True
    except Exception:
        pass

    return removed_something


@click.command(name="uninstall-scheduler")
def uninstall_scheduler() -> None:
    """Remove only the 24/7 background scheduler.

    This removes the scheduler service from your system but keeps
    all your tasks, logs, and configuration.

    For complete uninstallation, use: codegeass uninstall --all

    Example:
        codegeass uninstall-scheduler
        pipx uninstall codegeass
    """
    console.print("\n[bold]Removing scheduler...[/bold]")

    removed_something = _remove_scheduler()

    if removed_something:
        console.print(
            Panel.fit(
                "[green]Scheduler removed successfully![/green]\n\n"
                "Your tasks and configuration are still intact.\n\n"
                "To completely uninstall CodeGeass:\n"
                "[bold]codegeass uninstall --all[/bold]\n"
                "or just remove the package:\n"
                "[bold]pipx uninstall codegeass[/bold]",
                title="Scheduler Removed",
                border_style="green",
            )
        )
    else:
        console.print("\n[yellow]No scheduler was installed.[/yellow]")


@click.command()
@click.option(
    "--all",
    "remove_all",
    is_flag=True,
    help="Remove everything: scheduler, global config, and project data",
)
@click.option(
    "--keep-global",
    is_flag=True,
    help="Keep global config (~/.codegeass/) when using --all",
)
@click.option(
    "--keep-project",
    is_flag=True,
    help="Keep project data (config/, data/) when using --all",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def uninstall(remove_all: bool, keep_global: bool, keep_project: bool, yes: bool) -> None:
    """Uninstall CodeGeass and optionally remove all data.

    Without --all, this only removes the scheduler (same as uninstall-scheduler).

    With --all, this removes:
    - Scheduler service (launchd/systemd/cron)
    - Global config (~/.codegeass/) - credentials, shared skills
    - Project config (config/) - tasks, settings, notifications
    - Project data (data/) - logs, sessions

    Examples:
        codegeass uninstall              # Remove scheduler only
        codegeass uninstall --all        # Remove everything
        codegeass uninstall --all -y     # Remove everything without confirmation
        codegeass uninstall --all --keep-global  # Keep ~/.codegeass/
    """
    home = Path.home()
    cwd = Path.cwd()

    global_config_dir = home / ".codegeass"
    project_config_dir = cwd / "config"
    project_data_dir = cwd / "data"

    if not remove_all:
        # Just remove scheduler
        console.print("\n[bold]Removing scheduler...[/bold]")
        removed = _remove_scheduler()
        if removed:
            console.print(
                "\n[dim]To remove all data, use:[/dim] codegeass uninstall --all"
            )
        else:
            console.print("\n[yellow]No scheduler was installed.[/yellow]")
        return

    # Show what will be removed
    console.print("\n[bold red]CodeGeass Uninstall[/bold red]\n")
    console.print("[yellow]This will remove:[/yellow]")

    items_to_remove = []

    # Scheduler
    scheduler_installed, scheduler_type = is_scheduler_installed()
    if scheduler_installed:
        console.print(f"  - Scheduler service ({scheduler_type})")
        items_to_remove.append("scheduler")

    # Global config
    if not keep_global and global_config_dir.exists():
        console.print(f"  - Global config ({global_config_dir})")
        items_to_remove.append("global")

    # Project config
    if not keep_project and project_config_dir.exists():
        console.print(f"  - Project config ({project_config_dir})")
        items_to_remove.append("project_config")

    # Project data
    if not keep_project and project_data_dir.exists():
        console.print(f"  - Project data ({project_data_dir})")
        items_to_remove.append("project_data")

    if not items_to_remove:
        console.print("\n[yellow]Nothing to remove.[/yellow]")
        return

    console.print("")

    # Confirm
    if not yes:
        confirm = click.confirm("Are you sure you want to continue?", default=False)
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            return

    console.print("")

    # Remove scheduler
    if "scheduler" in items_to_remove:
        _remove_scheduler()

    # Remove global config
    if "global" in items_to_remove:
        try:
            shutil.rmtree(global_config_dir)
            console.print(f"[green]\u2713 Global config removed ({global_config_dir})[/green]")
        except Exception as e:
            console.print(f"[red]\u2717 Failed to remove global config: {e}[/red]")

    # Remove project config
    if "project_config" in items_to_remove:
        try:
            shutil.rmtree(project_config_dir)
            console.print(f"[green]\u2713 Project config removed ({project_config_dir})[/green]")
        except Exception as e:
            console.print(f"[red]\u2717 Failed to remove project config: {e}[/red]")

    # Remove project data
    if "project_data" in items_to_remove:
        try:
            shutil.rmtree(project_data_dir)
            console.print(f"[green]\u2713 Project data removed ({project_data_dir})[/green]")
        except Exception as e:
            console.print(f"[red]\u2717 Failed to remove project data: {e}[/red]")

    console.print(
        Panel.fit(
            "[green bold]CodeGeass uninstalled successfully![/green bold]\n\n"
            "To remove the Python package:\n"
            "[bold]pipx uninstall codegeass[/bold]",
            title="Uninstall Complete",
            border_style="green",
        )
    )
