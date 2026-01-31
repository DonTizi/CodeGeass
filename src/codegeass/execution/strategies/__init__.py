"""Execution strategies for Claude Code invocation."""

from codegeass.execution.strategies.autonomous import AutonomousStrategy
from codegeass.execution.strategies.base import BaseStrategy
from codegeass.execution.strategies.claude_cli import get_claude_executable
from codegeass.execution.strategies.context import ExecutionContext, ExecutionStrategy
from codegeass.execution.strategies.headless import HeadlessStrategy
from codegeass.execution.strategies.plan_mode import (
    PlanModeStrategy,
    ResumeContext,
    ResumeWithApprovalStrategy,
    ResumeWithFeedbackStrategy,
)
from codegeass.execution.strategies.provider import ProviderStrategy
from codegeass.execution.strategies.skill import AppendSystemPromptStrategy, SkillStrategy

__all__ = [
    "BaseStrategy",
    "ExecutionContext",
    "ExecutionStrategy",
    "HeadlessStrategy",
    "AutonomousStrategy",
    "SkillStrategy",
    "AppendSystemPromptStrategy",
    "PlanModeStrategy",
    "ResumeContext",
    "ResumeWithApprovalStrategy",
    "ResumeWithFeedbackStrategy",
    "ProviderStrategy",
    "get_claude_executable",
]
