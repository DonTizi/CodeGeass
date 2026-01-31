"""Headless execution strategy using `claude -p`."""

from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.claude_cli import get_claude_executable
from codegeass.execution.strategies.context import ExecutionContext

# Custom system prompt for scheduled tasks
TASK_SYSTEM_PROMPT = (
    "You are running as a scheduled task agent. You can help with ANY task the user "
    "has scheduled, including but not limited to: coding, content creation, research, "
    "writing, analysis, and automation. Do not refuse tasks based on them being "
    "'non-coding' - the user has explicitly scheduled this task and expects you to "
    "complete it."
)


class HeadlessStrategy(BaseStrategy):
    """Headless execution strategy using `claude -p`.

    Safe mode - no file modifications allowed without explicit tools.
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for headless execution."""
        cmd = [get_claude_executable(), "-p", context.prompt]
        cmd.extend(["--append-system-prompt", TASK_SYSTEM_PROMPT])
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        if context.task.model:
            cmd.extend(["--model", context.task.model])

        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        if context.task.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(context.task.allowed_tools)])

        return cmd
