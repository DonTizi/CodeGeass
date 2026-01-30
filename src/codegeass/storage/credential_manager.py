"""Credential manager for storing secrets in ~/.codegeass/."""

from pathlib import Path

import yaml

# Default location for CodeGeass home directory
CODEGEASS_HOME = Path.home() / ".codegeass"
CREDENTIALS_FILE = CODEGEASS_HOME / "credentials.yaml"


class CredentialManager:
    """Manages credentials stored in ~/.codegeass/credentials.yaml.

    This class handles secure storage of sensitive data like API tokens
    and webhook URLs. Credentials are stored separately from project
    configuration to avoid accidentally committing secrets to version control.

    Structure of credentials.yaml:
        telegram_devops:
          bot_token: "123456:ABC-DEF..."
        discord_alerts:
          webhook_url: "https://discord.com/api/webhooks/..."
    """

    def __init__(self, credentials_file: Path = CREDENTIALS_FILE):
        self._file = credentials_file
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure the ~/.codegeass/ directory exists."""
        self._file.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, dict[str, str]]:
        """Read credentials file."""
        if not self._file.exists():
            return {}

        with open(self._file) as f:
            content = yaml.safe_load(f)
            return content if content else {}

    def _write(self, data: dict[str, dict[str, str]]) -> None:
        """Write credentials file."""
        self._ensure_dir()

        with open(self._file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Set restrictive permissions (owner read/write only)
        self._file.chmod(0o600)

    def get(self, key: str) -> dict[str, str] | None:
        """Retrieve credentials for a key.

        Args:
            key: Credential key (e.g., 'telegram_devops')

        Returns:
            Dict of credential fields, or None if not found
        """
        data = self._read()
        return data.get(key)

    def save(self, key: str, credentials: dict[str, str]) -> None:
        """Save credentials for a key.

        Args:
            key: Credential key
            credentials: Dict of credential fields
        """
        data = self._read()
        data[key] = credentials
        self._write(data)

    def delete(self, key: str) -> bool:
        """Delete credentials for a key.

        Args:
            key: Credential key

        Returns:
            True if deleted, False if not found
        """
        data = self._read()
        if key in data:
            del data[key]
            self._write(data)
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if credentials exist for a key."""
        return self.get(key) is not None

    def list_keys(self) -> list[str]:
        """List all credential keys."""
        return list(self._read().keys())

    def update(self, key: str, updates: dict[str, str]) -> bool:
        """Update specific fields in existing credentials.

        Args:
            key: Credential key
            updates: Fields to update

        Returns:
            True if updated, False if key not found
        """
        data = self._read()
        if key not in data:
            return False

        data[key].update(updates)
        self._write(data)
        return True

    def rename(self, old_key: str, new_key: str) -> bool:
        """Rename a credential key.

        Args:
            old_key: Current key name
            new_key: New key name

        Returns:
            True if renamed, False if old_key not found or new_key exists
        """
        data = self._read()
        if old_key not in data or new_key in data:
            return False

        data[new_key] = data.pop(old_key)
        self._write(data)
        return True


# Global instance
_manager: CredentialManager | None = None


def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
    global _manager
    if _manager is None:
        _manager = CredentialManager()
    return _manager
