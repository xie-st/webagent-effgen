"""M2 vote evidence: persistent toggle controls, stable objects, scope proof."""
from __future__ import annotations

import json
import time
import unittest

from web_agent import verify
from web_agent.adapters import official
from web_agent.contracts import PendingAction
from web_agent.runtime import Runtime
from web_agent.state import TaskState

VOTE_TASK = "Upvote the newest post in books subreddit"
BOOKS_URL = "http://127.0.0.1:9876/f/books/new"
TITLE = "Adults reading to each other out loud?"
OTHER_TITLE = "Another post"

# The vote form only wraps the button; the post title is ordinary business text.
LISTING_BEFORE = (
    "[1] heading 'Books'\n"
    f"[2] heading '{TITLE}'\n"
    "[3] textbox 'Search posts'\n"
    "\t[4] button 'Upvote'\n"
    f"[5] heading '{OTHER_TITLE}'\n"
    "[6] button 'Upvote'\n"
)
LISTING_AFTER = (
    "[1] heading 'Books'\n"
    f"[2] heading '{TITLE}'\n"
    "[3] textbox 'Search posts'\n"
    "\t[4] button 'Retract upvote'\n"
    f"[5] heading '{OTHER_TITLE}'\n"
    "[6] button 'Upvote'\n"
)
HISTORY = [
    {
        "observation": {
            "url": BOOKS_URL,
            "text": (
                "[1] heading 'New'\n"
                f"[2] heading '{TITLE}'\n"
                f"[3] heading '{OTHER_TITLE}'\n"
            ),
        },
        "action": "goto [" + BOOKS_URL + "]",
    }
]


def frame(
    *,
    task=VOTE_TASK,
    text=LISTING_AFTER,
    step=1,
    url=BOOKS_URL,
    history=(),
    deadline=None,
):
    observation = {
        "type": "accessibility_tree",
        "url": url,
        "text": text,
        "tab": 0,
    }
    request = {
        "run_id": "m2-vote",
        "task": task,
        "observation": observation,
        "step": step,
        "observation_version": step,
        "execution_deadline": time.time() + 300 if deadline is None else deadline,
        "history": list(history),
    }
    return official.frame_from_request(request, step=step)


def state_for(task=VOTE_TASK, current=None):
    state = TaskState()
    state.set_task(task)
    verify.ensure_goals(current or frame(), state)
    return state


def pending(
    goal_ids,
    *,
    object_key,
    element_name="Upvote",
    element_id="4",
    step=0,
    url=BOOKS_URL,
):
    return PendingAction(
        pending_id="pending-vote",
        tab=0,
        step=step,
        action=f"click [{element_id}]",
        operation="commit",
        goal_ids=tuple(goal_ids),
        source={
            "url": url,
            "element_id": element_id,
            "element_name": element_name,
            "object_key": object_key,
        },
        expected={},
        status="unknown",
    )


def verify_json(checks):
    return json.dumps({"checks": checks})


