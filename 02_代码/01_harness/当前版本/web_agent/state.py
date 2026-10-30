"""The single mutable task state for the M2 short fix.

State owns only facts the runtime needs across callbacks: memory, one pending
operation per tab, input focus/replace intent, the last local readback,
completed operation keys, stalled-step accounting, screenshots and the one
absolute deadline.  It does not extract task goals or store a proof tree.
"""
from __future__ import annotations

import time
from typing import Any, Mapping, MutableMapping
from urllib.parse import urlsplit

from .contracts import Frame, PendingAction, ScreenshotReference

MAX_MEMORY = 10_000
MAX_COMPLETED = 30
_SCREENSHOT_BINDING = (
    "image_id",
    "mime_type",
    "width",
    "height",
    "byte_size",
    "sha256",
    "step",
    "run_id",
    "tab",
    "observation_version",
    "url",
)


def _identity_parts(url: str) -> tuple[str, str | None]:
    parts = urlsplit(str(url))
    base = f"{parts.scheme}://{parts.netloc}"
    segments = [part for part in parts.path.split("/") if part]
    lowered = [part.lower() for part in segments]
    for marker in ("user", "users", "u", "profile"):
        if marker in lowered:
            index = lowered.index(marker)
            if index + 1 < len(segments):
                return base, base + "/" + marker + "/" + segments[index + 1]
    return base, None


def identity_key(url: str) -> str:
    origin, account = _identity_parts(url)
    return account or origin


def _identity_origin(identity: str) -> str:
    parts = urlsplit(identity)
    return f"{parts.scheme}://{parts.netloc}"


