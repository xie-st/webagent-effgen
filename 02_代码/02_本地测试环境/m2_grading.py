"""Independent M2 task requirements and grading for the local fixtures.

The judge reads the actual fixture business state and the requirements
extracted from the original task text.  It never accepts an actor-provided
``goal_checks`` list as authoritative; such a list may be recorded as
advisory evidence only.

Write rules are reported separately from business requirements:

* ``total`` counts every committed write for an operation and is used for
  one-shot effects (like, order, cart add, subscription).
* ``target`` counts committed writes whose stored value became the required
  value.  This catches an unknown commit being resent (two target writes)
  while still allowing a visibly wrong replacement to be corrected.
"""
from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Any, Callable

from m2_faults import WRITE_OPERATIONS


@dataclass(frozen=True)
class RequirementSpec:
    key: str
    description: str
    actual: Callable[[Any], Any]
    expected: Callable[[Any], Any]
    equals: Callable[[Any, Any], bool] = operator.eq


@dataclass(frozen=True)
class WriteRule:
    operation: str
    kind: str
    expected: int
    description: str
    target: Callable[[Any], Any] | None = None

    def __post_init__(self):
        if self.operation not in WRITE_OPERATIONS:
            raise ValueError(f"unknown write operation: {self.operation!r}")
        if self.kind not in ("total", "target"):
            raise ValueError(f"unknown write rule kind: {self.kind!r}")
        if self.kind == "target" and self.target is None:
            raise ValueError("target write rule needs a target value")


@dataclass(frozen=True)
class TaskSpec:
    name: str
    prompt: str
    requirements: tuple[RequirementSpec, ...]
    write_rules: tuple[WriteRule, ...]
    initial_path: str = "/forum"


def _scalar(key, field_name, label, expected, description):
    return RequirementSpec(
        key=key, description=description,
        actual=lambda fixture: getattr(fixture, field_name),
        expected=expected)


def _target_rule(operation, label, expected):
    return WriteRule(
        operation=operation, kind="target", expected=1,
        description=f"{operation} 必须恰好提交 1 次达到要求的{label}",
        target=expected)


def _total_rule(operation, label):
    return WriteRule(
        operation=operation, kind="total", expected=1,
        description=f"{operation} 必须恰好提交 1 次{label}")


def _profile_requirement():
    return _scalar(
        "profile_exact", "bio", "个人简介",
        lambda fixture: f"开发者-{fixture.token}",
        "个人简介必须精确等于“开发者-{token}”，不能保留或追加旧内容")


def _post_requirement():
    return _scalar(
        "post_exact", "title", "帖子标题",
        lambda fixture: f"并行调度-{fixture.token}",
        "帖子标题必须精确等于“并行调度-{token}”")


def _reply_requirement():
    return _scalar(
        "reply_exact", "reply", "回复内容",
        lambda fixture: f"已确认-{fixture.token}",
        "回复内容必须精确等于“已确认-{token}”")


def _profile_target():
    return lambda fixture: f"开发者-{fixture.token}"


def _post_target():
    return lambda fixture: f"并行调度-{fixture.token}"


def _reply_target():
    return lambda fixture: f"已确认-{fixture.token}"


_SUBSCRIBE = RequirementSpec(
    key="subscribed", description="技术版块必须处于已订阅状态",
    actual=lambda fixture: bool(fixture.subscribed),
    expected=lambda fixture: True)

_VOTES = RequirementSpec(
    key="one_vote", description="技术帖子必须恰好有 1 次点赞",
    actual=lambda fixture: int(fixture.votes),
    expected=lambda fixture: 1)

_CART = RequirementSpec(
    key="cart_exact", description="购物车必须恰好包含一件“键盘”",
    actual=lambda fixture: list(fixture.cart),
    expected=lambda fixture: ["键盘"])

_ORDER_COUNT = RequirementSpec(
    key="one_order", description="必须恰好生成 1 个订单",
    actual=lambda fixture: len(fixture.orders),
    expected=lambda fixture: 1)

_ORDER_FLAG = RequirementSpec(
    key="order_submitted", description="订单必须处于已提交状态",
    actual=lambda fixture: bool(fixture.ordered),
    expected=lambda fixture: True)


