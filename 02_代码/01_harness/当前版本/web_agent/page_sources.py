"""Small, current-observation DOM/HTML outline for ambiguous readback.

This is reference text, never action IDs or authoritative live input state.
No cache, background requests, extra model, selector generation or JS execution.
"""
from html.parser import HTMLParser
import hashlib
import re
import time

LIMIT = 6000
ATTRS = {"name", "type", "value", "method", "action", "href", "aria-label"}
SKIP = {"script", "style", "noscript"}


def _attributes(tag, attrs):
    attrs = dict(attrs)
    if attrs.get("type", "").lower() in {"password", "hidden"}:
        return ""
    return tag + " " + " ".join(
        f"{key}={value!r}" for key, value in attrs.items()
        if key in ATTRS and value is not None
    )


def _dom_outline(root):
    pending, parts, visited = [root], [], 0
    while pending and visited < 400:
        node = pending.pop()
        if not isinstance(node, dict):
            continue
        visited += 1
        tag = str(node.get("nodeName", "")).lower()
        if tag in SKIP or tag == "#comment":
            continue
        attrs = node.get("attributes", [])
        if isinstance(attrs, list):
            parts.append(_attributes(tag, zip(attrs[::2], attrs[1::2])))
        if tag == "#text":
            parts.append(str(node.get("nodeValue", "")))
        children = list(node.get("children", [])) + list(node.get("shadowRoots", []))
        if isinstance(node.get("contentDocument"), dict):
            children.append(node["contentDocument"])
        pending.extend(reversed(children))
    return "\n".join(part.strip() for part in parts if part.strip())[:LIMIT]


class _Outline(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skipping = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skipping += 1
        if not self.skipping and tag in {"input", "textarea", "form", "a", "button"}:
            self.parts.append(_attributes(tag, attrs))

    def handle_endtag(self, tag):
        if tag in SKIP and self.skipping:
            self.skipping -= 1

    def handle_data(self, text):
        if not self.skipping and text.strip():
            self.parts.append(text.strip())


def read_details(observation, *, step, deadline=None, sdk=None):
    """Prefer the inline DOM; download HTML only as a bounded fallback."""
    if deadline is not None and deadline - time.time() < 2:
        return ""
    dom = observation.get("dom")
    if isinstance(dom, dict) and isinstance(dom.get("root"), dict):
        return "DOM reference (attributes may not be live values):\n" + _dom_outline(dom["root"])
    meta = observation.get("html")
    if not isinstance(meta, dict) or meta.get("available") is False:
        return ""
    if (meta.get("step") != step
            or not re.fullmatch(r"[0-9a-f]{32}", str(meta.get("html_id", "")))):
        return ""
    try:
        if sdk is None:
            from third_party_agent import browser as sdk
        text = sdk.get_html(meta["html_id"])
        raw = text.encode("utf-8")
        if (len(raw) > 4 * 1024 * 1024 or len(raw) != meta.get("byte_size")
                or hashlib.sha256(raw).hexdigest() != meta.get("sha256")):
            return ""
        if deadline is not None and time.time() >= deadline:
            raise TimeoutError("Task execution deadline reached")
        parser = _Outline()
        parser.feed(text)
        return "HTML reference (attributes may not be live values):\n" + "\n".join(parser.parts)[:LIMIT]
    except TimeoutError:
        raise
    except (AttributeError, RuntimeError, ValueError, OSError):
        return ""
