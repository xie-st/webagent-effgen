"""Official WebArena request to Frame mapping; no browser capabilities assumed."""
from __future__ import annotations

from typing import Any, Mapping

from ..contracts import Capabilities, Frame, ScreenshotReference

OFFICIAL_CAPABILITIES = Capabilities(
    single_tab=True,
    native_pause=False,
    screenshot=False,
)

try:  # The upgraded client adds browser.py; an older bundled SDK has no module.
    from third_party_agent import browser as _sdk_browser
except ImportError:  # pragma: no cover - exercised by versions with the old SDK.
    _sdk_browser = None

SDK_SCREENSHOT_SUPPORTED = callable(getattr(_sdk_browser, "save_screenshot", None))


def _step(request: Mapping[str, Any], fallback: int) -> int:
    value = request.get("step", fallback)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def _screenshot_reference(
    observation: Mapping[str, Any],
    *,
    run_id: str,
    tab: int | str,
    observation_version: int | str,
    step: int,
    url: str,
) -> ScreenshotReference | None:
    """Treat malformed/partial metadata as absent so old text-only runs continue."""
    metadata = observation.get("screenshot")
    if metadata is None:
        return None
    try:
        reference = ScreenshotReference.from_metadata(
            metadata,
            run_id=run_id,
            tab=tab,
            observation_version=observation_version,
            url=url,
        )
        return reference if reference.step == step else None
    except (TypeError, ValueError):
        return None


def frame_from_request(request: Mapping[str, Any], step: int = 0) -> Frame:
    observation = request["observation"]
    if not isinstance(observation, Mapping):
        raise ValueError("observation must be an object")
    url = observation.get("url")
    ax = observation.get("text")
    if not isinstance(url, str) or not isinstance(ax, str):
        raise ValueError("observation must contain string url and text fields")

    frame_step = _step(request, step)
    run_id = str(request.get("run_id", ""))
    tab = observation.get("tab", request.get("tab", 0))
    observation_version = request.get(
        "observation_version", observation.get("version", frame_step)
    )
    previous_receipt = request.get("previous_receipt")
    if previous_receipt is None:
        previous_receipt = request.get("previous_action_result")
    if previous_receipt is None:
        previous_receipt = request.get("last_action_result")
    screenshot = _screenshot_reference(
        observation,
        run_id=run_id,
        tab=tab,
        observation_version=observation_version,
        step=frame_step,
        url=url,
    )
    capabilities = Capabilities(
        single_tab=True,
        native_pause=False,
        screenshot=SDK_SCREENSHOT_SUPPORTED and screenshot is not None,
    )

    return Frame(
        task=str(request.get("task", "")),
        run_id=run_id,
        step=frame_step,
        url=url,
        tab=tab,
        observation_version=observation_version,
        ax=ax,
        deadline=request.get("execution_deadline"),
        capabilities=capabilities,
        previous_receipt=previous_receipt,
        history=tuple(request.get("history", ())),
        action_history=tuple(request.get("action_history", ())),
        screenshot=screenshot,
    )
