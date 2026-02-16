"""Hooks module for Claude Code settings passthrough.

This module provides tag-based hooks that map task tags to Claude Code
hook configurations, passing them via --settings to the CLI.
"""

from codegeass.hooks.models import HookHandler, HookMatcher, TagHooks
from codegeass.hooks.repository import HookRepository
from codegeass.hooks.resolver import HookResolver

__all__ = [
    "HookHandler",
    "HookMatcher",
    "TagHooks",
    "HookRepository",
    "HookResolver",
]
