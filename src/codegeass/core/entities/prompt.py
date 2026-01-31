"""Prompt entity for structured prompts."""

from dataclasses import dataclass
from typing import Any

from jinja2 import Template as Jinja2Template


@dataclass
class Prompt:
    """Structured prompt with system, task, and context."""

    task: str
    system: str = ""
    context: str | None = None

    def render(self, variables: dict[str, Any] | None = None) -> str:
        """Render full prompt with Jinja2 templating."""
        vars_dict = variables or {}

        parts = []
        if self.system:
            template = Jinja2Template(self.system)
            parts.append(template.render(**vars_dict))

        if self.context:
            template = Jinja2Template(self.context)
            parts.append(template.render(**vars_dict))

        template = Jinja2Template(self.task)
        parts.append(template.render(**vars_dict))

        return "\n\n".join(parts)
