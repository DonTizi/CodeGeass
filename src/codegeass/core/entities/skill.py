"""Skill entity for Claude Code skills."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import yaml

from codegeass.core.exceptions import SkillNotFoundError


@dataclass
class Skill:
    """Reference to a Claude Code skill in .claude/skills/.

    Skills follow the Agent Skills (agentskills.io) open standard format.
    """

    name: str
    path: Path
    description: str
    allowed_tools: list[str] = field(default_factory=list)
    context: str = "inline"  # "inline" or "fork"
    agent: str | None = None
    disable_model_invocation: bool = False
    content: str = ""  # Markdown content (instructions)

    @classmethod
    def from_skill_dir(cls, skill_dir: Path) -> Self:
        """Parse SKILL.md frontmatter and content from a skill directory."""
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            raise SkillNotFoundError(skill_dir.name)

        content = skill_file.read_text()
        return cls.from_skill_content(skill_dir.name, skill_file, content)

    @classmethod
    def from_skill_content(cls, name: str, path: Path, content: str) -> Self:
        """Parse skill from SKILL.md content."""
        frontmatter, markdown_content = cls._parse_frontmatter(content)
        allowed_tools = cls._parse_allowed_tools(frontmatter)

        return cls(
            name=frontmatter.get("name", name),
            path=path,
            description=frontmatter.get("description", ""),
            allowed_tools=allowed_tools,
            context=frontmatter.get("context", "inline"),
            agent=frontmatter.get("agent"),
            disable_model_invocation=frontmatter.get("disable-model-invocation", False),
            content=markdown_content,
        )

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from markdown content."""
        frontmatter: dict = {}
        markdown_content = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    frontmatter = {}
                markdown_content = parts[2].strip()

        return frontmatter, markdown_content

    @staticmethod
    def _parse_allowed_tools(frontmatter: dict) -> list[str]:
        """Parse allowed-tools from frontmatter."""
        allowed_tools_raw = frontmatter.get("allowed-tools", [])
        if isinstance(allowed_tools_raw, str):
            return [t.strip() for t in allowed_tools_raw.split(",")]
        return list(allowed_tools_raw)

    def render_content(self, arguments: str = "") -> str:
        """Render skill content with arguments substitution."""
        return self.content.replace("$ARGUMENTS", arguments)

    def get_dynamic_commands(self) -> list[str]:
        """Extract dynamic context commands (!`command`) from content."""
        pattern = r"!`([^`]+)`"
        return re.findall(pattern, self.content)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "allowed_tools": self.allowed_tools,
            "context": self.context,
            "agent": self.agent,
            "disable_model_invocation": self.disable_model_invocation,
        }
