"""Windows Task Scheduler provider."""

import subprocess
from pathlib import Path

from codegeass.scheduling.providers.base import (
    SchedulerConfig,
    SchedulerProvider,
    SchedulerStatus,
)


class WindowsTaskSchedulerProvider(SchedulerProvider):
    """Windows Task Scheduler implementation using schtasks.exe."""

    TASK_NAME = "CodeGeassScheduler"

    @property
    def name(self) -> str:
        return "windows"

    @property
    def display_name(self) -> str:
        return "Windows Task Scheduler"

    def _get_creation_flags(self) -> int:
        """Get subprocess creation flags to hide window on Windows."""
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)

    def is_available(self) -> bool:
        """Check if schtasks.exe is available."""
        try:
            result = subprocess.run(
                ["schtasks", "/?"],
                capture_output=True,
                creationflags=self._get_creation_flags(),
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _generate_task_xml(self, codegeass_path: str, working_dir: Path | None) -> str:
        """Generate Windows Task Scheduler XML configuration."""
        wd = str(working_dir) if working_dir else ""

        return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT1M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2024-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{codegeass_path}</Command>
      <Arguments>scheduler run-due</Arguments>
      <WorkingDirectory>{wd}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    def install(
        self, codegeass_path: str, working_dir: Path | None = None
    ) -> tuple[bool, str]:
        """Install Windows Task Scheduler task."""
        creation_flags = self._get_creation_flags()

        try:
            # Delete existing task if present
            subprocess.run(
                ["schtasks", "/Delete", "/TN", self.TASK_NAME, "/F"],
                capture_output=True,
                creationflags=creation_flags,
            )

            # Generate XML configuration
            xml_content = self._generate_task_xml(codegeass_path, working_dir)

            # Write XML to temp file (schtasks needs a file, not stdin)
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".xml", delete=False, encoding="utf-16"
            ) as f:
                f.write(xml_content)
                xml_path = f.name

            try:
                # Create task from XML file
                result = subprocess.run(
                    ["schtasks", "/Create", "/TN", self.TASK_NAME, "/XML", xml_path],
                    capture_output=True,
                    text=True,
                    creationflags=creation_flags,
                )

                if result.returncode == 0:
                    return True, f"Task '{self.TASK_NAME}' created"
                return False, result.stderr or result.stdout

            finally:
                # Clean up temp file
                Path(xml_path).unlink(missing_ok=True)

        except Exception as e:
            return False, str(e)

    def uninstall(self) -> tuple[bool, str]:
        """Remove Windows Task Scheduler task."""
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", self.TASK_NAME, "/F"],
                capture_output=True,
                text=True,
                creationflags=self._get_creation_flags(),
            )

            if result.returncode == 0:
                return True, "Task removed"

            # Check if task didn't exist
            if "does not exist" in result.stderr.lower():
                return True, "Not installed"

            return False, result.stderr or result.stdout

        except Exception as e:
            return False, str(e)

    def status(self) -> SchedulerStatus:
        """Get Windows Task Scheduler status."""
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.TASK_NAME, "/V", "/FO", "LIST"],
                capture_output=True,
                text=True,
                creationflags=self._get_creation_flags(),
            )

            if result.returncode == 0:
                # Parse output to check if task is running/enabled
                output = result.stdout.lower()
                running = "running" in output
                enabled = "enabled" in output

                return SchedulerStatus(
                    installed=True,
                    running=running or enabled,
                    scheduler_type=self.display_name,
                    details=f"Task: {self.TASK_NAME}",
                )

            return SchedulerStatus(
                installed=False,
                running=False,
                scheduler_type=self.display_name,
            )

        except Exception:
            return SchedulerStatus(
                installed=False,
                running=False,
                scheduler_type=self.display_name,
            )

    def get_config(self) -> SchedulerConfig:
        """Get Windows Task Scheduler configuration."""
        return SchedulerConfig(
            name=self.name,
            display_name=self.display_name,
            description="Windows built-in task scheduler",
            check_command=f'schtasks /Query /TN "{self.TASK_NAME}"',
            stop_command="codegeass uninstall-scheduler",
        )
