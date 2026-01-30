"""Execution strategies for Claude Code invocation."""

import json
import logging
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import yaml

from codegeass.core.entities import Skill, Task
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_claude_executable() -> str:
    """Get the path to the claude executable.

    Checks in order:
    1. Settings file (config/settings.yaml -> claude.executable)
    2. shutil.which('claude')
    3. Common installation paths

    Returns:
        Path to the claude executable

    Raises:
        FileNotFoundError: If claude executable cannot be found
    """
    # Try to load from settings
    settings_paths = [
        Path.cwd() / "config" / "settings.yaml",
        Path(__file__).parent.parent.parent.parent.parent / "config" / "settings.yaml",
    ]

    for settings_path in settings_paths:
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    settings = yaml.safe_load(f)
                    executable = settings.get("claude", {}).get("executable")
                    if executable and Path(executable).exists():
                        logger.debug(f"Using claude from settings: {executable}")
                        return executable
            except Exception as e:
                logger.warning(f"Failed to load settings from {settings_path}: {e}")

    # Try shutil.which
    which_claude = shutil.which("claude")
    if which_claude:
        logger.debug(f"Using claude from PATH: {which_claude}")
        return which_claude

    # Try common installation paths
    common_paths = [
        Path.home() / ".local" / "bin" / "claude",
        Path("/usr/local/bin/claude"),
        Path("/usr/bin/claude"),
    ]

    for path in common_paths:
        if path.exists():
            logger.debug(f"Using claude from common path: {path}")
            return str(path)

    raise FileNotFoundError(
        "Claude executable not found. Please install Claude Code or set "
        "claude.executable in config/settings.yaml"
    )


@dataclass
class ExecutionContext:
    """Context for task execution."""

    task: Task
    skill: Skill | None
    prompt: str
    working_dir: Path
    session_id: str | None = None
    # For streaming execution support
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
        """Execute the command and return result.

        If context.tracker is provided, uses streaming execution with Popen
        to emit real-time output events. Otherwise uses blocking subprocess.run.
        """
        # Use streaming execution if tracker is present
        if context.tracker and context.execution_id:
            return self._execute_streaming(context)
        else:
            return self._execute_blocking(context)

    def _execute_blocking(self, context: ExecutionContext) -> ExecutionResult:
        """Execute using blocking subprocess.run (original behavior)."""
        started_at = datetime.now()
        command = self.build_command(context)

        try:
            # Ensure ANTHROPIC_API_KEY is NOT set (use subscription)
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

    def _execute_streaming(self, context: ExecutionContext) -> ExecutionResult:
        """Execute using streaming Popen to emit real-time output events."""
        started_at = datetime.now()
        command = self.build_command(context)
        tracker = context.tracker
        execution_id = context.execution_id

        # Ensure we have required context
        if not tracker or not execution_id:
            return self._execute_blocking(context)

        output_lines: list[str] = []
        stderr_lines: list[str] = []

        try:
            # Ensure ANTHROPIC_API_KEY is NOT set (use subscription)
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)

            # Update tracker to running state
            tracker.update_execution(execution_id, status="running", phase="executing")

            # Start process with Popen for streaming
            process = subprocess.Popen(
                command,
                cwd=context.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1,  # Line buffered
            )

            timeout_seconds = context.task.timeout or self.timeout
            deadline = datetime.now().timestamp() + timeout_seconds

            # Read stdout and stderr in real-time
            while True:
                # Check timeout
                if datetime.now().timestamp() > deadline:
                    process.kill()
                    process.wait()
                    tracker.update_execution(execution_id, status="finishing")
                    raise subprocess.TimeoutExpired(command, timeout_seconds)

                # Check if process has finished
                return_code = process.poll()

                # Read available output
                if process.stdout:
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        line = line.rstrip("\n")
                        output_lines.append(line)
                        tracker.append_output(execution_id, line)
                        # Try to detect phase changes from JSON output
                        self._detect_phase(tracker, execution_id, line)

                if process.stderr:
                    while True:
                        line = process.stderr.readline()
                        if not line:
                            break
                        stderr_lines.append(line.rstrip("\n"))

                if return_code is not None:
                    break

            # Process has finished
            tracker.update_execution(execution_id, status="finishing")

            finished_at = datetime.now()
            status = ExecutionStatus.SUCCESS if return_code == 0 else ExecutionStatus.FAILURE

            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id,
                status=status,
                output="\n".join(output_lines),
                started_at=started_at,
                finished_at=finished_at,
                error="\n".join(stderr_lines) if return_code != 0 and stderr_lines else None,
                exit_code=return_code,
            )

        except subprocess.TimeoutExpired:
            finished_at = datetime.now()
            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id,
                status=ExecutionStatus.TIMEOUT,
                output="\n".join(output_lines),
                started_at=started_at,
                finished_at=finished_at,
                error=f"Execution timed out after {context.task.timeout or self.timeout}s",
            )

        except Exception as e:
            finished_at = datetime.now()
            logger.error(f"Streaming execution error: {e}")
            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id,
                status=ExecutionStatus.FAILURE,
                output="\n".join(output_lines),
                started_at=started_at,
                finished_at=finished_at,
                error=str(e),
            )

    def _detect_phase(self, tracker: "ExecutionTracker", execution_id: str, line: str) -> None:
        """Try to detect execution phase from stream-json output line."""
        try:
            # Claude stream-json format outputs structured events
            if line.startswith("{"):
                data = json.loads(line)

                # Handle different event types in stream-json format
                event_type = data.get("type", "")

                if event_type == "assistant":
                    # Assistant message with content blocks
                    message = data.get("message", {})
                    content = message.get("content", [])
                    for block in content:
                        block_type = block.get("type", "")
                        if block_type == "tool_use":
                            tool_name = block.get("name", "unknown")
                            tracker.update_execution(execution_id, phase=f"tool: {tool_name}")
                        elif block_type == "text":
                            tracker.update_execution(execution_id, phase="thinking")

                elif event_type == "content_block_start":
                    # Start of a content block
                    content_block = data.get("content_block", {})
                    block_type = content_block.get("type", "")
                    if block_type == "tool_use":
                        tool_name = content_block.get("name", "unknown")
                        tracker.update_execution(execution_id, phase=f"tool: {tool_name}")
                    elif block_type == "text":
                        tracker.update_execution(execution_id, phase="generating")

                elif event_type == "tool_use":
                    # Direct tool use event
                    tool_name = data.get("name", "unknown")
                    tracker.update_execution(execution_id, phase=f"tool: {tool_name}")

                elif event_type == "result":
                    # Final result
                    tracker.update_execution(execution_id, phase="completing")

        except (json.JSONDecodeError, KeyError):
            pass


