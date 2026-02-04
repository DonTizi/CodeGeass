"""Tests for the hooks system."""

import json
import tempfile
from pathlib import Path

import pytest


class TestHookHandler:
    """Tests for HookHandler model."""

    def test_creation(self):
        """Test HookHandler creation."""
        from codegeass.hooks.models import HookHandler

        handler = HookHandler(
            type="command",
            command="/path/to/script.sh",
            timeout=10,
        )

        assert handler.type == "command"
        assert handler.command == "/path/to/script.sh"
        assert handler.timeout == 10
        assert handler.is_async is False

    def test_to_dict(self):
        """Test HookHandler to_dict conversion."""
        from codegeass.hooks.models import HookHandler

        handler = HookHandler(
            type="command",
            command="/path/to/script.sh",
            timeout=10,
            is_async=True,
        )

        data = handler.to_dict()

        assert data["type"] == "command"
        assert data["command"] == "/path/to/script.sh"
        assert data["timeout"] == 10
        assert data["async"] is True

    def test_from_dict(self):
        """Test HookHandler from_dict creation."""
        from codegeass.hooks.models import HookHandler

        data = {
            "type": "prompt",
            "prompt": "Safety check",
            "async": True,
        }

        handler = HookHandler.from_dict(data)

        assert handler.type == "prompt"
        assert handler.prompt == "Safety check"
        assert handler.is_async is True


class TestHookMatcher:
    """Tests for HookMatcher model."""

    def test_creation(self):
        """Test HookMatcher creation."""
        from codegeass.hooks.models import HookHandler, HookMatcher

        handler = HookHandler(type="command", command="/test.sh")
        matcher = HookMatcher(
            matcher="Bash",
            hooks=(handler,),
        )

        assert matcher.matcher == "Bash"
        assert len(matcher.hooks) == 1

    def test_to_dict(self):
        """Test HookMatcher to_dict conversion."""
        from codegeass.hooks.models import HookHandler, HookMatcher

        handler = HookHandler(type="command", command="/test.sh")
        matcher = HookMatcher(matcher="Bash|Write", hooks=(handler,))

        data = matcher.to_dict()

        assert data["matcher"] == "Bash|Write"
        assert len(data["hooks"]) == 1
        assert data["hooks"][0]["type"] == "command"

    def test_from_dict(self):
        """Test HookMatcher from_dict creation."""
        from codegeass.hooks.models import HookMatcher

        data = {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "/test.sh"}],
        }

        matcher = HookMatcher.from_dict(data)

        assert matcher.matcher == "Bash"
        assert len(matcher.hooks) == 1
        assert matcher.hooks[0].type == "command"


class TestTagHooks:
    """Tests for TagHooks model."""

    def test_creation(self):
        """Test TagHooks creation."""
        from codegeass.hooks.models import TagHooks

        hooks = TagHooks(
            tag="production",
            description="Production safety hooks",
            hooks={
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/test.sh"}]}
                ]
            },
        )

        assert hooks.tag == "production"
        assert hooks.description == "Production safety hooks"
        assert "PreToolUse" in hooks.hooks

    def test_to_claude_settings(self):
        """Test conversion to Claude Code settings format."""
        from codegeass.hooks.models import TagHooks

        hooks = TagHooks(
            tag="production",
            hooks={
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/test.sh"}]}
                ]
            },
        )

        settings = hooks.to_claude_settings()

        assert "hooks" in settings
        assert "PreToolUse" in settings["hooks"]
        assert settings["hooks"]["PreToolUse"][0]["matcher"] == "Bash"

    def test_empty_hooks_returns_empty_settings(self):
        """Test that empty hooks returns empty settings."""
        from codegeass.hooks.models import TagHooks

        hooks = TagHooks(tag="empty", hooks={})
        settings = hooks.to_claude_settings()

        assert settings == {}

    def test_validate_valid_config(self):
        """Test validation of valid config."""
        from codegeass.hooks.models import TagHooks

        hooks = TagHooks(
            tag="valid-tag",
            hooks={
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/test.sh"}]}
                ]
            },
        )

        errors = hooks.validate()
        assert len(errors) == 0

    def test_validate_invalid_event(self):
        """Test validation catches invalid event names."""
        from codegeass.hooks.models import TagHooks

        hooks = TagHooks(
            tag="test",
            hooks={
                "InvalidEvent": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/test.sh"}]}
                ]
            },
        )

        errors = hooks.validate()
        assert any("Unknown hook event" in e for e in errors)

    def test_validate_missing_hooks_field(self):
        """Test validation catches missing hooks field."""
        from codegeass.hooks.models import TagHooks

        hooks = TagHooks(
            tag="test",
            hooks={
                "PreToolUse": [{"matcher": "Bash"}]  # Missing 'hooks' field
            },
        )

        errors = hooks.validate()
        assert any("Missing 'hooks' field" in e for e in errors)

    def test_validate_invalid_handler_type(self):
        """Test validation catches invalid handler type."""
        from codegeass.hooks.models import TagHooks

        hooks = TagHooks(
            tag="test",
            hooks={
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "invalid"}]}
                ]
            },
        )

        errors = hooks.validate()
        assert any("Invalid type" in e for e in errors)


