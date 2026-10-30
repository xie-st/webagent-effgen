"""Parse the official accessibility-tree text format used by the harness.

The local integration bridge renders the real browser DOM as the same text
shape the official client supplies to ``Runtime``::

    Tab 0 (current): page title
    [1] navigation
      [2] link 'Forum' url: http://127.0.0.1:8765/forum
    [3] heading 'Forum'
    [4] paragraph 'bio: old value'
    [5] textbox 'Biography'
    [6] button 'Save'

This module is standard-library only so both the Playwright environment and the
locked Runtime environment can import it.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_LINE = re.compile(r"^(\s*)\[(\d+)\]\s+([^\s]+)\s*(.*)$")
_NAME = re.compile(r"'((?:[^'\\]|\\.)*)'")
FORM_ROLES = frozenset(
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
BUSINESS_ROLES = frozenset({"StaticText", "heading", "paragraph"})
FIELD_MARKERS = {
    "bio": ("个人简介", "简介"),
    "title": ("帖子标题", "帖子"),
    "reply": ("回复内容", "回复"),
}
FIELD_COLON = ("：", ":")


@dataclass(frozen=True)
class Atom:
    """One numbered line in the rendered accessibility tree."""

    line: int
    element_id: str
    indent: int
    role: str
    name: str
    raw: str
    url: str | None = None
    checked: bool | None = None
    selected: bool | None = None
    focused: bool | None = None
    inside_form: bool = False
    inside_alert: bool = False


def quote_name(name: str) -> str:
    """Render a name in the single-quoted official AX shape."""
    escaped = name.replace("\\", "\\\\").replace("'", "\\'")
    return "'" + escaped + "'"


def _unescape(value: str) -> str:
    return value.replace("\\'", "'").replace("\\\\", "\\")


def parse_atoms(text: str) -> list[Atom]:
    """Parse numbered lines, keeping ancestor form/alert regions."""
    if not isinstance(text, str):
        return []
    parsed: list[dict] = []
    for index, raw in enumerate(text.splitlines(), start=1):
        match = _LINE.match(raw)
        if not match:
            continue
        indent = len(match.group(1).expandtabs(8))
        role, rest = match.group(3), match.group(4)
        name_match = _NAME.search(rest)
        name = _unescape(name_match.group(1)) if name_match else ""
        url_match = re.search(r"\burl:\s*(\S+)", rest)
        checked_match = re.search(r"\bchecked:\s*(true|false)", rest)
        selected_match = re.search(r"\bselected:\s*(true|false)", rest)
        focused_match = re.search(r"\bfocused:\s*(true|false)", rest)
        parsed.append(
            {
                "line": index,
                "element_id": match.group(2),
                "indent": indent,
                "role": role,
                "name": name,
                "raw": raw,
                "url": url_match.group(1) if url_match else None,
                "checked": checked_match.group(1) == "true" if checked_match else None,
                "selected": selected_match.group(1) == "true" if selected_match else None,
                "focused": focused_match.group(1) == "true" if focused_match else None,
            }
        )
    atoms: list[Atom] = []
    for position, item in enumerate(parsed):
        ancestors = []
        for previous in reversed(parsed[:position]):
            if previous["indent"] < item["indent"]:
                ancestors.append(previous)
                if previous["indent"] == 0:
                    break
        atoms.append(
            Atom(
                line=item["line"],
                element_id=item["element_id"],
                indent=item["indent"],
                role=item["role"],
                name=item["name"],
                raw=item["raw"],
                url=item["url"],
                checked=item["checked"],
                selected=item["selected"],
                focused=item["focused"],
                inside_alert=any(entry["role"] == "alert" for entry in ancestors),
                inside_form=any(entry["role"] in FORM_ROLES for entry in ancestors),
            )
        )
    return atoms


def business_atoms(atoms: list[Atom]) -> list[Atom]:
    return [
        atom
        for atom in atoms
        if atom.role in BUSINESS_ROLES
        and atom.name
        and not atom.inside_alert
        and not atom.inside_form
    ]


def _split_value(name: str) -> str | None:
    for colon in FIELD_COLON:
        if colon in name:
            return name.split(colon, 1)[1].strip()
    return None


def field_atom(atoms: list[Atom], field: str | None) -> tuple[Atom, str] | None:
    """Return the labelled business line for a scalar field, never a bare value.

    A task requirement is anchored by its field label (``个人简介：``).  An
    unrelated heading or article that merely contains the same text is not a
    match for the field.
    """
    markers = FIELD_MARKERS.get(str(field or "").casefold())
    if not markers:
        return None
    for atom in business_atoms(atoms):
        stripped = atom.name.strip()
        for marker in markers:
            if not stripped.startswith(marker):
                continue
            remainder = stripped[len(marker):].lstrip()
            if not remainder or remainder[0] not in FIELD_COLON:
                continue
            value = _split_value(stripped)
            if value is not None:
                return atom, value
    return None


def prefixed_atom(atoms: list[Atom], prefix: str) -> tuple[Atom, str] | None:
    """Return a labelled business line such as ``购物车：键盘``."""
    for atom in business_atoms(atoms):
        stripped = atom.name.strip()
        if not stripped.startswith(prefix):
            continue
        value = _split_value(stripped)
        if value is not None:
            return atom, value
    return None


def split_items(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[、,，]", value)
    return [part.strip() for part in parts if part.strip()]
