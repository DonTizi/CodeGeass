"""Executor package for Claude Code task execution.

Modules:
- core: Main ClaudeExecutor class
- environment: ExecutionEnvironment and worktree management
- strategy_selector: Strategy selection logic
- context_builder: Build execution context
- validation: Validation utilities
"""

from codegeass.execution.executor.core import ClaudeExecutor
from codegeass.execution.executor.environment import ExecutionEnvironment

__all__ = [
    "ClaudeExecutor",
    "ExecutionEnvironment",
]
