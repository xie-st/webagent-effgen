"""Single-observation/single-action local harness; platform adapter is separate."""
import argparse
import importlib
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright
from sandbox import Fixture, LocalServer

ROOT = Path(__file__).resolve().parent


class BrowserAdapter:
    def __init__(self, page, base_url):
        self.page, self.base_url = page, base_url
        self.elements = {}
        self.revision = 0

    def observe(self):
        self.revision += 1
        self.elements = {}
        lines = []
        for element in self.page.locator('a,button,input,textarea,select').all():
            if not element.is_visible():
                continue
            element_id = str(self.revision * 1000 + len(self.elements) + 1)
            self.elements[element_id] = element
            name = element.get_attribute('aria-label') or element.get_attribute('name') or element.inner_text()
            lines.append(f'[{element_id}] {element.evaluate("e => e.tagName.toLowerCase()")}: {name}')
        return {"type": "local_axtree", "url": self.page.url,
                "text": self.page.locator('body').aria_snapshot() + '\n当前可用元素编号：\n' + '\n'.join(lines)}

    def act(self, action):
        match = re.fullmatch(r'(click|type|press|scroll|goto|stop)(?:\s+(.*))?', action.strip(), re.S)
        if not match:
            raise ValueError('Unsupported action; expected one local action')
        kind, payload = match.groups()
        payload = payload or ''
        if kind == 'stop':
            return 'stopped'
        if kind == 'goto':
            url = payload.strip('[]')
            if urlparse(url).netloc != urlparse(self.base_url).netloc:
                raise ValueError('Practice runner only permits its own loopback origin')
            self.page.goto(url)
        elif kind == 'scroll':
            direction = payload.strip('[]')
            if direction not in ('up', 'down'):
                raise ValueError('scroll [up] or scroll [down]')
            self.page.mouse.wheel(0, 600 if direction == 'down' else -600)
        elif kind == 'press':
            self.page.keyboard.press(payload.strip('[]'))
        else:
            target = re.fullmatch(r'\[(\d+)\](?:\s+\[(.*)\])?', payload, re.S)
            if not target or target[1] not in self.elements:
                raise ValueError('Element ID is missing or stale; observe again')
            if kind == 'click':
                if target[2] is not None:
                    raise ValueError('click accepts only one element ID')
                self.elements[target[1]].click()
            else:
                if target[2] is None:
                    raise ValueError('type [id] [text]')
                self.elements[target[1]].fill(target[2])
        # An action consumes its observation; old IDs cannot be replayed.
        self.elements = {}
        return 'executed'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent', required=True, help='module:function, signature matching decide()')
    parser.add_argument('--task', choices=['profile', 'post', 'reply', 'subscribe', 'vote', 'cart', 'checkout'], default='profile')
    parser.add_argument('--scenario', choices=['normal', 'slow', 'rate', 'login'], default='normal')
    parser.add_argument('--headed', action='store_true')
    parser.add_argument('--max-steps', type=int, default=40)
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--output-dir', type=Path,
                        help='Result directory; defaults to the stable project result root')
    args = parser.parse_args()
    module, function = args.agent.split(':')
    decide = getattr(importlib.import_module(module), function)
    fixture = Fixture(delay=0.8 if args.scenario == 'slow' else 0,
                      rate_once=args.scenario == 'rate', require_login=args.scenario == 'login')
    state, history, actions = {}, [], []
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    result_dir = args.output_dir or ROOT.parents[1] / '01_文本' / '05_测试结果' / 'local' / run_id
    result_dir.mkdir(parents=True, exist_ok=True)
    output = result_dir / 'actions.jsonl'
    if output.exists():
        raise ValueError('Output directory already contains a run; choose a new directory')
    source = Path(importlib.import_module(module).__file__)
    snapshot = result_dir / 'snapshot'
    snapshot.mkdir(exist_ok=True)
    (snapshot / 'runner.py').write_bytes(Path(__file__).read_bytes())
    (snapshot / source.name).write_bytes(source.read_bytes())
    manifest = {'kind': 'local_synthetic_result', 'run_id': run_id, 'agent': args.agent,
                'task': args.task, 'scenario': args.scenario, 'official_score': False,
                'agent_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'status': 'running'}
    (result_dir / 'run.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    with LocalServer(fixture) as server, sync_playwright() as pw, output.open('w', encoding='utf-8') as log:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()
        page.goto(server.url + ('/shop' if args.task in ('cart', 'checkout') else '/forum'))
        adapter = BrowserAdapter(page, server.url)
        started = time.perf_counter()
        try:
            for step in range(args.max_steps):
                if time.perf_counter() - started > args.timeout:
                    break
                observation = adapter.observe()
                before = time.perf_counter()
                response = decide(task=fixture.task(args.task), observation=observation,
                                  history=history, action_history=actions, state=state)
                decision_seconds = time.perf_counter() - before
                action = response['action'] if isinstance(response, dict) else response
                try:
                    outcome = adapter.act(action)
                except Exception as exc:
                    outcome = f'{type(exc).__name__}: {exc}'
                metadata = response if isinstance(response, dict) else {}
                record = {'time': datetime.now(timezone.utc).isoformat(), 'url': observation['url'],
                          'action_type': action.split()[0], 'action': action, 'result': outcome,
                          'model_calls': metadata.get('model_calls'), 'tokens': metadata.get('tokens'),
                          'step': step, 'decision_seconds': decision_seconds}
                log.write(json.dumps(record, ensure_ascii=False) + '\n')
                log.flush()
                history.append({'observation': observation, 'result': outcome})
                actions.append(action)
                if outcome == 'stopped':
                    break
            summary = {'kind': 'local_synthetic_result', 'agent': args.agent, 'task': args.task,
                       'scenario': args.scenario, 'passed': fixture.grade(args.task),
                       'seconds': time.perf_counter() - started, 'steps': len(actions),
                       'official_score': False}
            log.write(json.dumps(summary, ensure_ascii=False) + '\n')
            manifest.update(status='completed', summary=summary)
            (result_dir / 'run.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            (result_dir / 'result.md').write_text(
                '# 本地合成任务\n\n' + json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(summary, ensure_ascii=False))
            print(output)
        finally:
            context.tracing.stop(path=str(output.with_suffix('.zip')))
            browser.close()


if __name__ == '__main__':
    main()
