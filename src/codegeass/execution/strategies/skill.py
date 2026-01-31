"""Skill execution strategies using /skill-name syntax.

This module provides strategies for invoking Claude Code skills,
which are reusable prompt templates following the Agent Skills standard.
"""

from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.claude_cli import get_claude_executable
from codegeass.execution.strategies.context import ExecutionContext
from codegeass.execution.strategies.headless import TASK_SYSTEM_PROMPT


class SkillStrategy(BaseStrategy):
    """Strategy for invoking Claude Code skills using /skill-name syntax.

    Skills are invoked using: `claude -p "/skill-name arguments"`

    Skills are reusable prompt templates stored in .claude/skills/ that
    encapsulate common workflows like code review, refactoring, or deployment.

    Use Cases:
        - Invoking project-specific skills (/commit, /deploy)
        - Running shared skills from ~/.codegeass/skills/
        - Combining skill templates with custom arguments

    Example:
        >>> strategy = SkillStrategy(timeout=300)
        >>> context = ExecutionContext(task=my_task, skill=my_skill, prompt="src/")
        >>> command = strategy.build_command(context)
        # Produces: claude -p "/refactor src/" ...
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for skill invocation.

        Args:
            context: Execution context containing skill and optional arguments.

        Returns:
            Command list with /skill-name prompt format.

        Raises:
            ValueError: If context does not contain a skill.
        """
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

    This injects skill instructions into Claude's system prompt rather than
    using the /skill-name invocation syntax. Useful when you want the skill
    content to act as background instructions.

    Differences from SkillStrategy:
        - SkillStrategy: Uses /skill-name in prompt (skill as primary task)
        - AppendSystemPromptStrategy: Appends skill to system prompt (skill as context)

    Use Cases:
        - Adding coding guidelines as background context
        - Injecting project-specific rules for all prompts
        - Combining multiple skills as system context

    Example:
        >>> strategy = AppendSystemPromptStrategy(timeout=300)
        >>> context = ExecutionContext(task=my_task, skill=style_guide, prompt="Fix the bug")
        >>> command = strategy.build_command(context)
        # The style_guide content becomes part of system prompt
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command with appended system prompt.

        Args:
            context: Execution context with skill whose content becomes system prompt.

        Returns:
            Command list with --append-system-prompt-file pointing to skill file.
        """
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
