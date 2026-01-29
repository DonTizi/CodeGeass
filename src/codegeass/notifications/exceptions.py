"""Notification-specific exceptions."""

from codegeass.core.exceptions import CodeGeassError


class NotificationError(CodeGeassError):
    """Base exception for notification errors."""


class ProviderError(NotificationError):
    """Raised when a provider operation fails."""

    def __init__(self, provider: str, message: str, cause: Exception | None = None):
        super().__init__(f"[{provider}] {message}", {"provider": provider})
        self.provider = provider
        self.cause = cause


class ProviderNotFoundError(NotificationError):
    """Raised when a provider is not found."""

    def __init__(self, provider: str):
        super().__init__(f"Provider not found: {provider}", {"provider": provider})
        self.provider = provider


class ChannelNotFoundError(NotificationError):
    """Raised when a channel is not found."""

    def __init__(self, channel_id: str):
        super().__init__(f"Channel not found: {channel_id}", {"channel_id": channel_id})
        self.channel_id = channel_id


class ChannelConfigError(NotificationError):
    """Raised when channel configuration is invalid."""

    def __init__(self, channel_id: str, message: str):
        super().__init__(f"Invalid channel config [{channel_id}]: {message}")
        self.channel_id = channel_id


class CredentialError(NotificationError):
    """Raised when credentials are missing or invalid."""

    def __init__(self, credential_key: str, message: str = "Credentials not found"):
        super().__init__(f"{message}: {credential_key}", {"credential_key": credential_key})
        self.credential_key = credential_key
