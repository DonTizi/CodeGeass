"""Provider registry for code execution providers."""

from typing import TypeVar

from codegeass.providers.base import CodeProvider, ProviderInfo
from codegeass.providers.exceptions import ProviderNotFoundError

T = TypeVar("T", bound=CodeProvider)


class ProviderRegistry:
    """Factory and registry for code execution providers.

    Manages available code execution providers and creates instances on demand.
    Uses lazy loading to avoid importing providers until needed.
    """

    # Registry of available providers (name -> module.class)
    _PROVIDERS: dict[str, str] = {
        "claude": "codegeass.providers.claude.ClaudeCodeAdapter",
        "codex": "codegeass.providers.codex.CodexAdapter",
    }

    def __init__(self) -> None:
        self._instances: dict[str, CodeProvider] = {}

    def get(self, name: str) -> CodeProvider:
        """Get a provider instance by name.

        Args:
            name: Provider name (e.g., 'claude', 'codex')

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

    def _create_provider(self, name: str) -> CodeProvider:
        """Create a provider instance from its class path."""
        class_path = self._PROVIDERS[name]
        module_path, class_name = class_path.rsplit(".", 1)

        try:
            import importlib

            module = importlib.import_module(module_path)
            provider_class: type[CodeProvider] = getattr(module, class_name)
            return provider_class()
        except ImportError as e:
            raise ProviderNotFoundError(name) from e

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._PROVIDERS.keys())

    def get_provider_info(self, name: str) -> ProviderInfo:
        """Get full information for a provider.

        Args:
            name: Provider name

        Returns:
            ProviderInfo with capabilities and availability
        """
        provider = self.get(name)
        return provider.get_info()

    def list_provider_info(self) -> list[ProviderInfo]:
        """Get information for all providers."""
        return [self.get_provider_info(name) for name in self.list_providers()]

    def get_available(self) -> list[CodeProvider]:
        """Get all available (ready to use) providers.

        Returns:
            List of provider instances that are available
        """
        available = []
        for name in self.list_providers():
            try:
                provider = self.get(name)
                if provider.is_available():
                    available.append(provider)
            except ProviderNotFoundError:
                continue
        return available

    def is_available(self, name: str) -> bool:
        """Check if a provider is available (registered and executable found).

        Args:
            name: Provider name

        Returns:
            True if provider is ready to use
        """
        if name not in self._PROVIDERS:
            return False

        try:
            provider = self.get(name)
            return provider.is_available()
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
