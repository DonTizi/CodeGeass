"""Project management CLI commands for multi-project support.

Split into modules by functionality:
- list_show: list and show commands
- add_remove: add and remove commands
- init_control: init, enable, disable, set-default, update commands
- utils: shared utility functions
"""

import click

from codegeass.cli.commands.project.add_remove import add_project, remove_project
from codegeass.cli.commands.project.init_control import (
    disable_project,
    enable_project,
    init_project,
    set_default_project,
    update_project,
)
from codegeass.cli.commands.project.list_show import list_projects, show_project


@click.group()
def project() -> None:
    """Manage registered projects."""
    pass


# Register all commands
project.add_command(list_projects)
project.add_command(show_project)
project.add_command(add_project)
project.add_command(remove_project)
project.add_command(set_default_project)
project.add_command(init_project)
project.add_command(enable_project)
project.add_command(disable_project)
project.add_command(update_project)

__all__ = ["project"]
