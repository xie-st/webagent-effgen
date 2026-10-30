"""Real browser task loop over the existing M2 Runtime, with cooperative takeover."""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import threading
import time
from urllib.parse import urlsplit
from uuid import uuid4

from .ax_page import AXPage
from ..contracts import Capabilities, Frame
from ..state import TaskState
from .. import operations
from ..ax import AXTree

MODEL_LOCK = threading.Lock()


def create_context(browser, **kwargs):
    """Isolated context whose service workers cannot bypass request routing."""
    context = browser.new_context(service_workers="block", **kwargs)
    context._webagent_network_guarded = True
    return context


def origin(url):
    p = urlsplit(url)
    if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise ValueError("Expected an HTTP(S) origin without credentials")
    return f"{p.scheme}://{p.netloc}"


class Interrupted(RuntimeError):
    pass


class SiteLimiter:
    """One shared Retry-After/spacing clock per origin, across all tabs."""
    def __init__(self, spacing=0.0, backoff=1.0):
        self.spacing, self.backoff = spacing, backoff
        self.until, self.lock = {}, threading.Lock()

    def defer(self, site, retry_after=None):
        try:
            delay = float(retry_after)
        except (TypeError, ValueError):
            try:
                delay = (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                delay = self.backoff
        with self.lock:
            self.until[site] = max(self.until.get(site, 0), time.monotonic() + max(0, delay))

    def wait(self, site, deadline, interrupted):
        while True:
            if interrupted():
                raise Interrupted("Task paused or cancelled")
            if time.time() >= deadline:
                raise TimeoutError("Browser task deadline reached")
            with self.lock:
                delay = self.until.get(site, 0) - time.monotonic()
                if delay <= 0:
                    self.until[site] = time.monotonic() + self.spacing
                    return
            time.sleep(min(delay, 0.05))


@dataclass(frozen=True)
class StepResult:
    action: str
    stopped: bool
    complete: bool


@dataclass(frozen=True)
class DraftSpec:
    field_label: str
    text: str
    screenshot: str


class BrowserSession:
    """Own one tab/task; Playwright calls stay on its creating thread.

    pause() can be called from a controller thread. It waits for an in-flight
    step, then returns progress; resume() forces fresh observation/evidence.
    A model port is injected through Runtime; no model service is invented.
    """
    def __init__(self, page, runtime, *, task, url, deadline, tab=0,
                 limiter=None, cancelled=None, draft=None, readonly=False, read_post_urls=()):
        self.page, self.runtime, self.task = page, runtime, task
        self.deadline, self.tab, self.site = deadline, tab, origin(url)
        self.run_id, self.state = uuid4().hex, TaskState({})
        self.current_url = url
        if getattr(runtime, 'initial_memory', None):
            self.state.memory = runtime.initial_memory
        self.telemetry = getattr(runtime, '_telemetry', None)
        if self.telemetry is not None:
            self.telemetry.bind_run(self.run_id)
            self.telemetry.run_start(task=task, deadline=deadline)
        self.adapter = AXPage(page, url)
        self.history, self.actions, self.events = [], [], []
        self.paused, self.step_lock = threading.Event(), threading.RLock()
        self.cancelled = cancelled or threading.Event()
        self.limiter = limiter or SiteLimiter()
        self.owner, self.ended = threading.get_ident(), False
        self._resume_values = []
        self.draft = draft
        self.readonly = readonly
        self.read_post_urls = frozenset(read_post_urls)
        for address in self.read_post_urls:
            parsed=urlsplit(address)
            if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.query or parsed.fragment or parsed.username or parsed.password or '%' in parsed.path or '\\' in parsed.path:
                raise ValueError('Read POST allowlist requires exact HTTP(S) endpoint URLs')
            if any(part in parsed.path.casefold() for part in ('/publish','/comment/post','/comment/create','/like','/vote','/checkout','/order/create')):
                raise ValueError('A publishing/mutation endpoint cannot be a read POST exception')
        if getattr(page.context, "_webagent_session_owner", None) is not None:
            raise ValueError("Each BrowserSession requires an isolated BrowserContext")
        if (draft is not None or readonly) and not getattr(page.context, "_webagent_network_guarded", False):
            raise ValueError("Use create_context() for guarded read-only/draft tasks")
        if getattr(runtime, "_browser_session_owner", None) is not None:
            raise ValueError("Each BrowserSession requires its own Runtime")
        page.context._webagent_session_owner = self
        runtime._browser_session_owner = self
        if draft is not None:
            self.runtime.completion_check = self._draft_complete
        page.context.route("**/*", self._route)
        page.on("popup", lambda popup: popup.close())
        page.on("response", self._response)
        self._check()
        self.limiter.wait(self.site, deadline, self._interrupted)
        page.goto(url, timeout=self._timeout())

    def _route(self, route):
        req = route.request
        permitted_post = req.method == 'POST' and req.url in self.read_post_urls
        if (self.draft is not None or self.readonly) and req.method not in {"GET", "HEAD", "OPTIONS"} and not permitted_post:
            parsed=urlsplit(req.url)
            self.events.append({"event": "network_write_blocked", "method": req.method,'endpoint':parsed.scheme+'://'+parsed.netloc+parsed.path})
            route.abort()
            return
        try:
            allowed = not (req.is_navigation_request() and req.frame.parent_frame is None
                           and origin(req.url) != self.site)
        except ValueError:
            allowed = False
        route.continue_() if allowed else route.abort()

    def _draft_complete(self, frame, state):
        return not state.pending_actions() and any(
            atom.role == "textbox" and atom.name == self.draft.field_label
            and AXTree(frame).control_value(atom) == self.draft.text
            for atom in AXTree(frame).nodes
        )

    def _finish_draft(self):
        from pathlib import Path
        path = Path(self.draft.screenshot)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.page.screenshot(path=str(path))
        finally:
            cancelled = self.cancel_draft()
        if cancelled != 'cleared':
            raise RuntimeError('Draft cancellation is unconfirmed')
        self.events.append({"event": "draft_cancelled", "screenshot": str(path)})

    def cancel_draft(self):
        if self.draft is None:
            return 'not_applicable'
        field = self.page.get_by_role("textbox", name=self.draft.field_label, exact=True,include_hidden=True)
        if field.count() != 1:
            return 'unconfirmed'
        value = lambda: field.evaluate("el => el.isContentEditable ? el.innerText : el.value")
        if not field.is_visible():
            return 'cleared' if not str(value() or '').strip() else 'unconfirmed'
        # Clear only the draft we just verified; never click a submit control.
        field.fill("")
        if str(value() or '').strip():
            raise RuntimeError('Draft was not cleared')
        self.page.keyboard.press("Escape")
        remaining = value() if field.count()==1 else ''
        if isinstance(remaining,str) and remaining.strip():
            raise RuntimeError("Draft was not cancelled")
        return 'cleared'

    def _response(self, response):
        if response.status == 429 and origin(response.url) == self.site:
            self.limiter.defer(self.site, response.headers.get("retry-after"))
            self.events.append({"event": "rate_limit", "url": response.url})

    def _interrupted(self):
        return self.paused.is_set() or self.cancelled.is_set()

    def _timeout(self):
        return max(1, min(15000, int((self.deadline - time.time()) * 1000)))

    def _check(self):
        if threading.get_ident() != self.owner:
            raise RuntimeError("Browser I/O must stay on its owning thread")
        if self.ended or self._interrupted():
            raise Interrupted("Task ended, paused or cancelled")
        if time.time() >= self.deadline:
            raise TimeoutError("Browser task deadline reached")

    def checkpoint(self):
        return {"run_id": self.run_id, "steps": len(self.actions),
                "url": self.current_url,
                "last_action": self.actions[-1] if self.actions else None,
                "memory": self.state.memory,
                "completed_operations": self.state.completed,
                "last_readback": self.state.last_result,
                "deadline": self.deadline,
                "pending": [p.as_dict() for p in self.state.pending_actions()]}

    def pause(self):
        self.paused.set()
        with self.step_lock:
            self.events.append({"event": "paused"})
            return self.checkpoint()

    def resume(self):
        with self.step_lock:
            # Human interaction invalidates editor selections and state evidence,
            # but never erases unknown submissions or permits sending them again.
            self.state.clear_focus()
            self.state.data.pop("_input_sequence", None)
            for pending in self.state.pending_actions():
                if pending.operation == "input":
                    self.state.clear_pending(pending.tab)
            saves = [item for item in self.state.completed if item.get('kind') == 'commit' and item.get('key','').startswith('save:')]
            self._resume_values = [value for item in saves for value in item.get('detail',{}).get('actual',[]) if isinstance(value,str)]
            self.state.data["_completed"] = [item for item in self.state.completed
                if item.get("kind") == "commit" and not item.get('key','').startswith('save:')]
            self.state.data.pop("_drafts", None)
            for key in ("_last_fingerprint", "_stalled_steps", "_last_result"):
                self.state.data.pop(key, None)
            if self.state.pending_actions():
                self.state.mark_unresolved("human takeover: query pending business result before writing")
            elif self._resume_values:
                self.state.mark_unresolved("human takeover: recheck saved fields before completion")
            else:
                self.state.mark_resolved()
            self.history.clear()
            self.paused.clear()
            self.events.append({"event": "resumed", "requires_observation": True})

    def step(self):
        try:
            return self._step()
        except Exception as exc:
            if self.telemetry is not None:
                self.telemetry.step_error(step=len(self.actions),error=exc)
            if not self.paused.is_set():
                self.cancel_draft()
            raise

    def _step(self):
        with self.step_lock:
            self._check()
            self.limiter.wait(self.site, self.deadline, self._interrupted)
            self.adapter.timeout_ms = self._timeout()
            self.page.set_default_timeout(self._timeout())
            self.page.set_default_navigation_timeout(self._timeout())
            obs = self.adapter.observe()
            self.current_url = obs['url']
            frame = Frame(task=self.task, run_id=self.run_id, step=len(self.actions),
                          url=obs["url"], tab=self.tab, observation_version=obs["version"],
                          ax=obs["text"], deadline=self.deadline,
                          capabilities=Capabilities(False, True, False),
                          history=tuple(self.history[-8:]), action_history=tuple(self.actions[-16:]))
            if self._resume_values:
                visible = AXTree(frame).business_texts()
                if not self.state.pending_actions() and all(value in visible for value in self._resume_values):
                    self.state.mark_resolved()
                self._resume_values = []
            if self.telemetry is not None:
                self.telemetry.observation(step=frame.step,url=frame.url,
                    observation_version=frame.observation_version,deadline=self.deadline,
                    remaining_seconds=max(0,self.deadline-time.time()))
            before = deepcopy(self.state.data)
            while not MODEL_LOCK.acquire(timeout=0.05):
                self._check()
            try:
                self._check()
                decision = self.runtime.advance(frame, self.state)
            finally:
                MODEL_LOCK.release()
            if self._interrupted():
                self.state.data.clear()
                self.state.data.update(before)
                raise Interrupted("Takeover/cancel requested before action dispatch")
            try:
                self._check()
            except Exception:
                self.state.data.clear()
                self.state.data.update(before)
                raise
            action = decision["action"]
            info = operations.plan(action, frame, self.state)
            keys = action[7:-1].casefold() if action.startswith("press [") else None
            safe_keys = {"escape", "tab", "shift+tab", "ctrl+a", "control+a",
                         "ctrl+end", "control+end", "end", "home",
                         "arrowup", "arrowdown", "arrowleft", "arrowright", "pageup", "pagedown"}
            forbidden = info.write or (info.node is not None and info.node.role in {"checkbox", "radio", "option", "combobox"})
            if self.readonly and self.draft is None and info.kind == 'search' and keys in {'enter', 'return'}:
                safe_keys.add(keys)
            if keys == 'backspace':
                focused=AXTree(frame).focused_field()
                draft_field = self.draft is not None and focused is not None and focused.name==self.draft.field_label
                search_field = self.readonly and focused is not None and (focused.role=='searchbox' or 'search' in focused.name.casefold() or '搜索' in focused.name)
                if draft_field or search_field:
                    safe_keys.add('backspace')
            forbidden = forbidden or (keys is not None and keys not in safe_keys)
            if self.readonly:
                forbidden = forbidden or info.kind == "input"
            if (self.draft is not None or self.readonly) and forbidden:
                self.state.data.clear()
                self.state.data.update(before)
                raise PermissionError("Read-only/draft task forbids this possible write")
            # Rate limits may arrive while a model decision is in flight.
            dispatched = False
            try:
                self.page.wait_for_timeout(0)
                self.limiter.wait(self.site, self.deadline, self._interrupted)
                self._check()
                dispatched = True
                result = self.adapter.act(action)
            except Exception:
                if dispatched:
                    self.actions.append(action)
                    self.history.append({"observation": obs, "action": action, "result": "unknown"})
                    self.events.append({"event": "action_failed", "outcome": "unknown"})
                else:
                    self.state.data.clear()
                    self.state.data.update(before)
                if not self.paused.is_set():
                    self.cancel_draft()
                raise
            self.actions.append(action)
            self.history.append({"observation": obs, "action": action, "result": result})
            stopped = result == "stopped"
            self.ended = stopped
            complete = stopped and not action.startswith("stop [Incomplete:")
            if stopped and complete and self.draft is not None:
                self._finish_draft()
            elif stopped:
                self.cancel_draft()
            self.events.append({"event": "action", "tab": self.tab, "action": action})
            if self.telemetry is not None:
                self.telemetry.action(step=frame.step,action=action)
                if stopped:
                    self.telemetry.finish('stop' if complete else 'incomplete')
            return StepResult(action, stopped, complete)

    def close(self):
        try:
            self.cancel_draft()
        finally:
            if self.telemetry is not None:
                self.telemetry.finish('close')

    def run(self):
        while True:
            result = self.step()
            if result.stopped:
                return result
