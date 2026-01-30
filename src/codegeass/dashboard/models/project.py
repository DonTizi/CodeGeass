"""Pydantic models for Project API."""

from pydantic import BaseModel, Field


class Project(BaseModel):
    """Project response model."""

    id: str
    name: str
    path: str
    description: str = ""
    default_model: str = "sonnet"
    default_timeout: int = 300
    default_autonomous: bool = False
    git_remote: str | None = None
    enabled: bool = True
    use_shared_skills: bool = True
    created_at: str | None = None

    # Computed fields (added by service)
    task_count: int = 0
    skill_count: int = 0
    is_default: bool = False
    exists: bool = True
    is_initialized: bool = True


class ProjectSummary(BaseModel):
    """Project summary for list views."""

    id: str
    name: str
    path: str
    enabled: bool = True
    is_default: bool = False
    task_count: int = 0
    skill_count: int = 0


class ProjectCreate(BaseModel):
    """Request model for creating/registering a project."""

    path: str = Field(..., description="Absolute path to the project directory")
    name: str | None = Field(None, description="Project name (defaults to directory name)")
    description: str = ""
    default_model: str = "sonnet"
    default_timeout: int = 300
    default_autonomous: bool = False
    use_shared_skills: bool = True


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""

    name: str | None = None
    description: str | None = None
    default_model: str | None = None
    default_timeout: int | None = None
    default_autonomous: bool | None = None
    use_shared_skills: bool | None = None
    enabled: bool | None = None


class TaskWithProject(BaseModel):
    """Task with project information for aggregated views."""

    # Task fields
    id: str
    name: str
    schedule: str
    working_dir: str
    skill: str | None = None
    prompt: str | None = None
    model: str = "sonnet"
    autonomous: bool = False
    timeout: int = 300
    enabled: bool = True
    last_run: str | None = None
    last_status: str | None = None
    next_run: str | None = None
    schedule_description: str | None = None

    # Project fields
    project_id: str | None = None
    project_name: str | None = None


class SkillWithSource(BaseModel):
    """Skill with source information."""

    name: str
    description: str
    source: str  # "project" or "shared"
    path: str
    allowed_tools: list[str] = []
    context: str = "inline"
    agent: str | None = None
