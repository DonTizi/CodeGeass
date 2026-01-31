"""Filter service for composable task filtering using the Specification pattern."""

from dataclasses import dataclass, field

from codegeass.core.entities import Task
from codegeass.core.specifications import (
    AlwaysTrueSpec,
    EnabledSpec,
    HasAnyTagSpec,
    ModelSpec,
    Specification,
    StatusSpec,
    TextSearchSpec,
)


@dataclass
class TaskFilter:
    """Filter criteria for tasks.

    All filter fields are optional. When specified, they are combined with AND logic.
    For tags, any matching tag will satisfy the filter (OR within tags).
    """

    search: str | None = None  # Full-text search across name, prompt, skill, tags
    name: str | None = None  # Name contains (deprecated, use search)
    tags: list[str] = field(default_factory=list)  # Any of these tags
    status: str | None = None  # Last execution status (success, failed, never_run)
    enabled: bool | None = None  # Enabled/disabled state
    model: str | None = None  # Model name (sonnet, haiku, opus)


class FilterService:
    """Service for filtering tasks using specifications.

    This is the single source of truth for task filtering logic.
    Both CLI and Dashboard should use this service.
    """

    def build_specification(self, filter_criteria: TaskFilter) -> Specification[Task]:
        """Build a composite specification from filter criteria.

        Args:
            filter_criteria: TaskFilter with optional filter fields

        Returns:
            A specification that combines all specified filters with AND logic
        """
        specs: list[Specification[Task]] = []

        # Full-text search
        if filter_criteria.search:
            specs.append(TextSearchSpec(filter_criteria.search))

        # Tags filter (any of the tags)
        if filter_criteria.tags:
            specs.append(HasAnyTagSpec(filter_criteria.tags))

        # Status filter
        if filter_criteria.status:
            specs.append(StatusSpec(filter_criteria.status))

        # Enabled filter
        if filter_criteria.enabled is not None:
            specs.append(EnabledSpec(filter_criteria.enabled))

        # Model filter
        if filter_criteria.model:
            specs.append(ModelSpec(filter_criteria.model))

        # Combine all specs with AND
        if not specs:
            return AlwaysTrueSpec()

        result = specs[0]
        for spec in specs[1:]:
            result = result & spec

        return result

    def filter_tasks(
        self, tasks: list[Task], filter_criteria: TaskFilter
    ) -> list[Task]:
        """Filter tasks based on criteria.

        Args:
            tasks: List of tasks to filter
            filter_criteria: Filter criteria to apply

        Returns:
            List of tasks matching all criteria
        """
        spec = self.build_specification(filter_criteria)
        return [task for task in tasks if spec.is_satisfied_by(task)]
