"""Registries for skills and templates."""

from collections.abc import Iterator
from pathlib import Path

from codegeass.core.entities import Skill, Template
from codegeass.core.exceptions import SkillNotFoundError, TemplateNotFoundError


class SkillRegistry:
    """Registry for Claude Code skills.

    Scans .claude/skills/ directory for SKILL.md files following
    the Agent Skills (agentskills.io) open standard format.
    """

    _instance: "SkillRegistry | None" = None

    def __init__(self, skills_dir: Path):
        """Initialize with path to skills directory."""
        self._skills_dir = skills_dir
        self._cache: dict[str, Skill] = {}
        self._loaded = False

    @classmethod
    def get_instance(cls, skills_dir: Path | None = None) -> "SkillRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            if skills_dir is None:
                raise ValueError("skills_dir required for first initialization")
            cls._instance = cls(skills_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None

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

    def get(self, name: str) -> Skill:
        """Get a skill by name."""
        self._load_skills()

        if name not in self._cache:
            raise SkillNotFoundError(name)

        return self._cache[name]

    def get_all(self) -> list[Skill]:
        """Get all registered skills."""
        self._load_skills()
        return list(self._cache.values())

    def exists(self, name: str) -> bool:
        """Check if a skill exists."""
        self._load_skills()
        return name in self._cache

    def __iter__(self) -> Iterator[Skill]:
        """Iterate over all skills."""
        self._load_skills()
        return iter(self._cache.values())

    def __len__(self) -> int:
        """Get number of registered skills."""
        self._load_skills()
        return len(self._cache)

    def reload(self) -> None:
        """Reload skills from disk."""
        self._cache.clear()
        self._loaded = False
        self._load_skills()


class TemplateRegistry:
    """Registry for task templates.

    Templates are defined in the settings and provide
    pre-configured task defaults.
    """

    _instance: "TemplateRegistry | None" = None

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._cache: dict[str, Template] = {}

    @classmethod
    def get_instance(cls) -> "TemplateRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None

    def register(self, template: Template) -> None:
        """Register a template."""
        self._cache[template.name] = template

    def register_from_dict(self, data: dict) -> Template:
        """Register a template from dictionary data."""
        template = Template.from_dict(data)
        self.register(template)
        return template

    def get(self, name: str) -> Template:
        """Get a template by name."""
        if name not in self._cache:
            raise TemplateNotFoundError(name)
        return self._cache[name]

    def get_all(self) -> list[Template]:
        """Get all registered templates."""
        return list(self._cache.values())

    def exists(self, name: str) -> bool:
        """Check if a template exists."""
        return name in self._cache

    def unregister(self, name: str) -> bool:
        """Unregister a template. Returns True if it existed."""
        if name in self._cache:
            del self._cache[name]
            return True
        return False

    def __iter__(self) -> Iterator[Template]:
        """Iterate over all templates."""
        return iter(self._cache.values())

    def __len__(self) -> int:
        """Get number of registered templates."""
        return len(self._cache)

    def clear(self) -> None:
        """Clear all registered templates."""
        self._cache.clear()
