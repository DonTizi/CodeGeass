"""Scheduler provider registry."""

import platform

from codegeass.scheduling.providers.base import SchedulerProvider


class SchedulerProviderNotFoundError(Exception):
    """Raised when a scheduler provider is not found."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Scheduler provider not found: {name}")
        self.name = name


class SchedulerProviderRegistry:
    """Factory and registry for scheduler providers.

    Manages available scheduler providers with lazy loading.
    """

    _PROVIDERS: dict[str, str] = {
        "launchd": "codegeass.scheduling.providers.launchd.LaunchdProvider",
        "systemd": "codegeass.scheduling.providers.systemd.SystemdProvider",
        "cron": "codegeass.scheduling.providers.cron.CronProvider",
        "windows": "codegeass.scheduling.providers.windows.WindowsTaskSchedulerProvider",
    }

    def __init__(self) -> None:
        self._instances: dict[str, SchedulerProvider] = {}

    def get(self, name: str) -> SchedulerProvider:
        """Get a provider instance by name (lazy instantiation).

        Args:
            name: Provider name (e.g., 'launchd', 'systemd', 'windows')

        Returns:
            SchedulerProvider instance

        Raises:
            SchedulerProviderNotFoundError: If provider not found
        """
        if name not in self._PROVIDERS:
            raise SchedulerProviderNotFoundError(name)

        if name not in self._instances:
            self._instances[name] = self._create_provider(name)

        return self._instances[name]

    def _create_provider(self, name: str) -> SchedulerProvider:
        """Create a provider instance from its class path."""
        import importlib

        class_path = self._PROVIDERS[name]
        module_path, class_name = class_path.rsplit(".", 1)

        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)
        return provider_class()

    def get_default(self) -> SchedulerProvider:
        """Get the appropriate provider for the current platform.

        Returns:
            SchedulerProvider suitable for the current OS
        """
        system = platform.system()

        if system == "Darwin":
            return self.get("launchd")
        elif system == "Windows":
            return self.get("windows")
        elif system == "Linux":
            provider = self.get("systemd")
            if provider.is_available():
                return provider
            return self.get("cron")
        else:
            # Unix fallback
            return self.get("cron")

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names
        """
        return list(self._PROVIDERS.keys())

    def get_available_providers(self) -> list[SchedulerProvider]:
        """Get all available providers for this system.

        Returns:
            List of available SchedulerProvider instances
        """
        available = []
        for name in self._PROVIDERS:
            try:
                provider = self.get(name)
                if provider.is_available():
                    available.append(provider)
            except Exception:
                continue
        return available


# Global registry instance
_registry: SchedulerProviderRegistry | None = None


def get_scheduler_registry() -> SchedulerProviderRegistry:
    """Get the global scheduler provider registry.

    Returns:
        SchedulerProviderRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = SchedulerProviderRegistry()
    return _registry
