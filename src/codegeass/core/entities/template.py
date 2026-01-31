"""Template entity for task templates."""

from dataclasses import dataclass, field
from typing import Any, Self

from jinja2 import Template as Jinja2Template


@dataclass
class Template:
    """Task template with default settings."""

    name: str
    description: str
    prompt_template: str = ""  # Jinja2 template string
    default_skills: list[str] = field(default_factory=list)
    default_tools: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    model: str = "sonnet"
    autonomous: bool = False
    timeout: int = 300

    def render_prompt(self, variables: dict[str, Any] | None = None) -> str:
        """Render prompt template with variables."""
        merged_vars = {**self.variables, **(variables or {})}
        template = Jinja2Template(self.prompt_template)
        return template.render(**merged_vars)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create template from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            prompt_template=data.get("prompt_template", ""),
            default_skills=data.get("default_skills", []),
            default_tools=data.get("default_tools", []),
            variables=data.get("variables", {}),
            model=data.get("model", "sonnet"),
            autonomous=data.get("autonomous", False),
            timeout=data.get("timeout", 300),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "prompt_template": self.prompt_template,
            "default_skills": self.default_skills,
            "default_tools": self.default_tools,
            "variables": self.variables,
            "model": self.model,
            "autonomous": self.autonomous,
            "timeout": self.timeout,
        }
