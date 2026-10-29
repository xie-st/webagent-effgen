"""Official WebArena request to Frame mapping; no browser capabilities assumed."""
from __future__ import annotations

from typing import Any, Mapping

from ..contracts import Capabilities, Frame

OFFICIAL_CAPABILITIES = Capabilities(
    single_tab=True,
    native_pause=False,
    screenshot=False,
)


def _step(request: Mapping[str, Any], fallback: int) -> int:
    value = request.get("step", fallback)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def frame_from_request(request: Mapping[str, Any], step: int = 0) -> Frame:
    observation = request["observation"]
    if not isinstance(observation, Mapping):
        raise ValueError("observation must be an object")
    url = observation.get("url")
    ax = observation.get("text")
    if not isinstance(url, str) or not isinstance(ax, str):
        raise ValueError("observation must contain string url and text fields")

    frame_step = _step(request, step)
    observation_version = request.get(
        "observation_version", observation.get("version", frame_step)
    )
    previous_receipt = request.get("previous_receipt")
    if previous_receipt is None:
        previous_receipt = request.get("previous_action_result")
    if previous_receipt is None:
        previous_receipt = request.get("last_action_result")

    return Frame(
        task=str(request.get("task", "")),
        run_id=str(request.get("run_id", "")),
        step=frame_step,
        url=url,
        tab=observation.get("tab", request.get("tab", 0)),
        observation_version=observation_version,
        ax=ax,
        deadline=request.get("execution_deadline"),
        capabilities=OFFICIAL_CAPABILITIES,
        previous_receipt=previous_receipt,
        history=tuple(request.get("history", ())),
        action_history=tuple(request.get("action_history", ())),
    )
