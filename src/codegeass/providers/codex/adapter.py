"""OpenAI Codex provider adapter."""

from codegeass.providers.base import (
    CodeProvider,
    ExecutionRequest,
    ProviderCapabilities,
)
from codegeass.providers.codex.cli import get_codex_executable
from codegeass.providers.codex.output_parser import parse_jsonl_output


class CodexAdapter(CodeProvider):
    """Adapter for OpenAI Codex CLI.

    Codex is OpenAI's coding assistant. Key differences from Claude Code:
    - Does NOT support plan mode (read-only planning)
    - Does NOT support session resume
    - Supports autonomous mode with --full-auto flag
    - Uses JSONL output format
    """

    @property
    def name(self) -> str:
        return "codex"

    @property
    def display_name(self) -> str:
        return "OpenAI Codex"

    @property
    def description(self) -> str:
        return "OpenAI's coding assistant CLI with autonomous execution support"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            plan_mode=False,  # Codex does NOT support plan mode
            resume=False,  # Codex does NOT support session resume
            streaming=True,
            autonomous=True,
            autonomous_flag="--full-auto",
            models=["gpt-5.2-codex", "gpt-5.2", "gpt-5.1-codex-max", "gpt-5.1-codex-mini"],
        )

    def get_executable(self) -> str:
        return get_codex_executable()

    def validate_request(self, request: ExecutionRequest) -> tuple[bool, str | None]:
        """Validate that Codex can handle the request.

        Codex has specific limitations compared to Claude Code.

        Args:
            request: The execution request to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First run base validation
        is_valid, error = super().validate_request(request)
        if not is_valid:
            return is_valid, error

        # Additional Codex-specific validation
        if request.plan_mode:
            return False, (
                "Codex does not support plan mode. "
                "Plan mode is only available with Claude Code."
            )

        if request.session_id:
            return False, (
                "Codex does not support session resume. "
                "Session resume is only available with Claude Code."
            )

        return True, None

    def build_command(self, request: ExecutionRequest) -> list[str]:
        """Build the Codex CLI command.

        Args:
            request: The execution request

        Returns:
            List of command arguments
        """
        executable = self.get_executable()
        command = [executable, "exec"]

        # Model selection (must come before positional prompt)
        if request.model:
            # Map Claude model names to Codex models for backward compatibility
            model_map = {
                "sonnet": "gpt-5.2-codex",
                "haiku": "gpt-5.1-codex-mini",
                "opus": "gpt-5.1-codex-max",
            }
            codex_model = model_map.get(request.model, request.model)
            command.extend(["--model", codex_model])

        # Autonomous mode (--full-auto for sandboxed auto-execution)
        if request.autonomous:
            command.append("--full-auto")

        # JSON output format
        command.append("--json")

        # Prompt is a positional argument (must be last)
        command.append(request.prompt)

        return command

    def parse_output(self, raw_output: str) -> tuple[str, str | None]:
        """Parse Codex CLI JSONL output.

        Args:
            raw_output: Raw stdout from Codex CLI

        Returns:
            Tuple of (clean_text, session_id)
        """
        parsed = parse_jsonl_output(raw_output)
        return parsed.text, parsed.session_id
