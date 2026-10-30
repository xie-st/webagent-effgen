"""Build the bounded decision context from a frame and accumulated state."""
from __future__ import annotations

import re
from typing import Any, Mapping

from .contracts import Context, Frame
from .recover import feedback, progress
from .state import TaskState


def _fingerprint(view: Mapping[str, Any]) -> str:
    return re.sub(r"\[\d+\]", "[id]", str(view.get("text", "")))


def build_context(frame: Frame, state: TaskState) -> Context:
    history = frame.history
    current = {"url": frame.url, "text": frame.ax}
    unchanged_count = sum(
        _fingerprint(item.get("observation", {})) == _fingerprint(current)
        for item in history[-3:]
    )

    raw_actions = [
        item["action"] for item in history if isinstance(item.get("action"), str)
    ] or list(frame.action_history)
    repeated_action = (
        len(raw_actions) >= 2 and raw_actions[-1] == raw_actions[-2]
    )

    recovery_feedback = ""
    if repeated_action or unchanged_count >= 2:
        recovery_feedback = (
            "The last action was repeated or the page is unchanged. Check whether it "
            "had any effect. Do not repeat the same ineffective action; look for "
            "validation errors, scroll to missing controls, or use a different "
            "visible navigation route."
        )
    m2_feedback = feedback(frame, state)
    if m2_feedback:
        recovery_feedback = (recovery_feedback + "\n" + m2_feedback).strip()

    past_views: list[Mapping[str, Any]] = []
    for item in reversed(history):
        view = item.get("observation", {})
        if not isinstance(view, Mapping):
            continue
        if _fingerprint(view) == _fingerprint(current):
            continue
        if any(_fingerprint(view) == _fingerprint(old) for old in past_views):
            continue
        past_views.append(
            {
                "url": view.get("url"),
                "text": str(view.get("text", ""))[-5000:],
                "action_taken": item.get("action"),
            }
        )
        if len(past_views) == 2:
            break

    pending = state.pending_for(frame.tab)
    effective_deadline = state.deadline
    if effective_deadline is None or (
        frame.deadline is not None and frame.deadline < effective_deadline
    ):
        effective_deadline = frame.deadline

    return Context(
        task=frame.task,
        run_id=frame.run_id,
        step=frame.step,
        url=frame.url,
        tab=frame.tab,
        observation_version=frame.observation_version,
        page=frame.ax,
        current_ids=tuple(re.findall(r"^\s*\[(\d+)\]", frame.ax, flags=re.M)),
        past_views=tuple(reversed(past_views)),
        recent_actions=tuple(frame.action_history[-16:]),
        memory=state.memory,
        recovery_feedback=recovery_feedback,
        remaining_seconds=state.remaining_seconds,
        deadline=effective_deadline,
        capabilities=frame.capabilities,
        previous_receipt=frame.previous_receipt,
        unchanged_count=unchanged_count,
        repeated_action=repeated_action,
        last_action=raw_actions[-1] if raw_actions else None,
        screenshot=frame.screenshot,
        goal_checks=tuple(goal.as_dict() for goal in state.goal_checks),
        pending_action=pending.as_dict() if pending is not None else None,
        write_guard=(
            "read_only_required"
            if pending is not None and pending.status == "unknown"
            else None
        ),
        verification_feedback=m2_feedback,
        goal_progress=progress(state),
    )
