"""Claude CLI executable discovery.

DEPRECATED: This module is deprecated. Use codegeass.providers.claude.cli instead.
This re-export is provided for backward compatibility.
"""

import warnings

# Re-export from new location for backward compatibility
from codegeass.providers.claude.cli import get_claude_executable as _get_claude_executable


def get_claude_executable() -> str:
    """Get the path to the claude executable.

    DEPRECATED: Use codegeass.providers.claude.get_claude_executable() instead.

    Returns:
        Path to the claude executable

    Raises:
        ProviderNotAvailableError: If claude executable cannot be found
    """
    warnings.warn(
        "codegeass.execution.strategies.claude_cli.get_claude_executable is deprecated. "
        "Use codegeass.providers.claude.get_claude_executable instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_claude_executable()
