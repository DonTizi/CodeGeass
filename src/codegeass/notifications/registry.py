"""Provider registry for notification providers."""

from typing import TypeVar

from codegeass.notifications.exceptions import ProviderNotFoundError
from codegeass.notifications.providers.base import NotificationProvider, ProviderConfig

T = TypeVar("T", bound=NotificationProvider)


class ProviderRegistry:
    """Factory and registry for notification providers.

    Manages available notification providers and creates instances on demand.
    Uses lazy loading to avoid importing providers until needed.
    """

    # Registry of available providers (name -> module.class)
    _PROVIDERS: dict[str, str] = {
        "telegram": "codegeass.notifications.providers.telegram.TelegramProvider",
        "discord": "codegeass.notifications.providers.discord.DiscordProvider",
        "teams": "codegeass.notifications.providers.teams.TeamsProvider",
    }

    def __init__(self) -> None:
        self._instances: dict[str, NotificationProvider] = {}

    def get(self, name: str) -> NotificationProvider:
        """Get a provider instance by name.

        Args:
            name: Provider name (e.g., 'telegram')

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        if name not in self._PROVIDERS:
            raise ProviderNotFoundError(name)

        # Lazy instantiation
        if name not in self._instances:
            self._instances[name] = self._create_provider(name)

        return self._instances[name]

    def _create_provider(self, name: str) -> NotificationProvider:
        """Create a provider instance from its class path."""
        class_path = self._PROVIDERS[name]
        module_path, class_name = class_path.rsplit(".", 1)

        try:
            import importlib

            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)
            return provider_class()
        except ImportError as e:
            raise ProviderNotFoundError(name) from e

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._PROVIDERS.keys())

    def get_provider_info(self, name: str) -> ProviderConfig:
        """Get configuration info for a provider.

        Args:
            name: Provider name

        Returns:
            ProviderConfig with required fields info
        """
        provider = self.get(name)
        return provider.get_config_schema()

    def list_provider_info(self) -> list[ProviderConfig]:
        """Get configuration info for all providers."""
        return [self.get_provider_info(name) for name in self.list_providers()]

    def is_available(self, name: str) -> bool:
        """Check if a provider is available (registered and importable)."""
        if name not in self._PROVIDERS:
            return False

        try:
            self.get(name)
            return True
        except ProviderNotFoundError:
            return False

    @classmethod
    def register(cls, name: str, class_path: str) -> None:
        """Register a custom provider.

        Args:
            name: Provider name
            class_path: Full class path (e.g., 'mymodule.MyProvider')
        """
        cls._PROVIDERS[name] = class_path


# Global registry instance
_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
