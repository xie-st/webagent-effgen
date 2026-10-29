"""Public action rules applied to every decision port."""
from __future__ import annotations

import re
from urllib.parse import urlsplit


def validate_action(text, observation):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('action must be a nonempty string')
    text = text.strip()
    # Normalize the common equivalent shorthand before strict ID validation.
    shorthand = re.fullmatch(r'type \[(\d+)\] (.+) ([01])', text, flags=re.S)
    if shorthand:
        text = f'type [{shorthand.group(1)}] [{shorthand.group(2)}] [{shorthand.group(3)}]'
    element = re.fullmatch(r'(?:click|hover) \[(\d+)\]', text)
    if element is None:
        element = re.fullmatch(r'type \[(\d+)\] \[.*\] \[[01]\]', text, flags=re.S)
    if element:
        ids = set(re.findall(r'^\s*\[(\d+)\]', observation['text'], flags=re.M))
        if element.group(1) not in ids:
            raise ValueError('Use an element ID from the CURRENT page')
        return text
    if text in ('go_back', 'go_forward', 'scroll [up]', 'scroll [down]'):
        return text
    if re.fullmatch(r'(?:press|stop) \[.*\]', text, flags=re.S):
        return text
    target = re.fullmatch(r'goto \[(.+)\]', text)
    if target:
        current, destination = urlsplit(observation['url']), urlsplit(target.group(1))
        if (current.scheme, current.netloc) == (destination.scheme, destination.netloc) and not destination.username and not destination.password:
            return text
    raise ValueError('Return a complete action, for example click [725], not a bare action name')
