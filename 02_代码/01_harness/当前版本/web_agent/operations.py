"""Local operation semantics for the M2 short fix.

The model still chooses one WebArena action per callback.  This module only
does what the page can settle locally: exact input readback, same-object target
state, and a pending submission that must be read back before another write.
There is no task-goal regex extraction and no model-written proof object.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Mapping

from .ax import AXTree, Node, text_contains
from .contracts import Frame, PendingAction
from .state import TaskState
from uuid import uuid4

_SAFE_READ = "press [Tab]"
_FIELD_ROLES = frozenset({"textbox", "searchbox", "combobox", "spinbutton", "slider"})
_COMMIT_TERMS = (
    "add to cart", "buy again", "checkout", "place order", "submit order",
    "save", "submit", "post", "publish", "reply", "comment", "send", "confirm",
    "create", "update", "delete", "remove", "order", "buy", "purchase",
    "保存", "提交", "发布", "发帖", "发表", "回复", "评论", "发送", "确认",
    "创建", "更新", "删除", "移除", "下单", "结账", "购买", "重购", "加入购物车",
)
_READ_TERMS = (
    "next", "previous", "prev", "page", "view", "show", "expand", "collapse",
    "more", "back", "cancel", "dismiss", "close", "filter", "sort", "search",
    "menu", "details", "history", "status", "preview", "help", "open",
    "刷新", "筛选", "排序", "搜索", "下一页", "上一页", "查看", "展开", "收起",
    "取消", "关闭", "返回", "详情", "历史", "菜单", "状态", "打开",
)
_DANGEROUS_URL = re.compile(
    r"(?:^|[/_\-?&=])(?:delete|remove|re-?order|buy[-_ ]?again|checkout|"
    r"cancel(?:lation|order)?|upvote|downvote|vote|like|unlike|subscribe|"
    r"unsubscribe|follow|unfollow|add[-_/]?(?:to[-_/]?)?cart|save|purchase)"
    r"(?=[/_\-?&=.]|$)",
    re.I,
)
_COMPOSE_URL = re.compile(
    r"(?:^|/)(?:submit|new|create|reply|compose|edit)(?:[/_\-]|$)"
    r"|[?&](?:reply|quote|compose|edit|new)(?:=|&|$)",
    re.I,
)
_ERROR_WORDS = (
    "error", "invalid", "required", "failed", "cannot", "could not",
    "错误", "失败", "不能", "无效", "必填", "请填写", "请选择",
)


@dataclass(frozen=True)
class Plan:
    action: str
    kind: str
    write: bool = False
    node: Node | None = None
    field_key: dict[str, Any] | None = None
    value: str | None = None
    baseline: str | None = None
    replace: bool = False
    expected: str | None = None
    object_key: str | None = None
    control_kind: str | None = None
    desired: bool | None = None
    before_state: bool | None = None
    satisfied: bool = False
    undo_guard: bool = False
    commit_kind: str = "commit"
    values: tuple[str, ...] = ()
    reason: str = ""


@dataclass
class Block:
    action: str
    reason: str
    detail: str = ""


def _has_word(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    for term in terms:
        if term.isascii():
            if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered):
                return True
        elif term.casefold() in lowered:
            return True
    return False


def _commit_kind(name: str) -> str:
    text = name.casefold()
    if any(word in text for word in ("order", "checkout", "下单", "结账", "订单")):
        return "order"
    if any(word in text for word in ("delete", "remove", "cancel", "删除", "移除", "取消")):
        return "delete"
    if any(word in text for word in ("post", "reply", "comment", "发帖", "发信", "回复", "评论", "发表")):
        return "post"
    if any(word in text for word in ("save", "update", "保存", "更新")):
        return "save"
    return "commit"


def _is_read_control(node: Node) -> bool:
    if node.role in {"tab", "menuitem"}:
        return True
    if node.expanded is not None or "haspopup:" in node.raw.casefold():
        return True
    return _has_word(node.name, _READ_TERMS)


def _recent_values(state: TaskState, frame: Frame) -> tuple[str, ...]:
    values: list[str] = []
    drafts = state.drafts
    for key in reversed(list(drafts)):
        item = drafts[key]
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            continue
        if item.get("role") == "searchbox":
            continue
        if item.get("url") != frame.url:
            continue
        text = item.get("expected") or item["text"]
        if text and text not in values:
            values.append(text)
        if len(values) == 4:
            break
    return tuple(reversed(values))


def _input_mismatch(tree: AXTree, state: TaskState, frame: Frame) -> str | None:
    drafts = state.drafts
    for key in reversed(list(drafts)):
        item = drafts[key]
        if not isinstance(item, dict) or item.get("url") != frame.url:
            continue
        expected = item.get("expected")
        if not isinstance(expected, str):
            continue
        node = tree.find_field(item.get("field_key"))
        if node is None:
            continue
        actual = tree.control_value(node)
        if actual is None:
            continue
        if _norm(actual) != _norm(expected):
            return (
                "The editable field does not contain the complete expected value. "
                "Expected: " + _clip(expected) + "; observed: " + _clip(actual)
            )
    return None


def plan(action: str, frame: Frame, state: TaskState) -> Plan:
    text = action.strip()
    tree = AXTree(frame)
    if text.startswith("stop ["):
        return Plan(text, "stop")
    if text in {"go_back", "go_forward", "scroll [up]", "scroll [down]"}:
        return Plan(text, "read")
    if text.startswith("hover ["):
        return Plan(text, "read")
    if text.startswith("goto ["):
        target = text[len("goto ["):-1]
        if _DANGEROUS_URL.search(target):
            return Plan(text, "commit", write=True, commit_kind="navigation",
                        values=(), reason="state-changing URL")
        return Plan(text, "read")
    click = re.fullmatch(r"click \[(\d+)\]", text)
    if click:
        node = tree.by_id.get(click.group(1))
        if node is None:
            return Plan(text, "unknown", write=True, reason="current element id not found")
        if node.role in _FIELD_ROLES:
            return Plan(text, "focus", node=node, field_key=node.field_key)
        if node.role in {"checkbox", "radio", "option", "switch"}:
            before = node.state
            desired = True if before is None else not before
            return Plan(
                text, "ensure", write=True, node=node,
                object_key=tree.object_key(node),
                control_kind=node.control_kind or node.role,
                desired=desired, before_state=before,
                satisfied=(before is not None and before == desired),
                undo_guard=(before is True and node.is_retract),
                reason="selectable control",
            )
        if node.control_kind:
            before = node.state
            desired = not node.is_retract
            return Plan(
                text, "ensure", write=True, node=node,
                object_key=tree.object_key(node),
                control_kind=node.control_kind,
                desired=desired, before_state=before,
                satisfied=(before is not None and before == desired),
                undo_guard=(before is True and node.is_retract),
                reason="target-state control",
            )
        if node.role == "link" and _DANGEROUS_URL.search(node.url or ""):
            return Plan(text, "commit", write=True, node=node,
                        object_key=tree.object_key(node), commit_kind=_commit_kind(node.name),
                        values=_recent_values(state, frame), reason="state-changing link")
        if node.role == "link":
            return Plan(text, "read", node=node, reason="resource or compose navigation")
        if node.expanded is not None or "haspopup:" in node.raw.casefold():
            commits = tuple(term for term in _COMMIT_TERMS if term not in {"post", "comment", "reply", "order"})
            if not _has_word(node.name, commits) and node.name.casefold() not in {"post", "comment", "reply", "order"}:
                return Plan(text, "read", node=node, reason="explicit menu/expander")
        if _has_word(node.name, _COMMIT_TERMS):
            return Plan(text, "commit", write=True, node=node,
                        object_key=tree.object_key(node), commit_kind=_commit_kind(node.name),
                        values=_recent_values(state, frame), reason="commit control")
        if node.role == "link":
            if _COMPOSE_URL.search(node.url or ""):
                return Plan(text, "read", node=node, reason="compose navigation")
            if _is_read_control(node):
                return Plan(text, "read", node=node, reason="navigation")
            return Plan(text, "read", node=node, reason="resource navigation")
        if node.role in {"button", "menuitem"} and node.inside_form:
            return Plan(text, "commit", write=True, node=node,
                        object_key=tree.object_key(node), commit_kind=_commit_kind(node.name),
                        values=_recent_values(state, frame), reason="form button")
        if _is_read_control(node):
            return Plan(text, "read", node=node, reason="read control")
        return Plan(text, "read", node=node, reason="control meaning unknown; observe effect")
    type_action = re.fullmatch(r"type \[(\d+)\] \[(.*)\] \[([01])\]", text, flags=re.S)
    if type_action:
        node = tree.by_id.get(type_action.group(1))
        value = type_action.group(2)
        enter = type_action.group(3) == "1"
        if node is None:
            return Plan(text, "unknown", write=True, reason="current element id not found")
        key = node.field_key
        replace = state.replace_armed(key)
        baseline = tree.control_value(node)
        if replace:
            expected = value
        elif baseline is not None:
            expected = baseline + value
        else:
            expected = None
        if node.role == "searchbox" or "search" in node.name.casefold() or "搜索" in node.name:
            return Plan(text, "search", node=node, field_key=key, value=value)
        if enter:
            return Plan(
                text, "commit", write=True, node=node, field_key=key,
                value=value, baseline=baseline, replace=replace, expected=expected,
                object_key=tree.object_key(node), commit_kind="submit",
                values=(value,) if value else _recent_values(state, frame),
                reason="typing submits the form",
            )
        return Plan(
            text, "input", node=node, field_key=key, value=value,
            baseline=baseline, replace=replace, expected=expected,
            reason="input effect",
        )
    press = re.fullmatch(r"press \[(.*)\]", text, flags=re.S)
    if press:
        keys = press.group(1).casefold()
        if keys in {"ctrl+a", "control+a", "control_l+a", "meta+a"}:
            focus_state = state.focus
            focus = (
                focus_state.get("field_key")
                if isinstance(focus_state, Mapping)
                else None
            )
            if focus is None:
                focused = tree.focused_field()
                focus = focused.field_key if focused is not None else None
            return Plan(text, "select_all", field_key=focus, replace=True,
                        node=tree.find_field(focus) if focus else None, reason="replace selection")
        if "enter" in keys or "return" in keys:
            focus = tree.focused_field()
            role = focus.role if focus is not None else None
            if role == "searchbox" or (
                focus is not None and ("search" in focus.name.casefold() or "搜索" in focus.name)
            ):
                return Plan(text, "search", node=focus, field_key=focus.field_key,
                            value=tree.control_value(focus) or "", reason="search submit")
            values = _recent_values(state, frame)
            return Plan(text, "commit", write=True, node=focus,
                        field_key=focus.field_key if focus is not None else None,
                        object_key=tree.object_key(focus) if focus is not None else None,
                        commit_kind="submit", values=values, reason="Enter submits")
        return Plan(text, "read", reason="keyboard navigation")
    return Plan(text, "unknown", write=True, reason="unrecognised action")


def register(plan: Plan, frame: Frame, state: TaskState, *, telemetry=None) -> PendingAction | None:
    if plan.kind == "focus":
        state.set_focus(plan.field_key, plan.node.element_id if plan.node else None)
        state.set_last_result("read", "focused an editable field", step=frame.step)
        return None
    if plan.kind == "select_all":
        if plan.field_key:
            state.set_focus(plan.field_key, plan.node.element_id if plan.node else None)
            state.arm_replace(plan.field_key)
            state.mark_activity()
            state.set_last_result("read", "selected the whole field; next type replaces it", step=frame.step)
        else:
            state.set_last_result("unknown", "Ctrl+A without a known field", step=frame.step)
        return None
    if plan.kind == "input":
        expected = {
            "kind": "input",
            "field_key": plan.field_key,
            "value": plan.expected,
            "typed": plan.value,
            "baseline": plan.baseline,
            "replace": plan.replace,
        }
        pending = PendingAction(
            pending_id=uuid4().hex,
            tab=frame.tab,
            step=frame.step,
            action=plan.action,
            operation="input",
            goal_ids=(),
            source={
                "run_id": frame.run_id,
                "step": frame.step,
                "url": frame.url,
                "observation_version": frame.observation_version,
                "element_id": plan.node.element_id if plan.node else None,
            },
            expected=expected,
            status="unknown",
        )
        state.clear_replace()
        if state.pending_for(frame.tab) is not None:
            raise ValueError("Cannot replace an unresolved operation with a draft")
        state.replace_pending(pending, tab=frame.tab)
        state.set_draft(
            plan.node.element_id if plan.node else "?",
            {
                "text": plan.value,
                "expected": plan.expected,
                "baseline": plan.baseline,
                "replace": plan.replace,
                "field_key": plan.field_key,
                "role": plan.node.role if plan.node else None,
                "step": frame.step,
                "url": frame.url,
                "observation_version": frame.observation_version,
            },
        )
        state.mark_unresolved("input typed but not observed as persisted")
        state.mark_activity()
        if telemetry is not None:
            telemetry.pending(step=frame.step, url=frame.url, action=plan.action,
                              pending=pending.as_dict(), expected=expected)
        return pending
    if plan.kind == "ensure":
        expected = {
            "kind": "ensure",
            "control_kind": plan.control_kind,
            "object_key": plan.object_key,
            "desired": plan.desired,
            "before": plan.before_state,
        }
        pending = PendingAction(
            pending_id=uuid4().hex,
            tab=frame.tab,
            step=frame.step,
            action=plan.action,
            operation="ensure",
            goal_ids=(),
            source={
                "run_id": frame.run_id,
                "step": frame.step,
                "url": frame.url,
                "observation_version": frame.observation_version,
                "element_id": plan.node.element_id if plan.node else None,
                "object_key": plan.object_key,
            },
            expected=expected,
            status="unknown",
        )
        state.replace_pending(pending, tab=frame.tab)
        state.mark_unresolved("target-state click not yet read back")
        state.mark_activity()
        if telemetry is not None:
            telemetry.pending(step=frame.step, url=frame.url, action=plan.action,
                              pending=pending.as_dict(), expected=expected)
        return pending
    if plan.kind == "commit":
        expected = {
            "kind": "commit",
            "object_key": plan.object_key,
            "commit_kind": plan.commit_kind,
            "values": list(plan.values),
            "baseline_texts": AXTree(frame).business_texts()[:30],
            "fields": [dict(item) for item in state.drafts.values()
                       if isinstance(item, dict) and item.get("url") == frame.url
                       and item.get("role") != "searchbox"],
        }
        pending = PendingAction(
            pending_id=uuid4().hex,
            tab=frame.tab,
            step=frame.step,
            action=plan.action,
            operation="commit",
            goal_ids=(),
            source={
                "run_id": frame.run_id,
                "step": frame.step,
                "url": frame.url,
                "observation_version": frame.observation_version,
                "element_id": plan.node.element_id if plan.node else None,
                "object_key": plan.object_key,
            },
            expected=expected,
            status="unknown",
        )
        state.replace_pending(pending, tab=frame.tab)
        state.mark_unresolved("submission result unknown until business readback")
        state.mark_activity()
        if telemetry is not None:
            telemetry.pending(step=frame.step, url=frame.url, action=plan.action,
                              pending=pending.as_dict(), expected=expected)
        return pending
    if plan.kind == "search":
        state.set_last_result("read", "search submission; results are read-only", step=frame.step)
        state.clear_focus()
        return None
    state.set_last_result("read", plan.reason or "read-only action", step=frame.step)
    state.clear_focus()
    return None


def guard(plan: Plan, frame: Frame, state: TaskState, *, telemetry=None) -> Block | None:
    if plan.kind == "stop":
        if not stop_allowed(state):
            return _block(frame, plan.action, state, "unresolved effect still needs readback",
                          telemetry=telemetry)
        return None
    pending = state.pending_for(frame.tab)
    if pending is not None and pending.status == "unknown" and (plan.write or plan.kind == "input"):
        return _block(frame, plan.action, state,
                      "previous write is unknown; read-only query/navigation only",
                      telemetry=telemetry)
    if plan.kind == "input" and not plan.replace:
        for draft in state.drafts.values():
            if (draft.get("url") == frame.url and draft.get("field_key") == plan.field_key
                    and draft.get("text") == plan.value and draft.get("expected") == plan.baseline):
                return _block(frame, plan.action, state,
                              "this exact append is already present; do not append twice",
                              telemetry=telemetry)
    if plan.kind == "ensure":
        if plan.satisfied:
            return _block(frame, plan.action, state,
                          "target state is already satisfied; do not click or undo",
                          telemetry=telemetry)
        if plan.undo_guard:
            return _block(frame, plan.action, state,
                          "the control would undo an already-applied state",
                          telemetry=telemetry)
        key = f"{plan.control_kind}:{plan.object_key}"
        if state.completed_has("ensure", key):
            return _block(frame, plan.action, state,
                          "this object's target state was already confirmed",
                          telemetry=telemetry)
        if state.failed_count(key) >= 2:
            return _block(frame, plan.action, state,
                          "the previous attempt had no confirmed effect; inspect the page first",
                          telemetry=telemetry)
    if plan.kind == "commit":
        key = f"{plan.commit_kind}:{plan.object_key}:{_values_key(plan.values)}"
        if state.completed_has("commit", key):
            return _block(frame, plan.action, state,
                          "this submission was already confirmed; do not send it again",
                          telemetry=telemetry)
        mismatch = _input_mismatch(AXTree(frame), state, frame)
        if mismatch:
            return _block(frame, plan.action, state, mismatch, telemetry=telemetry)
    return None


def _block(frame: Frame, action: str, state: TaskState, reason: str, *, telemetry=None) -> Block:
    state.set_last_result("blocked", reason, step=frame.step)
    # A rejected proposal is not progress. Stop repeated guard fallbacks instead
    # of moving focus with Tab until the global step ceiling is exhausted.
    pending = state.pending_for(frame.tab)
    key = f'{pending.pending_id if pending is not None else "none"}:{reason}'
    previous = state.data.get('_guard_block_streak', {})
    count = previous.get('count', 0) + 1 if previous.get('key') == key else 1
    state.data['_guard_block_streak'] = {'key': key, 'count': count}
    if telemetry is not None:
        telemetry.write_guard(
            step=frame.step,
            url=frame.url,
            action=action,
            pending_id=(state.pending_for(frame.tab).pending_id
                        if state.pending_for(frame.tab) is not None else None),
            allowed=False,
            reason=reason,
        )
    fallback = ('stop [Incomplete: repeated local guard rejection; effect remains unconfirmed]'
                if count >= 3 else _SAFE_READ)
    return Block(fallback, reason, reason)


def resolve(frame: Frame, state: TaskState, *, telemetry=None) -> dict[str, Any] | None:
    pending = state.pending_for(frame.tab)
    if pending is None or pending.step >= frame.step:
        return None
    tree = AXTree(frame)
    if pending.operation == "input":
        result = _resolve_input(pending, tree, frame)
    elif pending.operation == "ensure":
        result = _resolve_ensure(pending, tree, frame)
    elif pending.operation == "commit":
        result = _resolve_commit(pending, tree, frame)
    else:
        result = {"status": "unknown", "detail": "unknown operation"}
    status = result["status"]
    state.set_last_result(status, result.get("detail", ""), step=frame.step,
                          expected=result.get("expected"), actual=result.get("actual"))
    if status == "confirmed":
        state.clear_pending(frame.tab)
        remember_completed(state, pending, result)
        state.mark_resolved()
    elif status == "changed":
        # An input readback proves only the local draft.  It is not a
        # persistence claim, so the task remains unresolved until a save/post
        # submission is confirmed.
        state.clear_pending(frame.tab)
        if pending.operation == "input":
            state.mark_unresolved("input matches exactly but is not persisted yet")
        else:
            remember_completed(state, pending, result)
            state.mark_resolved()
    elif status in {"failed", "no_change", "mismatch", "unreadable"}:
        state.clear_pending(frame.tab)
        if status in {"failed", "no_change"}:
            remember_failed(state, pending, result)
        state.mark_unresolved(result.get("detail", status))
    else:
        state.mark_unresolved(result.get("detail", "unknown"))
    if telemetry is not None:
        telemetry.verification(
            step=frame.step,
            url=frame.url,
            observation_version=frame.observation_version,
            mode="operation",
            source="local_ax",
            status="confirmed" if status in {"confirmed", "changed"} else (
                "failed" if status in {"failed", "no_change", "mismatch"} else "unknown"
            ),
            pending_id=pending.pending_id,
            goal_ids=[],
            checks=[{"operation": pending.operation, **result}],
            invalid=[],
            deadline=frame.deadline,
        )
    return result


def _resolve_input(pending: PendingAction, tree: AXTree, frame: Frame) -> dict[str, Any]:
    expected = pending.expected
    node = tree.find_field(expected.get("field_key"))
    if node is None:
        return {"status": "unreadable", "detail": "the edited field is not visible",
                "expected": expected.get("value")}
    actual = tree.control_value(node)
    target = expected.get("value")
    if actual is None or target is None:
        return {"status": "unreadable", "detail": "the AX does not expose the live field value",
                "expected": target, "actual": actual}
    if _norm(actual) == _norm(target):
        return {"status": "changed", "detail": "input matches exactly; not yet persisted",
                "expected": target, "actual": actual}
    baseline = expected.get("baseline")
    if baseline is not None and _norm(actual) == _norm(baseline):
        return {"status": "no_change", "detail": "typing had no effect",
                "expected": target, "actual": actual}
    return {"status": "mismatch", "detail": "input differs from the complete expected value",
            "expected": target, "actual": actual}


def _resolve_ensure(pending: PendingAction, tree: AXTree, frame: Frame) -> dict[str, Any]:
    expected = pending.expected
    kind = expected.get("control_kind")
    object_key = expected.get("object_key")
    candidates = tree.controls_for(kind, object_key) if kind else []
    if not candidates:
        return {"status": "unknown", "detail": "target control is not visible"}
    node = candidates[0]
    actual = node.state
    desired = expected.get("desired")
    if actual is None:
        return {"status": "unknown", "detail": "control state is not exposed"}
    if actual == desired:
        return {"status": "confirmed", "detail": "target state is now true"
                if desired else "target state is now false",
                "actual": actual, "key": f"{kind}:{object_key}"}
    return {"status": "no_change", "detail": "control state did not change",
            "actual": actual}


def _resolve_commit(pending: PendingAction, tree: AXTree, frame: Frame) -> dict[str, Any]:
    expected = pending.expected
    values = [value for value in expected.get("values", ()) if isinstance(value, str) and value]
    business = tree.business_texts()
    # Whole submitted values only: OLD+NEW must never prove replacement NEW.
    present = [value for value in values if any(_norm(text) == _norm(value) for text in business)]
    error = _error_text(tree)
    source = pending.source
    url_changed = str(source.get("url", "")) != frame.url
    same_origin = frame.url.split('/')[0:3] == str(source.get("url", "")).split('/')[0:3]
    if not same_origin:
        return {"status": "unknown", "detail": "result belongs to another origin"}
    if values:
        was_present = all(any(_norm(text) == _norm(value) for text in expected.get("baseline_texts", ()))
                          for value in values)
        if len(present) == len(values) and not was_present:
            return {"status": "confirmed", "detail": "all submitted values are visible outside the form",
                    "actual": values}
        # Only a matching editable field can prove a definite wrong saved value.
        # A toast or unrelated page containing 'error/required' cannot release a write.
        return {"status": "unknown",
                "detail": "business value is not visible outside the form; draft or toast is not persistence",
                "expected": values, "actual": present}
    marker = tree.success_marker()
    if marker and not error and url_changed and _business_changed(expected.get("baseline_texts", ()), business):
        return {"status": "confirmed", "detail": "confirmation page changed after submission",
                "actual": marker}
    return {"status": "unknown",
            "detail": "no business result or definite error is visible yet"}


def _business_changed(before: Any, after: list[str]) -> bool:
    if not isinstance(before, (list, tuple)):
        return False
    old = {_norm(item) for item in before if isinstance(item, str)}
    new = {_norm(item) for item in after}
    return old != new


def _error_text(tree: AXTree) -> str | None:
    for text in tree.visible_texts():
        lowered = text.casefold()
        if any(word in lowered for word in _ERROR_WORDS):
            return text
    return None


def stop_allowed(state: TaskState) -> bool:
    pending = state.pending_actions()
    if any(item.status == "unknown" for item in pending):
        return False
    return not state.unresolved


def feedback(state: TaskState) -> str:
    parts: list[str] = []
    pending = state.pending_actions()
    unknown = [item for item in pending if item.status == "unknown"]
    if unknown:
        item = unknown[0]
        parts.append(
            "UNKNOWN WRITE: the previous " + item.operation + " has no confirmed business "
            "result. Only read-only query/navigation or drafts are allowed; do not resend "
            "the same comment/order/post even with another element id."
        )
    result = state.last_result
    if result:
        status = result.get("status", "unknown")
        detail = result.get("detail", "")
        if status == "changed":
            parts.append("Last local readback: changed. " + detail)
        elif status == "confirmed":
            parts.append("Last local readback: changed/confirmed. " + detail)
        elif status == "no_change":
            parts.append("Last local readback: no_change. " + detail)
        elif status == "mismatch":
            parts.append("Last local readback: mismatch. " + detail)
        elif status == "failed":
            parts.append("Last local readback: definite error. " + detail)
        elif status == "blocked":
            parts.append("Action blocked locally: " + detail)
        elif status == "read":
            parts.append("Last action was read-only. " + detail)
        elif status == "unreadable":
            parts.append("Last local readback: unknown (AX has no live value). " + detail)
        elif status == "unknown":
            parts.append("Last local readback: unknown. " + detail)
    completed = state.completed[-6:]
    if completed:
        labels = []
        for item in completed:
            labels.append(f"{item.get('kind')} {item.get('key')}")
        parts.append("Confirmed locally: " + "; ".join(labels))
    if state.unresolved and not unknown:
        parts.append("Do not stop yet: a local effect is still unconfirmed. Query the "
                     "business page or repair only the affected value.")
    return "\n".join(parts)[:1800]


def pending_summary(state: TaskState) -> dict[str, Any] | None:
    pending = state.pending_actions()
    if not pending:
        return None
    item = pending[0]
    return {
        "operation": item.operation,
        "status": item.status,
        "action": item.action,
        "expected": {
            key: value for key, value in item.expected.items()
            if key in {"kind", "control_kind", "object_key", "desired", "values", "value"}
        },
    }


def remember_completed(state: TaskState, operation: PendingAction, result: dict[str, Any]) -> None:
    expected = operation.expected
    if operation.operation == "ensure":
        key = f"{expected.get('control_kind')}:{expected.get('object_key')}"
        state.add_completed("ensure", key, result)
        return
    if operation.operation == "commit":
        key = f"{expected.get('commit_kind')}:{expected.get('object_key')}:{_values_key(tuple(expected.get('values', ())))}"
        state.add_completed("commit", key, result)
        return
    state.add_completed(operation.operation, operation.pending_id, result)


def remember_failed(state: TaskState, operation: PendingAction, result: dict[str, Any]) -> None:
    expected = operation.expected
    if operation.operation == "ensure":
        state.add_failed(f"{expected.get('control_kind')}:{expected.get('object_key')}", result)
    elif operation.operation == "commit":
        state.add_failed(f"commit:{expected.get('object_key')}", result)


def _values_key(values: tuple[str, ...]) -> str:
    if not values:
        return "-"
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()[:12]


def _norm(value: str) -> str:
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def _clip(value: str, limit: int = 280) -> str:
    text = str(value).replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


__all__ = [
    "Block", "Plan", "feedback", "guard", "pending_summary", "plan",
    "register", "remember_completed", "remember_failed", "resolve", "stop_allowed",
]
