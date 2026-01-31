"""Claude CLI executable discovery."""

import logging
import shutil
from functools import lru_cache
from pathlib import Path

import yaml

from codegeass.providers.exceptions import ProviderNotAvailableError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_claude_executable() -> str:
    """Get the path to the claude executable.

    Checks in order:
    1. Settings file (config/settings.yaml -> claude.executable)
    2. shutil.which('claude')
    3. Common installation paths

    Returns:
        Path to the claude executable

    Raises:
        ProviderNotAvailableError: If claude executable cannot be found
    """
    # Try to load from settings
    settings_paths = [
        Path.cwd() / "config" / "settings.yaml",
        Path(__file__).parent.parent.parent.parent.parent / "config" / "settings.yaml",
    ]

    for settings_path in settings_paths:
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    settings = yaml.safe_load(f)
                    executable = settings.get("claude", {}).get("executable")
                    if executable and Path(executable).exists():
                        logger.debug(f"Using claude from settings: {executable}")
                        return str(executable)
            except Exception as e:
                logger.warning(f"Failed to load settings from {settings_path}: {e}")

    # Try shutil.which
    which_claude = shutil.which("claude")
    if which_claude:
        logger.debug(f"Using claude from PATH: {which_claude}")
        return which_claude

    # Try common installation paths
    common_paths = [
        Path.home() / ".local" / "bin" / "claude",
        Path("/usr/local/bin/claude"),
        Path("/usr/bin/claude"),
    ]

    for path in common_paths:
        if path.exists():
            logger.debug(f"Using claude from common path: {path}")
            return str(path)

    raise ProviderNotAvailableError(
        "claude",
        "Claude executable not found. Please install Claude Code or set "
        "claude.executable in config/settings.yaml",
    )
