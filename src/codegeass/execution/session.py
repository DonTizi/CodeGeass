"""Session management for Claude Code executions."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Session:
    """Represents an execution session."""

    id: str
    task_id: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str = "running"
    output: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            finished_at=(
                datetime.fromisoformat(data["finished_at"]) if data.get("finished_at") else None
            ),
            status=data.get("status", "unknown"),
            output=data.get("output", ""),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Manages execution sessions."""

    def __init__(self, sessions_dir: Path):
        """Initialize with sessions directory."""
        self._sessions_dir = sessions_dir
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._current_session: Session | None = None

    def _get_session_file(self, session_id: str) -> Path:
        """Get session file path."""
        return self._sessions_dir / f"{session_id}.json"

    def create_session(self, task_id: str, metadata: dict[str, Any] | None = None) -> Session:
        """Create a new session."""
        session = Session(
            id=str(uuid.uuid4()),
            task_id=task_id,
            started_at=datetime.now(),
            metadata=metadata or {},
        )
        self._save_session(session)
        self._current_session = session
        return session

    def _save_session(self, session: Session) -> None:
        """Save session to disk."""
        session_file = self._get_session_file(session.id)
        with open(session_file, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

    def update_session(
        self,
        session_id: str,
        status: str | None = None,
        output: str | None = None,
        error: str | None = None,
    ) -> Session | None:
        """Update a session."""
        session = self.get_session(session_id)
        if not session:
            return None

        if status:
            session.status = status
        if output is not None:
            session.output = output
        if error is not None:
            session.error = error

        self._save_session(session)
        return session

    def complete_session(
        self, session_id: str, status: str, output: str = "", error: str | None = None
    ) -> Session | None:
        """Mark a session as complete."""
        session = self.get_session(session_id)
        if not session:
            return None

        session.finished_at = datetime.now()
        session.status = status
        session.output = output
        session.error = error

        self._save_session(session)

        if self._current_session and self._current_session.id == session_id:
            self._current_session = None

        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return None

        with open(session_file) as f:
            data = json.load(f)
            return Session.from_dict(data)

    def get_sessions_for_task(self, task_id: str, limit: int = 10) -> list[Session]:
        """Get sessions for a task."""
        sessions = []
        for session_file in self._sessions_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    if data.get("task_id") == task_id:
                        sessions.append(Session.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by started_at descending
        sessions.sort(key=lambda s: s.started_at, reverse=True)
        return sessions[:limit]

    def get_current_session(self) -> Session | None:
        """Get the current running session."""
        return self._current_session

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Remove sessions older than specified days. Returns count removed."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        removed = 0

        for session_file in self._sessions_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    started_at = datetime.fromisoformat(data["started_at"])
                    if started_at < cutoff:
                        session_file.unlink()
                        removed += 1
            except (json.JSONDecodeError, KeyError):
                continue

        return removed
