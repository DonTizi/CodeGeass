"""Tests for the Specification pattern implementation."""

from pathlib import Path

import pytest

from codegeass.core.entities import Task
from codegeass.core.specifications import (
    AlwaysTrueSpec,
    AndSpecification,
    EnabledSpec,
    HasAllTagsSpec,
    HasAnyTagSpec,
    HasTagSpec,
    ModelSpec,
    NameContainsSpec,
    NotSpecification,
    OrSpecification,
    PromptContainsSpec,
    SkillSpec,
    StatusSpec,
    TextSearchSpec,
)


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task.create(
        name="daily-backup",
        schedule="0 0 * * *",
        working_dir=Path("/tmp"),
        prompt="Run backup script",
        model="sonnet",
        tags=["backup", "production"],
    )


@pytest.fixture
def disabled_task() -> Task:
    """Create a disabled task."""
    return Task.create(
        name="weekly-cleanup",
        schedule="0 0 * * 0",
        working_dir=Path("/tmp"),
        prompt="Clean up old files",
        model="haiku",
        enabled=False,
        tags=["cleanup"],
    )


@pytest.fixture
def skill_task() -> Task:
    """Create a task using a skill."""
    return Task.create(
        name="code-review-task",
        schedule="0 12 * * *",
        working_dir=Path("/tmp"),
        skill="code-review",
        model="opus",
        tags=["review", "qa"],
    )


class TestBaseSpecification:
    """Test base specification operations."""

    def test_and_combination(self, sample_task: Task) -> None:
        """Test AND combination of specifications."""
        enabled_spec = EnabledSpec(True)
        name_spec = NameContainsSpec("backup")

        combined = enabled_spec & name_spec
        assert isinstance(combined, AndSpecification)
        assert combined.is_satisfied_by(sample_task) is True

    def test_or_combination(self, sample_task: Task, disabled_task: Task) -> None:
        """Test OR combination of specifications."""
        backup_spec = NameContainsSpec("backup")
        cleanup_spec = NameContainsSpec("cleanup")

        combined = backup_spec | cleanup_spec
        assert isinstance(combined, OrSpecification)
        assert combined.is_satisfied_by(sample_task) is True
        assert combined.is_satisfied_by(disabled_task) is True

    def test_not_specification(self, sample_task: Task, disabled_task: Task) -> None:
        """Test NOT specification."""
        enabled_spec = EnabledSpec(True)
        not_enabled = ~enabled_spec

        assert isinstance(not_enabled, NotSpecification)
        assert not_enabled.is_satisfied_by(sample_task) is False
        assert not_enabled.is_satisfied_by(disabled_task) is True

    def test_always_true_spec(self, sample_task: Task) -> None:
        """Test AlwaysTrueSpec."""
        spec = AlwaysTrueSpec()
        assert spec.is_satisfied_by(sample_task) is True


class TestNameContainsSpec:
    """Test NameContainsSpec."""

    def test_matches_substring(self, sample_task: Task) -> None:
        """Test matching substring in name."""
        spec = NameContainsSpec("backup")
        assert spec.is_satisfied_by(sample_task) is True

    def test_case_insensitive(self, sample_task: Task) -> None:
        """Test case insensitive matching."""
        spec = NameContainsSpec("BACKUP")
        assert spec.is_satisfied_by(sample_task) is True

    def test_no_match(self, sample_task: Task) -> None:
        """Test non-matching substring."""
        spec = NameContainsSpec("deploy")
        assert spec.is_satisfied_by(sample_task) is False


class TestHasTagSpec:
    """Test HasTagSpec."""

    def test_has_tag(self, sample_task: Task) -> None:
        """Test matching tag."""
        spec = HasTagSpec("backup")
        assert spec.is_satisfied_by(sample_task) is True

    def test_case_insensitive(self, sample_task: Task) -> None:
        """Test case insensitive tag matching."""
        spec = HasTagSpec("PRODUCTION")
        assert spec.is_satisfied_by(sample_task) is True

    def test_missing_tag(self, sample_task: Task) -> None:
        """Test non-existing tag."""
        spec = HasTagSpec("deploy")
        assert spec.is_satisfied_by(sample_task) is False


class TestHasAnyTagSpec:
    """Test HasAnyTagSpec."""

    def test_has_any_tag(self, sample_task: Task) -> None:
        """Test matching any of the tags."""
        spec = HasAnyTagSpec(["backup", "deploy"])
        assert spec.is_satisfied_by(sample_task) is True

    def test_has_multiple_matching(self, sample_task: Task) -> None:
        """Test when multiple tags match."""
        spec = HasAnyTagSpec(["backup", "production"])
        assert spec.is_satisfied_by(sample_task) is True

    def test_no_matching_tags(self, sample_task: Task) -> None:
        """Test when no tags match."""
        spec = HasAnyTagSpec(["deploy", "staging"])
        assert spec.is_satisfied_by(sample_task) is False


class TestHasAllTagsSpec:
    """Test HasAllTagsSpec."""

    def test_has_all_tags(self, sample_task: Task) -> None:
        """Test when all tags match."""
        spec = HasAllTagsSpec(["backup", "production"])
        assert spec.is_satisfied_by(sample_task) is True

    def test_missing_one_tag(self, sample_task: Task) -> None:
        """Test when one tag is missing."""
        spec = HasAllTagsSpec(["backup", "deploy"])
        assert spec.is_satisfied_by(sample_task) is False


