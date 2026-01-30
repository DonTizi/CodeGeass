"""Skill service wrapping SkillRegistry."""


from codegeass.core.entities import Skill as CoreSkill
from codegeass.factory.registry import SkillRegistry

from ..models import Skill, SkillSummary


class SkillService:
    """Service for managing skills."""

    def __init__(self, skill_registry: SkillRegistry):
        self.skill_registry = skill_registry

    def _core_to_api(self, skill: CoreSkill) -> Skill:
        """Convert core Skill to API Skill model."""
        dynamic_commands = []
        try:
            dynamic_commands = skill.get_dynamic_commands()
        except Exception:
            pass

        return Skill(
            name=skill.name,
            path=str(skill.path),
            description=skill.description,
            allowed_tools=skill.allowed_tools or [],
            context=skill.context,
            agent=skill.agent,
            disable_model_invocation=skill.disable_model_invocation,
            content=skill.content,
            dynamic_commands=dynamic_commands,
        )

    def _core_to_summary(self, skill: CoreSkill) -> SkillSummary:
        """Convert core Skill to API SkillSummary model."""
        return SkillSummary(
            name=skill.name,
            description=skill.description,
            context=skill.context,
            has_agent=skill.agent is not None,
        )

    def list_skills(self) -> list[SkillSummary]:
        """Get all skills (summary view)."""
        skills = self.skill_registry.get_all()
        return [self._core_to_summary(s) for s in skills]

    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name."""
        try:
            skill = self.skill_registry.get(name)
            return self._core_to_api(skill)
        except Exception:
            return None

    def skill_exists(self, name: str) -> bool:
        """Check if a skill exists."""
        return self.skill_registry.exists(name)

    def reload_skills(self) -> list[SkillSummary]:
        """Reload skills from disk."""
        self.skill_registry.reload()
        return self.list_skills()

    def render_skill_content(self, name: str, arguments: str = "") -> str | None:
        """Render skill content with arguments."""
        try:
            skill = self.skill_registry.get(name)
            return skill.render_content(arguments)
        except Exception:
            return None
