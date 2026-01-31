"""Task management CLI commands.

Split into modules by functionality:
- list_show: list and show commands
- create: create command
- run_control: run, enable, disable, delete, stop commands
- update_stats: update and stats commands
"""

import click

from codegeass.cli.commands.task.create import create_task
from codegeass.cli.commands.task.list_show import list_tasks, show_task
from codegeass.cli.commands.task.run_control import (
    delete_task,
    disable_task,
    enable_task,
    run_task,
    stop_task,
)
from codegeass.cli.commands.task.update_stats import stats_task, update_task


@click.group()
def task() -> None:
    """Manage scheduled tasks."""
    pass


# Register all commands
task.add_command(list_tasks)
task.add_command(show_task)
task.add_command(create_task)
task.add_command(run_task)
task.add_command(enable_task)
task.add_command(disable_task)
task.add_command(delete_task)
task.add_command(update_task)
task.add_command(stats_task)
task.add_command(stop_task)

__all__ = ["task"]
