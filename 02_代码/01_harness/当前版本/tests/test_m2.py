"""M2 core regressions: exact checks, pending effects, guard, recovery, stop."""
from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import agent_logic
from my_agent import MyAgent
from web_agent import recover, verify
from web_agent.adapters import official
from web_agent.contracts import Capabilities, GoalCheck, PendingAction
from web_agent.model_port import SdkModelPort
from web_agent.runtime import Runtime
from web_agent.screenshots import ScreenshotCapture
from web_agent.state import TaskState
from web_agent.telemetry import Telemetry

TASK = 'Change my bio to "New bio"'
URL = "http://127.0.0.1:9876/user/me/edit_biography"
PROFILE = "http://127.0.0.1:9876/user/me"
EDIT_TEXT = (
    "Tab 0 (current): edit\n"
    "[1] textbox 'Biography'\n"
    "\t[2] StaticText 'Old bio'\n"
    "[3] button 'Save'\n"
)
TYPED_TEXT = (
    "Tab 0 (current): edit\n"
    "[1] textbox 'Biography'\n"
    "\t[2] StaticText 'New bio'\n"
    "[3] button 'Save'\n"
)
SAVED_TEXT = (
    "Tab 0 (current): edit\n"
    "[4] alert 'The biography was updated.'\n"
    "\t[5] StaticText 'New bio'\n"
    "[1] textbox 'Biography'\n"
    "\t[2] StaticText 'New bio'\n"
    "[3] button 'Save'\n"
)
PROFILE_TEXT = (
    "Tab 0 (current): profile\n"
    "[9] StaticText 'New bio'\n"
    "[10] link 'Edit biography' url: " + URL + "\n"
)
QUERY_TEXT = "Tab 0 (current): profile\n[9] StaticText 'Something else'\n"


def frame(
    *,
    task=TASK,
    text=EDIT_TEXT,
    step=0,
    url=URL,
    deadline=None,
    run_id="m2",
    screenshot=None,
    history=(),
):
    observation = {"type": "accessibility_tree", "url": url, "text": text, "tab": 0}
    if screenshot is not None:
        observation["screenshot"] = screenshot
    request = {
        "run_id": run_id,
        "task": task,
        "observation": observation,
        "step": step,
        "observation_version": step,
        "execution_deadline": time.time() + 300 if deadline is None else deadline,
        "history": list(history),
    }
    return official.frame_from_request(request, step=step)


def request(
    *,
    task=TASK,
    text=EDIT_TEXT,
    url=URL,
    deadline=None,
    run_id="m2",
    step=None,
):
    del step
    return {
        "run_id": run_id,
        "task": task,
        "observation": {"type": "accessibility_tree", "url": url, "text": text},
        "execution_deadline": time.time() + 300 if deadline is None else deadline,
    }


def png_meta(step=0):
    return {
        "image_id": "a" * 32,
        "mime_type": "image/png",
        "width": 32,
        "height": 16,
        "byte_size": 24,
        "sha256": "b" * 64,
        "step": step,
    }


class FakePolicy:
    def __init__(self, decisions=(), corrections=(), verifications=()):
        self.decisions = list(decisions)
        self.corrections = list(corrections)
        self.verifications = list(verifications)
        self.verify_calls = []
        self.correct_calls = []
        self.telemetry = None

    def generate(self, context, state):
        return decision(self.decisions.pop(0))

    def correct(self, context, state, raw, error):
        self.correct_calls.append(str(error))
        return decision(self.corrections.pop(0))

    def verify(self, context, state, payload):
        self.verify_calls.append((context.deadline, payload))
        return self.verifications.pop(0)

    def close(self):
        pass


class FakeSdk:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        if not self.replies:
            raise AssertionError("unexpected extra fake SDK call")
        value = self.replies.pop(0)
        if isinstance(value, str):
            return SimpleNamespace(text=value, request_id="m2-fake")
        return SimpleNamespace(text=value[0], request_id=value[1])


def decision(action, memory=None):
    value = {"action": action}
    if memory is not None:
        value["memory"] = memory
    return json.dumps(value)


def verification_unknown(goal_id="goal-1", quote=TASK):
    return json.dumps(
        {
            "checks": [
                {
                    "goal_id": goal_id,
                    "status": "unknown",
                    "actual": None,
                    "source_task_quote": quote,
                    "evidence": [],
                    "reason": "not visible yet",
                }
            ]
        }
    )


