"""Local M2 fault/grading tests. No model, no official benchmark."""
import unittest
from pathlib import Path

from m2_faults import FaultPlan, WRITE_OPERATIONS
from m2_grading import TASKS, grade
from sandbox import Fixture, create_app

TOKEN = "fixed"
PROFILE_TARGET = f"开发者-{TOKEN}"
POST_TARGET = f"并行调度-{TOKEN}"
REPLY_TARGET = f"已确认-{TOKEN}"


def make_fixture(faults=None, seed=None, token=TOKEN):
    plan = FaultPlan.from_dict({"token": token, "faults": faults or {}, "seed": seed or {}})
    return Fixture(token=token, fault_plan=plan)


def post(fixture, operation, value=None):
    client = create_app(fixture).test_client()
    data = {} if value is None else {"value": value}
    return client.post(f"/write/{operation}", data=data)


def get_text(fixture, path):
    return create_app(fixture).test_client().get(path).get_data(as_text=True)


def requirement_map(report):
    return {item["key"]: item for item in report["requirements"]}


def write_rule_map(report):
    return {(item["operation"], item["kind"]): item for item in report["write_rules"]}


class NormalTaskTests(unittest.TestCase):
    def test_scalar_tasks_pass_with_exact_value_and_one_target_write(self):
        for task, value in [("profile", PROFILE_TARGET),
                            ("post", POST_TARGET),
                            ("reply", REPLY_TARGET)]:
            with self.subTest(task=task):
                fixture = make_fixture()
                response = post(fixture, task, value)
                self.assertEqual(response.status_code, 302)
                report = fixture.grade_report(task)
                self.assertTrue(report["passed"], report)
                self.assertEqual(fixture.write_counts, {task: 1})
                self.assertEqual(write_rule_map(report)[(task, "target")]["actual"], 1)
                self.assertEqual(report["requirements"][0]["actual"], value)

    def test_single_effect_tasks_pass_once(self):
        for task in ("subscribe", "vote", "cart"):
            with self.subTest(task=task):
                fixture = make_fixture()
                response = post(fixture, task)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(fixture.grade(task), fixture.grade_report(task))
                self.assertEqual(fixture.write_counts, {task: 1})

    def test_checkout_requires_cart_and_exactly_one_order(self):
        fixture = make_fixture()
        post(fixture, "cart")
        response = post(fixture, "checkout")
        self.assertEqual(response.status_code, 302)
        report = fixture.grade_report("checkout")
        self.assertTrue(report["passed"], report)
        self.assertEqual(fixture.cart, ["键盘"])
        self.assertEqual(len(fixture.orders), 1)
        self.assertEqual(fixture.write_counts, {"cart": 1, "checkout": 1})
        self.assertIn("已提交", get_text(fixture, "/shop"))

    def test_actor_claims_are_advisory_only(self):
        fixture = make_fixture()
        claimed = [{"key": "profile_exact", "passed": True}]
        report = fixture.grade_report("profile", actor_claims=claimed)
        self.assertFalse(report["passed"])
        self.assertTrue(report["actor_claims_ignored"])
        self.assertEqual(report["actor_claims"], claimed)

        post(fixture, "profile", PROFILE_TARGET)
        claimed_false = [{"key": "profile_exact", "passed": False}]
        report = fixture.grade_report("profile", actor_claims=claimed_false)
        self.assertTrue(report["passed"])
        self.assertTrue(report["actor_claims_ignored"])


