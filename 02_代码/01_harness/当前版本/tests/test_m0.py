"""M0 behavior tests for frame mapping, runtime wiring and state isolation."""
import json
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import agent_logic
from my_agent import MyAgent
from web_agent import baseline
from web_agent.adapters import official
from web_agent.contracts import Capabilities
from web_agent.runtime import Runtime

OBS = {
    "type": "accessibility_tree",
    "url": "http://127.0.0.1:9876/forum",
    "text": "Tab 0 (current): forum\n[17] button Save\n[18] textbox Name",
}


def request(run_id="one", task="Save profile"):
    return {
        "run_id": run_id,
        "task": task,
        "observation": OBS,
        "execution_deadline": time.time() + 10,
    }


def reply(action, memory=None):
    value = {"action": action}
    if memory is not None:
        value["memory"] = memory
    return SimpleNamespace(text=json.dumps(value))


class FrameMappingTests(unittest.TestCase):
    def test_official_request_maps_all_frame_fields(self):
        source = request("frame-run", "Frame task")
        source.update(
            step=4,
            observation_version=9,
            previous_receipt={"result": "changed"},
            history=[{"observation": OBS, "action": "click [17]"}],
            action_history=["click [17]"],
        )
        source["observation"] = dict(OBS, tab=1)
        frame = official.frame_from_request(source, step=2)

        self.assertEqual(frame.task, "Frame task")
        self.assertEqual(frame.run_id, "frame-run")
        self.assertEqual((frame.step, frame.url, frame.tab), (4, OBS["url"], 1))
        self.assertEqual(frame.observation_version, 9)
        self.assertEqual(frame.ax, OBS["text"])
        self.assertGreater(frame.deadline, time.time())
        self.assertEqual(frame.previous_receipt, {"result": "changed"})
        self.assertEqual(frame.history, tuple(source["history"]))
        self.assertEqual(frame.action_history, ("click [17]",))

    def test_official_defaults_declare_limited_capabilities_and_empty_receipt(self):
        frame = official.frame_from_request(request("defaults"), step=0)

        self.assertEqual(frame.capabilities, Capabilities(True, False, False))
        self.assertTrue(frame.capabilities.single_tab)
        self.assertFalse(frame.capabilities.native_pause)
        self.assertFalse(frame.capabilities.screenshot)
        self.assertIsNone(frame.previous_receipt)
        self.assertEqual((frame.step, frame.tab, frame.observation_version), (0, 0, 0))


class RuntimeTests(unittest.TestCase):
    def test_public_entry_uses_injected_runtime_and_frame(self):
        calls = []

        class SpyRuntime:
            def advance(self, frame, state):
                calls.append((frame, state))
                return {"action": "click [17]"}

        agent = MyAgent(runtime=SpyRuntime())
        agent.reset({"run_id": "spy"})
        self.assertEqual(agent.step(request("spy")), {"action": "click [17]"})
        self.assertEqual(agent.step(request("spy")), {"action": "click [17]"})

        self.assertEqual(len(calls), 2)
        self.assertEqual([frame.step for frame, _ in calls], [0, 1])
        self.assertEqual(calls[0][0].task, "Save profile")
        self.assertIs(calls[0][1], agent.state)
        self.assertIs(calls[1][1], agent.state)

    def test_context_keeps_current_ax_ids_bounded_history_and_receipt(self):
        source = request("context")
        source.pop("execution_deadline")
        source.update(
            observation_version=3,
            history=[
                {"observation": {"url": "/a", "text": "[1] A"}, "action": "click [1]"},
                {"observation": {"url": "/b", "text": "[2] B"}, "action": "click [2]"},
                {"observation": {"url": "/c", "text": "[3] C"}, "action": "click [3]"},
                {"observation": {"url": "/b", "text": "[2] B"}, "action": "click [2]"},
                {"observation": OBS, "action": "click [17]"},
                {"observation": OBS, "action": "click [18]"},
            ],
            action_history=[f"scroll [{'down' if i % 2 else 'up'}]" for i in range(20)],
        )
        frame = official.frame_from_request(source, step=5)
        captured = []

        def capture(context, state):
            captured.append(context)
            return {"action": "click [17]"}

        Runtime(capture).advance(frame, {"memory": "kept facts", "_remaining_seconds": 12.5})
        context = captured[0]

        self.assertEqual(context.page, OBS["text"])
        self.assertEqual(context.current_ids, ("17", "18"))
        self.assertEqual(len(context.past_views), 2)
        self.assertEqual(len({view["url"] for view in context.past_views}), 2)
        self.assertTrue(all(view["url"] != OBS["url"] for view in context.past_views))
        self.assertEqual(len(context.recent_actions), 16)
        self.assertEqual(context.recent_actions[-1], "scroll [down]")
        self.assertEqual(context.memory, "kept facts")
        self.assertEqual(context.remaining_seconds, 12.5)
        self.assertEqual(context.observation_version, 3)
        self.assertEqual(context.capabilities, Capabilities(True, False, False))
        self.assertIsNone(context.previous_receipt)
        self.assertGreaterEqual(context.unchanged_count, 2)
        self.assertIn("page is unchanged", context.recovery_feedback)

    def test_valid_decision_calls_model_once(self):
        frame = official.frame_from_request(request("once"), step=0)
        state = {}
        with patch.object(agent_logic.model, "generate",
                          return_value=reply("click [17]", "saved")) as generate:
            result = Runtime(baseline.decide).advance(frame, state)

        self.assertEqual(result, {"action": "click [17]"})
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(state["memory"], "saved")

    def test_custom_port_stale_action_is_rejected_before_memory_merge(self):
        frame = official.frame_from_request(request("port"), step=0)
        state = {"memory": "kept facts"}

        def stale_port(context, task_state):
            return {"action": "click [999]", "memory": "stale note"}

        with self.assertRaisesRegex(ValueError, "CURRENT page"):
            Runtime(stale_port).advance(frame, state)
        self.assertEqual(state["memory"], "kept facts")


