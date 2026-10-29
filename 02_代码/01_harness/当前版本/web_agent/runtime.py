"""One-decision runtime that owns context assembly, validation and state merge."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from . import observe
from .baseline import validate_action
from .contracts import Context, Frame
from .state import TaskState

DecisionPort = Callable[[Context, TaskState], str | Mapping[str, Any]]


class Runtime:
    """Drive one injected decision port and return one validated official action."""

    def __init__(self, decision_port: DecisionPort):
        if not callable(decision_port):
            raise TypeError("decision_port must be callable")
        self.decision_port = decision_port

    def advance(self, frame: Frame, state: TaskState | dict[str, Any]) -> dict[str, str]:
        task_state = state if isinstance(state, TaskState) else TaskState(state)
        task_state.update_deadline(frame.deadline)
        context = observe.build_context(frame, task_state)
        proposal = self.decision_port(context, task_state)
        action, memory = _unpack(proposal)
        action = validate_action(action, frame.as_observation())
        if memory is not None:
            task_state.memory = memory
        return {"action": action}


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
