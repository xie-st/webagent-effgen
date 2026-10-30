"""M2 action classification, pending registration and read-only write guard.

The runtime registers the expected business effect before returning any action.
A later observation confirms it.  Until an unknown write is settled, only
decidable reads, navigation, selection, clearing and text drafts are allowed;
changing the element id does not make a second submission legal.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4
from urllib.parse import unquote, urlsplit, parse_qs

from .contracts import Frame, GoalCheck, PendingAction
from .state import TaskState
from . import verify

_READ_ONLY_NAMES = (
    "filter",
    "sort",
    "search",
    "next",
    "previous",
    "prev",
    "page",
    "view",
    "show",
    "expand",
    "collapse",
    "more",
    "back",
    "cancel",
    "dismiss",
    "close",
    "preview",
    "help",
    "刷新",
    "筛选",
    "排序",
    "搜索",
    "下一页",
    "上一页",
    "查看",
    "展开",
    "收起",
    "取消",
    "关闭",
    "返回",
)


class WriteGuardError(ValueError):
    """A write was requested while an earlier write result is still unknown."""


class DuplicateWriteError(ValueError):
    """A verified one-shot goal was about to be written again."""


@dataclass(frozen=True)
class ActionInfo:
    action: str
    kind: str
    element_id: str | None = None
    role: str | None = None
    name: str = ""
    url: str | None = None
    is_write: bool = False
    is_read: bool = True
    is_draft: bool = False
    operation: str = "read"

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "kind": self.kind,
            "element_id": self.element_id,
            "role": self.role,
            "name": self.name,
            "url": self.url,
            "is_write": self.is_write,
            "is_read": self.is_read,
            "is_draft": self.is_draft,
            "operation": self.operation,
        }


def _read_name(value: str) -> bool:
    """Positive read evidence only: whole words, never a substring.

    ``view`` inside ``review`` or ``cancel`` inside ``cancel order`` must not
    turn a submit/delete control into a read.  Callers check commit semantics
    first, so this is only reached when no submit wording is present.
    """
    lowered = value.casefold()
    for word in _READ_ONLY_NAMES:
        if word.isascii():
            if re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", lowered):
                return True
        elif word in lowered:
            return True
    return False


_COMMIT_VOTE_WORDS = (
    "upvote",
    "downvote",
    "vote",
    "thumbs up",
    "thumbs down",
    "retract",
    "undo",
    "unvote",
    "点赞",
    "踩",
    "投票",
)
_ORDER_WORDS = (
    "checkout",
    "order",
    "reorder",
    "buy again",
    "结账",
    "订单",
    "下单",
    "重购",
)
_CART_WORDS = ("cart", "basket", "购物车", "加入购物车")

# Explicit UI state, not business commit: a popup menu, a tab, or a disclosed
# section opens content; the write happens later through a real form control.
_POPUP_MENU = re.compile(r"\bhasPopup:\s*menu\b", re.I)
_EXPANDED_CONTROL = re.compile(r"\bexpanded:\s*(?:true|false)\b", re.I)

# Links to a create/reply/edit form are navigation.  Their labels often match
# commit words ("Submit", "Reply", "Create post"), but clicking only opens the
# editor; submitting that editor is a separate control.
_COMPOSE_URL = re.compile(
    r"(?:^|/)(?:submit|new|create|reply|compose|edit)(?:[/_\-]|$)"
    r"|[?&](?:reply|quote|compose|edit|new)(?:=|&|$)",
    re.I,
)

# These links perform a state change through their href itself: votes, cart
# changes, removal/reordering, cancellation, checkout and similar actions.
_DANGEROUS_URL = re.compile(
    r"(?:^|[/_\-])(?:delete|remove|re-?order|buy[-_ ]?again|checkout|"
    r"cancel(?:lation)?|upvote|downvote|vote|like|subscribe|unsubscribe|"
    r"follow|unfollow|save|purchase|add(?:[-_/]?(?:to[-_/]?)?cart)?)"
    r"(?=[/_\-?&=.]|$)|cart[-_/]add",
    re.I,
)
_DANGEROUS_NAME = re.compile(
    r"\b(?:delete|remove|re-?order|buy\s+again|checkout|place\s+order|"
    r"cancel\s+(?:order|subscription|booking)|upvote|downvote|vote|"
    r"subscribe|unsubscribe|follow|unfollow)\b|"
    r"删除|取消订单|重购|退订|下单|投票|点赞|踩",
    re.I,
)


def _commit_control(atom) -> bool:
    return any(word in f"{atom.name} {atom.raw}".casefold() for word in verify._COMMIT_WORDS)


def _ui_navigation(atom) -> bool:
    return atom.role == "tab" or bool(_POPUP_MENU.search(atom.raw))


def _expanded_control(atom) -> bool:
    return bool(_EXPANDED_CONTROL.search(atom.raw))


def _dangerous_url(url: str | None) -> bool:
    parsed = urlsplit(unquote(url or ""))
    if _DANGEROUS_URL.search(parsed.path):
        return True
    for key, values in parse_qs(parsed.query).items():
        if key.casefold() in {"action", "do", "op", "operation", "cmd"}:
            if any(_DANGEROUS_URL.search("/" + value) or re.match(
                r"^(?:delete|remove|save|submit|reorder|upvote|downvote|"
                r"subscribe|unsubscribe|follow|unfollow|add_to_cart)(?:$|[_/-])",
                value, re.I,
            ) for value in values):
                return True
    return False


def _dangerous_link(atom) -> bool:
    return bool(_DANGEROUS_NAME.search(atom.name)) or _dangerous_url(atom.url)


def _compose_target(url: str | None) -> bool:
    return bool(_COMPOSE_URL.search(unquote(url or "")))


def classify_action(action: str, frame: Frame) -> ActionInfo:
    """Classify click/Enter conservatively; never relabel a potential submit as a read."""
    view = verify.parse_ax(frame)
    if action.startswith("stop ["):
        return ActionInfo(action, "stop", is_read=False, operation="stop")
    if action in {"go_back", "go_forward", "scroll [up]", "scroll [down]"}:
        return ActionInfo(action, "navigate", is_read=True, operation="read")
    if action.startswith("goto ["):
        target = action[len("goto ["):-1]
        if _dangerous_url(target):
            return ActionInfo(action, "navigate", url=target,
                              is_write=True, is_read=False, operation="commit")
        return ActionInfo(action, "navigate", url=target, is_read=True, operation="read")
    if action.startswith("hover ["):
        return ActionInfo(action, "hover", is_read=True, operation="read")
    click = re.fullmatch(r"click \[(\d+)\]", action)
    if click:
        element_id = click.group(1)
        atom = view.by_id.get(element_id)
        role = atom.role if atom is not None else None
        name = atom.name if atom is not None else ""
        url = atom.url if atom is not None else None
        if role in {"textbox", "searchbox", "combobox", "spinbutton", "slider"}:
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_read=False, is_draft=True, operation="draft")
        if role in {"option", "checkbox", "radio"}:
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_read=False, is_draft=True, operation="draft")
        if _dangerous_link(atom):
            # Explicit business mutation wins over popup/tab metadata. A
            # split button or link can both expose a menu and perform a write.
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_write=True, is_read=False, operation="commit")
        if _ui_navigation(atom):
            # A popup-menu opener or tab only opens UI state.  Committing is a
            # later form control, so this must not create a phantom pending.
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_read=True, operation="read")
        if role == "link":
            # Dangerous links perform the action in the href itself and always
            # win, even when their label also contains read wording.
            if _dangerous_link(atom):
                return ActionInfo(action, "click", element_id, role, name, url,
                                  is_write=True, is_read=False, operation="commit")
            if _expanded_control(atom):
                return ActionInfo(action, "click", element_id, role, name, url,
                                  is_read=True, operation="read")
            if url and url != frame.url and _compose_target(url):
                # "Submit"/"Reply"/"Edit" links that open a create or edit form
                # are navigation; the editor's own button is the real write.
                return ActionInfo(action, "click", element_id, role, name, url,
                                  is_read=True, operation="read")
            # Resource navigation is not a submission merely because an order
            # or post noun occurs in its label/URL.
            read_resource = re.fullmatch(
                r"(?:my\s+)?(?:orders?|order history|cart|shopping cart|posts?|comments?)"
                r"|edit\s+(?:post|profile|bio|biography|comment)", name.strip(), re.I,
            )
            if read_resource and url:
                return ActionInfo(action, "click", element_id, role, name, url,
                                  is_read=True, operation="read")
            if _commit_control(atom):
                return ActionInfo(action, "click", element_id, role, name, url,
                                  is_write=True, is_read=False, operation="commit")
            if _read_name(name):
                return ActionInfo(action, "click", element_id, role, name, url,
                                  is_read=True, operation="read")
            if url and url != frame.url:
                # URL-change alone is not read evidence; this branch is only
                # reached after the control name and URL were cleared for
                # submit/delete wording above.
                return ActionInfo(action, "click", element_id, role, name, url,
                                  is_read=True, operation="read")
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_write=True, is_read=False, operation="commit")
        if _commit_control(atom):
            # Commit semantics win before any read word, so "Preview & Submit"
            # and "Review order" are writes, never reads.
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_write=True, is_read=False, operation="commit")
        if _expanded_control(atom) and role in {"button", "menuitem"}:
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_read=True, operation="read")
        if _read_name(name):
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_read=True, operation="read")
        if role in {"button", "menuitem", "tab"}:
            return ActionInfo(action, "click", element_id, role, name, url,
                              is_write=True, is_read=False, operation="commit")
        return ActionInfo(action, "click", element_id, role, name, url,
                          is_write=True, is_read=False, operation="commit")
    type_action = re.fullmatch(r"type \[(\d+)\] \[(.*)\] \[([01])\]", action, flags=re.S)
    if type_action:
        element_id = type_action.group(1)
        atom = view.by_id.get(element_id)
        enter = type_action.group(3) == "1"
        role = atom.role if atom is not None else None
        name = atom.name if atom is not None else ""
        return ActionInfo(
            action,
            "type",
            element_id,
            role,
            name,
            atom.url if atom is not None else None,
            is_write=enter,
            is_read=False,
            is_draft=True,
            operation="submit" if enter else "draft",
        )
    press = re.fullmatch(r"press \[(.*)\]", action, flags=re.S)
    if press:
        keys = press.group(1).casefold()
        submit = any(key in keys for key in ("enter", "return", "numpadenter"))
        return ActionInfo(
            action,
            "press",
            None,
            None,
            keys,
            None,
            is_write=submit,
            is_read=not submit,
            operation="submit" if submit else "read",
        )
    return ActionInfo(action, "unknown", is_write=True, is_read=False, operation="unknown")


def _current_values(frame: Frame) -> list[tuple[str, str, str]]:
    view = verify.parse_ax(frame)
    values: list[tuple[str, str, str]] = []
    for atom, value in view.form_values():
        values.append((atom.element_id, atom.role, value))
    return values


def _draft_texts(state: TaskState) -> list[str]:
    values = []
    for value in state.drafts.values():
        if isinstance(value, dict) and isinstance(value.get("text"), str):
            values.append(value["text"])
    return values


def _select_goals(
    frame: Frame,
    state: TaskState,
    info: ActionInfo,
) -> list[GoalCheck]:
    unverified = [
        goal for goal in state.goal_checks
        if goal.status not in {"verified"}
    ]
    if not unverified:
        return []
    contexts = _draft_texts(state) + [value for _, _, value in _current_values(frame)]
    contexts.append(info.name)
    action_text = f"{info.action} {info.name}".casefold()
    selected: list[GoalCheck] = []
    for goal in unverified:
        if goal.kind in {"exact_equal", "exact_append"}:
            target = str(goal.target)
            if any(target in value for value in contexts):
                selected.append(goal)
            elif goal.kind == "exact_append" and goal.baseline is not None:
                selected.append(goal)
            elif len(unverified) == 1 and info.is_write:
                selected.append(goal)
        elif goal.kind in {"count_once", "count_per_object"} and (
            info.operation == "submit"
            or any(word in action_text for word in _COMMIT_VOTE_WORDS)
            or (len(unverified) == 1 and info.is_write)
        ):
            selected.append(goal)
        elif goal.kind == "state_true" and (
            any(word in action_text for word in ("subscribe", "follow", "订阅", "关注"))
            or len(unverified) == 1
        ):
            selected.append(goal)
        elif goal.kind == "item_exact" and (
            any(word in action_text for word in _CART_WORDS)
            or (len(unverified) == 1 and info.is_write)
        ):
            selected.append(goal)
        elif goal.kind == "order_once" and (
            any(word in action_text for word in _ORDER_WORDS)
            or (len(unverified) == 1 and info.is_write)
        ):
            selected.append(goal)
    # Keep original task order and remove duplicates.
    seen: set[str] = set()
    ordered = []
    for goal in state.goal_checks:
        if goal in selected and goal.goal_id not in seen:
            ordered.append(goal)
            seen.add(goal.goal_id)
    return ordered


def _capture_append_baseline(
    frame: Frame,
    state: TaskState,
    info: ActionInfo,
    text: str,
) -> None:
    if info.element_id is None:
        return
    view = verify.parse_ax(frame)
    atom = view.by_id.get(info.element_id)
    current = view.control_value(atom) if atom is not None else ""
    for goal in state.goal_checks:
        if goal.kind != "exact_append" or goal.status == "verified":
            continue
        target = str(goal.target)
        if target in current and goal.baseline is None:
            goal.baseline = current
        elif goal.baseline is None and text and (target in text or current):
            goal.baseline = current


def register_action(
    frame: Frame,
    state: TaskState,
    action: str,
    *,
    telemetry=None,
) -> PendingAction | None:
    """Record draft facts or a pending business effect before returning action."""
    info = classify_action(action, frame)
    if info.kind == "type":
        match = re.fullmatch(r"type \[(\d+)\] \[(.*)\] \[([01])\]", action, flags=re.S)
        if match:
            element_id, text = match.group(1), match.group(2)
            _capture_append_baseline(frame, state, info, text)
            state.set_draft(
                element_id,
                {
                    "text": text,
                    "step": frame.step,
                    "url": frame.url,
                    "observation_version": frame.observation_version,
                },
            )
    if not info.is_write:
        pending = state.pending_for(frame.tab)
        if pending is not None and pending.status == "unknown" and info.is_read:
            if action.startswith("goto [") or (info.kind == "click" and info.role == "link"):
                pending.expected = {**pending.expected, "readback_step": frame.step}
        return None
    rewritten = _verified_write(state, info)
    if rewritten is not None:
        raise DuplicateWriteError(
            "This requirement is already verified in business state; do not write it again."
        )
    selected = _select_goals(frame, state, info)
    view = verify.parse_ax(frame)
    atom = view.by_id.get(info.element_id) if info.element_id is not None else None
    object_id = verify.object_key(view, atom, frame.url)
    duplicate_object = _recorded_object(state, object_id)
    if duplicate_object is not None:
        raise DuplicateWriteError(
            "This object already has a confirmed write; do not write it again "
            "or undo it."
        )
    expected: dict[str, Any] = {
        "operation": info.operation,
        "object_key": object_id,
        "targets": [
            {
                "goal_id": goal.goal_id,
                "kind": goal.kind,
                "target": goal.target,
                "baseline": goal.baseline,
                "expected_value": (
                    (str(goal.baseline).rstrip() + "\n" + str(goal.target))
                    if goal.kind == "exact_append" and goal.baseline is not None
                    else goal.target
                ),
            }
            for goal in selected
        ],
        "requires_business_readback": True,
    }
    pending = PendingAction(
        pending_id=uuid4().hex,
        tab=frame.tab,
        step=frame.step,
        action=action,
        operation=info.operation,
        goal_ids=tuple(goal.goal_id for goal in selected),
        source={
            "run_id": frame.run_id,
            "step": frame.step,
            "url": frame.url,
            "observation_version": frame.observation_version,
            "ax_fingerprint": view.fingerprint,
            "element_id": info.element_id,
            "element_role": info.role,
            "element_name": info.name,
            "element_url": info.url,
            "object_key": object_id,
        },
        expected=expected,
        status="unknown",
    )
    state.set_pending(pending)
    if telemetry is not None:
        telemetry.pending(
            step=frame.step,
            url=frame.url,
            action=action,
            pending=pending.as_dict(),
            expected=expected,
        )
        telemetry.progress(
            step=frame.step,
            url=frame.url,
            goals=[goal.as_dict() for goal in state.goal_checks],
            source="after_action_registration",
        )
    return pending


def _guard_telemetry(
    telemetry,
    *,
    frame: Frame,
    pending: PendingAction | None,
    action: str,
    allowed: bool,
    reason: str,
) -> None:
    if telemetry is None:
        return
    telemetry.write_guard(
        step=frame.step,
        url=frame.url,
        action=action,
        pending_id=pending.pending_id if pending is not None else None,
        allowed=allowed,
        reason=reason,
    )


def _recorded_object(state: TaskState, key: str) -> GoalCheck | None:
    if not key:
        return None
    for goal in state.goal_checks:
        if goal.kind in {"count_per_object", "count_once"} and key in goal.objects:
            return goal
    return None


def _verified_write(state: TaskState, info: ActionInfo) -> GoalCheck | None:
    """Return a verified goal this action would rewrite, if any."""
    if not info.is_write:
        return None
    text = f"{info.action} {info.name}".casefold()
    retracts = any(
        word in text for word in ("retract", "undo", "unvote", "remove vote", "take back")
    )
    for goal in state.goal_checks:
        if goal.status != "verified":
            continue
        if goal.kind in {"count_once", "count_per_object"} and (
            retracts or any(word in text for word in _COMMIT_VOTE_WORDS)
        ):
            return goal
        if goal.kind == "state_true" and any(
            word in text for word in ("subscribe", "follow", "订阅", "关注")
        ):
            return goal
        if goal.kind == "item_exact" and any(word in text for word in _CART_WORDS):
            return goal
        if goal.kind == "order_once" and any(word in text for word in _ORDER_WORDS):
            return goal
    if retracts and state.goal_checks:
        # A retract/undo control always targets a state that a previous write
        # may have produced; never allow it while any goal tracks objects.
        if any(goal.objects for goal in state.goal_checks):
            return state.goal_checks[0]
    if state.goal_checks and all(goal.status == "verified" for goal in state.goal_checks):
        return state.goal_checks[0]
    return None


def guard_action(
    frame: Frame,
    state: TaskState,
    action: str,
    *,
    telemetry=None,
) -> ActionInfo:
    """Raise before a write that would overwrite an unknown pending result."""
    info = classify_action(action, frame)
    pending = state.pending_for(frame.tab)
    if info.is_write and info.kind in {"click", "press"}:
        replacements = [goal for goal in state.goal_checks
                        if goal.kind == "exact_equal" and goal.status != "verified"]
        if len(replacements) == 1 and str(replacements[0].target) in _draft_texts(state):
            goal = replacements[0]
            view = verify.parse_ax(frame)
            for atom, value in view.form_values():
                if (verify._field_scope_ok(view, atom, goal.field)
                        and verify._normalize_text(value) != verify._normalize_text(goal.target)):
                    raise ValueError(
                        "Before saving, replace the WHOLE field: click the field, "
                        "press [Ctrl+A], then type the requested value. "
                        "The observed input is not exactly the target."
                    )
    if pending is not None and pending.status == "unknown":
        if info.is_write:
            _guard_telemetry(
                telemetry, frame=frame, pending=pending, action=action,
                allowed=False, reason="unknown write requires read-only verification",
            )
            raise WriteGuardError(
                "The previous write result is unknown. Do not submit it again, "
                "even with a different element id. Use a read-only query or "
                "navigation to confirm or disprove the result first."
            )
        _guard_telemetry(
            telemetry, frame=frame, pending=pending, action=action,
            allowed=True, reason="read-only/draft while pending effect is unknown",
        )
    rewritten = _verified_write(state, info)
    if rewritten is not None:
        raise DuplicateWriteError(
            "The target requirement is already verified in business state; "
            "do not rewrite it."
        )
    if info.is_write:
        view = verify.parse_ax(frame)
        atom = view.by_id.get(info.element_id) if info.element_id is not None else None
        if _recorded_object(state, verify.object_key(view, atom, frame.url)) is not None:
            raise DuplicateWriteError(
                "This object already has a confirmed write; do not write it again "
                "or undo it."
            )
    return info


def progress(state: TaskState) -> dict[str, int]:
    goals = state.goal_checks
    return {
        "total": len(goals),
        "verified": sum(1 for goal in goals if goal.status == "verified"),
        "failed": sum(1 for goal in goals if goal.status == "failed"),
        "unknown": sum(1 for goal in goals if goal.status == "unknown"),
        "stale": sum(1 for goal in goals if goal.status == "stale"),
        "pending": sum(1 for goal in goals if goal.status == "pending"),
    }


def feedback(frame: Frame, state: TaskState) -> str:
    """Compact M2 feedback included in the next decision context."""
    parts: list[str] = []
    pending = state.pending_for(frame.tab)
    if pending is not None and pending.status == "unknown":
        parts.append(
            "UNKNOWN WRITE: the previous submission's effect is unconfirmed. "
            "Only read-only query/navigation, selection, clearing or drafts are "
            "allowed now. Do not resubmit the same write or a same-purpose write "
            "with another element id. Confirm the business value first."
        )
    elif pending is not None and pending.status == "failed":
        parts.append(
            "The last write had no confirmed effect. Recover only the affected "
            "requirement; keep every already verified goal."
        )
    progress_value = progress(state)
    if progress_value["total"]:
        remaining = [
            goal.description for goal in state.goal_checks
            if goal.status not in {"verified"}
        ]
        if remaining:
            parts.append(
                f"Verified {progress_value['verified']}/{progress_value['total']} "
                "original-task requirements. Unverified: " + "; ".join(remaining)
            )
        else:
            parts.append(
                "All original-task requirements are verified in business state. "
                "Do not rewrite them; stop only with the observed result."
            )
    return "\n".join(parts)


def recovery_plan(state: TaskState) -> dict[str, Any]:
    """Describe the local continuation without discarding the verified prefix."""
    verified = [goal.as_dict() for goal in state.goal_checks if goal.status == "verified"]
    remaining = [goal.as_dict() for goal in state.goal_checks if goal.status != "verified"]
    return {
        "verified_prefix": verified,
        "remaining": remaining,
        "preserve_verified": True,
        "local_only": True,
    }


__all__ = [
    "ActionInfo",
    "DuplicateWriteError",
    "WriteGuardError",
    "classify_action",
    "feedback",
    "guard_action",
    "progress",
    "recovery_plan",
    "register_action",
]
