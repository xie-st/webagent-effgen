"""M2 goal extraction, exact evidence verification and stop judging.

The task text is the authority.  Goal checks are extracted deterministically
where exact values are known; a model check is used only when the AX cannot
settle a fact.  Model output is accepted only when it cites real current AX
lines and the original task quote, and exact values are recompared here rather
than trusting a model's ``confirmed`` claim.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlsplit

from .contracts import Frame, GoalCheck, GoalEvidence, PendingAction
from .state import TaskState, identity_key

MAX_VERIFY_OUTPUT = 12_000
_QUOTED = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|‘([^’\n]+)’')
_LINE = re.compile(r"^(\s*)\[(\d+)\]\s+([^\s]+)\s*(.*)$")
_ATTR_NAME = re.compile(r"'((?:[^'\\]|\\.)*)'")
_FORM_ROLES = frozenset(
    {
        "textbox",
        "searchbox",
        "combobox",
        "option",
        "checkbox",
        "radio",
        "spinbutton",
        "slider",
        "listbox",
        "menuitem",
    }
)
_COMMIT_WORDS = (
    "add to cart",
    "add",
    "checkout",
    "comment",
    "confirm",
    "create",
    "delete",
    "downvote",
    "follow",
    "like",
    "order",
    "post",
    "publish",
    "remove",
    "reply",
    "save",
    "send",
    "submit",
    "subscribe",
    "unsubscribe",
    "update",
    "upvote",
    "vote",
    "下单",
    "取消订单",
    "保存",
    "发布",
    "回复",
    "提交",
    "点赞",
    "确认",
    "订阅",
    "购买",
    "删除",
    "发送",
)
_VALUE_KINDS = frozenset({"exact_equal", "exact_append"})
_EXACT_KINDS = frozenset({"exact_equal", "exact_append", "item_exact"})
# Semantic and per-object checks must also cite business (not draft/status) AX
# lines; the evidence shape is stricter than a bare model claim.
_EVIDENCE_KINDS = frozenset(_EXACT_KINDS | {"semantic", "count_per_object"})
_KNOWN_KINDS = frozenset(
    _EVIDENCE_KINDS | {"count_once", "state_true", "order_once"}
)
_VOTE_WORDS = (
    "upvote",
    "downvote",
    "vote",
    "thumbs up",
    "thumbs down",
    "点赞",
    "踩",
    "投票",
)
_VOTE_TOGGLED_WORDS = (
    "retract",
    "undo",
    "unvote",
    "remove vote",
    "remove upvote",
    "remove downvote",
    "take back",
    "已踩",
    "已赞",
)
# Quantity, ordering, identity, date/cancellation and multi-object language is a
# real requirement even when no exact field value can be parsed.  It is kept as
# a semantic goal rather than silently dropped.
_SCOPE_MARKERS = re.compile(
    r"\b(?:top|first|last|newest|oldest|latest|least|most|cheapest|"
    r"lowest|highest|minimum|maximum|at\s+least|at\s+most|capacity|price|"
    r"ever|all\s+time|sorted|cancelled|canceled|cancellation|"
    r"subreddit|focused\s+on|related\s+to|topic|"
    r"my\s+(?:post|order|comment|review|thread)\s+(?:on|about))\b|"
    r"最(?:新|旧|低|高|便宜|贵|近)|前\s*\d|至少|至多|容量|价格|"
    r"取消|板块|主题|相关",
    re.I,
)
_MULTI_OBJECT = re.compile(
    r"\b(?:top|first|last)\s+(\d+)\b|\b(\d+)\s+(?:posts?|items?|products?|"
    r"comments?|articles?)\b",
    re.I,
)


class GoalIncompleteError(ValueError):
    """A success stop tried to skip an original-task requirement."""


@dataclass(frozen=True)
class AXAtom:
    line_no: int
    element_id: str
    role: str
    name: str
    raw: str
    indent: int
    url: str | None
    checked: bool | None
    selected: bool | None
    focused: bool | None
    inside_alert: bool
    inside_form: bool
    descendants: tuple["AXAtom", ...] = ()


class AXView:
    """Small, lossless view over the current accessibility tree."""

    def __init__(self, frame: Frame):
        self.frame = frame
        self.lines = frame.ax.splitlines()
        self.atoms: list[AXAtom] = []
        self.by_id: dict[str, AXAtom] = {}
        self.by_line: dict[int, AXAtom] = {}
        self._parse()

    def _parse(self) -> None:
        parsed: list[dict[str, Any]] = []
        for index, raw in enumerate(self.lines, start=1):
            match = _LINE.match(raw)
            if not match:
                continue
            indent = len(match.group(1).expandtabs(8))
            element_id, role, rest = match.group(2), match.group(3), match.group(4)
            name_match = _ATTR_NAME.search(rest)
            name = name_match.group(1) if name_match else ""
            name = name.replace("\\'", "'").replace("\\\\", "\\")
            url_match = re.search(r"\burl:\s*(\S+)", rest)
            checked_match = re.search(r"\bchecked:\s*(true|false)", rest)
            selected_match = re.search(r"\bselected:\s*(true|false)", rest)
            focused_match = re.search(r"\bfocused:\s*(true|false)", rest)
            parsed.append(
                {
                    "line_no": index,
                    "element_id": element_id,
                    "role": role,
                    "name": name,
                    "raw": raw,
                    "indent": indent,
                    "url": url_match.group(1) if url_match else None,
                    "checked": (
                        checked_match.group(1) == "true" if checked_match else None
                    ),
                    "selected": (
                        selected_match.group(1) == "true" if selected_match else None
                    ),
                    "focused": (
                        focused_match.group(1) == "true" if focused_match else None
                    ),
                }
            )
        # Ancestor state and descendant text slices.
        for position, item in enumerate(parsed):
            ancestors: list[dict[str, Any]] = []
            for previous in reversed(parsed[:position]):
                if previous["indent"] < item["indent"]:
                    ancestors.append(previous)
                    if previous["indent"] == 0:
                        break
            descendants: list[dict[str, Any]] = []
            for following in parsed[position + 1:]:
                if following["indent"] <= item["indent"]:
                    break
                descendants.append(following)
            atom = AXAtom(
                line_no=item["line_no"],
                element_id=item["element_id"],
                role=item["role"],
                name=item["name"],
                raw=item["raw"],
                indent=item["indent"],
                url=item["url"],
                checked=item["checked"],
                selected=item["selected"],
                focused=item["focused"],
                inside_alert=any(entry["role"] == "alert" for entry in ancestors),
                inside_form=any(entry["role"] in _FORM_ROLES for entry in ancestors),
                descendants=tuple(
                    AXAtom(
                        line_no=entry["line_no"],
                        element_id=entry["element_id"],
                        role=entry["role"],
                        name=entry["name"],
                        raw=entry["raw"],
                        indent=entry["indent"],
                        url=entry["url"],
                        checked=entry["checked"],
                        selected=entry["selected"],
                        focused=entry["focused"],
                        inside_alert=(
                            item["role"] == "alert"
                            or any(a["role"] == "alert" for a in ancestors)
                        ),
                        inside_form=any(
                            a["role"] in _FORM_ROLES
                            for a in (ancestors + [item])
                        ),
                    )
                    for entry in descendants
                ),
            )
            self.atoms.append(atom)
            self.by_id[atom.element_id] = atom
            self.by_line[atom.line_no] = atom

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.frame.ax.encode("utf-8")).hexdigest()

    def current_ids(self) -> tuple[str, ...]:
        return tuple(atom.element_id for atom in self.atoms)

    def control_value(self, atom: AXAtom) -> str:
        values = [
            child.name
            for child in atom.descendants
            if child.role == "StaticText" and child.name
        ]
        return "\n".join(values) if values else atom.name

    def form_values(self) -> list[tuple[AXAtom, str]]:
        values: list[tuple[AXAtom, str]] = []
        for atom in self.atoms:
            if atom.role in {"textbox", "searchbox", "combobox", "spinbutton"}:
                values.append((atom, self.control_value(atom)))
        return values

    def business_texts(self) -> list[AXAtom]:
        return [
            atom
            for atom in self.atoms
            if atom.role in {"StaticText", "heading", "paragraph"}
            and atom.name
            and not atom.inside_alert
            and not atom.inside_form
        ]

    def commit_control(self, atom: AXAtom) -> bool:
        text = f"{atom.name} {atom.raw}".casefold()
        return any(word in text for word in _COMMIT_WORDS)

    def quote_valid(self, line: int, quote: str) -> bool:
        if not isinstance(line, int) or not isinstance(quote, str) or not quote:
            return False
        if line < 1 or line > len(self.lines):
            return False
        return quote in self.lines[line - 1]


def _protected_split(task: str) -> list[str]:
    spans: list[str] = []
    pieces: list[str] = []
    cursor = 0
    for match in _QUOTED.finditer(task):
        pieces.append(task[cursor:match.start()])
        token = f"\x00{len(spans)}\x00"
        spans.append(match.group(0))
        pieces.append(token)
        cursor = match.end()
    pieces.append(task[cursor:])
    protected = "".join(pieces)
    separator = re.compile(
        r"(?:[;；]|(?:\s+(?:and\s+then|and|then)\s+)|，|并且|然后|同时|"
        r"并(?=[把将发订点回在给提交购买添加关注创建修改更保删加]))",
        flags=re.I,
    )
    clauses = []
    for piece in separator.split(protected):
        for index, quote in enumerate(spans):
            piece = piece.replace(f"\x00{index}\x00", quote)
        piece = piece.strip(" \t\r\n,，;；")
        if piece:
            clauses.append(piece)
    return clauses


def _first_quote(text: str) -> str | None:
    match = _QUOTED.search(text)
    if not match:
        return None
    return next(group for group in match.groups() if group is not None).strip()


def _field(text: str) -> str | None:
    lowered = text.casefold()
    for marker, name in (
        ("biography", "bio"),
        ("bio", "bio"),
        ("简介", "bio"),
        ("title", "title"),
        ("标题", "title"),
        ("body", "body"),
        ("正文", "body"),
        ("comment", "comment"),
        ("回复", "reply"),
        ("reply", "reply"),
    ):
        if marker in lowered:
            return name
    return None


def _goal_id(index: int) -> str:
    return f"goal-{index}"


def _add_goal(
    goals: list[GoalCheck],
    *,
    clause: str,
    kind: str,
    target: Any,
    field: str | None,
    source_quote: str | None = None,
) -> None:
    goals.append(
        GoalCheck(
            goal_id=_goal_id(len(goals) + 1),
            description=clause,
            kind=kind,
            target=target,
            field=field,
            source_quote=source_quote or clause,
        )
    )


def _clean_value(value: str) -> str:
    value = value.strip(" \t\"'“”‘’,，。.")
    value = re.sub(r"\s*(?:的)?(?:帖子|文章|标题|内容|简介|正文)$", "", value)
    return value.strip()


def _cart_item(clause: str) -> str | None:
    patterns = (
        r"(?:把|将)\s*(.+?)\s*(?:加入|加到|放入|放进|添加到)\s*(?:我的)?购物车",
        r"add\s+(.+?)\s+to\s+(?:my\s+|the\s+|your\s+|a\s+)?"
        r"(?:shopping\s+)?(?:cart|basket)",
        r"(?:购买|买)\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, clause, flags=re.I)
        if match:
            value = match.group(1).strip(" \t\"'“”‘’,，。.")
            if value:
                return value
    return None


def _vote_requirement(clause: str) -> tuple[str, int, str] | None:
    if not re.search(
        r"\b(?:thumbs?\s+(?:up|down)|upvote|downvote|vote)\b|点赞|踩|投票",
        clause,
        flags=re.I,
    ):
        return None
    numbers = _MULTI_OBJECT.findall(clause)
    count = max((int(up or down) for up, down in numbers), default=1)
    kind = "count_per_object" if count > 1 else "count_once"
    return kind, count, "vote"


def _parse_clause(clause: str) -> tuple[str, Any, str | None] | None:
    lowered = clause.casefold()
    quote = _first_quote(clause)
    if quote is not None:
        field = _field(clause)
        if re.search(r"\b(add|adding|append|appending|preserv|keep)\b", lowered) and (
            field in {"bio", "body", "title", "reply"}
            or re.search(r"\b(body|line|text|original)\b", lowered)
        ):
            return "exact_append", quote, field
        if re.search(r"\b(reply|comment|respond)\b|回复|评论", lowered):
            return "exact_equal", quote, field or "reply"
        if re.search(r"\b(change|update|edit|set|replace|rename)\b|改为|修改|更改为|设置为", lowered):
            return "exact_equal", quote, field
        if re.search(r"\b(post|title|thread|question)\b|标题|帖子", lowered):
            return "exact_equal", quote, field or "title"
        return "exact_equal", quote, field
    append_text = re.search(
        r"(?:追加|添加|加上|append(?:ing)?|add(?:ing)?)\s*(?:一行|line|内容|text)?\s*"
        r"(?:为|是|:|：|says?|that says)?\s*(.+)$",
        clause,
        flags=re.I,
    )
    if append_text and re.search(r"正文|原文|body|original|保留|preserv|keep", lowered):
        value = _clean_value(append_text.group(1))
        if value:
            return "exact_append", value, _field(clause) or "body"
    # Only explicit assignment language may yield an exact value.  A loose
    # ``... to ...`` match turned topic constraints such as "subreddit focused
    # on topics related to gaming consoles" into a fake exact field value.
    unquoted = re.search(
        r"(?:改为|改成|设置为|更新为|更改为|标题为|内容为|回复内容为|简介为|"
        r"\b(?:rename|set|change|update|edit|title)\b[^，,;；]{0,60}?\bto\s+)"
        r"([^，,;；]+)$",
        clause,
        flags=re.I,
    )
    if unquoted:
        value = _clean_value(unquoted.group(1))
        if value:
            field = _field(clause)
            if re.search(r"标题|title|帖子", lowered):
                field = field or "title"
            elif re.search(r"回复|reply|comment", lowered):
                field = field or "reply"
            return "exact_equal", value, field
    vote = _vote_requirement(clause)
    if vote is not None:
        return vote
    if re.search(r"\b(subscribe|follow)\b|订阅|关注", lowered):
        return "state_true", True, "subscription"
    if re.search(
        r"\b(checkout|place\s+(?:an\s+)?order|reorder|buy\s+again)\b|"
        r"提交订单|下单|结账|重新购买|重购",
        lowered,
    ):
        return "order_once", 1, "order"
    item = _cart_item(clause)
    if item is not None:
        return "item_exact", item, "cart"
    return None


def _is_scope_clause(clause: str) -> bool:
    return bool(_SCOPE_MARKERS.search(clause))


def extract_goal_checks(task: str) -> list[GoalCheck]:
    """Extract every recognizable requirement from the original task text.

    No task id, answer or URL is consulted.  Quotes are exact values; verbs
    distinguish replacement, append, reply/count/state/item/order.  Quantity,
    ranking, identity, date/status and topic constraints are retained as
    semantic goals; an unrecognized clause becomes one too, so a non-empty task
    can never produce an empty checklist that stops successfully.  Exact
    checks stay first within a clause so deterministic comparison keeps
    precedence.
    """
    if not isinstance(task, str) or not task.strip():
        return []
    goals: list[GoalCheck] = []
    for clause in _protected_split(task):
        parsed = _parse_clause(clause)
        if parsed is None:
            _add_goal(goals, clause=clause, kind="semantic", target=clause.strip(),
                      field=None)
            continue
        kind, target, field = parsed
        _add_goal(goals, clause=clause, kind=kind, target=target, field=field)
        if _is_scope_clause(clause):
            # The action alone ("downvote") is not the whole requirement; the
            # object set ("top 4 post ever in movies") is checked semantically
            # against the original task at stop time.
            _add_goal(goals, clause=clause, kind="semantic", target=clause.strip(),
                      field=None)
    if not goals:
        goals.append(
            GoalCheck(
                goal_id=_goal_id(1),
                description=task.strip(),
                kind="semantic",
                target=task.strip(),
                source_quote=task.strip(),
            )
        )
    return goals


def goal_signature(goal: GoalCheck) -> tuple[str, str, str]:
    return (
        goal.kind,
        json.dumps(goal.target, ensure_ascii=False, sort_keys=True),
        goal.field or "",
    )


def ensure_goals(
    frame: Frame,
    state: TaskState,
    *,
    telemetry=None,
) -> list[GoalCheck]:
    """Initialize goals once from this task; never replace them on each frame."""
    task = frame.task
    if state.task != task:
        if state.task or state.goal_checks:
            state.clear_pending(frame.tab)
            state.data.pop("_drafts", None)
        state.set_task(task)
        goals = extract_goal_checks(task)
        state.set_goal_checks(goals)
        if telemetry is not None:
            telemetry.goal_plan(
                task=task,
                source="deterministic_original_task",
                goals=[goal.as_dict() for goal in goals],
            )
        return goals
    if not state.goals_initialized:
        goals = extract_goal_checks(task)
        state.set_goal_checks(goals)
        if telemetry is not None:
            telemetry.goal_plan(
                task=task,
                source="deterministic_original_task",
                goals=[goal.as_dict() for goal in goals],
            )
        return goals
    return state.goal_checks


def _evidence(
    *,
    state: TaskState,
    frame: Frame,
    atom: AXAtom | None,
    quote: str,
    actual: Any,
    source: str,
    deterministic: bool,
) -> GoalEvidence:
    return GoalEvidence(
        source=source,
        step=frame.step,
        url=frame.url,
        observation_version=frame.observation_version,
        line=atom.line_no if atom is not None else None,
        element_id=atom.element_id if atom is not None else None,
        quote=quote,
        actual=actual,
        identity=state.identity or identity_key(frame.url),
        deterministic=deterministic,
    )


def _normalize_text(value: Any) -> str:
    return (
        str(value)
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def evaluate_goal(goal: GoalCheck, view: AXView, state: TaskState) -> dict[str, Any]:
    """Deterministically settle a goal when the AX makes the fact exact."""
    frame = view.frame
    if goal.kind in _VALUE_KINDS:
        target = _normalize_text(goal.target)
        if goal.kind == "exact_append":
            baseline = goal.baseline
            if baseline is None:
                return {"status": "unknown", "reason": "append baseline not observed"}
            base = _normalize_text(baseline)
            if target and target in base:
                return {
                    "status": "failed",
                    "reason": "target already existed in the preserved baseline",
                }
            expected = {base + "\n" + target, base + target}
            texts = [(atom, _normalize_text(atom.name)) for atom in view.business_texts()]
            # A body may be rendered as consecutive AX text lines.
            blocks: list[tuple[AXAtom, str]] = []
            business = view.business_texts()
            for start in range(len(business)):
                joined = _normalize_text(business[start].name)
                for end in range(start + 1, len(business)):
                    joined = joined + "\n" + _normalize_text(business[end].name)
                    if len(joined) > max(len(value) for value in expected) + 20:
                        break
                    blocks.append((business[start], joined))
            texts.extend(blocks)
            for atom, actual in texts:
                if actual in expected:
                    return {
                        "status": "verified",
                        "actual": actual,
                        "reason": "business text preserves the original and appends exactly",
                        "evidence": [
                            _evidence(
                                state=state,
                                frame=frame,
                                atom=atom,
                                quote=atom.name,
                                actual=actual,
                                source="ax_exact",
                                deterministic=True,
                            )
                        ],
                    }
            for atom, actual in texts:
                if actual.startswith(base) and target in actual:
                    return {
                        "status": "failed",
                        "actual": actual,
                        "reason": "appended text is not exactly the requested addition",
                        "evidence": [
                            _evidence(
                                state=state,
                                frame=frame,
                                atom=atom,
                                quote=atom.name,
                                actual=actual,
                                source="ax_exact",
                                deterministic=True,
                            )
                        ],
                    }
            if any(actual == base for _, actual in texts):
                return {"status": "failed", "reason": "append had no visible effect"}
        else:
            for atom in view.business_texts():
                if _normalize_text(atom.name) == target:
                    return {
                        "status": "verified",
                        "actual": atom.name,
                        "reason": "exact business value visible",
                        "evidence": [
                            _evidence(
                                state=state,
                                frame=frame,
                                atom=atom,
                                quote=atom.name,
                                actual=atom.name,
                                source="ax_exact",
                                deterministic=True,
                            )
                        ],
                    }
        # Draft text, input values and save toasts are not persistence evidence.
        for atom, value in view.form_values():
            if target and target in _normalize_text(value):
                return {
                    "status": "unknown",
                    "reason": "value exists only in an input draft",
                }
        for atom in view.atoms:
            if atom.inside_alert and target and target in _normalize_text(atom.name):
                return {
                    "status": "unknown",
                    "reason": "value appears only in a save/status message",
                }
        return {"status": "unknown", "reason": "no exact business value visible"}
    if goal.kind == "count_per_object":
        if goal.status == "verified" and len(goal.objects) >= int(goal.target):
            return {
                "status": "verified",
                "actual": len(goal.objects),
                "reason": "each required object has a confirmed vote effect",
            }
        return {
            "status": "unknown",
            "reason": (
                f"{len(goal.objects)}/{goal.target} objects confirmed; "
                "per-object effects settle one action at a time"
            ),
        }
    if goal.kind == "item_exact":
        target = _normalize_text(goal.target)
        for atom in view.business_texts():
            value = _normalize_text(atom.name)
            if value == target:
                return {
                    "status": "verified",
                    "actual": value,
                    "reason": "exact item visible in business state",
                    "evidence": [
                        _evidence(
                            state=state,
                            frame=frame,
                            atom=atom,
                            quote=atom.name,
                            actual=value,
                            source="ax_exact",
                            deterministic=True,
                        )
                    ],
                }
        return {"status": "unknown", "reason": "item state needs semantic verification"}
    return {"status": "unknown", "reason": "goal requires semantic verification"}


def _apply_check(
    goal: GoalCheck,
    *,
    status: str,
    evidence: Iterable[GoalEvidence],
    actual: Any = None,
    reason: str = "",
    increment_attempt: bool = False,
) -> bool:
    """Apply a check without erasing an already verified prefix."""
    evidence_list = list(evidence)
    if status == "verified":
        if goal.status != "verified":
            goal.status = "verified"
            goal.evidence.extend(evidence_list)
            goal.actual = actual
            return True
        return False
    if goal.status == "verified":
        return False
    if status in {"failed", "unknown"}:
        if increment_attempt:
            goal.attempts += 1
        if status == "failed":
            goal.status = "failed"
        elif goal.status not in {"failed"}:
            goal.status = "unknown"
        if evidence_list:
            goal.evidence.extend(evidence_list)
        if reason:
            goal.reason = reason
    return True


def _apply_verification(
    frame: Frame,
    state: TaskState,
    checks: Iterable[Mapping[str, Any]],
    *,
    source: str,
) -> list[str]:
    changed: list[str] = []
    for check in checks:
        goal = state.goal(check.get("goal_id", ""))
        if goal is None:
            continue
        status = check.get("status")
        if status not in {"confirmed", "failed", "unknown"}:
            continue
        normalized = "verified" if status == "confirmed" else status
        evidence = [
            item
            for item in check.get("evidence", ())
            if isinstance(item, GoalEvidence)
        ]
        if _apply_check(
            goal,
            status=normalized,
            evidence=evidence,
            actual=check.get("actual"),
            reason=str(check.get("reason", "")),
            increment_attempt=normalized == "failed",
        ):
            changed.append(goal.goal_id)
    return changed


def _evidence_from_model(
    *,
    state: TaskState,
    frame: Frame,
    view: AXView,
    entry: Mapping[str, Any],
) -> GoalEvidence | None:
    try:
        line = int(entry["line"])
    except (KeyError, TypeError, ValueError):
        return None
    quote = entry.get("quote")
    if not view.quote_valid(line, quote):
        return None
    atom = view.by_line.get(line)
    return _evidence(
        state=state,
        frame=frame,
        atom=atom,
        quote=str(quote),
        actual=entry.get("actual"),
        source="model",
        deterministic=False,
    )


def _exact_actual_ok(goal: GoalCheck, actual: Any) -> bool:
    target = _normalize_text(goal.target)
    value = _normalize_text(actual)
    if goal.kind == "exact_append":
        if goal.baseline is None:
            return False
        base = _normalize_text(goal.baseline)
        if target in base:
            return False
        return value in {base + "\n" + target, base + target}
    return value == target


def parse_verification(
    raw: str,
    frame: Frame,
    state: TaskState,
    *,
    mode: str,
) -> dict[str, Any]:
    """Strictly validate an independent model verification response.

    Every confirmed check needs a current AX line and an exact quote plus the
    original task quote.  Exact kinds are recomputed here, so a model cannot
    turn a draft, toast or ``contains`` match into success.
    """
    invalid: list[str] = []
    try:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2 and lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1]).strip()
        data = json.loads(text)
    except (TypeError, ValueError) as exc:
        return {
            "status": "unknown",
            "checks": [],
            "invalid": [f"verification output is not JSON: {exc}"],
            "source": "model",
            "all_confirmed": False,
        }
    if not isinstance(data, dict) or not isinstance(data.get("checks"), list):
        return {
            "status": "unknown",
            "checks": [],
            "invalid": ["verification output requires a checks list"],
            "source": "model",
            "all_confirmed": False,
        }
    view = parse_ax(frame)
    valid_checks: list[dict[str, Any]] = []
    goals = {goal.goal_id: goal for goal in state.goal_checks}
    covered: set[str] = set()
    for index, entry in enumerate(data["checks"]):
        if not isinstance(entry, Mapping):
            invalid.append(f"check {index} is not an object")
            continue
        goal_id = entry.get("goal_id")
        goal = goals.get(goal_id) if isinstance(goal_id, str) else None
        if goal is None:
            invalid.append(f"unknown goal reference: {goal_id!r}")
            continue
        task_quote = entry.get("source_task_quote")
        if (
            not isinstance(task_quote, str)
            or not task_quote
            or task_quote not in state.task
            or not (
                goal.source_quote in task_quote
                or task_quote in goal.source_quote
            )
        ):
            invalid.append(f"goal {goal_id} lacks original-task coverage")
            continue
        covered.add(goal_id)
        status = entry.get("status", entry.get("verdict"))
        if status not in {"confirmed", "failed", "unknown"}:
            invalid.append(f"goal {goal_id} has invalid status {status!r}")
            continue
        evidence_entries = entry.get("evidence")
        if not isinstance(evidence_entries, list):
            evidence_entries = []
        evidence: list[GoalEvidence] = []
        evidence_invalid = False
        for item in evidence_entries:
            if not isinstance(item, Mapping):
                evidence_invalid = True
                continue
            record = _evidence_from_model(
                state=state, frame=frame, view=view, entry=item
            )
            if record is None:
                evidence_invalid = True
                continue
            evidence.append(record)
        if evidence_invalid:
            invalid.append(f"goal {goal_id} cites a non-current AX quote")
            status = "unknown"
        if status == "confirmed":
            if goal.kind not in _KNOWN_KINDS:
                invalid.append(f"goal {goal_id} has an unsupported check kind")
                status = "unknown"
            elif not evidence:
                invalid.append(f"goal {goal_id} confirmed without AX evidence")
                status = "unknown"
            else:
                for record in evidence:
                    atom = view.by_line.get(record.line or 0)
                    if atom is None:
                        status = "unknown"
                        invalid.append(f"goal {goal_id} evidence line is missing")
                        break
                    if goal.kind in _EVIDENCE_KINDS and (atom.inside_alert or atom.inside_form):
                        status = "unknown"
                        invalid.append(
                            f"goal {goal_id} relies on a draft/status area, not business state"
                        )
                        break
                if status == "confirmed":
                    actual = entry.get("actual")
                    if goal.kind in _VALUE_KINDS and not _exact_actual_ok(goal, actual):
                        status = "unknown"
                        invalid.append(f"goal {goal_id} exact value does not match")
                    elif goal.kind in _VALUE_KINDS:
                        normalized_ax = _normalize_text(frame.ax)
                        actual_parts = [
                            _normalize_text(part)
                            for part in str(actual).splitlines()
                            if _normalize_text(part)
                        ]
                        cited_text = _normalize_text(
                            "\n".join(
                                view.lines[record.line - 1]
                                for record in evidence
                                if record.line is not None
                                and 1 <= record.line <= len(view.lines)
                            )
                        )
                        if not actual_parts or any(
                            part not in normalized_ax or part not in cited_text
                            for part in actual_parts
                        ):
                            status = "unknown"
                            invalid.append(
                                f"goal {goal_id} actual value is not in cited current AX"
                            )
                    elif goal.kind == "count_once":
                        if type(actual) is not int or actual != goal.target:
                            status = "unknown"
                            invalid.append(f"goal {goal_id} count does not match")
                    elif goal.kind == "count_per_object":
                        current = len(goal.objects)
                        if (
                            type(actual) is not int
                            or actual < current + 1
                            or actual > int(goal.target)
                        ):
                            status = "unknown"
                            invalid.append(f"goal {goal_id} object count does not match")
                        elif mode == "stop" and not (
                            current >= int(goal.target)
                            and actual == int(goal.target)
                        ):
                            status = "unknown"
                            invalid.append(
                                f"goal {goal_id} aggregate objects are not complete"
                            )
                    elif goal.kind == "semantic":
                        if not isinstance(actual, str) or not actual.strip():
                            status = "unknown"
                            invalid.append(
                                f"goal {goal_id} semantic check lacks an observed value"
                            )
                    elif goal.kind == "state_true":
                        if type(actual) is not bool or actual is not goal.target:
                            status = "unknown"
                            invalid.append(f"goal {goal_id} state does not match")
                    elif goal.kind == "order_once":
                        if type(actual) is not int or actual != goal.target:
                            status = "unknown"
                            invalid.append(f"goal {goal_id} order count does not match")
                    elif goal.kind == "item_exact":
                        expected = [goal.target]
                        if actual != expected:
                            status = "unknown"
                            invalid.append(f"goal {goal_id} item state does not match")
        valid_checks.append(
            {
                "goal_id": goal_id,
                "status": status,
                "actual": entry.get("actual"),
                "reason": str(entry.get("reason", ""))[:500],
                "source_task_quote": task_quote,
                "evidence": evidence,
            }
        )
    if mode == "stop":
        missing = sorted(set(goals) - covered)
        if missing:
            invalid.append("verification omitted goals: " + ", ".join(missing))
    all_confirmed = bool(valid_checks) and all(
        check["status"] == "confirmed" for check in valid_checks
    ) and covered == set(goals)
    return {
        "status": "confirmed" if all_confirmed else (
            "failed" if valid_checks and all(
                check["status"] == "failed" for check in valid_checks
            ) else "unknown"
        ),
        "checks": valid_checks,
        "invalid": invalid,
        "source": "model",
        "all_confirmed": all_confirmed,
    }


def parse_ax(frame: Frame) -> AXView:
    return AXView(frame)


def _record_verification(
    telemetry,
    *,
    frame: Frame,
    mode: str,
    result: Mapping[str, Any],
    source: str,
    pending: PendingAction | None,
) -> None:
    if telemetry is None:
        return
    telemetry.verification(
        step=frame.step,
        url=frame.url,
        observation_version=frame.observation_version,
        mode=mode,
        source=source,
        status=str(result.get("status", "unknown")),
        pending_id=pending.pending_id if pending is not None else None,
        goal_ids=list(pending.goal_ids) if pending is not None else [],
        checks=list(result.get("checks", ())),
        invalid=list(result.get("invalid", ())),
        deadline=frame.deadline,
    )


def _confirm_goal(goal: GoalCheck, result: Mapping[str, Any]) -> None:
    if goal.status == "verified":
        return
    goal.status = "verified"
    goal.evidence.extend(
        [item for item in result.get("evidence", ()) if isinstance(item, GoalEvidence)]
    )


def _fail_goal(goal: GoalCheck, result: Mapping[str, Any]) -> None:
    if goal.status == "verified":
        return
    goal.status = "failed"
    goal.attempts += 1
    goal.evidence.extend(
        [item for item in result.get("evidence", ()) if isinstance(item, GoalEvidence)]
    )
    goal.reason = str(result.get("reason", ""))


def object_key(view: AXView, atom: AXAtom | None, fallback_url: str = "") -> str:
    """Stable identity for the object a write applies to.

    A post/product page URL, an enclosing link URL or an item heading is real
    identity.  Otherwise the current page plus the acted control id keeps
    distinct list items apart within one observation.
    """
    if atom is None:
        return fallback_url
    preceding = [item for item in view.atoms if item.line_no < atom.line_no]
    for candidate in reversed(preceding):
        if candidate.role in {"link", "heading"} and candidate.url:
            return "url:" + candidate.url
        if candidate.role == "heading" and candidate.name:
            return "heading:" + candidate.name
        if candidate.role in {"link", "heading"} and candidate.name:
            return "title:" + candidate.name
    return f"{fallback_url}#{atom.element_id}"


def _vote_effect(
    pending: PendingAction,
    view: AXView,
) -> tuple[bool, AXAtom | None, str]:
    """Read the toggled vote control that proves the dispatched vote landed.

    The candidate must belong to the same acted object (same control id or same
    enclosing title/URL), so one post's "Retract upvote" cannot confirm a vote
    on a different post in a listing.
    """
    source = pending.source
    before = str(source.get("element_name", "")).casefold()
    if not any(word in before for word in _VOTE_WORDS):
        return False, None, ""
    direction = ""
    if "down" in before or "踩" in before:
        direction = "down"
    elif "up" in before or "赞" in before:
        direction = "up"
    source_key = str(source.get("object_key") or "")
    source_id = source.get("element_id")
    source_url = str(source.get("url", ""))

    def same_object(atom: AXAtom) -> bool:
        if source_id is not None and atom.element_id == str(source_id):
            return True
        if source_key and object_key(view, atom, source_url) == source_key:
            return True
        return False

    for atom in view.atoms:
        name = atom.name.casefold()
        if not any(word in name for word in ("upvote", "downvote", "vote", "thumb")):
            continue
        if not any(word in name for word in _VOTE_TOGGLED_WORDS):
            continue
        if direction == "down" and "down" not in name and "踩" not in name:
            continue
        if direction == "up" and "up" not in name and "赞" not in name:
            continue
        if same_object(atom):
            return True, atom, atom.name
    element_id = source.get("element_id")
    atom = view.by_id.get(str(element_id)) if element_id is not None else None
    if atom is not None:
        name = atom.name.casefold()
        if atom.checked or atom.selected:
            return True, atom, atom.name
    return False, None, ""


def _record_object(
    goal: GoalCheck,
    pending: PendingAction,
    *,
    state: TaskState,
    frame: Frame,
    atom: AXAtom | None,
    quote: str,
    source: str,
) -> bool:
    """Record one confirmed object without claiming the aggregate goal."""
    key = str(pending.source.get("object_key") or "")
    if not key:
        key = f"{pending.source.get('url', frame.url)}#{pending.source.get('element_id', '')}"
    if not key or key in goal.objects:
        return False
    goal.objects.append(key)
    goal.actual = len(goal.objects)
    goal.evidence.append(
        _evidence(
            state=state,
            frame=frame,
            atom=atom,
            quote=quote or key,
            actual=key,
            source=source,
            deterministic=source != "model",
        )
    )
    if len(goal.objects) >= int(goal.target):
        goal.status = "verified"
        goal.reason = "all required objects have confirmed effects"
    else:
        goal.status = "unknown"
        goal.reason = f"{len(goal.objects)}/{goal.target} objects confirmed"
    return True


def resolve_pending(
    frame: Frame,
    state: TaskState,
    *,
    semantic_verify: Callable[[Frame, TaskState, str], Mapping[str, Any] | None] | None = None,
    telemetry=None,
    screenshot_request: Callable[[], Any] | None = None,
) -> dict[str, Any] | None:
    """Resolve the previous tab action against this next observation.

    A query/navigation frame may confirm or contradict the pending effect, but
    it never replaces or clears an unresolved record.  A changed page with no
    decidable value stays unknown and keeps the write guard active.  Multi-
    object effects are settled per object: confirming one vote clears this
    pending action while the aggregate goal keeps the remaining objects.
    """
    pending = state.pending_for(frame.tab)
    if pending is None or pending.step >= frame.step:
        return None
    view = parse_ax(frame)
    goals = [state.goal(item) for item in pending.goal_ids]
    goals = [goal for goal in goals if goal is not None]
    aggregate = [goal for goal in goals if goal.kind != "count_per_object"]
    per_object = [goal for goal in goals if goal.kind == "count_per_object"]
    results = {goal.goal_id: evaluate_goal(goal, view, state) for goal in aggregate}
    effect = False
    effect_atom: AXAtom | None = None
    effect_quote = ""
    if per_object or any(goal.kind == "count_once" for goal in aggregate):
        effect, effect_atom, effect_quote = _vote_effect(pending, view)
    confirmed_ids: set[str] = set()
    failed_ids: set[str] = set()
    for goal in aggregate:
        result = results[goal.goal_id]
        if result["status"] == "verified":
            _confirm_goal(goal, result)
            confirmed_ids.add(goal.goal_id)
        elif goal.kind == "count_once" and effect:
            _confirm_goal(
                goal,
                {
                    "evidence": [
                        _evidence(
                            state=state,
                            frame=frame,
                            atom=effect_atom,
                            quote=effect_quote,
                            actual=effect_quote,
                            source="ax_vote_state",
                            deterministic=True,
                        )
                    ]
                },
            )
            confirmed_ids.add(goal.goal_id)
    for goal in per_object:
        if effect and _record_object(
            goal,
            pending,
            state=state,
            frame=frame,
            atom=effect_atom,
            quote=effect_quote,
            source="ax_vote_state",
        ):
            confirmed_ids.add(goal.goal_id)
    source = "deterministic"
    semantic_result: Mapping[str, Any] | None = None
    unresolved = [
        goal for goal in goals
        if goal.goal_id not in confirmed_ids and goal.status != "verified"
    ]
    unchanged = pending.source.get("ax_fingerprint") == view.fingerprint
    if unresolved and unchanged and not confirmed_ids:
        for goal in unresolved:
            if goal.kind == "count_per_object":
                # A vote that changed nothing is a local miss, not a reason to
                # fail the whole aggregate; the pending action is released so
                # the same object may be retried.
                goal.status = "unknown"
                goal.attempts += 1
                goal.reason = "no observation effect after action"
                failed_ids.add(goal.goal_id)
            else:
                _fail_goal(goal, {"reason": "no observation effect after action"})
                failed_ids.add(goal.goal_id)
        source = "ax_no_effect"
    elif unresolved and semantic_verify is not None:
        semantic_result = semantic_verify(frame, state, "pending")
        source = "model"
        if semantic_result is not None:
            checks = _checks_for_goals(
                semantic_result, [goal.goal_id for goal in unresolved]
            )
            for goal in unresolved:
                check = checks.get(goal.goal_id)
                if not check:
                    continue
                if goal.kind == "count_per_object":
                    if check["status"] == "confirmed":
                        evidence = [
                            item for item in check.get("evidence", ())
                            if isinstance(item, GoalEvidence)
                        ]
                        atom = (
                            view.by_line.get(evidence[0].line)
                            if evidence and evidence[0].line is not None
                            else None
                        )
                        quote = evidence[0].quote if evidence else ""
                        if _record_object(
                            goal,
                            pending,
                            state=state,
                            frame=frame,
                            atom=atom,
                            quote=quote,
                            source="model",
                        ):
                            confirmed_ids.add(goal.goal_id)
                    elif check["status"] == "failed":
                        goal.status = "unknown"
                        goal.reason = str(check.get("reason", ""))
                elif check["status"] == "confirmed":
                    _confirm_goal(goal, check)
                    confirmed_ids.add(goal.goal_id)
                elif check["status"] == "failed":
                    _fail_goal(goal, check)
                    failed_ids.add(goal.goal_id)
            unresolved = [
                goal for goal in goals
                if goal.goal_id not in confirmed_ids and goal.status != "verified"
            ]
    if goals and all(
        goal.goal_id in confirmed_ids or goal.status == "verified" for goal in goals
    ):
        outcome = "confirmed"
    elif goals and all(
        goal.goal_id in failed_ids or goal.status == "failed" for goal in goals
    ):
        outcome = "failed"
    elif unresolved and all(goal.goal_id in failed_ids for goal in unresolved):
        outcome = "failed"
    else:
        outcome = "unknown"
    result_status = (
        "confirmed" if outcome == "confirmed"
        else "failed" if outcome == "failed"
        else "unknown"
    )
    _record_verification(
        telemetry,
        frame=frame,
        mode="pending",
        result={
            "status": result_status,
            "checks": semantic_result.get("checks", ()) if semantic_result else [],
            "invalid": semantic_result.get("invalid", ()) if semantic_result else [],
        },
        source=source,
        pending=pending,
    )
    if outcome == "unknown" and screenshot_request is not None:
        # AX did not settle the effect.  Request one current-frame PNG only as
        # diagnostic evidence; image existence never becomes success proof.
        screenshot_request()
    if outcome == "confirmed":
        state.clear_pending(frame.tab)
        pending.status = "confirmed"
        pending.verification_source = source
        if telemetry is not None:
            telemetry.recovery(
                step=frame.step,
                pending_id=pending.pending_id,
                from_status="unknown",
                to_status="confirmed",
                goal_ids=list(pending.goal_ids),
                preserved_prefix=sum(1 for g in state.goal_checks if g.status == "verified"),
                detail="this action's business effect confirmed; do not rewrite it",
            )
    elif outcome == "failed":
        pending.status = "failed"
        pending.verification_source = source
        state.clear_pending(frame.tab)
        if telemetry is not None:
            telemetry.recovery(
                step=frame.step,
                pending_id=pending.pending_id,
                from_status="unknown",
                to_status="failed",
                goal_ids=list(pending.goal_ids),
                preserved_prefix=sum(1 for g in state.goal_checks if g.status == "verified"),
                detail="confirmed local failure; recover only the affected goal",
            )
    else:
        pending.status = "unknown"
        pending.attempts += 1
        pending.verification_source = source
        state.replace_pending(pending, tab=frame.tab)
        if telemetry is not None:
            telemetry.recovery(
                step=frame.step,
                pending_id=pending.pending_id,
                from_status="unknown",
                to_status="unknown",
                goal_ids=list(pending.goal_ids),
                preserved_prefix=sum(1 for g in state.goal_checks if g.status == "verified"),
                detail="write effect unknown; only read-only query/navigation allowed",
            )
    return {
        "pending_id": pending.pending_id,
        "status": outcome,
        "source": source,
        "results": semantic_result.get("checks", ()) if semantic_result else results,
    }


def _checks_for_goals(
    result: Mapping[str, Any], goal_ids: Iterable[str]
) -> dict[str, Mapping[str, Any]]:
    wanted = set(goal_ids)
    return {
        check["goal_id"]: check
        for check in result.get("checks", ())
        if isinstance(check, Mapping) and check.get("goal_id") in wanted
    }


def judge_goals(task: str, state: TaskState) -> tuple[bool, list[GoalCheck]]:
    """Re-read the current task and judge complete coverage from state facts.

    Fails closed: an empty task, an unextractable task or a state checklist
    without matching verified evidence can never produce a success stop, and
    the comparison is against the original task rather than the actor's list.
    """
    if not isinstance(task, str) or not task.strip():
        return False, []
    required = extract_goal_checks(task)
    if not required:
        return False, []
    available = list(state.goal_checks)
    used: set[int] = set()
    missing: list[GoalCheck] = []
    for requirement in required:
        matched: tuple[int, GoalCheck] | None = None
        for index, actual in enumerate(available):
            if index in used:
                continue
            if goal_signature(actual) == goal_signature(requirement):
                matched = (index, actual)
                break
        if matched is None:
            missing.append(requirement)
            continue
        index, actual = matched
        used.add(index)
        if (
            actual.status != "verified"
            or not actual.evidence
            or actual.source_quote not in task
        ):
            missing.append(actual)
    return not missing, missing


def build_verify_payload(
    frame: Frame,
    state: TaskState,
    *,
    mode: str,
) -> dict[str, Any]:
    view = parse_ax(frame)
    return {
        "mode": "independent_m2_verification",
        "check_kind": mode,
        "task": state.task or frame.task,
        "original_task": state.task or frame.task,
        "requirements_source": "original_task_text",
        "url": frame.url,
        "step": frame.step,
        "deadline": frame.deadline,
        "accessibility_tree": frame.ax,
        "line_count": len(view.lines),
        "goal_checks_from_original_task": [
            goal.as_dict() for goal in state.goal_checks
        ],
        "pending_action": (
            state.pending_for(frame.tab).as_dict()
            if state.pending_for(frame.tab) is not None
            else None
        ),
        "required_output": {
            "checks": [
                {
                    "goal_id": "existing id",
                    "status": "confirmed|failed|unknown",
                    "actual": "exact observed business value/count/state",
                    "source_task_quote": "exact substring of task",
                    "evidence": [
                        {"line": "1-based line number from accessibility_tree",
                         "quote": "exact substring of that AX line"}
                    ],
                    "reason": "short reason",
                }
            ]
        },
        "rules": [
            "Re-read the supplied original_task; do not rely only on the goal list.",
            "Do not return an action. Verify only the supplied original-task goals.",
            "Input drafts, save toasts, success messages and visual evidence are not persistence.",
            "For exact replacement report actual and require equality, never substring.",
            "For append require the preserved original plus exactly the requested addition.",
            "Never invent goals, line numbers or quotes; missing evidence must be unknown.",
            "Counts/states must be observed in the current AX, not inferred from the click.",
            "For multi-object requirements confirm one object per action with evidence.",
        ],
    }


def assert_stop(
    frame: Frame,
    state: TaskState,
    *,
    semantic_verify: Callable[[Frame, TaskState, str], Mapping[str, Any] | None] | None = None,
    telemetry=None,
    screenshot_request: Callable[[], Any] | None = None,
) -> None:
    """Refuse a success stop until all original-task goals are verified."""
    ensure_goals(frame, state, telemetry=telemetry)
    if not state.task.strip():
        raise GoalIncompleteError(
            "Cannot stop: the original task text is empty, so no requirement "
            "can be verified."
        )
    if not state.goal_checks:
        raise GoalIncompleteError(
            "Cannot stop: no original-task requirement could be extracted; an "
            "empty checklist is not success."
        )
    pending = state.pending_for(frame.tab)
    if pending is not None and pending.status == "unknown":
        raise GoalIncompleteError(
            "Cannot stop: the last write result is unknown. Use a read-only query "
            "or navigation to confirm or disprove it before stopping."
        )
    ok, missing = judge_goals(state.task, state)
    if not ok:
        view = parse_ax(frame)
        changed = []
        for goal in missing:
            result = evaluate_goal(goal, view, state)
            if result["status"] == "verified":
                _confirm_goal(goal, result)
                changed.append(goal.goal_id)
        if changed:
            ok, missing = judge_goals(state.task, state)
    if not ok and semantic_verify is not None:
        if screenshot_request is not None:
            screenshot_request()
        result = semantic_verify(frame, state, "stop")
        if result is not None:
            _apply_verification(
                frame, state, result.get("checks", ()), source="model"
            )
            _record_verification(
                telemetry,
                frame=frame,
                mode="stop",
                result=result,
                source="model",
                pending=pending,
            )
            ok, missing = judge_goals(state.task, state)
    if not ok:
        labels = "; ".join(goal.description or goal.goal_id for goal in missing)
        raise GoalIncompleteError(
            "Cannot stop: unverified original-task requirements remain: " + labels
        )
    if telemetry is not None:
        telemetry.progress(
            step=frame.step,
            url=frame.url,
            goals=[goal.as_dict() for goal in state.goal_checks],
            source="stop_judge",
        )


__all__ = [
    "AXView",
    "GoalIncompleteError",
    "assert_stop",
    "build_verify_payload",
    "ensure_goals",
    "evaluate_goal",
    "extract_goal_checks",
    "goal_signature",
    "judge_goals",
    "object_key",
    "parse_ax",
    "parse_verification",
    "resolve_pending",
]
