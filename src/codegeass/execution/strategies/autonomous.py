"""Autonomous execution strategy with `--dangerously-skip-permissions`."""

from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.claude_cli import get_claude_executable
from codegeass.execution.strategies.context import ExecutionContext
from codegeass.execution.strategies.headless import TASK_SYSTEM_PROMPT


class AutonomousStrategy(BaseStrategy):
    """Autonomous execution strategy with `--dangerously-skip-permissions`.

    WARNING: This allows Claude to modify files without confirmation.
    Use only for trusted, well-tested tasks.
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for autonomous execution."""
        cmd = [get_claude_executable(), "-p", context.prompt]
        cmd.extend(["--append-system-prompt", TASK_SYSTEM_PROMPT])
        cmd.append("--dangerously-skip-permissions")
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        if context.task.model:
            cmd.extend(["--model", context.task.model])

        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        if context.task.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(context.task.allowed_tools)])

        return cmd
