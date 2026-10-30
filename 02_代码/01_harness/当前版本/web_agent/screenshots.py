"""On-demand viewport screenshot evidence for one current observation.

The screenshot helper is called synchronously from the still-active SDK task
callback.  Nothing here starts a background download, and image bytes never
leave this module: callers receive a path and verified metadata, while model
messages stay text-only.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import time
from dataclasses import dataclass, replace
from typing import Any, Mapping

from .contracts import (
    Frame,
    SCREENSHOT_MAX_BYTES,
    SCREENSHOT_MAX_PIXELS,
    SCREENSHOT_MAX_SIDE,
    ScreenshotReference,
)
from .telemetry import Telemetry

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_OK_RESULTS = frozenset({"saved", "cached"})


@dataclass(frozen=True)
class ScreenshotCapture:
    """Outcome of one explicit screenshot request."""

    result: str
    reference: ScreenshotReference | None
    path: str | None = None
    cached: bool = False
    requested: bool = True
    byte_size: int | None = None
    sha256: str | None = None
    width: int | None = None
    height: int | None = None
    duration_ms: float = 0.0
    error: str | None = None
    http_status: int | None = None

    @property
    def ok(self) -> bool:
        return self.result in _OK_RESULTS

    def as_state(self) -> dict[str, Any] | None:
        """Reference-only state record; deliberately excludes image bytes."""
        if not self.ok or self.reference is None:
            return None
        value = self.reference.as_dict()
        value["path"] = self.path
        return value


def _http_status(error: BaseException) -> int | None:
    code = getattr(error, "code", None)
    if type(code) is int:
        return code
    match = re.search(r"HTTP (\d{3})", str(error))
    return int(match.group(1)) if match else None


def _binding_mismatches(reference: ScreenshotReference, frame: Frame) -> list[str]:
    expected = {
        "run_id": frame.run_id,
        "tab": frame.tab,
        "observation_version": frame.observation_version,
        "step": frame.step,
        "url": frame.url,
    }
    return [
        name for name, value in expected.items()
        if getattr(reference, name) != value
    ]


def _validate_reference(reference: ScreenshotReference) -> None:
    """Reapply the metadata contract to a manually constructed reference."""
    ScreenshotReference.from_metadata(
        reference.as_dict(),
        run_id=reference.run_id,
        tab=reference.tab,
        observation_version=reference.observation_version,
        url=reference.url,
    )


def _verify_file(path: Path, reference: ScreenshotReference) -> str | None:
    """Check the saved PNG and return an error string, or None when valid."""
    try:
        raw = path.read_bytes()
    except OSError:
        return "saved screenshot is not readable"
    if len(raw) != reference.byte_size:
        return "saved screenshot byte_size does not match metadata"
    if len(raw) > SCREENSHOT_MAX_BYTES:
        return "saved screenshot exceeds the platform byte limit"
    if hashlib.sha256(raw).hexdigest() != reference.sha256:
        return "saved screenshot sha256 does not match metadata"
    if len(raw) < 24 or raw[:8] != PNG_SIGNATURE or raw[12:16] != b"IHDR":
        return "saved screenshot is not a PNG with an IHDR header"
    try:
        width, height = struct.unpack(">II", raw[16:24])
    except struct.error:
        return "saved screenshot has an incomplete IHDR header"
    if (width, height) != (reference.width, reference.height):
        return "saved screenshot dimensions do not match metadata"
    if width > SCREENSHOT_MAX_SIDE or height > SCREENSHOT_MAX_SIDE:
        return "saved screenshot side exceeds the platform limit"
    if width * height > SCREENSHOT_MAX_PIXELS:
        return "saved screenshot pixel count exceeds the platform limit"
    return None


class ScreenshotPort:
    """Synchronous on-demand port over ``third_party_agent.browser``.

    The port caches only successful captures, keyed by run/tab/observation/
    URL/image/step.  A different frame never receives the previous frame's
    path.  Metadata/HTTP/validation failures return a failed result so the
    caller can continue with the accessibility tree.
    """

    def __init__(
        self,
        *,
        browser=None,
        directory: str | Path | None = None,
        telemetry: Telemetry | None = None,
        clock=time.time,
    ) -> None:
        self._browser = browser
        self.directory = Path(directory).expanduser().resolve() if directory else None
        self.telemetry = telemetry
        self._clock = clock
        self._cache: dict[tuple[Any, ...], ScreenshotCapture] = {}

    @classmethod
    def from_env(
        cls,
        *,
        browser=None,
        telemetry: Telemetry | None = None,
        clock=time.time,
    ) -> "ScreenshotPort":
        """Use the current run's Git-ignored ``raw/screenshots`` directory."""
        run_dir = os.environ.get("WEBAGENT_RUN_DIR")
        directory = Path(run_dir) / "raw" / "screenshots" if run_dir else None
        return cls(browser=browser, directory=directory, telemetry=telemetry, clock=clock)

    def _browser_module(self):
        if self._browser is not None:
            return self._browser
        try:
            from third_party_agent import browser
        except ImportError:
            return None
        return browser

    def _emit(
        self,
        *,
        frame: Frame,
        reference: ScreenshotReference | None,
        result: str,
        started: float,
        path: str | None = None,
        cached: bool = False,
        error: BaseException | str | None = None,
        http_status: int | None = None,
        byte_size: int | None = None,
        sha256: str | None = None,
        width: int | None = None,
        height: int | None = None,
        reason: str = "diagnostic",
    ) -> None:
        if self.telemetry is None:
            return
        error_type = type(error).__name__ if isinstance(error, BaseException) else None
        error_text = str(error)[:1000] if error is not None else None
        self.telemetry.screenshot(
            step=frame.step,
            url=frame.url,
            observation_version=frame.observation_version,
            run_id=frame.run_id,
            image_id=reference.image_id if reference is not None else None,
            reason=reason,
            result=result,
            requested=True,
            cache_hit=cached,
            duration_ms=round((self._clock() - started) * 1000.0, 3),
            byte_size=byte_size,
            sha256=sha256,
            width=width,
            height=height,
            path=path,
            http_status=http_status,
            error_type=error_type,
            error=error_text,
        )

    def _capture(
        self,
        *,
        frame: Frame,
        reference: ScreenshotReference,
        reason: str,
        directory: Path | None,
    ) -> ScreenshotCapture:
        started = self._clock()
        key = reference.binding()
        cached = self._cache.get(key)
        if cached is not None and directory is not None:
            try:
                source = Path(cached.path)
                problem = _verify_file(source, reference)
                if problem is not None:
                    raise ValueError(problem)
                target = directory / (reference.image_id + ".png")
                if source.resolve() != target.resolve():
                    directory.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                if frame.deadline is not None and self._clock() >= frame.deadline:
                    raise TimeoutError("Task deadline reached while restoring cached screenshot")
                cached = replace(cached, path=str(target))
                self._cache[key] = cached
            except (OSError, ValueError) as exc:
                if isinstance(exc, TimeoutError):
                    self._emit(frame=frame, reference=reference, result="timeout",
                               started=started, error=exc, reason=reason)
                    raise
                result = ScreenshotCapture(result="invalid", reference=reference,
                                           error=str(exc))
                self._emit(frame=frame, reference=reference, result=result.result,
                           started=started, error=exc, reason=reason)
                return result
            result = replace(cached, result="cached", cached=True, requested=True)
            self._emit(
                frame=frame,
                reference=reference,
                result=result.result,
                started=started,
                path=result.path,
                cached=True,
                byte_size=result.byte_size,
                sha256=result.sha256,
                width=result.width,
                height=result.height,
                reason=reason,
            )
            return result

        if directory is None:
            result = ScreenshotCapture(
                result="no_directory", reference=reference, requested=True,
                duration_ms=0.0,
            )
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, reason=reason)
            return result
        browser = self._browser_module()
        if browser is None or not callable(getattr(browser, "save_screenshot", None)):
            result = ScreenshotCapture(
                result="sdk_unavailable", reference=reference, requested=True,
                duration_ms=0.0,
            )
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, reason=reason)
            return result

        observation = frame.screenshot_observation()
        if observation is None:  # defensive; reference and frame agree by contract
            result = ScreenshotCapture(result="no_reference", reference=reference)
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, reason=reason)
            return result

        try:
            saved = browser.save_screenshot(observation, str(directory))
        except TimeoutError as exc:
            self._emit(frame=frame, reference=reference, result="timeout",
                       started=started, error=exc, reason=reason)
            raise
        except Exception as exc:
            if frame.deadline is not None and self._clock() >= frame.deadline:
                error = TimeoutError("Task execution deadline reached during screenshot request")
                self._emit(frame=frame, reference=reference, result="timeout",
                           started=started, error=error, reason=reason)
                raise error from exc
            status = _http_status(exc)
            result_name = f"http_{status}" if status in (404, 409) else (
                "invalid" if isinstance(exc, ValueError) else "unavailable"
            )
            result = ScreenshotCapture(
                result=result_name,
                reference=reference,
                requested=True,
                duration_ms=round((self._clock() - started) * 1000.0, 3),
                error=str(exc)[:1000],
                http_status=status,
            )
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, error=exc, http_status=status, reason=reason)
            return result

        if saved is None:
            result = ScreenshotCapture(
                result="unavailable", reference=reference, requested=True,
                duration_ms=round((self._clock() - started) * 1000.0, 3),
                error="SDK returned no screenshot for this observation",
            )
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, error=result.error, reason=reason)
            return result

        path = Path(saved)
        try:
            inside = path.resolve().is_relative_to(directory.resolve())
        except (OSError, ValueError):
            inside = False
        problem = None if inside else "saved screenshot is outside the run directory"
        if problem is None:
            problem = _verify_file(path, reference)
        if problem is not None:
            if inside:
                try:
                    path.unlink()
                except OSError:
                    pass
            result = ScreenshotCapture(
                result="invalid",
                reference=reference,
                requested=True,
                duration_ms=round((self._clock() - started) * 1000.0, 3),
                error=problem,
            )
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, error=problem, reason=reason)
            return result

        if frame.deadline is not None and self._clock() >= frame.deadline:
            error = TimeoutError("Task execution deadline reached during screenshot processing")
            self._emit(frame=frame, reference=reference, result="timeout",
                       started=started, error=error, reason=reason)
            raise error

        result = ScreenshotCapture(
            result="saved",
            reference=reference,
            path=str(path),
            requested=True,
            byte_size=reference.byte_size,
            sha256=reference.sha256,
            width=reference.width,
            height=reference.height,
            duration_ms=round((self._clock() - started) * 1000.0, 3),
        )
        self._cache[key] = result
        self._emit(frame=frame, reference=reference, result=result.result,
                   started=started, path=result.path, byte_size=result.byte_size,
                   sha256=result.sha256, width=result.width, height=result.height,
                   reason=reason)
        return result

    def capture(
        self,
        frame: Frame,
        *,
        reason: str = "diagnostic",
        directory: str | Path | None = None,
    ) -> ScreenshotCapture:
        """Request the current frame's PNG; failures never raise except deadline."""
        started = self._clock()
        reference = frame.screenshot
        if reference is None:
            result = ScreenshotCapture(result="no_reference", reference=None)
            self._emit(frame=frame, reference=None, result=result.result,
                       started=started, reason=reason)
            return result
        mismatches = _binding_mismatches(reference, frame)
        if mismatches:
            result = ScreenshotCapture(
                result="binding_mismatch",
                reference=reference,
                error="reference is not bound to this observation: "
                      + ", ".join(mismatches),
            )
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, error=result.error, reason=reason)
            return result
        try:
            _validate_reference(reference)
        except (TypeError, ValueError) as exc:
            result = ScreenshotCapture(
                result="invalid_metadata",
                reference=reference,
                error=str(exc)[:1000],
            )
            self._emit(frame=frame, reference=reference, result=result.result,
                       started=started, error=exc, reason=reason)
            return result
        if frame.deadline is not None and self._clock() >= frame.deadline:
            # No usable budget remains; this is not an AX fallback case.
            error = TimeoutError("Task execution deadline reached before screenshot request")
            self._emit(frame=frame, reference=reference, result="timeout",
                       started=started, error=error, reason=reason)
            raise error
        selected = Path(directory).expanduser().resolve() if directory is not None else self.directory
        return self._capture(
            frame=frame,
            reference=reference,
            reason=reason,
            directory=selected,
        )


__all__ = ["ScreenshotCapture", "ScreenshotPort"]
