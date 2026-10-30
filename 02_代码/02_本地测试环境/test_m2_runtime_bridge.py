"""Small deterministic checks for the local Runtime bridge helpers.

The browser/Runtime integration itself is exercised by
``m2_runtime_bridge.py``; these tests only pin the pure AX parser, the
field/object scoping of the verification stub and the premature-stop correction
path.  No model, fixture or grading truth is used.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from m2_ax_text import field_atom, parse_atoms
from m2_runtime_policy import ScriptedPolicy


def ax(*lines: str) -> str:
    return "\n".join(lines) + "\n"


class AXTextTests(unittest.TestCase):
    def test_parser_keeps_regions_links_values_and_ancestors(self):
        text = ax(
            "Tab 0 (current): forum",
            "[1] navigation",
            "  [2] link 'Forum' url: http://127.0.0.1:8765/forum",
            "[3] heading 'Forum' level: 1",
            "[4] paragraph '个人简介：旧简介'",
            "[5] textbox '个人简介' value: '旧简介'",
            "[6] button '保存简介'",
            "[7] alert '保存成功'",
            "  [8] StaticText '已保存'",
        )
        atoms = parse_atoms(text)
        self.assertEqual(len(atoms), 8)
        self.assertEqual(atoms[1].role, "link")
        self.assertEqual(atoms[1].url, "http://127.0.0.1:8765/forum")
        self.assertEqual(atoms[4].name, "个人简介")
        self.assertTrue(atoms[7].inside_alert)
        self.assertFalse(atoms[3].inside_form)
        self.assertEqual(field_atom(atoms, "bio")[1], "旧简介")


class VerificationScopeTests(unittest.TestCase):
    def check(self, task, goal, text):
        policy = ScriptedPolicy()
        payload = {
            "task": task,
            "original_task": task,
            "accessibility_tree": text,
            "goal_checks_from_original_task": [goal],
        }
        result = json.loads(policy.verify(None, None, payload))
        return result["checks"][0]

    def test_exact_value_requires_field_label_not_any_same_text(self):
        task = "把个人简介改为 开发者-abc"
        goal = {
            "goal_id": "goal-1",
            "kind": "exact_equal",
            "target": "开发者-abc",
            "field": "bio",
            "source_quote": task,
        }
        unrelated = ax(
            "[1] heading '开发者-abc'",
            "[2] paragraph '文章：开发者-abc'",
            "[3] paragraph '个人简介：旧简介开发者-abc'",
        )
        check = self.check(task, goal, unrelated)
        self.assertEqual(check["status"], "failed")
        exact = ax("[1] heading '开发者-abc'", "[2] paragraph '个人简介：开发者-abc'")
        self.assertEqual(self.check(task, goal, exact)["status"], "confirmed")

    def test_cart_check_reads_cart_line_not_product_heading(self):
        task = "把键盘加入购物车"
        goal = {
            "goal_id": "goal-1",
            "kind": "item_exact",
            "target": "键盘",
            "source_quote": task,
        }
        empty = ax(
            "[1] heading '键盘'",
            "[2] paragraph '价格：199 元'",
            "[3] paragraph '购物车：'",
        )
        check = self.check(task, goal, empty)
        self.assertEqual(check["status"], "failed")
        self.assertEqual(check["actual"], [])
        filled = ax("[1] heading '键盘'", "[2] paragraph '购物车：键盘'")
        self.assertEqual(self.check(task, goal, filled)["status"], "confirmed")

    def test_count_state_and_order_use_business_lines(self):
        task = "点赞技术帖子一次"
        goal = {
            "goal_id": "goal-1",
            "kind": "count_once",
            "target": 1,
            "source_quote": task,
        }
        self.assertEqual(
            self.check(task, goal, ax("[1] paragraph '点赞数：1'"))["status"],
            "confirmed",
        )
        self.assertEqual(
            self.check(task, goal, ax("[1] paragraph '点赞数：0'"))["status"],
            "failed",
        )


class PrematureStopTests(unittest.TestCase):
    def test_policy_attempts_stop_once_then_runtime_correction_continues(self):
        page = ax(
            "[1] textbox '个人简介'",
            "[2] button '保存简介'",
            "[3] paragraph '个人简介：旧简介'",
        )
        context = SimpleNamespace(
            page=page,
            goal_checks=(
                {
                    "goal_id": "goal-1",
                    "kind": "exact_equal",
                    "field": "bio",
                    "target": "开发者-abc",
                    "status": "pending",
                },
            ),
            write_guard=None,
            task="把个人简介改为 开发者-abc",
            url="http://127.0.0.1:8765/forum",
            step=0,
        )
        policy = ScriptedPolicy(premature_stop=True)
        first = json.loads(policy.generate(context, None))["action"]
        self.assertTrue(first.startswith("stop ["))
        corrected = json.loads(
            policy.correct(context, None, first, ValueError("Cannot stop"))
        )["action"]
        self.assertTrue(corrected.startswith("type ["))
        events = policy.drain_events()
        self.assertTrue(any(event["kind"] == "runtime_rejection" for event in events))
        self.assertTrue(any(event.get("after_runtime_correction") for event in events))


if __name__ == "__main__":
    unittest.main()
