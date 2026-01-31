"""Strategy selection for task execution."""

import logging
from typing import TYPE_CHECKING

from codegeass.core.entities import Task
from codegeass.execution.strategies import (
    AutonomousStrategy,
    ExecutionStrategy,
    HeadlessStrategy,
    PlanModeStrategy,
    ProviderStrategy,
    SkillStrategy,
)

if TYPE_CHECKING:
    from codegeass.providers import ProviderRegistry

logger = logging.getLogger(__name__)


class StrategySelector:
    """Selects appropriate execution strategy for tasks."""

    def __init__(self, provider_registry: "ProviderRegistry"):
        self._provider_registry = provider_registry

        # Claude strategy instances (reused)
        self._headless = HeadlessStrategy()
        self._autonomous = AutonomousStrategy()
        self._skill_strategy = SkillStrategy()
        self._plan_mode = PlanModeStrategy()

        # Cache for provider strategies
        self._provider_strategies: dict[str, ProviderStrategy] = {}

    def select(self, task: Task, force_plan_mode: bool = False) -> ExecutionStrategy:
        """Select appropriate execution strategy based on task configuration.

        For Claude provider, uses the battle-tested strategy pattern.
        For other providers, uses the generic ProviderStrategy wrapper.
        """
        provider_name = task.code_source or "claude"

        if provider_name != "claude":
            logger.info(f"Using provider strategy for: {provider_name}")
            return self._get_provider_strategy(provider_name)

        return self._select_claude_strategy(task, force_plan_mode)

    def _select_claude_strategy(
        self, task: Task, force_plan_mode: bool
    ) -> ExecutionStrategy:
        """Select strategy for Claude provider."""
        if force_plan_mode or task.plan_mode:
            return self._plan_mode
        if task.skill:
            return self._skill_strategy
        if task.autonomous:
            return self._autonomous
        return self._headless

    def _get_provider_strategy(self, provider_name: str) -> ProviderStrategy:
        """Get or create a ProviderStrategy for the given provider."""
        if provider_name not in self._provider_strategies:
            provider = self._provider_registry.get(provider_name)
            self._provider_strategies[provider_name] = ProviderStrategy(provider)
        return self._provider_strategies[provider_name]

    @property
    def resume_approval_strategy(self) -> ExecutionStrategy:
        """Get the resume with approval strategy."""
        from codegeass.execution.strategies import ResumeWithApprovalStrategy
        return ResumeWithApprovalStrategy()
