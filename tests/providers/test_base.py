"""Tests for provider base classes and dataclasses."""

from pathlib import Path

from codegeass.providers.base import (
    CodeProvider,
    ExecutionRequest,
    ExecutionResponse,
    ProviderCapabilities,
    ProviderInfo,
)


class TestProviderCapabilities:
    """Tests for ProviderCapabilities dataclass."""

    def test_default_values(self):
        """Test that default values are correct."""
        caps = ProviderCapabilities()
        assert caps.plan_mode is False
        assert caps.resume is False
        assert caps.streaming is False
        assert caps.autonomous is False
        assert caps.autonomous_flag is None
        assert caps.models == []

    def test_custom_values(self):
        """Test creating capabilities with custom values."""
        caps = ProviderCapabilities(
            plan_mode=True,
            resume=True,
            streaming=True,
            autonomous=True,
            autonomous_flag="--yolo",
            models=["model1", "model2"],
        )
        assert caps.plan_mode is True
        assert caps.resume is True
        assert caps.streaming is True
        assert caps.autonomous is True
        assert caps.autonomous_flag == "--yolo"
        assert caps.models == ["model1", "model2"]

    def test_to_dict(self):
        """Test serialization to dictionary."""
        caps = ProviderCapabilities(
            plan_mode=True,
            autonomous=True,
            autonomous_flag="--skip",
            models=["a", "b"],
        )
        d = caps.to_dict()
        assert d["plan_mode"] is True
        assert d["resume"] is False
        assert d["autonomous"] is True
        assert d["autonomous_flag"] == "--skip"
        assert d["models"] == ["a", "b"]


class TestExecutionRequest:
    """Tests for ExecutionRequest dataclass."""

    def test_minimal_request(self):
        """Test creating request with minimal required fields."""
        req = ExecutionRequest(
            prompt="Test prompt",
            working_dir=Path("/tmp"),
        )
        assert req.prompt == "Test prompt"
        assert req.working_dir == Path("/tmp")
        assert req.model == "sonnet"
        assert req.timeout == 300
        assert req.session_id is None
        assert req.autonomous is False
        assert req.plan_mode is False
        assert req.max_turns is None
        assert req.allowed_tools == []
        assert req.variables == {}

    def test_full_request(self):
        """Test creating request with all fields."""
        req = ExecutionRequest(
            prompt="Test",
            working_dir=Path("/project"),
            model="opus",
            timeout=600,
            session_id="session-123",
            autonomous=True,
            plan_mode=True,
            max_turns=10,
            allowed_tools=["Read", "Write"],
            variables={"name": "value"},
        )
        assert req.model == "opus"
        assert req.timeout == 600
        assert req.session_id == "session-123"
        assert req.autonomous is True
        assert req.plan_mode is True
        assert req.max_turns == 10
        assert req.allowed_tools == ["Read", "Write"]
        assert req.variables == {"name": "value"}


class TestExecutionResponse:
    """Tests for ExecutionResponse dataclass."""

    def test_success_response(self):
        """Test creating a successful response."""
        resp = ExecutionResponse(
            status="success",
            output="Hello world",
            exit_code=0,
            session_id="sess-abc",
        )
        assert resp.status == "success"
        assert resp.is_success is True
        assert resp.output == "Hello world"
        assert resp.error is None
        assert resp.exit_code == 0
        assert resp.session_id == "sess-abc"
        assert resp.metadata == {}

    def test_failure_response(self):
        """Test creating a failure response."""
        resp = ExecutionResponse(
            status="failure",
            output="",
            error="Something went wrong",
            exit_code=1,
        )
        assert resp.status == "failure"
        assert resp.is_success is False
        assert resp.error == "Something went wrong"
        assert resp.exit_code == 1

    def test_timeout_response(self):
        """Test creating a timeout response."""
        resp = ExecutionResponse(
            status="timeout",
            output="partial output",
            error="Timed out after 300s",
        )
        assert resp.status == "timeout"
        assert resp.is_success is False


