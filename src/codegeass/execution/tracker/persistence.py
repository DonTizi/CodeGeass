"""Persistence logic for execution tracker."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from codegeass.execution.tracker.execution import ActiveExecution

logger = logging.getLogger(__name__)


class ExecutionPersistence:
    """Handles persistence of active executions to disk."""

    def __init__(self, data_dir: Path):
        """Initialize persistence with data directory."""
        self._data_dir = data_dir
        self._persistence_file = data_dir / "active_executions.json"

    def load(self) -> dict[str, ActiveExecution]:
        """Load active executions from persistence file."""
        if not self._persistence_file.exists():
            return {}

        try:
            with open(self._persistence_file) as f:
                data = json.load(f)

            result = {}
            for exec_data in data.get("executions", []):
                execution = ActiveExecution.from_dict(exec_data)
                result[execution.execution_id] = execution
                logger.info(f"Recovered active execution: {execution.execution_id}")

            return result

        except Exception as e:
            logger.warning(f"Failed to load active executions: {e}")
            return {}

    def save(self, active: dict[str, ActiveExecution]) -> None:
        """Persist active executions to file."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            data: dict[str, Any] = {
                "executions": [ex.to_dict() for ex in active.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(self._persistence_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save active executions: {e}")

    def clear(self) -> None:
        """Delete the persistence file."""
        if self._persistence_file.exists():
            self._persistence_file.unlink()
