"""Official entry: map one request to a Frame and advance the M1a Runtime."""
from __future__ import annotations

import time
from typing import Any

from web_agent.adapters import official
from web_agent.model_port import SdkModelPort
from web_agent.policy import EffGenPolicy
from web_agent.runtime import Runtime
from web_agent.screenshots import ScreenshotPort
from web_agent.telemetry import Telemetry


class MyAgent:
    def __init__(
        self,
        runtime: Runtime | None = None,
        *,
        model_port: SdkModelPort | None = None,
        telemetry: Telemetry | None = None,
        screenshot_port: ScreenshotPort | None = None,
    ):
        self._fixed_runtime = runtime
        self._model_port = model_port
        self._injected_telemetry = telemetry
        self._screenshot_port = screenshot_port
        self.runtime = runtime
        self.run_id: str | None = None
        self.state: dict[str, Any] = {}
        self._step = 0
        self._telemetry: Telemetry | None = None
        self._owned_runtime = False
        self._last_error: BaseException | None = None
        self._last_action: str | None = None
        self._last_frame = None
        self._stopped = False

    def reset(self, request):
        if self.run_id is not None or self._telemetry is not None:
            self._end_run("reset")
        self.run_id = request["run_id"]
        self.state = {}
        self._step = 0
        self._last_error = None
        self._last_action = None
        self._last_frame = None
        self._stopped = False

        if (
            self._injected_telemetry is not None
            and not self._injected_telemetry.is_finished
        ):
            self._telemetry = self._injected_telemetry
            self._telemetry.bind_run(self.run_id)
        elif self._injected_telemetry is not None:
            self._telemetry = Telemetry(
                run_id=self.run_id, path=self._injected_telemetry.path
            )
        else:
            self._telemetry = Telemetry.from_env(self.run_id)
        if self._model_port is not None:
            # The caller may inject one port for several runs.  Rebind it to
            # the telemetry allocated for this run before any SDK call starts.
            self._model_port.bind_telemetry(self._telemetry)
        deadline = request.get("execution_deadline")
        self._telemetry.run_start(task=str(request.get("task", "")), deadline=deadline)

        if self._fixed_runtime is not None:
            self.runtime = self._fixed_runtime
            self._owned_runtime = False
        else:
            port = self._model_port or SdkModelPort(telemetry=self._telemetry)
            policy = EffGenPolicy(model_port=port, telemetry=self._telemetry)
            screenshot_port = self._screenshot_port or ScreenshotPort.from_env(
                telemetry=self._telemetry
            )
            self.runtime = Runtime(
                policy=policy,
                screenshot_port=screenshot_port,
                telemetry=self._telemetry,
            )
            self._owned_runtime = True

    def step(self, request):
        if self.run_id is None:
            raise ValueError("reset is required")
        if self._stopped:
            raise ValueError("run already ended with stop")
        if request["run_id"] != self.run_id:
            raise ValueError("run_id mismatch; reset is required")
        deadline = request.get("execution_deadline")
        self.state["_remaining_seconds"] = max(0, deadline - time.time()) if deadline else None
        frame = official.frame_from_request(request, step=self._step)
        self._last_frame = frame
        if self._telemetry is not None:
            self._telemetry.observation(
                step=frame.step,
                url=frame.url,
                observation_version=frame.observation_version,
                previous_receipt=frame.previous_receipt,
                deadline=frame.deadline,
                remaining_seconds=self.state["_remaining_seconds"],
            )
        memory_before = self.state.get("memory")
        try:
            result = self.runtime.advance(frame, self.state)
            action = (result if isinstance(result, str)
                      else result.get("action") if isinstance(result, dict) else None)
            if not isinstance(action, str) or not action.strip():
                raise ValueError('Runtime must return an action string or {"action": "..."}')
        except Exception as exc:
            self._last_error = exc
            if self._telemetry is not None:
                self._telemetry.step_error(step=frame.step, error=exc)
            raise
        action = action.strip()
        self._last_action = action
        if self._telemetry is not None:
            self._telemetry.action(
                step=frame.step,
                action=action,
                memory_changed=self.state.get("memory") != memory_before,
                previous_receipt=frame.previous_receipt,
            )
            if action.startswith("stop ["):
                # A stop is terminal; record its reason before the SDK close
                # arrives so a killed or disconnected client still has it.
                self._telemetry.finish("stop")
                self._stopped = True
        self._step = frame.step + 1
        return {"action": action}

    def request_screenshot(
        self,
        *,
        reason: str = "diagnostic",
        frame=None,
        directory: str | None = None,
    ):
        """Explicit current-frame screenshot request; ordinary steps never call it."""
        if self.runtime is None:
            raise ValueError("reset is required")
        target = frame if frame is not None else self._last_frame
        if target is None:
            raise ValueError("no current observation is available")
        if not hasattr(self.runtime, "request_screenshot"):
            raise TypeError("runtime does not expose a screenshot port")
        return self.runtime.request_screenshot(
            target,
            self.state,
            reason=reason,
            directory=directory,
        )

    def close(self):
        self._end_run("close")

    def _end_run(self, reason: str) -> None:
        active_reason = reason
        if self._last_error is not None:
            active_reason = (
                "deadline"
                if isinstance(self._last_error, TimeoutError)
                else f"error:{type(self._last_error).__name__}"
            )
        elif self._last_action is not None and self._last_action.startswith("stop ["):
            active_reason = "stop"
        if self._owned_runtime and self.runtime is not None:
            try:
                self.runtime.close()
            finally:
                self._owned_runtime = False
        if self._telemetry is not None:
            self._telemetry.finish(active_reason)
        self._telemetry = None
        self.runtime = self._fixed_runtime
        self.state = {}
        self.run_id = None
        self._step = 0
        self._last_error = None
        self._last_action = None
        self._last_frame = None
        self._stopped = False


__all__ = ["MyAgent"]
