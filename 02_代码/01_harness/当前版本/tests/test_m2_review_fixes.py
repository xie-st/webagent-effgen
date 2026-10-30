"""Main-thread regressions for independently reviewed M2 boundaries."""
import unittest
import time
import json

from web_agent import recover, verify
from web_agent.adapters import official
from web_agent.state import TaskState


def frame(text):
    return official.frame_from_request({
        "run_id": "review-fix", "task": 'Change my bio to "New bio"',
        "step": 0, "execution_deadline": time.time() + 300,
        "observation": {"type": "accessibility_tree", "tab": 0,
                        "url": "https://example.test/profile", "text": text},
    }, step=0)


class QueryWriteGuardTests(unittest.TestCase):
    def test_mutating_query_cannot_bypass_unknown_write_guard(self):
        original = frame(text="[1] button 'Save'")
        state = TaskState({})
        verify.ensure_goals(original, state)
        recover.register_action(original, state, "click [1]")
        for target in (
            "https://example.test/?action=delete",
            "https://example.test/?operation=save",
            "https://example.test/?action=%64elete",
        ):
            with self.subTest(target=target), self.assertRaises(recover.WriteGuardError):
                recover.guard_action(original, state, "goto [" + target + "]")
        for target in (
            "https://example.test/search?q=delete",
            "https://example.test/submit/topic",
        ):
            self.assertTrue(recover.guard_action(
                original, state, "goto [" + target + "]"
            ).is_read)


class QuantityCoverageTests(unittest.TestCase):
    def test_non_vote_quantity_survives_and_one_object_cannot_complete_it(self):
        for task in ('Follow 3 users.', 'Reply to 3 comments with "x".'):
            with self.subTest(task=task):
                current = frame("[1] link 'Alice' url: https://example.test/user/alice")
                state = TaskState({})
                state.set_task(task)
                state.set_goal_checks(verify.extract_goal_checks(task))
                semantic = next(g for g in state.goal_checks if g.kind == "semantic")
                self.assertEqual(verify._semantic_object_count(semantic), 3)
                result = verify.parse_verification(json.dumps({"checks": [{
                    "goal_id": semantic.goal_id, "status": "confirmed",
                    "actual": "All 3 done", "source_task_quote": task,
                    "evidence": [{"line": 1, "quote": "Alice"}],
                }]}), current, state, mode="stop")
                self.assertFalse(result["all_confirmed"])


class BusinessRegionTests(unittest.TestCase):
    def test_exited_form_does_not_own_later_business_region(self):
        current = frame(
            "[1] RootWebArea 'site'\n"
            "\t[2] form ''\n\t\t[3] textbox 'Search'\n"
            "\t[4] main ''\n\t\t[5] article ''\n"
            "\t\t\t[6] StaticText 'Saved biography'\n"
            "\t\t\t[7] form ''\n\t\t\t\t[8] button 'Retract upvote'"
        )
        view = verify.parse_ax(current)
        self.assertFalse(view.by_id["6"].inside_form)
        self.assertTrue(view.by_id["8"].inside_form)

    def test_detail_page_does_not_identify_an_unrelated_vote(self):
        current = frame("[1] link 'Other post' url: https://example.test/post/other\n"
                        "[2] button 'Retract upvote'")
        view = verify.parse_ax(current)
        self.assertFalse(verify._same_stable_identity(
            view, "url:" + current.url, view.by_id["2"]
        ))


if __name__ == "__main__":
    unittest.main()
