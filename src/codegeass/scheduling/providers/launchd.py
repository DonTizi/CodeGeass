"""macOS launchd scheduler provider."""

import shutil
import subprocess
from pathlib import Path

from codegeass.scheduling.providers.base import (
    SchedulerConfig,
    SchedulerProvider,
    SchedulerStatus,
)


class LaunchdProvider(SchedulerProvider):
    """macOS launchd implementation."""

    PLIST_NAME = "com.codegeass.scheduler.plist"
    SERVICE_LABEL = "com.codegeass.scheduler"

    @property
    def name(self) -> str:
        return "launchd"

    @property
    def display_name(self) -> str:
        return "launchd (macOS)"

    def is_available(self) -> bool:
        """Check if launchctl is available."""
        return shutil.which("launchctl") is not None

    def _get_plist_path(self) -> Path:
        """Get the path to the plist file."""
        return Path.home() / "Library" / "LaunchAgents" / self.PLIST_NAME

    def _generate_plist(self, codegeass_path: str) -> str:
        """Generate the plist content."""
        home = Path.home()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.SERVICE_LABEL}</string>
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

    def install(
        self, codegeass_path: str, working_dir: Path | None = None
    ) -> tuple[bool, str]:
        """Install launchd service."""
        plist_path = self._get_plist_path()
        launch_agents_dir = plist_path.parent

        try:
            # Create LaunchAgents directory if needed
            launch_agents_dir.mkdir(parents=True, exist_ok=True)

            # Unload existing service if present
            if plist_path.exists():
                subprocess.run(
                    ["launchctl", "unload", str(plist_path)],
                    capture_output=True,
                    check=False,
                )

            # Write plist file
            plist_content = self._generate_plist(codegeass_path)
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

    def uninstall(self) -> tuple[bool, str]:
        """Uninstall launchd service."""
        plist_path = self._get_plist_path()

        if not plist_path.exists():
            return True, "Not installed"

        try:
            subprocess.run(
                ["launchctl", "unload", str(plist_path)],
                capture_output=True,
                check=False,
            )
            plist_path.unlink(missing_ok=True)
            return True, "Service unloaded and plist removed"
        except Exception as e:
            return False, str(e)

    def status(self) -> SchedulerStatus:
        """Get launchd scheduler status."""
        plist_path = self._get_plist_path()

        if not plist_path.exists():
            return SchedulerStatus(
                installed=False,
                running=False,
                scheduler_type=self.display_name,
            )

        # Check if service is loaded and running
        try:
            result = subprocess.run(
                ["launchctl", "list"],
                capture_output=True,
                text=True,
            )
            running = self.SERVICE_LABEL in result.stdout
        except Exception:
            running = False

        return SchedulerStatus(
            installed=True,
            running=running,
            scheduler_type=self.display_name,
            details=str(plist_path),
        )

    def get_config(self) -> SchedulerConfig:
        """Get launchd configuration."""
        return SchedulerConfig(
            name=self.name,
            display_name=self.display_name,
            description="macOS native task scheduler",
            check_command="launchctl list | grep codegeass",
            stop_command="codegeass uninstall-scheduler",
        )
