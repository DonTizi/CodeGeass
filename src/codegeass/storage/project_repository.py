"""Project repository implementation for multi-project support."""

from pathlib import Path
from typing import Any

import yaml

from codegeass.core.entities import Project


class ProjectRepository:
    """Repository for project registry at ~/.codegeass/projects.yaml.

    The project registry is a global configuration file that tracks all
    registered projects. Each project has its own config, skills, and data.
    """

    DEFAULT_REGISTRY_PATH = Path.home() / ".codegeass" / "projects.yaml"
    CURRENT_VERSION = 1

    def __init__(self, registry_file: Path | None = None):
        """Initialize with path to projects.yaml.

        Args:
            registry_file: Path to the registry file. Defaults to ~/.codegeass/projects.yaml
        """
        self._file = registry_file or self.DEFAULT_REGISTRY_PATH

    def _read(self) -> dict[str, Any]:
        """Read the registry file."""
        if not self._file.exists():
            return {
                "version": self.CURRENT_VERSION,
                "default_project": None,
                "shared_skills_dir": str(Path.home() / ".codegeass" / "skills"),
                "projects": [],
            }

        with open(self._file) as f:
            content = yaml.safe_load(f)
            return (
                content
                if content
                else {
                    "version": self.CURRENT_VERSION,
                    "default_project": None,
                    "shared_skills_dir": str(Path.home() / ".codegeass" / "skills"),
                    "projects": [],
                }
            )

    def _write(self, data: dict[str, Any]) -> None:
        """Write the registry file."""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def find_all(self) -> list[Project]:
        """Find all registered projects."""
        data = self._read()
        return [Project.from_dict(item) for item in data.get("projects", [])]

    def find_enabled(self) -> list[Project]:
        """Find all enabled projects."""
        return [project for project in self.find_all() if project.enabled]

    def find_by_id(self, project_id: str) -> Project | None:
        """Find project by ID."""
        for project in self.find_all():
            if project.id == project_id:
                return project
        return None

    def find_by_name(self, name: str) -> Project | None:
        """Find project by name (case-insensitive)."""
        name_lower = name.lower()
        for project in self.find_all():
            if project.name.lower() == name_lower:
                return project
        return None

    def find_by_path(self, path: Path) -> Project | None:
        """Find project by path."""
        path_resolved = path.resolve()
        for project in self.find_all():
            if project.path == path_resolved:
                return project
        return None

    def find_by_id_or_name(self, identifier: str) -> Project | None:
        """Find project by ID or name."""
        # Try ID first
        project = self.find_by_id(identifier)
        if project:
            return project
        # Try name
        return self.find_by_name(identifier)

    def save(self, project: Project) -> None:
        """Save a new project or update existing one."""
        data = self._read()
        projects = data.get("projects", [])

        # Check if project already exists (by ID)
        for i, item in enumerate(projects):
            if item.get("id") == project.id:
                projects[i] = project.to_dict()
                data["projects"] = projects
                self._write(data)
                return

        # Add new project
        projects.append(project.to_dict())
        data["projects"] = projects
        self._write(data)

    def delete(self, project_id: str) -> bool:
        """Delete a project by ID. Returns True if deleted.

        Note: This only removes the project from the registry.
        The actual project files are not deleted.
        """
        data = self._read()
        projects = data.get("projects", [])
        original_len = len(projects)

        projects = [item for item in projects if item.get("id") != project_id]

        if len(projects) < original_len:
            data["projects"] = projects
            # Clear default if deleted project was default
            if data.get("default_project") == project_id:
                data["default_project"] = None
            self._write(data)
            return True
        return False

    def delete_by_name(self, name: str) -> bool:
        """Delete a project by name. Returns True if deleted."""
        project = self.find_by_name(name)
        if project:
            return self.delete(project.id)
        return False

    def get_default_project_id(self) -> str | None:
        """Get the default project ID."""
        data = self._read()
        return data.get("default_project")

    def get_default_project(self) -> Project | None:
        """Get the default project."""
        default_id = self.get_default_project_id()
        if default_id:
            return self.find_by_id(default_id)
        return None

    def set_default_project(self, project_id: str) -> None:
        """Set the default project by ID.

        Raises:
            ValueError: If project with given ID doesn't exist
        """
        project = self.find_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        data = self._read()
        data["default_project"] = project_id
        self._write(data)

    def set_default_project_by_name(self, name: str) -> None:
        """Set the default project by name.

        Raises:
            ValueError: If project with given name doesn't exist
        """
        project = self.find_by_name(name)
        if not project:
            raise ValueError(f"Project not found: {name}")
        self.set_default_project(project.id)

    def clear_default_project(self) -> None:
        """Clear the default project setting."""
        data = self._read()
        data["default_project"] = None
        self._write(data)

    def get_shared_skills_dir(self) -> Path | None:
        """Get the shared skills directory path."""
        data = self._read()
        shared_dir = data.get("shared_skills_dir")
        if shared_dir:
            path = Path(shared_dir).expanduser()
            return path if path.exists() else None
        return None

    def set_shared_skills_dir(self, path: Path) -> None:
        """Set the shared skills directory path."""
        data = self._read()
        data["shared_skills_dir"] = str(path.resolve())
        self._write(data)

    def exists(self) -> bool:
        """Check if the registry file exists."""
        return self._file.exists()

    def is_empty(self) -> bool:
        """Check if there are no registered projects."""
        return len(self.find_all()) == 0

    def enable(self, project_id: str) -> bool:
        """Enable a project. Returns True if successful."""
        project = self.find_by_id(project_id)
        if project:
            project.enabled = True
            self.save(project)
            return True
        return False

    def disable(self, project_id: str) -> bool:
        """Disable a project. Returns True if successful."""
        project = self.find_by_id(project_id)
        if project:
            project.enabled = False
            self.save(project)
            return True
        return False
