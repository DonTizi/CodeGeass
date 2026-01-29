"""Fluent task builder for creating tasks."""

from pathlib import Path
from typing import Any, Self

from codegeass.core.entities import Task
from codegeass.core.exceptions import ValidationError


class TaskBuilder:
    """Fluent builder for creating Task instances.

    Example:
        task = (TaskBuilder()
            .with_name("daily-review")
            .with_skill("code-review")
            .with_schedule("0 9 * * 1-5")
            .with_working_dir(Path("/my/project"))
            .build())
    """

    def __init__(self) -> None:
        """Initialize builder with empty configuration."""
        self._name: str | None = None
        self._schedule: str | None = None
        self._working_dir: Path | None = None
        self._skill: str | None = None
        self._prompt: str | None = None
        self._allowed_tools: list[str] = []
        self._model: str = "sonnet"
        self._autonomous: bool = False
        self._max_turns: int | None = None
        self._timeout: int = 300
        self._enabled: bool = True
        self._variables: dict[str, Any] = {}

    def with_name(self, name: str) -> Self:
        """Set task name."""
        self._name = name
        return self

    def with_schedule(self, schedule: str) -> Self:
        """Set CRON schedule expression."""
        self._schedule = schedule
        return self

    def with_working_dir(self, path: Path | str) -> Self:
        """Set working directory."""
        self._working_dir = Path(path) if isinstance(path, str) else path
        return self

    def with_skill(self, skill: str) -> Self:
        """Set skill to invoke."""
        self._skill = skill
        self._prompt = None  # Clear prompt if setting skill
        return self

    def with_prompt(self, prompt: str) -> Self:
        """Set direct prompt."""
        self._prompt = prompt
        self._skill = None  # Clear skill if setting prompt
        return self

    def with_tools(self, tools: list[str]) -> Self:
        """Set allowed tools."""
        self._allowed_tools = tools
        return self

    def add_tool(self, tool: str) -> Self:
        """Add a single tool to allowed tools."""
        if tool not in self._allowed_tools:
            self._allowed_tools.append(tool)
        return self

    def with_model(self, model: str) -> Self:
        """Set model (haiku, sonnet, opus)."""
        self._model = model
        return self

    def with_autonomous(self, autonomous: bool = True) -> Self:
        """Enable autonomous mode (dangerously-skip-permissions)."""
        self._autonomous = autonomous
        return self

    def with_max_turns(self, max_turns: int) -> Self:
        """Set maximum agentic turns."""
        self._max_turns = max_turns
        return self

    def with_timeout(self, timeout: int) -> Self:
        """Set execution timeout in seconds."""
        self._timeout = timeout
        return self

    def with_enabled(self, enabled: bool) -> Self:
        """Set enabled state."""
        self._enabled = enabled
        return self

    def with_variable(self, key: str, value: Any) -> Self:
        """Set a single variable."""
        self._variables[key] = value
        return self

    def with_variables(self, variables: dict[str, Any]) -> Self:
        """Set multiple variables."""
        self._variables.update(variables)
        return self

    def validate(self) -> list[str]:
        """Validate builder state and return list of errors."""
        errors = []

        if not self._name:
            errors.append("name is required")
        if not self._schedule:
            errors.append("schedule is required")
        if not self._working_dir:
            errors.append("working_dir is required")
        if not self._skill and not self._prompt:
            errors.append("either skill or prompt is required")

        return errors

    def build(self) -> Task:
        """Build the Task instance.

        Raises:
            ValidationError: If builder state is invalid
        """
        errors = self.validate()
        if errors:
            raise ValidationError(f"Invalid task configuration: {', '.join(errors)}")

        assert self._name is not None
        assert self._schedule is not None
        assert self._working_dir is not None

        return Task.create(
            name=self._name,
            schedule=self._schedule,
            working_dir=self._working_dir,
            skill=self._skill,
            prompt=self._prompt,
            allowed_tools=self._allowed_tools,
            model=self._model,
            autonomous=self._autonomous,
            max_turns=self._max_turns,
            timeout=self._timeout,
            enabled=self._enabled,
            variables=self._variables,
        )

    def reset(self) -> Self:
        """Reset builder to initial state."""
        self.__init__()  # type: ignore
        return self
