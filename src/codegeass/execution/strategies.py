"""Execution strategies for Claude Code invocation."""

import subprocess
import shlex
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from codegeass.core.entities import Skill, Task
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus


@dataclass
class ExecutionContext:
    """Context for task execution."""

    task: Task
    skill: Skill | None
    prompt: str
    working_dir: Path
    session_id: str | None = None


class ExecutionStrategy(Protocol):
    """Protocol for execution strategies."""

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute a task with the given context."""
        ...

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build the Claude command to execute."""
        ...


class BaseStrategy(ABC):
    """Base class for execution strategies."""

    def __init__(self, timeout: int = 300):
        """Initialize with default timeout."""
        self.timeout = timeout

    @abstractmethod
    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build the Claude command to execute."""
        ...

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the command and return result."""
        started_at = datetime.now()
        command = self.build_command(context)

        try:
            # Ensure ANTHROPIC_API_KEY is NOT set (use subscription)
            import os

            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)

            result = subprocess.run(
                command,
                cwd=context.working_dir,
                capture_output=True,
                text=True,
                timeout=context.task.timeout or self.timeout,
                env=env,
            )

            finished_at = datetime.now()
            status = ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.FAILURE

            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id,
                status=status,
                output=result.stdout,
                started_at=started_at,
                finished_at=finished_at,
                error=result.stderr if result.returncode != 0 else None,
                exit_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            finished_at = datetime.now()
            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id,
                status=ExecutionStatus.TIMEOUT,
                output="",
                started_at=started_at,
                finished_at=finished_at,
                error=f"Execution timed out after {context.task.timeout or self.timeout}s",
            )

        except Exception as e:
            finished_at = datetime.now()
            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id,
                status=ExecutionStatus.FAILURE,
                output="",
                started_at=started_at,
                finished_at=finished_at,
                error=str(e),
            )


class HeadlessStrategy(BaseStrategy):
    """Headless execution strategy using `claude -p`.

    Safe mode - no file modifications allowed without explicit tools.
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for headless execution."""
        cmd = ["claude", "-p", context.prompt]

        # Add output format
        cmd.extend(["--output-format", "json"])

        # Add model if specified
        if context.task.model:
            cmd.extend(["--model", context.task.model])

        # Add max turns if specified
        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        # Add allowed tools if specified
        if context.task.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(context.task.allowed_tools)])

        return cmd


class AutonomousStrategy(BaseStrategy):
    """Autonomous execution strategy with `--dangerously-skip-permissions`.

    WARNING: This allows Claude to modify files without confirmation.
    Use only for trusted, well-tested tasks.
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for autonomous execution."""
        cmd = ["claude", "-p", context.prompt]

        # Add autonomous flag
        cmd.append("--dangerously-skip-permissions")

        # Add output format
        cmd.extend(["--output-format", "json"])

        # Add model if specified
        if context.task.model:
            cmd.extend(["--model", context.task.model])

        # Add max turns if specified
        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        # Add allowed tools if specified
        if context.task.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(context.task.allowed_tools)])

        return cmd


class SkillStrategy(BaseStrategy):
    """Strategy for invoking Claude Code skills using /skill-name syntax.

    Skills are invoked using: claude -p "/skill-name arguments"
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for skill invocation."""
        if not context.skill:
            raise ValueError("SkillStrategy requires a skill in context")

        # Build skill invocation prompt
        skill_prompt = f"/{context.skill.name}"
        if context.prompt:
            skill_prompt += f" {context.prompt}"

        cmd = ["claude", "-p", skill_prompt]

        # Add output format
        cmd.extend(["--output-format", "json"])

        # Add model if specified
        if context.task.model:
            cmd.extend(["--model", context.task.model])

        # Add max turns if specified
        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        # Autonomous mode if configured
        if context.task.autonomous:
            cmd.append("--dangerously-skip-permissions")

        return cmd


class AppendSystemPromptStrategy(BaseStrategy):
    """Strategy that uses --append-system-prompt-file for skill content.

    This injects skill instructions into Claude's system prompt.
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command with appended system prompt."""
        cmd = ["claude", "-p", context.prompt]

        # Add skill file as system prompt if available
        if context.skill:
            cmd.extend(["--append-system-prompt-file", str(context.skill.path)])

        # Add output format
        cmd.extend(["--output-format", "json"])

        # Add model if specified
        if context.task.model:
            cmd.extend(["--model", context.task.model])

        # Add allowed tools from skill
        if context.skill and context.skill.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(context.skill.allowed_tools)])

        # Autonomous mode if configured
        if context.task.autonomous:
            cmd.append("--dangerously-skip-permissions")

        return cmd
