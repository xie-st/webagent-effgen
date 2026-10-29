"""The single mutable task state shared across M0 runtime calls."""
from __future__ import annotations

import time
from typing import Any, MutableMapping

MAX_MEMORY = 10_000


class TaskState:
    """Thin owner for memory and recovery data stored in the legacy state dict."""

    def __init__(self, data: MutableMapping[str, Any] | None = None):
        if data is None:
            data = {}
        if not isinstance(data, MutableMapping):
            raise TypeError("TaskState requires a mutable mapping")
        self.data = data

    @property
    def memory(self) -> str:
        value = self.data.get("memory", "")
        return value if isinstance(value, str) else ""

    @memory.setter
    def memory(self, value: str) -> None:
        if not isinstance(value, str) or len(value) > MAX_MEMORY:
            raise ValueError("Memory must be a string of at most 10000 characters")
        self.data["memory"] = value

    @property
    def recovery_count(self) -> int:
        value = self.data.get("_recovery_count", 0)
        return value if isinstance(value, int) and value >= 0 else 0

    @recovery_count.setter
    def recovery_count(self, value: int) -> None:
        if not isinstance(value, int) or value < 0:
            raise ValueError("Recovery count must be a non-negative integer")
        self.data["_recovery_count"] = value

    def next_recovery(self) -> int:
        index = self.recovery_count
        self.recovery_count = index + 1
        return index

    @property
    def remaining_seconds(self) -> float | None:
        value = self.data.get("_remaining_seconds")
        return value if isinstance(value, (int, float)) else None

    def update_deadline(self, deadline: float | None) -> None:
        if deadline is not None:
            self.data["_remaining_seconds"] = max(0.0, float(deadline) - time.time())

    def as_dict(self) -> MutableMapping[str, Any]:
        return self.data
