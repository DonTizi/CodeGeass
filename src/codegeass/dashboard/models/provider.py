"""Provider models for API."""

from pydantic import BaseModel, Field


class ProviderCapabilities(BaseModel):
    """Capabilities supported by a code execution provider."""

    plan_mode: bool = Field(False, description="Supports plan mode (read-only planning)")
    resume: bool = Field(False, description="Supports session resume")
    streaming: bool = Field(False, description="Supports streaming output")
    autonomous: bool = Field(False, description="Supports autonomous execution mode")
    autonomous_flag: str | None = Field(None, description="CLI flag for autonomous mode")
    models: list[str] = Field(default_factory=list, description="Supported models")


class Provider(BaseModel):
    """Full provider model with all details."""

    name: str = Field(..., description="Provider identifier (e.g., 'claude', 'codex')")
    display_name: str = Field(..., description="Human-readable provider name")
    description: str = Field(..., description="Brief description of the provider")
    capabilities: ProviderCapabilities
    is_available: bool = Field(False, description="Whether the provider is ready to use")
    executable_path: str | None = Field(None, description="Path to the executable if available")


class ProviderSummary(BaseModel):
    """Summary view of a provider for list endpoints."""

    name: str
    display_name: str
    is_available: bool
    supports_plan_mode: bool
