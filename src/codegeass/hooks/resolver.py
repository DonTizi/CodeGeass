"""Hook resolver for merging tag hooks into Claude Code settings.

This module provides the HookResolver class that:
1. Resolves tags to their hook configurations
2. Merges multiple tag hooks into a single settings dict
3. Writes merged settings to a temp file for --settings flag
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codegeass.hooks.repository import HookRepository


class HookResolver:
    """Resolves and merges tag hooks into Claude Code settings.

    The resolver takes a list of tags, retrieves their hook configurations
    from the repository, merges them into a single settings dict, and can
    write that to a temp file for use with Claude Code's --settings flag.

    Merge Strategy:
        - Hooks for the same event are concatenated (not replaced)
        - Later tags' hooks are appended after earlier tags' hooks
        - This allows layering multiple behaviors (e.g., "production" + "linted")

    Attributes:
        repo: HookRepository for retrieving tag configurations

    Example:
        >>> resolver = HookResolver(repo)
        >>> settings = resolver.resolve(["production", "linted"])
        >>> settings_path = resolver.write_temp_settings(settings)
        >>> # Use with: claude -p "..." --settings {settings_path}
    """

    def __init__(self, repo: HookRepository):
        """Initialize with a hook repository.

        Args:
            repo: HookRepository for retrieving tag configurations
        """
        self.repo = repo

    def resolve(self, tags: list[str]) -> dict[str, Any]:
        """Resolve tags to merged Claude Code settings.

        Merges hooks from all provided tags into a single settings dict.
        Hooks for the same event are concatenated.

        Args:
            tags: List of tag names to resolve

        Returns:
            Merged Claude Code settings dict. Empty dict if no valid tags
            or no hooks configured.

        Example:
            >>> settings = resolver.resolve(["production", "formatted"])
            >>> print(settings)
            {
                "hooks": {
                    "PreToolUse": [...],  # Combined from both tags
                    "PostToolUse": [...], # From "formatted" tag
                }
            }
        """
        if not tags:
            return {}

        # Collect all hooks, merging by event
        merged_hooks: dict[str, list[dict[str, Any]]] = {}

        for tag in tags:
            tag_hooks = self.repo.get_tag(tag)
            if not tag_hooks:
                continue

            for event, matchers in tag_hooks.hooks.items():
                if event not in merged_hooks:
                    merged_hooks[event] = []
                merged_hooks[event].extend(matchers)

        if not merged_hooks:
            return {}

        return {"hooks": merged_hooks}

    def resolve_for_task(
        self,
        tags: list[str],
        working_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Resolve tags with task-specific context.

        Enhanced version of resolve() that can substitute
        task-specific variables in hook commands.

        Args:
            tags: List of tag names to resolve
            working_dir: Task's working directory (for variable substitution)

        Returns:
            Merged Claude Code settings dict with variables substituted.
        """
        settings = self.resolve(tags)

        if not settings or "hooks" not in settings:
            return settings

        # Substitute variables in commands
        if working_dir:
            settings = self._substitute_variables(settings, {
                "WORKING_DIR": str(working_dir),
                "PROJECT_ROOT": str(working_dir),
            })

        return settings

    def _substitute_variables(
        self,
        settings: dict[str, Any],
        variables: dict[str, str],
    ) -> dict[str, Any]:
        """Substitute variables in hook commands.

        Args:
            settings: Settings dict to process
            variables: Variable name -> value mapping

        Returns:
            Settings dict with variables substituted.
        """
        import copy
        result = copy.deepcopy(settings)

        hooks = result.get("hooks", {})
        for event, matchers in hooks.items():
            for matcher in matchers:
                for handler in matcher.get("hooks", []):
                    if "command" in handler:
                        for var_name, var_value in variables.items():
                            handler["command"] = handler["command"].replace(
                                f"${{{var_name}}}", var_value
                            )
                            handler["command"] = handler["command"].replace(
                                f"${var_name}", var_value
                            )

        return result

    def write_temp_settings(self, settings: dict[str, Any]) -> Path:
        """Write settings to a temporary JSON file.

        Creates a temp file that persists until explicitly deleted
        (useful for passing to --settings flag).

        Args:
            settings: Claude Code settings dict to write

        Returns:
            Path to the temporary settings file.

        Note:
            The caller is responsible for cleaning up the temp file
            after the Claude execution completes.
        """
        # Create temp file that won't auto-delete
        fd, path = tempfile.mkstemp(
            prefix="codegeass-hooks-",
            suffix=".json",
        )

        with open(fd, "w") as f:
            json.dump(settings, f, indent=2)

        return Path(path)

    def get_preview(self, tags: list[str]) -> str:
        """Get a human-readable preview of merged hooks.

        Useful for CLI commands to show what hooks would be applied.

        Args:
            tags: List of tag names

        Returns:
            Formatted string preview of the merged hooks.
        """
        settings = self.resolve(tags)

        if not settings or "hooks" not in settings:
            return "No hooks configured"

        lines = []
        hooks = settings["hooks"]

        for event in sorted(hooks.keys()):
            matchers = hooks[event]
            lines.append(f"\n{event}:")
            for matcher in matchers:
                matcher_pattern = matcher.get("matcher", "(all)")
                lines.append(f"  Matcher: {matcher_pattern}")
                for handler in matcher.get("hooks", []):
                    handler_type = handler.get("type", "unknown")
                    if handler_type == "command":
                        lines.append(f"    → command: {handler.get('command', '?')}")
                    elif handler_type == "prompt":
                        prompt = handler.get("prompt", "?")[:50]
                        lines.append(f"    → prompt: {prompt}...")
                    else:
                        lines.append(f"    → {handler_type}")

        return "\n".join(lines)

    def validate_tags(self, tags: list[str]) -> tuple[list[str], list[str]]:
        """Validate which tags exist.

        Args:
            tags: List of tag names to validate

        Returns:
            Tuple of (valid_tags, invalid_tags)
        """
        valid = []
        invalid = []

        for tag in tags:
            if self.repo.exists(tag):
                valid.append(tag)
            else:
                invalid.append(tag)

        return valid, invalid
