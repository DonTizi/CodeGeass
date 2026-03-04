"""Platform-agnostic I/O handling interface."""

from typing import IO, Protocol, runtime_checkable


@runtime_checkable
class IOHandler(Protocol):
    """Protocol for platform-specific non-blocking I/O."""

    def read_nonblocking(self, stream: IO[str], timeout: float = 0.1) -> str | None:
        """Read from stream without blocking. Returns None if no data."""
        ...


class UnixIOHandler:
    """Unix implementation using select()."""

    def read_nonblocking(self, stream: IO[str], timeout: float = 0.1) -> str | None:
        """Read from stream without blocking using select.

        Args:
            stream: File-like object to read from
            timeout: Maximum time to wait in seconds

        Returns:
            Line read from stream, or None if no data available
        """
        import select

        ready, _, _ = select.select([stream], [], [], timeout)
        if ready:
            line = stream.readline()
            return line if line else None
        return None


class WindowsIOHandler:
    """Windows implementation using threading.

    Windows doesn't support select() on pipes, so we use a threading-based
    approach with a timeout.
    """

    def read_nonblocking(self, stream: IO[str], timeout: float = 0.1) -> str | None:
        """Read from stream without blocking using threading.

        Args:
            stream: File-like object to read from
            timeout: Maximum time to wait in seconds

        Returns:
            Line read from stream, or None if no data available
        """
        import queue
        import threading

        result_queue: queue.Queue[str | None] = queue.Queue()

        def reader() -> None:
            try:
                line = stream.readline()
                result_queue.put(line if line else None)
            except Exception:
                result_queue.put(None)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()

        try:
            return result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
