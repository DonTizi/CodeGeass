"""Task management CLI commands.

This module re-exports from the task/ package for backward compatibility.
The functionality is now split into:
- task/list_show.py: list and show commands
- task/create.py: create command
- task/run_control.py: run, enable, disable, delete, stop commands
- task/update_stats.py: update and stats commands
"""

from codegeass.cli.commands.task import task

__all__ = ["task"]
