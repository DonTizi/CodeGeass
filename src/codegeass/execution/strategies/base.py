"""Base execution strategy with streaming support."""

import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.strategies.context import ExecutionContext

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker

logger = logging.getLogger(__name__)


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
        if context.tracker and context.execution_id:
            return self._execute_streaming(context)
        else:
            return self._execute_blocking(context)

    def _execute_blocking(self, context: ExecutionContext) -> ExecutionResult:
        """Execute using blocking subprocess.run (original behavior)."""
        started_at = datetime.now()
        command = self.build_command(context)

        try:
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
            return self._timeout_result(context, started_at)
        except Exception as e:
            return self._error_result(context, started_at, str(e))

    def _execute_streaming(self, context: ExecutionContext) -> ExecutionResult:
        """Execute using streaming Popen to emit real-time output events."""
        started_at = datetime.now()
        command = self.build_command(context)
        tracker = context.tracker
        execution_id = context.execution_id

        if not tracker or not execution_id:
            return self._execute_blocking(context)

        output_lines: list[str] = []
        stderr_lines: list[str] = []

        try:
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)

            tracker.update_execution(execution_id, status="running", phase="executing")

            process = subprocess.Popen(
                command,
                cwd=context.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1,
            )

            tracker.set_pid(execution_id, process.pid)
            timeout_seconds = context.task.timeout or self.timeout
            deadline = datetime.now().timestamp() + timeout_seconds

            while True:
                if datetime.now().timestamp() > deadline:
                    process.kill()
                    process.wait()
                    tracker.update_execution(execution_id, status="finishing")
                    raise subprocess.TimeoutExpired(command, timeout_seconds)

                return_code = process.poll()
                self._read_process_output(process, output_lines, tracker, execution_id)
                self._read_stderr(process, stderr_lines)

                if return_code is not None:
                    break

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
            return self._timeout_result(context, started_at, "\n".join(output_lines))
        except Exception as e:
            logger.error(f"Streaming execution error: {e}")
            return self._error_result(context, started_at, str(e), "\n".join(output_lines))

    def _read_process_output(
        self,
        process: subprocess.Popen,
        output_lines: list[str],
        tracker: "ExecutionTracker",
        execution_id: str,
    ) -> None:
        """Read stdout from process and emit events."""
        if process.stdout:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                line = line.rstrip("\n")
                output_lines.append(line)
                tracker.append_output(execution_id, line)
                self._detect_phase(tracker, execution_id, line)

    def _read_stderr(self, process: subprocess.Popen, stderr_lines: list[str]) -> None:
        """Read stderr from process."""
        if process.stderr:
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                stderr_lines.append(line.rstrip("\n"))

    def _detect_phase(
        self, tracker: "ExecutionTracker", execution_id: str, line: str
    ) -> None:
        """Try to detect execution phase from stream-json output line."""
        try:
            if not line.startswith("{"):
                return

            data = json.loads(line)
            event_type = data.get("type", "")

            if event_type == "assistant":
                self._handle_assistant_event(tracker, execution_id, data)
            elif event_type == "content_block_start":
                self._handle_content_block_start(tracker, execution_id, data)
            elif event_type == "tool_use":
                tool_name = data.get("name", "unknown")
                tracker.update_execution(execution_id, phase=f"tool: {tool_name}")
            elif event_type == "result":
                tracker.update_execution(execution_id, phase="completing")

        except (json.JSONDecodeError, KeyError):
            pass

    def _handle_assistant_event(
        self, tracker: "ExecutionTracker", execution_id: str, data: dict
    ) -> None:
        """Handle assistant event type."""
        message = data.get("message", {})
        content = message.get("content", [])
        for block in content:
            block_type = block.get("type", "")
            if block_type == "tool_use":
                tool_name = block.get("name", "unknown")
                tracker.update_execution(execution_id, phase=f"tool: {tool_name}")
            elif block_type == "text":
                tracker.update_execution(execution_id, phase="thinking")

    def _handle_content_block_start(
        self, tracker: "ExecutionTracker", execution_id: str, data: dict
    ) -> None:
        """Handle content_block_start event type."""
        content_block = data.get("content_block", {})
        block_type = content_block.get("type", "")
        if block_type == "tool_use":
            tool_name = content_block.get("name", "unknown")
            tracker.update_execution(execution_id, phase=f"tool: {tool_name}")
        elif block_type == "text":
            tracker.update_execution(execution_id, phase="generating")

    def _timeout_result(
        self, context: ExecutionContext, started_at: datetime, output: str = ""
    ) -> ExecutionResult:
        """Create timeout result."""
        return ExecutionResult(
            task_id=context.task.id,
            session_id=context.session_id,
            status=ExecutionStatus.TIMEOUT,
            output=output,
            started_at=started_at,
            finished_at=datetime.now(),
            error=f"Execution timed out after {context.task.timeout or self.timeout}s",
        )

    def _error_result(
        self, context: ExecutionContext, started_at: datetime, error: str, output: str = ""
    ) -> ExecutionResult:
        """Create error result."""
        return ExecutionResult(
            task_id=context.task.id,
            session_id=context.session_id,
            status=ExecutionStatus.FAILURE,
            output=output,
            started_at=started_at,
            finished_at=datetime.now(),
            error=error,
        )