class HeadlessStrategy(BaseStrategy):
    """Headless execution strategy using `claude -p`.

    Safe mode - no file modifications allowed without explicit tools.
    """

    # Custom system prompt for scheduled tasks
    TASK_SYSTEM_PROMPT = (
        "You are running as a scheduled task agent. You can help with ANY task the user "
        "has scheduled, including but not limited to: coding, content creation, research, "
        "writing, analysis, and automation. Do not refuse tasks based on them being "
        "'non-coding' - the user has explicitly scheduled this task and expects you to "
        "complete it."
    )

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for headless execution."""
        cmd = [get_claude_executable(), "-p", context.prompt]

        # Add custom system prompt for flexibility
        cmd.extend(["--append-system-prompt", self.TASK_SYSTEM_PROMPT])

        # Add output format - stream-json for real-time output visibility
        # Note: stream-json requires --verbose when using -p (print mode)
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        # Include partial messages for real-time streaming
        cmd.append("--include-partial-messages")

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

    # Reuse the flexible system prompt
    TASK_SYSTEM_PROMPT = HeadlessStrategy.TASK_SYSTEM_PROMPT

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for autonomous execution."""
        cmd = [get_claude_executable(), "-p", context.prompt]

        # Add custom system prompt for flexibility
        cmd.extend(["--append-system-prompt", self.TASK_SYSTEM_PROMPT])

        # Add autonomous flag
        cmd.append("--dangerously-skip-permissions")

        # Add output format - stream-json for real-time output visibility
        # Note: stream-json requires --verbose when using -p (print mode)
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        # Include partial messages for real-time streaming
        cmd.append("--include-partial-messages")

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

    # Reuse the flexible system prompt
    TASK_SYSTEM_PROMPT = HeadlessStrategy.TASK_SYSTEM_PROMPT

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for skill invocation."""
        if not context.skill:
            raise ValueError("SkillStrategy requires a skill in context")

        # Build skill invocation prompt
        skill_prompt = f"/{context.skill.name}"
        if context.prompt:
            skill_prompt += f" {context.prompt}"

        cmd = [get_claude_executable(), "-p", skill_prompt]

        # Add custom system prompt for flexibility
        cmd.extend(["--append-system-prompt", self.TASK_SYSTEM_PROMPT])

        # Add output format - stream-json for real-time output visibility
        # Note: stream-json requires --verbose when using -p (print mode)
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        # Include partial messages for real-time streaming
        cmd.append("--include-partial-messages")

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
        cmd = [get_claude_executable(), "-p", context.prompt]

        # Add skill file as system prompt if available
        if context.skill:
            cmd.extend(["--append-system-prompt-file", str(context.skill.path)])

        # Add output format - stream-json for real-time output visibility
        # Note: stream-json requires --verbose when using -p (print mode)
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        # Include partial messages for real-time streaming
        cmd.append("--include-partial-messages")

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


class PlanModeStrategy(BaseStrategy):
    """Plan mode execution strategy using `--permission-mode plan`.

    This runs Claude in read-only planning mode where it can analyze
    the codebase and produce a plan, but cannot make any modifications.
    The plan can then be reviewed and approved before execution.

    If the task has a skill, the skill is invoked using /skill-name syntax.
    """

    # Custom system prompt to make Claude more flexible for scheduled tasks
    TASK_SYSTEM_PROMPT = (
        "You are running as a scheduled task agent. You can help with ANY task the user "
        "has scheduled, including but not limited to: coding, content creation, research, "
        "writing, analysis, and automation. Do not refuse tasks based on them being "
        "'non-coding' - the user has explicitly scheduled this task and expects you to "
        "complete it. If the task involves creating content (tweets, articles, etc.), "
        "generate the content directly. If it involves file operations, plan those operations."
    )

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command for plan mode execution."""
        # Build prompt - use skill invocation if skill is present
        if context.skill:
            prompt = f"/{context.skill.name}"
            if context.prompt:
                prompt += f" {context.prompt}"
        else:
            prompt = context.prompt

        cmd = [get_claude_executable(), "-p", prompt]

        # Add custom system prompt to make Claude more flexible
        cmd.extend(["--append-system-prompt", self.TASK_SYSTEM_PROMPT])

        # Add plan permission mode (read-only)
        cmd.extend(["--permission-mode", "plan"])

        # Add output format - stream-json for real-time output visibility
        # Note: stream-json requires --verbose when using -p (print mode)
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        # Include partial messages for real-time streaming
        cmd.append("--include-partial-messages")

        # Add model if specified
        if context.task.model:
            cmd.extend(["--model", context.task.model])

        # Add max turns if specified
        if context.task.max_turns:
            cmd.extend(["--max-turns", str(context.task.max_turns)])

        # Add allowed tools - from skill or task
        allowed_tools = context.task.allowed_tools
        if context.skill and context.skill.allowed_tools:
            allowed_tools = context.skill.allowed_tools
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        return cmd


