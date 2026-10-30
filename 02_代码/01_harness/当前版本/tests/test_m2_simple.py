"""Default M2 is one actor call per step, with optional inline readback."""
import hashlib
import json
import time
import unittest
from dataclasses import replace
from types import SimpleNamespace

from web_agent.adapters import official
from web_agent.model_port import SdkModelPort
from web_agent.policy import EffGenPolicy
from web_agent.runtime import Runtime
from web_agent.state import TaskState
from web_agent.page_sources import read_details

TASK = 'Change my bio to "New bio"'


def frame(text, step=0):
    return official.frame_from_request({
        "run_id": "simple", "task": TASK, "step": step,
        "execution_deadline": time.time() + 100,
        "observation": {"type": "accessibility_tree", "tab": 0,
                        "url": "https://example.test/profile", "text": text},
    }, step=step)


class SimpleFlowTests(unittest.TestCase):
    def test_near_deadline_finishes_incomplete_without_model_call(self):
        current = replace(frame("[1] button 'Save'"), deadline=time.time() + 1)
        def no_call(context, state):
            self.fail("must reserve time for final-state grading")
        result = Runtime(decision_port=no_call).advance(current, TaskState({}))
        self.assertTrue(result["action"].startswith("stop [Incomplete:"))

    def test_replacement_must_not_save_an_appended_value(self):
        from web_agent import recover
        state = TaskState({})
        initial = frame("[1] textbox 'Biography'\n [3] StaticText 'Old bio'\n[2] button 'Save'")
        Runtime(decision_port=lambda c,s: "type [1] [New bio] [0]").advance(initial, state)
        current = frame("[4] textbox 'Biography'\n [5] StaticText 'Old bioNew bio'\n[6] button 'Save'", 1)
        with self.assertRaisesRegex(ValueError, "WHOLE field"):
            recover.guard_action(current, state, "click [6]")
        self.assertIsNone(state.pending_for(0))

    def test_unknown_write_does_not_spawn_a_second_model_call(self):
        class Sdk:
            calls = 0
            def generate(self, messages):
                self.calls += 1
                action = "click [2]" if self.calls == 1 else "goto [https://example.test/profile]"
                return SimpleNamespace(text=json.dumps({"action": action}), request_id="simple")
        sdk = Sdk()
        policy = EffGenPolicy(model_port=SdkModelPort(sdk=sdk))
        self.assertFalse(hasattr(policy, "verify"))
        runtime = Runtime(policy=policy)
        state = TaskState({})
        text = "[1] textbox 'Biography'\n[2] button 'Save'"
        runtime.advance(frame(text), state)
        runtime.advance(frame(text + "\n[3] alert 'Saved'", 1), state)
        self.assertEqual(sdk.calls, 2)
        self.assertIsNotNone(state.pending_for(0))

    def test_inline_failed_readback_releases_only_the_failed_write(self):
        class Policy:
            def generate(self, context, state):
                return json.dumps({"action": "click [2]", "checks": [{
                    "goal_id": "goal-1", "status": "failed", "actual": "Old bio",
                    "source_task_quote": TASK,
                    "evidence": [{"line": 1, "quote": "Old bio"}],
                    "reason": "The saved value is still Old bio, not New bio",
                }]})
        state = TaskState({})
        Runtime(decision_port=lambda c,s: "click [2]").advance(
            frame("[1] textbox 'Biography'\n[2] button 'Save'"), state
        )
        current = frame("[1] StaticText 'Old bio'\n"
                        "[2] link 'Edit biography' url: https://example.test/profile/edit", 1)
        self.assertEqual(Runtime(policy=Policy()).advance(current, state), {"action": "click [2]"})
        self.assertIsNone(state.pending_for(0))
        self.assertEqual(state.goal_checks[0].status, "failed")


class PageSourceTests(unittest.TestCase):
    def test_inline_dom_needs_no_download_and_omits_script_and_node_ids(self):
        class Sdk:
            def get_html(self, value):
                raise AssertionError("DOM is already inline")
        dom = {"root": {"nodeName": "HTML", "nodeId": 987654, "children": [
            {"nodeName": "SCRIPT", "children": [{"nodeName": "#text", "nodeValue": "malicious()"}]},
            {"nodeName": "INPUT", "attributes": ["name", "bio", "value", "Old bio"]},
        ]}}
        text = read_details({"dom": dom}, step=0, sdk=Sdk())
        self.assertIn("Old bio", text)
        self.assertNotIn("987654", text)
        self.assertNotIn("malicious", text)

    def test_html_checks_observation_binding_hash_and_filters_script(self):
        html = '<script>do_not_execute()</script><form method="post"><input name="bio" value="Old"></form>'
        raw = html.encode()
        meta = {"html_id": "a" * 32, "step": 4, "byte_size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest()}
        sdk = SimpleNamespace(get_html=lambda _: html)
        text = read_details({"html": meta}, step=4, sdk=sdk)
        self.assertIn("method='post'", text)
        self.assertNotIn("do_not_execute", text)
        self.assertEqual(read_details({"html": meta}, step=5, sdk=sdk), "")
        self.assertEqual(read_details({"html": {**meta, "sha256": "0" * 64}}, step=4, sdk=sdk), "")

    def test_older_observation_and_sdk_are_optional(self):
        self.assertEqual(read_details({}, step=0), "")
        self.assertEqual(read_details({"html": {"available": False}}, step=0), "")
        self.assertEqual(read_details({"dom": {"available": False}}, step=0), "")

    def test_no_download_when_deadline_is_near(self):
        sdk = SimpleNamespace(get_html=lambda _: self.fail("must not download"))
        self.assertEqual(read_details({"html": {"html_id": "a" * 32, "step": 0}},
                                      step=0, deadline=time.time() + 0.5, sdk=sdk), "")


if __name__ == "__main__":
    unittest.main()
