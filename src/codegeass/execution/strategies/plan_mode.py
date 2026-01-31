"""Plan mode and resume strategies.

This module provides strategies for the plan-approve-execute workflow:

1. PlanModeStrategy: Runs Claude in read-only mode to generate a plan
2. ResumeWithApprovalStrategy: Executes approved plan with full permissions
3. ResumeWithFeedbackStrategy: Continues planning with user feedback

Workflow:
    1. Task runs with PlanModeStrategy (read-only)
    2. Claude produces a plan (stored as approval)
    3. User reviews plan via dashboard/Telegram/CLI
    4. User approves -> ResumeWithApprovalStrategy executes
    5. Or user provides feedback -> ResumeWithFeedbackStrategy refines plan
"""

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
    """Context for resuming a Claude session.

    Used when resuming a paused session, either after approval
    or with user feedback for further refinement.

    Attributes:
        task: The task being executed.
        session_id: Claude session ID from the planning phase.
        working_dir: Directory where the session runs.
        feedback: Optional user feedback for plan refinement.
    """

    task: Task
    session_id: str
    working_dir: Path
    feedback: str | None = None


class PlanModeStrategy(BaseStrategy):
    """Plan mode execution strategy using `--permission-mode plan`.

    This runs Claude in read-only planning mode where it can analyze
    the codebase and produce a plan, but cannot make any modifications.
    The plan can then be reviewed and approved before execution.

    Key Characteristics:
        - Read-only: No file modifications allowed
        - Full analysis: Can read files, search code, explore codebase
        - Plan output: Produces a reviewable plan with proposed changes
        - Session saved: Claude session ID preserved for later resume

    Use Cases:
        - Safe automated code review
        - Change impact analysis
        - Architectural planning with human approval

    Example:
        >>> strategy = PlanModeStrategy(timeout=600)
        >>> result = executor.execute(task, strategy)
        >>> # result.session_id can be used with ResumeWithApprovalStrategy
    """

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for plan mode execution.

        Args:
            context: Execution context with task and optional skill.

        Returns:
            Command list with --permission-mode plan flag.
        """
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

    This is the "execute" phase of the plan-approve-execute workflow.
    The session context from planning is preserved, allowing Claude to
    proceed with the exact changes it proposed.

    Workflow:
        1. PlanModeStrategy produced a plan and session_id
        2. User reviewed and approved via dashboard/Telegram/CLI
        3. This strategy resumes with full write permissions
        4. Claude executes the approved changes

    Example:
        >>> strategy = ResumeWithApprovalStrategy(timeout=600)
        >>> context.session_id = approved_session_id
        >>> result = executor.execute(task, strategy)
    """

    def __init__(self, timeout: int = 300):
        """Initialize with task timeout.

        Args:
            timeout: Maximum execution time in seconds (default 300).
        """
        super().__init__(timeout)

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command to resume with approval.

        Args:
            context: Execution context with session_id from planning phase.

        Returns:
            Command list with --resume and --dangerously-skip-permissions.

        Raises:
            ValueError: If context.session_id is not set.
        """
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

    This enables a conversational refinement loop where the user can
    ask questions, request changes, or provide additional context
    before approving the plan.

    Workflow:
        1. PlanModeStrategy produced a plan
        2. User provides feedback: "Also consider error handling"
        3. This strategy resumes with feedback, still in plan mode
        4. Claude refines the plan based on feedback
        5. User can approve or provide more feedback

    Example:
        >>> strategy = ResumeWithFeedbackStrategy(
        ...     feedback="Please also add unit tests for the changes",
        ...     timeout=600
        ... )
        >>> context.session_id = discussion_session_id
        >>> result = executor.execute(task, strategy)
    """

    def __init__(self, feedback: str, timeout: int = 300):
        """Initialize with feedback text.

        Args:
            feedback: User's feedback or questions about the plan.
            timeout: Maximum execution time in seconds (default 300).
        """
        super().__init__(timeout)
        self.feedback = feedback

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command to resume with feedback.

        Args:
            context: Execution context with session_id from planning phase.

        Returns:
            Command list with --resume, feedback as prompt, still in plan mode.

        Raises:
            ValueError: If context.session_id is not set.
        """
        if not context.session_id:
            raise ValueError("ResumeWithFeedbackStrategy requires session_id in context")

        cmd = [get_claude_executable(), "--resume", context.session_id]
        cmd.extend(["--append-system-prompt", PLAN_MODE_SYSTEM_PROMPT])
        cmd.extend(["-p", self.feedback])
        cmd.extend(["--permission-mode", "plan"])
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        cmd.append("--include-partial-messages")

        return cmd