class TestHookRepository:
    """Tests for HookRepository."""

    def test_list_tags_empty(self, tmp_path):
        """Test listing tags when no hooks exist."""
        from codegeass.hooks.repository import HookRepository

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        tags = repo.list_tags()
        assert tags == []

    def test_save_and_get_tag(self, tmp_path):
        """Test saving and retrieving a tag."""
        from codegeass.hooks.models import TagHooks
        from codegeass.hooks.repository import HookRepository

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        hooks = TagHooks(
            tag="test-tag",
            description="Test description",
            hooks={
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/test.sh"}]}
                ]
            },
        )

        repo.save_tag(hooks)

        # Retrieve it
        retrieved = repo.get_tag("test-tag")

        assert retrieved is not None
        assert retrieved.tag == "test-tag"
        assert retrieved.description == "Test description"
        assert "PreToolUse" in retrieved.hooks

    def test_delete_tag(self, tmp_path):
        """Test deleting a tag."""
        from codegeass.hooks.models import TagHooks
        from codegeass.hooks.repository import HookRepository

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        hooks = TagHooks(tag="delete-me", description="To be deleted")
        repo.save_tag(hooks)

        assert repo.exists("delete-me")

        repo.delete_tag("delete-me")

        assert not repo.exists("delete-me")

    def test_project_hooks_take_precedence(self, tmp_path):
        """Test that project hooks take precedence over global hooks."""
        from codegeass.hooks.models import TagHooks
        from codegeass.hooks.repository import HookRepository

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        # Create global hook
        global_hooks = TagHooks(tag="shared", description="Global version")
        repo.save_tag(global_hooks, global_scope=True)

        # Create project hook with same name
        project_hooks = TagHooks(tag="shared", description="Project version")
        repo.save_tag(project_hooks, global_scope=False)

        # Project should take precedence
        retrieved = repo.get_tag("shared")
        assert retrieved is not None
        assert retrieved.description == "Project version"

    def test_get_tag_location(self, tmp_path):
        """Test getting tag location (project vs global)."""
        from codegeass.hooks.models import TagHooks
        from codegeass.hooks.repository import HookRepository

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        global_hooks = TagHooks(tag="global-tag", description="Global")
        repo.save_tag(global_hooks, global_scope=True)

        project_hooks = TagHooks(tag="project-tag", description="Project")
        repo.save_tag(project_hooks, global_scope=False)

        assert repo.get_tag_location("global-tag") == "global"
        assert repo.get_tag_location("project-tag") == "project"
        assert repo.get_tag_location("nonexistent") is None


