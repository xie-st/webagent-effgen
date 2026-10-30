"""Actual local HTTP + Edge tests. Deterministic decisions, zero model calls."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from playwright.sync_api import sync_playwright
from web_agent.adapters.browser import BrowserSession, DraftSpec, Interrupted, MODEL_LOCK, create_context
from web_agent.adapters.ax_page import AXPage
from web_agent.runtime import Runtime
from web_agent.ax import AXTree


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(channel="msedge", headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.data = {"value": "Old bio", "writes": 0, "published": 0, "rate": 0}
        data = self.data
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                if self.path == "/rate" and data["rate"] == 0:
                    data["rate"] += 1
                    self.send_response(429)
                    self.send_header("Retry-After", "0.3")
                    self.end_headers()
                    self.wfile.write(b"Rate limited")
                    return
                if self.path == "/profile":
                    html = "<h1>Biography</h1><p>" + data["value"] + "</p>"
                else:
                    html = '''<h1>Profile</h1><label>Biography<input id="bio" value="Old bio"></label>
                    <button onclick="fetch('/save',{method:'POST',body:document.querySelector('#bio').value}).then(()=>location.href='/profile')">Save</button>
                    <label>Comment<textarea oninput="fetch('/publish',{method:'POST'})"></textarea></label>
                    <button onclick="fetch('/publish',{method:'POST'})">Publish</button>
                    <label>Subscribe<input type="checkbox" onchange="fetch('/publish',{method:'POST'})"></label>'''
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode())
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
                if self.path == "/save":
                    data["value"], data["writes"] = body, data["writes"] + 1
                elif self.path == '/lookup':
                    data['lookups']=data.get('lookups',0)+1
                else:
                    data["published"] += 1
                self.send_response(200)
                self.end_headers()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.context = create_context(self.browser)
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_runtime_replaces_and_confirms_last_write(self):
        actions = iter(["click", "select", "type", "save", "stop"])
        def decide(ctx, state):
            view = AXTree(type("F", (), {"ax": ctx.page})())
            ids = {a.name: a.element_id for a in view.nodes}
            stage = next(actions)
            return {"click": f"click [{ids.get('Biography')}]", "select": "press [Ctrl+A]",
                    "type": f"type [{ids.get('Biography')}] [New bio] [0]",
                    "save": f"click [{ids.get('Save')}]", "stop": "stop [done]"}[stage]
        session = BrowserSession(self.page, Runtime(decision_port=decide),
            task='Change my bio to "New bio"', url=self.url, deadline=time.time() + 30)
        self.assertTrue(session.run().complete)
        self.assertEqual(self.data["value"], "New bio")
        self.assertEqual(self.data["writes"], 1)
        self.assertIsNone(session.state.pending_for(0))

    def test_typing_appends_and_ids_expire(self):
        self.page.goto(self.url)
        adapter = AXPage(self.page, self.url)
        obs = adapter.observe()
        atom = next(a for a in adapter.atoms if a["name"] == "Biography" and a["role"] == "textbox")
        old_id = atom["id"]
        adapter.act(f"type [{old_id}] [New] [0]")
        self.assertIn("New", self.page.get_by_role("textbox", name="Biography").input_value())
        self.assertNotEqual(self.page.get_by_role("textbox", name="Biography").input_value(), "New")
        with self.assertRaises(ValueError): adapter.act(f"click [{old_id}]")

    def test_real_429_defers_the_next_navigation(self):
        runtime = Runtime(decision_port=lambda c,s: f"goto [{self.url}/profile]")
        session = BrowserSession(self.page, runtime, task="Read profile", url=self.url + "/rate",
                                 deadline=time.time() + 30)
        started = time.perf_counter()
        session.step()
        self.assertGreater(time.perf_counter() - started, 0.1)
        self.assertTrue(any(e["event"] == "rate_limit" for e in session.events))
        self.assertEqual(self.page.url, self.url + "/profile")

    def test_bound_target_survives_identical_controls_reordering(self):
        self.page.goto(self.url)
        self.page.set_content("<button id='a' onclick=\"window.selected='a'\">Vote</button>"
                              "<button id='b' onclick=\"window.selected='b'\">Vote</button>")
        adapter = AXPage(self.page, self.url)
        adapter.observe()
        first = next(a["id"] for a in adapter.atoms if a["name"] == "Vote")
        self.page.evaluate("document.body.prepend(document.querySelector('#b'))")
        adapter.act(f"click [{first}]")
        self.assertEqual(self.page.evaluate("window.selected"), "a")

    def test_draft_is_screenshotted_then_cancelled_without_publish(self):
        text = "感谢分享\n感谢支持 😊"
        def decide(ctx, state):
            if state.memory:
                return "stop [draft ready]"
            import re
            element = re.search(r"\[(\d+)\] textbox 'Comment'", ctx.page).group(1)
            return {"action": f"type [{element}] [{text}] [0]", "memory": "typed"}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "draft.png"
            session = BrowserSession(self.page, Runtime(decision_port=decide), task="Draft only, do not send",
                url=self.url, deadline=time.time() + 30, draft=DraftSpec("Comment", text, str(path)))
            self.assertTrue(session.run().complete)
            self.assertTrue(path.is_file())
            self.assertEqual(self.data["published"], 0)
            self.assertEqual(self.page.get_by_role("textbox", name="Comment").input_value(), "")
            self.assertTrue(any(e["event"] == "network_write_blocked" for e in session.events))

    def test_draft_mode_blocks_publish_before_dispatch(self):
        def decide(ctx, state):
            import re
            element = re.search(r"\[(\d+)\] button 'Publish'", ctx.page).group(1)
            return f"click [{element}]"
        session = BrowserSession(self.page, Runtime(decision_port=decide), task="Draft only",
            url=self.url, deadline=time.time() + 30, draft=DraftSpec("Comment", "Thanks 😊", "unused.png"))
        with self.assertRaises(PermissionError): session.step()
        self.assertEqual(self.data["published"], 0)
        self.assertEqual(session.state.pending_actions(), [])

    def test_draft_blocks_space_and_autosave_checkbox(self):
        for kind in ("space", "checkbox"):
            if kind == "checkbox":
                self.context.close()
                self.context = create_context(self.browser)
                self.page = self.context.new_page()
            def decide(ctx, state):
                import re
                if kind == "space": return "press [Space]"
                element = re.search(r"\[(\d+)\] checkbox 'Subscribe'", ctx.page).group(1)
                return f"click [{element}]"
            session = BrowserSession(self.page, Runtime(decision_port=decide), task="Draft only",
                url=self.url, deadline=time.time() + 30, draft=DraftSpec("Comment", "Thanks 😊", "unused.png"))
            self.page.get_by_role("button", name="Publish").focus()
            with self.assertRaises(PermissionError): session.step()
            self.assertEqual(self.data["published"], 0)

    def test_readonly_is_enforced_before_write(self):
        def decide(ctx, state):
            import re
            element = re.search(r"\[(\d+)\] button 'Save'", ctx.page).group(1)
            return f"click [{element}]"
        session = BrowserSession(self.page, Runtime(decision_port=decide), task="Read only",
            url=self.url, deadline=time.time() + 30, readonly=True)
        with self.assertRaises(PermissionError): session.step()
        self.assertEqual(self.data["writes"], 0)

    def test_readonly_search_can_clear_and_replace_without_writing(self):
        import json
        from types import SimpleNamespace
        calls=[]
        def generate(ctx,state):
            calls.append(1)
            if len(calls)>1:return json.dumps({'action':'stop [ready]'})
            field=next(node for node in AXTree(type('F',(),{'ax':ctx.page})()).nodes if node.role=='searchbox')
            return json.dumps({'action':f'type [{field.element_id}] [NEW] [0]'})
        session=BrowserSession(self.page,Runtime(policy=SimpleNamespace(generate=generate)),task='Search only',url=self.url,deadline=time.time()+30,readonly=True)
        self.page.set_content('<input type="search" aria-label="Search" value="OLD">')
        self.assertTrue(session.run().complete)
        self.assertEqual(self.page.get_by_role('searchbox').input_value(),'NEW')
        self.assertEqual(self.data['writes'],0)

    def test_second_session_cannot_override_context_guard(self):
        runtime = Runtime(decision_port=lambda c,s: "scroll [down]")
        BrowserSession(self.page, runtime, task="Draft only", url=self.url,
                       deadline=time.time() + 30, draft=DraftSpec("Comment", "Thanks 😊", "unused.png"))
        with self.assertRaisesRegex(ValueError, "isolated"):
            BrowserSession(self.context.new_page(), runtime, task="Write", url=self.url,
                           deadline=time.time() + 30)

    def test_readonly_search_can_submit_get_in_chinese_or_english(self):
        from types import SimpleNamespace
        import json
        for label in ['Search', '搜索']:
            with self.subTest(label=label):
                calls=[]
                def generate(ctx,state):
                    calls.append(1)
                    if len(calls)==1:
                        field=next(node for node in AXTree(type('F',(),{'ax':ctx.page})()).nodes if node.name==label)
                        return json.dumps({'action':f'type [{field.element_id}] [NEW] [0]'})
                    return json.dumps({'action':'press [Enter]' if len(calls)==2 else 'stop [ready]'})
                context=create_context(self.browser)
                page=context.new_page()
                try:
                    session=BrowserSession(page,Runtime(policy=SimpleNamespace(generate=generate)),task='Search only',url=self.url,deadline=time.time()+30,readonly=True)
                    page.set_content(f'<form method="GET" action="{self.url}/search"><input name="q" aria-label="{label}" value="OLD"></form>')
                    self.assertTrue(session.run().complete)
                    self.assertEqual(page.url,self.url+'/search?q=NEW')
                    self.assertEqual(self.data['writes'],0)
                    self.assertEqual(self.data['published'],0)
                finally:
                    context.close()

    def test_contenteditable_value_is_observed_and_cancelled(self):
        session=BrowserSession(self.page,Runtime(decision_port=lambda *_:'stop [ready]'),task='Draft only',
            url=self.url,deadline=time.time()+30,draft=DraftSpec('Comment','Thanks 😊','unused.png'))
        self.page.set_content('<div role="textbox" aria-label="Comment" contenteditable="true">Thanks 😊</div>')
        observation=session.adapter.observe()
        self.assertIn('Thanks 😊',observation['text'])
        session.cancel_draft()
        self.assertEqual(self.page.get_by_role('textbox',name='Comment').inner_text().strip(),'')

    def test_hidden_nonempty_editor_does_not_claim_cancellation(self):
        with tempfile.TemporaryDirectory() as folder:
            session=BrowserSession(self.page,Runtime(decision_port=lambda *_:'stop [ready]'),task='Draft only',
                url=self.url,deadline=time.time()+30,draft=DraftSpec('Comment','Thanks',str(Path(folder)/'draft.png')))
            self.page.set_content('<textarea aria-label="Comment" style="display:none">Thanks</textarea>')
            with self.assertRaisesRegex(RuntimeError,'unconfirmed'):
                session._finish_draft()
            self.assertFalse(any(event.get('event')=='draft_cancelled' for event in session.events))

    def test_publish_endpoint_cannot_be_whitelisted_as_read(self):
        with self.assertRaises(ValueError):
            BrowserSession(self.page,Runtime(decision_port=lambda *_:'stop []'),task='Read',url=self.url,
                deadline=time.time()+30,readonly=True,read_post_urls=(self.url+'/publish',))

    def test_encoded_publish_endpoint_cannot_bypass_read_exception_validation(self):
        with self.assertRaises(ValueError):
            BrowserSession(self.page,Runtime(decision_port=lambda *_:'stop []'),task='Read',url=self.url,
                deadline=time.time()+30,readonly=True,read_post_urls=(self.url+'/comment/%70ost',))

    def test_read_post_exception_does_not_release_other_posts(self):
        session=BrowserSession(self.page,Runtime(decision_port=lambda *_:'stop [read]'),task='Read',url=self.url,
            deadline=time.time()+30,readonly=True,read_post_urls=(self.url+'/lookup',))
        self.page.evaluate("fetch('/lookup',{method:'POST'}).then(r=>r.text())")
        self.page.evaluate("fetch('/publish',{method:'POST'}).catch(()=> 'blocked')")
        self.assertEqual(self.data.get('lookups'),1)
        self.assertEqual(self.data['published'],0)

    def test_takeover_invalidates_old_save_without_releasing_nonidempotent_commits(self):
        session=BrowserSession(self.page,Runtime(decision_port=lambda *_:'scroll [down]'),task='Edit',url=self.url,deadline=time.time()+30)
        session.state.add_completed('commit','save:profile:key',{'actual':['New bio']})
        session.state.add_completed('commit','post:thread:key',{'actual':['Thanks']})
        session.pause();session.resume()
        self.assertFalse(session.state.completed_has('commit','save:profile:key'))
        self.assertTrue(session.state.completed_has('commit','post:thread:key'))
        self.assertTrue(session.state.unresolved)

    def test_screenshot_failure_still_cancels_draft(self):
        def decide(ctx, state): return "stop [draft ready]"
        session = BrowserSession(self.page, Runtime(decision_port=decide), task="Draft only",
            url=self.url, deadline=time.time() + 30, draft=DraftSpec("Comment", "Thanks 😊", "unused.png"))
        self.page.get_by_role("textbox", name="Comment").fill("Thanks 😊")
        with patch.object(self.page, "screenshot", side_effect=RuntimeError("capture failed")):
            with self.assertRaisesRegex(RuntimeError, "capture failed"): session.step()
        self.assertEqual(self.page.get_by_role("textbox", name="Comment").input_value(), "")
        self.assertEqual(self.data["published"], 0)

    def test_model_queue_pause_does_not_wait_for_other_model(self):
        session = BrowserSession(self.page, Runtime(decision_port=lambda c,s:self.fail("no model")),
            task="Read", url=self.url, deadline=time.time() + 30)
        thread = threading.Thread(target=lambda: (time.sleep(0.05), session.pause()))
        MODEL_LOCK.acquire()
        thread.start()
        started = time.perf_counter()
        try:
            with self.assertRaises(Interrupted): session.step()
        finally:
            MODEL_LOCK.release()
        thread.join()
        self.assertLess(time.perf_counter() - started, 1)

    def test_dispatched_io_failure_advances_step_and_keeps_unknown(self):
        def decide(ctx, state):
            import re
            element = re.search(r"\[(\d+)\] button 'Save'", ctx.page).group(1)
            return f"click [{element}]"
        session = BrowserSession(self.page, Runtime(decision_port=decide),
            task='Change my bio to "New bio"', url=self.url, deadline=time.time() + 30)
        with patch.object(session.adapter, "act", side_effect=TimeoutError("unknown transport")):
            with self.assertRaises(TimeoutError): session.step()
        self.assertEqual(len(session.actions), 1)
        self.assertEqual(session.history[-1]["result"], "unknown")
        self.assertIsNotNone(session.state.pending_for(0))

    def test_takeover_during_decision_suppresses_action_and_reobserves(self):
        started = threading.Event()
        session = None
        def decide(ctx, state):
            started.set()
            session.paused.wait(2)
            import re
            element = re.search(r"\[(\d+)\] button 'Save'", ctx.page).group(1)
            return f"click [{element}]"
        runtime = Runtime(decision_port=decide)
        session = BrowserSession(self.page, runtime, task='Change my bio to "New bio"',
                                 url=self.url, deadline=time.time() + 30)
        thread = threading.Thread(target=lambda: (started.wait(), session.pause()))
        thread.start()
        with self.assertRaises(Interrupted): session.step()
        thread.join()
        self.assertEqual(self.data["writes"], 0)
        self.page.get_by_role("textbox", name="Biography").fill("Human edit")
        session.resume()
        seen = []
        runtime.decision_port = lambda ctx,state: (seen.append(ctx.page) or "scroll [down]")
        session.step()
        self.assertIn("Human edit", seen[0])
        self.assertEqual(session.state.pending_actions(), [])


if __name__ == "__main__":
    unittest.main()
