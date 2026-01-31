"""Output parser for Claude CLI stream-json format."""

import json
import re
from dataclasses import dataclass


@dataclass
class ParsedOutput:
    """Parsed output from Claude CLI stream-json."""

    session_id: str | None
    text: str
    raw_output: str


def parse_stream_json(raw_output: str) -> ParsedOutput:
    """Parse Claude CLI stream-json output to extract clean text.

    Handles:
    - {"type":"system",...} - metadata, extract session_id
    - {"type":"stream_event","event":{"type":"content_block_delta",...}} - text chunks
    - {"type":"assistant","message":{"content":[...]}} - full message
    - {"type":"result",...} - skip (final stats)

    Args:
        raw_output: Raw output from Claude CLI with stream-json format

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

            # Extract session_id from system message
            if data.get("type") == "system" and data.get("session_id"):
                session_id = data["session_id"]
                continue

            # Handle result type - extract the "result" field which contains the actual text
            if data.get("type") == "result":
                # The "result" type contains the final text in the "result" field
                if "result" in data and data["result"]:
                    text_parts.append(str(data["result"]))
                # Also extract session_id if present
                if not session_id and data.get("session_id"):
                    session_id = data["session_id"]
                continue

            # Extract text from stream_event
            if data.get("type") == "stream_event":
                event = data.get("event", {})
                # Skip metadata events
                if event.get("type") in (
                    "message_start",
                    "message_stop",
                    "message_delta",
                    "content_block_start",
                    "content_block_stop",
                ):
                    continue
                # Extract text delta
                if (
                    event.get("type") == "content_block_delta"
                    and event.get("delta", {}).get("type") == "text_delta"
                ):
                    text = event.get("delta", {}).get("text", "")
                    if text:
                        text_parts.append(text)
                continue

            # Extract from assistant message
            if data.get("type") == "assistant":
                content = data.get("message", {}).get("content", [])
                for block in content:
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        # If we have stream deltas, don't duplicate with full message
                        if text and not text_parts:
                            text_parts.append(text)
                # Also try to get session_id from assistant message
                if not session_id:
                    session_id = data.get("session_id")
                continue

            # Legacy format: single JSON with result field
            if "result" in data:
                text_parts.append(str(data["result"]))
                session_id = session_id or data.get("session_id")
                continue

            # Extract session_id from any JSON with session_id field
            if "session_id" in data and not session_id:
                session_id = data["session_id"]

            # Handle error field
            if "error" in data:
                text_parts.append(str(data["error"]))

        except json.JSONDecodeError:
            # Not JSON - might be plain text or contain session_id
            if "session_id" in line.lower() and not session_id:
                match = re.search(r"[a-f0-9-]{36}", line)
                if match:
                    session_id = match.group(0)
            elif line and not line.startswith("{"):
                # Plain text line
                text_parts.append(line)

    # Combine text parts
    # Avoid returning raw JSON as text - if we couldn't parse anything meaningful,
    # return empty string instead of the raw JSON output
    text = "".join(text_parts)
    if not text and raw_output.strip().startswith("{"):
        # Raw output is JSON that we couldn't extract text from - don't return it as text
        text = ""

    return ParsedOutput(session_id=session_id, text=text, raw_output=raw_output)


def extract_session_id(raw_output: str) -> str | None:
    """Extract session ID from Claude CLI output.

    Args:
        raw_output: Raw output from Claude CLI

    Returns:
        Session ID if found, None otherwise
    """
    parsed = parse_stream_json(raw_output)
    return parsed.session_id


def extract_clean_text(raw_output: str, max_length: int | None = None) -> str:
    """Get clean text from Claude CLI stream-json output.

    Args:
        raw_output: Raw output from Claude CLI with stream-json format
        max_length: Optional max length to truncate text to

    Returns:
        Clean, human-readable text extracted from the output
    """
    parsed = parse_stream_json(raw_output)
    text = parsed.text
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text
