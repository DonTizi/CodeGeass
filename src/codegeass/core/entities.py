"""Domain entities for CodeGeass."""

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

import yaml
from jinja2 import Template as Jinja2Template

from codegeass.core.exceptions import SkillNotFoundError, ValidationError
from codegeass.core.value_objects import CronExpression


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
        # Parse YAML frontmatter
        frontmatter = {}
        markdown_content = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    frontmatter = {}
                markdown_content = parts[2].strip()

        # Parse allowed-tools (can be comma-separated string or list)
        allowed_tools_raw = frontmatter.get("allowed-tools", [])
        if isinstance(allowed_tools_raw, str):
            allowed_tools = [t.strip() for t in allowed_tools_raw.split(",")]
        else:
            allowed_tools = list(allowed_tools_raw)

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

    def render_content(self, arguments: str = "") -> str:
        """Render skill content with arguments substitution.

        Replaces $ARGUMENTS with provided arguments.
        Note: Dynamic context (!`command`) should be handled by executor.
        """
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


@dataclass
class Task:
    """Scheduled task entity."""

    id: str
    name: str
    schedule: str  # CRON expression
    working_dir: Path

    # Execution configuration
    skill: str | None = None  # Reference to skill name
    prompt: str | None = None  # Direct prompt (if no skill)
    allowed_tools: list[str] = field(default_factory=list)
    model: str = "sonnet"
    autonomous: bool = False
    max_turns: int | None = None
    timeout: int = 300

    # Code execution provider (claude, codex, etc.)
    code_source: str = "claude"

    # Task state
    enabled: bool = True
    variables: dict[str, Any] = field(default_factory=dict)
    last_run: str | None = None  # ISO timestamp
    last_status: str | None = None

    # Notification configuration
    notifications: dict[str, Any] | None = None  # NotificationConfig as dict

    # Plan mode configuration
    plan_mode: bool = False  # Enable interactive plan approval
    plan_timeout: int = 3600  # Approval timeout in seconds (default 1 hour)
    plan_max_iterations: int = 5  # Max discuss rounds before auto-cancel

    def __post_init__(self) -> None:
        """Validate task configuration."""
        # Validate CRON expression
        CronExpression(self.schedule)

        # Validate working directory
        if not self.working_dir.is_absolute():
            raise ValidationError(f"working_dir must be absolute: {self.working_dir}")

        # Must have either skill or prompt
        if not self.skill and not self.prompt:
            raise ValidationError("Task must have either 'skill' or 'prompt'")

    @classmethod
    def create(
        cls,
        name: str,
        schedule: str,
        working_dir: Path,
        skill: str | None = None,
        prompt: str | None = None,
        **kwargs: Any,
    ) -> Self:
        """Factory method to create a new task with generated ID."""
        task_id = str(uuid.uuid4())[:8]
        return cls(
            id=task_id,
            name=name,
            schedule=schedule,
            working_dir=working_dir,
            skill=skill,
            prompt=prompt,
            **kwargs,
        )

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            schedule=data["schedule"],
            working_dir=Path(data["working_dir"]),
            skill=data.get("skill"),
            prompt=data.get("prompt"),
            allowed_tools=data.get("allowed_tools", []),
            model=data.get("model", "sonnet"),
            autonomous=data.get("autonomous", False),
            max_turns=data.get("max_turns"),
            timeout=data.get("timeout", 300),
            code_source=data.get("code_source", "claude"),  # Default to claude for backward compat
            enabled=data.get("enabled", True),
            variables=data.get("variables", {}),
            last_run=data.get("last_run"),
            last_status=data.get("last_status"),
            notifications=data.get("notifications"),
            plan_mode=data.get("plan_mode", False),
            plan_timeout=data.get("plan_timeout", 3600),
            plan_max_iterations=data.get("plan_max_iterations", 5),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "working_dir": str(self.working_dir),
            "skill": self.skill,
            "prompt": self.prompt,
            "allowed_tools": self.allowed_tools,
            "model": self.model,
            "autonomous": self.autonomous,
            "max_turns": self.max_turns,
            "timeout": self.timeout,
            "code_source": self.code_source,
            "enabled": self.enabled,
            "variables": self.variables,
            "last_run": self.last_run,
            "last_status": self.last_status,
        }
        if self.notifications:
            result["notifications"] = self.notifications
        if self.plan_mode:
            result["plan_mode"] = self.plan_mode
            result["plan_timeout"] = self.plan_timeout
            result["plan_max_iterations"] = self.plan_max_iterations
        return result

    @property
    def cron(self) -> CronExpression:
        """Get CRON expression value object."""
        return CronExpression(self.schedule)

    def is_due(self, window_seconds: int = 60) -> bool:
        """Check if task is due for execution."""
        return self.enabled and self.cron.is_due(window_seconds)

    def update_last_run(self, status: str) -> None:
        """Update last run timestamp and status."""
        from datetime import datetime

        self.last_run = datetime.now().isoformat()
        self.last_status = status


