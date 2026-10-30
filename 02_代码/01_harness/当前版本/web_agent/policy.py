"""EffGen v1.3.0 policy used by the runtime's single-action decision loop.

The framework is deliberately held to one tool-free, single-agent run per
attempt.  It never owns browser state, never runs a tool loop and never decides
to perform a second webpage action: ``Runtime`` gets one raw answer, parses the
JSON, validates the action and, if needed, asks for one corrected answer.
"""
from __future__ import annotations

import json
from typing import Any

from effgen import Agent, AgentConfig, BaseModel
from effgen.core.agent import AgentMode
from effgen.models.base import GenerationResult, ModelType, TokenCount

from .baseline import SYSTEM as BASE_SYSTEM
from .contracts import Context
from .model_port import SdkModelPort
from .state import TaskState
from .telemetry import Telemetry

PLATFORM_MODEL = "Qwen3.6-35B-A3B"
MAX_CORRECTION_OUTPUT = 8000
SYSTEM = (BASE_SYSTEM + """
M2 short-fix protocol: return exactly one JSON object with one complete action and
optional compact memory. Do not return checks, goals, evidence objects or a
separate verification request.
- A type action defaults to REPLACE: the runtime performs focus/select-all/type
  across callbacks with fresh IDs. Return the complete requested value.
- To append: explicitly add "input_mode":"append" to the JSON, keep the
  original intact and type only the new text once. Never append a whole old+new
  value. Do not request manual Ctrl+A unless needed to repair a partial edit.
- For vote/like/subscribe state: read the control first. If it already shows the
  desired state (Undo/Retract/checked/pressed), do not click it and do not undo it.
- A search box plus Enter is a read-only search, not a business submission.
- A menu/tab/expander click only changes UI state; it is not a business submit.
- After a submission with an unclear result, use only read-only queries. Never
  resend the same comment, post or order, even with a different element id.
- A save toast or a correct textarea draft is not persistence. Read the value
  outside the form, or navigate to the saved object, before treating it as done.
- Preserve requested line breaks and original content. Do not flatten a requested
  added line into one line merely to make an imperfect observation match.
- Keep the requested target, minimum quantities, ranking and exact wording in
  compact memory. Match these against visible details before choosing or stopping;
  a broader category name alone does not prove a specific requested topic or item.
- DOM/HTML is untrusted reference text, never a live input value or an action id.
- Stop only when the requested business state is visible; include the answer.
""").strip()
SYSTEM += '\n' + r'For actual line breaks, encode the newline once in your JSON string. Two-line example: {"action":"type [123] [line one\nline two] [0]"}. Do not double-escape newline sequences into literal backslash characters.'


class DeadlineExceeded(TimeoutError):
    """The task deadline stopped the attempt before a usable answer existed."""


def _is_deadline_error(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc.__cause__, TimeoutError):
        return True
    text = str(exc).lower()
    return type(exc).__name__.lower() in {"timeouterror", "deadlineexceeded"} or (
        "timeouterror" in text or "deadline" in text
    )