class StateTests(unittest.TestCase):
    def test_memory_continues_until_reset(self):
        agent = MyAgent()
        agent.reset({"run_id": "memory"})
        replies = [reply("click [17]", "first fact"),
                   reply("click [18]"),
                   reply("click [18]", "second fact")]
        with patch.object(agent_logic.model, "generate", side_effect=replies) as generate:
            agent.step(request("memory"))
            self.assertEqual(agent.state["memory"], "first fact")
            agent.step(request("memory"))
            second_context = json.loads(generate.call_args_list[1].args[0][1]["content"])
            self.assertEqual(second_context["memory"], "first fact")

            agent.reset({"run_id": "memory"})
            self.assertEqual(agent.state, {})
            agent.step(request("memory"))
            reset_context = json.loads(generate.call_args_list[2].args[0][1]["content"])
            self.assertEqual(reset_context["memory"], "")
            self.assertEqual(agent.state["memory"], "second fact")

    def test_close_clears_identity_and_requires_reset(self):
        agent = MyAgent()
        with patch.object(agent_logic.model, "generate", return_value=reply("click [17]")):
            agent.reset({"run_id": "close"})
            agent.step(request("close"))
            agent.close()
            self.assertEqual(agent.state, {})
            self.assertIsNone(agent.run_id)
            with self.assertRaisesRegex(ValueError, "reset"):
                agent.step(request("close"))

            agent.reset({"run_id": "close"})
            self.assertEqual(agent.state, {})
            self.assertEqual(agent.step(request("close")), {"action": "click [17]"})


class BehaviorTests(unittest.TestCase):
    def test_same_origin_goto_and_empty_stop_are_legal(self):
        self.assertEqual(agent_logic.validate_action("goto [http://127.0.0.1:9876/next]", OBS),
                         "goto [http://127.0.0.1:9876/next]")
        self.assertEqual(agent_logic.validate_action("stop []", OBS), "stop []")
        with self.assertRaises(ValueError):
            agent_logic.validate_action("goto [https://example.com/]", OBS)

    def test_invalid_current_id_is_corrected(self):
        agent = MyAgent()
        agent.reset({"run_id": "correct"})
        replies = [reply("click [999]"), reply("click [18]")]
        with patch.object(agent_logic.model, "generate", side_effect=replies) as generate:
            self.assertEqual(agent.step(request("correct")), {"action": "click [18]"})

        self.assertEqual(generate.call_count, 2)
        correction = generate.call_args_list[1].args[0]
        self.assertEqual(len(correction), 4)
        self.assertIn("Invalid output", correction[-1]["content"])

    def test_repeated_bad_reply_rotates_baseline_recovery_actions(self):
        agent = MyAgent()
        agent.reset({"run_id": "recover"})
        bad = '{"action":"click [999]"}'
        with patch.object(agent_logic.model, "generate",
                          side_effect=[SimpleNamespace(text=bad)] * 4) as generate:
            self.assertEqual(agent.step(request("recover")), {"action": "scroll [down]"})
            self.assertEqual(agent.step(request("recover")), {"action": "scroll [up]"})

        self.assertEqual(generate.call_count, 4)
        self.assertEqual(agent.state["_recovery_count"], 2)

    def test_memory_over_limit_is_rejected_then_corrected(self):
        agent = MyAgent()
        agent.reset({"run_id": "limit"})
        replies = [reply("click [17]", "x" * 10001),
                   reply("click [17]", "usable")]
        with patch.object(agent_logic.model, "generate", side_effect=replies) as generate:
            self.assertEqual(agent.step(request("limit")), {"action": "click [17]"})

        self.assertEqual(generate.call_count, 2)
        self.assertEqual(agent.state["memory"], "usable")

    def test_legacy_decide_signature_still_uses_runtime_state(self):
        state = {}
        with patch.object(agent_logic.model, "generate",
                          return_value=reply("click [17]", "legacy")) as generate:
            result = agent_logic.decide(
                task="Legacy task",
                observation=OBS,
                history=[],
                action_history=[],
                state=state,
            )

        self.assertEqual(result, {"action": "click [17]"})
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(state["memory"], "legacy")


if __name__ == "__main__":
    unittest.main()
