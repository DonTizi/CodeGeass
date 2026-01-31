"""Domain entities for CodeGeass.

Each entity is in its own module for single-responsibility:
- skill: Skill entity for Claude Code skills
- template: Template entity for task templates
- prompt: Prompt entity for structured prompts
- task: Task entity for scheduled tasks
- project: Project entity for multi-project support
"""

from codegeass.core.entities.project import Project
from codegeass.core.entities.prompt import Prompt
from codegeass.core.entities.skill import Skill
from codegeass.core.entities.task import Task
from codegeass.core.entities.template import Template

__all__ = [
    "Project",
    "Prompt",
    "Skill",
    "Task",
    "Template",
]
