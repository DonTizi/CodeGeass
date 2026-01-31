"""Tests for Claude Code adapter."""

from pathlib import Path
from unittest.mock import patch

import pytest

from codegeass.providers.base import ExecutionRequest
from codegeass.providers.claude import ClaudeCodeAdapter
from codegeass.providers.claude.output_parser import parse_stream_json


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Create a Claude adapter instance."""
        return ClaudeCodeAdapter()

    def test_name(self, adapter):
        """Test provider name."""
        assert adapter.name == "claude"

    def test_display_name(self, adapter):
        """Test provider display name."""
        assert adapter.display_name == "Claude Code"

    def test_description(self, adapter):
        """Test provider description."""
        assert "Claude" in adapter.description
        assert "plan mode" in adapter.description.lower()

    def test_capabilities(self, adapter):
        """Test provider capabilities."""
        caps = adapter.get_capabilities()

        assert caps.plan_mode is True
        assert caps.resume is True
        assert caps.streaming is True
        assert caps.autonomous is True
        assert caps.autonomous_flag == "--dangerously-skip-permissions"
        assert "haiku" in caps.models
        assert "sonnet" in caps.models
        assert "opus" in caps.models

    def test_build_command_basic(self, adapter):
        """Test building a basic command."""
        request = ExecutionRequest(
            prompt="Hello world",
            working_dir=Path("/tmp"),
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/claude"):
            cmd = adapter.build_command(request)

        assert cmd[0] == "/usr/bin/claude"
        assert "-p" in cmd
        assert "Hello world" in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd

    def test_build_command_with_model(self, adapter):
        """Test building command with model specified."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            model="opus",
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/claude"):
            cmd = adapter.build_command(request)

        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "opus"

    def test_build_command_with_max_turns(self, adapter):
        """Test building command with max_turns."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            max_turns=5,
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/claude"):
            cmd = adapter.build_command(request)

        assert "--max-turns" in cmd
        idx = cmd.index("--max-turns")
        assert cmd[idx + 1] == "5"

    def test_build_command_with_allowed_tools(self, adapter):
        """Test building command with allowed tools."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            allowed_tools=["Read", "Write", "Bash"],
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/claude"):
            cmd = adapter.build_command(request)

        # Each tool should have its own --allowedTools flag
        allowed_tools_count = cmd.count("--allowedTools")
        assert allowed_tools_count == 3

    def test_build_command_autonomous(self, adapter):
        """Test building command with autonomous mode."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            autonomous=True,
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/claude"):
            cmd = adapter.build_command(request)

        assert "--dangerously-skip-permissions" in cmd

    def test_build_command_resume(self, adapter):
        """Test building command for resume."""
        request = ExecutionRequest(
            prompt="Continue",
            working_dir=Path("/tmp"),
            session_id="session-abc-123",
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/claude"):
            cmd = adapter.build_command(request)

        assert "--resume" in cmd
        assert "session-abc-123" in cmd

    def test_build_command_resume_with_autonomous(self, adapter):
        """Test building resume command with autonomous mode."""
        request = ExecutionRequest(
            prompt="Approve",
            working_dir=Path("/tmp"),
            session_id="session-abc-123",
            autonomous=True,
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/claude"):
            cmd = adapter.build_command(request)

        assert "--resume" in cmd
        assert "--dangerously-skip-permissions" in cmd

    def test_validate_request_all_supported(self, adapter):
        """Test validation passes for all supported features."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            plan_mode=True,
            autonomous=True,
            session_id="sess-123",
        )

        valid, error = adapter.validate_request(request)
        assert valid is True
        assert error is None

    def test_parse_output(self, adapter):
        """Test output parsing."""
        raw_output = '{"type":"result","result":"Hello from Claude","session_id":"abc-123"}'
        text, session_id = adapter.parse_output(raw_output)

        assert "Hello from Claude" in text
        assert session_id == "abc-123"


class TestClaudeOutputParser:
    """Tests for Claude output parser."""

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        result = parse_stream_json("")
        assert result.text == ""
        assert result.session_id is None

    def test_parse_system_message(self):
        """Test extracting session_id from system message."""
        output = '{"type":"system","session_id":"sess-12345"}'
        result = parse_stream_json(output)
        assert result.session_id == "sess-12345"

    def test_parse_result_type(self):
        """Test parsing result type message."""
        output = '{"type":"result","result":"Hello world","session_id":"abc"}'
        result = parse_stream_json(output)
        assert result.text == "Hello world"
        assert result.session_id == "abc"

    def test_parse_stream_event_text_delta(self):
        """Test parsing stream event with text delta."""
        # Parser expects single-line JSON (JSONL format)
        output = (
            '{"type":"stream_event","event":{"type":"content_block_delta",'
            '"delta":{"type":"text_delta","text":"Hello"}}}'
        )
        result = parse_stream_json(output)
        assert result.text == "Hello"

    def test_parse_multiple_deltas(self):
        """Test parsing multiple text deltas."""
        line1 = (
            '{"type":"stream_event","event":{"type":"content_block_delta",'
            '"delta":{"type":"text_delta","text":"Hello "}}}'
        )
        line2 = (
            '{"type":"stream_event","event":{"type":"content_block_delta",'
            '"delta":{"type":"text_delta","text":"world"}}}'
        )
        output = f"{line1}\n{line2}"
        result = parse_stream_json(output)
        assert result.text == "Hello world"

    def test_parse_assistant_message(self):
        """Test parsing assistant message type."""
        # Parser expects single-line JSON (JSONL format)
        output = (
            '{"type":"assistant","message":{"content":[{"type":"text",'
            '"text":"Response text"}]},"session_id":"sess-xyz"}'
        )
        result = parse_stream_json(output)
        assert result.session_id == "sess-xyz"

    def test_parse_skips_metadata_events(self):
        """Test that metadata events are skipped."""
        output = """{"type":"stream_event","event":{"type":"message_start"}}
{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}}
{"type":"stream_event","event":{"type":"message_stop"}}"""
        result = parse_stream_json(output)
        assert result.text == "Hello"

    def test_parse_error_field(self):
        """Test parsing error field."""
        output = '{"error": "Something went wrong"}'
        result = parse_stream_json(output)
        assert "Something went wrong" in result.text

    def test_parse_invalid_json_gracefully(self):
        """Test that invalid JSON is handled gracefully."""
        output = "Not valid JSON\nAlso not valid"
        result = parse_stream_json(output)
        # Should not crash, may include as plain text
        assert result is not None

    def test_parse_mixed_content(self):
        """Test parsing mixed system and content messages."""
        output = """{"type":"system","session_id":"sess-abc"}
{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}}
{"type":"result","result":"Final result"}"""
        result = parse_stream_json(output)
        assert result.session_id == "sess-abc"
        # Should prefer streaming deltas or result
        assert "Hello" in result.text or "Final result" in result.text
