"""Platform-agnostic process management interface."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessHandler(Protocol):
    """Protocol for platform-specific process control."""

    def terminate(self, pid: int, force: bool = False) -> bool:
        """Terminate a process. Returns True if successful."""
        ...

    def is_running(self, pid: int) -> bool:
        """Check if a process is running."""
        ...


class UnixProcessHandler:
    """Unix implementation using signals."""

    def terminate(self, pid: int, force: bool = False) -> bool:
        """Terminate a process using SIGTERM or SIGKILL.

        Args:
            pid: Process ID to terminate
            force: If True, use SIGKILL instead of SIGTERM

        Returns:
            True if signal was sent successfully
        """
        import os
        import signal

        try:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            return True
        except OSError:
            return False

    def is_running(self, pid: int) -> bool:
        """Check if a process is running using signal 0.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running
        """
        import os

        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


class WindowsProcessHandler:
    """Windows implementation using taskkill."""

    def terminate(self, pid: int, force: bool = False) -> bool:
        """Terminate a process using taskkill.

        Args:
            pid: Process ID to terminate
            force: If True, use /F flag for forceful termination

        Returns:
            True if taskkill completed successfully
        """
        import subprocess

        args = ["taskkill", "/PID", str(pid)]
        if force:
            args.append("/F")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return result.returncode == 0
        except Exception:
            return False

    def is_running(self, pid: int) -> bool:
        """Check if a process is running using tasklist.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running
        """
        import subprocess

        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return str(pid) in result.stdout
        except Exception:
            return False
