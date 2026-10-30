"""One-decision runtime with M2 effect registration, verification and recovery.

The runtime owns ordering: extract goals from the original task, resolve any
previous per-tab pending write against the new observation, assemble context,
obtain exactly one decision, validate it, apply the read-only write guard,
verify a success stop, register the new pending effect, then merge memory.
All model traffic still goes through the injected policy/ModelPort.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any

from . import observe, recover, verify
from .actions import validate_action
from .contracts import Context, Frame
from .screenshots import ScreenshotCapture, ScreenshotPort
from .state import MAX_MEMORY, TaskState

DecisionPort = Callable[[Context, TaskState], str | Mapping[str, Any]]


class Runtime:
    """Drive either a legacy decision port or an EffGen raw-decision policy."""

    def __init__(
        self,
        decision_port: DecisionPort | None = None,
        *,
        policy=None,
        screenshot_port: ScreenshotPort | None = None,
        telemetry=None,
    ):
        if (decision_port is None) == (policy is None):
            raise ValueError("Provide exactly one of decision_port or policy")
        if decision_port is not None and not callable(decision_port):
            raise TypeError("decision_port must be callable")
        self.decision_port = decision_port
        self.policy = policy
        self.screenshot_port = screenshot_port
        self._telemetry = telemetry or getattr(policy, "telemetry", None)

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
        task_state.update_deadline(frame.deadline)
        task_state.invalidate_screenshot(frame)
        task_state.observe_identity(frame)
        verify.ensure_goals(frame, task_state, telemetry=self._telemetry)
        self._active_frame = frame
        self._active_state = task_state
        self._verification_screenshot_done = False
        if screenshot_reason is not None:
            # Explicit demand only: ordinary decisions keep the text-only path
            # and never download a PNG.
            self.request_screenshot(frame, task_state, reason=screenshot_reason)
        try:
            pending = task_state.pending_for(frame.tab)
            if pending is not None and pending.step < frame.step:
                verify.resolve_pending(
                    frame,
                    task_state,
                    semantic_verify=self._semantic_verify,
                    telemetry=self._telemetry,
                    screenshot_request=lambda: self._request_verification_screenshot(
                        frame, task_state
                    ),
                )
            context = observe.build_context(frame, task_state)
            if self.policy is None:
                proposal = self.decision_port(context, task_state)
                action, memory = _unpack(proposal)
                action = validate_action(action, frame.as_observation())
                if memory is not None and len(memory) > MAX_MEMORY:
                    raise ValueError("Memory must be a string of at most 10000 characters")
                self._accept_action(frame, task_state, action)
                decision = {"action": action}
                if memory is not None:
                    decision["memory"] = memory
            else:
                decision = self._policy_decision(context, task_state, frame)
            memory = decision.get("memory")
            if memory is not None:
                task_state.memory = memory
            return {"action": decision["action"]}
        except Exception:
            # AX failure/diagnostic only; this never turns an image into success
            # and never delays the final response with a background download.
            try:
                self._request_verification_screenshot(frame, task_state, reason="diagnostic")
            except Exception:
                pass
            raise
        finally:
            self._active_frame = None
            self._active_state = None

    def _accept_action(self, frame: Frame, state: TaskState, action: str) -> None:
        recover.guard_action(frame, state, action, telemetry=self._telemetry)
        if action.startswith("stop ["):
            verify.assert_stop(
                frame,
                state,
                semantic_verify=self._semantic_verify,
                telemetry=self._telemetry,
                screenshot_request=lambda: self._request_verification_screenshot(
                    frame, state, reason="verify"
                ),
            )
        recover.register_action(frame, state, action, telemetry=self._telemetry)

    def _policy_decision(
        self,
        context: Context,
        state: TaskState,
        frame: Frame,
    ) -> dict[str, str]:
        invalid_outputs: set[str] = set()
        raw = self.policy.generate(context, state)
        while True:
            try:
                decision = _parse_decision(raw, frame.as_observation(), context, state)
                self._accept_action(frame, state, decision["action"])
                return decision
            except (ValueError, TypeError) as exc:
                if not isinstance(raw, str):
                    raise ValueError("Policy must return a string decision") from exc
                if raw in invalid_outputs:
                    recovery_actions = (
                        "scroll [down]",
                        "scroll [up]",
                        "press [Escape]",
                        "press [Tab]",
                    )
                    index = state.next_recovery()
                    return {"action": recovery_actions[index % len(recovery_actions)]}
                invalid_outputs.add(raw)
                raw = self.policy.correct(context, state, raw, exc)

    def _semantic_verify(
        self,
        frame: Frame,
        state: TaskState,
        mode: str,
    ) -> dict[str, Any] | None:
        if self.policy is None or not hasattr(self.policy, "verify"):
            return None
        context = observe.build_context(frame, state)
        payload = verify.build_verify_payload(frame, state, mode=mode)
        raw = self.policy.verify(context, state, payload)
        return verify.parse_verification(raw, frame, state, mode=mode)

    def _request_verification_screenshot(
        self,
        frame: Frame,
        state: TaskState,
        *,
        reason: str = "verify",
    ) -> ScreenshotCapture | None:
        """Fetch one current-frame PNG only when AX verification is inconclusive."""
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
        """Explicitly fetch this frame's PNG, defaulting to no request at all.

        A failure other than the absolute deadline returns a failed capture and
        leaves the normal AX decision path intact.  Only verified metadata/path
        references enter TaskState.
        """
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
        capture = self.screenshot_port.capture(
            frame,
            reason=reason,
            directory=directory,
        )
        task_state.set_screenshot_reference(capture.as_state())
        return capture

    def close(self) -> None:
        if self.policy is not None and hasattr(self.policy, "close"):
            self.policy.close()


def _parse_decision(
    raw: str,
    observation: Mapping[str, Any],
    context: Context,
    state: TaskState,
) -> dict[str, str]:
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
        or set(result) - {"action", "memory"}
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


__all__ = ["DecisionPort", "Runtime"]