class TestHookResolver:
    """Tests for HookResolver."""

    def test_resolve_single_tag(self, tmp_path):
        """Test resolving a single tag."""
        from codegeass.hooks.models import TagHooks
        from codegeass.hooks.repository import HookRepository
        from codegeass.hooks.resolver import HookResolver

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        hooks = TagHooks(
            tag="production",
            hooks={
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/test.sh"}]}
                ]
            },
        )
        repo.save_tag(hooks)

        resolver = HookResolver(repo)
        settings = resolver.resolve(["production"])

        assert "hooks" in settings
        assert "PreToolUse" in settings["hooks"]

    def test_resolve_multiple_tags_merge(self, tmp_path):
        """Test that hooks from multiple tags are merged."""
        from codegeass.hooks.models import TagHooks
        from codegeass.hooks.repository import HookRepository
        from codegeass.hooks.resolver import HookResolver

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        # Create two tags
        hooks1 = TagHooks(
            tag="production",
            hooks={
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "/prod.sh"}]}
                ]
            },
        )
        hooks2 = TagHooks(
            tag="audited",
            hooks={
                "PreToolUse": [
                    {"matcher": "Write", "hooks": [{"type": "command", "command": "/audit.sh"}]}
                ],
                "PostToolUse": [
                    {"hooks": [{"type": "command", "command": "/log.sh"}]}
                ],
            },
        )

        repo.save_tag(hooks1)
        repo.save_tag(hooks2)

        resolver = HookResolver(repo)
        settings = resolver.resolve(["production", "audited"])

        assert "hooks" in settings
        # PreToolUse should have hooks from both tags
        assert len(settings["hooks"]["PreToolUse"]) == 2
        # PostToolUse only from audited
        assert "PostToolUse" in settings["hooks"]

    def test_resolve_empty_tags(self, tmp_path):
        """Test resolving with empty tags list."""
        from codegeass.hooks.repository import HookRepository
        from codegeass.hooks.resolver import HookResolver

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        resolver = HookResolver(repo)
        settings = resolver.resolve([])

        assert settings == {}

    def test_resolve_nonexistent_tag(self, tmp_path):
        """Test resolving with nonexistent tag."""
        from codegeass.hooks.repository import HookRepository
        from codegeass.hooks.resolver import HookResolver

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        resolver = HookResolver(repo)
        settings = resolver.resolve(["nonexistent"])

        # Should return empty settings, not error
        assert settings == {}

    def test_write_temp_settings(self, tmp_path):
        """Test writing settings to temp file."""
        from codegeass.hooks.repository import HookRepository
        from codegeass.hooks.resolver import HookResolver

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        resolver = HookResolver(repo)
        settings = {"hooks": {"PreToolUse": []}}

        path = resolver.write_temp_settings(settings)

        assert path.exists()
        with open(path) as f:
            written = json.load(f)
        assert written == settings

        # Cleanup
        path.unlink()

    def test_validate_tags(self, tmp_path):
        """Test validating tag existence."""
        from codegeass.hooks.models import TagHooks
        from codegeass.hooks.repository import HookRepository
        from codegeass.hooks.resolver import HookResolver

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        hooks = TagHooks(tag="exists", description="Exists")
        repo.save_tag(hooks)

        resolver = HookResolver(repo)
        valid, invalid = resolver.validate_tags(["exists", "nonexistent"])

        assert "exists" in valid
        assert "nonexistent" in invalid


class TestTemplateLoading:
    """Tests for template loading."""

    def test_get_templates(self, tmp_path):
        """Test getting template list."""
        from codegeass.hooks.repository import HookRepository

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        templates = repo.get_templates()

        # Should have the built-in templates
        assert "production" in templates
        assert "safe-mode" in templates
        assert "formatted" in templates

    def test_init_from_templates(self, tmp_path):
        """Test initializing from templates."""
        from codegeass.hooks.repository import HookRepository

        repo = HookRepository(
            project_hooks_dir=tmp_path / "project_hooks",
            global_hooks_dir=tmp_path / "global_hooks",
        )

        initialized = repo.init_from_templates()

        assert len(initialized) > 0
        assert "production" in initialized

        # Check that the hooks were created
        assert repo.exists("production")
        hook = repo.get_tag("production")
        assert hook is not None
        assert hook.description != ""


class TestExecutionContextHooks:
    """Tests for hooks integration with ExecutionContext."""

    def test_context_has_hook_settings_path_field(self):
        """Test that ExecutionContext has hook_settings_path field."""
        from codegeass.execution.strategies.context import ExecutionContext

        # Check field exists in dataclass
        import dataclasses
        fields = {f.name for f in dataclasses.fields(ExecutionContext)}
        assert "hook_settings_path" in fields
