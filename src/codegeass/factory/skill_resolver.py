"""Chained skill resolution for multi-project and multi-platform support.

Implements the Chain of Responsibility pattern for skill resolution:
1. Project skills (platform-specific) are checked first
2. Global skills (platform-specific) are checked as fallback

Supports multiple AI agent platforms:
- Claude Code: ~/.claude/skills/ + .claude/skills/
- OpenAI Codex: ~/.codex/skills/ + .codex/skills/
"""

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from codegeass.core.entities import Skill
from codegeass.core.exceptions import SkillNotFoundError


class Platform(Enum):
    """Supported AI agent platforms."""

    CLAUDE = "claude"
    CODEX = "codex"


@dataclass(frozen=True)
class PlatformConfig:
    """Configuration for a platform's skill directories."""

    name: str
    global_dir: Path
    project_subdir: str  # e.g., ".claude/skills" or ".codex/skills"


# Platform configurations
PLATFORMS: dict[Platform, PlatformConfig] = {
    Platform.CLAUDE: PlatformConfig(
        name="claude",
        global_dir=Path.home() / ".claude" / "skills",
        project_subdir=".claude/skills",
    ),
    Platform.CODEX: PlatformConfig(
        name="codex",
        global_dir=Path.home() / ".codex" / "skills",
        project_subdir=".codex/skills",
    ),
}


def get_platform(name: str) -> Platform:
    """Get Platform enum from string name.

    Args:
        name: Platform name (e.g., "claude", "codex")

    Returns:
        Platform enum value

    Raises:
        ValueError: If platform name is not valid
    """
    try:
        return Platform(name.lower())
    except ValueError:
        valid = [p.value for p in Platform]
        raise ValueError(f"Invalid platform: {name}. Valid platforms: {valid}")


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
            source: Label for this resolver (e.g., "project-claude", "global-codex")
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


class PlatformSkillResolver(DirectorySkillResolver):
    """Resolves skills from a platform-specific directory.

    Used for both project-level and global platform skills.
    """

    def __init__(self, skills_dir: Path, platform: Platform, scope: str):
        """Initialize with platform-specific directory.

        Args:
            skills_dir: Path to the skills directory
            platform: The AI platform (CLAUDE, CODEX)
            scope: Either "project" or "global"
        """
        source = f"{scope}-{platform.value}"
        super().__init__(skills_dir, source=source)
        self._platform = platform
        self._scope = scope

    @property
    def platform(self) -> Platform:
        """Get the platform for this resolver."""
        return self._platform

    @property
    def scope(self) -> str:
        """Get the scope (project or global)."""
        return self._scope


class ChainedSkillRegistry:
    """Multi-platform skill registry with priority chain.

    Resolves skills in order:
    1. Project skills from each platform (in platform order)
    2. Global skills from each platform (in platform order)

    This allows projects to override global skills while still
    having access to common skills from multiple platforms.
    """

    def __init__(
        self,
        project_dir: Path | None = None,
        platforms: list[Platform] | None = None,
        include_global: bool = True,
        # Legacy parameters for backward compatibility
        project_skills_dir: Path | None = None,
        shared_skills_dir: Path | None = None,
        use_shared: bool = True,
    ):
        """Initialize with skill directories.

        Args:
            project_dir: Project root directory (new multi-platform mode)
            platforms: Platforms to use (default: [CLAUDE, CODEX])
            include_global: Include global skills directories
            project_skills_dir: Legacy: Path to project's skills directory
            shared_skills_dir: Legacy: Path to shared skills directory
            use_shared: Legacy: Whether to use shared skills as fallback
        """
        self._resolvers: list[DirectorySkillResolver] = []
        self._platforms = platforms or [Platform.CLAUDE, Platform.CODEX]

        # Check if using new multi-platform mode
        if project_dir is not None:
            self._init_multiplatform(project_dir, include_global)
        else:
            # Legacy mode for backward compatibility
            self._init_legacy(project_skills_dir, shared_skills_dir, use_shared)

    def _init_multiplatform(self, project_dir: Path, include_global: bool) -> None:
        """Initialize resolvers for multi-platform mode."""
        # Add project skills first (higher priority)
        for platform in self._platforms:
            config = PLATFORMS[platform]
            project_skills = project_dir / config.project_subdir
            self._resolvers.append(
                PlatformSkillResolver(project_skills, platform, scope="project")
            )

        # Add global skills (lower priority)
        if include_global:
            for platform in self._platforms:
                config = PLATFORMS[platform]
                self._resolvers.append(
                    PlatformSkillResolver(config.global_dir, platform, scope="global")
                )

    def _init_legacy(
        self,
        project_skills_dir: Path | None,
        shared_skills_dir: Path | None,
        use_shared: bool,
    ) -> None:
        """Initialize resolvers for legacy mode (backward compatibility)."""
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

        Project skills take precedence over global skills with the same name.
        Earlier platforms take precedence over later platforms.
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

        Returns tuples of (skill, source) where source indicates
        platform and scope (e.g., "project-claude", "global-codex").
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
        """Get the source of a skill (e.g., project-claude, global-codex).

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
    def platforms(self) -> list[Platform]:
        """Get the list of platforms."""
        return self._platforms

    @property
    def project_skills_count(self) -> int:
        """Get the number of project-specific skills."""
        count = 0
        for resolver in self._resolvers:
            if resolver.source.startswith("project"):
                count += len(resolver.get_all())
        return count

    @property
    def shared_skills_count(self) -> int:
        """Get the number of shared/global skills."""
        count = 0
        seen: set[str] = set()
        # First mark project skills as seen
        for resolver in self._resolvers:
            if resolver.source.startswith("project"):
                for skill in resolver.get_all():
                    seen.add(skill.name)
        # Count unique global skills
        for resolver in self._resolvers:
            if resolver.source.startswith("global") or resolver.source == "shared":
                for skill in resolver.get_all():
                    if skill.name not in seen:
                        seen.add(skill.name)
                        count += 1
        return count

    def get_skills_by_platform(self, platform: Platform) -> list[Skill]:
        """Get all skills from a specific platform."""
        skills = []
        seen: set[str] = set()
        for resolver in self._resolvers:
            if isinstance(resolver, PlatformSkillResolver):
                if resolver.platform == platform:
                    for skill in resolver.get_all():
                        if skill.name not in seen:
                            seen.add(skill.name)
                            skills.append(skill)
        return skills

    def get_skills_by_scope(self, scope: str) -> list[Skill]:
        """Get all skills from a specific scope (project or global)."""
        skills = []
        seen: set[str] = set()
        for resolver in self._resolvers:
            if resolver.source.startswith(scope):
                for skill in resolver.get_all():
                    if skill.name not in seen:
                        seen.add(skill.name)
                        skills.append(skill)
        return skills