class TaskState:
    """Thin owner for memory, pending operations and local readback facts."""

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

    @property
    def deadline(self) -> float | None:
        value = self.data.get("_execution_deadline")
        return float(value) if isinstance(value, (int, float)) else None

    def update_deadline(self, deadline: float | None) -> float | None:
        """Keep one absolute task deadline; a later frame never renews it."""
        if deadline is not None:
            value = float(deadline)
            stored = self.deadline
            if stored is None or value < stored:
                self.data["_execution_deadline"] = value
                stored = value
            self.data["_remaining_seconds"] = max(0.0, stored - time.time())
            return stored
        return self.deadline

    @property
    def task(self) -> str:
        value = self.data.get("_task", "")
        return value if isinstance(value, str) else ""

    def set_task(self, task: str) -> None:
        if not isinstance(task, str):
            raise TypeError("task must be a string")
        self.data["_task"] = task

    @property
    def run_id(self) -> str | None:
        value = self.data.get("_run_id")
        return value if isinstance(value, str) else None

    @property
    def pending(self) -> list[PendingAction]:
        return self.pending_actions()

    def pending_for(self, tab: int | str) -> PendingAction | None:
        value = self.data.get("_pending_actions")
        if not isinstance(value, dict):
            return None
        item = value.get(str(tab))
        return item if isinstance(item, PendingAction) else None

    def pending_actions(self) -> list[PendingAction]:
        value = self.data.get("_pending_actions")
        if not isinstance(value, dict):
            return []
        return [item for item in value.values() if isinstance(item, PendingAction)]

    def set_pending(self, pending: PendingAction) -> None:
        if not isinstance(pending, PendingAction):
            raise TypeError("pending must be a PendingAction")
        value = self.data.get("_pending_actions")
        if not isinstance(value, dict):
            value = {}
            self.data["_pending_actions"] = value
        if str(pending.tab) in value:
            raise ValueError("one pending action per tab is already registered")
        value[str(pending.tab)] = pending

    def replace_pending(self, pending: PendingAction | None, *, tab: int | str) -> None:
        value = self.data.get("_pending_actions")
        if not isinstance(value, dict):
            value = {}
            self.data["_pending_actions"] = value
        if pending is None:
            value.pop(str(tab), None)
        else:
            value[str(tab)] = pending

    def clear_pending(self, tab: int | str) -> None:
        self.replace_pending(None, tab=tab)

    @property
    def drafts(self) -> dict[str, Any]:
        value = self.data.get("_drafts")
        return value if isinstance(value, dict) else {}

    def set_draft(self, element_id: str, value: Mapping[str, Any]) -> None:
        drafts = self.drafts
        if value.get("field_key") is not None:
            for key, old in list(drafts.items()):
                if old.get("url") == value.get("url") and old.get("field_key") == value.get("field_key"):
                    drafts.pop(key)
        drafts[str(element_id)] = dict(value)
        self.data["_drafts"] = drafts

    # ------------------------------------------------------------------ focus
    @property
    def focus(self) -> dict[str, Any] | None:
        value = self.data.get("_focus")
        return dict(value) if isinstance(value, Mapping) else None

    def set_focus(self, field_key: Mapping[str, Any] | None, element_id: str | None = None) -> None:
        if not isinstance(field_key, Mapping):
            self.clear_focus()
            return
        previous = self.focus
        key = dict(field_key)
        if previous is not None and previous.get("field_key") != key:
            self.data.pop("_replace", None)
        self.data["_focus"] = {"field_key": key, "element_id": element_id}

    def clear_focus(self) -> None:
        self.data.pop("_focus", None)
        self.data.pop("_replace", None)

    def arm_replace(self, field_key: Mapping[str, Any] | None) -> None:
        if isinstance(field_key, Mapping):
            self.data["_replace"] = {"field_key": dict(field_key)}
            self.data["_focus"] = {"field_key": dict(field_key), "element_id": None}

    def replace_armed(self, field_key: Mapping[str, Any] | None) -> bool:
        value = self.data.get("_replace")
        if not isinstance(value, Mapping) or not isinstance(field_key, Mapping):
            return False
        return value.get("field_key") == dict(field_key)

    def clear_replace(self) -> None:
        self.data.pop("_replace", None)

    # --------------------------------------------------------------- readback
    @property
    def last_result(self) -> dict[str, Any] | None:
        value = self.data.get("_last_result")
        return dict(value) if isinstance(value, Mapping) else None

    def set_last_result(
        self,
        status: str,
        detail: str = "",
        *,
        step: int | None = None,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        self.data["_last_result"] = {
            "status": str(status),
            "detail": str(detail)[:1200],
            "step": step,
            "expected": expected,
            "actual": actual,
        }

    @property
    def unresolved(self) -> bool:
        return bool(self.data.get("_unresolved"))

    @property
    def unresolved_reason(self) -> str:
        value = self.data.get("_unresolved_reason")
        return value if isinstance(value, str) else ""

    def mark_unresolved(self, reason: str) -> None:
        self.data["_unresolved"] = True
        self.data["_unresolved_reason"] = str(reason)[:600]

    def mark_resolved(self) -> None:
        self.data["_unresolved"] = False
        self.data["_unresolved_reason"] = ""

    @property
    def completed(self) -> list[dict[str, Any]]:
        value = self.data.get("_completed")
        return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []

    def add_completed(self, kind: str, key: str, result: Mapping[str, Any] | None = None) -> None:
        items = self.data.get("_completed")
        if not isinstance(items, list):
            items = []
            self.data["_completed"] = items
        items.append({"kind": str(kind), "key": str(key), "detail": dict(result or {})})
        del items[:-MAX_COMPLETED]

    def completed_has(self, kind: str, key: str) -> bool:
        return any(item.get("kind") == kind and item.get("key") == key for item in self.completed)

    @property
    def failures(self) -> dict[str, int]:
        value = self.data.get("_failures")
        return dict(value) if isinstance(value, dict) else {}

    def add_failed(self, key: str, result: Mapping[str, Any] | None = None) -> None:
        value = self.data.get("_failures")
        if not isinstance(value, dict):
            value = {}
            self.data["_failures"] = value
        value[str(key)] = int(value.get(str(key), 0)) + 1
        self.data["_last_failure"] = dict(result or {})

    def failed_count(self, key: str) -> int:
        return int(self.failures.get(str(key), 0))

    def clear_failures(self) -> None:
        self.data.pop("_failures", None)
        self.data.pop("_last_failure", None)

    # -------------------------------------------------------------- progress
    @property
    def step_count(self) -> int:
        value = self.data.get("_step_count", 0)
        return value if isinstance(value, int) and value >= 0 else 0

    def note_step(self) -> int:
        self.data["_step_count"] = self.step_count + 1
        return self.data["_step_count"]

    @property
    def stalled_steps(self) -> int:
        value = self.data.get("_stalled_steps", 0)
        return value if isinstance(value, int) and value >= 0 else 0

    def note_observation(self, fingerprint: str) -> int:
        """Count consecutive unchanged observations with no local activity."""
        previous = self.data.get("_last_fingerprint")
        activity = bool(self.data.get("_activity"))
        if previous == fingerprint and not activity:
            self.data["_stalled_steps"] = self.stalled_steps + 1
        else:
            self.data["_stalled_steps"] = 0
        self.data["_last_fingerprint"] = str(fingerprint)
        self.data["_activity"] = False
        return self.stalled_steps

    def mark_activity(self) -> None:
        self.data["_activity"] = True

    # -------------------------------------------------------------- identity
    @property
    def identity(self) -> str:
        value = self.data.get("_identity")
        return value if isinstance(value, str) else ""

    def observe_identity(self, frame: Frame) -> bool:
        origin, account = _identity_parts(frame.url)
        new_identity = account or origin
        old_identity = self.identity
        if not old_identity:
            self.data["_identity"] = new_identity
            return False
        old_origin = _identity_origin(old_identity)
        old_is_account = old_identity != old_origin
        if old_origin == origin:
            if account is None:
                return False
            if old_identity == account:
                return False
            if not old_is_account:
                self.data["_identity"] = account
                return False
        self.data["_identity"] = new_identity
        changes = self.data.get("_identity_changes")
        if not isinstance(changes, list):
            changes = []
            self.data["_identity_changes"] = changes
        changes.append({"from": old_identity, "to": new_identity, "step": frame.step})
        self.clear_failures()
        return True

    # ------------------------------------------------------------ screenshot
    @property
    def screenshot_reference(self) -> Mapping[str, Any] | None:
        value = self.data.get("_screenshot_reference")
        return dict(value) if isinstance(value, Mapping) else None

    def set_screenshot_reference(self, value: Mapping[str, Any] | None) -> None:
        if value is None:
            self.data.pop("_screenshot_reference", None)
            return
        if not isinstance(value, Mapping):
            raise TypeError("screenshot reference must be a mapping")
        self.data["_screenshot_reference"] = dict(value)

    def invalidate_screenshot(self, frame: Frame) -> None:
        stored = self.screenshot_reference
        if stored is None:
            return
        reference: ScreenshotReference | None = frame.screenshot
        if reference is None:
            self.data.pop("_screenshot_reference", None)
            return
        bound = {key: getattr(reference, key) for key in _SCREENSHOT_BINDING}
        bound["step"] = frame.step
        if any(stored.get(key) != value for key, value in bound.items()):
            self.data.pop("_screenshot_reference", None)

    def screenshot_requested(self, step: int) -> bool:
        value = self.data.get("_screenshot_attempts")
        return isinstance(value, list) and step in value

    def mark_screenshot_attempt(self, step: int) -> None:
        value = self.data.get("_screenshot_attempts")
        if not isinstance(value, list):
            value = []
            self.data["_screenshot_attempts"] = value
        if step not in value:
            value.append(step)

    def clear(self) -> None:
        self.data.clear()

    def as_dict(self) -> MutableMapping[str, Any]:
        return self.data


__all__ = ["MAX_MEMORY", "TaskState", "identity_key"]
