"""Local-only official-protocol browser adapter for the M2 Runtime bridge.

The older ``runner.BrowserAdapter`` emits a local ``[a] tag: name`` list plus an
ARIA YAML snapshot.  That is enough for scripted environment checks but not for
the harness's official AX parser, which requires ``[id] role 'name'`` lines with
ancestor regions, links and attributes.  This adapter converts the real DOM's
Playwright ARIA snapshot into that official text shape, numbers the current
observation, records visible input values and keeps role locators so actions
are executed in the actual Chromium page.

It is deliberately a test adapter: it does not implement M3 browser,
multi-tab, credential, scheduler or production policies.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlsplit
import re

from m2_ax_text import quote_name

_PW_ROLES = {
    "button": "button",
    "link": "link",
    "textbox": "textbox",
    "searchbox": "searchbox",
    "checkbox": "checkbox",
    "radio": "radio",
    "combobox": "combobox",
    "option": "option",
    "menuitem": "menuitem",
    "tab": "tab",
    "slider": "slider",
    "spinbutton": "spinbutton",
    "listbox": "listbox",
}
_NODE = re.compile(r"^-\s+([A-Za-z][A-Za-z0-9]*)\s*(.*)$")
_QUOTED = re.compile(r'^"((?:[^"\\]|\\.)*)"')
_FLAG = re.compile(r"\[([A-Za-z]+)(?:=([^\]]+))?\]")


def _unescape(value: str) -> str:
    return value.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def _parse_aria(snapshot: str) -> list[dict]:
    """Parse the constrained YAML emitted by ``locator.aria_snapshot()``."""
    nodes: list[dict] = []
    previous: dict | None = None
    for raw in (snapshot or "").splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        indent = (len(raw) - len(raw.lstrip(" "))) // 2
        if stripped.startswith("- /"):
            if previous is not None:
                key, _, value = stripped[3:].partition(":")
                attribute = key.strip()
                if attribute == "url":
                    previous["url"] = value.strip()
                else:
                    previous.setdefault("attributes", {})[attribute] = value.strip()
            continue
        match = _NODE.match(stripped)
        if not match:
            continue
        role, rest = match.group(1), match.group(2).strip()
        name = ""
        if rest.startswith('"'):
            quoted = _QUOTED.match(rest)
            if quoted:
                name = _unescape(quoted.group(1))
                rest = rest[quoted.end():].strip()
        elif rest.startswith(":"):
            name = rest[1:].strip()
        flags = {}
        for flag, value in _FLAG.findall(rest):
            flags[flag.casefold()] = value if value else True
        if role == "text":
            role = "StaticText"
        node = {
            "indent": indent,
            "role": role,
            "name": name,
            "url": None,
            "attributes": flags,
        }
        nodes.append(node)
        previous = node
    return nodes


class OfficialProtocolAdapter:
    """Number and execute actions against the real current browser DOM."""

    def __init__(self, page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.revision = 0
        self.atoms: list[dict] = []
        self.locators: dict[str, object] = {}

    def observe(self) -> dict:
        self.revision += 1
        self.atoms = []
        self.locators = {}
        try:
            title = self.page.title()
        except Exception:
            title = ""
        nodes = _parse_aria(self.page.locator("body").aria_snapshot())
        lines = [f"Tab 0 (current): {title}"]
        counts: dict[tuple[str, str], int] = {}
        next_id = 1
        for node in nodes:
            element_id = str(next_id)
            next_id += 1
            role = node["role"]
            name = re.sub(r"\s+", " ", str(node["name"] or "")).strip()
            parts = [f"[{element_id}]", role]
            if name:
                parts.append(quote_name(name))
            url = node.get("url")
            if url:
                parts.append("url: " + urljoin(self.base_url, url))
            attributes = node.get("attributes") or {}
            for key in ("checked", "selected", "focused", "disabled", "expanded"):
                if key not in attributes:
                    continue
                value = attributes[key]
                if value is True:
                    value = "true"
                parts.append(f"{key}: {value}")
            if "level" in attributes:
                parts.append(f"level: {attributes['level']}")
            pw_role = _PW_ROLES.get(role)
            locator = None
            if pw_role is not None and name:
                key = (pw_role, name)
                index = counts.get(key, 0)
                counts[key] = index + 1
                locator = self.page.get_by_role(
                    pw_role, name=name, exact=True
                ).nth(index)
                self.locators[element_id] = locator
            if pw_role == "textbox" and locator is not None:
                try:
                    value = str(locator.input_value(timeout=1000))
                except Exception:
                    value = ""
                if value:
                    parts.append("value: " + quote_name(value.replace("\n", " ")))
            atom = {
                "id": element_id,
                "line": len(lines) + 1,
                "role": role,
                "name": name,
                "url": urljoin(self.base_url, url) if url else None,
            }
            self.atoms.append(atom)
            lines.append(" ".join(parts))
        return {
            "type": "accessibility_tree",
            "url": self.page.url,
            "text": "\n".join(lines) + "\n",
            "tab": 0,
            "version": self.revision,
        }

    def _locator(self, element_id: str):
        locator = self.locators.get(str(element_id))
        if locator is None:
            raise ValueError("element id is missing or stale; observe again")
        return locator

    def _settle(self) -> None:
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:
            pass
        self.locators = {}

    def act(self, action: str) -> str:
        text = str(action or "").strip()
        if text.startswith("stop"):
            return "stopped"
        click = re.fullmatch(r"click \[(\d+)\]", text)
        if click:
            self._locator(click.group(1)).click(timeout=5000)
            self._settle()
            return "executed"
        typed = re.fullmatch(r"type \[(\d+)\] \[(.*)\] \[([01])\]", text, flags=re.S)
        if typed:
            locator = self._locator(typed.group(1))
            locator.fill(typed.group(2), timeout=5000)
            if typed.group(3) == "1":
                locator.press("Enter")
                self._settle()
            return "executed"
        hover = re.fullmatch(r"hover \[(\d+)\]", text)
        if hover:
            self._locator(hover.group(1)).hover(timeout=5000)
            return "executed"
        goto = re.fullmatch(r"goto \[(.+)\]", text, flags=re.S)
        if goto:
            destination = goto.group(1)
            if urlsplit(destination).netloc != urlsplit(self.base_url).netloc:
                raise ValueError("local bridge only permits its own loopback origin")
            self.page.goto(destination)
            self._settle()
            return "executed"
        press = re.fullmatch(r"press \[(.*)\]", text, flags=re.S)
        if press:
            self.page.keyboard.press(press.group(1))
            return "executed"
        scroll = re.fullmatch(r"scroll \[(up|down)\]", text)
        if scroll:
            self.page.mouse.wheel(0, 600 if scroll.group(1) == "down" else -600)
            return "executed"
        raise ValueError("unsupported action: " + text)
