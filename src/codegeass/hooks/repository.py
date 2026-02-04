"""Hook repository for CRUD operations on tag hook configurations.

This module provides the HookRepository class for managing hook configurations
stored in YAML files. Hooks can be stored at project level (.codegeass/hooks/)
or global level (~/.codegeass/hooks/).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import yaml

if TYPE_CHECKING:
    from codegeass.hooks.models import TagHooks


class HookRepositoryProtocol(Protocol):
    """Protocol for hook repository implementations."""

    def list_tags(self) -> list[str]:
        """List all available tag names."""
        ...

    def get_tag(self, tag: str) -> TagHooks | None:
        """Get hook configuration for a tag."""
        ...

    def save_tag(self, tag_hooks: TagHooks) -> None:
        """Save hook configuration for a tag."""
        ...

    def delete_tag(self, tag: str) -> bool:
        """Delete a tag's hook configuration."""
        ...

    def exists(self, tag: str) -> bool:
        """Check if a tag exists."""
        ...


class HookRepository:
    """Repository for managing tag hook configurations.

    Manages hook configurations stored as YAML files. Supports both
    project-level hooks (.codegeass/hooks/) and global hooks (~/.codegeass/hooks/).

    Project hooks take precedence over global hooks when both exist.

    Storage format:
        .codegeass/hooks/{tag}.yaml  (project-level)
        ~/.codegeass/hooks/{tag}.yaml (global)

    Attributes:
        project_hooks_dir: Path to project-level hooks directory
        global_hooks_dir: Path to global hooks directory

    Example:
        >>> repo = HookRepository(
        ...     project_hooks_dir=Path(".codegeass/hooks"),
        ...     global_hooks_dir=Path.home() / ".codegeass/hooks"
        ... )
        >>> tags = repo.list_tags()
        >>> production_hooks = repo.get_tag("production")
    """

    def __init__(
        self,
        project_hooks_dir: Path | None = None,
        global_hooks_dir: Path | None = None,
    ):
        """Initialize hook repository.

        Args:
            project_hooks_dir: Path to project-level hooks (optional)
            global_hooks_dir: Path to global hooks (optional)
        """
        self.project_hooks_dir = project_hooks_dir
        self.global_hooks_dir = global_hooks_dir or (Path.home() / ".codegeass" / "hooks")

    def _ensure_dirs(self) -> None:
        """Ensure hook directories exist."""
        if self.project_hooks_dir:
            self.project_hooks_dir.mkdir(parents=True, exist_ok=True)
        self.global_hooks_dir.mkdir(parents=True, exist_ok=True)

    def _get_hook_file(self, tag: str, global_only: bool = False) -> Path | None:
        """Get the path to a tag's hook file.

        Checks project-level first, then global. Returns None if not found.

        Args:
            tag: Tag name
            global_only: If True, only check global hooks

        Returns:
            Path to the hook file, or None if not found.
        """
        if not global_only and self.project_hooks_dir:
            project_file = self.project_hooks_dir / f"{tag}.yaml"
            if project_file.exists():
                return project_file

        global_file = self.global_hooks_dir / f"{tag}.yaml"
        if global_file.exists():
            return global_file

        return None

    def list_tags(self) -> list[str]:
        """List all available tag names.

        Returns tags from both project and global directories,
        with duplicates removed (project tags take precedence).

        Returns:
            List of unique tag names.
        """
        tags = set()

        # Collect project tags
        if self.project_hooks_dir and self.project_hooks_dir.exists():
            for file in self.project_hooks_dir.glob("*.yaml"):
                tags.add(file.stem)

        # Collect global tags
        if self.global_hooks_dir.exists():
            for file in self.global_hooks_dir.glob("*.yaml"):
                tags.add(file.stem)

        return sorted(tags)

    def get_tag(self, tag: str) -> TagHooks | None:
        """Get hook configuration for a tag.

        Args:
            tag: Tag name to retrieve

        Returns:
            TagHooks object, or None if not found.
        """
        from codegeass.hooks.models import TagHooks

        hook_file = self._get_hook_file(tag)
        if not hook_file:
            return None

        try:
            with open(hook_file) as f:
                data = yaml.safe_load(f)
                if not data:
                    return None

                # Ensure tag is set (may be missing in file)
                data["tag"] = tag
                return TagHooks.from_dict(data)
        except Exception:
            return None

    def get_all(self) -> list[TagHooks]:
        """Get all tag hook configurations.

        Returns:
            List of all TagHooks objects.
        """
        result = []
        for tag in self.list_tags():
            tag_hooks = self.get_tag(tag)
            if tag_hooks:
                result.append(tag_hooks)
        return result

    def save_tag(
        self,
        tag_hooks: TagHooks,
        global_scope: bool = False,
    ) -> None:
        """Save hook configuration for a tag.

        Args:
            tag_hooks: TagHooks object to save
            global_scope: If True, save to global directory instead of project

        Raises:
            ValueError: If tag_hooks validation fails.
        """
        errors = tag_hooks.validate()
        if errors:
            raise ValueError(f"Invalid hook configuration: {', '.join(errors)}")

        self._ensure_dirs()

        if global_scope:
            hook_file = self.global_hooks_dir / f"{tag_hooks.tag}.yaml"
        elif self.project_hooks_dir:
            hook_file = self.project_hooks_dir / f"{tag_hooks.tag}.yaml"
        else:
            # No project dir, fall back to global
            hook_file = self.global_hooks_dir / f"{tag_hooks.tag}.yaml"

        hook_file.parent.mkdir(parents=True, exist_ok=True)

        # Write as YAML (without the tag field, since filename is tag)
        data = {
            "description": tag_hooks.description,
            "hooks": tag_hooks.hooks,
        }

        with open(hook_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def delete_tag(self, tag: str) -> bool:
        """Delete a tag's hook configuration.

        Deletes from both project and global directories if present.

        Args:
            tag: Tag name to delete

        Returns:
            True if at least one file was deleted.
        """
        deleted = False

        if self.project_hooks_dir:
            project_file = self.project_hooks_dir / f"{tag}.yaml"
            if project_file.exists():
                project_file.unlink()
                deleted = True

        global_file = self.global_hooks_dir / f"{tag}.yaml"
        if global_file.exists():
            global_file.unlink()
            deleted = True

        return deleted

    def exists(self, tag: str) -> bool:
        """Check if a tag exists.

        Args:
            tag: Tag name to check

        Returns:
            True if the tag exists.
        """
        return self._get_hook_file(tag) is not None

    def get_tag_location(self, tag: str) -> str | None:
        """Get the location (project/global) of a tag.

        Args:
            tag: Tag name

        Returns:
            "project", "global", or None if not found.
        """
        if self.project_hooks_dir:
            project_file = self.project_hooks_dir / f"{tag}.yaml"
            if project_file.exists():
                return "project"

        global_file = self.global_hooks_dir / f"{tag}.yaml"
        if global_file.exists():
            return "global"

        return None

    def init_from_templates(self, overwrite: bool = False) -> list[str]:
        """Initialize hooks from built-in templates.

        Copies template files to the global hooks directory.

        Args:
            overwrite: If True, overwrite existing hooks

        Returns:
            List of initialized tag names.
        """
        templates_dir = Path(__file__).parent / "templates"
        if not templates_dir.exists():
            return []

        self._ensure_dirs()
        initialized = []

        for template_file in templates_dir.glob("*.yaml"):
            tag = template_file.stem
            target = self.global_hooks_dir / f"{tag}.yaml"

            if target.exists() and not overwrite:
                continue

            shutil.copy(template_file, target)
            initialized.append(tag)

        return sorted(initialized)

    def get_templates(self) -> list[str]:
        """Get list of available built-in template names.

        Returns:
            List of template tag names.
        """
        templates_dir = Path(__file__).parent / "templates"
        if not templates_dir.exists():
            return []

        return sorted(f.stem for f in templates_dir.glob("*.yaml"))
