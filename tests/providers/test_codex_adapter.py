"""Tests for OpenAI Codex adapter."""

from pathlib import Path
from unittest.mock import patch

import pytest

from codegeass.providers.base import ExecutionRequest
from codegeass.providers.codex import CodexAdapter
from codegeass.providers.codex.output_parser import parse_jsonl_output


class TestCodexAdapter:
    """Tests for CodexAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Create a Codex adapter instance."""
        return CodexAdapter()

    def test_name(self, adapter):
        """Test provider name."""
        assert adapter.name == "codex"

    def test_display_name(self, adapter):
        """Test provider display name."""
        assert adapter.display_name == "OpenAI Codex"

    def test_description(self, adapter):
        """Test provider description."""
        assert "OpenAI" in adapter.description or "Codex" in adapter.description

    def test_capabilities(self, adapter):
        """Test provider capabilities."""
        caps = adapter.get_capabilities()

        # Codex does NOT support plan mode or resume
        assert caps.plan_mode is False
        assert caps.resume is False
        # But supports streaming and autonomous
        assert caps.streaming is True
        assert caps.autonomous is True
        assert caps.autonomous_flag == "--full-auto"
        # Has OpenAI Codex models
        assert "gpt-5.2-codex" in caps.models
        assert "gpt-5.1-codex-mini" in caps.models

    def test_build_command_basic(self, adapter):
        """Test building a basic command."""
        request = ExecutionRequest(
            prompt="Hello world",
            working_dir=Path("/tmp"),
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/codex"):
            cmd = adapter.build_command(request)

        assert cmd[0] == "/usr/bin/codex"
        assert "exec" in cmd
        assert "Hello world" in cmd

    def test_build_command_with_model_mapping(self, adapter):
        """Test that Claude model names are mapped to Codex equivalents."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            model="sonnet",  # Claude model name
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/codex"):
            cmd = adapter.build_command(request)

        # Should map sonnet -> gpt-5.2-codex
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "gpt-5.2-codex"

    def test_build_command_haiku_mapping(self, adapter):
        """Test haiku -> gpt-5.1-codex-mini mapping."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            model="haiku",
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/codex"):
            cmd = adapter.build_command(request)

        idx = cmd.index("--model")
        assert cmd[idx + 1] == "gpt-5.1-codex-mini"

    def test_build_command_opus_mapping(self, adapter):
        """Test opus -> gpt-5.1-codex-max mapping."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            model="opus",
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/codex"):
            cmd = adapter.build_command(request)

        idx = cmd.index("--model")
        assert cmd[idx + 1] == "gpt-5.1-codex-max"

    def test_build_command_native_codex_model(self, adapter):
        """Test using native Codex model name directly."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            model="gpt-5.2-codex",
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/codex"):
            cmd = adapter.build_command(request)

        idx = cmd.index("--model")
        assert cmd[idx + 1] == "gpt-5.2-codex"

    def test_build_command_autonomous(self, adapter):
        """Test building command with autonomous mode."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            autonomous=True,
        )

        with patch.object(adapter, "get_executable", return_value="/usr/bin/codex"):
            cmd = adapter.build_command(request)

        # Codex uses --full-auto for autonomous mode
        assert "--full-auto" in cmd

    def test_validate_request_plan_mode_rejected(self, adapter):
        """Test that plan_mode is rejected."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            plan_mode=True,
        )

        valid, error = adapter.validate_request(request)
        assert valid is False
        assert "plan mode" in error.lower()
        assert "codex" in error.lower()

    def test_validate_request_resume_rejected(self, adapter):
        """Test that resume is rejected."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            session_id="some-session",
        )

        valid, error = adapter.validate_request(request)
        assert valid is False
        assert "resume" in error.lower()

    def test_validate_request_basic_accepted(self, adapter):
        """Test that basic request is accepted."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
        )

        valid, error = adapter.validate_request(request)
        assert valid is True
        assert error is None

    def test_validate_request_autonomous_accepted(self, adapter):
        """Test that autonomous mode is accepted."""
        request = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/tmp"),
            autonomous=True,
        )

        valid, error = adapter.validate_request(request)
        assert valid is True
        assert error is None


class TestCodexOutputParser:
    """Tests for Codex output parser."""

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        result = parse_jsonl_output("")
        assert result.text == ""

    def test_parse_plain_text(self):
        """Test parsing plain text output."""
        output = "Hello world"
        result = parse_jsonl_output(output)
        assert result.text == "Hello world"

    def test_parse_jsonl_message(self):
        """Test parsing JSONL message format."""
        output = '{"type":"message","content":"Hello from Codex"}'
        result = parse_jsonl_output(output)
        assert "Hello from Codex" in result.text

    def test_parse_multiple_jsonl_lines(self):
        """Test parsing multiple JSONL lines."""
        output = """{"type":"message","content":"Hello "}
{"type":"message","content":"world"}"""
        result = parse_jsonl_output(output)
        # Should concatenate content
        assert "Hello" in result.text
        assert "world" in result.text

    def test_parse_result_type(self):
        """Test parsing result type message."""
        output = '{"type":"result","result":"Final answer"}'
        result = parse_jsonl_output(output)
        assert "Final answer" in result.text

    def test_parse_error_message(self):
        """Test parsing error message."""
        output = '{"type":"error","message":"Something failed"}'
        result = parse_jsonl_output(output)
        assert "Something failed" in result.text

    def test_parse_mixed_content(self):
        """Test parsing mixed JSON and text."""
        output = """Starting execution...
{"type":"message","content":"Processing"}
Done."""
        result = parse_jsonl_output(output)
        # Should handle mixed content gracefully
        assert result is not None

    def test_parse_session_id(self):
        """Test extracting session_id from output."""
        output = '{"session_id":"sess-abc-123","type":"message","content":"Hello"}'
        result = parse_jsonl_output(output)
        assert result.session_id == "sess-abc-123"
