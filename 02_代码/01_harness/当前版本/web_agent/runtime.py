"""One-decision runtime with local M2 operation readback.

The default path asks EffGen exactly once per ordinary step.  A malformed
action may get one correction call.  There is no separate verification model,
no task-goal regex extraction and no model-written proof object.  The runtime
resolves the previous operation from the next AX, applies a small read-only
write guard, registers the new operation, and enforces one absolute deadline
plus a bounded no-progress exit.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any

from . import observe, operations
from .ax import AXTree
from .actions import validate_action
from .contracts import Context, Frame
from .screenshots import ScreenshotCapture, ScreenshotPort
from .state import MAX_MEMORY, TaskState

DecisionPort = Callable[[Context, TaskState], str | Mapping[str, Any]]

# Bound repairs of one observation, not the number of task/browser steps.
MAX_DECISION_CORRECTIONS = 1
# Hand control back before the platform's own transport timeout.
DEADLINE_RESERVE_SECONDS = 6.0
# Consecutive unchanged observations without a local effect before Incomplete.
MAX_STALLED_STEPS = 3
# Hard step ceiling; the 300-second deadline remains the primary budget.
MAX_TASK_STEPS = 40


class Runtime:
    """Drive either a legacy decision port or an EffGen raw-decision policy."""

    def __init__(
        self,
        decision_port: DecisionPort | None = None,
        *,
        policy=None,
        screenshot_port: ScreenshotPort | None = None,
        telemetry=None,
        completion_check=None,
    ):
        if (decision_port is None) == (policy is None):
            raise ValueError("Provide exactly one of decision_port or policy")
        if decision_port is not None and not callable(decision_port):
            raise TypeError("decision_port must be callable")
        self.decision_port = decision_port
        self.policy = policy
        self.screenshot_port = screenshot_port
        self._telemetry = telemetry or getattr(policy, "telemetry", None)
        self.completion_check = completion_check

        self._active_frame: Frame | None = None
        self._active_state: TaskState | None = None
        self._verification_screenshot_done = False

    def advance(
        self,
        frame: Frame,
        state: TaskState | dict[str, Any],
        *,
        screenshot_reason: str | None = None,
    ) -> dict[str, str]:
        task_state = state if isinstance(state, TaskState) else TaskState(state)
        effective_deadline = task_state.update_deadline(frame.deadline)
        if effective_deadline is not None and frame.deadline != effective_deadline:
            frame = replace(frame, deadline=effective_deadline)
        task_state.invalidate_screenshot(frame)
        task_state.observe_identity(frame)
        if (task_state.remaining_seconds is not None
                and 0 < task_state.remaining_seconds < DEADLINE_RESERVE_SECONDS):
            # Reserve transport and platform grading time; this is Incomplete,
            # never a successful stop.
            return {"action": "stop [Incomplete: execution time is nearly exhausted]"}
        self._active_frame = frame
        self._active_state = task_state
        self._verification_screenshot_done = False
        if screenshot_reason is not None:
            self.request_screenshot(frame, task_state, reason=screenshot_reason)
        try:
            pending = task_state.pending_for(frame.tab)
            if pending is not None and pending.step < frame.step:
                operations.resolve(frame, task_state, telemetry=self._telemetry)

            stalled = task_state.note_observation(observe.fingerprint(frame.ax))
            step_count = task_state.note_step()
            if stalled >= MAX_STALLED_STEPS:
                return {"action": (
                    "stop [Incomplete: no observable progress for "
                    f"{stalled} consecutive observations]"
                )}
            if step_count > MAX_TASK_STEPS:
                return {"action": (
                    "stop [Incomplete: local step ceiling "
                    f"{MAX_TASK_STEPS} reached]"
                )}

            continuation = self._resume_input(frame, task_state)
            if continuation is not None:
                return {"action": continuation}

            context = observe.build_context(frame, task_state)
            if self.policy is None:
                proposal = self.decision_port(context, task_state)
                action, memory = _unpack(proposal)
                action = validate_action(action, frame.as_observation())
                if memory is not None and len(memory) > MAX_MEMORY:
                    raise ValueError("Memory must be a string of at most 10000 characters")
                selected, accepted = self._finalize(frame, task_state, action)
                if accepted and memory is not None:
                    task_state.memory = memory
                return {"action": selected}

            decision = self._policy_decision(context, task_state, frame)
            return {"action": decision["action"]}
        except Exception:
            # Diagnostic only; a screenshot never turns an action into success.
            try:
                self._request_verification_screenshot(frame, task_state, reason="diagnostic")
            except Exception:
                pass
            raise
        finally:
            self._active_frame = None
            self._active_state = None

    def _resume_input(self, frame: Frame, state: TaskState) -> str | None:
        sequence = state.data.get("_input_sequence")
        if not isinstance(sequence, dict):
            return None
        node = AXTree(frame).find_field(sequence["field_key"])
        if frame.url != sequence["url"] or node is None:
            state.data.pop("_input_sequence", None)
            state.clear_replace()
            state.clear_focus()
            state.mark_unresolved("replacement interrupted; locate the original field again")
            from urllib.parse import urlsplit
            before, current = urlsplit(sequence['url']), urlsplit(frame.url)
            if (before.scheme, before.netloc) != (current.scheme, current.netloc):
                return "stop [Incomplete: input origin changed during replacement]"
            state.set_last_result('blocked', 'Input sequence cancelled after page/field change. '
                                  'Use the current observation to locate the intended field again; '
                                  'no stale select, clear or type action was executed.', step=frame.step)
            return None
        focused = AXTree(frame).focused_field()
        if focused is not None and focused.field_key != node.field_key:
            state.data.pop("_input_sequence", None)
            state.mark_unresolved("focus moved to another field; replacement cancelled")
            return "stop [Incomplete: focus changed before replacement]"
        if sequence["phase"] in {"select", "end"}:
            action = "press [Ctrl+A]" if sequence["phase"] == "select" else "press [Ctrl+End]"
            sequence["phase"] = "clear" if sequence["phase"] == "select" else "type"
        elif sequence["phase"] == "clear":
            sequence["phase"] = "type"
            action = "press [Backspace]"
        else:
            state.data.pop("_input_sequence", None)
            if sequence.get('mode') == 'replace':
                state.arm_replace(node.field_key)
            action = f'type [{node.element_id}] [{sequence["text"]}] [{sequence["enter"]}]'
        selected, _ = self._finalize(frame, state, action)
        return selected

    def _finalize(self, frame: Frame, state: TaskState, action: str,
                  input_mode: str | None = None) -> tuple[str, bool]:
        action = action.strip()
        plan = operations.plan(action, frame, state)
        if plan.kind == "stop" and self.completion_check is not None:
            if not self.completion_check(frame, state):
                state.set_last_result("blocked", "browser completion condition is not satisfied", step=frame.step)
                return "press [Tab]", False
            # A guarded browser draft may complete without persistence. This
            # callback must never release an unresolved business submission.
            if not state.pending_actions():
                state.mark_resolved()
        blocked = operations.guard(plan, frame, state, telemetry=self._telemetry)
        if blocked is not None:
            return blocked.action, False
        state.data.pop('_guard_block_streak', None)
        if plan.kind == 'commit' and state.last_result and state.last_result.get('status') == 'changed':
            # Editing can insert a preview and move the submit button. Refresh
            # layout before creating an unknown business write; decide again on
            # the next frame instead of dispatching this potentially stale click.
            refresh = 'scroll [down]'
            operations.register(operations.plan(refresh, frame, state), frame, state)
            return refresh, False
        typed = re.fullmatch(r"type \[(\d+)\] \[(.*)\] \[([01])\]", action, re.S)
        if typed and input_mode in {"append", "replace"}:
            # One primitive now; subsequent callbacks supply fresh IDs/observations.
            state.data["_input_sequence"] = {
                "field_key": plan.field_key, "url": frame.url,
                "text": typed.group(2), "enter": typed.group(3), "mode":input_mode,
                "phase": "end" if input_mode == "append" else "select",
            }
            if input_mode == "append":
                state.clear_replace()
            focus_action = f"click [{typed.group(1)}]"
            operations.register(operations.plan(focus_action, frame, state), frame, state)
            state.mark_activity()
            return focus_action, True
        if plan.kind == "stop":
            state.set_last_result("stop", "local effect checks passed", step=frame.step)
            return action, True
        operations.register(plan, frame, state, telemetry=self._telemetry)
        return action, True

    def _policy_decision(
        self,
        context: Context,
        state: TaskState,
        frame: Frame,
    ) -> dict[str, Any]:
        invalid_outputs: set[str] = set()
        corrections = 0
        raw = self.policy.generate(context, state)
        while True:
            try:
                decision = _parse_decision(raw, frame.as_observation(), context, state)
                selected, accepted = self._finalize(frame, state, decision["action"],
                                                     decision.get("input_mode", "replace"))
                if accepted and decision.get("memory") is not None:
                    state.memory = decision["memory"]
                return {"action": selected}
            except (ValueError, TypeError) as exc:
                if not isinstance(raw, str):
                    raise ValueError("Policy must return a string decision") from exc
                if raw in invalid_outputs or corrections >= MAX_DECISION_CORRECTIONS:
                    recovery_actions = (
                        "scroll [down]",
                        "scroll [up]",
                        "press [Escape]",
                        "press [Tab]",
                    )
                    index = state.next_recovery()
                    action = recovery_actions[index % len(recovery_actions)]
                    selected, _ = self._finalize(frame, state, action)
                    return {"action": selected}
                invalid_outputs.add(raw)
                corrections += 1
                raw = self.policy.correct(context, state, raw, exc)

    def _request_verification_screenshot(
        self,
        frame: Frame,
        state: TaskState,
        *,
        reason: str = "diagnostic",
    ) -> ScreenshotCapture | None:
        """Fetch one current-frame PNG only on an explicit diagnostic path."""
        if not frame.capabilities.screenshot:
            return None
        if self._verification_screenshot_done or state.screenshot_requested(frame.step):
            return None
        self._verification_screenshot_done = True
        state.mark_screenshot_attempt(frame.step)
        return self.request_screenshot(frame, state, reason=reason)

    def request_screenshot(
        self,
        frame: Frame,
        state: TaskState | dict[str, Any] | None = None,
        *,
        reason: str = "diagnostic",
        directory: str | None = None,
    ) -> ScreenshotCapture:
        """Explicitly fetch this frame's PNG, defaulting to no request at all."""
        task_state = (
            state if isinstance(state, TaskState)
            else TaskState({} if state is None else state)
        )
        effective_deadline = task_state.update_deadline(frame.deadline)
        if effective_deadline is not None and frame.deadline != effective_deadline:
            frame = replace(frame, deadline=effective_deadline)
        task_state.invalidate_screenshot(frame)
        if self.screenshot_port is None:
            task_state.set_screenshot_reference(None)
            return ScreenshotCapture(result="disabled", reference=frame.screenshot)
        capture = self.screenshot_port.capture(frame, reason=reason, directory=directory)
        task_state.set_screenshot_reference(capture.as_state())
        return capture

    def close(self) -> None:
        self._active_frame = None
        self._active_state = None
        self._verification_screenshot_done = False
        if self.policy is not None and hasattr(self.policy, "close"):
            self.policy.close()


