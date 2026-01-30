"""Message formatter for notifications."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from jinja2 import Template

from codegeass.execution.output_parser import extract_clean_text
from codegeass.notifications.models import NotificationEvent

if TYPE_CHECKING:
    from codegeass.core.entities import Task
    from codegeass.core.value_objects import ExecutionResult


class MessageFormatter:
    """Formats notification messages using Jinja2 templates.

    Each notification event type has a default template that can be
    customized per provider or channel.
    """

    # Default templates for each event type (compact format, no emojis)
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
<pre>{{ output | truncate(300) }}</pre>
{% endif %}
        """.strip(),
        NotificationEvent.TASK_SUCCESS: """
<b>{{ task.name }}</b> - SUCCESS
Duration: {{ duration }}s
{% if include_output and output %}
<pre>{{ output | truncate(300) }}</pre>
{% endif %}
        """.strip(),
        NotificationEvent.TASK_FAILURE: """
<b>{{ task.name }}</b> - FAILED
Duration: {{ duration }}s
Error: {{ error or "Unknown error" }}
{% if include_output and output %}
<pre>{{ output | truncate(300) }}</pre>
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
        **extra_context: Any,
    ) -> str:
        """Format a notification message.

        Args:
            event: The notification event type
            task: Task that triggered the event
            result: Execution result (for completion events)
            include_output: Whether to include task output
            **extra_context: Additional template context

        Returns:
            Formatted message string
        """
        context = self._build_context(event, task, result, include_output, **extra_context)
        template = Template(self._templates[event])
        return template.render(**context).strip()

    def _build_context(
        self,
        event: NotificationEvent,
        task: "Task | None",
        result: "ExecutionResult | None",
        include_output: bool,
        **extra: Any,
    ) -> dict[str, Any]:
        """Build template context from task and result."""
        context: dict[str, Any] = {
            "event": event.value,
            "include_output": include_output,
            "now": datetime.now().isoformat(),
            **extra,
        }

        if task:
            context["task"] = task
            context["task_name"] = task.name
            context["task_id"] = task.id

        if result:
            context["status"] = result.status.value
            # Extract human-readable output from Claude CLI JSON
            context["output"] = (
                extract_clean_text(result.output, max_length=1000) if include_output else None
            )
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
            provider: Provider name (e.g., 'telegram', 'discord')
            event: Notification event type
            task: Task that triggered the event
            result: Execution result
            include_output: Whether to include output
            **extra_context: Additional context

        Returns:
            Formatted message
        """
        message = self.format(event, task, result, include_output, **extra_context)

        # Apply provider-specific formatting
        if provider == "discord":
            # Convert HTML to Discord Markdown
            message = self._html_to_discord_markdown(message)
        elif provider == "teams":
            # Convert HTML to Teams Markdown (same as Discord)
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
