"""Official entry: map one request to a Frame and advance the M0 Runtime."""
from __future__ import annotations

import time
from typing import Any

from web_agent import baseline
from web_agent.adapters import official
from web_agent.runtime import Runtime


class MyAgent:
    def __init__(self, runtime: Runtime | None = None):
        self.runtime = runtime or Runtime(baseline.decide)
        self.run_id: str | None = None
        self.state: dict[str, Any] = {}
        self._step = 0

    def reset(self, request):
        self.run_id = request["run_id"]
        self.state = {}
        self._step = 0

    def step(self, request):
        if self.run_id is None:
            raise ValueError("reset is required")
        if request["run_id"] != self.run_id:
            raise ValueError("run_id mismatch; reset is required")
        deadline = request.get("execution_deadline")
        self.state["_remaining_seconds"] = max(0, deadline - time.time()) if deadline else None
        frame = official.frame_from_request(request, step=self._step)
        result = self.runtime.advance(frame, self.state)
        action = (result if isinstance(result, str)
                  else result.get("action") if isinstance(result, dict) else None)
        if not isinstance(action, str) or not action.strip():
            raise ValueError('Runtime must return an action string or {"action": "..."}')
        self._step += 1
        return {"action": action.strip()}

    def close(self):
        self.state = {}
        self.run_id = None
        self._step = 0