@dataclass
class Project:
    """Registered project for multi-project support.

    Projects allow CodeGeass to manage tasks across multiple repositories
    from a single dashboard with per-project skills and aggregated views.
    """

    id: str
    name: str
    path: Path
    description: str = ""
    default_model: str = "sonnet"
    default_timeout: int = 300
    default_autonomous: bool = False
    git_remote: str | None = None
    enabled: bool = True
    use_shared_skills: bool = True
    created_at: str | None = None

    # Computed properties
    @property
    def config_dir(self) -> Path:
        """Get the config directory for this project."""
        return self.path / "config"

    @property
    def skills_dir(self) -> Path:
        """Get the skills directory for this project."""
        return self.path / ".claude" / "skills"

    @property
    def schedules_file(self) -> Path:
        """Get the schedules file for this project."""
        return self.config_dir / "schedules.yaml"

    @property
    def data_dir(self) -> Path:
        """Get the data directory for this project."""
        return self.path / "data"

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory for this project."""
        return self.data_dir / "logs"

    @property
    def sessions_dir(self) -> Path:
        """Get the sessions directory for this project."""
        return self.data_dir / "sessions"

    @classmethod
    def create(
        cls,
        name: str,
        path: Path,
        description: str = "",
        default_model: str = "sonnet",
        default_timeout: int = 300,
        default_autonomous: bool = False,
        git_remote: str | None = None,
        use_shared_skills: bool = True,
    ) -> Self:
        """Factory method to create a new project with generated ID."""
        from datetime import datetime

        project_id = str(uuid.uuid4())[:8]
        return cls(
            id=project_id,
            name=name,
            path=path.resolve(),
            description=description,
            default_model=default_model,
            default_timeout=default_timeout,
            default_autonomous=default_autonomous,
            git_remote=git_remote,
            enabled=True,
            use_shared_skills=use_shared_skills,
            created_at=datetime.now().isoformat(),
        )

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create project from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            path=Path(data["path"]),
            description=data.get("description", ""),
            default_model=data.get("default_model", "sonnet"),
            default_timeout=data.get("default_timeout", 300),
            default_autonomous=data.get("default_autonomous", False),
            git_remote=data.get("git_remote"),
            enabled=data.get("enabled", True),
            use_shared_skills=data.get("use_shared_skills", True),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "default_model": self.default_model,
            "default_timeout": self.default_timeout,
            "default_autonomous": self.default_autonomous,
            "git_remote": self.git_remote,
            "enabled": self.enabled,
            "use_shared_skills": self.use_shared_skills,
            "created_at": self.created_at,
        }

    def exists(self) -> bool:
        """Check if the project path exists."""
        return self.path.exists()

    def is_initialized(self) -> bool:
        """Check if the project has CodeGeass structure initialized."""
        return self.config_dir.exists() and self.schedules_file.exists()