class ExtractionTests(unittest.TestCase):
    def test_official_exact_replace_reply_and_append_are_full_coverage(self):
        replace = verify.extract_goal_checks('Change my reddit bio to "I am a robot"')
        self.assertEqual(len(replace), 1)
        self.assertEqual((replace[0].kind, replace[0].target), ("exact_equal", "I am a robot"))
        self.assertEqual(replace[0].source_quote, 'Change my reddit bio to "I am a robot"')

        reply = verify.extract_goal_checks(
            'Reply to the post with my comment "I am a big fan of the bookorg"'
        )
        self.assertEqual(reply[0].kind, "exact_equal")
        self.assertEqual(reply[0].target, "I am a big fan of the bookorg")

        append = verify.extract_goal_checks(
            'Edit my post on Nvidia RTX 4090 by adding a line to the body '
            'that says "EDIT: This news aged well"'
        )
        self.assertEqual(append[0].kind, "exact_append")
        self.assertEqual(append[0].target, "EDIT: This news aged well")
        self.assertEqual(append[0].field, "body")

    def test_upvote_and_composite_requirements_are_separate(self):
        vote = verify.extract_goal_checks("Upvote the newest post in books subreddit")
        self.assertEqual((vote[0].kind, vote[0].target), ("count_once", 1))
        self.assertTrue(
            any(
                goal.kind == "semantic"
                and "newest post in books subreddit" in str(goal.target)
                for goal in vote
            )
        )

        composite = verify.extract_goal_checks(
            "把个人简介改为 开发者-t，并发表标题为 并行调度-t 的帖子"
        )
        self.assertEqual(len(composite), 2)
        self.assertEqual(composite[0].target, "开发者-t")
        self.assertEqual(composite[1].target, "并行调度-t")

    def test_no_task_id_answer_or_path_is_consulted(self):
        first = verify.extract_goal_checks('Change my bio to "same"')
        second = verify.extract_goal_checks('Edit my profile bio to "same"')
        self.assertEqual(first[0].target, second[0].target)
        self.assertNotIn("399", first[0].goal_id)
        self.assertNotIn("/user/", first[0].source_quote)


