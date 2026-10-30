"""Small accessibility-tree reader used by local operation checks.

This module deliberately does not extract task goals or ask a model to prove a
claim.  It only reads the current AX: element roles/names, explicit control
state, live input values when the SDK exposes them, and the nearest business
text.  Missing values stay missing; DOM/HTML is never treated as live input.
"""
from __future__ import annotations

from dataclasses import dataclass
import ast
import re
from typing import Iterable

from .contracts import Frame

_LINE = re.compile(r"^(\s*)\[(\d+)\]\s+([^\s]+)\s*(.*)$")
_QUOTED = re.compile(r"'((?:[^'\\]|\\.)*)'")
_VALUE = re.compile(
    r"\bvalue\s*[:=]\s*(?:'((?:[^'\\]|\\.)*)'|\"([^\"]*)\"|([^\s]+))",
    re.I,
)
_URL = re.compile(r"\burl:\s*(\S+)")
_BOOL = re.compile(r"\b(checked|selected|focused|pressed|expanded|disabled):\s*(true|false)", re.I)
_FORM_ROLES = frozenset(
    {"form", "textbox", "searchbox", "combobox", "option", "checkbox", "radio",
     "spinbutton", "slider", "listbox", "menuitem"}
)
_FIELD_ROLES = frozenset({"textbox", "searchbox", "combobox", "spinbutton", "slider"})
_STATE_WORDS = (
    "upvote", "downvote", "vote", "like", "subscribe", "follow",
    "点赞", "踩", "投票", "订阅", "关注",
)
_RETRACT_WORDS = (
    "retract", "undo", "unvote", "unlike", "unfollow", "unsubscribe",
    "remove vote", "remove upvote", "remove downvote", "take back",
    "取消点赞", "取消踩", "取消订阅", "取消关注", "已点赞", "已踩", "已订阅", "已关注",
)


def _unescape(value: str) -> str:
    try:
        return ast.literal_eval("'" + value + "'")
    except (SyntaxError, ValueError):
        return value.replace("\\'", "'").replace("\\\\", "\\")


@dataclass(frozen=True)
class Node:
    line_no: int
    element_id: str
    role: str
    name: str
    raw: str
    indent: int
    url: str | None
    value: str | None
    checked: bool | None
    selected: bool | None
    pressed: bool | None
    expanded: bool | None
    disabled: bool | None
    inside_alert: bool
    inside_form: bool
    inside_nav: bool
    section: str
    descendants: tuple["Node", ...] = ()

    @property
    def field_key(self) -> dict[str, str | None]:
        return {"role": self.role, "name": self.name, "section": self.section}

    @property
    def state(self) -> bool | None:
        for value in (self.pressed, self.checked, self.selected):
            if value is not None:
                return value
        text = self.name.casefold()
        if any(word in text for word in _RETRACT_WORDS):
            return True
        if any(word in text for word in _STATE_WORDS):
            return False
        return None

    @property
    def control_kind(self) -> str | None:
        text = self.name.casefold()
        if "upvote" in text or "点赞" in text:
            return "upvote"
        if "downvote" in text or "踩" in text:
            return "downvote"
        if "subscribe" in text or "订阅" in text:
            return "subscribe"
        if "follow" in text or "关注" in text:
            return "follow"
        if "unlike" in text or "like" in text:
            return "like"
        if "vote" in text or "投票" in text:
            return "vote"
        return self.role if self.role in {"checkbox", "radio", "option", "switch"} else None

    @property
    def is_retract(self) -> bool:
        text = self.name.casefold()
        return any(word in text for word in _RETRACT_WORDS)

    @property
    def stem(self) -> str:
        text = self.name
        for word in _RETRACT_WORDS + _STATE_WORDS:
            text = re.sub(re.escape(word), " ", text, flags=re.I)
        return re.sub(r"\s+", " ", text).strip(" -_:：·|")


