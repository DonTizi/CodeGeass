"""Notification service for dashboard backend."""


from codegeass.notifications.models import Channel as CoreChannel
from codegeass.notifications.registry import get_provider_registry
from codegeass.notifications.service import NotificationService as CoreNotificationService
from codegeass.storage.channel_repository import ChannelRepository

from ..models import (
    Channel,
    ChannelCreate,
    ChannelUpdate,
    ProviderInfo,
    TestResult,
)


class NotificationService:
    """Dashboard service for managing notifications.

    This wraps the core NotificationService to adapt it for the API models.
    IMPORTANT: Use the core_service parameter to inject the singleton instance
    to ensure message_ids are shared across task executions.
    """

    def __init__(
        self,
        channel_repo: ChannelRepository,
        core_service: CoreNotificationService | None = None,
    ):
        self._channel_repo = channel_repo
        # Use provided core service (singleton) or create new one
        self._core_service = core_service or CoreNotificationService(channel_repo)
        self._registry = get_provider_registry()

    def _core_to_api(self, channel: CoreChannel) -> Channel:
        """Convert core Channel to API model."""
        return Channel(
            id=channel.id,
            name=channel.name,
            provider=channel.provider,
            credential_key=channel.credential_key,
            config=channel.config,
            enabled=channel.enabled,
            created_at=channel.created_at,
        )

    def list_channels(self) -> list[Channel]:
        """List all notification channels."""
        channels = self._channel_repo.find_all()
        return [self._core_to_api(ch) for ch in channels]

    def get_channel(self, channel_id: str) -> Channel | None:
        """Get a channel by ID."""
        channel = self._channel_repo.find_by_id(channel_id)
        if channel:
            return self._core_to_api(channel)
        return None

    def create_channel(self, data: ChannelCreate) -> Channel:
        """Create a new notification channel."""
        # Generate credential key
        credential_key = f"{data.provider}_{data.name.lower().replace(' ', '_')}"

        channel = self._core_service.create_channel(
            name=data.name,
            provider=data.provider,
            credential_key=credential_key,
            credentials=data.credentials,
            config=data.config,
        )

        return self._core_to_api(channel)

    def update_channel(self, channel_id: str, data: ChannelUpdate) -> Channel | None:
        """Update a channel."""
        channel = self._channel_repo.find_by_id(channel_id)
        if not channel:
            return None

        if data.name is not None:
            channel.name = data.name
        if data.config is not None:
            channel.config = data.config
        if data.enabled is not None:
            channel.enabled = data.enabled

        self._channel_repo.save(channel)
        return self._core_to_api(channel)

    def delete_channel(self, channel_id: str, delete_credentials: bool = True) -> bool:
        """Delete a channel."""
        return self._core_service.delete_channel(channel_id, delete_credentials)

    def enable_channel(self, channel_id: str) -> bool:
        """Enable a channel."""
        return self._core_service.enable_channel(channel_id)

    def disable_channel(self, channel_id: str) -> bool:
        """Disable a channel."""
        return self._core_service.disable_channel(channel_id)

    async def test_channel(self, channel_id: str) -> TestResult:
        """Test a notification channel."""
        success, message = await self._core_service.test_channel(channel_id)
        return TestResult(success=success, message=message)

    async def send_test_message(self, channel_id: str, message: str) -> bool:
        """Send a test message to a channel."""
        return await self._core_service.send_test_message(channel_id, message)

    def list_providers(self) -> list[ProviderInfo]:
        """List available notification providers."""
        providers = []
        for name in self._registry.list_providers():
            try:
                info = self._registry.get_provider_info(name)
                providers.append(
                    ProviderInfo(
                        name=info.name,
                        display_name=info.display_name,
                        description=info.description,
                        required_credentials=[
                            {
                                "name": f["name"],
                                "description": f.get("description", ""),
                                "sensitive": f.get("sensitive", True),
                            }
                            for f in info.required_credentials
                        ],
                        required_config=[
                            {
                                "name": f["name"],
                                "description": f.get("description", ""),
                                "default": f.get("default"),
                            }
                            for f in info.required_config
                        ],
                        optional_config=[
                            {
                                "name": f["name"],
                                "description": f.get("description", ""),
                                "default": f.get("default"),
                            }
                            for f in (info.optional_config or [])
                        ],
                    )
                )
            except Exception:
                continue
        return providers

    def get_provider(self, name: str) -> ProviderInfo | None:
        """Get information about a specific provider."""
        if name not in self._registry.list_providers():
            return None

        info = self._registry.get_provider_info(name)
        return ProviderInfo(
            name=info.name,
            display_name=info.display_name,
            description=info.description,
            required_credentials=[
                {
                    "name": f["name"],
                    "description": f.get("description", ""),
                    "sensitive": f.get("sensitive", True),
                }
                for f in info.required_credentials
            ],
            required_config=[
                {
                    "name": f["name"],
                    "description": f.get("description", ""),
                    "default": f.get("default"),
                }
                for f in info.required_config
            ],
            optional_config=[
                {
                    "name": f["name"],
                    "description": f.get("description", ""),
                    "default": f.get("default"),
                }
                for f in (info.optional_config or [])
            ],
        )
