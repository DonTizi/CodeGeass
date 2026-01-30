"""Execution layer - Claude Code execution strategies and session management."""

from codegeass.execution.executor import ClaudeExecutor
from codegeass.execution.plan_service import (
    PlanApprovalService,
    get_plan_approval_service,
    reset_plan_approval_service,
)
from codegeass.execution.session import SessionManager
from codegeass.execution.strategies import (
    AutonomousStrategy,
    ExecutionContext,
    ExecutionStrategy,
    HeadlessStrategy,
    PlanModeStrategy,
    ResumeWithApprovalStrategy,
    ResumeWithFeedbackStrategy,
    SkillStrategy,
    get_claude_executable,
)
from codegeass.execution.tracker import (
    ActiveExecution,
    ExecutionTracker,
    get_execution_tracker,
)

__all__ = [
    # Strategies
    "ExecutionStrategy",
    "ExecutionContext",
    "HeadlessStrategy",
    "AutonomousStrategy",
    "SkillStrategy",
    "PlanModeStrategy",
    "ResumeWithApprovalStrategy",
    "ResumeWithFeedbackStrategy",
    "get_claude_executable",
    # Session management
    "SessionManager",
    "ClaudeExecutor",
    # Tracker
    "ActiveExecution",
    "ExecutionTracker",
    "get_execution_tracker",
    # Plan service
    "PlanApprovalService",
    "get_plan_approval_service",
    "reset_plan_approval_service",
]
