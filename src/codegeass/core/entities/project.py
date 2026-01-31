"""Project entity for multi-project support."""

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass
class Project:
    """Registered project for multi-project support.

    Projects allow CodeGeass to manage tasks across multiple repositories
    from a single dashboard with per-project skills and aggregated views.
    """

    id: str
    name: str
    path: Path
    description: str = ""
    default_model: str = "sonnet"
    default_timeout: int = 300
    default_autonomous: bool = False
    git_remote: str | None = None
    enabled: bool = True
    use_shared_skills: bool = True
    created_at: str | None = None

    @property
    def config_dir(self) -> Path:
        """Get the config directory for this project."""
        return self.path / "config"

    @property
    def skills_dir(self) -> Path:
        """Get the skills directory for this project."""
        return self.path / ".claude" / "skills"

    @property
    def schedules_file(self) -> Path:
        """Get the schedules file for this project."""
        return self.config_dir / "schedules.yaml"

    @property
    def data_dir(self) -> Path:
        """Get the data directory for this project."""
        return self.path / "data"

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory for this project."""
        return self.data_dir / "logs"

    @property
    def sessions_dir(self) -> Path:
        """Get the sessions directory for this project."""
        return self.data_dir / "sessions"

    @classmethod
    def create(
        cls,
        name: str,
        path: Path,
        description: str = "",
        default_model: str = "sonnet",
        default_timeout: int = 300,
        default_autonomous: bool = False,
        git_remote: str | None = None,
        use_shared_skills: bool = True,
    ) -> Self:
        """Factory method to create a new project with generated ID."""
        from datetime import datetime

        project_id = str(uuid.uuid4())[:8]
        return cls(
            id=project_id,
            name=name,
            path=path.resolve(),
            description=description,
            default_model=default_model,
            default_timeout=default_timeout,
            default_autonomous=default_autonomous,
            git_remote=git_remote,
            enabled=True,
            use_shared_skills=use_shared_skills,
            created_at=datetime.now().isoformat(),
        )

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create project from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            path=Path(data["path"]),
            description=data.get("description", ""),
            default_model=data.get("default_model", "sonnet"),
            default_timeout=data.get("default_timeout", 300),
            default_autonomous=data.get("default_autonomous", False),
            git_remote=data.get("git_remote"),
            enabled=data.get("enabled", True),
            use_shared_skills=data.get("use_shared_skills", True),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "default_model": self.default_model,
            "default_timeout": self.default_timeout,
            "default_autonomous": self.default_autonomous,
            "git_remote": self.git_remote,
            "enabled": self.enabled,
            "use_shared_skills": self.use_shared_skills,
            "created_at": self.created_at,
        }

    def exists(self) -> bool:
        """Check if the project path exists."""
        return self.path.exists()

    def is_initialized(self) -> bool:
        """Check if the project has CodeGeass structure initialized."""
        return self.config_dir.exists() and self.schedules_file.exists()
