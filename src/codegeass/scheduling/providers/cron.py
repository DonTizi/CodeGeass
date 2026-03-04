"""Unix cron scheduler provider (fallback)."""

import shutil
import subprocess
from pathlib import Path

from codegeass.scheduling.providers.base import (
    SchedulerConfig,
    SchedulerProvider,
    SchedulerStatus,
)


class CronProvider(SchedulerProvider):
    """Unix cron fallback implementation."""

    CRON_MARKER = "codegeass scheduler run-due"

    @property
    def name(self) -> str:
        return "cron"

    @property
    def display_name(self) -> str:
        return "cron (Unix)"

    def is_available(self) -> bool:
        """Check if crontab is available."""
        return shutil.which("crontab") is not None

    def _get_crontab(self) -> str:
        """Get current crontab content."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""

    def _set_crontab(self, content: str) -> bool:
        """Set crontab content."""
        try:
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                text=True,
            )
            process.communicate(input=content)
            return process.returncode == 0
        except Exception:
            return False

    def install(
        self, codegeass_path: str, working_dir: Path | None = None
    ) -> tuple[bool, str]:
        """Install cron job."""
        cron_line = f"* * * * * {codegeass_path} scheduler run-due >> /tmp/codegeass.log 2>&1"

        try:
            current_crontab = self._get_crontab()

            # Check if already installed
            if self.CRON_MARKER in current_crontab:
                return True, "Already installed in crontab"

            # Add new cron line
            new_crontab = current_crontab.rstrip() + "\n" + cron_line + "\n"

            if self._set_crontab(new_crontab):
                return True, "Installed in crontab"
            return False, "Failed to update crontab"

        except Exception as e:
            return False, str(e)

    def uninstall(self) -> tuple[bool, str]:
        """Remove cron job."""
        try:
            current_crontab = self._get_crontab()

            if "codegeass" not in current_crontab:
                return True, "Not installed"

            # Remove codegeass lines
            new_lines = [
                line for line in current_crontab.splitlines() if "codegeass" not in line
            ]
            new_crontab = "\n".join(new_lines) + "\n"

            if self._set_crontab(new_crontab):
                return True, "Cron entry removed"
            return False, "Failed to update crontab"

        except Exception as e:
            return False, str(e)

    def status(self) -> SchedulerStatus:
        """Get cron scheduler status."""
        current_crontab = self._get_crontab()
        installed = "codegeass" in current_crontab

        return SchedulerStatus(
            installed=installed,
            running=installed,  # If installed in cron, it's "running"
            scheduler_type=self.display_name,
            details="Crontab entry" if installed else None,
        )

    def get_config(self) -> SchedulerConfig:
        """Get cron configuration."""
        return SchedulerConfig(
            name=self.name,
            display_name=self.display_name,
            description="Unix cron job scheduler",
            check_command="crontab -l | grep codegeass",
            stop_command="codegeass uninstall-scheduler",
        )
