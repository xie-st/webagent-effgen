"""M0 data contracts shared by the public adapter, runtime and observers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Capabilities:
    """Platform features the current adapter can actually rely on."""

    single_tab: bool
    native_pause: bool
    screenshot: bool


@dataclass(frozen=True)
class Frame:
    """One official observation translated into the runtime's input shape."""

    task: str
    run_id: str
    step: int
    url: str
    tab: int | str
    observation_version: int | str
    ax: str
    deadline: float | None
    capabilities: Capabilities
    previous_receipt: Mapping[str, Any] | None = None
    history: tuple[Mapping[str, Any], ...] = ()
    action_history: tuple[str, ...] = ()

    def as_observation(self) -> dict[str, Any]:
        return {"type": "accessibility_tree", "url": self.url, "text": self.ax}


@dataclass(frozen=True)
class Context:
    """Current page plus only the history needed for one decision."""

    task: str
    run_id: str
    step: int
    url: str
    tab: int | str
    observation_version: int | str
    page: str
    current_ids: tuple[str, ...]
    past_views: tuple[Mapping[str, Any], ...]
    recent_actions: tuple[str, ...]
    memory: str
    recovery_feedback: str
    remaining_seconds: float | None
    capabilities: Capabilities
    previous_receipt: Mapping[str, Any] | None
    unchanged_count: int
    repeated_action: bool
    last_action: str | None
