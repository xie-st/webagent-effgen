"""Compatibility entry; decisions now pass through the shared Runtime.

``decide`` keeps its original signature, but one mutable task state now owns a
whole cross-observation run: the unique run id, the step cursor and the run's
telemetry live in that state until a terminal action or an exception ends it.
A new state therefore starts a new run instead of appending calls to the
previous task's counters.
"""
from __future__ import annotations

from collections.abc import MutableMapping
import time
from typing import Any
from uuid import uuid4

from third_party_agent import model

from web_agent import actions, policy
from web_agent.adapters import official
from web_agent.model_port import SdkModelPort
from web_agent.runtime import Runtime
from web_agent.screenshots import ScreenshotPort
from web_agent.state import TaskState
from web_agent.telemetry import Telemetry

SYSTEM = policy.SYSTEM
validate_action = actions.validate_action


def _default_runtime(*, telemetry: Telemetry) -> Runtime:
    port = SdkModelPort(sdk=model, telemetry=telemetry)
    return Runtime(
        policy=policy.EffGenPolicy(model_port=port, telemetry=telemetry),
        screenshot_port=ScreenshotPort.from_env(telemetry=telemetry),
    )


def _state_data(state) -> MutableMapping[str, Any]:
    if isinstance(state, TaskState):
        return state.data
    if isinstance(state, MutableMapping):
        return state
    raise TypeError("state must be a TaskState or a mutable mapping")


def _run_id(data: MutableMapping[str, Any]) -> str:
    value = data.get("_run_id")
    if value is None:
        value = "legacy-" + uuid4().hex
        data["_run_id"] = value
    if not isinstance(value, str) or not value:
        raise ValueError("state run identity must be a non-empty string")
    return value


def _step_cursor(data: MutableMapping[str, Any]) -> int:
    value = data.get("_step", 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("state step cursor must be a non-negative integer")
    return value


def _execution_deadline(data: MutableMapping[str, Any]) -> float | None:
    """Fix the absolute deadline once per task state.

    The legacy caller stores only the remaining seconds measured before the
    model call.  Adding that value to the current clock on every observation
    would renew the task budget after each call, so the first finite value
    becomes the state's absolute deadline and later calls reuse it.  A new
    state still obtains a new deadline.
    """
    stored = data.get("_execution_deadline")
    if stored is not None:
        if not isinstance(stored, (int, float)):
            raise ValueError("state execution deadline must be a number or None")
        return float(stored)
    remaining = data.get("_remaining_seconds")
    if not isinstance(remaining, (int, float)):
        return None
    deadline = time.time() + float(remaining)
    data["_execution_deadline"] = deadline
    return deadline


def _telemetry_for(data: MutableMapping[str, Any], run_id: str, task, deadline) -> Telemetry:
    telemetry = data.get("_telemetry")
    if telemetry is None:
        telemetry = Telemetry.from_env(run_id)
        telemetry.run_start(task=str(task), deadline=deadline)
        data["_telemetry"] = telemetry
        return telemetry
    if not isinstance(telemetry, Telemetry):
        raise TypeError("state telemetry must be a Telemetry instance")
    if telemetry.run_id != run_id:
        raise ValueError("state run identity does not match its telemetry")
    if telemetry.is_finished:
        raise RuntimeError("task already ended; use a fresh state for a new run")
    return telemetry


def _is_stop(action: str) -> bool:
    return action.startswith("stop [")


def decide(*, task, observation, history, action_history, state):
    """Keep the original signature while using one run per task state.

    The first observation opens the run and gets step 0.  Ordinary decisions
    advance the state's step cursor without ending the run; only a ``stop``
    action or an exception writes ``run_end``.  Every model call in between
    remains part of the same run and the same cumulative call sequence.
    """
    data = _state_data(state)
    if data.get("_run_ended"):
        raise RuntimeError("task already ended; use a fresh state for a new run")

    step = _step_cursor(data)
    run_id = _run_id(data)
    remaining = data.get("_remaining_seconds")
    deadline = _execution_deadline(data)
    telemetry = _telemetry_for(data, run_id, task, deadline)
    request: dict[str, Any] = {
        "run_id": run_id,
        "task": task,
        "observation": observation,
        "history": history,
        "action_history": action_history,
        "step": step,
        "execution_deadline": deadline,
    }
    frame = official.frame_from_request(request, step=step)
    memory_before = data.get("memory")
    runtime: Runtime | None = None
    try:
        telemetry.observation(
            step=frame.step,
            url=frame.url,
            observation_version=frame.observation_version,
            previous_receipt=frame.previous_receipt,
            deadline=frame.deadline,
            remaining_seconds=remaining,
        )
        runtime = _default_runtime(telemetry=telemetry)
        result = runtime.advance(frame, state)
        action = (result if isinstance(result, str)
                  else result.get("action") if isinstance(result, dict) else None)
        if not isinstance(action, str) or not action.strip():
            raise ValueError('Runtime must return an action string or {"action": "..."}')
        action = action.strip()
        telemetry.action(
            step=frame.step,
            action=action,
            memory_changed=data.get("memory") != memory_before,
            previous_receipt=frame.previous_receipt,
        )
        if _is_stop(action):
            telemetry.finish("stop")
            data["_run_ended"] = True
            data["_end_reason"] = "stop"
        else:
            data["_step"] = frame.step + 1
        return {"action": action}
    except Exception as exc:
        telemetry.step_error(step=frame.step, error=exc)
        reason = (
            "deadline" if isinstance(exc, TimeoutError)
            else f"error:{type(exc).__name__}"
        )
        telemetry.finish(reason)
        data["_run_ended"] = True
        data["_end_reason"] = reason
        raise
    finally:
        if runtime is not None:
            runtime.close()


__all__ = ["SYSTEM", "decide", "model", "validate_action"]
