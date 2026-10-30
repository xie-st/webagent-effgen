"""Append-only run telemetry shared by the harness and the SDK child process.

The official SDK runs every task in a spawned process.  The launcher therefore
publishes the result directory through ``WEBAGENT_RUN_DIR`` (or an explicit
``WEBAGENT_TELEMETRY_PATH``) before connecting, and this module resolves the
same file in the child.  Records are JSON Lines so a child can append without
rewriting state owned by the parent.

Only facts the platform actually returned are recorded.  Token counts and cost
stay ``null`` when unavailable; no local estimator is presented as usage.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_VERSION = 1
TELEMETRY_FILENAME = "telemetry.jsonl"
SUMMARY_FILENAME = "telemetry-summary.json"


def _iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(timespec="milliseconds")


def telemetry_path(run_id: str | None = None) -> Path:
    """Resolve the log destination without consulting project-specific globals."""
    explicit = os.environ.get("WEBAGENT_TELEMETRY_PATH")
    if explicit:
        return Path(explicit).expanduser().resolve()
    run_dir = os.environ.get("WEBAGENT_RUN_DIR")
    if run_dir:
        return (Path(run_dir).expanduser().resolve() / TELEMETRY_FILENAME)
    results = os.environ.get("WEBAGENT_RESULTS_ROOT")
    if results:
        name = run_id or "untracked"
        return (Path(results).expanduser().resolve() / "telemetry" / (name + ".jsonl"))
    name = run_id or "untracked"
    return (Path.cwd() / "results" / "telemetry" / (name + ".jsonl"))


class Telemetry:
    """One run's events and final counters.

    A new instance is created on ``reset``.  Appends are serialized in this
    process; each line is one complete event so an interrupted run still leaves
    the events it emitted.
    """

    def __init__(
        self,
        *,
        run_id: str | None = None,
        path: str | Path | None = None,
        clock=time.time,
    ) -> None:
        self.run_id = run_id
        self.path = Path(path).expanduser().resolve() if path is not None else telemetry_path(run_id)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self._lock = threading.Lock()
        self.started_at = _iso(clock())
        self._model_calls = 0
        self._rejected_calls = 0
        self._successful = 0
        self._failed = 0
        self._by_purpose: dict[str, int] = {}
        self._finished = False
        self.end_reason: str | None = None

    @classmethod
    def from_env(cls, run_id: str | None = None) -> "Telemetry":
        return cls(run_id=run_id)

    @property
    def is_finished(self) -> bool:
        return self._finished

    def bind_run(self, run_id: str) -> None:
        """Attach the current run when a telemetry object is injected."""
        self.run_id = run_id

    def _append(self, event: str, fields: Mapping[str, Any]) -> dict[str, Any]:
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "event": event,
            "run_id": self.run_id,
            "timestamp": _iso(self._clock()),
            "pid": os.getpid(),
        }
        record.update(fields)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str)
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(line + "\n")
        return record

    def run_start(self, *, task: str = "", deadline: float | None = None) -> None:
        self._append(
            "run_start",
            {
                "task": task,
                "deadline": deadline,
                "started_at": self.started_at,
                "python": sys.version,
            },
        )

    def observation(
        self,
        *,
        step: int,
        url: str,
        observation_version: int | str,
        previous_receipt: Mapping[str, Any] | None = None,
        deadline: float | None = None,
        remaining_seconds: float | None = None,
    ) -> None:
        self._append(
            "observation",
            {
                "step": step,
                "url": url,
                "observation_version": observation_version,
                "previous_receipt": previous_receipt,
                "deadline": deadline,
                "remaining_seconds": remaining_seconds,
            },
        )

    def model_call_start(
        self,
        *,
        purpose: str,
        call_id: str,
        started_at: float,
        run_id: str | None = None,
        step: int | None = None,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        """Record a call before the SDK is entered.

        The start record is what survives a hung or killed call.  ``call_seq``
        is assigned here because this is the point at which a real model
        attempt begins; a deadline pre-check never reaches this method.
        """
        with self._lock:
            self._model_calls += 1
            call_seq = self._model_calls
            self._by_purpose[purpose] = self._by_purpose.get(purpose, 0) + 1
        return self._append(
            "model_call_start",
            {
                "run_id": run_id or self.run_id,
                "step": step,
                "purpose": purpose,
                "call_id": call_id,
                "call_seq": call_seq,
                "request_id": None,
                "started_at": _iso(started_at),
                "ended_at": None,
                "duration_ms": None,
                "deadline": deadline,
                "sdk_invoked": True,
                "success": None,
                "error_type": None,
                "error": None,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
            },
        )

    def model_call_end(
        self,
        *,
        purpose: str,
        call_id: str,
        call_seq: int,
        request_id: str | None,
        started_at: float,
        ended_at: float,
        run_id: str | None = None,
        step: int | None = None,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self._successful += 1
        return self._append(
            "model_call_end",
            {
                "run_id": run_id or self.run_id,
                "step": step,
                "purpose": purpose,
                "call_id": call_id,
                "call_seq": call_seq,
                "request_id": request_id,
                "started_at": _iso(started_at),
                "ended_at": _iso(ended_at),
                "duration_ms": round((ended_at - started_at) * 1000.0, 3),
                "deadline": deadline,
                "sdk_invoked": True,
                "success": True,
                "error_type": None,
                "error": None,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
            },
        )

    def model_call_failed(
        self,
        *,
        purpose: str,
        call_id: str,
        call_seq: int,
        request_id: str | None,
        started_at: float,
        ended_at: float,
        error: BaseException,
        run_id: str | None = None,
        step: int | None = None,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self._failed += 1
        return self._append(
            "model_call_failed",
            {
                "run_id": run_id or self.run_id,
                "step": step,
                "purpose": purpose,
                "call_id": call_id,
                "call_seq": call_seq,
                "request_id": request_id,
                "started_at": _iso(started_at),
                "ended_at": _iso(ended_at),
                "duration_ms": round((ended_at - started_at) * 1000.0, 3),
                "deadline": deadline,
                "sdk_invoked": True,
                "success": False,
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
            },
        )

    def model_call_rejected(
        self,
        *,
        purpose: str,
        started_at: float,
        ended_at: float,
        error: BaseException,
        run_id: str | None = None,
        step: int | None = None,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        """Record a call refused before the SDK was invoked.

        This is deliberately not a model call: it has no ``call_seq`` and is
        not included in ``model_calls``/``by_purpose``.
        """
        with self._lock:
            self._rejected_calls += 1
        return self._append(
            "model_call_rejected",
            {
                "run_id": run_id or self.run_id,
                "step": step,
                "purpose": purpose,
                "call_id": None,
                "call_seq": None,
                "request_id": None,
                "started_at": _iso(started_at),
                "ended_at": _iso(ended_at),
                "duration_ms": round((ended_at - started_at) * 1000.0, 3),
                "deadline": deadline,
                "sdk_invoked": False,
                "success": False,
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
            },
        )

    def action(
        self,
        *,
        step: int,
        action: str,
        memory_changed: bool = False,
        previous_receipt: Mapping[str, Any] | None = None,
    ) -> None:
        self._append(
            "decision",
            {
                "step": step,
                "action": action,
                "memory_changed": memory_changed,
                "previous_receipt": previous_receipt,
            },
        )

    def step_error(self, *, step: int, error: BaseException) -> None:
        self._append(
            "step_error",
            {
                "step": step,
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
            },
        )

    def finish(self, reason: str) -> dict[str, Any]:
        """Write one summary event and a companion summary file.

        Repeated calls are idempotent so a reset path and an SDK close path can
        both ask for the same ending without duplicating the counters.
        """
        if self._finished:
            return self.summary()
        ended = self._clock()
        with self._lock:
            self._finished = True
            self.end_reason = reason
            summary = {
                "schema_version": SCHEMA_VERSION,
                "run_id": self.run_id,
                "started_at": self.started_at,
                "ended_at": _iso(ended),
                "end_reason": reason,
                "model_calls": self._model_calls,
                "rejected_calls": self._rejected_calls,
                "completed_calls": self._successful + self._failed,
                "incomplete_calls": max(
                    0, self._model_calls - self._successful - self._failed
                ),
                "by_purpose": dict(sorted(self._by_purpose.items())),
                "successful": self._successful,
                "failed": self._failed,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
            }
        self._append("run_end", {k: v for k, v in summary.items() if k != "schema_version"})
        summary_path = self.path.with_name(SUMMARY_FILENAME)
        temporary = summary_path.with_name(summary_path.name + ".tmp")
        temporary.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, summary_path)
        return summary

    def summary(self) -> dict[str, Any]:
        with self._lock:
            return {
                "schema_version": SCHEMA_VERSION,
                "run_id": self.run_id,
                "started_at": self.started_at,
                "ended_at": _iso(self._clock()) if self._finished else None,
                "end_reason": self.end_reason,
                "model_calls": self._model_calls,
                "rejected_calls": self._rejected_calls,
                "completed_calls": self._successful + self._failed,
                "incomplete_calls": max(
                    0, self._model_calls - self._successful - self._failed
                ),
                "by_purpose": dict(sorted(self._by_purpose.items())),
                "successful": self._successful,
                "failed": self._failed,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
            }