class CompositeTaskTests(unittest.TestCase):
    def test_composites_have_at_least_two_requirements(self):
        for task in ("profile_post", "reply_subscribe", "subscribe_vote", "cart_checkout"):
            with self.subTest(task=task):
                self.assertGreaterEqual(len(TASKS[task].requirements), 2)

    def test_profile_post_needs_both_requirements(self):
        fixture = make_fixture()
        post(fixture, "profile", PROFILE_TARGET)
        report = fixture.grade_report("profile_post")
        self.assertFalse(report["passed"])
        self.assertTrue(requirement_map(report)["profile_exact"]["passed"])
        self.assertFalse(requirement_map(report)["post_exact"]["passed"])

        post(fixture, "post", POST_TARGET)
        self.assertTrue(fixture.grade("profile_post"), fixture.grade_report("profile_post"))

    def test_subscribe_vote_needs_both_requirements(self):
        fixture = make_fixture()
        post(fixture, "subscribe")
        report = fixture.grade_report("subscribe_vote")
        self.assertFalse(report["passed"])
        self.assertTrue(requirement_map(report)["subscribed"]["passed"])
        self.assertFalse(requirement_map(report)["one_vote"]["passed"])
        post(fixture, "vote")
        self.assertTrue(fixture.grade("subscribe_vote"))

    def test_reply_subscribe_and_cart_checkout_composites(self):
        reply = make_fixture()
        post(reply, "reply", REPLY_TARGET)
        post(reply, "subscribe")
        self.assertTrue(reply.grade("reply_subscribe"), reply.grade_report("reply_subscribe"))

        checkout = make_fixture()
        post(checkout, "cart")
        post(checkout, "checkout")
        report = checkout.grade_report("cart_checkout")
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["write_counts"], {"cart": 1, "checkout": 1})

    def test_missing_target_in_composite_cannot_pass(self):
        fixture = make_fixture(faults={"subscribe": {"mode": "missing_target"}})
        response = post(fixture, "subscribe")
        self.assertEqual(response.status_code, 200)
        self.assertIn("缺项", response.get_data(as_text=True))
        post(fixture, "vote")
        report = fixture.grade_report("subscribe_vote")
        self.assertFalse(report["passed"])
        self.assertFalse(requirement_map(report)["subscribed"]["passed"])
        self.assertTrue(requirement_map(report)["one_vote"]["passed"])
        self.assertEqual(fixture.write_counts.get("subscribe", 0), 0)

    def test_checkout_missing_order_cannot_pass(self):
        fixture = make_fixture(faults={"checkout": {"mode": "missing_target"}})
        post(fixture, "cart")
        response = post(fixture, "checkout")
        self.assertEqual(response.status_code, 200)
        report = fixture.grade_report("checkout")
        self.assertFalse(report["passed"])
        self.assertTrue(requirement_map(report)["cart_exact"]["passed"])
        self.assertFalse(requirement_map(report)["one_order"]["passed"])
        self.assertEqual(fixture.orders, [])


