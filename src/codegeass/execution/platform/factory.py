"""Factory for creating platform-appropriate handlers."""

import platform
from functools import lru_cache

from codegeass.execution.platform.io_handler import IOHandler, UnixIOHandler, WindowsIOHandler
from codegeass.execution.platform.process_handler import (
    ProcessHandler,
    UnixProcessHandler,
    WindowsProcessHandler,
)


@lru_cache(maxsize=1)
def get_io_handler() -> IOHandler:
    """Get the appropriate I/O handler for the current platform.

    Returns:
        WindowsIOHandler on Windows, UnixIOHandler on other platforms
    """
    if platform.system() == "Windows":
        return WindowsIOHandler()
    return UnixIOHandler()


@lru_cache(maxsize=1)
def get_process_handler() -> ProcessHandler:
    """Get the appropriate process handler for the current platform.

    Returns:
        WindowsProcessHandler on Windows, UnixProcessHandler on other platforms
    """
    if platform.system() == "Windows":
        return WindowsProcessHandler()
    return UnixProcessHandler()
