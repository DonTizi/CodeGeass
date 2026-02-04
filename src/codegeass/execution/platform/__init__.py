"""Platform abstraction layer for cross-platform I/O and process handling."""

from codegeass.execution.platform.factory import get_io_handler, get_process_handler
from codegeass.execution.platform.io_handler import IOHandler, UnixIOHandler, WindowsIOHandler
from codegeass.execution.platform.process_handler import (
    ProcessHandler,
    UnixProcessHandler,
    WindowsProcessHandler,
)

__all__ = [
    "IOHandler",
    "UnixIOHandler",
    "WindowsIOHandler",
    "ProcessHandler",
    "UnixProcessHandler",
    "WindowsProcessHandler",
    "get_io_handler",
    "get_process_handler",
]
