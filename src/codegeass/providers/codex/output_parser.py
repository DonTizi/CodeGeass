"""Output parser for Codex CLI JSONL format."""

import json
from dataclasses import dataclass


@dataclass
class ParsedOutput:
    """Parsed output from Codex CLI."""

    session_id: str | None
    text: str
    raw_output: str


def parse_jsonl_output(raw_output: str) -> ParsedOutput:
    """Parse Codex CLI JSONL output to extract clean text.

    Codex outputs one JSON object per line (JSONL format).
    Common event types:
    - {"type": "thread.started", "thread_id": "..."} - session start
    - {"type": "item.completed", "item": {"type": "agent_message", "text": "..."}} - response
    - {"type": "turn.completed", "usage": {...}} - turn end with token usage
    - {"type": "message", "content": "..."} - legacy text output
    - {"type": "error", "message": "..."} - errors

    Args:
        raw_output: Raw output from Codex CLI

    Returns:
        ParsedOutput with session_id and clean text
    """
    if not raw_output:
        return ParsedOutput(session_id=None, text="", raw_output="")

    session_id: str | None = None
    text_parts: list[str] = []

    for line in raw_output.split("\n"):
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)

            # Extract session_id / thread_id if present
            if "session_id" in data and not session_id:
                session_id = data["session_id"]
            if "thread_id" in data and not session_id:
                session_id = data["thread_id"]

            # Extract text from message events
            event_type = data.get("type", "")

            # Codex item.completed event - main response format
            if event_type == "item.completed":
                item = data.get("item", {})
                item_type = item.get("type", "")
                item_text = item.get("text", "")
                # Only include agent_message, not reasoning/thinking
                if item_type == "agent_message" and item_text:
                    text_parts.append(item_text)

            elif event_type == "message":
                content = data.get("content", "")
                if content:
                    text_parts.append(content)

            elif event_type == "assistant":
                # Alternative format for assistant responses
                content = data.get("content", "")
                if content:
                    text_parts.append(content)

            elif event_type == "text":
                # Simple text event
                text = data.get("text", "") or data.get("content", "")
                if text:
                    text_parts.append(text)

            elif event_type == "error":
                # Include error messages in output
                error_msg = data.get("message", "") or data.get("error", "")
                if error_msg:
                    text_parts.append(f"Error: {error_msg}")

            elif event_type == "result":
                # Final result
                result = data.get("result", "")
                if result:
                    text_parts.append(str(result))

            # Handle raw content field at top level
            elif "content" in data and not event_type:
                text_parts.append(str(data["content"]))

        except json.JSONDecodeError:
            # Not JSON - treat as plain text
            if line and not line.startswith("{"):
                text_parts.append(line)

    # Combine text parts
    text = "\n".join(text_parts) if text_parts else ""

    return ParsedOutput(session_id=session_id, text=text, raw_output=raw_output)


def extract_session_id(raw_output: str) -> str | None:
    """Extract session ID from Codex CLI output.

    Args:
        raw_output: Raw output from Codex CLI

    Returns:
        Session ID if found, None otherwise
    """
    parsed = parse_jsonl_output(raw_output)
    return parsed.session_id


def extract_clean_text(raw_output: str, max_length: int | None = None) -> str:
    """Get clean text from Codex CLI output.

    Args:
        raw_output: Raw output from Codex CLI
        max_length: Optional max length to truncate text to

    Returns:
        Clean, human-readable text extracted from the output
    """
    parsed = parse_jsonl_output(raw_output)
    text = parsed.text
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text
