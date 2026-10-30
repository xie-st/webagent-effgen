"""The one synchronous model boundary between the harness and the official SDK.

``generate(messages, purpose, deadline)`` is intentionally the whole public
surface used for inference.  Messages are ordinary ``system``/``user``/
``assistant`` dictionaries with string content; the platform owns model choice,
credentials and sampling parameters.  The SDK call is made on the caller's
current thread, which is the thread the official SDK binds for each task.
"""
from __future__ import annotations

import contextlib
import contextvars
import time
from dataclasses import dataclass
from typing import Any, Iterator, Mapping
from uuid import uuid4

from .telemetry import Telemetry

ALLOWED_ROLES = frozenset({"system", "user", "assistant"})


@dataclass(frozen=True)
class ModelReply:
    text: str
    request_id: str | None


@dataclass(frozen=True)
class CallScope:
    run_id: str | None
    step: int
    deadline: float | None
    purpose: str


_scope: contextvars.ContextVar[CallScope | None] = contextvars.ContextVar(
    "webagent_model_call_scope", default=None
)


def _validate_messages(messages: Any) -> list[dict[str, str]]:
    if not isinstance(messages, (list, tuple)) or not messages:
        raise ValueError("messages must be a non-empty list")
    clean: list[dict[str, str]] = []
    for index, message in enumerate(messages):
        if not isinstance(message, Mapping):
            raise ValueError(f"message {index} must be an object")
        if set(message) != {"role", "content"}:
            raise ValueError(
                f"message {index} must contain only string role and content fields"
            )
        role, content = message["role"], message["content"]
        if role not in ALLOWED_ROLES:
            raise ValueError(
                f"message {index} role must be system, user or assistant, got {role!r}"
            )
        if not isinstance(content, str):
            raise ValueError(f"message {index} content must be a string")
        clean.append({"role": role, "content": content})
    return clean


class SdkModelPort:
    """Synchronous adapter over ``third_party_agent.model.generate``."""

    def __init__(self, sdk=None, telemetry: Telemetry | None = None) -> None:
        if sdk is None:
            from third_party_agent import model as sdk
        self._sdk = sdk
        self.telemetry = telemetry or Telemetry()

    def bind_telemetry(self, telemetry: Telemetry) -> None:
        """Point this port at the active run's log destination.

        A port may outlive one ``MyAgent`` run when it is injected by the
        caller.  Each reset allocates or reuses the current run's telemetry and
        rebinds the port before the policy can issue another SDK call, so no
        model call is written to the previous run's summary.
        """
        if not isinstance(telemetry, Telemetry):
            raise TypeError("telemetry must be a Telemetry instance")
        self.telemetry = telemetry

    @contextlib.contextmanager
    def call_scope(
        self,
        *,
        run_id: str | None,
        step: int,
        deadline: float | None,
        purpose: str,
    ) -> Iterator[None]:
        token = _scope.set(CallScope(run_id, int(step), deadline, purpose))
        try:
            yield
        finally:
            _scope.reset(token)

    def current_scope(self) -> CallScope:
        return _scope.get() or CallScope(
            self.telemetry.run_id,
            0,
            None,
            "decision",
        )

    def generate(
        self,
        messages: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
        purpose: str,
        deadline: float | None,
    ) -> ModelReply:
        """Make exactly one SDK generation call and log its outcome.

        Nothing except the validated messages reaches the SDK.  The purpose and
        deadline are harness metadata for logging and the pre-call deadline
        check; they are not sent to the platform.
        """
        clean = _validate_messages(messages)
        if not isinstance(purpose, str) or not purpose:
            raise ValueError("purpose must be a non-empty string")
        if deadline is not None and not isinstance(deadline, (int, float)):
            raise ValueError("deadline must be a number or None")
        scope = self.current_scope()

        started = time.time()
        if deadline is not None and started >= float(deadline):
            error = TimeoutError("Task execution deadline reached before model call")
            self.telemetry.model_call_rejected(
                purpose=purpose,
                started_at=started,
                ended_at=time.time(),
                error=error,
                run_id=scope.run_id,
                step=scope.step,
                deadline=deadline,
            )
            raise error

        call_id = uuid4().hex
        start_event = self.telemetry.model_call_start(
            purpose=purpose,
            call_id=call_id,
            started_at=started,
            run_id=scope.run_id,
            step=scope.step,
            deadline=deadline,
        )
        call_seq = int(start_event["call_seq"])
        request_id: str | None = None
        try:
            reply = self._sdk.generate(clean)
            request_id = getattr(reply, "request_id", None)
            if request_id is not None and not isinstance(request_id, str):
                request_id = str(request_id)
            text = getattr(reply, "text", None)
            if not isinstance(text, str):
                raise TypeError("SDK model response must contain string text")
            ended = time.time()
            self.telemetry.model_call_end(
                purpose=purpose,
                call_id=call_id,
                call_seq=call_seq,
                request_id=request_id,
                started_at=started,
                ended_at=ended,
                run_id=scope.run_id,
                step=scope.step,
                deadline=deadline,
            )
            return ModelReply(text=text, request_id=request_id)
        except Exception as exc:
            self.telemetry.model_call_failed(
                purpose=purpose,
                call_id=call_id,
                call_seq=call_seq,
                request_id=request_id,
                started_at=started,
                ended_at=time.time(),
                error=exc,
                run_id=scope.run_id,
                step=scope.step,
                deadline=deadline,
            )
            raise


__all__ = ["ALLOWED_ROLES", "CallScope", "ModelReply", "SdkModelPort"]