TASKS: dict[str, TaskSpec] = {
    "profile": TaskSpec(
        name="profile",
        prompt="把个人简介改为 开发者-{token}",
        requirements=(_profile_requirement(),),
        write_rules=(_target_rule("profile", "个人简介", _profile_target()),)),
    "post": TaskSpec(
        name="post",
        prompt="发表标题为 并行调度-{token} 的帖子",
        requirements=(_post_requirement(),),
        write_rules=(_target_rule("post", "帖子标题", _post_target()),)),
    "reply": TaskSpec(
        name="reply",
        prompt="回复内容为 已确认-{token}",
        requirements=(_reply_requirement(),),
        write_rules=(_target_rule("reply", "回复内容", _reply_target()),)),
    "subscribe": TaskSpec(
        name="subscribe",
        prompt="订阅技术版块",
        requirements=(_SUBSCRIBE,),
        write_rules=(_total_rule("subscribe", "订阅"),)),
    "vote": TaskSpec(
        name="vote",
        prompt="点赞技术帖子一次",
        requirements=(_VOTES,),
        write_rules=(_total_rule("vote", "点赞"),)),
    "cart": TaskSpec(
        name="cart",
        prompt="把键盘加入购物车",
        requirements=(_CART,),
        write_rules=(_total_rule("cart", "加入购物车"),)),
    "checkout": TaskSpec(
        name="checkout",
        prompt="购买键盘并提交订单",
        requirements=(_CART, _ORDER_COUNT, _ORDER_FLAG),
        write_rules=(_total_rule("cart", "加入购物车"),
                     _total_rule("checkout", "提交订单")),
        initial_path="/shop"),
    "profile_post": TaskSpec(
        name="profile_post",
        prompt="把个人简介改为 开发者-{token}，并发表标题为 并行调度-{token} 的帖子",
        requirements=(_profile_requirement(), _post_requirement()),
        write_rules=(_target_rule("profile", "个人简介", _profile_target()),
                     _target_rule("post", "帖子标题", _post_target()))),
    "reply_subscribe": TaskSpec(
        name="reply_subscribe",
        prompt="回复内容为 已确认-{token}，并订阅技术版块",
        requirements=(_reply_requirement(), _SUBSCRIBE),
        write_rules=(_target_rule("reply", "回复内容", _reply_target()),
                     _total_rule("subscribe", "订阅"))),
    "subscribe_vote": TaskSpec(
        name="subscribe_vote",
        prompt="订阅技术版块，并点赞技术帖子一次",
        requirements=(_SUBSCRIBE, _VOTES),
        write_rules=(_total_rule("subscribe", "订阅"),
                     _total_rule("vote", "点赞"))),
    "cart_checkout": TaskSpec(
        name="cart_checkout",
        prompt="把键盘加入购物车并提交订单",
        requirements=(_CART, _ORDER_COUNT, _ORDER_FLAG),
        write_rules=(_total_rule("cart", "加入购物车"),
                     _total_rule("checkout", "提交订单")),
        initial_path="/shop"),
}

TASK_NAMES = tuple(TASKS)


def task_prompt(task: str, token: str) -> str:
    return TASKS[task].prompt.format(token=token)


def initial_path(task: str) -> str:
    return TASKS[task].initial_path


def _target_write_count(fixture, operation: str, target_value: Any) -> int:
    count = 0
    for event in getattr(fixture, "write_events", ()):
        if (event.get("operation") == operation and event.get("committed")
                and event.get("after") == target_value):
            count += 1
    return count


def grade(fixture, task: str, actor_claims=None) -> dict:
    """Grade ``task`` from the actual fixture state, ignoring actor claims."""
    spec = TASKS.get(task)
    if spec is None:
        raise KeyError(f"unknown task: {task!r}")

    requirement_results = []
    for requirement in spec.requirements:
        expected = requirement.expected(fixture)
        actual = requirement.actual(fixture)
        requirement_results.append({
            "key": requirement.key,
            "description": requirement.description.format(token=fixture.token),
            "expected": expected,
            "actual": actual,
            "passed": bool(requirement.equals(actual, expected)),
        })

    write_results = []
    for rule in spec.write_rules:
        if rule.kind == "total":
            target_value = None
            actual = int(getattr(fixture, "write_counts", {}).get(rule.operation, 0))
        else:
            target_value = rule.target(fixture)
            actual = _target_write_count(fixture, rule.operation, target_value)
        write_results.append({
            "operation": rule.operation,
            "kind": rule.kind,
            "description": rule.description,
            "expected": rule.expected,
            "actual": actual,
            "target_value": target_value,
            "passed": actual == rule.expected,
        })

    passed = (all(item["passed"] for item in requirement_results)
              and all(item["passed"] for item in write_results))
    snapshot = fixture.business_snapshot()
    return {
        "task": task,
        "passed": passed,
        "requirements": requirement_results,
        "write_rules": write_results,
        "write_counts": dict(getattr(fixture, "write_counts", {})),
        "attempt_counts": dict(getattr(fixture, "attempt_counts", {})),
        "faults": fixture.fault_plan.to_dict(),
        "business_state": snapshot,
        "actor_claims": actor_claims,
        "actor_claims_ignored": actor_claims is not None,
        "judged_from": "actual_fixture_state_and_original_task_requirements",
        "official_score": False,
        "model_calls": None,
    }