@dataclass
class ResumeContext:
    """Context for resuming a Claude session."""

    task: Task
    session_id: str  # Claude session ID to resume
    working_dir: Path
    feedback: str | None = None  # Optional feedback for discuss mode


class ResumeWithApprovalStrategy(BaseStrategy):
    """Strategy for resuming a session with full permissions after approval.

    Used after user approves a plan - resumes the Claude session with
    --dangerously-skip-permissions to execute the approved plan.
    """

    # Custom system prompt for approval execution
    APPROVAL_SYSTEM_PROMPT = (
        "You are running as a scheduled task agent. The user has reviewed and APPROVED "
        "your plan. Complete the task now without refusing or redirecting. You can help "
        "with ANY task: coding, content creation, research, writing, analysis, automation. "
        "If the task involves files, create/modify them. If it's content generation, "
        "output the final content. The user explicitly approved this - proceed fully."
    )

    def __init__(self, timeout: int = 300):
        """Initialize with task timeout."""
        super().__init__(timeout)

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command to resume with approval.

        Note: This uses context.session_id as the Claude session to resume.
        """
        if not context.session_id:
            raise ValueError("ResumeWithApprovalStrategy requires session_id in context")

        cmd = [get_claude_executable(), "--resume", context.session_id]

        # Add custom system prompt to ensure Claude completes the task
        cmd.extend(["--append-system-prompt", self.APPROVAL_SYSTEM_PROMPT])

        # Add approval prompt
        cmd.extend(["-p", "USER APPROVED. Complete the task now."])

        # Add autonomous flag for approved execution
        cmd.append("--dangerously-skip-permissions")

        # Add output format - stream-json for consistent parsing
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        # Include partial messages for real-time streaming
        cmd.append("--include-partial-messages")

        return cmd


class ResumeWithFeedbackStrategy(BaseStrategy):
    """Strategy for resuming a session with feedback in plan mode.

    Used when user clicks "Discuss" - resumes the Claude session with
    user feedback, still in plan mode for iterative refinement.
    """

    # Reuse the same flexible system prompt
    TASK_SYSTEM_PROMPT = PlanModeStrategy.TASK_SYSTEM_PROMPT

    def __init__(self, feedback: str, timeout: int = 300):
        """Initialize with feedback text."""
        super().__init__(timeout)
        self.feedback = feedback

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command to resume with feedback.

        Note: This uses context.session_id as the Claude session to resume.
        """
        if not context.session_id:
            raise ValueError("ResumeWithFeedbackStrategy requires session_id in context")

        cmd = [get_claude_executable(), "--resume", context.session_id]

        # Add custom system prompt for flexibility
        cmd.extend(["--append-system-prompt", self.TASK_SYSTEM_PROMPT])

        # Add the feedback as a new prompt
        cmd.extend(["-p", self.feedback])

        # Stay in plan mode
        cmd.extend(["--permission-mode", "plan"])

        # Add output format - stream-json for consistent parsing
        cmd.extend(["--output-format", "stream-json", "--verbose"])
        # Include partial messages for real-time streaming
        cmd.append("--include-partial-messages")

        return cmd
