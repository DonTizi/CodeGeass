"""YAML file backend for configuration storage."""

from pathlib import Path
from typing import Any

import yaml


class YAMLBackend:
    """Low-level YAML file operations."""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def read(self) -> dict[str, Any]:
        """Read YAML file and return contents as dict."""
        if not self.file_path.exists():
            return {}

        with open(self.file_path) as f:
            content = yaml.safe_load(f)
            return content if content else {}

    def write(self, data: dict[str, Any]) -> None:
        """Write dict to YAML file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def exists(self) -> bool:
        """Check if file exists."""
        return self.file_path.exists()

    def delete(self) -> bool:
        """Delete the file if it exists."""
        if self.file_path.exists():
            self.file_path.unlink()
            return True
        return False


class YAMLListBackend:
    """YAML backend for list-based storage (schedules.yaml)."""

    def __init__(self, file_path: Path, list_key: str = "tasks"):
        self.file_path = file_path
        self.list_key = list_key
        self._backend = YAMLBackend(file_path)

    def read_all(self) -> list[dict[str, Any]]:
        """Read all items from the list."""
        data = self._backend.read()
        return data.get(self.list_key, [])

    def write_all(self, items: list[dict[str, Any]]) -> None:
        """Write all items to the list."""
        data = self._backend.read()
        data[self.list_key] = items
        self._backend.write(data)

    def append(self, item: dict[str, Any]) -> None:
        """Append an item to the list."""
        items = self.read_all()
        items.append(item)
        self.write_all(items)

    def find_by_key(self, key: str, value: Any) -> dict[str, Any] | None:
        """Find an item by key-value match."""
        for item in self.read_all():
            if item.get(key) == value:
                return item
        return None

    def update_by_key(self, key: str, value: Any, new_item: dict[str, Any]) -> bool:
        """Update an item matching key-value. Returns True if found and updated."""
        items = self.read_all()
        for i, item in enumerate(items):
            if item.get(key) == value:
                items[i] = new_item
                self.write_all(items)
                return True
        return False

    def delete_by_key(self, key: str, value: Any) -> bool:
        """Delete an item matching key-value. Returns True if found and deleted."""
        items = self.read_all()
        original_len = len(items)
        items = [item for item in items if item.get(key) != value]

        if len(items) < original_len:
            self.write_all(items)
            return True
        return False
