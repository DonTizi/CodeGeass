"""Provider-based execution strategy.

This strategy wraps a CodeProvider to execute tasks using non-Claude providers
like OpenAI Codex while maintaining compatibility with the existing strategy pattern.
"""

from codegeass.core.value_objects import ExecutionResult
from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.context import ExecutionContext
from codegeass.providers.base import CodeProvider, ExecutionRequest


class ProviderStrategy(BaseStrategy):
    """Generic execution strategy that wraps a CodeProvider.

    This allows non-Claude providers to be used with the existing executor
    by delegating command building and output parsing to the provider.

    Inherits streaming execution from BaseStrategy for real-time output.
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
        """Execute using streaming from BaseStrategy.

        Uses the inherited streaming execution to provide real-time output
        to the dashboard.

        Args:
            context: The execution context

        Returns:
            ExecutionResult with execution details
        """
        # Use BaseStrategy's streaming execute which calls build_command
        # This provides real-time output via tracker.append_output()
        result = super().execute(context)

        # Add provider metadata
        if result.metadata is None:
            result = ExecutionResult(
                task_id=result.task_id,
                session_id=result.session_id,
                status=result.status,
                output=result.output,
                started_at=result.started_at,
                finished_at=result.finished_at,
                exit_code=result.exit_code,
                error=result.error,
                metadata={"provider": self._provider.name},
            )
        else:
            result.metadata["provider"] = self._provider.name

        return result