class ExactVerificationTests(unittest.TestCase):
    def test_replacement_requires_exact_business_text_not_contains(self):
        goal = GoalCheck("goal-1", TASK, "exact_equal", "New bio", TASK, field="bio")
        contains = frame(text="[9] StaticText 'Old New bio extra'\n")
        result = verify.evaluate_goal(goal, verify.parse_ax(contains), TaskState())
        self.assertEqual(result["status"], "unknown")
        exact = frame(text="[9] StaticText 'New bio'\n")
        state = TaskState()
        state.set_task(TASK)
        result = verify.evaluate_goal(goal, verify.parse_ax(exact), state)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["evidence"][0].quote, "New bio")

    def test_append_preserves_original_and_rejects_extra_content(self):
        state = TaskState()
        state.set_task(
            'Edit my post by adding a line to the body that says "EDIT: aged well"'
        )
        goal = GoalCheck(
            "goal-1", state.task, "exact_append", "EDIT: aged well",
            state.task, field="body", baseline="Original body",
        )
        good = frame(
            task=state.task,
            text="[9] StaticText 'Original body'\n[10] StaticText 'EDIT: aged well'\n",
        )
        self.assertEqual(verify.evaluate_goal(goal, verify.parse_ax(good), state)["status"],
                         "verified")
        extra = frame(
            task=state.task,
            text="[9] StaticText 'Original body\\nEDIT: aged well\\nEXTRA'\n",
        )
        self.assertEqual(verify.evaluate_goal(goal, verify.parse_ax(extra), state)["status"],
                         "failed")
        duplicate = GoalCheck(
            "goal-2", state.task, "exact_append", "old",
            state.task, field="body", baseline="old body",
        )
        duplicate_frame = frame(task=state.task, text="[9] StaticText 'old body'\n")
        self.assertEqual(
            verify.evaluate_goal(duplicate, verify.parse_ax(duplicate_frame), state)["status"],
            "failed",
        )

    def test_draft_success_toast_and_screenshot_are_not_persistence(self):
        goal = GoalCheck("goal-1", TASK, "exact_equal", "New bio", TASK, field="bio")
        state = TaskState()
        state.set_task(TASK)
        result = verify.evaluate_goal(goal, verify.parse_ax(frame(text=SAVED_TEXT)), state)
        self.assertEqual(result["status"], "unknown")
        raw = json.dumps(
            {
                "checks": [
                    {
                        "goal_id": "goal-1",
                        "status": "confirmed",
                        "actual": "New bio",
                        "source_task_quote": TASK,
                        "evidence": [{"line": 2, "quote": "THE BIOGRAPHY"}],
                    }
                ]
            }
        )
        # Line 2 is an alert, not business state.
        parsed = verify.parse_verification(raw, frame(text=SAVED_TEXT), state, mode="pending")
        self.assertFalse(parsed["all_confirmed"])
        self.assertTrue(parsed["invalid"])

    def test_model_evidence_must_cite_current_ax_and_task_quote(self):
        state = TaskState()
        state.set_task(TASK)
        verify.ensure_goals(frame(), state)
        fake = json.dumps(
            {
                "checks": [
                    {
                        "goal_id": "goal-1",
                        "status": "confirmed",
                        "actual": "New bio",
                        "source_task_quote": TASK,
                        "evidence": [{"line": 999, "quote": "New bio"}],
                    }
                ]
            }
        )
        parsed = verify.parse_verification(fake, frame(text=PROFILE_TEXT), state, mode="stop")
        self.assertFalse(parsed["all_confirmed"])
        self.assertIn("non-current AX quote", " ".join(parsed["invalid"]))

        missing_task = json.dumps(
            {
                "checks": [
                    {
                        "goal_id": "goal-1",
                        "status": "confirmed",
                        "actual": "New bio",
                        "source_task_quote": "invented requirement",
                        "evidence": [{"line": 2, "quote": "New bio"}],
                    }
                ]
            }
        )
        parsed = verify.parse_verification(
            missing_task, frame(text=PROFILE_TEXT), state, mode="stop"
        )
        self.assertFalse(parsed["all_confirmed"])
        self.assertIn("original-task coverage", " ".join(parsed["invalid"]))


