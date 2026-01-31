"""Main executor for Claude Code tasks.

This module re-exports from the executor/ package for backward compatibility.
The functionality is now split into:
- executor/core.py: Main ClaudeExecutor class
- executor/environment.py: ExecutionEnvironment and worktree management
- executor/strategy_selector.py: Strategy selection logic
- executor/context_builder.py: Build execution context
- executor/validation.py: Validation utilities
"""

from codegeass.execution.executor import ClaudeExecutor, ExecutionEnvironment

__all__ = [
    "ClaudeExecutor",
    "ExecutionEnvironment",
]
