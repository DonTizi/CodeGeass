"""Codex CLI executable discovery."""

import logging
import shutil
from functools import lru_cache
from pathlib import Path

import yaml

from codegeass.providers.exceptions import ProviderNotAvailableError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_codex_executable() -> str:
    """Get the path to the codex executable.

    Checks in order:
    1. Settings file (config/settings.yaml -> codex.executable)
    2. shutil.which('codex')
    3. Common installation paths

    Returns:
        Path to the codex executable

    Raises:
        ProviderNotAvailableError: If codex executable cannot be found
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
                    executable = settings.get("codex", {}).get("executable")
                    if executable and Path(executable).exists():
                        logger.debug(f"Using codex from settings: {executable}")
                        return str(executable)
            except Exception as e:
                logger.warning(f"Failed to load settings from {settings_path}: {e}")

    # Try shutil.which
    which_codex = shutil.which("codex")
    if which_codex:
        logger.debug(f"Using codex from PATH: {which_codex}")
        return which_codex

    # Try common installation paths
    common_paths = [
        Path.home() / ".local" / "bin" / "codex",
        Path("/usr/local/bin/codex"),
        Path("/usr/bin/codex"),
        # npm global installation paths
        Path.home() / ".npm-global" / "bin" / "codex",
        Path("/usr/local/lib/node_modules/.bin/codex"),
    ]

    for path in common_paths:
        if path.exists():
            logger.debug(f"Using codex from common path: {path}")
            return str(path)

    raise ProviderNotAvailableError(
        "codex",
        "Codex executable not found. Please install OpenAI Codex CLI or set "
        "codex.executable in config/settings.yaml",
    )