class FaultTests(unittest.TestCase):
    def test_no_effect_success_is_consumed_and_recoverable_for_every_operation(self):
        for operation in sorted(WRITE_OPERATIONS):
            with self.subTest(operation=operation):
                fixture = make_fixture(faults={operation: {"mode": "no_effect_success"}})
                if operation == "checkout":
                    post(fixture, "cart")
                before = fixture.operation_state(operation)
                value = {"profile": PROFILE_TARGET, "post": POST_TARGET,
                         "reply": REPLY_TARGET}.get(operation)
                response = post(fixture, operation, value)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(fixture.operation_state(operation), before)
                self.assertEqual(fixture.write_counts.get(operation, 0), 0)
                self.assertEqual(fixture.attempt_counts[operation], 1)
                self.assertEqual(fixture.fault_plan.events[0]["mode"], "no_effect_success")

                post(fixture, operation, value)
                self.assertEqual(fixture.write_counts.get(operation, 0), 1)
                self.assertTrue(fixture.grade(operation), fixture.grade_report(operation))

    def test_append_value_is_observable_and_correctable_for_scalar_tasks(self):
        cases = [("profile", "bio", PROFILE_TARGET),
                 ("post", "title", POST_TARGET),
                 ("reply", "reply", REPLY_TARGET)]
        for operation, field_name, target in cases:
            with self.subTest(operation=operation):
                fixture = make_fixture(
                    faults={operation: {"mode": "append_value"}},
                    seed={field_name: "旧值"})
                post(fixture, operation, target)
                self.assertEqual(getattr(fixture, field_name), "旧值" + target)
                report = fixture.grade_report(operation)
                self.assertFalse(report["passed"])
                self.assertEqual(report["write_counts"][operation], 1)
                self.assertEqual(write_rule_map(report)[(operation, "target")]["actual"], 0)

                post(fixture, operation, target)
                self.assertEqual(getattr(fixture, field_name), target)
                report = fixture.grade_report(operation)
                self.assertTrue(report["passed"], report)
                self.assertEqual(report["write_counts"][operation], 2)
                self.assertEqual(write_rule_map(report)[(operation, "target")]["actual"], 1)

    def test_unknown_commit_profile_query_then_no_resend(self):
        fixture = make_fixture(faults={"profile": {"mode": "commit_lost_receipt"}})
        response = post(fixture, "profile", PROFILE_TARGET)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(fixture.bio, PROFILE_TARGET)
        self.assertEqual(fixture.write_counts["profile"], 1)
        self.assertIn(PROFILE_TARGET, get_text(fixture, "/forum"))
        self.assertTrue(fixture.grade("profile"))

        # A blind resend after the unknown receipt is a duplicate target write.
        post(fixture, "profile", PROFILE_TARGET)
        report = fixture.grade_report("profile")
        self.assertFalse(report["passed"])
        self.assertEqual(report["write_counts"]["profile"], 2)
        self.assertEqual(write_rule_map(report)[("profile", "target")]["actual"], 2)

    def test_unknown_commit_vote_and_checkout_are_one_shot(self):
        vote = make_fixture(faults={"vote": {"mode": "commit_lost_receipt"}})
        self.assertEqual(post(vote, "vote").status_code, 503)
        self.assertEqual(vote.votes, 1)
        self.assertIn("点赞数：1", get_text(vote, "/forum"))
        self.assertTrue(vote.grade("vote"))
        post(vote, "vote")
        self.assertEqual(vote.votes, 2)
        self.assertFalse(vote.grade("vote"))

        checkout = make_fixture(faults={"checkout": {"mode": "commit_lost_receipt"}})
        post(checkout, "cart")
        self.assertEqual(post(checkout, "checkout").status_code, 503)
        self.assertEqual(len(checkout.orders), 1)
        self.assertIn("已提交", get_text(checkout, "/shop"))
        self.assertTrue(checkout.grade("checkout"))
        post(checkout, "checkout")
        self.assertEqual(len(checkout.orders), 2)
        self.assertFalse(checkout.grade("checkout"))

    def test_missing_target_operations_do_not_write(self):
        cases = [("subscribe", "subscribed", False),
                 ("vote", "votes", 0),
                 ("cart", "cart", [])]
        for operation, field_name, expected in cases:
            with self.subTest(operation=operation):
                fixture = make_fixture(faults={operation: {"mode": "missing_target"}})
                response = post(fixture, operation)
                self.assertEqual(response.status_code, 200)
                self.assertIn("缺项", response.get_data(as_text=True))
                self.assertEqual(getattr(fixture, field_name), expected)
                self.assertEqual(fixture.write_counts.get(operation, 0), 0)
                self.assertFalse(fixture.grade(operation))

        reply = make_fixture(faults={"reply": {"mode": "missing_target"}})
        response = post(reply, "reply", REPLY_TARGET)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reply.reply, "")
        self.assertFalse(reply.grade("reply"))

    def test_partial_failure_after_verified_prefix_preserves_prefix(self):
        fixture = make_fixture(faults={"post": {"mode": "no_effect_success"}})
        post(fixture, "profile", PROFILE_TARGET)
        post(fixture, "post", POST_TARGET)
        report = fixture.grade_report("profile_post")
        self.assertFalse(report["passed"])
        self.assertTrue(requirement_map(report)["profile_exact"]["passed"])
        self.assertFalse(requirement_map(report)["post_exact"]["passed"])
        self.assertEqual(fixture.write_counts, {"profile": 1})
        self.assertIn(PROFILE_TARGET, get_text(fixture, "/forum"))

        post(fixture, "post", POST_TARGET)
        report = fixture.grade_report("profile_post")
        self.assertTrue(report["passed"], report)
        self.assertEqual(fixture.write_counts, {"profile": 1, "post": 1})
        self.assertEqual(fixture.attempt_counts["post"], 2)
        self.assertEqual(fixture.fault_plan.events, [
            {"operation": "post", "mode": "no_effect_success",
             "times": 1, "fired": 1, "note": ""}])

    def test_partial_checkout_recovery_keeps_cart_write(self):
        fixture = make_fixture(faults={"checkout": {"mode": "no_effect_success"}})
        post(fixture, "cart")
        post(fixture, "checkout")
        self.assertFalse(fixture.grade("checkout"))
        self.assertEqual(fixture.cart, ["键盘"])
        self.assertEqual(fixture.write_counts, {"cart": 1})
        self.assertIn("键盘", get_text(fixture, "/shop"))

        post(fixture, "checkout")
        self.assertTrue(fixture.grade("checkout"))
        self.assertEqual(fixture.write_counts, {"cart": 1, "checkout": 1})
        self.assertEqual(len(fixture.orders), 1)

    def test_duplicate_writes_are_rejected_by_grade(self):
        vote = make_fixture()
        post(vote, "vote")
        post(vote, "vote")
        self.assertEqual(vote.votes, 2)
        self.assertFalse(vote.grade("vote"))

        checkout = make_fixture()
        post(checkout, "cart")
        post(checkout, "checkout")
        post(checkout, "checkout")
        self.assertEqual(len(checkout.orders), 2)
        self.assertFalse(checkout.grade("checkout"))

        reply = make_fixture()
        post(reply, "reply", REPLY_TARGET)
        post(reply, "reply", REPLY_TARGET)
        report = reply.grade_report("reply")
        self.assertFalse(report["passed"])
        self.assertEqual(write_rule_map(report)[("reply", "target")]["actual"], 2)

        subscribe = make_fixture()
        post(subscribe, "subscribe")
        post(subscribe, "subscribe")
        self.assertFalse(subscribe.grade("subscribe"))


