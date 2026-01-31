"""Provider-specific exceptions."""

from codegeass.core.exceptions import CodeGeassError


class ProviderError(CodeGeassError):
    """Base exception for code execution provider errors."""


class ProviderNotFoundError(ProviderError):
    """Raised when a provider is not found in the registry."""

    def __init__(self, provider: str):
        super().__init__(f"Provider not found: {provider}", {"provider": provider})
        self.provider = provider


class ProviderCapabilityError(ProviderError):
    """Raised when a provider doesn't support a requested capability."""

    def __init__(self, provider: str, capability: str, message: str | None = None):
        msg = message or f"Provider '{provider}' does not support: {capability}"
        super().__init__(msg, {"provider": provider, "capability": capability})
        self.provider = provider
        self.capability = capability


class ProviderExecutionError(ProviderError):
    """Raised when a provider execution fails."""

    def __init__(
        self,
        provider: str,
        message: str,
        exit_code: int | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(f"[{provider}] {message}", {"provider": provider, "exit_code": exit_code})
        self.provider = provider
        self.exit_code = exit_code
        self.cause = cause


class ProviderNotAvailableError(ProviderError):
    """Raised when a provider is not available (e.g., executable not found)."""

    def __init__(self, provider: str, reason: str | None = None):
        msg = f"Provider '{provider}' is not available"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, {"provider": provider, "reason": reason})
        self.provider = provider
        self.reason = reason
