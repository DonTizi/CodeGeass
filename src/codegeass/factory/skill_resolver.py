"""Chained skill resolution for multi-project support.

Implements the Chain of Responsibility pattern for skill resolution:
Project skills are checked first, then shared skills as fallback.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from codegeass.core.entities import Skill
from codegeass.core.exceptions import SkillNotFoundError


class SkillResolverProtocol(Protocol):
    """Protocol for skill resolvers."""

    def get(self, name: str) -> Skill | None:
        """Get a skill by name. Returns None if not found."""
        ...

    def get_all(self) -> list[Skill]:
        """Get all skills from this resolver."""
        ...

    def exists(self, name: str) -> bool:
        """Check if a skill exists."""
        ...


class DirectorySkillResolver:
    """Resolves skills from a specific directory.

    This is the base resolver that scans a single skills directory
    for SKILL.md files.
    """

    def __init__(self, skills_dir: Path, source: str = "local"):
        """Initialize with path to skills directory.

        Args:
            skills_dir: Path to the skills directory
            source: Label for this resolver (e.g., "project", "shared")
        """
        self._skills_dir = skills_dir
        self._source = source
        self._cache: dict[str, Skill] = {}
        self._loaded = False

    def _load_skills(self) -> None:
        """Load all skills from directory."""
        if self._loaded:
            return

        if not self._skills_dir.exists():
            self._loaded = True
            return

        for skill_dir in self._skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        skill = Skill.from_skill_dir(skill_dir)
                        self._cache[skill.name] = skill
                    except Exception:
                        # Skip invalid skills
                        pass

        self._loaded = True

    def get(self, name: str) -> Skill | None:
        """Get a skill by name. Returns None if not found."""
        self._load_skills()
        return self._cache.get(name)

    def get_all(self) -> list[Skill]:
        """Get all skills from this directory."""
        self._load_skills()
        return list(self._cache.values())

    def exists(self, name: str) -> bool:
        """Check if a skill exists."""
        self._load_skills()
        return name in self._cache

    def reload(self) -> None:
        """Reload skills from disk."""
        self._cache.clear()
        self._loaded = False
        self._load_skills()

    @property
    def source(self) -> str:
        """Get the source label for this resolver."""
        return self._source

    @property
    def skills_dir(self) -> Path:
        """Get the skills directory."""
        return self._skills_dir


class ProjectSkillResolver(DirectorySkillResolver):
    """Resolves skills from a project's .claude/skills/ directory."""

    def __init__(self, skills_dir: Path):
        super().__init__(skills_dir, source="project")


class SharedSkillResolver(DirectorySkillResolver):
    """Resolves skills from the shared ~/.codegeass/skills/ directory."""

    def __init__(self, skills_dir: Path):
        super().__init__(skills_dir, source="shared")


class ChainedSkillRegistry:
    """Chained skill registry implementing Chain of Responsibility.

    Resolves skills in order:
    1. Project skills (from project's .claude/skills/)
    2. Shared skills (from ~/.codegeass/skills/) - if enabled

    This allows projects to override shared skills while still
    having access to common skills.
    """

    def __init__(
        self,
        project_skills_dir: Path | None = None,
        shared_skills_dir: Path | None = None,
        use_shared: bool = True,
    ):
        """Initialize with skill directories.

        Args:
            project_skills_dir: Path to project's skills directory
            shared_skills_dir: Path to shared skills directory
            use_shared: Whether to use shared skills as fallback
        """
        self._resolvers: list[DirectorySkillResolver] = []
        self._use_shared = use_shared

        # Add project resolver if directory specified
        if project_skills_dir:
            self._resolvers.append(ProjectSkillResolver(project_skills_dir))

        # Add shared resolver if enabled and directory specified
        if use_shared and shared_skills_dir:
            self._resolvers.append(SharedSkillResolver(shared_skills_dir))

    def get(self, name: str) -> Skill:
        """Get a skill by name.

        Searches resolvers in order until skill is found.

        Raises:
            SkillNotFoundError: If skill is not found in any resolver
        """
        for resolver in self._resolvers:
            skill = resolver.get(name)
            if skill:
                return skill

        raise SkillNotFoundError(name)

    def get_optional(self, name: str) -> Skill | None:
        """Get a skill by name, returning None if not found."""
        for resolver in self._resolvers:
            skill = resolver.get(name)
            if skill:
                return skill
        return None

    def get_all(self) -> list[Skill]:
        """Get all skills from all resolvers, deduplicated.

        Project skills take precedence over shared skills with the same name.
        """
        seen: set[str] = set()
        skills: list[Skill] = []

        for resolver in self._resolvers:
            for skill in resolver.get_all():
                if skill.name not in seen:
                    seen.add(skill.name)
                    skills.append(skill)

        return skills

    def get_all_with_source(self) -> list[tuple[Skill, str]]:
        """Get all skills with their source labels.

        Returns tuples of (skill, source) where source is "project" or "shared".
        """
        seen: set[str] = set()
        skills: list[tuple[Skill, str]] = []

        for resolver in self._resolvers:
            for skill in resolver.get_all():
                if skill.name not in seen:
                    seen.add(skill.name)
                    skills.append((skill, resolver.source))

        return skills

    def exists(self, name: str) -> bool:
        """Check if a skill exists in any resolver."""
        return any(resolver.exists(name) for resolver in self._resolvers)

    def get_source(self, name: str) -> str | None:
        """Get the source of a skill (project/shared).

        Returns None if skill is not found.
        """
        for resolver in self._resolvers:
            if resolver.exists(name):
                return resolver.source
        return None

    def reload(self) -> None:
        """Reload all resolvers."""
        for resolver in self._resolvers:
            resolver.reload()

    def __iter__(self) -> Iterator[Skill]:
        """Iterate over all skills."""
        return iter(self.get_all())

    def __len__(self) -> int:
        """Get total number of unique skills."""
        return len(self.get_all())

    @property
    def resolvers(self) -> list[DirectorySkillResolver]:
        """Get the list of resolvers."""
        return self._resolvers

    @property
    def project_skills_count(self) -> int:
        """Get the number of project-specific skills."""
        for resolver in self._resolvers:
            if resolver.source == "project":
                return len(resolver.get_all())
        return 0

    @property
    def shared_skills_count(self) -> int:
        """Get the number of shared skills."""
        for resolver in self._resolvers:
            if resolver.source == "shared":
                return len(resolver.get_all())
        return 0
