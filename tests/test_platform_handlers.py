"""Tests for platform abstraction layer."""

import os
import platform

import pytest

from codegeass.execution.platform import (
    IOHandler,
    ProcessHandler,
    UnixIOHandler,
    UnixProcessHandler,
    WindowsIOHandler,
    WindowsProcessHandler,
    get_io_handler,
    get_process_handler,
)


class TestIOHandler:
    """Tests for IOHandler implementations."""

    def test_handler_creation(self) -> None:
        """Test that get_io_handler returns a valid handler."""
        handler = get_io_handler()
        assert handler is not None
        assert hasattr(handler, "read_nonblocking")

    def test_handler_type_by_platform(self) -> None:
        """Test correct handler type is returned for platform."""
        handler = get_io_handler()
        if platform.system() == "Windows":
            assert isinstance(handler, WindowsIOHandler)
        else:
            assert isinstance(handler, UnixIOHandler)

    def test_handler_protocol_compliance(self) -> None:
        """Test handlers comply with IOHandler protocol."""
        unix_handler = UnixIOHandler()
        windows_handler = WindowsIOHandler()

        # Both should have read_nonblocking method
        assert hasattr(unix_handler, "read_nonblocking")
        assert hasattr(windows_handler, "read_nonblocking")


class TestProcessHandler:
    """Tests for ProcessHandler implementations."""

    def test_handler_creation(self) -> None:
        """Test that get_process_handler returns a valid handler."""
        handler = get_process_handler()
        assert handler is not None
        assert hasattr(handler, "terminate")
        assert hasattr(handler, "is_running")

    def test_handler_type_by_platform(self) -> None:
        """Test correct handler type is returned for platform."""
        handler = get_process_handler()
        if platform.system() == "Windows":
            assert isinstance(handler, WindowsProcessHandler)
        else:
            assert isinstance(handler, UnixProcessHandler)

    def test_current_process_running(self) -> None:
        """Test is_running returns True for current process."""
        handler = get_process_handler()
        current_pid = os.getpid()
        assert handler.is_running(current_pid) is True

    def test_nonexistent_process_not_running(self) -> None:
        """Test is_running returns False for nonexistent process."""
        handler = get_process_handler()
        # Use an unlikely PID that should not exist
        fake_pid = 99999999
        assert handler.is_running(fake_pid) is False

    def test_handler_protocol_compliance(self) -> None:
        """Test handlers comply with ProcessHandler protocol."""
        unix_handler = UnixProcessHandler()
        windows_handler = WindowsProcessHandler()

        # Both should have required methods
        assert hasattr(unix_handler, "terminate")
        assert hasattr(unix_handler, "is_running")
        assert hasattr(windows_handler, "terminate")
        assert hasattr(windows_handler, "is_running")
