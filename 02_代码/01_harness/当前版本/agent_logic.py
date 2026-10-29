"""M0 compatibility entry; decisions now pass through the shared Runtime."""
from __future__ import annotations

from typing import Any

from web_agent import baseline
from web_agent.adapters import official
from web_agent.runtime import Runtime

SYSTEM = baseline.SYSTEM
model = baseline.model
validate_action = baseline.validate_action


def _default_runtime() -> Runtime:
    return Runtime(baseline.decide)


def decide(*, task, observation, history, action_history, state):
    """Keep the original signature while using the same frame/runtime path."""
    data = state.data if hasattr(state, "data") else state
    step = data.get("_step", 0) if isinstance(data, dict) else 0
    run_id = data.get("_run_id", "legacy") if isinstance(data, dict) else "legacy"
    request: dict[str, Any] = {
        "run_id": run_id,
        "task": task,
        "observation": observation,
        "history": history,
        "action_history": action_history,
        "step": step,
    }
    return _default_runtime().advance(official.frame_from_request(request, step=step), state)
