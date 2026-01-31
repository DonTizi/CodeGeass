"""Claude Code provider adapter."""

from codegeass.providers.base import (
    CodeProvider,
    ExecutionRequest,
    ProviderCapabilities,
)
from codegeass.providers.claude.cli import get_claude_executable
from codegeass.providers.claude.output_parser import parse_stream_json


class ClaudeCodeAdapter(CodeProvider):
    """Adapter for Claude Code CLI.

    Claude Code is Anthropic's official CLI for Claude. It supports:
    - Plan mode (read-only planning before execution)
    - Session resume
    - Streaming output
    - Autonomous mode (--dangerously-skip-permissions)
    """

    @property
    def name(self) -> str:
        return "claude"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    @property
    def description(self) -> str:
        return "Anthropic's CLI for Claude with plan mode, session resume, and autonomous execution"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            plan_mode=True,
            resume=True,
            streaming=True,
            autonomous=True,
            autonomous_flag="--dangerously-skip-permissions",
            models=["haiku", "sonnet", "opus"],
        )

    def get_executable(self) -> str:
        return get_claude_executable()

    def build_command(self, request: ExecutionRequest) -> list[str]:
        """Build the Claude CLI command.

        Args:
            request: The execution request

        Returns:
            List of command arguments
        """
        executable = self.get_executable()
        command = [executable]

        # Resume mode
        if request.session_id:
            command.extend(["--resume", request.session_id])
            if request.prompt:
                command.extend(["-p", request.prompt])
            # Add full permissions for resume with approval
            if request.autonomous:
                command.append("--dangerously-skip-permissions")
        else:
            # Non-interactive mode
            command.extend(["-p", request.prompt])

        # Model selection
        if request.model:
            command.extend(["--model", request.model])

        # Max turns
        if request.max_turns:
            command.extend(["--max-turns", str(request.max_turns)])

        # Allowed tools
        for tool in request.allowed_tools:
            command.extend(["--allowedTools", tool])

        # Output format
        command.append("--output-format")
        command.append("stream-json")

        # Autonomous mode (skip permissions)
        if request.autonomous and not request.session_id:
            command.append("--dangerously-skip-permissions")

        return command

    def parse_output(self, raw_output: str) -> tuple[str, str | None]:
        """Parse Claude CLI stream-json output.

        Args:
            raw_output: Raw stdout from Claude CLI

        Returns:
            Tuple of (clean_text, session_id)
        """
        parsed = parse_stream_json(raw_output)
        return parsed.text, parsed.session_id
