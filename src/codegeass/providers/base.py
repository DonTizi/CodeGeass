"""Base code execution provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProviderCapabilities:
    """Describes what a code execution provider can do.

    Attributes:
        plan_mode: Provider supports plan mode (read-only planning before execution)
        resume: Provider supports resuming a previous session
        streaming: Provider supports streaming output
        autonomous: Provider supports autonomous execution mode
        autonomous_flag: CLI flag to enable autonomous mode (e.g., "--dangerously-skip-permissions")
        models: List of supported models (e.g., ["haiku", "sonnet", "opus"])
    """

    plan_mode: bool = False
    resume: bool = False
    streaming: bool = False
    autonomous: bool = False
    autonomous_flag: str | None = None
    models: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan_mode": self.plan_mode,
            "resume": self.resume,
            "streaming": self.streaming,
            "autonomous": self.autonomous,
            "autonomous_flag": self.autonomous_flag,
            "models": self.models,
        }


@dataclass
class ExecutionRequest:
    """Request to execute code via a provider.

    Attributes:
        prompt: The prompt/instructions to execute
        working_dir: Directory where execution should happen
        model: Model to use (provider-specific)
        timeout: Execution timeout in seconds
        session_id: Optional session ID for resume operations
        autonomous: Whether to run in autonomous mode
        plan_mode: Whether to run in plan mode (read-only)
        max_turns: Maximum number of agentic turns
        allowed_tools: List of tools allowed for execution
        variables: Template variables to substitute
    """

    prompt: str
    working_dir: Path
    model: str = "sonnet"
    timeout: int = 300
    session_id: str | None = None
    autonomous: bool = False
    plan_mode: bool = False
    max_turns: int | None = None
    allowed_tools: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResponse:
    """Response from a provider execution.

    Attributes:
        status: Execution status ("success", "failure", "timeout")
        output: Raw output from the execution
        error: Error message if execution failed
        exit_code: Process exit code
        session_id: Session ID for potential resume
        metadata: Additional provider-specific metadata
    """

    status: str
    output: str
    error: str | None = None
    exit_code: int | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == "success"


@dataclass
class ProviderInfo:
    """Metadata about a code execution provider."""

    name: str
    display_name: str
    description: str
    capabilities: ProviderCapabilities
    is_available: bool = False
    executable_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "capabilities": self.capabilities.to_dict(),
            "is_available": self.is_available,
            "executable_path": self.executable_path,
        }


class CodeProvider(ABC):
    """Abstract base class for code execution providers.

    Each provider (Claude Code, Codex, etc.) implements this interface
    to provide platform-specific code execution capabilities.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'claude', 'codex')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of the provider."""
        ...

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get the capabilities supported by this provider.

        Returns:
            ProviderCapabilities describing what this provider can do
        """
        ...

    @abstractmethod
    def get_executable(self) -> str:
        """Get the path to the provider's executable.

        Returns:
            Path to the executable

        Raises:
            ProviderNotAvailableError: If executable cannot be found
        """
        ...

    @abstractmethod
    def build_command(self, request: ExecutionRequest) -> list[str]:
        """Build the command to execute for the given request.

        Args:
            request: The execution request

        Returns:
            List of command arguments
        """
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> tuple[str, str | None]:
        """Parse raw output from the provider.

        Args:
            raw_output: Raw stdout from the provider

        Returns:
            Tuple of (clean_text, session_id)
        """
        ...

    def validate_request(self, request: ExecutionRequest) -> tuple[bool, str | None]:
        """Validate that this provider can handle the request.

        Override to add provider-specific validation.

        Args:
            request: The execution request to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        capabilities = self.get_capabilities()

        if request.plan_mode and not capabilities.plan_mode:
            return False, f"Provider '{self.name}' does not support plan mode"

        if request.session_id and not capabilities.resume:
            return False, f"Provider '{self.name}' does not support resume"

        if request.autonomous and not capabilities.autonomous:
            return False, f"Provider '{self.name}' does not support autonomous mode"

        return True, None

    def is_available(self) -> bool:
        """Check if this provider is available (executable exists).

        Returns:
            True if provider is ready to use
        """
        try:
            self.get_executable()
            return True
        except Exception:
            return False

    def get_info(self) -> ProviderInfo:
        """Get full information about this provider.

        Returns:
            ProviderInfo with all metadata
        """
        executable_path = None
        try:
            executable_path = self.get_executable()
        except Exception:
            pass

        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            capabilities=self.get_capabilities(),
            is_available=self.is_available(),
            executable_path=executable_path,
        )
