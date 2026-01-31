"""Centralized parser for Claude CLI stream-json output.

DEPRECATED: This module is deprecated. Use codegeass.providers.claude.output_parser instead.
This re-export is provided for backward compatibility.
"""

import warnings

# Re-export from new location for backward compatibility
from codegeass.providers.claude.output_parser import (
    ParsedOutput as _ParsedOutput,
)
from codegeass.providers.claude.output_parser import (
    extract_clean_text as _extract_clean_text,
)
from codegeass.providers.claude.output_parser import (
    parse_stream_json as _parse_stream_json,
)

# Re-export types without deprecation warning
ParsedOutput = _ParsedOutput


def parse_stream_json(raw_output: str) -> ParsedOutput:
    """Parse Claude CLI stream-json output to extract clean text.

    DEPRECATED: Use codegeass.providers.claude.output_parser.parse_stream_json() instead.
    """
    warnings.warn(
        "codegeass.execution.output_parser.parse_stream_json is deprecated. "
        "Use codegeass.providers.claude.output_parser.parse_stream_json instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _parse_stream_json(raw_output)


def extract_clean_text(raw_output: str, max_length: int | None = None) -> str:
    """Get clean text from Claude CLI stream-json output.

    DEPRECATED: Use codegeass.providers.claude.output_parser.extract_clean_text() instead.
    """
    warnings.warn(
        "codegeass.execution.output_parser.extract_clean_text is deprecated. "
        "Use codegeass.providers.claude.output_parser.extract_clean_text instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _extract_clean_text(raw_output, max_length)
