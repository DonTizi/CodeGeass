"""Skill models for API."""

from pydantic import BaseModel, Field


class SkillSummary(BaseModel):
    """Summary view of a skill."""
    name: str
    description: str
    context: str = "inline"
    has_agent: bool = False


class Skill(BaseModel):
    """Full skill model."""
    name: str
    path: str
    description: str
    allowed_tools: list[str] = Field(default_factory=list)
    context: str = "inline"
    agent: str | None = None
    disable_model_invocation: bool = False
    content: str = ""
    dynamic_commands: list[str] = Field(default_factory=list)
