"""Tests for core entities."""

from pathlib import Path
import pytest

from codegeass.core.entities import Prompt, Skill, Task, Template
from codegeass.core.exceptions import SkillNotFoundError, ValidationError
from codegeass.core.value_objects import CronExpression, ExecutionResult, ExecutionStatus


class TestCronExpression:
    """Tests for CronExpression value object."""

    def test_valid_expression(self):
        cron = CronExpression("0 9 * * 1-5")
        assert cron.expression == "0 9 * * 1-5"

    def test_invalid_expression_raises(self):
        with pytest.raises(ValidationError):
            CronExpression("invalid cron")

    def test_is_due_within_window(self):
        # Use a past expression that we can check
        cron = CronExpression("* * * * *")  # Every minute
        # This should always be "due" since it runs every minute
        assert cron.is_due(window_seconds=120)

    def test_describe_common_patterns(self):
        assert CronExpression("* * * * *").describe() == "Every minute"
        assert "9:00" in CronExpression("0 9 * * *").describe()


class TestTask:
    """Tests for Task entity."""

    def test_create_with_skill(self, tmp_path):
        task = Task.create(
            name="test-task",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            skill="code-review",
        )
        assert task.name == "test-task"
        assert task.skill == "code-review"
        assert task.prompt is None
        assert task.enabled is True

    def test_create_with_prompt(self, tmp_path):
        task = Task.create(
            name="test-task",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            prompt="Run tests",
        )
        assert task.prompt == "Run tests"
        assert task.skill is None

    def test_create_requires_skill_or_prompt(self, tmp_path):
        with pytest.raises(ValidationError):
            Task.create(
                name="test-task",
                schedule="0 9 * * *",
                working_dir=tmp_path,
            )

    def test_create_validates_cron(self, tmp_path):
        with pytest.raises(ValidationError):
            Task.create(
                name="test-task",
                schedule="invalid",
                working_dir=tmp_path,
                skill="test",
            )

    def test_to_dict_and_from_dict(self, tmp_path):
        task = Task.create(
            name="test-task",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            skill="code-review",
            model="opus",
            autonomous=True,
        )
        data = task.to_dict()
        restored = Task.from_dict(data)

        assert restored.name == task.name
        assert restored.schedule == task.schedule
        assert restored.skill == task.skill
        assert restored.model == task.model
        assert restored.autonomous == task.autonomous


class TestSkill:
    """Tests for Skill entity."""

    def test_from_skill_content(self, tmp_path):
        content = """---
name: test-skill
description: A test skill
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

# Test Skill

Instructions for $ARGUMENTS.
"""
        skill = Skill.from_skill_content("test", tmp_path / "SKILL.md", content)

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.context == "fork"
        assert skill.agent == "Explore"
        assert "Read" in skill.allowed_tools
        assert "Grep" in skill.allowed_tools
        assert "Glob" in skill.allowed_tools

    def test_render_content_replaces_arguments(self, tmp_path):
        content = """---
name: test
description: Test
---

Review code at $ARGUMENTS.
"""
        skill = Skill.from_skill_content("test", tmp_path / "SKILL.md", content)
        rendered = skill.render_content("/path/to/project")

        assert "/path/to/project" in rendered
        assert "$ARGUMENTS" not in rendered

    def test_get_dynamic_commands(self, tmp_path):
        content = """---
name: test
description: Test
---

Context: !`git status`
Branch: !`git branch --show-current`
"""
        skill = Skill.from_skill_content("test", tmp_path / "SKILL.md", content)
        commands = skill.get_dynamic_commands()

        assert "git status" in commands
        assert "git branch --show-current" in commands


class TestTemplate:
    """Tests for Template entity."""

    def test_render_prompt(self):
        template = Template(
            name="test",
            description="Test template",
            prompt_template="Review {{ project_name }} for {{ focus }}",
            variables={"focus": "security"},
        )
        rendered = template.render_prompt({"project_name": "MyApp"})

        assert "MyApp" in rendered
        assert "security" in rendered

    def test_from_dict(self):
        data = {
            "name": "code-review",
            "description": "Code review template",
            "default_skills": ["code-review"],
            "model": "sonnet",
            "timeout": 600,
        }
        template = Template.from_dict(data)

        assert template.name == "code-review"
        assert template.default_skills == ["code-review"]
        assert template.model == "sonnet"
        assert template.timeout == 600


class TestPrompt:
    """Tests for Prompt entity."""

    def test_render_full_prompt(self):
        prompt = Prompt(
            system="You are a code reviewer.",
            task="Review the changes in {{ file_path }}.",
            context="Focus on {{ focus_area }}.",
        )
        rendered = prompt.render({"file_path": "main.py", "focus_area": "security"})

        assert "code reviewer" in rendered
        assert "main.py" in rendered
        assert "security" in rendered


class TestExecutionResult:
    """Tests for ExecutionResult value object."""

    def test_duration_calculation(self):
        from datetime import datetime, timedelta

        start = datetime.now()
        end = start + timedelta(seconds=30)

        result = ExecutionResult(
            task_id="test",
            session_id="sess-1",
            status=ExecutionStatus.SUCCESS,
            output="Done",
            started_at=start,
            finished_at=end,
        )

        assert result.duration_seconds == 30.0
        assert result.is_success is True

    def test_to_dict_and_from_dict(self):
        from datetime import datetime

        result = ExecutionResult(
            task_id="test",
            session_id="sess-1",
            status=ExecutionStatus.FAILURE,
            output="Error occurred",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            finished_at=datetime(2024, 1, 1, 12, 0, 30),
            error="Test error",
            exit_code=1,
        )

        data = result.to_dict()
        restored = ExecutionResult.from_dict(data)

        assert restored.task_id == result.task_id
        assert restored.status == result.status
        assert restored.error == result.error
        assert restored.exit_code == result.exit_code
