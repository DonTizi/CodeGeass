"""Tests for scheduler provider architecture."""

import platform

import pytest

from codegeass.scheduling.providers import SchedulerConfig, SchedulerProvider, SchedulerStatus
from codegeass.scheduling.registry import (
    SchedulerProviderNotFoundError,
    SchedulerProviderRegistry,
    get_scheduler_registry,
)


class TestSchedulerStatus:
    """Tests for SchedulerStatus dataclass."""

    def test_status_creation(self) -> None:
        """Test SchedulerStatus can be created."""
        status = SchedulerStatus(
            installed=True,
            running=False,
            scheduler_type="test",
            details="test details",
        )
        assert status.installed is True
        assert status.running is False
        assert status.scheduler_type == "test"
        assert status.details == "test details"

    def test_status_optional_details(self) -> None:
        """Test SchedulerStatus works without optional details."""
        status = SchedulerStatus(
            installed=False,
            running=False,
            scheduler_type="test",
        )
        assert status.details is None


class TestSchedulerConfig:
    """Tests for SchedulerConfig dataclass."""

    def test_config_creation(self) -> None:
        """Test SchedulerConfig can be created."""
        config = SchedulerConfig(
            name="test",
            display_name="Test Scheduler",
            description="A test scheduler",
            check_command="test --check",
            stop_command="test --stop",
        )
        assert config.name == "test"
        assert config.display_name == "Test Scheduler"


class TestSchedulerProviderRegistry:
    """Tests for SchedulerProviderRegistry."""

    def test_registry_creation(self) -> None:
        """Test registry can be created."""
        registry = SchedulerProviderRegistry()
        assert registry is not None

    def test_global_registry(self) -> None:
        """Test global registry singleton."""
        registry1 = get_scheduler_registry()
        registry2 = get_scheduler_registry()
        assert registry1 is registry2

    def test_list_providers(self) -> None:
        """Test listing all registered providers."""
        registry = SchedulerProviderRegistry()
        providers = registry.list_providers()

        assert "launchd" in providers
        assert "systemd" in providers
        assert "cron" in providers
        assert "windows" in providers

    def test_get_provider_by_name(self) -> None:
        """Test getting a specific provider by name."""
        registry = SchedulerProviderRegistry()

        # These should not raise
        launchd = registry.get("launchd")
        assert launchd.name == "launchd"

        systemd = registry.get("systemd")
        assert systemd.name == "systemd"

        cron = registry.get("cron")
        assert cron.name == "cron"

        windows = registry.get("windows")
        assert windows.name == "windows"

    def test_get_nonexistent_provider(self) -> None:
        """Test getting a nonexistent provider raises error."""
        registry = SchedulerProviderRegistry()

        with pytest.raises(SchedulerProviderNotFoundError):
            registry.get("nonexistent")

    def test_get_default_provider(self) -> None:
        """Test getting the default provider for current platform."""
        registry = SchedulerProviderRegistry()
        provider = registry.get_default()

        assert provider is not None
        assert hasattr(provider, "name")
        assert hasattr(provider, "is_available")
        assert hasattr(provider, "install")
        assert hasattr(provider, "uninstall")
        assert hasattr(provider, "status")
        assert hasattr(provider, "get_config")

        # Check expected default by platform
        system = platform.system()
        if system == "Darwin":
            assert provider.name == "launchd"
        elif system == "Windows":
            assert provider.name == "windows"
        # Linux could be systemd or cron depending on availability

    def test_provider_lazy_loading(self) -> None:
        """Test providers are lazily loaded."""
        registry = SchedulerProviderRegistry()

        # Initially no instances
        assert len(registry._instances) == 0

        # Get a provider
        registry.get("launchd")

        # Now one instance
        assert len(registry._instances) == 1
        assert "launchd" in registry._instances

    def test_get_available_providers(self) -> None:
        """Test getting available providers for current system."""
        registry = SchedulerProviderRegistry()
        available = registry.get_available_providers()

        # At least one provider should be available on any platform
        assert len(available) >= 1

        # All returned providers should have is_available() == True
        for provider in available:
            assert provider.is_available() is True


class TestProviderInterfaces:
    """Tests for provider interface compliance."""

    def test_all_providers_implement_interface(self) -> None:
        """Test all providers implement SchedulerProvider interface."""
        registry = SchedulerProviderRegistry()

        for name in registry.list_providers():
            provider = registry.get(name)

            # Check all abstract methods are implemented
            assert hasattr(provider, "name")
            assert hasattr(provider, "display_name")
            assert hasattr(provider, "is_available")
            assert hasattr(provider, "install")
            assert hasattr(provider, "uninstall")
            assert hasattr(provider, "status")
            assert hasattr(provider, "get_config")

            # Check properties return correct types
            assert isinstance(provider.name, str)
            assert isinstance(provider.display_name, str)
            assert isinstance(provider.is_available(), bool)

            # Check status returns correct type
            status = provider.status()
            assert isinstance(status, SchedulerStatus)

            # Check config returns correct type
            config = provider.get_config()
            assert isinstance(config, SchedulerConfig)

    def test_provider_names_are_unique(self) -> None:
        """Test all providers have unique names."""
        registry = SchedulerProviderRegistry()
        names = set()

        for provider_name in registry.list_providers():
            provider = registry.get(provider_name)
            assert provider.name not in names, f"Duplicate provider name: {provider.name}"
            names.add(provider.name)
