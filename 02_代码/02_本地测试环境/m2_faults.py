"""Controllable write faults for the local M2 fixtures.

This module is deliberately independent of the harness and of any M2 policy
implementation.  A fault plan is configured per write operation, is consumed
after a fixed number of activations, and can optionally seed the business
state so that replacement-vs-append faults are observable.

The local practice site is synthetic.  None of these faults exist on the
official site and nothing here is an official benchmark result.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any

FAULT_MODES = frozenset({
    "no_effect_success",
    "append_value",
    "commit_lost_receipt",
    "missing_target",
})
WRITE_OPERATIONS = frozenset({
    "profile", "post", "reply", "subscribe", "vote", "cart", "checkout",
})
SCALAR_OPERATIONS = frozenset({"profile", "post", "reply"})
SEED_FIELDS = frozenset({
    "bio", "title", "reply", "subscribed", "votes", "cart", "ordered", "orders",
})


@dataclass
class FaultSpec:
    """One operation's fault, consumed after ``times`` activations."""

    mode: str
    times: int = 1
    note: str = ""
    fired: int = 0

    def __post_init__(self):
        if self.mode not in FAULT_MODES:
            raise ValueError(f"unknown fault mode: {self.mode!r}")
        if not isinstance(self.times, int) or self.times < 1:
            raise ValueError("fault times must be a positive integer")

    def to_dict(self):
        return {"mode": self.mode, "times": self.times,
                "note": self.note, "fired": self.fired}


@dataclass
class FaultPlan:
    """Per-operation faults plus an optional deterministic fixture seed.

    ``take`` records every activation, so evidence can show that a fault was
    actually injected once and consumed before recovery.
    """

    specs: dict[str, FaultSpec] = field(default_factory=dict)
    seed: dict[str, Any] = field(default_factory=dict)
    token: str | None = None
    _lock: RLock = field(default_factory=RLock, repr=False)
    _events: list[dict] = field(default_factory=list, repr=False)

    def __post_init__(self):
        for operation, spec in self.specs.items():
            if operation not in WRITE_OPERATIONS and operation != "*":
                raise ValueError(f"unknown write operation: {operation!r}")
            if spec.mode == "append_value" and operation not in SCALAR_OPERATIONS:
                raise ValueError(
                    "append_value is only meaningful for profile/post/reply")
        for key in self.seed:
            if key not in SEED_FIELDS:
                raise ValueError(f"unknown fixture seed field: {key!r}")

    def take(self, operation: str) -> dict | None:
        """Consume one activation for ``operation`` and return its record."""
        with self._lock:
            spec = self.specs.get(operation) or self.specs.get("*")
            if spec is None or spec.fired >= spec.times:
                return None
            spec.fired += 1
            event = {"operation": operation, "mode": spec.mode,
                     "times": spec.times, "fired": spec.fired, "note": spec.note}
            self._events.append(event)
            return dict(event)

    @property
    def events(self):
        with self._lock:
            return [dict(event) for event in self._events]

    def apply_seed(self, fixture):
        """Apply configured initial values before the first request."""
        for key, value in self.seed.items():
            if key in ("cart", "orders"):
                value = list(value)
            setattr(fixture, key, value)
        if "orders" in self.seed and "ordered" not in self.seed:
            fixture.ordered = bool(fixture.orders)

    def to_dict(self):
        return {"token": self.token, "seed": dict(self.seed),
                "faults": {operation: spec.to_dict()
                           for operation, spec in self.specs.items()},
                "activations": self.events}

    @classmethod
    def from_dict(cls, data: dict | None):
        data = data or {}
        raw_faults = data.get("faults") or {}
        specs = {}
        for operation, raw in raw_faults.items():
            if isinstance(raw, str):
                raw = {"mode": raw}
            if not isinstance(raw, dict):
                raise ValueError(f"fault for {operation!r} must be an object")
            specs[operation] = FaultSpec(
                mode=raw["mode"], times=int(raw.get("times", 1)),
                note=str(raw.get("note", "")))
        return cls(specs=specs, seed=dict(data.get("seed") or {}),
                   token=data.get("token"))

    @classmethod
    def from_file(cls, path: str | Path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def empty(cls):
        return cls()
