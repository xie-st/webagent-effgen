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
        "form",
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
_EVIDENCE_KINDS = frozenset(
    _EXACT_KINDS | {"semantic", "count_once", "count_per_object"}
)
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
# Ranking/position words need their own business evidence; a vote toggle says
# only that one object was voted, never that it is newest or in the top N.
_RANKING_SCOPE = re.compile(
    r"\b(?:newest|oldest|latest|earliest|top|first|last|highest|lowest|"
    r"most|least|cheapest|most\s+expensive)\b|"
    r"最新|最旧|最早|最晚|前\s*\d|排名|第\s*\d",
    re.I,
)
_VOTE_STATE_ROLES = frozenset({"button", "link", "checkbox", "radio"})
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
    r"comments?|articles?|users?|accounts?|forums?|communities)\b",
    re.I,
)
# A field value is only evidence when it sits in that field's business region.
# These are generic UI/URL words, not task ids, answers or site-specific paths.
_FIELD_MARKERS: dict[str, tuple[str, ...]] = {
    "bio": ("bio", "biography", "profile", "about", "简介", "个人简介", "个人资料"),
    "title": ("title", "标题"),
    "body": ("body", "post", "thread", "selftext", "content", "正文", "内容", "帖子"),
    "comment": ("comment", "comments", "reply", "replies", "回复", "评论"),
    "reply": ("comment", "comments", "reply", "replies", "回复", "评论"),
    "name": ("name", "username", "account", "profile", "姓名", "用户名", "名称"),
    "cart": (
        "cart", "basket", "shopping cart", "checkout", "subtotal",
        "购物车", "结算", "小计",
    ),
}
_FIELD_URL_MARKERS: dict[str, tuple[str, ...]] = {
    "bio": ("bio", "biography", "profile", "user", "account"),
    "title": ("post", "thread", "topic", "question", "comment"),
    "body": ("post", "thread", "topic", "comment"),
    "comment": ("comment", "reply", "post"),
    "reply": ("comment", "reply", "post"),
    "name": ("profile", "account", "user", "settings"),
    "cart": ("cart", "basket", "checkout"),
}
# A candidate under one of these headings is in a different object region even
# if the same text (or a cart label) appears elsewhere on the page.
_UNRELATED_SECTIONS: dict[str, tuple[str, ...]] = {
    "bio": ("post", "posts", "article", "thread", "comment", "product", "products",
            "cart", "帖子", "文章", "商品", "产品", "购物车"),
    "title": ("product", "products", "cart", "shopping cart", "商品", "产品", "购物车"),
    "body": ("product", "products", "cart", "shopping cart", "商品", "产品", "购物车"),
    "comment": ("product", "products", "cart", "shopping cart", "商品", "产品", "购物车"),
    "reply": ("product", "products", "cart", "shopping cart", "商品", "产品", "购物车"),
    "name": ("post", "article", "product", "products", "cart", "帖子", "文章", "商品"),
    "cart": ("product", "products", "catalog", "listing", "search results",
             "商品", "产品", "搜索结果"),
}
_HISTORY_PAGE_LIMIT = 3
_HISTORY_TEXT_LIMIT = 6_000
_HISTORY_LINE_LIMIT = 80
_HISTORY_ID_KINDS = frozenset({"semantic"})
_HISTORY_TERMS = (
    "price", "cost", "capacity", "order", "orders", "cancelled", "canceled",
    "cancel", "cart", "checkout", "total", "date", "pairs", "价格", "容量",
    "订单", "取消", "购物车", "结算", "日期",
)
_STOPWORDS = frozenset(
    {
        "a", "an", "the", "and", "or", "for", "with", "from", "into", "onto",
        "this", "that", "these", "those", "my", "me", "to", "of", "in", "on",
        "at", "is", "are", "was", "were", "be", "please", "can", "you", "it",
        "least", "most", "show", "find", "open", "add", "change", "update",
        "把", "将", "我的", "一个", "一些", "请", "帮我",
    }
)
_HISTORY_REQUIRED = re.compile(
    r"(?:least|cheapest|lowest|minimum|at\s+least)[^.;]{0,100}"
    r"(?:price|cost|capacity)|"
    r"(?:previous|previously|earlier|past|cancel(?:l)?ed)[^.;]{0,100}"
    r"(?:order|purchase|bought|reorder)|"
    r"(?:最低|least|cheapest|lowest)[^。;]{0,80}(?:价|容量)|"
    r"容量[^。;]{0,80}(?:最低|least|cheapest|lowest)|"
    r"重购|重新购买|历史订单|"
    r"(?:取消|cancel(?:l)?ed?)[^。;]{0,60}(?:重购|重新购买|reorder)",
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
            ancestor_indent = item["indent"]
            for previous in reversed(parsed[:position]):
                if previous["indent"] < ancestor_indent:
                    ancestors.append(previous)
                    ancestor_indent = previous["indent"]
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


def _marker_in(text: str, markers: Iterable[str]) -> bool:
    value = text.casefold()
    return any(marker.casefold() in value for marker in markers)


def _nearest_section(view: AXView, atom: AXAtom) -> AXAtom | None:
    """Return the closest preceding heading that owns this atom's section."""
    found: AXAtom | None = None
    for candidate in view.atoms:
        if candidate.line_no >= atom.line_no:
            break
        if (
            candidate.role == "heading"
            and candidate.indent <= atom.indent
            and atom.line_no - candidate.line_no <= 80
        ):
            found = candidate
    return found


def _field_scope_ok(view: AXView, atom: AXAtom | None, field: str | None) -> bool:
    """Bind an exact value to its field/business region, not just its text.

    The candidate must be under a matching section/ancestor/control or on a
    matching route.  A heading for a different object region (a product listing,
    an unrelated post, another cart area) blocks the same text elsewhere on the
    page.  These markers are generic UI vocabulary; no task id, answer or site
    path is consulted.
    """
    if atom is None or field not in _FIELD_MARKERS:
        return False
    markers = _FIELD_MARKERS[field]
    section = _nearest_section(view, atom)
    if section is not None:
        if _marker_in(section.name, markers):
            return True
        if _marker_in(section.name, _UNRELATED_SECTIONS[field]):
            return False
    # A field control/region wrapping the text is stronger than a neighbouring
    # label, so check enclosing structure first.
    for other in reversed(view.atoms):
        if other.line_no >= atom.line_no:
            continue
        if other.indent < atom.indent:
            if _marker_in(other.name, markers):
                return True
            if other.indent == 0:
                break
    for other in view.atoms:
        if other.line_no == atom.line_no:
            continue
        if (
            abs(other.line_no - atom.line_no) <= 8
            and other.role in {
                "heading", "button", "link", "textbox", "searchbox",
                "combobox", "listbox", "menuitem",
            }
            and _marker_in(other.name, markers)
        ):
            return True
    if _marker_in(view.frame.url, _FIELD_URL_MARKERS[field]):
        return True
    return False


def _scope_blocked(view: AXView, atom: AXAtom | None, field: str | None) -> bool:
    """Explain a same-value match that belongs to another field/object."""
    if atom is None or field not in _FIELD_MARKERS:
        return False
    section = _nearest_section(view, atom)
    return (
        section is not None
        and not _marker_in(section.name, _FIELD_MARKERS[field])
        and _marker_in(section.name, _UNRELATED_SECTIONS[field])
    )


def _goal_mentions_vote(goal: GoalCheck) -> bool:
    text = f"{goal.target} {goal.description}".casefold()
    return any(word in text for word in _VOTE_WORDS)


def _vote_control_atom(atom: AXAtom | None) -> bool:
    return bool(
        atom is not None
        and atom.role in _VOTE_STATE_ROLES
        and any(word in atom.name.casefold() for word in _VOTE_WORDS)
    )


def _persistent_vote_control(atom: AXAtom | None) -> bool:
    """A post-action toggle control (``Retract upvote``) carries vote state.

    An untouched ``Upvote`` button, a checklist item or a draft textbox does
    not.  The check is deliberately narrow: persistent vote wording, or an
    explicit checked/selected vote control.
    """
    if not _vote_control_atom(atom):
        return False
    text = atom.name.casefold()
    return any(word in text for word in _VOTE_TOGGLED_WORDS) or bool(
        atom.checked is True or atom.selected is True
    )


def _business_evidence_atom(goal: GoalCheck, atom: AXAtom | None) -> bool:
    """Reject draft/status evidence while accepting a persistent vote toggle.

    Most controls inside a form are drafts (unsubmitted text), and alert text is
    a success/status message.  The one exception is a vote goal citing its own
    post-action toggle: that control is the business vote state itself even when
    the site wraps its vote button in an HTML form.  This is not a general
    relaxation of form evidence.
    """
    if atom is None or atom.inside_alert or atom.role in {"alert", "status"}:
        return False
    if atom.inside_form:
        return _goal_mentions_vote(goal) and _persistent_vote_control(atom)
    return True


def _scope_semantic_goal(goal: GoalCheck) -> bool:
    return goal.kind == "semantic" and bool(
        _SCOPE_MARKERS.search(f"{goal.target} {goal.description}")
    )


def _ranking_semantic_goal(goal: GoalCheck) -> bool:
    return goal.kind == "semantic" and bool(
        _RANKING_SCOPE.search(f"{goal.target} {goal.description}")
    )


def _acted_object_keys(state: TaskState) -> set[str]:
    """Stable identities already confirmed by vote actions on this task."""
    keys: set[str] = set()
    for goal in state.goal_checks:
        if goal.kind in {"count_once", "count_per_object"}:
            keys.update(key for key in goal.objects if key)
    return keys


def _same_stable_identity(view: AXView, source_key: str, atom: AXAtom) -> bool:
    """Match the acted business object, rather than any object on its page."""
    candidate = object_key(view, atom, view.frame.url)
    return bool(candidate and candidate == source_key)


def _identities_overlap(view: AXView, identities: set[str], acted: set[str]) -> bool:
    return bool(identities & acted)


def _business_identity_keys(
    view: AXView, evidence: Iterable[GoalEvidence], goal: GoalCheck
) -> set[str]:
    """Stable URL/title identities among current business evidence.

    Vote toggles, alert text and unsubmitted form drafts are not business
    identity evidence, so they cannot prove a newest/top-N/object scope.
    """
    keys: set[str] = set()
    for record in evidence:
        if record.history_id is not None or record.line is None:
            continue
        atom = view.by_line.get(record.line)
        if atom is None or not _business_evidence_atom(goal, atom):
            continue
        if _vote_control_atom(atom):
            continue
        key = object_key(view, atom, view.frame.url)
        if key:
            keys.add(key)
    return keys


def _history_terms(goals: Iterable[GoalCheck]) -> tuple[str, ...]:
    terms = set(_HISTORY_TERMS)
    for goal in goals:
        source = f"{goal.description} {goal.target} {goal.field or ''}"
        for token in re.findall(
            r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}|\d{2,}", source
        ):
            lowered = token.casefold()
            if lowered not in _STOPWORDS and len(lowered) >= 2:
                terms.add(lowered)
    return tuple(sorted(terms))


