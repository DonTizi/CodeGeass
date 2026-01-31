"""CodeGeass - Claude Code Scheduler Framework.

Orchestrate automated Claude Code sessions with templates, prompts and skills,
executed via CRON with your Pro/Max subscription.
"""

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("codegeass")
except Exception:
    __version__ = "unknown"  # fallback for editable installs without metadata

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