class FaultPlanTests(unittest.TestCase):
    def test_invalid_fault_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            FaultPlan.from_dict({"faults": {"profile": {"mode": "not-a-mode"}}})
        with self.assertRaises(ValueError):
            FaultPlan.from_dict({"faults": {"vote": {"mode": "append_value"}}})
        with self.assertRaises(ValueError):
            FaultPlan.from_dict({"faults": {"profile": {"mode": "no_effect_success", "times": 0}}})
        with self.assertRaises(ValueError):
            FaultPlan.from_dict({"seed": {"unknown": 1}})

    def test_plan_round_trip_keeps_seed_and_fault(self):
        plan = FaultPlan.from_dict({
            "token": "t1",
            "seed": {"bio": "旧值"},
            "faults": {"profile": {"mode": "append_value", "times": 1, "note": "demo"}}})
        data = plan.to_dict()
        self.assertEqual(data["token"], "t1")
        self.assertEqual(data["seed"], {"bio": "旧值"})
        self.assertEqual(data["faults"]["profile"]["mode"], "append_value")
        self.assertEqual(data["faults"]["profile"]["times"], 1)

    def test_grade_rejects_unknown_task(self):
        with self.assertRaises(KeyError):
            grade(make_fixture(), "not-a-task")

    def test_example_fault_plans_are_valid(self):
        paths = sorted((Path(__file__).resolve().parent / "m2_fault_plans").glob("*.json"))
        self.assertGreaterEqual(len(paths), 8)
        for path in paths:
            with self.subTest(path=path.name):
                plan = FaultPlan.from_file(path)
                self.assertTrue(plan.specs, path.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
