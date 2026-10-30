"""M0 data contracts shared by the public adapter, runtime and observers."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

SCREENSHOT_MIME = "image/png"
SCREENSHOT_MAX_BYTES = 4 * 1024 * 1024
SCREENSHOT_MAX_SIDE = 4096
SCREENSHOT_MAX_PIXELS = 4_194_304
_IMAGE_ID = re.compile(r"[0-9a-f]{32}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class Capabilities:
    """Platform features the current adapter can actually rely on."""

    single_tab: bool
    native_pause: bool
    screenshot: bool


@dataclass(frozen=True)
class ScreenshotReference:
    """Verified-or-requestable viewport PNG metadata for one observation.

    The reference carries only platform metadata and the binding needed to
    reject stale evidence.  Image bytes never enter a Frame, Context, model
    message or TaskState.
    """

    image_id: str
    mime_type: str
    width: int
    height: int
    byte_size: int
    sha256: str
    step: int
    run_id: str
    tab: int | str
    observation_version: int | str
    url: str

    @classmethod
    def from_metadata(
        cls,
        metadata: Mapping[str, Any],
        *,
        run_id: str,
        tab: int | str,
        observation_version: int | str,
        url: str,
    ) -> "ScreenshotReference":
        """Parse one optional observation.screenshot value strictly.

        Callers that must keep old servers running catch the error and treat the
        frame as text-only.  A screenshot object with missing or malformed
        fields is not promoted to a usable reference.
        """
        if not isinstance(metadata, Mapping):
            raise ValueError("screenshot metadata must be an object")
        image_id = metadata.get("image_id")
        mime_type = metadata.get("mime_type")
        width = metadata.get("width")
        height = metadata.get("height")
        byte_size = metadata.get("byte_size")
        digest = metadata.get("sha256")
        step = metadata.get("step")
        if not isinstance(image_id, str) or not _IMAGE_ID.fullmatch(image_id):
            raise ValueError("screenshot image_id must be 32 lowercase hex characters")
        if mime_type != SCREENSHOT_MIME:
            raise ValueError("screenshot mime_type must be image/png")
        if type(width) is not int or type(height) is not int:
            raise ValueError("screenshot width and height must be integers")
        if not (0 < width <= SCREENSHOT_MAX_SIDE and 0 < height <= SCREENSHOT_MAX_SIDE):
            raise ValueError("screenshot dimensions exceed the platform limit")
        if width * height > SCREENSHOT_MAX_PIXELS:
            raise ValueError("screenshot pixel count exceeds the platform limit")
        if type(byte_size) is not int or not (24 <= byte_size <= SCREENSHOT_MAX_BYTES):
            raise ValueError("screenshot byte_size is outside the platform limit")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("screenshot sha256 must be 64 lowercase hex characters")
        if type(step) is not int or step < 0:
            raise ValueError("screenshot step must be a non-negative integer")
        if not isinstance(run_id, str):
            raise ValueError("screenshot run binding must be a string")
        if not isinstance(url, str):
            raise ValueError("screenshot URL binding must be a string")
        if tab is None or observation_version is None:
            raise ValueError("screenshot tab and observation binding must be present")
        return cls(
            image_id=image_id,
            mime_type=mime_type,
            width=width,
            height=height,
            byte_size=byte_size,
            sha256=digest,
            step=step,
            run_id=run_id,
            tab=tab,
            observation_version=observation_version,
            url=url,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "step": self.step,
            "run_id": self.run_id,
            "tab": self.tab,
            "observation_version": self.observation_version,
            "url": self.url,
        }

    def sdk_metadata(self) -> dict[str, Any]:
        """Only the fields ``browser.save_screenshot`` needs."""
        return {
            "image_id": self.image_id,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "step": self.step,
        }

    def binding(self) -> tuple[str, int | str, int | str, str, str, int]:
        return (
            self.run_id,
            self.tab,
            self.observation_version,
            self.url,
            self.image_id,
            self.step,
        )


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
    screenshot: ScreenshotReference | None = None

    def as_observation(self) -> dict[str, Any]:
        return {"type": "accessibility_tree", "url": self.url, "text": self.ax}

    def screenshot_observation(self) -> dict[str, Any] | None:
        """Observation shape accepted by the SDK screenshot helper."""
        if self.screenshot is None:
            return None
        return {
            "type": "accessibility_tree",
            "url": self.url,
            "text": self.ax,
            "screenshot": self.screenshot.sdk_metadata(),
        }


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
    deadline: float | None
    capabilities: Capabilities
    previous_receipt: Mapping[str, Any] | None
    unchanged_count: int
    repeated_action: bool
    last_action: str | None
    screenshot: ScreenshotReference | None = None
