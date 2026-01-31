"""Universal Code Execution Provider Architecture.

This module provides a standardized interface for multiple AI coding assistants
(Claude Code, OpenAI Codex, etc.) through an adapter pattern.

Usage:
    from codegeass.providers import get_provider_registry, CodeProvider

    registry = get_provider_registry()
    provider = registry.get("claude")
    info = provider.get_info()
"""

from codegeass.providers.base import (
    CodeProvider,
    ExecutionRequest,
    ExecutionResponse,
    ProviderCapabilities,
    ProviderInfo,
)
from codegeass.providers.exceptions import (
    ProviderCapabilityError,
    ProviderError,
    ProviderExecutionError,
    ProviderNotAvailableError,
    ProviderNotFoundError,
)
from codegeass.providers.registry import ProviderRegistry, get_provider_registry

__all__ = [
    # Base classes
    "CodeProvider",
    "ProviderCapabilities",
    "ExecutionRequest",
    "ExecutionResponse",
    "ProviderInfo",
    # Registry
    "ProviderRegistry",
    "get_provider_registry",
    # Exceptions
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderCapabilityError",
    "ProviderExecutionError",
    "ProviderNotAvailableError",
]
