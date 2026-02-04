"""Hook models for API."""

from typing import Any

from pydantic import BaseModel, Field


class HookSummary(BaseModel):
    """Summary view of a hook tag."""

    tag: str
    description: str
    location: str  # "project" or "global"
    events: list[str] = Field(default_factory=list)


class Hook(BaseModel):
    """Full hook model."""

    tag: str
    description: str = ""
    hooks: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    location: str | None = None  # "project" or "global"


class HookCreate(BaseModel):
    """Model for creating a new hook."""

    tag: str
    description: str = ""
    hooks: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    global_scope: bool = False


class HookUpdate(BaseModel):
    """Model for updating a hook."""

    description: str | None = None
    hooks: dict[str, list[dict[str, Any]]] | None = None


class HookPreview(BaseModel):
    """Preview of merged hooks."""

    tags: list[str]
    preview: str
    settings: dict[str, Any]


class HookValidation(BaseModel):
    """Hook validation result."""

    tag: str
    valid: bool
    errors: list[str] = Field(default_factory=list)
