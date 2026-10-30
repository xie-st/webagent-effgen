"""M2 takeover regressions; exercise real runtime without an EffGen dependency."""
import json
import time
import unittest

from web_agent import recover, verify
from web_agent.adapters import official
from web_agent.runtime import Runtime
from web_agent.state import TaskState


def frame(text="[1] button 'Save'"):
    return official.frame_from_request({
        "run_id": "takeover", "task": 'Change my bio to "New bio"',
        "step": 0, "execution_deadline": time.time() + 300,
        "observation": {"type": "accessibility_tree", "tab": 0,
                        "url": "https://example.test/profile", "text": text},
    }, step=0)


def unknown_state(current):
    state = TaskState({})
    verify.ensure_goals(current, state)
    recover.register_action(current, state, "click [1]")
    return state


class MutationClassificationTests(unittest.TestCase):
    def test_query_mutations_are_blocked_while_effect_is_unknown(self):
        current = frame()
        state = unknown_state(current)
        for operation in ("cancel", "checkout", "vote", "like", "purchase",
                          "addcart", "add_to_cart", "delete", "submit"):
            for key in ("action", "do", "op", "operation", "cmd"):
                with self.subTest(operation=operation, key=key):
                    with self.assertRaises(recover.WriteGuardError):
                        recover.guard_action(current, state,
                            f"goto [https://example.test/?{key}={operation}]")

    def test_popup_metadata_cannot_override_a_dangerous_link(self):
        current = frame("[1] button 'Save'\n"
                        "[2] link 'More' hasPopup: menu url: https://example.test/delete/1")
        with self.assertRaises(recover.WriteGuardError):
            recover.guard_action(current, unknown_state(current), "click [2]")

    def test_popup_metadata_cannot_override_a_commit_button(self):
        current = frame("[1] button 'Save'\n[2] button 'Delete' hasPopup: menu")
        with self.assertRaises(recover.WriteGuardError):
            recover.guard_action(current, unknown_state(current), "click [2]")

    def test_normal_menus_and_queries_stay_read_only(self):
        current = frame("[1] button 'Save'\n"
                        "[2] button 'Account' hasPopup: menu expanded: False\n"
                        "[3] tab 'Orders'")
        state = unknown_state(current)
        for action in ("click [2]", "click [3]",
                       "goto [https://example.test/search?q=delete]",
                       "goto [https://example.test/?action=view]"):
            with self.subTest(action=action):
                self.assertTrue(recover.guard_action(current, state, action).is_read)


class CorrectionBudgetTests(unittest.TestCase):
    def test_different_invalid_answers_cannot_consume_unbounded_calls(self):
        class Policy:
            corrections = 0

            def generate(self, context, state):
                return json.dumps({"action": "click [90]"})

            def correct(self, context, state, raw, exc):
                self.corrections += 1
                if self.corrections > 5:
                    raise AssertionError("unbounded corrections")
                return json.dumps({"action": f"click [{90 + self.corrections}]"})

        policy = Policy()
        state = TaskState({})
        result = Runtime(policy=policy).advance(frame(), state)
        self.assertEqual(policy.corrections, 2)
        self.assertEqual(result, {"action": "scroll [down]"})
        self.assertEqual(state.recovery_count, 1)
        self.assertIsNone(state.pending_for(0))

    def test_valid_first_correction_is_accepted(self):
        class Policy:
            corrections = 0

            def generate(self, context, state):
                return "invalid JSON"

            def correct(self, context, state, raw, exc):
                self.corrections += 1
                return json.dumps({"action": "scroll [up]"})

        policy = Policy()
        result = Runtime(policy=policy).advance(frame(), TaskState({}))
        self.assertEqual(result, {"action": "scroll [up]"})
        self.assertEqual(policy.corrections, 1)


if __name__ == "__main__":
    unittest.main()