class PersistentVoteEvidenceTests(unittest.TestCase):
    def test_form_wrapped_retract_control_confirms_vote_and_newest_semantic(self):
        current = frame(history=HISTORY)
        state = state_for(current=current)
        count, scope = state.goal_checks[0], state.goal_checks[1]
        self.assertEqual((count.kind, scope.kind), ("count_once", "semantic"))

        # The deterministic effect already recorded this stable object.
        count.objects.append("name:" + TITLE)
        count.status = "verified"
        payload = verify.build_verify_payload(current, state, mode="stop")
        history_id = payload["history_evidence"][0]["source_id"]
        parsed = verify.parse_verification(
            verify_json(
                [
                    {
                        "goal_id": count.goal_id,
                        "status": "confirmed",
                        "actual": 1,
                        "source_task_quote": VOTE_TASK,
                        "evidence": [{"line": 4, "quote": "Retract upvote"}],
                    },
                    {
                        "goal_id": scope.goal_id,
                        "status": "confirmed",
                        "actual": (
                            "newest post '" + TITLE + "' is upvoted; "
                            "it is first in the supplied new listing"
                        ),
                        "source_task_quote": VOTE_TASK,
                        "evidence": [
                            {"line": 2, "quote": TITLE},
                            {"line": 4, "quote": "Retract upvote"},
                            {"history_id": history_id, "quote": TITLE},
                        ],
                    },
                ]
            ),
            current,
            state,
            mode="stop",
        )
        self.assertTrue(parsed["all_confirmed"], parsed["invalid"])
        self.assertEqual(
            [check["status"] for check in parsed["checks"]],
            ["confirmed", "confirmed"],
        )

    def test_vote_toggle_alone_cannot_prove_newest_or_an_unrelated_object(self):
        current = frame(history=HISTORY)
        state = state_for(current=current)
        count, scope = state.goal_checks
        count.objects.append("name:" + TITLE)
        count.status = "verified"
        payload = verify.build_verify_payload(current, state, mode="stop")
        history_id = payload["history_evidence"][0]["source_id"]

        vote_only = verify.parse_verification(
            verify_json(
                [
                    {
                        "goal_id": scope.goal_id,
                        "status": "confirmed",
                        "actual": "vote landed",
                        "source_task_quote": VOTE_TASK,
                        "evidence": [
                            {"line": 4, "quote": "Retract upvote"},
                            {"history_id": history_id, "quote": TITLE},
                        ],
                    }
                ]
            ),
            current,
            state,
            mode="stop",
        )
        self.assertFalse(vote_only["all_confirmed"])
        self.assertIn("business evidence", " ".join(vote_only["invalid"]))

        untouched_vote = verify.parse_verification(
            verify_json(
                [
                    {
                        "goal_id": scope.goal_id,
                        "status": "confirmed",
                        "actual": "vote control visible",
                        "source_task_quote": VOTE_TASK,
                        "evidence": [
                            {"line": 6, "quote": "Upvote"},
                            {"history_id": history_id, "quote": TITLE},
                        ],
                    }
                ]
            ),
            current,
            state,
            mode="stop",
        )
        self.assertFalse(untouched_vote["all_confirmed"])
        self.assertIn("business evidence", " ".join(untouched_vote["invalid"]))

        wrong_object = verify.parse_verification(
            verify_json(
                [
                    {
                        "goal_id": scope.goal_id,
                        "status": "confirmed",
                        "actual": "newest post is upvoted",
                        "source_task_quote": VOTE_TASK,
                        "evidence": [
                            {"line": 5, "quote": OTHER_TITLE},
                            {"line": 4, "quote": "Retract upvote"},
                            {"history_id": history_id, "quote": TITLE},
                        ],
                    }
                ]
            ),
            current,
            state,
            mode="stop",
        )
        self.assertFalse(wrong_object["all_confirmed"])
        self.assertIn("acted object", " ".join(wrong_object["invalid"]))

    def test_draft_textbox_and_success_alert_are_still_rejected(self):
        bio_task = 'Change my bio to "New bio"'
        bio_state = state_for(
            bio_task,
            frame(
                task=bio_task,
                url="http://127.0.0.1:9876/user/me/edit_biography",
                text="[1] textbox 'Biography'\n\t[2] StaticText 'New bio'\n",
            ),
        )
        bio_current = frame(
            task=bio_task,
            url="http://127.0.0.1:9876/user/me/edit_biography",
            text="[1] textbox 'Biography'\n\t[2] StaticText 'New bio'\n",
        )
        parsed = verify.parse_verification(
            verify_json(
                [
                    {
                        "goal_id": bio_state.goal_checks[0].goal_id,
                        "status": "confirmed",
                        "actual": "New bio",
                        "source_task_quote": bio_task,
                        "evidence": [{"line": 2, "quote": "New bio"}],
                    }
                ]
            ),
            bio_current,
            bio_state,
            mode="stop",
        )
        self.assertFalse(parsed["all_confirmed"])
        self.assertIn("draft/status", " ".join(parsed["invalid"]))

        alert_state = state_for(current=frame(history=HISTORY))
        alert_current = frame(
            text="[1] alert 'Upvote successful. Retract upvote'\n",
            history=HISTORY,
        )
        parsed = verify.parse_verification(
            verify_json(
                [
                    {
                        "goal_id": alert_state.goal_checks[0].goal_id,
                        "status": "confirmed",
                        "actual": 1,
                        "source_task_quote": VOTE_TASK,
                        "evidence": [{"line": 1, "quote": "Retract upvote"}],
                    }
                ]
            ),
            alert_current,
            alert_state,
            mode="pending",
        )
        self.assertFalse(parsed["all_confirmed"])
        self.assertIn("draft/status", " ".join(parsed["invalid"]))


