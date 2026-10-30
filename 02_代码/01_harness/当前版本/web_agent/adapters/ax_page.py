"""Shared AX numbering and real Playwright actions for M3 and local tests."""
from __future__ import annotations

from urllib.parse import urljoin, urlsplit
import re
import json

def quote_name(name):
    escaped = name.replace("\\", "\\\\").replace("'", "\\'")
    return "'" + escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + "'"


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
            if name.startswith('"') and name.endswith('"'):
                try:
                    name = json.loads(name)
                except ValueError:
                    pass
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


class AXPage:
    """Number and execute actions against the real current browser DOM."""

    def __init__(self, page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.revision = 0
        self.timeout_ms = 5000
        self.atoms: list[dict] = []
        self.locators: dict[str, object] = {}

    def observe(self) -> dict:
        self.revision += 1
        self.atoms = []
        self._clear_targets()
        try:
            title = self.page.title()
        except Exception:
            title = ""
        nodes = _parse_aria(self.page.locator("body").aria_snapshot())
        # ARIA snapshots collapse whitespace in static text. Preserve exact
        # multiline business text only where one visible DOM block uniquely
        # matches that same AX text; never join unrelated paragraph fragments.
        multiline, form_texts = {}, set()
        for form in self.page.locator('form').all():
            for item in _parse_aria(form.aria_snapshot()):
                form_texts.add(re.sub(r'\s+', ' ', item['name']).strip())
        # Form membership is independent of formatting. Include all visible
        # form descendants and bare text, even when ARIA omits an unnamed form.
        for text in self.page.locator('form').evaluate_all('''forms => forms.flatMap(form => {
            const texts=[];
            for (const e of [form,...form.querySelectorAll('*')]) {
                if (!e.matches('input,textarea,select,option,script,style') && e.getClientRects().length
                    && getComputedStyle(e).visibility !== 'hidden') texts.push(e.innerText || '');
            }
            const walker=document.createTreeWalker(form,NodeFilter.SHOW_TEXT);
            while(walker.nextNode()) {
                const n=walker.currentNode, p=n.parentElement;
                if(!p || p.closest('input,textarea,select,option,script,style') || getComputedStyle(p).visibility==='hidden') continue;
                const range=document.createRange();range.selectNodeContents(n);
                if(range.getClientRects().length) texts.push(n.textContent || '');
            }
            return texts;
        })'''):
            form_texts.add(re.sub(r'\s+', ' ', text).strip())
        for block in self.page.locator('pre,p,blockquote').evaluate_all('''elements => elements
            .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden'
                && !e.querySelector('input,textarea,select'))
            .map(e => ({text:e.innerText, form:!!e.closest('form')}))'''):
            text=block['text']
            key = re.sub(r'\s+', ' ', text).strip()
            if key in multiline and multiline[key] != text:
                multiline[key] = None
            elif key not in multiline:
                multiline[key] = text
        lines = [f"Tab 0 (current): {title}"]
        counts: dict[tuple[str, str], int] = {}
        next_id = 1
        for node in nodes:
            element_id = str(self.revision * 1_000_000 + next_id)
            next_id += 1
            role = node["role"]
            name = str(node["name"] or "").strip()
            if role == 'StaticText':
                exact = multiline.get(re.sub(r'\s+', ' ', name).strip())
                if exact is not None:
                    name = exact
            if role in _PW_ROLES:
                name = re.sub(r'\s+',' ',name)
            parts = [f"[{element_id}]", role]
            if role in {'StaticText','heading','paragraph','link','cell'} and re.sub(r'\s+', ' ', name).strip() in form_texts:
                parts.append('in_form: true')
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
            if pw_role is not None:
                key = (pw_role, name)
                index = counts.get(key, 0)
                counts[key] = index + 1
                handles = self.page.get_by_role(
                    pw_role, name=name, exact=True
                ).element_handles()
                locator = handles[index] if index < len(handles) else None
                if locator is not None:
                    self.locators[element_id] = locator
                else:
                    parts.append('disabled: true')
            if pw_role in {"textbox", "searchbox", "spinbutton"} and locator is not None:
                try:
                    value = str(locator.input_value(timeout=1000))
                except Exception:
                    value = locator.evaluate("el => el.isContentEditable ? el.innerText : ''") or ""
                parts.append("value: " + quote_name(value))
            if locator is not None and locator.evaluate("el => el === document.activeElement"):
                parts.append("focused: true")
            atom = {
                "id": element_id,
                "line": len(lines) + 1,
                "role": role,
                "name": name,
                "url": urljoin(self.base_url, url) if url else None,
            }
            self.atoms.append(atom)
            lines.append("  " * node["indent"] + " ".join(parts))
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

    def _clear_targets(self):
        for handle in self.locators.values():
            handle.dispose()
        self.locators = {}

    def _settle(self) -> None:
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=min(3000, self.timeout_ms))
        except Exception:
            pass

    def act(self, action: str) -> str:
        try:
            return self._act(action)
        finally:
            self._clear_targets()

    def _act(self, action: str) -> str:
        text = str(action or "").strip()
        if text.startswith("stop"):
            return "stopped"
        click = re.fullmatch(r"click \[(\d+)\]", text)
        if click:
            self._locator(click.group(1)).click(timeout=self.timeout_ms)
            self._settle()
            return "executed"
        typed = re.fullmatch(r"type \[(\d+)\] \[(.*)\] \[([01])\]", text, flags=re.S)
        if typed:
            locator = self._locator(typed.group(1))
            locator.type(typed.group(2), timeout=self.timeout_ms)
            if typed.group(3) == "1":
                locator.press("Enter")
                self._settle()
            return "executed"
        hover = re.fullmatch(r"hover \[(\d+)\]", text)
        if hover:
            self._locator(hover.group(1)).hover(timeout=self.timeout_ms)
            return "executed"
        goto = re.fullmatch(r"goto \[(.+)\]", text, flags=re.S)
        if goto:
            destination = goto.group(1)
            if (urlsplit(destination).scheme, urlsplit(destination).netloc) != (urlsplit(self.base_url).scheme, urlsplit(self.base_url).netloc):
                raise ValueError("local bridge only permits its own loopback origin")
            self.page.goto(destination, timeout=self.timeout_ms)
            self._settle()
            return "executed"
        if text in {"go_back", "go_forward"}:
            getattr(self.page, text)(timeout=self.timeout_ms)
            self._settle()
            return "executed"
        press = re.fullmatch(r"press \[(.*)\]", text, flags=re.S)
        if press:
            keys = "+".join("Control" if key.casefold() == "ctrl" else key
                            for key in press.group(1).split("+"))
            self.page.keyboard.press(keys)
            return "executed"
        scroll = re.fullmatch(r"scroll \[(up|down)\]", text)
        if scroll:
            self.page.mouse.wheel(0, 600 if scroll.group(1) == "down" else -600)
            return "executed"
        raise ValueError("unsupported action: " + text)
