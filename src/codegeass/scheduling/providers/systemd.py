"""Linux systemd scheduler provider."""

import shutil
import subprocess
from pathlib import Path

from codegeass.scheduling.providers.base import (
    SchedulerConfig,
    SchedulerProvider,
    SchedulerStatus,
)


class SystemdProvider(SchedulerProvider):
    """Linux systemd user service implementation."""

    SERVICE_NAME = "codegeass-scheduler.service"
    TIMER_NAME = "codegeass-scheduler.timer"

    @property
    def name(self) -> str:
        return "systemd"

    @property
    def display_name(self) -> str:
        return "systemd (Linux)"

    def is_available(self) -> bool:
        """Check if systemctl is available for user services."""
        if shutil.which("systemctl") is None:
            return False

        # Check if user systemd is available
        try:
            result = subprocess.run(
                ["systemctl", "--user", "show-environment"],
                capture_output=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_systemd_dir(self) -> Path:
        """Get the path to the user systemd directory."""
        return Path.home() / ".config" / "systemd" / "user"

    def _generate_service(self, codegeass_path: str) -> str:
        """Generate the service unit content."""
        home = Path.home()
        return f"""[Unit]
Description=CodeGeass Scheduler - Run due tasks
After=network.target

[Service]
Type=oneshot
ExecStart={codegeass_path} scheduler run-due
Environment="PATH=/usr/local/bin:/usr/bin:/bin:{home}/.local/bin"

[Install]
WantedBy=default.target
"""

    def _generate_timer(self) -> str:
        """Generate the timer unit content."""
        return """[Unit]
Description=CodeGeass Scheduler Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
AccuracySec=1s

[Install]
WantedBy=timers.target
"""

    def install(
        self, codegeass_path: str, working_dir: Path | None = None
    ) -> tuple[bool, str]:
        """Install systemd user service and timer."""
        systemd_dir = self._get_systemd_dir()
        service_path = systemd_dir / self.SERVICE_NAME
        timer_path = systemd_dir / self.TIMER_NAME

        try:
            # Create systemd user directory if needed
            systemd_dir.mkdir(parents=True, exist_ok=True)

            # Stop existing timer if running
            subprocess.run(
                ["systemctl", "--user", "stop", self.TIMER_NAME],
                capture_output=True,
                check=False,
            )

            # Write unit files
            service_path.write_text(self._generate_service(codegeass_path))
            timer_path.write_text(self._generate_timer())

            # Reload systemd
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                capture_output=True,
                check=True,
            )

            # Enable and start timer
            subprocess.run(
                ["systemctl", "--user", "enable", "--now", self.TIMER_NAME],
                capture_output=True,
                check=True,
            )

            return True, str(timer_path)

        except subprocess.CalledProcessError as e:
            return False, f"systemctl failed: {e.stderr.decode() if e.stderr else str(e)}"
        except Exception as e:
            return False, str(e)

    def uninstall(self) -> tuple[bool, str]:
        """Uninstall systemd service and timer."""
        systemd_dir = self._get_systemd_dir()
        service_path = systemd_dir / self.SERVICE_NAME
        timer_path = systemd_dir / self.TIMER_NAME

        try:
            # Disable and stop timer
            subprocess.run(
                ["systemctl", "--user", "disable", "--now", self.TIMER_NAME],
                capture_output=True,
                check=False,
            )

            # Remove unit files
            timer_path.unlink(missing_ok=True)
            service_path.unlink(missing_ok=True)

            # Reload systemd
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                capture_output=True,
                check=False,
            )

            return True, "Service and timer removed"

        except Exception as e:
            return False, str(e)

    def status(self) -> SchedulerStatus:
        """Get systemd scheduler status."""
        timer_path = self._get_systemd_dir() / self.TIMER_NAME

        if not timer_path.exists():
            return SchedulerStatus(
                installed=False,
                running=False,
                scheduler_type=self.display_name,
            )

        # Check if timer is active
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", self.TIMER_NAME],
                capture_output=True,
                text=True,
            )
            running = result.returncode == 0
        except Exception:
            running = False

        return SchedulerStatus(
            installed=True,
            running=running,
            scheduler_type=self.display_name,
            details=str(timer_path),
        )

    def get_config(self) -> SchedulerConfig:
        """Get systemd configuration."""
        return SchedulerConfig(
            name=self.name,
            display_name=self.display_name,
            description="Linux systemd user service",
            check_command=f"systemctl --user status {self.TIMER_NAME}",
            stop_command="codegeass uninstall-scheduler",
        )