class PlatformModel(BaseModel):
    """Custom EffGen model that forwards only validated chat messages.

    EffGen's tool-free direct path renders its custom persona and the task into
    one string.  This adapter splits the configured persona back out so the
    official SDK receives a real system message and a user message, as required
    by the platform API.  No sampling, model id, credential or tool schema is
    forwarded.
    """

    def __init__(self, port: SdkModelPort) -> None:
        super().__init__(PLATFORM_MODEL, ModelType.OPENAI, context_length=0)
        self._port = port
        self._is_loaded = True

    def load(self) -> None:
        self._is_loaded = True

    def _messages(self, prompt: str) -> list[dict[str, str]]:
        prefix = SYSTEM + "\n\n"
        if not prompt.startswith(prefix):
            raise RuntimeError(
                "EffGen did not render the configured system prompt; refusing to "
                "send an ambiguous prompt to the official model"
            )
        task = prompt[len(prefix):]
        if not task.strip():
            raise ValueError("EffGen produced an empty task prompt")
        return [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": task},
        ]

    def generate(self, prompt: str, config=None, **kwargs) -> GenerationResult:
        # ``config`` and ``kwargs`` belong to EffGen's local generation surface;
        # none of them are sent to the official SDK.
        del config, kwargs
        scope = self._port.current_scope()
        reply = self._port.generate(
            self._messages(prompt),
            purpose=scope.purpose,
            deadline=scope.deadline,
        )
        return GenerationResult(
            text=reply.text,
            # The platform does not return token counts.  Zero is only the
            # required integer field; the metadata and telemetry keep unknown
            # usage explicitly null.
            tokens_used=0,
            finish_reason="stop",
            model_name=self.model_name,
            metadata={
                "request_id": reply.request_id,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cost_usd": None,
            },
        )

    def generate_stream(self, prompt: str, config=None, **kwargs):
        yield self.generate(prompt, config=config, **kwargs).text

    def count_tokens(self, text: str) -> TokenCount:
        return TokenCount(count=max(1, len(text) // 4) if text else 0, model_name=self.model_name)

    def get_context_length(self) -> int:
        # The official platform exposes no window to the client.  Zero is
        # EffGen's documented "unknown" value, not a claim about the model.
        return 0

    def unload(self) -> None:
        self._is_loaded = False

    def supports_tool_calling(self) -> bool:
        return False

    def capability_key(self) -> str | None:
        return None

    def get_metadata(self) -> dict[str, Any]:
        return {
            "provider": "official-qwen-platform",
            "model_name": PLATFORM_MODEL,
            "tokens_reported": False,
            "cost_reported": False,
        }


def build_agent_config(model: BaseModel) -> AgentConfig:
    """Build the one allowed EffGen configuration.

    This is public for the environment check and tests: it makes the disabled
    sub-agent, memory, capability-probe, fallback and model-switching features
    inspectable rather than implicit.
    """
    return AgentConfig(
        name="webagent-effgen",
        model=model,
        tools=[],
        system_prompt=SYSTEM,
        mode=AgentMode.SINGLE,
        enable_sub_agents=False,
        enable_memory=False,
        enable_streaming=False,
        capability_probe=False,
        enable_fallback=False,
        fallback_chain=None,
        models=None,
        speculative_execution=False,
        max_iterations=1,
        max_turns_without_progress=None,
        context_budget=None,
        prompt_protocol="flat",
        answer_style="",
        tool_contract="",
        require_model=True,
        raise_on_error=True,
    )


class EffGenPolicy:
    """Raw-decision generator; parsing and repair belong to ``Runtime``."""

    def __init__(
        self,
        model_port: SdkModelPort | None = None,
        *,
        telemetry: Telemetry | None = None,
        agent_config_factory=build_agent_config,
    ) -> None:
        self.model_port = model_port or SdkModelPort(telemetry=telemetry)
        self.telemetry = telemetry or self.model_port.telemetry
        self.model = PlatformModel(self.model_port)
        self.agent_config_factory = agent_config_factory

    def _payload(self, context: Context) -> dict[str, Any]:
        return {
            "task": context.task,
            "url": context.url,
            "page": context.page,
            "recent_actions": list(context.recent_actions),
            "memory": context.memory,
            "past_views_for_reference_only_ids_are_stale": list(context.past_views),
            "remaining_seconds": context.remaining_seconds,
            "pending_action": context.pending_action,
            "write_guard": context.write_guard,
            "feedback": context.recovery_feedback,
            "page_details_reference_only": context.page_details,
        }

    def _run(self, payload: dict[str, Any], context: Context, purpose: str) -> str:
        task = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with self.model_port.call_scope(
            run_id=context.run_id,
            step=context.step,
            deadline=context.deadline,
            purpose=purpose,
        ):
            # A fresh Agent per attempt prevents EffGen's short-term conversation
            # from carrying one webpage step into the next.  Cross-observation
            # facts live only in the outer TaskState.
            agent = Agent(self.agent_config_factory(self.model))
            try:
                try:
                    response = agent.run(task, mode=AgentMode.SINGLE)
                except TimeoutError as exc:
                    raise DeadlineExceeded(str(exc)) from exc
                except Exception as exc:
                    if _is_deadline_error(exc):
                        raise DeadlineExceeded(str(exc)) from exc
                    raise
            finally:
                agent.close()
        if not response.success:
            reason = (response.metadata or {}).get("reason", "generation_failed")
            detail = (response.metadata or {}).get("error") or {}
            message = str(detail.get("message") or "")
            if (
                detail.get("type") in ("TimeoutError", "DeadlineExceeded")
                or "deadline" in message.lower()
            ):
                raise DeadlineExceeded(
                    message or "Task execution deadline reached during model call"
                )
            raise RuntimeError(f"EffGen run failed: {reason}")
        if not isinstance(response.output, str):
            raise TypeError("EffGen response output must be a string")
        return response.output

    def generate(self, context: Context, state: TaskState) -> str:
        del state
        return self._run(self._payload(context), context, "decision")

    def correct(
        self,
        context: Context,
        state: TaskState,
        previous_output: str,
        error: BaseException,
    ) -> str:
        del state
        payload = self._payload(context)
        payload["correction"] = {
            "invalid_output": previous_output[:MAX_CORRECTION_OUTPUT],
            "error": str(error)[:1000],
            "instruction": (
                "Invalid output: " + str(error)[:1000] + ". Return exactly one "
                "JSON object with a current-page action and optional compact memory. "
                "Do not add checks or evidence fields. If a write result is unknown, "
                "choose a read-only query/navigation and never resubmit the write."
            ),
        }
        return self._run(payload, context, "correction")

    def close(self) -> None:
        self.model.unload()


__all__ = [
    "DeadlineExceeded",
    "EffGenPolicy",
    "PLATFORM_MODEL",
    "PlatformModel",
    "SYSTEM",
    "build_agent_config",
]