class TestEnabledSpec:
    """Test EnabledSpec."""

    def test_enabled_true(self, sample_task: Task, disabled_task: Task) -> None:
        """Test matching enabled tasks."""
        spec = EnabledSpec(True)
        assert spec.is_satisfied_by(sample_task) is True
        assert spec.is_satisfied_by(disabled_task) is False

    def test_enabled_false(self, sample_task: Task, disabled_task: Task) -> None:
        """Test matching disabled tasks."""
        spec = EnabledSpec(False)
        assert spec.is_satisfied_by(sample_task) is False
        assert spec.is_satisfied_by(disabled_task) is True


class TestModelSpec:
    """Test ModelSpec."""

    def test_matches_model(self, sample_task: Task) -> None:
        """Test matching model."""
        spec = ModelSpec("sonnet")
        assert spec.is_satisfied_by(sample_task) is True

    def test_case_insensitive(self, sample_task: Task) -> None:
        """Test case insensitive model matching."""
        spec = ModelSpec("SONNET")
        assert spec.is_satisfied_by(sample_task) is True

    def test_different_model(self, sample_task: Task) -> None:
        """Test non-matching model."""
        spec = ModelSpec("opus")
        assert spec.is_satisfied_by(sample_task) is False


class TestStatusSpec:
    """Test StatusSpec."""

    def test_never_run(self, sample_task: Task) -> None:
        """Test matching never run status."""
        spec = StatusSpec("never_run")
        assert spec.is_satisfied_by(sample_task) is True

    def test_with_status(self, sample_task: Task) -> None:
        """Test matching specific status."""
        sample_task.last_status = "success"
        spec = StatusSpec("success")
        assert spec.is_satisfied_by(sample_task) is True

    def test_wrong_status(self, sample_task: Task) -> None:
        """Test non-matching status."""
        sample_task.last_status = "success"
        spec = StatusSpec("failed")
        assert spec.is_satisfied_by(sample_task) is False


class TestTextSearchSpec:
    """Test TextSearchSpec."""

    def test_search_in_name(self, sample_task: Task) -> None:
        """Test searching in task name."""
        spec = TextSearchSpec("backup")
        assert spec.is_satisfied_by(sample_task) is True

    def test_search_in_prompt(self, sample_task: Task) -> None:
        """Test searching in prompt."""
        spec = TextSearchSpec("script")
        assert spec.is_satisfied_by(sample_task) is True

    def test_search_in_tags(self, sample_task: Task) -> None:
        """Test searching in tags."""
        spec = TextSearchSpec("production")
        assert spec.is_satisfied_by(sample_task) is True

    def test_search_in_skill(self, skill_task: Task) -> None:
        """Test searching in skill name."""
        spec = TextSearchSpec("review")
        assert spec.is_satisfied_by(skill_task) is True

    def test_no_match(self, sample_task: Task) -> None:
        """Test no match found."""
        spec = TextSearchSpec("deploy")
        assert spec.is_satisfied_by(sample_task) is False


class TestPromptContainsSpec:
    """Test PromptContainsSpec."""

    def test_matches_prompt(self, sample_task: Task) -> None:
        """Test matching prompt content."""
        spec = PromptContainsSpec("backup")
        assert spec.is_satisfied_by(sample_task) is True

    def test_no_prompt(self, skill_task: Task) -> None:
        """Test task without prompt."""
        spec = PromptContainsSpec("something")
        assert spec.is_satisfied_by(skill_task) is False


class TestSkillSpec:
    """Test SkillSpec."""

    def test_matches_skill(self, skill_task: Task) -> None:
        """Test matching skill name."""
        spec = SkillSpec("code-review")
        assert spec.is_satisfied_by(skill_task) is True

    def test_no_skill(self, sample_task: Task) -> None:
        """Test task without skill."""
        spec = SkillSpec("code-review")
        assert spec.is_satisfied_by(sample_task) is False


class TestComplexCombinations:
    """Test complex specification combinations."""

    def test_enabled_and_has_tag(
        self, sample_task: Task, disabled_task: Task
    ) -> None:
        """Test combining enabled and tag specs."""
        spec = EnabledSpec(True) & HasTagSpec("backup")
        assert spec.is_satisfied_by(sample_task) is True
        assert spec.is_satisfied_by(disabled_task) is False

    def test_model_or_enabled(
        self, sample_task: Task, disabled_task: Task, skill_task: Task
    ) -> None:
        """Test OR combination with different specs."""
        spec = ModelSpec("opus") | EnabledSpec(False)
        assert spec.is_satisfied_by(sample_task) is False
        assert spec.is_satisfied_by(disabled_task) is True
        assert spec.is_satisfied_by(skill_task) is True

    def test_triple_and(self, sample_task: Task) -> None:
        """Test three specs combined with AND."""
        spec = EnabledSpec(True) & HasTagSpec("backup") & ModelSpec("sonnet")
        assert spec.is_satisfied_by(sample_task) is True

    def test_not_with_and(self, sample_task: Task, disabled_task: Task) -> None:
        """Test NOT combined with AND."""
        spec = EnabledSpec(True) & ~HasTagSpec("cleanup")
        assert spec.is_satisfied_by(sample_task) is True
        assert spec.is_satisfied_by(disabled_task) is False
