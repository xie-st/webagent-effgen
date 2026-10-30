"""One-decision runtime: context assembly, policy parsing, validation and merge.

EffGen only produces raw model text.  This module owns JSON extraction, action
validation, correction requests and the repeated-invalid fallback, so no
framework-side parser can turn a malformed answer into a webpage action.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from . import observe
from .actions import validate_action
from .contracts import Context, Frame
from .state import MAX_MEMORY, TaskState

DecisionPort = Callable[[Context, TaskState], str | Mapping[str, Any]]


class Runtime:
    """Drive either a legacy decision port or an EffGen raw-decision policy."""

    def __init__(
        self,
        decision_port: DecisionPort | None = None,
        *,
        policy=None,
    ):
        if (decision_port is None) == (policy is None):
            raise ValueError("Provide exactly one of decision_port or policy")
        if decision_port is not None and not callable(decision_port):
            raise TypeError("decision_port must be callable")
        self.decision_port = decision_port
        self.policy = policy

    def advance(self, frame: Frame, state: TaskState | dict[str, Any]) -> dict[str, str]:
        task_state = state if isinstance(state, TaskState) else TaskState(state)
        task_state.update_deadline(frame.deadline)
        context = observe.build_context(frame, task_state)
        if self.policy is None:
            proposal = self.decision_port(context, task_state)
        else:
            proposal = self._policy_proposal(context, task_state, frame.as_observation())
        action, memory = _unpack(proposal)
        action = validate_action(action, frame.as_observation())
        if memory is not None:
            task_state.memory = memory
        return {"action": action}

    def _policy_proposal(
        self,
        context: Context,
        state: TaskState,
        observation: Mapping[str, Any],
    ) -> dict[str, str]:
        invalid_outputs: set[str] = set()
        raw = self.policy.generate(context, state)
        while True:
            try:
                return _parse_decision(raw, observation, context, state)
            except (ValueError, TypeError) as exc:
                if not isinstance(raw, str):
                    raise ValueError("Policy must return a string decision") from exc
                if raw in invalid_outputs:
                    # A deterministic model can repeat the same stale ID forever.
                    # Return a fresh observation instead of spending the entire
                    # lease correcting an unchanged answer.
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