def _history_excerpt(text: str, terms: tuple[str, ...]) -> str:
    """Keep only bounded, relevant lines from one historical observation."""
    lines = text.splitlines()
    keep: set[int] = set()
    for index, line in enumerate(lines):
        lowered = line.casefold()
        if _marker_in(lowered, terms) or re.search(
            r"[$€£¥]\s*\d|\d+(?:\.\d+)?\s*(?:pairs?|items?|orders?)", lowered
        ):
            keep.update(range(max(0, index - 1), min(len(lines), index + 2)))
    if not keep:
        return text[:_HISTORY_TEXT_LIMIT]
    selected = [line for index, line in enumerate(lines) if index in keep]
    excerpt = "\n".join(selected[:_HISTORY_LINE_LIMIT])
    return excerpt[:_HISTORY_TEXT_LIMIT]


def history_observations(frame: Frame, state: TaskState) -> list[dict[str, Any]]:
    """Select bounded, source-bound historical observations for verification.

    IDs are local ``hN`` labels over the supplied Frame.history.  A step or
    observation version that the platform did not provide stays ``None``; none
    is invented.  These records are evidence-only and are never action targets.
    """
    terms = _history_terms(state.goal_checks)
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(frame.history):
        if not isinstance(item, Mapping):
            continue
        observation = item.get("observation")
        if not isinstance(observation, Mapping):
            continue
        url = observation.get("url")
        text = observation.get("text")
        if not isinstance(url, str) or not isinstance(text, str) or not text.strip():
            continue
        if url == frame.url and text == frame.ax:
            continue
        run_id = item.get("run_id", observation.get("run_id"))
        if (
            isinstance(run_id, str)
            and run_id
            and frame.run_id
            and run_id != frame.run_id
        ):
            continue
        key = (url, text)
        if key in seen:
            continue
        seen.add(key)
        lowered = text.casefold()
        score = sum(1 for term in terms if term in lowered)
        score += len(re.findall(r"[$€£¥]\s*\d|\borders?\b|购物车|订单", lowered))
        step = item.get("step", observation.get("step"))
        if type(step) is not int:
            step = None
        version = item.get(
            "observation_version",
            observation.get("observation_version", observation.get("version")),
        )
        action = item.get("action")
        candidates.append(
            {
                "index": index,
                "score": score,
                "source_id": f"h{index + 1}",
                "url": url,
                "text": text,
                "excerpt": _history_excerpt(text, terms),
                "step": step,
                "observation_version": version,
                "action": action if isinstance(action, str) else None,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
        )
    if not candidates:
        return []
    selected = sorted(
        candidates, key=lambda entry: (entry["score"], entry["index"]), reverse=True
    )[:_HISTORY_PAGE_LIMIT]
    selected.sort(key=lambda entry: entry["index"])
    return [
        {
            "source_id": entry["source_id"],
            "url": entry["url"],
            "text": entry["excerpt"],
            "step": entry["step"],
            "observation_version": entry["observation_version"],
            "action": entry["action"],
            "text_sha256": entry["text_sha256"],
        }
        for entry in selected
    ]


def _history_required(goal: GoalCheck) -> bool:
    return goal.kind == "semantic" and bool(
        _HISTORY_REQUIRED.search(f"{goal.target} {goal.description}")
    )


def _history_evidence(
    observation: Mapping[str, Any],
    *,
    quote: str,
    actual: Any,
) -> GoalEvidence:
    return GoalEvidence(
        source="history",
        step=observation.get("step"),
        url=str(observation.get("url", "")),
        observation_version=observation.get("observation_version"),
        quote=quote,
        actual=actual,
        identity=identity_key(str(observation.get("url", ""))),
        deterministic=False,
        history_id=str(observation.get("source_id", "")),
    )


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
        ("display name", "name"),
        ("username", "name"),
        ("用户名", "name"),
        ("姓名", "name"),
        ("name", "name"),
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
    return bool(_SCOPE_MARKERS.search(clause) or _MULTI_OBJECT.search(clause))


def _semantic_object_count(goal: GoalCheck) -> int:
    # Vote counts already have a deterministic per-object progress ledger.
    # Other numbered object sets must retain and substantiate their quantity.
    if goal.kind != "semantic" or _goal_mentions_vote(goal):
        return 1
    match = _MULTI_OBJECT.search(str(goal.target))
    return max(1, int(match.group(1) or match.group(2))) if match else 1


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
            scoped = [
                atom for atom in view.business_texts()
                if _field_scope_ok(view, atom, goal.field)
            ]
            texts = [(atom, _normalize_text(atom.name)) for atom in scoped]
            # A body may be rendered as consecutive AX text lines.
            blocks: list[tuple[AXAtom, str]] = []
            business = scoped
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
                if _normalize_text(atom.name) != target:
                    continue
                if _field_scope_ok(view, atom, goal.field):
                    return {
                        "status": "verified",
                        "actual": atom.name,
                        "reason": "exact value visible in the requested field",
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
            if any(
                _normalize_text(atom.name) == target
                and _scope_blocked(view, atom, goal.field)
                for atom in view.business_texts()
            ):
                return {
                    "status": "unknown",
                    "reason": (
                        "the same text appears in an unrelated field/object region"
                    ),
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
            if value == target and _field_scope_ok(view, atom, "cart"):
                return {
                    "status": "verified",
                    "actual": value,
                    "reason": "exact item visible in the cart region",
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
        if any(
            _normalize_text(atom.name) == target
            and _scope_blocked(view, atom, "cart")
            for atom in view.business_texts()
        ):
            return {
                "status": "unknown",
                "reason": "the product name appears outside the cart region",
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


def _history_evidence_from_model(
    observation: Mapping[str, Any],
    entry: Mapping[str, Any],
) -> GoalEvidence | None:
    """Validate one historical quote against the supplied, source-bound text."""
    quote = entry.get("quote")
    if (
        not isinstance(quote, str)
        or not quote
        or quote not in str(observation.get("text", ""))
    ):
        return None
    for key in ("url", "history_url"):
        if key in entry and entry[key] != observation.get("url"):
            return None
    for key in ("step", "observation_version"):
        if key in entry:
            actual = observation.get(key)
            if actual is None or entry[key] != actual:
                return None
    return _history_evidence(
        observation,
        quote=quote,
        actual=entry.get("actual"),
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

    Every confirmed check needs a current business-state line and an exact quote
    plus the original task quote.  Exact kinds are recomputed here, so a model
    cannot turn a draft, toast or ``contains`` match into success.  Historical
    evidence is limited to semantic checks, must cite a supplied ``hN`` source
    and quote its text verbatim, and can never replace current evidence.
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
    history_by_id = {
        observation["source_id"]: observation
        for observation in history_observations(frame, state)
    }
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
        history_invalid = False
        for item in evidence_entries:
            if not isinstance(item, Mapping):
                evidence_invalid = True
                continue
            source = str(item.get("source", "")).casefold()
            history_id = item.get("history_id", item.get("source_id"))
            is_history = history_id is not None or source in {
                "history", "historical", "past",
            }
            if is_history:
                observation = (
                    history_by_id.get(history_id)
                    if isinstance(history_id, str)
                    else None
                )
                record = (
                    _history_evidence_from_model(observation, item)
                    if observation is not None
                    else None
                )
                if record is None:
                    history_invalid = True
                    continue
                evidence.append(record)
            else:
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
        if history_invalid:
            invalid.append(
                f"goal {goal_id} cites a history source/quote outside the supplied history"
            )
            status = "unknown"
        current_evidence = [
            record for record in evidence if record.history_id is None
        ]
        history_evidence = [
            record for record in evidence if record.history_id is not None
        ]
        if status == "confirmed":
            if goal.kind not in _KNOWN_KINDS:
                invalid.append(f"goal {goal_id} has an unsupported check kind")
                status = "unknown"
            elif not current_evidence:
                invalid.append(f"goal {goal_id} confirmed without current AX evidence")
                status = "unknown"
            elif history_evidence and goal.kind not in _HISTORY_ID_KINDS:
                invalid.append(
                    f"goal {goal_id} uses history for a current-value check"
                )
                status = "unknown"
            else:
                for record in current_evidence:
                    atom = view.by_line.get(record.line or 0)
                    if atom is None:
                        status = "unknown"
                        invalid.append(f"goal {goal_id} evidence line is missing")
                        break
                    if goal.kind in _EVIDENCE_KINDS and not _business_evidence_atom(
                        goal, atom
                    ):
                        status = "unknown"
                        invalid.append(
                            f"goal {goal_id} relies on a draft/status area, not business state"
                        )
                        break
                    field = (
                        "cart" if goal.kind == "item_exact" else goal.field
                    )
                    if goal.kind in _EXACT_KINDS and not _field_scope_ok(
                        view, atom, field
                    ):
                        status = "unknown"
                        invalid.append(
                            f"goal {goal_id} cites the value outside its field/object region"
                        )
                        break
                if (
                    status == "confirmed"
                    and goal.kind == "semantic"
                    and _history_required(goal)
                    and not history_evidence
                ):
                    status = "unknown"
                    invalid.append(
                        f"goal {goal_id} needs historical comparison evidence"
                    )
                if status == "confirmed" and _scope_semantic_goal(goal):
                    identities = _business_identity_keys(view, current_evidence, goal)
                    acted = _acted_object_keys(state)
                    if not identities:
                        status = "unknown"
                        invalid.append(
                            f"goal {goal_id} semantic scope lacks concrete business "
                            "evidence beyond vote/status controls"
                        )
                    elif acted and not _identities_overlap(view, identities, acted):
                        status = "unknown"
                        invalid.append(
                            f"goal {goal_id} semantic scope does not identify the "
                            "acted object by URL/title"
                        )
                    elif _ranking_semantic_goal(goal) and not history_evidence:
                        status = "unknown"
                        invalid.append(
                            f"goal {goal_id} newest/ranking claim lacks historical "
                            "ordering evidence"
                        )
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
                                for record in current_evidence
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
                        elif (
                            _semantic_object_count(goal) > 1
                            and len(_business_identity_keys(view, current_evidence, goal))
                            < _semantic_object_count(goal)
                        ):
                            status = "unknown"
                            invalid.append(
                                f"goal {goal_id} lacks distinct business evidence for "
                                "all requested objects"
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

    A link's URL and a post/product heading are real identity; a named link
    without a URL still has its title.  A changing DOM element id is never
    identity, so browser repaint or a reused id cannot confirm a different
    object or turn one object into several.  When there is no stable identity
    this returns an empty string and callers keep the effect unknown rather
    than inventing a key.
    """
    del fallback_url  # Kept for call compatibility; a page URL alone is not per-object.
    if atom is None:
        return ""
    if atom.url:
        return "url:" + atom.url
    if atom.role == "heading" and atom.name.strip():
        return "name:" + atom.name.strip()
    if atom.role == "link" and atom.name.strip():
        return "name:" + atom.name.strip()
    preceding = [item for item in view.atoms if item.line_no < atom.line_no]
    for candidate in reversed(preceding):
        if candidate.role in {"link", "heading"} and candidate.url:
            return "url:" + candidate.url
        if candidate.role == "heading" and candidate.name.strip():
            return "name:" + candidate.name.strip()
        if candidate.role == "link" and candidate.name.strip():
            return "name:" + candidate.name.strip()
    return ""


def _vote_effect(
    pending: PendingAction,
    view: AXView,
) -> tuple[bool, AXAtom | None, str]:
    """Read the toggled vote control that proves the dispatched vote landed.

    The candidate must belong to the same acted object by stable URL/title
    identity.  A DOM element id is not identity: a repaint or a reused id that
    now points at another post must stay unknown, and no stable identity means
    no confirmation rather than an invented one.
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
    if not source_key:
        return False, None, ""

    def same_object(atom: AXAtom) -> bool:
        return bool(source_key and _same_stable_identity(view, source_key, atom))

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
    if atom is not None and _persistent_vote_control(atom) and same_object(atom):
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
        key = object_key(view, atom, frame.url)
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
            if _record_object(
                goal,
                pending,
                state=state,
                frame=frame,
                atom=effect_atom,
                quote=effect_quote,
                source="ax_vote_state",
            ):
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
    readback_step = pending.expected.get("readback_step")
    queried = type(readback_step) is int and pending.step <= readback_step < frame.step
    if unresolved and unchanged and not confirmed_ids and not queried:
        # Missing receipts and an unchanged page do not disprove a commit.
        # Require an explicit readback before a no-effect retry is permitted.
        for goal in unresolved:
            goal.status = "unknown"
            goal.reason = "unchanged result requires read-only verification before retry"
        source = "ax_unchanged_unconfirmed"
    elif unresolved and unchanged and not confirmed_ids:
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
    effect_goals = [goal for goal in goals if goal.kind != "semantic"]
    action_confirmed = bool(effect_goals) and all(
        goal.goal_id in confirmed_ids or goal.status == "verified"
        for goal in effect_goals
    )
    if action_confirmed:
        # The dispatched action's own effect is settled.  Semantic scope checks
        # (newest/top-N/topic) belong to the task, not to this action's write, so
        # they neither keep the write guard active nor let a later stop pass.
        outcome = "confirmed"
    elif goals and all(
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
    history = history_observations(frame, state)
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
        "history_evidence": history,
        "history_evidence_note": (
            "source_id hN is a local, evidence-only label over the supplied "
            "Frame.history; step/observation_version are null when the platform "
            "did not provide them"
        ),
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
                         "quote": "exact substring of that AX line"},
                        {"history_id": "hN from history_evidence",
                         "quote": "exact substring of that history text"},
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
            "Exact field/cart values need current AX evidence inside that field/object region; "
            "the same text in an unrelated post, product listing or empty region is not proof.",
            "Never invent goals, line numbers or quotes; missing evidence must be unknown.",
            "History IDs hN are verification evidence only, never action targets. Every history "
            "quote must occur in the supplied history_evidence text for that ID.",
            "Current AX evidence is still required; history can only add prior comparison/order "
            "facts to a semantic check. Step/version null means unknown, not invented.",
            "Counts/states must be observed in the current AX, not inferred from the click.",
            "A persistent post-action vote toggle is current business evidence that this vote "
            "landed, even inside an HTML form; an untouched vote button, draft textbox or "
            "success alert is not evidence.",
            "A vote toggle proves only vote state. Newest/latest/ranking/top-N/subreddit/"
            "object scope needs the concrete business heading/link/title and, for ordering, "
            "the supplied history showing the object's position.",
            "Identify objects by URL/title/heading, never by DOM element id. A new id is not "
            "a new object and a reused id after a repaint is not proof; unstable identity "
            "must stay unknown.",
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
    "history_observations",
    "judge_goals",
    "object_key",
    "parse_ax",
    "parse_verification",
    "resolve_pending",
]
