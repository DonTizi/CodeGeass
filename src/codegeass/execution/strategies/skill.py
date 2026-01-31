"""Skill execution strategies using /skill-name syntax."""

from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.claude_cli import get_claude_executable
from codegeass.execution.strategies.context import ExecutionContext
from codegeass.execution.strategies.headless import TASK_SYSTEM_PROMPT


class SkillStrategy(BaseStrategy):
    """Strategy for invoking Claude Code skills using /skill-name syntax.

    Skills are invoked using: claude -p "/skill-name arguments"
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for skill invocation."""
        if not context.skill:
            raise ValueError("SkillStrategy requires a skill in context")

        skill_prompt = f"/{context.skill.name}"
        if context.prompt:
            skill_prompt += f" {context.prompt}"

        cmd = [get_claude_executable(), "-p", skill_prompt]
        cmd.extend(["--append-system-prompt", TASK_SYSTEM_PROMPT])
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        if context.task.model:
            cmd.extend(["--model", context.task.model])

        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        if context.task.autonomous:
            cmd.append("--dangerously-skip-permissions")

        return cmd


class AppendSystemPromptStrategy(BaseStrategy):
    """Strategy that uses --append-system-prompt-file for skill content.

    This injects skill instructions into Claude's system prompt.
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command with appended system prompt."""
        cmd = [get_claude_executable(), "-p", context.prompt]

        if context.skill:
            cmd.extend(["--append-system-prompt-file", str(context.skill.path)])

        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        if context.task.model:
            cmd.extend(["--model", context.task.model])

        if context.skill and context.skill.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(context.skill.allowed_tools)])

        if context.task.autonomous:
            cmd.append("--dangerously-skip-permissions")

        return cmd