class RuntimeFlowTests(unittest.TestCase):
    def test_final_write_is_confirmed_by_read_only_readback_then_stop(self):
        runtime = Runtime(
            lambda context, state: {"action": state.data.pop("_next")}
        )
        state = {}
        state["_next"] = "type [1] [New bio] [0]"
        runtime.advance(frame(step=0), state)
        self.assertEqual(state["_goal_checks"][0].status, "pending")
        self.assertNotIn("_pending_actions", state)

        state["_next"] = "click [3]"
        runtime.advance(frame(step=1, text=TYPED_TEXT), state)
        pending = state["_pending_actions"]["0"]
        self.assertEqual(pending.goal_ids, ("goal-1",))
        self.assertEqual(pending.status, "unknown")

        state["_next"] = "goto [" + PROFILE + "]"
        runtime.advance(frame(step=2, text=SAVED_TEXT), state)
        self.assertIn("_pending_actions", state)
        self.assertEqual(state["_pending_actions"]["0"].status, "unknown")

        state["_next"] = "stop [done]"
        result = runtime.advance(frame(step=3, text=PROFILE_TEXT, url=PROFILE), state)
        self.assertEqual(result["action"], "stop [done]")
        self.assertEqual(state.get("_pending_actions", {}), {})
        self.assertEqual(state["_goal_checks"][0].status, "verified")

    def test_no_effect_does_not_advance_and_allows_local_retry(self):
        runtime = Runtime(lambda context, state: {"action": state.data["_next"]})
        state = {"_next": "click [3]"}
        runtime.advance(frame(step=0), state)
        state["_next"] = "click [3]"
        runtime.advance(frame(step=1), state)
        goal = state["_goal_checks"][0]
        self.assertEqual(goal.status, "failed")
        self.assertNotEqual(goal.status, "verified")
        self.assertEqual(state["_pending_actions"]["0"].step, 1)

    def test_stop_with_missing_goal_is_corrected_not_accepted(self):
        policy = FakePolicy(
            decisions=["stop [done]"],
            corrections=["goto [" + URL + "]"],
            verifications=[verification_unknown()],
        )
        runtime = Runtime(policy=policy)
        state = {}
        result = runtime.advance(frame(step=0), state)
        self.assertEqual(result["action"], "goto [" + URL + "]")
        self.assertEqual(len(policy.correct_calls), 1)
        self.assertIn("unverified", policy.correct_calls[0])

    def test_unknown_write_blocks_second_submit_with_another_element_id(self):
        policy = FakePolicy(
            decisions=["click [3]", "click [4]"],
            corrections=["goto [" + PROFILE + "]"],
            verifications=[verification_unknown()],
        )
        runtime = Runtime(policy=policy)
        state = {}
        runtime.advance(frame(step=0), state)
        pending_id = state["_pending_actions"]["0"].pending_id
        text = (
            "[3] button 'Save'\n"
            "[4] button 'Save'\n"
            "[9] StaticText 'Nothing changed'\n"
        )
        result = runtime.advance(frame(step=1, text=text), state)
        self.assertEqual(result["action"], "goto [" + PROFILE + "]")
        self.assertIn("different element id", policy.correct_calls[0])
        self.assertEqual(state["_pending_actions"]["0"].pending_id, pending_id)

    def test_query_confirmation_does_not_rewrite_and_clears_pending(self):
        runtime = Runtime(lambda context, state: {"action": state.data["_next"]})
        state = {"_next": "click [3]"}
        runtime.advance(frame(step=0), state)
        state["_next"] = "goto [" + PROFILE + "]"
        runtime.advance(frame(step=1, text="[9] StaticText 'New bio'\n"), state)
        self.assertEqual(state.get("_pending_actions", {}), {})
        self.assertEqual(state["_goal_checks"][0].status, "verified")
        state["_next"] = "stop [done]"
        self.assertEqual(
            runtime.advance(frame(step=2, text=PROFILE_TEXT, url=PROFILE), state),
            {"action": "stop [done]"},
        )

    def test_query_without_evidence_keeps_pending(self):
        actions = ["click [3]", "goto [" + PROFILE + "]"]
        runtime = Runtime(lambda context, state: {"action": actions.pop(0)})
        state = {}
        runtime.advance(frame(step=0), state)
        pending = state["_pending_actions"]["0"]
        runtime.advance(frame(step=1, text=QUERY_TEXT, url=PROFILE), state)
        self.assertEqual(state["_pending_actions"]["0"].pending_id, pending.pending_id)
        self.assertEqual(state["_pending_actions"]["0"].status, "unknown")

    def test_verified_value_cannot_be_rewritten(self):
        state = TaskState()
        state.set_task(TASK)
        verify.ensure_goals(frame(), state)
        state.goal_checks[0].status = "verified"
        with self.assertRaises(recover.DuplicateWriteError):
            recover.guard_action(frame(), state, "click [3]")

    def test_verified_prefix_survives_local_failure_of_second_goal(self):
        task = (
            'Change my bio to "New bio", and reply with my comment "Thanks"'
        )
        goals = verify.extract_goal_checks(task)
        state = TaskState()
        state.set_task(task)
        state.set_goal_checks(goals)
        goals[0].status = "verified"
        goals[0].evidence.append(
            verify.GoalEvidence("ax_exact", 0, URL, 0, line=1, quote="New bio",
                                actual="New bio", identity="http://127.0.0.1:9876/user/me",
                                deterministic=True)
        )
        goals[1].status = "failed"
        info = recover.ActionInfo("click [3]", "click", "3", "button", "Save", None,
                                  is_write=True, is_read=False, operation="commit")
        selected = recover._select_goals(frame(task=task, text=TYPED_TEXT), state, info)
        self.assertEqual([goal.goal_id for goal in selected], ["goal-2"])
        self.assertEqual(goals[0].status, "verified")
        self.assertEqual(len(goals[0].evidence), 1)

    def test_identity_change_marks_verified_evidence_stale(self):
        state = TaskState()
        state.set_task(TASK)
        verify.ensure_goals(frame(), state)
        state.observe_identity(frame())
        state.goal_checks[0].status = "verified"
        state.goal_checks[0].evidence.append(
            verify.GoalEvidence("ax_exact", 0, URL, 0, line=1, quote="New bio",
                                actual="New bio", identity="http://127.0.0.1:9876/user/me",
                                deterministic=True)
        )
        frame_b = frame(text=PROFILE_TEXT, url="http://127.0.0.1:9876/user/other")
        state.observe_identity(frame_b)
        self.assertEqual(state.goal_checks[0].status, "stale")

    def test_click_enter_and_link_are_classified_conservatively(self):
        text = (
            "[1] textbox 'Search'\n"
            "[2] button 'Save'\n"
            "[3] link 'Profile' url: " + PROFILE + "\n"
        )
        current = frame(text=text)
        self.assertTrue(recover.classify_action("press [Enter]", current).is_write)
        self.assertTrue(recover.classify_action("click [2]", current).is_write)
        self.assertFalse(recover.classify_action("click [3]", current).is_write)
        self.assertTrue(recover.classify_action("click [1]", current).is_draft)
        self.assertFalse(recover.classify_action("press [Tab]", current).is_write)

    def test_screenshot_is_requested_once_on_unknown_and_404_is_not_success(self):
        class FakePort:
            def __init__(self):
                self.calls = []

            def capture(self, target, *, reason="diagnostic", directory=None):
                self.calls.append((target.step, reason))
                return ScreenshotCapture(
                    result="http_404",
                    reference=target.screenshot,
                    requested=True,
                    http_status=404,
                )

        port = FakePort()
        policy = FakePolicy(
            decisions=["click [3]", "goto [" + PROFILE + "]"],
            verifications=[verification_unknown()],
        )
        runtime = Runtime(policy=policy, screenshot_port=port)
        state = {}
        runtime.advance(frame(step=0, screenshot=png_meta(0)), state)
        runtime.advance(
            frame(step=1, text=SAVED_TEXT, screenshot=png_meta(1)), state
        )
        self.assertEqual(port.calls, [(1, "verify")])
        self.assertEqual(state["_pending_actions"]["0"].status, "unknown")
        self.assertEqual(
            state.get("_screenshot_reference"), None
        )


