"""Message formatter for notifications."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from jinja2 import Template

from codegeass.notifications.models import NotificationEvent

if TYPE_CHECKING:
    from codegeass.core.entities import Task
    from codegeass.core.value_objects import ExecutionResult


class MessageFormatter:
    """Formats notification messages using Jinja2 templates.

    Each notification event type has a default template that can be
    customized per provider or channel.
    """

    # Output truncation limits per provider (in characters)
    # Teams has 28KB limit for Adaptive Cards, so we can use a much higher limit
    PROVIDER_OUTPUT_LIMITS: dict[str, int] = {
        "telegram": 4000,  # Telegram message limit is 4096
        "discord": 2000,   # Discord embed limit
        "teams": 20000,    # Teams Adaptive Card can handle up to 28KB
    }
    DEFAULT_OUTPUT_LIMIT = 2000

    # Default templates for each event type (compact format, no emojis)
    # Uses {{ max_output_length }} variable set per provider
    TEMPLATES: dict[NotificationEvent, str] = {
        NotificationEvent.TASK_START: """
<b>{{ task.name }}</b> - Running...
<code>{{ task.working_dir }}</code>
{{ started_at }}
        """.strip(),
        NotificationEvent.TASK_COMPLETE: """
<b>{{ task.name }}</b> - {{ status | upper }}
Duration: {{ duration }}s
{% if include_output and output %}
<pre>{{ output | truncate(max_output_length) }}</pre>
{% endif %}
        """.strip(),
        NotificationEvent.TASK_SUCCESS: """
<b>{{ task.name }}</b> - SUCCESS
Duration: {{ duration }}s
{% if include_output and output %}
<pre>{{ output | truncate(max_output_length) }}</pre>
{% endif %}
        """.strip(),
        NotificationEvent.TASK_FAILURE: """
<b>{{ task.name }}</b> - FAILED
Duration: {{ duration }}s
Error: {{ error or "Unknown error" }}
{% if include_output and output %}
<pre>{{ output | truncate(max_output_length) }}</pre>
{% endif %}
        """.strip(),
        NotificationEvent.DAILY_SUMMARY: """
<b>Daily Summary</b> - {{ date }}
Success: {{ successes }} | Failed: {{ failures }} | Rate: {{ success_rate }}%
        """.strip(),
    }

    def __init__(self, custom_templates: dict[NotificationEvent, str] | None = None):
        """Initialize formatter with optional custom templates.

        Args:
            custom_templates: Override default templates for specific events
        """
        self._templates = {**self.TEMPLATES}
        if custom_templates:
            self._templates.update(custom_templates)

    def format(
        self,
        event: NotificationEvent,
        task: "Task | None" = None,
        result: "ExecutionResult | None" = None,
        include_output: bool = False,
        max_output_length: int | None = None,
        **extra_context: Any,
    ) -> str:
        """Format a notification message.

        Args:
            event: The notification event type
            task: Task that triggered the event
            result: Execution result (for completion events)
            include_output: Whether to include task output
            max_output_length: Max chars for output (default: DEFAULT_OUTPUT_LIMIT)
            **extra_context: Additional template context

        Returns:
            Formatted message string
        """
        limit = max_output_length or self.DEFAULT_OUTPUT_LIMIT
        context = self._build_context(
            event, task, result, include_output, max_output_length=limit, **extra_context
        )
        template = Template(self._templates[event])
        return template.render(**context).strip()

    def _build_context(
        self,
        event: NotificationEvent,
        task: "Task | None",
        result: "ExecutionResult | None",
        include_output: bool,
        max_output_length: int = 2000,
        **extra: Any,
    ) -> dict[str, Any]:
        """Build template context from task and result."""
        context: dict[str, Any] = {
            "event": event.value,
            "include_output": include_output,
            "max_output_length": max_output_length,
            "now": datetime.now().isoformat(),
            **extra,
        }

        if task:
            context["task"] = task
            context["task_name"] = task.name
            context["task_id"] = task.id

        if result:
            context["status"] = result.status.value
            # Use provider-aware clean_output (handles both Claude and Codex formats)
            if include_output:
                clean = result.clean_output
                # Truncate if needed
                if clean and len(clean) > max_output_length:
                    clean = clean[:max_output_length] + "..."
                context["output"] = clean
            else:
                context["output"] = None
            context["error"] = result.error
            context["duration"] = f"{result.duration_seconds:.1f}"
            context["started_at"] = result.started_at.strftime("%Y-%m-%d %H:%M:%S")
            context["finished_at"] = result.finished_at.strftime("%Y-%m-%d %H:%M:%S")
            context["session_id"] = result.session_id
        elif event == NotificationEvent.TASK_START:
            context["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return context

    def format_for_provider(
        self,
        provider: str,
        event: NotificationEvent,
        task: "Task | None" = None,
        result: "ExecutionResult | None" = None,
        include_output: bool = False,
        **extra_context: Any,
    ) -> str:
        """Format a message with provider-specific adjustments.

        Args:
            provider: Provider name (e.g., 'telegram', 'discord', 'teams')
            event: Notification event type
            task: Task that triggered the event
            result: Execution result
            include_output: Whether to include output
            **extra_context: Additional context

        Returns:
            Formatted message
        """
        # Get provider-specific output limit
        max_output_length = self.PROVIDER_OUTPUT_LIMITS.get(provider, self.DEFAULT_OUTPUT_LIMIT)

        message = self.format(
            event, task, result, include_output,
            max_output_length=max_output_length, **extra_context
        )

        # Apply provider-specific formatting
        if provider == "discord":
            # Convert HTML to Discord Markdown
            message = self._html_to_discord_markdown(message)
        elif provider == "teams":
            # Convert HTML to Teams Markdown
            message = self._html_to_teams_markdown(message)

        return message

    def _html_to_discord_markdown(self, html: str) -> str:
        """Convert HTML-formatted message to Discord Markdown."""
        # Simple conversions
        conversions = [
            ("<b>", "**"),
            ("</b>", "**"),
            ("<i>", "_"),
            ("</i>", "_"),
            ("<code>", "`"),
            ("</code>", "`"),
            ("<pre>", "```\n"),
            ("</pre>", "\n```"),
        ]

        result = html
        for html_tag, md in conversions:
            result = result.replace(html_tag, md)

        return result

    def _html_to_teams_markdown(self, html: str) -> str:
        """Convert HTML-formatted message to Teams Markdown.

        Teams supports similar Markdown formatting to Discord.
        """
        # Same conversions as Discord (Teams uses similar Markdown)
        conversions = [
            ("<b>", "**"),
            ("</b>", "**"),
            ("<i>", "_"),
            ("</i>", "_"),
            ("<code>", "`"),
            ("</code>", "`"),
            ("<pre>", "```\n"),
            ("</pre>", "\n```"),
        ]

        result = html
        for html_tag, md in conversions:
            result = result.replace(html_tag, md)

        return result


# Global formatter instance
_formatter: MessageFormatter | None = None


def get_message_formatter() -> MessageFormatter:
    """Get the global message formatter instance."""
    global _formatter
    if _formatter is None:
        _formatter = MessageFormatter()
    return _formatter
