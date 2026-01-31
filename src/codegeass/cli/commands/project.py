"""Project management CLI commands for multi-project support.

This module re-exports from the project/ package for backward compatibility.
The functionality is now split into:
- project/list_show.py: list and show commands
- project/add_remove.py: add and remove commands
- project/init_control.py: init, enable, disable, set-default, update commands
- project/utils.py: shared utility functions
"""

from codegeass.cli.commands.project import project

__all__ = ["project"]