class DeadlineAndLifecycleTests(unittest.TestCase):
    def test_extra_verification_uses_the_same_absolute_deadline(self):
        deadline = time.time() + 42
        policy = FakePolicy(
            decisions=["click [3]", "goto [" + PROFILE + "]"],
            verifications=[verification_unknown()],
        )
        runtime = Runtime(policy=policy)
        state = {}
        runtime.advance(frame(step=0, deadline=deadline), state)
        runtime.advance(frame(step=1, text=SAVED_TEXT, deadline=deadline + 100), state)
        self.assertEqual(len(policy.verify_calls), 1)
        self.assertEqual(policy.verify_calls[0][0], deadline)

        legacy = {"_remaining_seconds": 10}
        first = agent_logic._execution_deadline(legacy)
        legacy["_remaining_seconds"] = 30
        self.assertEqual(agent_logic._execution_deadline(legacy), first)

    def test_reset_and_close_clear_goal_and_pending_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="m2", path=log)
            sdk = FakeSdk([decision("type [1] [New bio] [0]"), decision("click [3]")])
            agent = MyAgent(
                model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                telemetry=telemetry,
            )
            agent.reset({"run_id": "m2", "task": TASK, "execution_deadline": time.time() + 300})
            agent.step(request(step=0))
            self.assertEqual(len(agent.state["_goal_checks"]), 1)
            agent.step(request(step=1, text=TYPED_TEXT))
            self.assertIn("_pending_actions", agent.state)
            agent.reset({"run_id": "m2b", "task": TASK, "execution_deadline": time.time() + 300})
            self.assertEqual(agent.state, {})
            agent.close()
            with self.assertRaisesRegex(ValueError, "reset"):
                agent.step(request(step=0, run_id="m2b"))


