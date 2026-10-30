"""M1a acceptance: real EffGen, fake SDK, telemetry and deadline behavior."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import effgen
from effgen import AgentConfig, BaseModel
from effgen.core.agent import AgentMode
from third_party_agent import model as sdk_model

import agent_logic
from my_agent import MyAgent
from web_agent import model_port as model_port_module
from web_agent import state as state_module
from web_agent.model_port import SdkModelPort
from web_agent.policy import EffGenPolicy, PlatformModel, SYSTEM, build_agent_config
from web_agent.state import TaskState
from web_agent.telemetry import Telemetry

OBS = {
    "type": "accessibility_tree",
    "url": "http://127.0.0.1:9876/forum",
    "text": "Tab 0 (current): forum\n[17] button Save\n[18] textbox Name",
}


def request(run_id="m1a", task="Save profile", deadline=None):
    return {
        "run_id": run_id,
        "task": task,
        "observation": OBS,
        "execution_deadline": deadline if deadline is not None else time.time() + 30,
    }


def reply(action, memory=None, request_id="fake-request"):
    value = {"action": action}
    if memory is not None:
        value["memory"] = memory
    return json.dumps(value), request_id


class FakeSdk:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        text, request_id = self.replies[len(self.calls) - 1]
        return SimpleNamespace(text=text, request_id=request_id)


def read_events(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


class EffGenWiringTests(unittest.TestCase):
    def test_real_effgen_version_and_disabled_features(self):
        self.assertEqual(effgen.__version__, "1.3.0")
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="config", path=Path(temporary) / "telemetry.jsonl")
            port = SdkModelPort(sdk=FakeSdk([]), telemetry=telemetry)
            policy = EffGenPolicy(model_port=port, telemetry=telemetry)
            self.assertIsInstance(policy.model, BaseModel)
            config = build_agent_config(policy.model)

        self.assertIsInstance(config, AgentConfig)
        self.assertEqual(config.tools, [])
        self.assertEqual(config.mode, AgentMode.SINGLE)
        self.assertFalse(config.enable_sub_agents)
        self.assertFalse(config.enable_memory)
        self.assertFalse(config.capability_probe)
        self.assertFalse(config.enable_fallback)
        self.assertFalse(config.speculative_execution)
        self.assertIsNone(config.models)
        self.assertIsNone(config.fallback_chain)
        self.assertEqual(config.max_iterations, 1)
        self.assertIsNone(config.max_turns_without_progress)
        self.assertEqual(config.system_prompt, SYSTEM)
        self.assertIsInstance(policy.model, PlatformModel)
        self.assertIs(agent_logic.model, sdk_model)
        self.assertEqual(agent_logic.SYSTEM, SYSTEM)
        self.assertTrue(callable(agent_logic.validate_action))
        self.assertTrue(callable(agent_logic.decide))


class DecisionTests(unittest.TestCase):
    def test_valid_decision_exactly_one_model_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="once", path=log)
            sdk = FakeSdk([reply("click [17]", "saved", "request-1")])
            port = SdkModelPort(sdk=sdk, telemetry=telemetry)
            agent = MyAgent(model_port=port, telemetry=telemetry)
            agent.reset({"run_id": "once", "task": "Save profile"})
            self.assertIsInstance(agent.runtime.policy, EffGenPolicy)
            self.assertEqual(agent.step(request("once")), {"action": "click [17]"})
            self.assertEqual(agent.state["memory"], "saved")
            agent.close()

            self.assertEqual(len(sdk.calls), 1)
            self.assertEqual([m["role"] for m in sdk.calls[0]], ["system", "user"])
            self.assertTrue(all(isinstance(m["content"], str) for m in sdk.calls[0]))
            payload = json.loads(sdk.calls[0][1]["content"])
            self.assertEqual(payload["task"], "Save profile")
            self.assertEqual(payload["memory"], "")

            events = read_events(log)
            starts = [e for e in events if e["event"] == "model_call_start"]
            ends = [e for e in events if e["event"] == "model_call_end"]
            self.assertEqual(len(starts), 1)
            self.assertEqual(len(ends), 1)
            self.assertLess(events.index(starts[0]), events.index(ends[0]))
            self.assertEqual(starts[0]["purpose"], "decision")
            self.assertEqual(starts[0]["call_seq"], 1)
            self.assertTrue(starts[0]["sdk_invoked"])
            self.assertEqual(ends[0]["purpose"], "decision")
            self.assertEqual(ends[0]["call_seq"], 1)
            self.assertEqual(ends[0]["request_id"], "request-1")
            self.assertTrue(ends[0]["success"])
            self.assertIsNone(starts[0]["prompt_tokens"])
            self.assertIsNone(ends[0]["total_tokens"])
            self.assertIsNone(ends[0]["cost_usd"])
            self.assertEqual([e["action"] for e in events if e["event"] == "decision"],
                             ["click [17]"])
            self.assertEqual(events[1]["event"], "observation")
            self.assertEqual(events[0]["event"], "run_start")
            end = [e for e in events if e["event"] == "run_end"][-1]
            self.assertEqual(end["model_calls"], 1)
            self.assertEqual(end["rejected_calls"], 0)
            self.assertEqual(end["by_purpose"], {"decision": 1})
            self.assertEqual(end["end_reason"], "close")
            self.assertTrue((Path(temporary) / "telemetry-summary.json").is_file())

    def test_observation_memory_continues_across_steps(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="memory", path=log)
            sdk = FakeSdk([
                reply("click [17]", "Customer record 42; next open detail"),
                reply("click [18]"),
            ])
            agent = MyAgent(model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                            telemetry=telemetry)
            agent.reset({"run_id": "memory", "task": "Find record 42"})
            agent.step(request("memory"))
            agent.step(request("memory"))
            agent.close()

            self.assertEqual(len(sdk.calls), 2)
            second = json.loads(sdk.calls[1][1]["content"])
            self.assertEqual(second["memory"], "Customer record 42; next open detail")
            self.assertEqual([m["role"] for m in sdk.calls[1]], ["system", "user"])

    def test_log_step_uses_platform_step_consistently(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="steps", path=log)
            sdk = FakeSdk([reply("click [17]")])
            agent = MyAgent(model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                            telemetry=telemetry)
            agent.reset({"run_id": "steps", "task": "Step alignment"})
            source = request("steps")
            source["step"] = 7
            agent.step(source)
            agent.close()

            events = read_events(log)
            self.assertEqual([e["step"] for e in events if e["event"] == "observation"], [7])
            self.assertEqual([e["step"] for e in events if e["event"] == "model_call_start"], [7])
            self.assertEqual([e["step"] for e in events if e["event"] == "decision"], [7])

    def test_stop_is_terminal_and_sets_end_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="stop", path=log)
            sdk = FakeSdk([reply("stop [done]")])
            agent = MyAgent(model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                            telemetry=telemetry)
            agent.reset({"run_id": "stop", "task": "Finish"})
            self.assertEqual(agent.step(request("stop")), {"action": "stop [done]"})
            with self.assertRaisesRegex(ValueError, "stop"):
                agent.step(request("stop"))
            agent.close()

            events = read_events(log)
            ends = [e for e in events if e["event"] == "run_end"]
            self.assertEqual(len(ends), 1)
            self.assertEqual(ends[0]["end_reason"], "stop")
            self.assertEqual(ends[0]["model_calls"], 1)
            self.assertEqual([e["action"] for e in events if e["event"] == "decision"],
                             ["stop [done]"])

    def test_invalid_output_correction_is_a_separate_logged_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="correct", path=log)
            sdk = FakeSdk([
                reply("click [999]", request_id="bad-request"),
                reply("click [18]", "fixed", "good-request"),
            ])
            agent = MyAgent(model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                            telemetry=telemetry)
            agent.reset({"run_id": "correct", "task": "Fix"})
            self.assertEqual(agent.step(request("correct")), {"action": "click [18]"})
            agent.close()

            self.assertEqual(len(sdk.calls), 2)
            correction = json.loads(sdk.calls[1][1]["content"])
            self.assertEqual(correction["correction"]["invalid_output"],
                             '{"action": "click [999]"}')
            self.assertIn("Invalid output", correction["correction"]["instruction"])
            starts = [e for e in read_events(log) if e["event"] == "model_call_start"]
            ends = [e for e in read_events(log) if e["event"] == "model_call_end"]
            self.assertEqual([e["purpose"] for e in starts], ["decision", "correction"])
            self.assertEqual([e["call_seq"] for e in starts], [1, 2])
            self.assertEqual([e["request_id"] for e in ends], ["bad-request", "good-request"])
            end = [e for e in read_events(log) if e["event"] == "run_end"][-1]
            self.assertEqual(end["model_calls"], 2)
            self.assertEqual(end["rejected_calls"], 0)
            self.assertEqual(end["by_purpose"], {"decision": 1, "correction": 1})

    def test_expired_deadline_does_not_reach_sdk_and_is_logged(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="deadline", path=log)
            sdk = FakeSdk([reply("click [17]")])
            agent = MyAgent(model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                            telemetry=telemetry)
            agent.reset({"run_id": "deadline", "task": "Too late"})
            with self.assertRaises(TimeoutError):
                agent.step(request("deadline", deadline=time.time() - 1))
            agent.close()

            self.assertEqual(len(sdk.calls), 0)
            events = read_events(log)
            starts = [e for e in events if e["event"] == "model_call_start"]
            rejected = [e for e in events if e["event"] == "model_call_rejected"]
            self.assertEqual(starts, [])
            self.assertGreaterEqual(len(rejected), 1)
            self.assertTrue(all(not event["sdk_invoked"] for event in rejected))
            self.assertTrue(all(event["error_type"] == "TimeoutError" for event in rejected))
            self.assertTrue(all(event["call_seq"] is None for event in rejected))
            end = [e for e in events if e["event"] == "run_end"][-1]
            self.assertEqual(end["model_calls"], 0)
            self.assertGreaterEqual(end["rejected_calls"], 1)
            self.assertEqual(end["end_reason"], "deadline")


class BudgetDeadlineTests(unittest.TestCase):
    def test_legacy_budget_keeps_one_absolute_deadline(self):
        """A later observation reuses the task deadline instead of renewing it."""
        class FakeClock:
            now = 1000.0

            def __call__(self):
                return self.now

        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            clock = FakeClock()
            fake_time = SimpleNamespace(time=clock)
            state = {"_remaining_seconds": 10}
            sdk = FakeSdk([
                reply("click [17]", request_id="first"),
                reply("click [18]", request_id="second"),
            ])
            with patch.dict(os.environ, {"WEBAGENT_TELEMETRY_PATH": str(log)}), \
                    patch.object(agent_logic, "time", fake_time), \
                    patch.object(state_module, "time", fake_time), \
                    patch.object(model_port_module, "time", fake_time), \
                    patch.object(agent_logic.model, "generate", side_effect=sdk.generate):
                agent_logic.decide(
                    task="Read page", observation=OBS, history=[],
                    action_history=[], state=state,
                )
                clock.now = 1005.0
                agent_logic.decide(
                    task="Read page", observation=OBS, history=[],
                    action_history=[], state=state,
                )
                clock.now = 1011.0
                with self.assertRaises(TimeoutError):
                    agent_logic.decide(
                        task="Read page", observation=OBS, history=[],
                        action_history=[], state=state,
                    )

            self.assertEqual(state["_execution_deadline"], 1010.0)
            self.assertEqual(len(sdk.calls), 2)
            events = read_events(log)
            observations = [e for e in events if e["event"] == "observation"]
            starts = [e for e in events if e["event"] == "model_call_start"]
            rejected = [e for e in events if e["event"] == "model_call_rejected"]
            self.assertEqual([e["deadline"] for e in observations], [1010.0] * 3)
            self.assertEqual([e["deadline"] for e in starts], [1010.0] * 2)
            self.assertGreaterEqual(len(rejected), 1)
            self.assertTrue(all(e["deadline"] == 1010.0 for e in rejected))
            self.assertTrue(all(not e["sdk_invoked"] for e in rejected))
            end = [e for e in events if e["event"] == "run_end"][-1]
            self.assertEqual(end["end_reason"], "deadline")
            self.assertEqual(end["model_calls"], 2)


class LifecycleTests(unittest.TestCase):
    def test_injected_port_logs_each_run_to_its_current_telemetry(self):
        """One injected port and telemetry survive two reset/close cycles."""
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(path=log)
            sdk = FakeSdk([reply("click [17]"), reply("click [18]")])
            port = SdkModelPort(sdk=sdk, telemetry=telemetry)
            agent = MyAgent(model_port=port, telemetry=telemetry)

            for run_id, action in (("first", {"action": "click [17]"}),
                                   ("second", {"action": "click [18]"})):
                agent.reset({"run_id": run_id, "task": "Read page"})
                self.assertEqual(agent.step(request(run_id)), action)
                agent.close()

            events = read_events(log)
            starts = [e for e in events if e["event"] == "model_call_start"]
            ends = [e for e in events if e["event"] == "model_call_end"]
            run_ends = [e for e in events if e["event"] == "run_end"]
            self.assertEqual(len(sdk.calls), 2)
            self.assertEqual([e["run_id"] for e in starts], ["first", "second"])
            self.assertEqual([e["step"] for e in starts], [0, 0])
            self.assertEqual([e["call_seq"] for e in starts], [1, 1])
            self.assertEqual([e["call_id"] for e in starts], [e["call_id"] for e in ends])
            self.assertEqual(
                [(e["run_id"], e["model_calls"], e["end_reason"]) for e in run_ends],
                [("first", 1, "close"), ("second", 1, "close")],
            )
            self.assertEqual(telemetry.summary()["run_id"], "first")

    def test_legacy_state_keeps_one_run_until_stop(self):
        for state in ({}, TaskState()):
            with self.subTest(state=type(state).__name__), \
                    tempfile.TemporaryDirectory() as temporary:
                log = Path(temporary) / "telemetry.jsonl"
                if isinstance(state, TaskState):
                    state.memory = "kept fact"
                else:
                    state["memory"] = "kept fact"
                sdk = FakeSdk([
                    reply("click [17]", "first fact", "request-1"),
                    reply("click [18]", None, "request-2"),
                    reply("stop [done]", None, "request-3"),
                ])
                expected = [
                    {"action": "click [17]"},
                    {"action": "click [18]"},
                    {"action": "stop [done]"},
                ]
                with patch.dict(os.environ, {"WEBAGENT_TELEMETRY_PATH": str(log)}), \
                        patch.object(agent_logic.model, "generate",
                                     side_effect=sdk.generate):
                    for action in expected:
                        self.assertEqual(
                            agent_logic.decide(
                                task="Read page",
                                observation=OBS,
                                history=[],
                                action_history=[],
                                state=state,
                            ),
                            action,
                        )

                data = state.data if isinstance(state, TaskState) else state
                events = read_events(log)
                starts = [e for e in events if e["event"] == "model_call_start"]
                ends = [e for e in events if e["event"] == "model_call_end"]
                run_ends = [e for e in events if e["event"] == "run_end"]
                run_id = data["_run_id"]

                self.assertEqual(len(sdk.calls), 3)
                self.assertEqual([e["run_id"] for e in starts], [run_id] * 3)
                self.assertEqual([e["step"] for e in starts], [0, 1, 2])
                self.assertEqual([e["call_seq"] for e in starts], [1, 2, 3])
                self.assertEqual([e["call_id"] for e in starts], [e["call_id"] for e in ends])
                self.assertEqual(len(run_ends), 1)
                self.assertEqual(run_ends[0]["run_id"], run_id)
                self.assertEqual(run_ends[0]["model_calls"], 3)
                self.assertEqual(run_ends[0]["end_reason"], "stop")
                self.assertEqual(data["memory"], "first fact")
                second_payload = json.loads(sdk.calls[1][1]["content"])
                self.assertEqual(second_payload["memory"], "first fact")
                with self.assertRaisesRegex(RuntimeError, "fresh state"):
                    agent_logic.decide(
                        task="Read page",
                        observation=OBS,
                        history=[],
                        action_history=[],
                        state=state,
                    )

    def test_fresh_legacy_state_starts_a_new_run_and_call_sequence(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"WEBAGENT_TELEMETRY_PATH": str(Path(temporary) / "telemetry.jsonl")}
        ):
            log = Path(temporary) / "telemetry.jsonl"
            first = {}
            second = {}
            sdk = FakeSdk([
                reply("click [17]"),
                reply("click [17]"),
                reply("click [18]"),
            ])
            with patch.object(agent_logic.model, "generate", side_effect=sdk.generate):
                for state in (first, second):
                    agent_logic.decide(
                        task="Read page",
                        observation=OBS,
                        history=[],
                        action_history=[],
                        state=state,
                    )
                agent_logic.decide(
                    task="Read page",
                    observation=OBS,
                    history=[],
                    action_history=[],
                    state=second,
                )

            starts = [e for e in read_events(log) if e["event"] == "model_call_start"]
            self.assertNotEqual(first["_run_id"], second["_run_id"])
            self.assertEqual([e["run_id"] for e in starts],
                             [first["_run_id"], second["_run_id"], second["_run_id"]])
            self.assertEqual([e["step"] for e in starts], [0, 0, 1])
            self.assertEqual([e["call_seq"] for e in starts], [1, 1, 2])

    def test_legacy_exception_writes_one_run_end_and_stops_the_state(self):
        class BrokenRuntime:
            def advance(self, frame, state):
                raise TimeoutError("deadline reached")

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"WEBAGENT_TELEMETRY_PATH": str(Path(temporary) / "telemetry.jsonl")}
        ), patch.object(agent_logic, "_default_runtime", return_value=BrokenRuntime()):
            log = Path(temporary) / "telemetry.jsonl"
            state = {}
            with self.assertRaisesRegex(TimeoutError, "deadline"):
                agent_logic.decide(
                    task="Read page",
                    observation=OBS,
                    history=[],
                    action_history=[],
                    state=state,
                )

            events = read_events(log)
            errors = [e for e in events if e["event"] == "step_error"]
            ends = [e for e in events if e["event"] == "run_end"]
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["error_type"], "TimeoutError")
            self.assertEqual(len(ends), 1)
            self.assertEqual(ends[0]["run_id"], state["_run_id"])
            self.assertEqual(ends[0]["end_reason"], "deadline")
            self.assertEqual(ends[0]["model_calls"], 0)
            self.assertTrue(state["_run_ended"])
            with self.assertRaisesRegex(RuntimeError, "fresh state"):
                agent_logic.decide(
                    task="Read page",
                    observation=OBS,
                    history=[],
                    action_history=[],
                    state=state,
                )

    def test_effgen_internal_retry_records_every_real_sdk_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="retry", path=log)
            sdk = FakeSdk([("", "empty-request"), reply("click [17]", request_id="good-request")])
            agent = MyAgent(
                model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                telemetry=telemetry,
            )
            agent.reset({"run_id": "retry", "task": "Retry once"})
            self.assertEqual(agent.step(request("retry")), {"action": "click [17]"})
            agent.close()

            events = read_events(log)
            starts = [e for e in events if e["event"] == "model_call_start"]
            ends = [e for e in events if e["event"] == "model_call_end"]
            run_end = [e for e in events if e["event"] == "run_end"][-1]
            self.assertEqual(len(sdk.calls), 2)
            self.assertEqual([e["purpose"] for e in starts], ["decision", "decision"])
            self.assertEqual([e["step"] for e in starts], [0, 0])
            self.assertEqual([e["call_seq"] for e in starts], [1, 2])
            self.assertEqual([e["call_id"] for e in starts], [e["call_id"] for e in ends])
            self.assertEqual([e["request_id"] for e in ends],
                             ["empty-request", "good-request"])
            self.assertEqual(run_end["model_calls"], 2)
            self.assertEqual(run_end["by_purpose"], {"decision": 2})


class ModelPortTests(unittest.TestCase):
    def test_only_role_and_string_content_reach_sdk(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="messages",
                                  path=Path(temporary) / "telemetry.jsonl")
            sdk = FakeSdk([reply("click [17]")])
            port = SdkModelPort(sdk=sdk, telemetry=telemetry)
            result = port.generate(
                [{"role": "system", "content": "s"},
                 {"role": "user", "content": "u"}],
                purpose="decision",
                deadline=time.time() + 10,
            )
            self.assertEqual(result.text, '{"action": "click [17]"}')
            self.assertEqual(len(sdk.calls), 1)
            events = read_events(telemetry.path)
            self.assertEqual([e["event"] for e in events],
                             ["model_call_start", "model_call_end"])
            self.assertEqual(events[1]["request_id"], "fake-request")
            with self.assertRaises(ValueError):
                port.generate(
                    [{"role": "user", "content": "u", "model": "other"}],
                    purpose="decision",
                    deadline=time.time() + 10,
                )
            self.assertEqual(len(sdk.calls), 1)

    def test_deadline_is_checked_before_the_sdk(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="late",
                                  path=Path(temporary) / "telemetry.jsonl")
            sdk = FakeSdk([reply("click [17]")])
            port = SdkModelPort(sdk=sdk, telemetry=telemetry)
            with self.assertRaises(TimeoutError):
                port.generate([{"role": "user", "content": "u"}],
                              purpose="decision", deadline=time.time() - 1)
            self.assertEqual(len(sdk.calls), 0)
            events = read_events(telemetry.path)
            self.assertEqual([e["event"] for e in events], ["model_call_rejected"])
            self.assertFalse(events[0]["sdk_invoked"])
            self.assertIsNone(events[0]["call_seq"])


if __name__ == "__main__":
    unittest.main()
