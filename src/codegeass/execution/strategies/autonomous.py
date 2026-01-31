"""Autonomous execution strategy with `--dangerously-skip-permissions`.

This strategy enables Claude to execute file operations without user confirmation,
making it suitable for automated batch operations and CI/CD pipelines.
"""

from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.claude_cli import get_claude_executable
from codegeass.execution.strategies.context import ExecutionContext
from codegeass.execution.strategies.headless import TASK_SYSTEM_PROMPT


class AutonomousStrategy(BaseStrategy):
    """Autonomous execution strategy with `--dangerously-skip-permissions`.

    This strategy allows Claude to modify files, run commands, and perform
    system operations without requiring user confirmation for each action.

    Use Cases:
        - Automated code refactoring tasks
        - Batch file operations
        - CI/CD pipeline integrations
        - Scheduled maintenance tasks

    WARNING:
        This allows Claude to modify files without confirmation.
        Use only for trusted, well-tested tasks in controlled environments.

    Example:
        >>> strategy = AutonomousStrategy(timeout=300)
        >>> context = ExecutionContext(task=my_task, prompt="Refactor all test files")
        >>> command = strategy.build_command(context)
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for autonomous execution.

        Args:
            context: Execution context containing task configuration and prompt.

        Returns:
            Command list with --dangerously-skip-permissions flag enabled.
        """
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
