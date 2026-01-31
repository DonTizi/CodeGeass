"""Provider-based execution strategy.

This strategy wraps a CodeProvider to execute tasks using non-Claude providers
like OpenAI Codex while maintaining compatibility with the existing strategy pattern.
"""

import subprocess
from datetime import datetime

from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.context import ExecutionContext
from codegeass.providers.base import CodeProvider, ExecutionRequest


class ProviderStrategy(BaseStrategy):
    """Generic execution strategy that wraps a CodeProvider.

    This allows non-Claude providers to be used with the existing executor
    by delegating command building and output parsing to the provider.
    """

    def __init__(self, provider: CodeProvider):
        """Initialize with a code provider.

        Args:
            provider: The code provider to use for execution
        """
        self._provider = provider

    @property
    def provider(self) -> CodeProvider:
        """Get the underlying provider."""
        return self._provider

    def _build_execution_request(self, context: ExecutionContext) -> ExecutionRequest:
        """Build an ExecutionRequest from an ExecutionContext.

        Args:
            context: The execution context

        Returns:
            ExecutionRequest for the provider
        """
        return ExecutionRequest(
            prompt=context.prompt,
            working_dir=context.working_dir,
            model=context.task.model or "sonnet",
            timeout=context.task.timeout,
            session_id=context.session_id,
            autonomous=context.task.autonomous,
            plan_mode=context.task.plan_mode,
            max_turns=context.task.max_turns,
            allowed_tools=context.task.allowed_tools or [],
        )

    def build_command(self, context: ExecutionContext) -> list[str]:
        """Build command using the provider's build_command method.

        Args:
            context: The execution context

        Returns:
            List of command arguments
        """
        request = self._build_execution_request(context)
        return self._provider.build_command(request)

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute using the provider.

        Args:
            context: The execution context

        Returns:
            ExecutionResult with execution details
        """
        started_at = datetime.now()
        command = self.build_command(context)

        try:
            # Run the command
            result = subprocess.run(
                command,
                cwd=context.working_dir,
                capture_output=True,
                text=True,
                timeout=context.task.timeout,
            )

            # Parse output using provider
            output_text, session_id = self._provider.parse_output(result.stdout)

            # Determine status based on exit code
            if result.returncode == 0:
                status = ExecutionStatus.SUCCESS
            else:
                status = ExecutionStatus.FAILURE

            return ExecutionResult(
                task_id=context.task.id,
                session_id=session_id or context.session_id or "",
                status=status,
                output=output_text or result.stdout,
                started_at=started_at,
                finished_at=datetime.now(),
                exit_code=result.returncode,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"provider": self._provider.name},
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id or "",
                status=ExecutionStatus.TIMEOUT,
                output="",
                started_at=started_at,
                finished_at=datetime.now(),
                error=f"Execution timed out after {context.task.timeout}s",
                metadata={"provider": self._provider.name},
            )

        except FileNotFoundError:
            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id or "",
                status=ExecutionStatus.FAILURE,
                output="",
                started_at=started_at,
                finished_at=datetime.now(),
                error=f"Provider executable not found: {command[0]}",
                metadata={"provider": self._provider.name},
            )

        except Exception as e:
            return ExecutionResult(
                task_id=context.task.id,
                session_id=context.session_id or "",
                status=ExecutionStatus.FAILURE,
                output="",
                started_at=started_at,
                finished_at=datetime.now(),
                error=str(e),
                metadata={"provider": self._provider.name},
            )
