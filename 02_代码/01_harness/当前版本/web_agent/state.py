"""The single mutable task state shared by the runtime and all M2 checks.

The state owns the task text, extracted goal checks, one pending action per tab,
drafts, verified evidence, page identity and the absolute deadline.  Verification
and recovery only propose changes; ``Runtime`` applies them here.
"""
from __future__ import annotations

import time
from typing import Any, Mapping, MutableMapping
from urllib.parse import urlsplit

from .contracts import Frame, GoalCheck, PendingAction, ScreenshotReference

MAX_MEMORY = 10_000
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
    """Return the site origin and an explicit account key when the URL has one."""
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
    """Return the account/page identity that owns verified evidence.

    A normal route change inside one site does not invalidate every confirmed
    value.  A different origin or account (for example ``/user/alice`` versus
    ``/user/bob``) does.
    """
    origin, account = _identity_parts(url)
    return account or origin


def _identity_origin(identity: str) -> str:
    parts = urlsplit(identity)
    return f"{parts.scheme}://{parts.netloc}"


class TaskState:
    """Thin owner for memory, goals, pending effects and recovery data."""

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
    def goals_initialized(self) -> bool:
        return bool(self.data.get("_goals_initialized"))

    @property
    def goal_checks(self) -> list[GoalCheck]:
        value = self.data.get("_goal_checks")
        return value if isinstance(value, list) else []

    def set_goal_checks(self, goals: list[GoalCheck], *, mark_initialized: bool = True) -> None:
        if not isinstance(goals, list) or not all(isinstance(item, GoalCheck) for item in goals):
            raise TypeError("goal checks must be a list of GoalCheck")
        self.data["_goal_checks"] = goals
        if mark_initialized:
            self.data["_goals_initialized"] = True

    def goal(self, goal_id: str) -> GoalCheck | None:
        for item in self.goal_checks:
            if item.goal_id == goal_id:
                return item
        return None

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
        drafts[str(element_id)] = dict(value)
        self.data["_drafts"] = drafts

    @property
    def identity(self) -> str:
        value = self.data.get("_identity")
        return value if isinstance(value, str) else ""

    def observe_identity(self, frame: Frame) -> bool:
        """Update page identity and stale old evidence only on a real switch.

        Generic same-origin pages (forums, listings, product pages) keep the
        established account identity and its verified evidence.  A different
        origin or an explicit different account still invalidates it.
        """
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
                # A generic page is not an identity change; keep the account
                # established for this task and the evidence bound to it.
                return False
            if old_identity == account:
                return False
            if not old_is_account:
                # Only the origin was known; adopt this account without
                # discarding progress verified elsewhere on the same site.
                self.data["_identity"] = account
                return False
        self.data["_identity"] = new_identity
        changes = self.data.get("_identity_changes")
        if not isinstance(changes, list):
            changes = []
            self.data["_identity_changes"] = changes
        changes.append({"from": old_identity, "to": new_identity, "step": frame.step})
        for goal in self.goal_checks:
            if goal.status == "verified":
                goal.status = "stale"
        return True

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
        """Drop a reference that is not bound to the current observation."""
        stored = self.screenshot_reference
        if stored is None:
            return
        reference: ScreenshotReference | None = frame.screenshot
        if reference is None:
            self.data.pop("_screenshot_reference", None)
            return
        bound = {key: getattr(reference, key) for key in _SCREENSHOT_BINDING}
        # The stored reference is one observation's evidence.  A reused
        # reference keeps its own step, so compare against the current frame
        # step instead of trusting frame.screenshot alone.
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

    def as_dict(self) -> MutableMapping[str, Any]:
        return self.data


__all__ = ["MAX_MEMORY", "TaskState", "identity_key"]
