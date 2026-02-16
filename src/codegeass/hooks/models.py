"""Hook models for Claude Code settings passthrough.

This module defines the value objects for hook configuration:
- HookHandler: A single hook handler (command, prompt, or agent)
- HookMatcher: A matcher group with handlers
- TagHooks: Full hook configuration for a tag
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HookHandler:
    """Single hook handler (command, prompt, or agent).

    Represents one handler that gets invoked when a hook event fires.
    Handlers can be shell commands, prompt injections, or agent invocations.

    Attributes:
        type: Handler type - "command", "prompt", or "agent"
        command: Shell command to execute (for command type)
        prompt: Prompt text to inject (for prompt type)
        timeout: Execution timeout in seconds
        is_async: Run handler asynchronously (default False)

    Example:
        >>> handler = HookHandler(
        ...     type="command",
        ...     command="/path/to/validate.sh",
        ...     timeout=10
        ... )
    """

    type: str  # "command", "prompt", "agent"
    command: str | None = None
    prompt: str | None = None
    timeout: int | None = None
    is_async: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for Claude Code settings."""
        result: dict[str, Any] = {"type": self.type}

        if self.command is not None:
            result["command"] = self.command
        if self.prompt is not None:
            result["prompt"] = self.prompt
        if self.timeout is not None:
            result["timeout"] = self.timeout
        if self.is_async:
            result["async"] = True

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HookHandler:
        """Create from dictionary."""
        return cls(
            type=data.get("type", "command"),
            command=data.get("command"),
            prompt=data.get("prompt"),
            timeout=data.get("timeout"),
            is_async=data.get("async", False),
        )


@dataclass(frozen=True)
class HookMatcher:
    """Matcher group with handlers.

    Groups handlers under a regex pattern that matches tool names.
    None matcher means match all tools.

    Attributes:
        matcher: Regex pattern for tool names (None = match all)
        hooks: Tuple of handlers to invoke on match

    Example:
        >>> matcher = HookMatcher(
        ...     matcher="Bash",
        ...     hooks=(HookHandler(type="command", command="/validate.sh"),)
        ... )
    """

    matcher: str | None  # Regex pattern, None = match all
    hooks: tuple[HookHandler, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for Claude Code settings."""
        result: dict[str, Any] = {
            "hooks": [h.to_dict() for h in self.hooks],
        }
        if self.matcher is not None:
            result["matcher"] = self.matcher
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HookMatcher:
        """Create from dictionary."""
        hooks_data = data.get("hooks", [])
        hooks = tuple(HookHandler.from_dict(h) for h in hooks_data)
        return cls(
            matcher=data.get("matcher"),
            hooks=hooks,
        )


@dataclass
class TagHooks:
    """Hooks configuration for a tag.

    Represents the complete hook configuration associated with a tag.
    Tags are applied to tasks and their hooks are merged and passed
    to Claude Code via --settings.

    Attributes:
        tag: Unique tag identifier (e.g., "production", "linted")
        description: Human-readable description of what this tag does
        hooks: Event name → list of matcher groups

    Hook Events:
        - PreToolUse: Before a tool is invoked (exit 2 blocks)
        - PostToolUse: After successful tool invocation
        - PostToolUseFailure: After tool failure
        - Stop: When execution stops
        - SessionStart: At session start
        - SessionEnd: At session end
        - Notification: When Claude sends a notification
        - SubagentStart: When a subagent starts
        - SubagentStop: When a subagent stops
        - UserPromptSubmit: When user submits a prompt
        - PermissionRequest: When Claude requests permission
        - PreCompact: Before conversation compaction

    Example:
        >>> hooks = TagHooks(
        ...     tag="production",
        ...     description="Safety hooks for production tasks",
        ...     hooks={
        ...         "PreToolUse": [
        ...             {"matcher": "Bash", "hooks": [{"type": "command", "command": "/x.sh"}]}
        ...         ]
        ...     }
        ... )
        >>> settings = hooks.to_claude_settings()
    """

    tag: str
    description: str = ""
    hooks: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    # Valid Claude Code hook events
    VALID_EVENTS = frozenset([
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "Stop",
        "SessionStart",
        "SessionEnd",
        "Notification",
        "SubagentStart",
        "SubagentStop",
        "UserPromptSubmit",
        "PermissionRequest",
        "PreCompact",
    ])

    def to_claude_settings(self) -> dict[str, Any]:
        """Convert to Claude Code settings format.

        Returns:
            Dictionary suitable for use as Claude Code --settings file.

        Example output:
            {
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "Bash", "hooks": [{"type": "command", "command": "/script.sh"}]}
                    ]
                }
            }
        """
        if not self.hooks:
            return {}

        return {"hooks": self.hooks}

    def get_matchers(self, event: str) -> list[HookMatcher]:
        """Get parsed HookMatchers for an event.

        Args:
            event: Hook event name (e.g., "PreToolUse")

        Returns:
            List of HookMatcher objects for the event.
        """
        matchers_data = self.hooks.get(event, [])
        return [HookMatcher.from_dict(m) for m in matchers_data]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tag": self.tag,
            "description": self.description,
            "hooks": self.hooks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TagHooks:
        """Create from dictionary."""
        return cls(
            tag=data["tag"],
            description=data.get("description", ""),
            hooks=data.get("hooks", {}),
        )

    def validate(self) -> list[str]:
        """Validate the hook configuration.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        if not self.tag:
            errors.append("Tag name is required")

        if not self.tag.replace("-", "").replace("_", "").isalnum():
            errors.append("Tag must be alphanumeric with hyphens/underscores only")

        for event_name in self.hooks:
            if event_name not in self.VALID_EVENTS:
                errors.append(f"Unknown hook event: {event_name}")

            for i, matcher_data in enumerate(self.hooks[event_name]):
                if "hooks" not in matcher_data:
                    errors.append(f"{event_name}[{i}]: Missing 'hooks' field")
                    continue

                for j, handler_data in enumerate(matcher_data.get("hooks", [])):
                    handler_type = handler_data.get("type")
                    if handler_type not in ("command", "prompt", "agent"):
                        errors.append(
                            f"{event_name}[{i}].hooks[{j}]: Invalid type '{handler_type}'"
                        )

                    if handler_type == "command" and not handler_data.get("command"):
                        errors.append(
                            f"{event_name}[{i}].hooks[{j}]: command type requires 'command' field"
                        )

                    if handler_type == "prompt" and not handler_data.get("prompt"):
                        errors.append(
                            f"{event_name}[{i}].hooks[{j}]: prompt type requires 'prompt' field"
                        )

        return errors