class AXTree:
    """One immutable view over the current accessibility tree."""

    def __init__(self, frame: Frame):
        self.frame = frame
        self.nodes: list[Node] = []
        self.by_id: dict[str, Node] = {}
        self._parse()

    def _parse(self) -> None:
        rows: list[dict] = []
        for index, raw in enumerate(self.frame.ax.splitlines(), start=1):
            match = _LINE.match(raw)
            if not match:
                continue
            indent = len(match.group(1).expandtabs(8))
            element_id, role, rest = match.group(2), match.group(3), match.group(4)
            name_match = _QUOTED.search(rest)
            name = _unescape(name_match.group(1)) if name_match else ""
            value_match = _VALUE.search(rest)
            explicit_value = None
            if value_match:
                explicit_value = _unescape(next(group for group in value_match.groups() if group is not None))
            flags = {key.casefold(): value == "true" for key, value in _BOOL.findall(rest)}
            url_match = _URL.search(rest)
            rows.append({
                "line_no": index,
                "element_id": element_id,
                "role": role,
                "name": name,
                "raw": raw,
                "indent": indent,
                "url": url_match.group(1) if url_match else None,
                "value": explicit_value,
                "checked": flags.get("checked"),
                "selected": flags.get("selected"),
                "pressed": flags.get("pressed"),
                "expanded": flags.get("expanded"),
                "disabled": flags.get("disabled"),
            })
        for position, row in enumerate(rows):
            ancestors = []
            ancestor_indent = row["indent"]
            for previous in reversed(rows[:position]):
                if previous["indent"] < ancestor_indent:
                    ancestors.append(previous)
                    ancestor_indent = previous["indent"]
                    if previous["indent"] == 0:
                        break
            descendants = []
            for following in rows[position + 1:]:
                if following["indent"] <= row["indent"]:
                    break
                descendants.append(following)
            section = ""
            for previous in reversed(rows[:position]):
                if previous["role"] in {"heading", "link", "paragraph"} and previous["name"]:
                    if previous["role"] == "heading" or len(previous["name"]) >= 5:
                        section = previous["name"]
                        break
            node = Node(
                line_no=row["line_no"],
                element_id=row["element_id"],
                role=row["role"],
                name=row["name"],
                raw=row["raw"],
                indent=row["indent"],
                url=row["url"],
                value=row["value"],
                checked=row["checked"],
                selected=row["selected"],
                pressed=row["pressed"],
                expanded=row["expanded"],
                disabled=row["disabled"],
                inside_alert=any(entry["role"] == "alert" for entry in ancestors),
                inside_form=any(entry["role"] in _FORM_ROLES for entry in ancestors),
                inside_nav=any(entry["role"] in {"navigation", "banner", "contentinfo"} for entry in ancestors),
                section=section,
                descendants=tuple(_node_from_row(entry, ancestors + [row]) for entry in descendants),
            )
            self.nodes.append(node)
            self.by_id[node.element_id] = node

    def find_field(self, key: dict | None) -> Node | None:
        if not isinstance(key, dict):
            return None
        candidates = [
            node for node in self.nodes
            if node.role == key.get("role") and node.name == key.get("name")
        ]
        if not candidates:
            return None
        section = key.get("section")
        if section:
            scoped = [node for node in candidates if node.section == section]
            return scoped[0] if len(scoped) == 1 else None
        return candidates[0] if len(candidates) == 1 else None

    def focused_field(self) -> Node | None:
        fields = [node for node in self.nodes if node.role in _FIELD_ROLES]
        for node in fields:
            if node.pressed is None and "focused: true" in node.raw.casefold():
                return node
        for node in fields:
            if "focused: true" in node.raw.casefold():
                return node
        return None

    def control_value(self, node: Node | None) -> str | None:
        if node is None:
            return None
        if node.value is not None:
            return node.value
        text_nodes = [child for child in node.descendants
                      if child.role in {"StaticText", "text", "LineBreak"}]
        if any(child.role == 'LineBreak' for child in text_nodes):
            return ''.join('\n' if child.role == 'LineBreak' else child.name
                           for child in text_nodes)
        values = [child.name for child in text_nodes]
        if values:
            return "\n".join(values)
        # Some AX writers expose the editable value as a child text node with
        # no role.  Only a direct child is accepted, never the field label.
        for child in node.descendants:
            if child.role in {"#text", "text"} and child.name:
                return child.name
        return None

    def business_texts(self) -> list[str]:
        return [
            node.name for node in self.nodes
            if node.role in {"StaticText", "heading", "paragraph", "link", "cell"}
            and node.name
            and not node.inside_form
            and not node.inside_alert
            and not node.inside_nav
        ]

    def visible_texts(self) -> list[str]:
        return [
            node.name for node in self.nodes
            if node.role in {"StaticText", "heading", "paragraph", "link", "cell"}
            and node.name
            and not node.inside_nav
        ]

    def controls_for(self, kind: str, object_key: str | None = None) -> list[Node]:
        matches = [node for node in self.nodes if node.control_kind == kind]
        if object_key:
            return [node for node in matches if self.object_key(node) == object_key]
        return matches

    def object_key(self, node: Node) -> str:
        stem = node.stem
        if len(stem) >= 4:
            return self.frame.url + "#" + stem.casefold()
        if node.section:
            return self.frame.url + "#" + node.section.casefold()
        if node.url:
            return node.url
        return self.frame.url + "#" + f"{node.role}:{node.name}".casefold()

    def has_error_text(self) -> str | None:
        markers = (
            "error", "invalid", "required", "failed", "cannot", "could not",
            "错误", "失败", "不能", "无效", "必填", "请填写", "请选择",
        )
        for text in self.visible_texts():
            lowered = text.casefold()
            if any(marker in lowered for marker in markers):
                return text
        return None

    def success_marker(self) -> str | None:
        markers = (
            "success", "saved", "posted", "created", "confirmed", "thank you",
            "order number", "order #", "成功", "已保存", "已发布", "已提交",
            "订单号", "订单已", "感谢",
        )
        for text in self.visible_texts():
            lowered = text.casefold()
            if any(marker in lowered for marker in markers):
                return text
        return None


def _node_from_row(row: dict, ancestors: Iterable[dict]) -> Node:
    ancestor_list = list(ancestors)
    return Node(
        line_no=row["line_no"],
        element_id=row["element_id"],
        role=row["role"],
        name=row["name"],
        raw=row["raw"],
        indent=row["indent"],
        url=row["url"],
        value=row["value"],
        checked=row["checked"],
        selected=row["selected"],
        pressed=row["pressed"],
        expanded=row["expanded"],
        disabled=row["disabled"],
        inside_alert=any(entry["role"] == "alert" for entry in ancestor_list),
        inside_form=any(entry["role"] in _FORM_ROLES for entry in ancestor_list),
        inside_nav=any(entry["role"] in {"navigation", "banner", "contentinfo"} for entry in ancestor_list),
        section="",
        descendants=(),
    )


def text_contains(texts: Iterable[str], value: str) -> bool:
    target = _normalise(value)
    if not target:
        return False
    return any(target in _normalise(text) for text in texts)


def _normalise(value: str) -> str:
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


__all__ = ["AXTree", "Node", "text_contains"]
