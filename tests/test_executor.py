"""Tests for execution layer."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from codegeass.core.entities import Skill, Task
from codegeass.core.value_objects import ExecutionStatus
from codegeass.execution.strategies import (
    ExecutionContext,
    HeadlessStrategy,
    AutonomousStrategy,
    SkillStrategy,
)


class TestExecutionStrategies:
    """Tests for execution strategies."""

    @pytest.fixture(autouse=True)
    def mock_claude_executable(self):
        """Mock get_claude_executable in all strategy modules."""
        with (
            patch(
                "codegeass.execution.strategies.headless.get_claude_executable",
                return_value="claude",
            ),
            patch(
                "codegeass.execution.strategies.autonomous.get_claude_executable",
                return_value="claude",
            ),
            patch(
                "codegeass.execution.strategies.skill.get_claude_executable",
                return_value="claude",
            ),
        ):
            yield

    @pytest.fixture
    def task(self, tmp_path):
        """Create a test task."""
        return Task.create(
            name="test-task",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            prompt="Run tests",
            model="sonnet",
        )

    @pytest.fixture
    def skill(self, tmp_path):
        """Create a test skill."""
        return Skill(
            name="test-skill",
            path=tmp_path / "SKILL.md",
            description="Test skill",
            allowed_tools=["Read", "Grep"],
            context="fork",
            agent="Explore",
        )

    @pytest.fixture
    def context(self, task, tmp_path):
        """Create execution context."""
        return ExecutionContext(
            task=task,
            skill=None,
            prompt="Run tests",
            working_dir=tmp_path,
        )

    def test_headless_strategy_build_command(self, context):
        strategy = HeadlessStrategy()
        command = strategy.build_command(context)

        # command is a list, check for expected elements
        cmd_str = " ".join(str(c) for c in command)
        assert "claude" in cmd_str
        assert "-p" in command
        assert "Run tests" in command
        assert "--output-format" in command
        assert any("json" in str(c) for c in command)
        assert "--model" in command
        assert "sonnet" in command

    def test_headless_strategy_no_dangerous_flag(self, context):
        strategy = HeadlessStrategy()
        command = strategy.build_command(context)

        assert "--dangerously-skip-permissions" not in command

    def test_autonomous_strategy_has_dangerous_flag(self, context):
        strategy = AutonomousStrategy()
        command = strategy.build_command(context)

        assert "--dangerously-skip-permissions" in command

    def test_skill_strategy_invokes_skill(self, task, skill, tmp_path):
        context = ExecutionContext(
            task=task,
            skill=skill,
            prompt="/path/to/project",
            working_dir=tmp_path,
        )

        strategy = SkillStrategy()
        command = strategy.build_command(context)

        assert "/test-skill" in command[2]  # Skill invocation in prompt

    def test_strategy_adds_max_turns(self, task, tmp_path):
        task.max_turns = 10
        context = ExecutionContext(
            task=task,
            skill=None,
            prompt="Test",
            working_dir=tmp_path,
        )

        strategy = HeadlessStrategy()
        command = strategy.build_command(context)

        assert "--max-turns" in command
        assert "10" in command

    def test_strategy_adds_allowed_tools(self, task, tmp_path):
        task.allowed_tools = ["Read", "Grep", "Glob"]
        context = ExecutionContext(
            task=task,
            skill=None,
            prompt="Test",
            working_dir=tmp_path,
        )

        strategy = HeadlessStrategy()
        command = strategy.build_command(context)

        assert "--allowedTools" in command
        assert "Read,Grep,Glob" in command


class TestExecutionContext:
    """Tests for ExecutionContext."""

    def test_context_creation(self, tmp_path):
        task = Task.create(
            name="test",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            prompt="Test prompt",
        )

        context = ExecutionContext(
            task=task,
            skill=None,
            prompt="Test prompt",
            working_dir=tmp_path,
            session_id="test-session",
        )

        assert context.task == task
        assert context.prompt == "Test prompt"
        assert context.session_id == "test-session"


class TestStrategyExecution:
    """Tests for actual strategy execution (mocked)."""

    @pytest.fixture(autouse=True)
    def mock_claude_executable(self):
        """Mock get_claude_executable in all strategy modules."""
        with (
            patch(
                "codegeass.execution.strategies.headless.get_claude_executable",
                return_value="claude",
            ),
            patch(
                "codegeass.execution.strategies.autonomous.get_claude_executable",
                return_value="claude",
            ),
            patch(
                "codegeass.execution.strategies.skill.get_claude_executable",
                return_value="claude",
            ),
        ):
            yield

    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess.run."""
        with patch("codegeass.execution.strategies.base.subprocess.run") as mock:
            mock.return_value = MagicMock(
                returncode=0,
                stdout='{"result": "success"}',
                stderr="",
            )
            yield mock

    def test_execute_success(self, mock_subprocess, tmp_path):
        task = Task.create(
            name="test",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            prompt="Test",
        )
        context = ExecutionContext(
            task=task,
            skill=None,
            prompt="Test",
            working_dir=tmp_path,
        )

        strategy = HeadlessStrategy()
        result = strategy.execute(context)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.task_id == task.id
        assert '{"result": "success"}' in result.output

    def test_execute_failure(self, mock_subprocess, tmp_path):
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: something went wrong",
        )

        task = Task.create(
            name="test",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            prompt="Test",
        )
        context = ExecutionContext(
            task=task,
            skill=None,
            prompt="Test",
            working_dir=tmp_path,
        )

        strategy = HeadlessStrategy()
        result = strategy.execute(context)

        assert result.status == ExecutionStatus.FAILURE
        assert result.error is not None

    def test_execute_timeout(self, tmp_path):
        import subprocess

        with patch("codegeass.execution.strategies.base.subprocess.run") as mock:
            mock.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=300)

            task = Task.create(
                name="test",
                schedule="0 9 * * *",
                working_dir=tmp_path,
                prompt="Test",
                timeout=300,
            )
            context = ExecutionContext(
                task=task,
                skill=None,
                prompt="Test",
                working_dir=tmp_path,
            )

            strategy = HeadlessStrategy()
            result = strategy.execute(context)

            assert result.status == ExecutionStatus.TIMEOUT
            assert "timed out" in result.error.lower()

    def test_execute_unsets_api_key(self, mock_subprocess, tmp_path):
        """Verify that ANTHROPIC_API_KEY is not passed to subprocess."""
        import os

        # Set a dummy API key
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            task = Task.create(
                name="test",
                schedule="0 9 * * *",
                working_dir=tmp_path,
                prompt="Test",
            )
            context = ExecutionContext(
                task=task,
                skill=None,
                prompt="Test",
                working_dir=tmp_path,
            )

            strategy = HeadlessStrategy()
            strategy.execute(context)

            # Check that subprocess was called with env that doesn't have API key
            call_kwargs = mock_subprocess.call_args.kwargs
            env = call_kwargs.get("env", {})
            assert "ANTHROPIC_API_KEY" not in env