def _parse_decision(
    raw: str,
    observation: Mapping[str, Any],
    context: Context,
    state: TaskState,
) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise ValueError("Decision output must be a string")
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
    result = json.loads(text)
    if (
        not isinstance(result, dict)
        or "action" not in result
        or set(result) - {"action", "memory", "input_mode"}
    ):
        raise ValueError("Return action and optional memory; put the ID inside the action string")
    action = validate_action(result["action"], observation)
    if (
        context.unchanged_count >= 2
        and context.repeated_action
        and context.last_action is not None
        and action == context.last_action
        and action.startswith(("click [", "type [", "hover ["))
    ):
        raise ValueError(
            "This exact action repeatedly had no visible effect. Scroll to reveal "
            "clipped controls, use a different visible control or keyboard navigation."
        )
    memory = None
    if "memory" in result:
        memory = result["memory"]
        if not isinstance(memory, str) or len(memory) > MAX_MEMORY:
            raise ValueError("Memory must be a string of at most 10000 characters")
    decision = {"action": action}
    if "input_mode" in result:
        if result["input_mode"] not in {"replace", "append"} or not action.startswith("type ["):
            raise ValueError("input_mode is replace or append and applies only to type")
        decision["input_mode"] = result["input_mode"]
    if memory is not None:
        decision["memory"] = memory
    return decision


def _unpack(proposal: str | Mapping[str, Any]) -> tuple[str, str | None]:
    if isinstance(proposal, str):
        return proposal, None
    if not isinstance(proposal, Mapping):
        raise ValueError("Decision must be an action string or an action object")
    extra = set(proposal) - {"action", "memory"}
    if extra:
        raise ValueError("Decision contains unsupported fields: " + ", ".join(sorted(extra)))
    action = proposal.get("action")
    memory = proposal.get("memory")
    if not isinstance(action, str):
        raise ValueError("Decision must contain a string action")
    if memory is not None and not isinstance(memory, str):
        raise ValueError("Decision memory must be a string")
    return action, memory


__all__ = [
    "DEADLINE_RESERVE_SECONDS",
    "MAX_DECISION_CORRECTIONS",
    "MAX_STALLED_STEPS",
    "MAX_TASK_STEPS",
    "DecisionPort",
    "Runtime",
]
