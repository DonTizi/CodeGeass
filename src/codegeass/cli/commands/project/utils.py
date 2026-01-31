"""Utility functions for project commands."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codegeass.cli.main import Context
    from codegeass.storage.project_repository import ProjectRepository


def get_project_repo(ctx: "Context") -> "ProjectRepository":
    """Get project repository from context or create new one."""
    from codegeass.storage.project_repository import ProjectRepository

    if hasattr(ctx, "_project_repo") and ctx._project_repo is not None:
        return ctx._project_repo
    return ProjectRepository()
