"""Tests for the FilterService."""

from pathlib import Path

import pytest

from codegeass.core.entities import Task
from codegeass.factory.filter_service import FilterService, TaskFilter


@pytest.fixture
def tasks() -> list[Task]:
    """Create a list of sample tasks for filtering tests."""
    return [
        Task.create(
            name="daily-backup",
            schedule="0 0 * * *",
            working_dir=Path("/tmp"),
            prompt="Run daily backup",
            model="sonnet",
            tags=["backup", "production"],
            enabled=True,
        ),
        Task.create(
            name="weekly-cleanup",
            schedule="0 0 * * 0",
            working_dir=Path("/tmp"),
            prompt="Clean up old files",
            model="haiku",
            tags=["cleanup", "maintenance"],
            enabled=False,
        ),
        Task.create(
            name="code-review",
            schedule="0 12 * * *",
            working_dir=Path("/tmp"),
            skill="code-review",
            model="opus",
            tags=["review", "qa", "production"],
            enabled=True,
        ),
        Task.create(
            name="deploy-staging",
            schedule="0 18 * * *",
            working_dir=Path("/tmp"),
            prompt="Deploy to staging environment",
            model="sonnet",
            tags=["deploy", "staging"],
            enabled=True,
        ),
    ]


@pytest.fixture
def filter_service() -> FilterService:
    """Create FilterService instance."""
    return FilterService()


class TestTaskFilter:
    """Test TaskFilter dataclass."""

    def test_default_values(self) -> None:
        """Test default filter values."""
        f = TaskFilter()
        assert f.search is None
        assert f.name is None
        assert f.tags == []
        assert f.status is None
        assert f.enabled is None
        assert f.model is None

    def test_with_values(self) -> None:
        """Test filter with specified values."""
        f = TaskFilter(
            search="backup",
            tags=["production"],
            enabled=True,
            model="sonnet",
        )
        assert f.search == "backup"
        assert f.tags == ["production"]
        assert f.enabled is True
        assert f.model == "sonnet"


class TestFilterService:
    """Test FilterService."""

    def test_no_filters(self, filter_service: FilterService, tasks: list[Task]) -> None:
        """Test filtering with no criteria returns all tasks."""
        result = filter_service.filter_tasks(tasks, TaskFilter())
        assert len(result) == 4

    def test_search_filter(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test search filter."""
        result = filter_service.filter_tasks(tasks, TaskFilter(search="backup"))
        assert len(result) == 1
        assert result[0].name == "daily-backup"

    def test_search_in_skill(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test search matches skill name."""
        result = filter_service.filter_tasks(tasks, TaskFilter(search="review"))
        assert len(result) == 1
        assert result[0].name == "code-review"

    def test_search_in_tags(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test search matches tags."""
        result = filter_service.filter_tasks(tasks, TaskFilter(search="staging"))
        assert len(result) == 1
        assert result[0].name == "deploy-staging"

    def test_tags_filter_single(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test filtering by single tag."""
        result = filter_service.filter_tasks(tasks, TaskFilter(tags=["production"]))
        assert len(result) == 2
        names = {t.name for t in result}
        assert names == {"daily-backup", "code-review"}

    def test_tags_filter_multiple(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test filtering by multiple tags (any match)."""
        result = filter_service.filter_tasks(
            tasks, TaskFilter(tags=["backup", "review"])
        )
        assert len(result) == 2
        names = {t.name for t in result}
        assert names == {"daily-backup", "code-review"}

    def test_enabled_filter_true(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test filtering enabled tasks."""
        result = filter_service.filter_tasks(tasks, TaskFilter(enabled=True))
        assert len(result) == 3
        assert all(t.enabled for t in result)

    def test_enabled_filter_false(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test filtering disabled tasks."""
        result = filter_service.filter_tasks(tasks, TaskFilter(enabled=False))
        assert len(result) == 1
        assert result[0].name == "weekly-cleanup"

    def test_model_filter(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test filtering by model."""
        result = filter_service.filter_tasks(tasks, TaskFilter(model="sonnet"))
        assert len(result) == 2
        names = {t.name for t in result}
        assert names == {"daily-backup", "deploy-staging"}

    def test_status_filter_never_run(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test filtering by never_run status."""
        result = filter_service.filter_tasks(tasks, TaskFilter(status="never_run"))
        assert len(result) == 4  # All tasks have never run

    def test_status_filter_success(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test filtering by success status."""
        tasks[0].last_status = "success"
        tasks[1].last_status = "failed"
        result = filter_service.filter_tasks(tasks, TaskFilter(status="success"))
        assert len(result) == 1
        assert result[0].name == "daily-backup"

    def test_combined_filters(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test combining multiple filters with AND logic."""
        result = filter_service.filter_tasks(
            tasks,
            TaskFilter(
                tags=["production"],
                enabled=True,
                model="sonnet",
            ),
        )
        assert len(result) == 1
        assert result[0].name == "daily-backup"

    def test_combined_filters_no_match(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test combined filters that match no tasks."""
        result = filter_service.filter_tasks(
            tasks,
            TaskFilter(
                tags=["production"],
                enabled=False,  # production tasks are all enabled
            ),
        )
        assert len(result) == 0

    def test_search_with_enabled(
        self, filter_service: FilterService, tasks: list[Task]
    ) -> None:
        """Test search combined with enabled filter."""
        result = filter_service.filter_tasks(
            tasks,
            TaskFilter(
                search="deploy",
                enabled=True,
            ),
        )
        assert len(result) == 1
        assert result[0].name == "deploy-staging"


class TestBuildSpecification:
    """Test specification building."""

    def test_empty_filter_returns_always_true(
        self, filter_service: FilterService
    ) -> None:
        """Test that empty filter returns AlwaysTrueSpec."""
        from codegeass.core.specifications import AlwaysTrueSpec

        spec = filter_service.build_specification(TaskFilter())
        assert isinstance(spec, AlwaysTrueSpec)

    def test_single_filter_returns_single_spec(
        self, filter_service: FilterService
    ) -> None:
        """Test that single filter returns correct spec type."""
        from codegeass.core.specifications import TextSearchSpec

        spec = filter_service.build_specification(TaskFilter(search="test"))
        assert isinstance(spec, TextSearchSpec)

    def test_multiple_filters_returns_and_spec(
        self, filter_service: FilterService
    ) -> None:
        """Test that multiple filters are combined with AND."""
        from codegeass.core.specifications import AndSpecification

        spec = filter_service.build_specification(
            TaskFilter(search="test", enabled=True)
        )
        assert isinstance(spec, AndSpecification)
