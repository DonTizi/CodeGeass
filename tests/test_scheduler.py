"""Tests for scheduling layer."""

from datetime import datetime, timedelta
from pathlib import Path
import pytest

from codegeass.core.entities import Task
from codegeass.scheduling.cron_parser import CronParser


class TestCronParser:
    """Tests for CronParser utility."""

    def test_validate_valid_expressions(self):
        assert CronParser.validate("0 9 * * *") is True
        assert CronParser.validate("*/15 * * * *") is True
        assert CronParser.validate("0 0 1 * *") is True
        assert CronParser.validate("0 9 * * 1-5") is True

    def test_validate_invalid_expressions(self):
        assert CronParser.validate("invalid") is False
        assert CronParser.validate("60 9 * * *") is False  # minute > 59
        assert CronParser.validate("0 25 * * *") is False  # hour > 23

    def test_normalize_aliases(self):
        assert CronParser.normalize("@daily") == "0 0 * * *"
        assert CronParser.normalize("@hourly") == "0 * * * *"
        assert CronParser.normalize("@weekly") == "0 0 * * 0"

    def test_get_next(self):
        base = datetime(2024, 1, 15, 8, 0, 0)  # Monday 8:00
        next_run = CronParser.get_next("0 9 * * *", base)

        assert next_run.hour == 9
        assert next_run.minute == 0

    def test_get_next_n(self):
        base = datetime(2024, 1, 15, 8, 0, 0)
        next_runs = CronParser.get_next_n("0 9 * * *", 3, base)

        assert len(next_runs) == 3
        # Each should be at 9:00
        for run in next_runs:
            assert run.hour == 9

    def test_describe_patterns(self):
        assert CronParser.describe("* * * * *") == "Every minute"
        assert CronParser.describe("0 * * * *") == "Every hour"
        assert CronParser.describe("0 0 * * *") == "Daily at midnight"
        assert "09:00" in CronParser.describe("0 9 * * *")

    def test_describe_aliases(self):
        assert CronParser.describe("@daily") == "Daily"
        assert CronParser.describe("@hourly") == "Hourly"

    def test_is_due(self):
        # Every minute expression should always be "due"
        assert CronParser.is_due("* * * * *", window_seconds=120) is True

    def test_parse_field_star(self):
        values = CronParser.parse_field("*", 0, 59)
        assert values == list(range(0, 60))

    def test_parse_field_range(self):
        values = CronParser.parse_field("1-5", 0, 59)
        assert values == [1, 2, 3, 4, 5]

    def test_parse_field_step(self):
        values = CronParser.parse_field("*/15", 0, 59)
        assert values == [0, 15, 30, 45]

    def test_parse_field_list(self):
        values = CronParser.parse_field("1,15,30", 0, 59)
        assert values == [1, 15, 30]


class TestSchedulerIntegration:
    """Integration tests for scheduler components."""

    @pytest.fixture
    def test_task(self, tmp_path):
        """Create a test task."""
        return Task.create(
            name="test-task",
            schedule="* * * * *",  # Every minute
            working_dir=tmp_path,
            skill="test-skill",
        )

    def test_task_is_due(self, test_task):
        """Test that a task with every-minute schedule is due."""
        assert test_task.is_due(window_seconds=120) is True

    def test_task_cron_property(self, test_task):
        """Test that task.cron returns CronExpression."""
        cron = test_task.cron
        assert cron.expression == "* * * * *"

    def test_task_update_last_run(self, test_task):
        """Test updating task last run status."""
        test_task.update_last_run("success")

        assert test_task.last_status == "success"
        assert test_task.last_run is not None
