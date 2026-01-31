"""Plan mode and resume strategies."""

from dataclasses import dataclass
from pathlib import Path

from codegeass.core.entities import Task
from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.claude_cli import get_claude_executable
from codegeass.execution.strategies.context import ExecutionContext

# System prompt for plan mode - more flexible for content generation
PLAN_MODE_SYSTEM_PROMPT = (
    "You are running as a scheduled task agent. You can help with ANY task the user "
    "has scheduled, including but not limited to: coding, content creation, research, "
    "writing, analysis, and automation. Do not refuse tasks based on them being "
    "'non-coding' - the user has explicitly scheduled this task and expects you to "
    "complete it. If the task involves creating content (tweets, articles, etc.), "
    "generate the content directly. If it involves file operations, plan those operations."
)

# System prompt for approved execution
APPROVAL_SYSTEM_PROMPT = (
    "You are running as a scheduled task agent. The user has reviewed and APPROVED "
    "your plan. Complete the task now without refusing or redirecting. You can help "
    "with ANY task: coding, content creation, research, writing, analysis, automation. "
    "If the task involves files, create/modify them. If it's content generation, "
    "output the final content. The user explicitly approved this - proceed fully."
)


@dataclass
class ResumeContext:
    """Context for resuming a Claude session."""

    task: Task
    session_id: str
    working_dir: Path
    feedback: str | None = None


class PlanModeStrategy(BaseStrategy):
    """Plan mode execution strategy using `--permission-mode plan`.

    This runs Claude in read-only planning mode where it can analyze
    the codebase and produce a plan, but cannot make any modifications.
    The plan can then be reviewed and approved before execution.
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for plan mode execution."""
        if context.skill:
            prompt = f"/{context.skill.name}"
            if context.prompt:
                prompt += f" {context.prompt}"
        else:
            prompt = context.prompt

        cmd = [get_claude_executable(), "-p", prompt]
        cmd.extend(["--append-system-prompt", PLAN_MODE_SYSTEM_PROMPT])
        cmd.extend(["--permission-mode", "plan"])
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        if context.task.model:
            cmd.extend(["--model", context.task.model])

        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        allowed_tools = context.task.allowed_tools
        if context.skill and context.skill.allowed_tools:
            allowed_tools = context.skill.allowed_tools
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        return cmd


class ResumeWithApprovalStrategy(BaseStrategy):
    """Strategy for resuming a session with full permissions after approval.

    Used after user approves a plan - resumes the Claude session with
    --dangerously-skip-permissions to execute the approved plan.
    """

    def __init__(self, timeout: int = 300):
        """Initialize with task timeout."""
        super().__init__(timeout)

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command to resume with approval."""
        if not context.session_id:
            raise ValueError("ResumeWithApprovalStrategy requires session_id in context")

        cmd = [get_claude_executable(), "--resume", context.session_id]
        cmd.extend(["--append-system-prompt", APPROVAL_SYSTEM_PROMPT])
        cmd.extend(["-p", "USER APPROVED. Complete the task now."])
        cmd.append("--dangerously-skip-permissions")
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        return cmd


class ResumeWithFeedbackStrategy(BaseStrategy):
    """Strategy for resuming a session with feedback in plan mode.

    Used when user clicks "Discuss" - resumes the Claude session with
    user feedback, still in plan mode for iterative refinement.
    """

    def __init__(self, feedback: str, timeout: int = 300):
        """Initialize with feedback text."""
        super().__init__(timeout)
        self.feedback = feedback

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command to resume with feedback."""
        if not context.session_id:
            raise ValueError("ResumeWithFeedbackStrategy requires session_id in context")

        cmd = [get_claude_executable(), "--resume", context.session_id]
        cmd.extend(["--append-system-prompt", PLAN_MODE_SYSTEM_PROMPT])
        cmd.extend(["-p", self.feedback])
        cmd.extend(["--permission-mode", "plan"])
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        return cmd
