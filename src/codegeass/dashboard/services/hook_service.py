"""Hook service wrapping core HookRepository.

This service delegates to the core HookRepository and converts
between core models and API models.
"""

from codegeass.hooks.models import TagHooks
from codegeass.hooks.repository import HookRepository
from codegeass.hooks.resolver import HookResolver

from ..models.hook import (
    Hook,
    HookCreate,
    HookPreview,
    HookSummary,
    HookUpdate,
    HookValidation,
)


class HookService:
    """Service for managing hooks via the core HookRepository."""

    def __init__(self, hook_repo: HookRepository):
        """Initialize with a core HookRepository.

        Args:
            hook_repo: The core HookRepository to delegate to
        """
        self.hook_repo = hook_repo

    def _core_to_summary(self, tag_hooks: TagHooks, location: str | None) -> HookSummary:
        """Convert core TagHooks to API summary model."""
        return HookSummary(
            tag=tag_hooks.tag,
            description=tag_hooks.description,
            location=location or "unknown",
            events=sorted(tag_hooks.hooks.keys()),
        )

    def _core_to_api(self, tag_hooks: TagHooks, location: str | None = None) -> Hook:
        """Convert core TagHooks to API model."""
        return Hook(
            tag=tag_hooks.tag,
            description=tag_hooks.description,
            hooks=tag_hooks.hooks,
            location=location,
        )

    def list_tags(self) -> list[HookSummary]:
        """List all hook tags as summaries."""
        tags = self.hook_repo.list_tags()
        result = []

        for tag in tags:
            tag_hooks = self.hook_repo.get_tag(tag)
            if tag_hooks:
                location = self.hook_repo.get_tag_location(tag)
                result.append(self._core_to_summary(tag_hooks, location))

        return result

    def get_tag(self, tag: str) -> Hook | None:
        """Get full hook configuration for a tag."""
        tag_hooks = self.hook_repo.get_tag(tag)
        if not tag_hooks:
            return None

        location = self.hook_repo.get_tag_location(tag)
        return self._core_to_api(tag_hooks, location)

    def create_tag(self, data: HookCreate) -> Hook:
        """Create a new hook tag."""
        tag_hooks = TagHooks(
            tag=data.tag,
            description=data.description,
            hooks=data.hooks,
        )
        self.hook_repo.save_tag(tag_hooks, global_scope=data.global_scope)

        location = "global" if data.global_scope else "project"
        return self._core_to_api(tag_hooks, location)

    def update_tag(self, tag: str, data: HookUpdate) -> Hook | None:
        """Update an existing hook tag."""
        tag_hooks = self.hook_repo.get_tag(tag)
        if not tag_hooks:
            return None

        # Update fields
        description = data.description if data.description is not None else tag_hooks.description
        hooks = data.hooks if data.hooks is not None else tag_hooks.hooks

        updated = TagHooks(
            tag=tag,
            description=description,
            hooks=hooks,
        )

        # Save to same location
        location = self.hook_repo.get_tag_location(tag)
        global_scope = location == "global"
        self.hook_repo.save_tag(updated, global_scope=global_scope)

        return self._core_to_api(updated, location)

    def delete_tag(self, tag: str) -> bool:
        """Delete a hook tag."""
        return self.hook_repo.delete_tag(tag)

    def validate_tag(self, tag: str) -> HookValidation:
        """Validate a hook tag configuration."""
        tag_hooks = self.hook_repo.get_tag(tag)

        if not tag_hooks:
            return HookValidation(
                tag=tag,
                valid=False,
                errors=["Tag not found"],
            )

        errors = tag_hooks.validate()
        return HookValidation(
            tag=tag,
            valid=len(errors) == 0,
            errors=errors,
        )

    def preview_tags(self, tags: list[str]) -> HookPreview:
        """Preview merged hooks for given tags."""
        resolver = HookResolver(self.hook_repo)

        valid_tags, invalid_tags = resolver.validate_tags(tags)
        settings = resolver.resolve(valid_tags)
        preview = resolver.get_preview(valid_tags)

        return HookPreview(
            tags=valid_tags,
            preview=preview,
            settings=settings,
        )

    def init_templates(self, overwrite: bool = False) -> list[str]:
        """Initialize hooks from built-in templates."""
        return self.hook_repo.init_from_templates(overwrite=overwrite)

    def get_templates(self) -> list[str]:
        """Get list of available template names."""
        return self.hook_repo.get_templates()

    def exists(self, tag: str) -> bool:
        """Check if a tag exists."""
        return self.hook_repo.exists(tag)