class StableObjectTests(unittest.TestCase):
    def test_object_key_is_title_not_element_id(self):
        first = verify.parse_ax(
            frame(text=f"[1] heading '{TITLE}'\n[2] button 'Upvote'\n")
        )
        second = verify.parse_ax(
            frame(text=f"[1] heading '{TITLE}'\n[2] button 'Upvote'\n[9] button 'Upvote'\n")
        )
        self.assertEqual(
            verify.object_key(first, first.by_id["2"]),
            "name:" + TITLE,
        )
        self.assertEqual(
            verify.object_key(first, first.by_id["2"]),
            verify.object_key(second, second.by_id["9"]),
        )

    def test_same_id_with_another_object_does_not_confirm(self):
        state = state_for(current=frame(text=LISTING_BEFORE, step=0))
        state.set_pending(pending(("goal-1",), object_key="name:" + TITLE))
        current = frame(
            text=(
                "[1] heading '" + OTHER_TITLE + "'\n"
                "[2] textbox 'Search posts'\n"
                "\t[4] button 'Retract upvote'\n"
            ),
            step=1,
        )
        result = verify.resolve_pending(current, state)
        self.assertEqual(result["status"], "unknown")
        self.assertIsNotNone(state.pending_for(0))
        self.assertEqual(state.goal_checks[0].objects, [])

    def test_missing_stable_identity_stays_unknown(self):
        state = state_for(
            current=frame(text="[1] textbox 'Vote'\n\t[2] button 'Upvote'\n", step=0)
        )
        state.set_pending(pending(("goal-1",), object_key=""))
        current = frame(
            text="[1] textbox 'Vote'\n\t[2] button 'Retract upvote'\n",
            step=1,
        )
        result = verify.resolve_pending(current, state)
        self.assertEqual(result["status"], "unknown")
        self.assertIsNotNone(state.pending_for(0))
        self.assertEqual(state.goal_checks[0].objects, [])

    def test_repeated_same_title_with_a_new_id_is_not_counted_twice(self):
        task = "Thumbs down the top 4 post ever in movies."
        state = state_for(
            task,
            frame(task=task, text="[1] heading 'Top movie post 0'\n[2] button 'Downvote'\n", step=0),
        )
        goal = state.goal_checks[0]
        state.set_pending(pending(("goal-1",), object_key="name:Top movie post 0",
                                  element_name="Downvote"))
        result = verify.resolve_pending(
            frame(
                task=task,
                text="[1] heading 'Top movie post 0'\n[9] button 'Retract downvote'\n",
                step=1,
            ),
            state,
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(goal.objects, ["name:Top movie post 0"])

        state.set_pending(
            pending(
                ("goal-1",),
                object_key="name:Top movie post 0",
                element_name="Downvote",
                element_id="11",
                step=2,
            )
        )
        verify.resolve_pending(
            frame(
                task=task,
                text="[1] heading 'Top movie post 0'\n[11] button 'Retract downvote'\n",
                step=3,
            ),
            state,
        )
        self.assertEqual(goal.objects, ["name:Top movie post 0"])


class PendingEffectTests(unittest.TestCase):
    def test_runtime_registers_and_clears_the_form_wrapped_vote_effect(self):
        runtime = Runtime(lambda context, state: {"action": state.data.pop("_next")})
        state = {"_next": "click [4]"}
        runtime.advance(
            frame(text=LISTING_BEFORE, step=0),
            state,
        )
        pending_ = state["_pending_actions"]["0"]
        self.assertEqual(pending_.source["object_key"], "name:" + TITLE)
        state["_next"] = "scroll [down]"
        runtime.advance(
            frame(text=LISTING_AFTER, step=1, history=HISTORY),
            state,
        )
        self.assertEqual(state.get("_pending_actions", {}), {})
        count, scope = state["_goal_checks"]
        self.assertEqual(count.status, "verified")
        self.assertEqual(count.objects, ["name:" + TITLE])
        self.assertNotEqual(scope.status, "verified")
        with self.assertRaises(verify.GoalIncompleteError):
            verify.assert_stop(
                frame(text=LISTING_AFTER, step=1, history=HISTORY),
                TaskState(state),
            )

    def test_confirmed_count_clears_pending_but_semantic_still_blocks_stop(self):
        current = frame(step=1, history=HISTORY)
        state = state_for(current=current)
        count, scope = state.goal_checks

        def semantic(frame_, state_, mode):
            return {
                "checks": [
                    {
                        "goal_id": scope.goal_id,
                        "status": "unknown",
                        "reason": "newest scope still needs concrete business proof",
                    }
                ]
            }

        state.set_pending(
            pending(
                (count.goal_id, scope.goal_id),
                object_key="name:" + TITLE,
            )
        )
        result = verify.resolve_pending(current, state, semantic_verify=semantic)
        self.assertEqual(result["status"], "confirmed")
        self.assertIsNone(state.pending_for(0))
        self.assertEqual(count.status, "verified")
        self.assertEqual(count.objects, ["name:" + TITLE])
        self.assertNotEqual(scope.status, "verified")
        with self.assertRaises(verify.GoalIncompleteError):
            verify.assert_stop(current, state)

    def test_verified_count_survives_an_unrelated_semantic_model_check(self):
        current = frame(step=1, history=HISTORY)
        state = state_for(current=current)
        count = state.goal_checks[0]
        count.status = "verified"
        count.objects.append("name:" + TITLE)
        verify._apply_verification(
            current,
            state,
            [
                {
                    "goal_id": count.goal_id,
                    "status": "unknown",
                    "reason": "unrelated semantic result",
                }
            ],
            source="model",
        )
        self.assertEqual(count.status, "verified")

    def test_four_objects_clear_each_pending_while_ranking_stays_unknown(self):
        task = "Thumbs down the top 4 post ever in movies."
        current = frame(
            task=task,
            text="[1] heading 'Top movie post 0'\n[2] button 'Downvote'\n",
            step=0,
        )
        state = state_for(task, current)
        count, scope = state.goal_checks
        self.assertEqual((count.kind, scope.kind), ("count_per_object", "semantic"))

        for index in range(4):
            title = f"Top movie post {index}"
            state.set_pending(
                pending(
                    (count.goal_id, scope.goal_id),
                    object_key="name:" + title,
                    element_name="Downvote",
                    step=index * 2,
                )
            )
            result = verify.resolve_pending(
                frame(
                    task=task,
                    text=f"[1] heading '{title}'\n[2] button 'Retract downvote'\n",
                    step=index * 2 + 1,
                ),
                state,
                semantic_verify=lambda frame_, state_, mode: {
                    "checks": [
                        {
                            "goal_id": scope.goal_id,
                            "status": "unknown",
                            "reason": "ranking still needs history",
                        }
                    ]
                },
            )
            self.assertEqual(result["status"], "confirmed")
            self.assertIsNone(state.pending_for(0))
            self.assertEqual(len(count.objects), index + 1)
            if index < 3:
                self.assertNotEqual(count.status, "verified")
        self.assertEqual(count.status, "verified")
        self.assertNotEqual(scope.status, "verified")
        with self.assertRaises(verify.GoalIncompleteError):
            verify.assert_stop(
                frame(task=task, text="[1] heading 'movies'\n", step=9),
                state,
            )


if __name__ == "__main__":
    unittest.main()
