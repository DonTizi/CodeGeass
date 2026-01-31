"""Execution context and protocol definitions."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from codegeass.core.entities import Skill, Task
from codegeass.core.value_objects import ExecutionResult

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker


@dataclass
class ExecutionContext:
    """Context for task execution."""

    task: Task
    skill: Skill | None
    prompt: str
    working_dir: Path
    session_id: str | None = None
    execution_id: str | None = None
    tracker: "ExecutionTracker | None" = None


class ExecutionStrategy(Protocol):
    """Protocol for execution strategies."""

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute a task with the given context."""
        ...

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build the Claude command to execute."""
        ...
