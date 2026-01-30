"""CodeGeass - Claude Code Scheduler Framework.

Orchestrate automated Claude Code sessions with templates, prompts and skills,
executed via CRON with your Pro/Max subscription.
"""

__version__ = "0.1.3"

from codegeass.core.entities import Skill, Task, Template
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus

__all__ = [
    "__version__",
    "Task",
    "Template",
    "Skill",
    "ExecutionResult",
    "ExecutionStatus",
]
