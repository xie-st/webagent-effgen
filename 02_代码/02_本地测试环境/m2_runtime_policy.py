"""Deterministic local policy and semantic-verification stub for the bridge.

This is not a model and it is not an official submission path.  The policy sees
only the original task, the current real-DOM accessibility tree and the
Runtime's own context/state.  It has no access to the fixture object, fault
plan, write counters or grading truth.  The verification stub likewise reads
only the supplied original task and current AX, and returns evidence lines from
that AX so the real ``verify.parse_verification`` can reject fabricated claims.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

from m2_ax_text import field_atom, parse_atoms, prefixed_atom, split_items

_SAVE_BUTTONS = {
    "bio": "保存简介",
    "title": "发表帖子",
    "reply": "发送回复",
}
_FIELD_LABELS = {
    "bio": ("个人简介", "简介"),
    "title": ("帖子标题", "标题"),
    "reply": ("回复内容", "回复"),
}
_SHOP_WORDS = ("购物车", "订单", "键盘", "商城", "下单")


def _normalize(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _origin(url: str) -> str:
    parts = urlsplit(str(url or ""))
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else ""


def _int_value(value: str) -> int | None:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else None


def _infer_field(task: str, target) -> str | None:
    text = f"{task} {target}"
    if "简介" in text or "开发者-" in str(target):
        return "bio"
    if "帖子" in text and ("标题" in text or "并行调度-" in str(target)):
        return "title"
    if "回复" in text or "已确认-" in str(target):
        return "reply"
    return None


def _find_role(atoms, role: str, contains: str):
    for atom in atoms:
        if atom.role == role and contains in atom.name:
            return atom
    return None


class ScriptedPolicy:
    """Small deterministic planner with an independent AX verifier stub."""

    def __init__(self, *, premature_stop: bool = False, guard_probe: bool = False):
        self.premature_stop = bool(premature_stop)
        self.guard_probe = bool(guard_probe)
        self._premature_done = False
        self._guard_probe_done = False
        self._typed_for: str | None = None
        self._fallbacks = 0
        self.events: list[dict] = []

    # Decision port -----------------------------------------------------
    def generate(self, context, state) -> str:
        action = self._next_action(context)
        self.events.append(
            {
                "kind": "policy_decision",
                "step": context.step,
                "action": action,
                "stop": action.startswith("stop"),
                "write_guard": context.write_guard,
            }
        )
        return json.dumps({"action": action}, ensure_ascii=False)

    def correct(self, context, state, raw, error) -> str:
        message = str(error)
        error_type = type(error).__name__
        if "Cannot stop" in message:
            # The runtime refused a premature success stop.  Keep the rejection
            # as evidence, then return the next real action through the same
            # correction path the production policy uses.
            self.events.append(
                {
                    "kind": "runtime_rejection",
                    "error_type": error_type,
                    "error": message[:1000],
                }
            )
            action = self._next_action(context)
            self.events.append(
                {
                    "kind": "policy_decision",
                    "step": context.step,
                    "action": action,
                    "stop": action.startswith("stop"),
                    "write_guard": context.write_guard,
                    "after_runtime_correction": True,
                }
            )
            return json.dumps({"action": action}, ensure_ascii=False)
        if error_type == "WriteGuardError" or "write result is unknown" in message:
            # Deliberate probe: a write (Enter) while the previous result is
            # unknown must be refused before it reaches the browser.  Then use
            # the allowed read-only query path.
            self.events.append(
                {
                    "kind": "runtime_rejection",
                    "error_type": error_type,
                    "error": message[:1000],
                    "probe": "write_while_pending_unknown",
                }
            )
            action = self._next_action(context)
            self.events.append(
                {
                    "kind": "policy_decision",
                    "step": context.step,
                    "action": action,
                    "stop": action.startswith("stop"),
                    "write_guard": context.write_guard,
                    "after_runtime_correction": True,
                }
            )
            return json.dumps({"action": action}, ensure_ascii=False)
        raise RuntimeError("local scripted policy emitted invalid output: " + message)

    def note_runtime_error(self, error: BaseException) -> None:
        self.events.append(
            {
                "kind": "runtime_rejection",
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
            }
        )

    def drain_events(self) -> list[dict]:
        events, self.events = self.events, []
        return events

    def close(self) -> None:
        pass

    # Planner -----------------------------------------------------------
    def _next_action(self, context) -> str:
        atoms = parse_atoms(context.page)
        goals = [dict(goal) for goal in context.goal_checks]
        origin = _origin(context.url)

        if self.premature_stop and not self._premature_done:
            self._premature_done = True
            return "stop [premature]"

        if context.write_guard == "read_only_required":
            if self.guard_probe and not self._guard_probe_done:
                self._guard_probe_done = True
                # Enter is classified as a write by the Runtime.  The guard
                # must reject it before any browser action is executed.
                return "press [Enter]"
            path = "/shop" if self._shop_task(context.task, goals) else "/forum"
            return f"goto [{origin}{path}]"

        if self._typed_for is not None:
            button_name = self._typed_for
            self._typed_for = None
            button = _find_role(atoms, "button", button_name)
            if button is not None:
                return f"click [{button.element_id}]"

        for goal in goals:
            if goal.get("status") == "verified":
                continue
            action = self._goal_action(goal, atoms, context.task)
            if action:
                return action

        if goals and all(goal.get("status") == "verified" for goal in goals):
            return "stop [done]"

        # Nothing actionable on this page or an unrecognised requirement:
        # navigate read-only to the task's home page once and let verification
        # decide instead of inventing a write.
        path = "/shop" if self._shop_task(context.task, goals) else "/forum"
        self._fallbacks += 1
        if self._fallbacks <= 3:
            return f"goto [{origin}{path}]"
        return "stop [blocked]"

    def _goal_action(self, goal, atoms, task: str) -> str | None:
        kind = goal.get("kind")
        target = goal.get("target")
        status = goal.get("status")
        if kind in {"exact_equal", "exact_append"}:
            field = goal.get("field") or _infer_field(task, target)
            if field is None:
                return None
            current = field_atom(atoms, field)
            if current is not None and _normalize(current[1]) == _normalize(target):
                return None
            labels = _FIELD_LABELS.get(field, ())
            textbox = None
            for label in labels:
                textbox = _find_role(atoms, "textbox", label)
                if textbox is not None:
                    break
            if textbox is None:
                return None
            button_name = _SAVE_BUTTONS[field]
            self._typed_for = button_name
            return f"type [{textbox.element_id}] [{target}] [0]"
        if kind == "state_true":
            current = prefixed_atom(atoms, "订阅状态")
            if current is not None and "已订阅" in current[1]:
                return None
            button = _find_role(atoms, "button", "订阅")
            return f"click [{button.element_id}]" if button else None
        if kind in {"count_once", "count_per_object"}:
            current = prefixed_atom(atoms, "点赞数")
            if current is not None:
                count = _int_value(current[1])
                if count is not None and count >= int(target or 1):
                    return None
            button = _find_role(atoms, "button", "点赞")
            return f"click [{button.element_id}]" if button else None
        if kind == "item_exact":
            current = prefixed_atom(atoms, "购物车")
            if current is not None and split_items(current[1]) == [str(target)]:
                return None
            button = _find_role(atoms, "button", "加入购物车")
            if button is None:
                button = _find_role(atoms, "button", "购物车")
            return f"click [{button.element_id}]" if button else None
        if kind == "order_once":
            current = prefixed_atom(atoms, "订单")
            if current is not None:
                count = _int_value(current[1])
                if "已提交" in current[1] and count is not None and count >= int(target or 1):
                    return None
            button = _find_role(atoms, "button", "提交订单")
            if button is None:
                button = _find_role(atoms, "button", "下单")
            return f"click [{button.element_id}]" if button else None
        return None

    @staticmethod
    def _shop_task(task: str, goals) -> bool:
        if any(word in str(task) for word in _SHOP_WORDS):
            return True
        return any(
            goal.get("kind") in {"item_exact", "order_once"} for goal in goals
        )

    # Verification port ------------------------------------------------
    def verify(self, context, state, payload) -> str:
        atoms = parse_atoms(payload.get("accessibility_tree", ""))
        task = str(payload.get("original_task") or payload.get("task") or "")
        checks = [
            self._check_goal(goal, atoms, task)
            for goal in payload.get("goal_checks_from_original_task", ())
            if isinstance(goal, dict)
        ]
        return json.dumps(
            {
                "checks": checks,
                "actual": "deterministic_ax_stub",
                "model_calls": 0,
            },
            ensure_ascii=False,
        )

    def _check_goal(self, goal: dict, atoms, task: str) -> dict:
        goal_id = str(goal.get("goal_id", ""))
        quote = str(goal.get("source_quote") or task)
        kind = goal.get("kind")
        target = goal.get("target")
        status, actual, atom, reason = "unknown", None, None, ""
        if kind in {"exact_equal", "exact_append"}:
            field = goal.get("field") or _infer_field(task, target)
            current = field_atom(atoms, field)
            if current is not None:
                atom, value = current
                actual = value
                if kind == "exact_equal":
                    if _normalize(value) == _normalize(target):
                        status, reason = "confirmed", "exact field value visible"
                    else:
                        status, reason = "failed", "field value is not exact"
                else:
                    baseline = goal.get("baseline")
                    base = _normalize(baseline)
                    expected = {base + _normalize(target)}
                    if base and _normalize(value) in expected:
                        status, reason = "confirmed", "baseline plus exact addition"
                    elif base and _normalize(value).startswith(base):
                        status, reason = "failed", "addition is not exact"
                    else:
                        status, reason = "unknown", "append baseline not visible"
            else:
                reason = "labelled business field not visible"
        elif kind == "item_exact":
            current = prefixed_atom(atoms, "购物车")
            if current is not None:
                atom, value = current
                items = split_items(value)
                actual = items
                if items == [str(target)]:
                    status, reason = "confirmed", "cart contains exactly the item"
                else:
                    status, reason = "failed", "cart state differs from the target"
            else:
                reason = "cart business line not visible"
        elif kind == "count_once":
            current = prefixed_atom(atoms, "点赞数")
            if current is not None:
                atom, value = current
                count = _int_value(value)
                actual = count if count is not None else value
                if count is not None and count == int(target or 0):
                    status, reason = "confirmed", "vote count matches"
                else:
                    status, reason = "failed", "vote count differs"
            else:
                reason = "vote business line not visible"
        elif kind == "state_true":
            current = prefixed_atom(atoms, "订阅状态")
            if current is not None:
                atom, value = current
                subscribed = "已订阅" in value and "未订阅" not in value
                actual = subscribed
                if subscribed is bool(target):
                    status, reason = "confirmed", "subscription state matches"
                else:
                    status, reason = "failed", "subscription state differs"
            else:
                reason = "subscription business line not visible"
        elif kind == "order_once":
            current = prefixed_atom(atoms, "订单")
            if current is not None:
                atom, value = current
                count = _int_value(value)
                submitted = "已提交" in value and "未提交" not in value
                actual = count if count is not None else value
                if submitted and count is not None and count == int(target or 0):
                    status, reason = "confirmed", "submitted order count matches"
                else:
                    status, reason = "failed", "order state differs"
            else:
                reason = "order business line not visible"
        else:
            reason = "deterministic local stub does not settle this kind"
        evidence = []
        if atom is not None:
            evidence.append({"line": atom.line, "quote": atom.name})
        return {
            "goal_id": goal_id,
            "status": status,
            "actual": actual,
            "source_task_quote": quote,
            "evidence": evidence,
            "reason": reason,
        }
