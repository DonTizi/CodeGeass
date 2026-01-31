"""Validation utilities for task execution."""

from codegeass.core.entities import Task
from codegeass.core.exceptions import ExecutionError
from codegeass.providers import ProviderCapabilityError
from codegeass.providers.base import ExecutionRequest


def validate_working_dir(task: Task) -> None:
    """Validate that the working directory exists.

    Raises:
        ExecutionError: If working directory doesn't exist
    """
    if not task.working_dir.exists():
        raise ExecutionError(
            f"Working directory does not exist: {task.working_dir}",
            task_id=task.id,
        )


def validate_provider_capabilities(
    task: Task,
    provider_registry: object,
    force_plan_mode: bool = False,
) -> None:
    """Validate that the task's provider supports the requested capabilities.

    Args:
        task: The task to validate
        provider_registry: Provider registry for getting provider
        force_plan_mode: Whether plan mode is being forced

    Raises:
        ProviderCapabilityError: If provider doesn't support a requested capability
    """
    provider_name = task.code_source or "claude"
    provider = provider_registry.get(provider_name)  # type: ignore[union-attr]

    # Build a request to validate
    effective_plan_mode = force_plan_mode or task.plan_mode
    request = ExecutionRequest(
        prompt=task.prompt or "",
        working_dir=task.working_dir,
        plan_mode=effective_plan_mode,
        autonomous=task.autonomous,
        session_id=None,
    )

    is_valid, error = provider.validate_request(request)
    if not is_valid:
        raise ProviderCapabilityError(provider_name, "capability", error)