class ProductionWiringTests(unittest.TestCase):
    def test_my_agent_runs_m2_with_decision_verify_purposes_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            telemetry = Telemetry(run_id="prod", path=log)
            sdk = FakeSdk(
                [
                    decision("type [1] [New bio] [0]"),
                    decision("click [3]"),
                    verification_unknown(),
                    decision("goto [" + PROFILE + "]"),
                    decision("stop [done]"),
                ]
            )
            agent = MyAgent(
                model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                telemetry=telemetry,
            )
            agent.reset(
                {"run_id": "m2", "task": TASK, "execution_deadline": time.time() + 300}
            )
            agent.step(request(step=0))
            agent.step(request(step=1, text=TYPED_TEXT))
            agent.step(request(step=2, text=SAVED_TEXT))
            result = agent.step(request(step=3, text=PROFILE_TEXT, url=PROFILE))
            self.assertEqual(result, {"action": "stop [done]"})
            agent.close()

            events = [
                json.loads(line)
                for line in log.read_text(encoding="utf-8").splitlines()
            ]
            starts = [event for event in events if event["event"] == "model_call_start"]
            self.assertEqual(
                [event["purpose"] for event in starts],
                ["decision", "decision", "verify", "decision", "decision"],
            )
            for call in sdk.calls:
                content = "\n".join(message["content"] for message in call)
                self.assertNotIn("sha256", content)
                self.assertNotIn("base64", content)
                self.assertNotIn("screenshot", content)
            self.assertIn("goal_plan", [event["event"] for event in events])
            self.assertIn("verification", [event["event"] for event in events])
            self.assertIn("pending_action", [event["event"] for event in events])
            verification = [event for event in events if event["event"] == "verification"][-1]
            self.assertIsNone(verification["total_tokens"])
            self.assertIsNone(verification["cost_usd"])

    def test_legacy_decide_actually_uses_goals_and_stop_judge(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "telemetry.jsonl"
            state = {"_remaining_seconds": 60}
            sdk = FakeSdk([decision("stop [done]")])
            with patch.dict(
                "os.environ", {"WEBAGENT_TELEMETRY_PATH": str(log)}
            ), patch.object(
                agent_logic.model, "generate", side_effect=sdk.generate
            ):
                result = agent_logic.decide(
                    task=TASK,
                    observation={
                        "type": "accessibility_tree",
                        "url": PROFILE,
                        "text": PROFILE_TEXT,
                    },
                    history=[],
                    action_history=[],
                    state=state,
                )
            self.assertEqual(result, {"action": "stop [done]"})
            self.assertEqual(state["_goal_checks"][0].status, "verified")
            self.assertTrue(state["_run_ended"])


class ExpandedSuiteCoverageTests(unittest.TestCase):
    """New-suite requirements: fail closed, semantic scope, per-object effects."""

    def test_non_empty_task_can_never_stop_with_an_empty_checklist(self):
        task = "Make the dashboard nicer somehow."
        goals = verify.extract_goal_checks(task)
        self.assertEqual([goal.kind for goal in goals], ["semantic"])
        state = TaskState()
        state.set_task(task)
        self.assertFalse(verify.judge_goals(task, state)[0])
        with self.assertRaises(verify.GoalIncompleteError):
            verify.assert_stop(frame(task=task, text="[1] StaticText 'Done'\n"), state)
        self.assertTrue(state.goal_checks)

    def test_subreddit_topic_is_a_constraint_not_an_exact_field_value(self):
        task = (
            "Find a subreddit focused on topics related to gaming consoles, and "
            'post my question, "what is the recommended console to buy these days" '
            "there"
        )
        goals = verify.extract_goal_checks(task)
        exact = [goal for goal in goals if goal.kind == "exact_equal"]
        self.assertEqual(len(exact), 1)
        self.assertEqual(
            exact[0].target, "what is the recommended console to buy these days"
        )
        self.assertFalse(any(goal.target == "gaming consoles" for goal in goals))
        self.assertTrue(
            any(
                goal.kind == "semantic" and "gaming consoles" in str(goal.target)
                for goal in goals
            )
        )

    def test_quantity_and_capacity_requirement_blocks_stop_without_evidence(self):
        task = (
            "Show the least expensive shoe storage with a minimum storage "
            "capacity of 12 pairs."
        )
        goals = verify.extract_goal_checks(task)
        self.assertTrue(goals)
        self.assertTrue(
            any(
                goal.kind == "semantic" and "12 pairs" in str(goal.target)
                for goal in goals
            )
        )
        state = TaskState()
        state.set_task(task)
        verify.ensure_goals(frame(task=task, text="[1] StaticText 'Shoe rack'\n"), state)
        self.assertFalse(verify.judge_goals(task, state)[0])
        with self.assertRaises(verify.GoalIncompleteError):
            verify.assert_stop(
                frame(task=task, text="[1] StaticText 'Shoe rack'\n"), state
            )

    def test_cancelled_order_reorder_keeps_history_date_and_status(self):
        task = (
            "I previously ordered some a mattress foundation around Feb or March "
            "2023 and later cancelled. Can you reorder it for me?"
        )
        goals = verify.extract_goal_checks(task)
        kinds = [goal.kind for goal in goals]
        self.assertIn("order_once", kinds)
        semantic = " ".join(
            str(goal.target) for goal in goals if goal.kind == "semantic"
        ).casefold()
        self.assertIn("mattress foundation", semantic)
        self.assertIn("2023", semantic)
        self.assertIn("cancel", semantic)

    def _vote_page(self, title, *, voted):
        button = "Retract downvote" if voted else "Downvote"
        return (
            f"Tab 0 (current): post\n[1] heading '{title}'\n"
            f"[2] button '{button}'\n[3] StaticText '0 points'\n"
        )

    def test_four_distinct_downvotes_confirm_one_by_one_and_guard_retract(self):
        task = "Thumbs down the top 4 post ever in movies."
        goals = verify.extract_goal_checks(task)
        self.assertEqual((goals[0].kind, goals[0].target), ("count_per_object", 4))
        runtime = Runtime(lambda context, state: {"action": state.data.pop("_next")})
        state = {}
        for index in range(4):
            url = f"http://127.0.0.1:9876/f/movies/comments/{index}"
            title = f"Top movie post {index}"
            state["_next"] = "click [2]"
            result = runtime.advance(
                frame(task=task, url=url, text=self._vote_page(title, voted=False),
                      step=index * 2),
                state,
            )
            self.assertEqual(result["action"], "click [2]")
            self.assertIn("_pending_actions", state)
            state["_next"] = "scroll [down]"
            runtime.advance(
                frame(task=task, url=url, text=self._vote_page(title, voted=True),
                      step=index * 2 + 1),
                state,
            )
            count_goal = state["_goal_checks"][0]
            self.assertEqual(state.get("_pending_actions", {}), {})
            self.assertEqual(len(count_goal.objects), index + 1)
            self.assertEqual(count_goal.actual, index + 1)
            if index < 3:
                self.assertNotEqual(count_goal.status, "verified")
        self.assertEqual(state["_goal_checks"][0].status, "verified")
        self.assertEqual(state["_goal_checks"][1].status, "pending")
        with self.assertRaises(recover.DuplicateWriteError):
            recover.guard_action(
                frame(task=task, url="http://127.0.0.1:9876/f/movies/comments/0",
                      text=self._vote_page("Top movie post 0", voted=True)),
                TaskState(state),
                "click [2]",
            )
        # The aggregate is verified but the ranking/topic requirement is not.
        with self.assertRaises(verify.GoalIncompleteError):
            verify.assert_stop(
                frame(task=task, url="http://127.0.0.1:9876/f/movies",
                      text="[1] heading 'movies'\n", step=9),
                TaskState(state),
            )

    def test_partial_cart_write_clears_pending_and_allows_checkout(self):
        task = "Add the mattress foundation to the cart and checkout"
        goals = verify.extract_goal_checks(task)
        self.assertEqual([goal.kind for goal in goals], ["item_exact", "order_once"])
        runtime = Runtime(lambda context, state: {"action": state.data.pop("_next")})
        state = {}
        state["_next"] = "click [1]"
        runtime.advance(
            frame(task=task, url="http://127.0.0.1:9876/shop/product/7",
                  text="[1] button 'Add to cart'\n[2] StaticText 'mattress foundation'\n",
                  step=0),
            state,
        )
        self.assertIn("_pending_actions", state)
        state["_next"] = "scroll [down]"
        runtime.advance(
            frame(task=task, url="http://127.0.0.1:9876/shop/cart",
                  text="[5] StaticText 'the mattress foundation'\n[9] button 'Checkout'\n",
                  step=1),
            state,
        )
        self.assertEqual(state.get("_pending_actions", {}), {})
        self.assertEqual(state["_goal_checks"][0].status, "verified")
        self.assertEqual(state["_goal_checks"][1].status, "pending")
        with self.assertRaises(verify.GoalIncompleteError):
            verify.assert_stop(
                frame(task=task, url="http://127.0.0.1:9876/shop/cart",
                      text="[5] StaticText 'the mattress foundation'\n"),
                TaskState(state),
            )
        state["_next"] = "click [9]"
        result = runtime.advance(
            frame(task=task, url="http://127.0.0.1:9876/shop/cart",
                  text="[5] StaticText 'the mattress foundation'\n[9] button 'Checkout'\n",
                  step=2),
            state,
        )
        self.assertEqual(result["action"], "click [9]")
        self.assertEqual(state["_pending_actions"]["0"].goal_ids, ("goal-2",))

    def test_unknown_semantics_on_dangerous_link_or_button_is_blocked(self):
        text = (
            "[1] link 'Continue' url: http://127.0.0.1:9876/delete/post/1\n"
            "[2] button 'Preview and submit'\n"
            "[3] link 'Preview' url: http://127.0.0.1:9876/f/books\n"
            "[4] button 'Review order'\n"
            "[5] button 'Cancel'\n"
        )
        current = frame(text=text)
        self.assertTrue(recover.classify_action("click [1]", current).is_write)
        self.assertTrue(recover.classify_action("click [2]", current).is_write)
        self.assertFalse(recover.classify_action("click [3]", current).is_write)
        self.assertTrue(recover.classify_action("click [4]", current).is_write)
        self.assertFalse(recover.classify_action("click [5]", current).is_write)
        state = TaskState()
        state.set_task("Upvote the newest post in books subreddit")
        state.set_pending(
            PendingAction(
                pending_id="pending", tab=0, step=0, action="click [9]",
                operation="commit", goal_ids=(), source={}, expected={},
                status="unknown",
            )
        )
        with self.assertRaises(recover.WriteGuardError):
            recover.guard_action(current, state, "click [1]")
        with self.assertRaises(recover.WriteGuardError):
            recover.guard_action(current, state, "click [2]")

    def test_verified_upvote_is_not_retracted_by_a_second_click(self):
        task = "Upvote the newest post in books subreddit"
        state = TaskState()
        state.set_task(task)
        state.set_goal_checks(verify.extract_goal_checks(task))
        goal = state.goal_checks[0]
        goal.status = "verified"
        goal.evidence.append(
            verify.GoalEvidence(
                "ax_vote_state", 0, URL, 0, line=2, quote="Retract upvote",
                actual="Retract upvote", deterministic=True,
            )
        )
        after = frame(
            task=task,
            text="[1] heading 'Post'\n[2] button 'Retract upvote'\n",
        )
        with self.assertRaises(recover.DuplicateWriteError):
            recover.guard_action(after, state, "click [2]")


    def test_another_posts_retract_state_cannot_confirm_a_new_vote(self):
        task = "Thumbs down the top 4 post ever in movies."
        runtime = Runtime(lambda context, state: {"action": state.data.pop("_next")})
        state = {}
        listing_before = (
            "[1] heading 'Post A'\n[2] button 'Downvote'\n"
            "[3] heading 'Post B'\n[4] button 'Downvote'\n"
        )
        listing_after = (
            "[1] heading 'Post A'\n[2] button 'Retract downvote'\n"
            "[3] heading 'Post B'\n[4] button 'Downvote'\n"
        )
        state["_next"] = "click [2]"
        runtime.advance(
            frame(task=task, url="http://127.0.0.1:9876/f/movies",
                  text=listing_before, step=0),
            state,
        )
        state["_next"] = "scroll [down]"
        runtime.advance(
            frame(task=task, url="http://127.0.0.1:9876/f/movies",
                  text=listing_after, step=1),
            state,
        )
        self.assertEqual(len(state["_goal_checks"][0].objects), 1)
        state["_next"] = "click [4]"
        runtime.advance(
            frame(task=task, url="http://127.0.0.1:9876/f/movies",
                  text=listing_after, step=2),
            state,
        )
        state["_next"] = "scroll [down]"
        runtime.advance(
            frame(task=task, url="http://127.0.0.1:9876/f/movies",
                  text=listing_after, step=3),
            state,
        )
        self.assertEqual(len(state["_goal_checks"][0].objects), 1)

if __name__ == "__main__":
    unittest.main()