class TestProviderInfo:
    """Tests for ProviderInfo dataclass."""

    def test_provider_info(self):
        """Test creating provider info."""
        caps = ProviderCapabilities(plan_mode=True, streaming=True)
        info = ProviderInfo(
            name="test",
            display_name="Test Provider",
            description="A test provider",
            capabilities=caps,
            is_available=True,
            executable_path="/usr/bin/test",
        )
        assert info.name == "test"
        assert info.display_name == "Test Provider"
        assert info.is_available is True
        assert info.executable_path == "/usr/bin/test"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        caps = ProviderCapabilities(plan_mode=True)
        info = ProviderInfo(
            name="test",
            display_name="Test",
            description="Test",
            capabilities=caps,
            is_available=True,
        )
        d = info.to_dict()
        assert d["name"] == "test"
        assert d["is_available"] is True
        assert d["capabilities"]["plan_mode"] is True


class MockProvider(CodeProvider):
    """Mock provider for testing abstract base class."""

    def __init__(
        self,
        name: str = "mock",
        caps: ProviderCapabilities | None = None,
        executable: str = "/usr/bin/mock",
    ):
        self._name = name
        self._caps = caps or ProviderCapabilities()
        self._executable = executable

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return f"Mock {self._name}"

    @property
    def description(self) -> str:
        return "A mock provider for testing"

    def get_capabilities(self) -> ProviderCapabilities:
        return self._caps

    def get_executable(self) -> str:
        return self._executable

    def build_command(self, request: ExecutionRequest) -> list[str]:
        return [self._executable, "-p", request.prompt]

    def parse_output(self, raw_output: str) -> tuple[str, str | None]:
        return raw_output, None


class TestCodeProviderBase:
    """Tests for CodeProvider abstract base class methods."""

    def test_validate_request_valid(self):
        """Test validating a valid request."""
        caps = ProviderCapabilities(plan_mode=True, resume=True, autonomous=True)
        provider = MockProvider(caps=caps)

        req = ExecutionRequest(
            prompt="test",
            working_dir=Path("/tmp"),
            plan_mode=True,
            autonomous=True,
            session_id="sess-123",
        )

        valid, error = provider.validate_request(req)
        assert valid is True
        assert error is None

    def test_validate_request_plan_mode_unsupported(self):
        """Test validation fails when plan_mode not supported."""
        caps = ProviderCapabilities(plan_mode=False)
        provider = MockProvider(name="noplanner", caps=caps)

        req = ExecutionRequest(
            prompt="test",
            working_dir=Path("/tmp"),
            plan_mode=True,
        )

        valid, error = provider.validate_request(req)
        assert valid is False
        assert "plan mode" in error.lower()
        assert "noplanner" in error

    def test_validate_request_resume_unsupported(self):
        """Test validation fails when resume not supported."""
        caps = ProviderCapabilities(resume=False)
        provider = MockProvider(name="noresume", caps=caps)

        req = ExecutionRequest(
            prompt="test",
            working_dir=Path("/tmp"),
            session_id="sess-123",
        )

        valid, error = provider.validate_request(req)
        assert valid is False
        assert "resume" in error.lower()

    def test_validate_request_autonomous_unsupported(self):
        """Test validation fails when autonomous not supported."""
        caps = ProviderCapabilities(autonomous=False)
        provider = MockProvider(name="noauto", caps=caps)

        req = ExecutionRequest(
            prompt="test",
            working_dir=Path("/tmp"),
            autonomous=True,
        )

        valid, error = provider.validate_request(req)
        assert valid is False
        assert "autonomous" in error.lower()

    def test_is_available_true(self):
        """Test is_available returns True when executable exists."""
        provider = MockProvider(executable="/bin/ls")  # exists on all systems
        assert provider.is_available() is True

    def test_get_info(self):
        """Test get_info returns complete provider info."""
        caps = ProviderCapabilities(plan_mode=True, streaming=True)
        provider = MockProvider(name="test", caps=caps, executable="/bin/ls")

        info = provider.get_info()
        assert info.name == "test"
        assert info.display_name == "Mock test"
        assert info.capabilities.plan_mode is True
        assert info.is_available is True
        assert info.executable_path == "/bin/ls"
