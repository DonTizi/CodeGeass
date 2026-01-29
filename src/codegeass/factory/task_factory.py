"""Task factory for creating tasks from templates or skills."""

from pathlib import Path
from typing import Any

from codegeass.core.entities import Task
from codegeass.factory.registry import SkillRegistry, TemplateRegistry


class TaskFactory:
    """Factory for creating tasks with various configurations."""

    def __init__(
        self,
        skill_registry: SkillRegistry,
        template_registry: TemplateRegistry | None = None,
    ):
        """Initialize with registries."""
        self._skill_registry = skill_registry
        self._template_registry = template_registry or TemplateRegistry.get_instance()

    def create_from_skill(
        self,
        name: str,
        skill_name: str,
        schedule: str,
        working_dir: Path,
        **overrides: Any,
    ) -> Task:
        """Create a task that invokes a skill.

        Args:
            name: Task name
            skill_name: Name of skill to invoke (from .claude/skills/)
            schedule: CRON expression
            working_dir: Working directory for execution
            **overrides: Additional task configuration

        Returns:
            Configured Task instance
        """
        # Validate skill exists
        skill = self._skill_registry.get(skill_name)

        # Use skill's allowed tools as default
        allowed_tools = overrides.pop("allowed_tools", None) or skill.allowed_tools

        return Task.create(
            name=name,
            schedule=schedule,
            working_dir=working_dir,
            skill=skill_name,
            allowed_tools=allowed_tools,
            **overrides,
        )

    def create_from_template(
        self,
        name: str,
        template_name: str,
        schedule: str,
        working_dir: Path,
        **overrides: Any,
    ) -> Task:
        """Create a task from a template.

        Args:
            name: Task name
            template_name: Name of template to use
            schedule: CRON expression
            working_dir: Working directory for execution
            **overrides: Override template defaults

        Returns:
            Configured Task instance
        """
        template = self._template_registry.get(template_name)

        # Merge template defaults with overrides
        merged = {
            "model": template.model,
            "autonomous": template.autonomous,
            "timeout": template.timeout,
            "allowed_tools": template.default_tools,
            "variables": {**template.variables, **overrides.pop("variables", {})},
        }
        merged.update(overrides)

        # If template has skills, use first as default
        if template.default_skills:
            return Task.create(
                name=name,
                schedule=schedule,
                working_dir=working_dir,
                skill=template.default_skills[0],
                **merged,
            )

        # Otherwise use template prompt
        prompt = template.render_prompt(merged.get("variables", {}))
        return Task.create(
            name=name,
            schedule=schedule,
            working_dir=working_dir,
            prompt=prompt,
            **merged,
        )

    def create_from_prompt(
        self,
        name: str,
        prompt: str,
        schedule: str,
        working_dir: Path,
        **kwargs: Any,
    ) -> Task:
        """Create a task with a direct prompt.

        Args:
            name: Task name
            prompt: Direct prompt text
            schedule: CRON expression
            working_dir: Working directory for execution
            **kwargs: Additional task configuration

        Returns:
            Configured Task instance
        """
        return Task.create(
            name=name,
            schedule=schedule,
            working_dir=working_dir,
            prompt=prompt,
            **kwargs,
        )
