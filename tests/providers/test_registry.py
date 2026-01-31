"""Tests for provider registry."""

import pytest

from codegeass.providers import (
    ProviderNotFoundError,
    get_provider_registry,
)
from codegeass.providers.base import CodeProvider
from codegeass.providers.registry import ProviderRegistry


class TestProviderRegistry:
    """Tests for ProviderRegistry class."""

    def test_get_provider_registry_singleton(self):
        """Test that get_provider_registry returns singleton."""
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()
        assert registry1 is registry2

    def test_list_providers(self):
        """Test listing all provider names."""
        registry = get_provider_registry()
        providers = registry.list_providers()

        assert isinstance(providers, list)
        assert "claude" in providers
        assert "codex" in providers
        assert len(providers) >= 2

    def test_get_claude_provider(self):
        """Test getting Claude provider."""
        registry = get_provider_registry()
        provider = registry.get("claude")

        assert isinstance(provider, CodeProvider)
        assert provider.name == "claude"

    def test_get_codex_provider(self):
        """Test getting Codex provider."""
        registry = get_provider_registry()
        provider = registry.get("codex")

        assert isinstance(provider, CodeProvider)
        assert provider.name == "codex"

    def test_get_nonexistent_provider(self):
        """Test getting a provider that doesn't exist."""
        registry = get_provider_registry()

        with pytest.raises(ProviderNotFoundError) as exc_info:
            registry.get("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_provider_info(self):
        """Test getting provider info."""
        registry = get_provider_registry()
        info = registry.get_provider_info("claude")

        assert info.name == "claude"
        assert info.display_name == "Claude Code"
        assert info.capabilities.plan_mode is True
        assert info.capabilities.resume is True

    def test_get_provider_info_codex(self):
        """Test getting Codex provider info."""
        registry = get_provider_registry()
        info = registry.get_provider_info("codex")

        assert info.name == "codex"
        assert info.display_name == "OpenAI Codex"
        assert info.capabilities.plan_mode is False
        assert info.capabilities.resume is False
        assert info.capabilities.autonomous is True

    def test_list_provider_info(self):
        """Test listing all provider info."""
        registry = get_provider_registry()
        infos = registry.list_provider_info()

        assert len(infos) >= 2
        names = [info.name for info in infos]
        assert "claude" in names
        assert "codex" in names

    def test_is_available(self):
        """Test checking if a provider is available."""
        registry = get_provider_registry()

        # Both should be available if executables are installed
        # This is environment-dependent, so just check it doesn't error
        claude_available = registry.is_available("claude")
        assert isinstance(claude_available, bool)

        codex_available = registry.is_available("codex")
        assert isinstance(codex_available, bool)

    def test_get_available_providers(self):
        """Test getting list of available providers."""
        registry = get_provider_registry()
        available = registry.get_available()

        assert isinstance(available, list)
        # All returned should be available
        for provider in available:
            assert provider.is_available()

    def test_lazy_loading(self):
        """Test that providers are lazily loaded."""
        # Create a fresh registry to test lazy loading
        registry = ProviderRegistry()

        # Before accessing, _instances should be empty
        assert len(registry._instances) == 0

        # Access a provider
        provider = registry.get("claude")
        assert provider is not None

        # Now it should be cached
        assert "claude" in registry._instances

        # Access again - should return same instance
        provider2 = registry.get("claude")
        assert provider is provider2

    def test_provider_caching(self):
        """Test that providers are cached after first load."""
        registry = get_provider_registry()

        # Get twice
        p1 = registry.get("claude")
        p2 = registry.get("claude")

        # Should be same instance
        assert p1 is p2
