"""M2 local acceptance runner.

Two modes:

* ``--suite scripted`` (default) runs deterministic scripted browser
  scenarios against the fault fixtures and grades them independently.
  This is an environment check, not a model result.
* ``--agent module:function`` injects a real decision function (for example
  the future harness Runtime adapter) and records the same independent grade.
  It still is a local synthetic run, not an official score.

Evidence is written to the project's local test-result archive.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright

from m2_faults import FaultPlan
from m2_grading import TASK_NAMES, grade, initial_path, task_prompt
from runner import BrowserAdapter
from sandbox import Fixture, LocalServer

ROOT = Path(__file__).resolve().parent
PROJECT = Path(os.environ.get("WEBAGENT_PROJECT_ROOT", ROOT.parents[1]))
EVIDENCE_ROOT = PROJECT / "01_文本/05_测试结果/local"


def new_evidence_dir(label):
    folder = EVIDENCE_ROOT / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ") + "_" + label)
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def model_call_total(records):
    counts = [record.get("model_calls") for record in records]
    return (sum(counts) if counts and all(type(value) is int and value >= 0
                                        for value in counts) else None)


def select_output_dir(requested, label):
    if requested is None:
        return new_evidence_dir(label)
    folder = Path(requested)
    folder.mkdir(parents=True, exist_ok=False)
    return folder


class ScriptedBrowser:
    """Small deterministic browser script used only for fixture checks."""

    def __init__(self, page, base_url, records):
        self.page = page
        self.base_url = base_url
        self.records = records

    def _record(self, action, outcome):
        self.records.append({
            "step": len(self.records) + 1,
            "time": datetime.now(timezone.utc).isoformat(),
            "url": self.page.url,
            "action": action,
            "result": outcome,
            "model_calls": 0,
            "decision_source": "scripted_browser",
        })

    def fill(self, label, text):
        action = f"type [{label}] [{text}]"
        try:
            self.page.get_by_label(label).fill(text)
            outcome = "executed"
        except Exception as exc:
            outcome = f"{type(exc).__name__}: {exc}"
        self._record(action, outcome)
        return outcome

    def click(self, button):
        action = f"click [{button}]"
        try:
            self.page.get_by_role("button", name=button, exact=True).click()
            outcome = "executed"
        except Exception as exc:
            outcome = f"{type(exc).__name__}: {exc}"
        self._record(action, outcome)
        return outcome

    def goto(self, path):
        action = f"goto [{path}]"
        try:
            self.page.goto(self.base_url + path)
            outcome = "executed"
        except Exception as exc:
            outcome = f"{type(exc).__name__}: {exc}"
        self._record(action, outcome)
        return outcome

    def text(self):
        return self.page.inner_text("body")


def _profile(script, fixture):
    script.fill("个人简介", f"开发者-{fixture.token}")


def _post(script, fixture):
    script.fill("帖子标题", f"并行调度-{fixture.token}")


def _reply(script, fixture):
    script.fill("回复内容", f"已确认-{fixture.token}")


def scenario_normal_profile(script, fixture):
    _profile(script, fixture)
    script.click("保存简介")
    assert f"开发者-{fixture.token}" in script.text()


def scenario_normal_checkout(script, fixture):
    script.click("键盘加入购物车")
    script.click("提交订单")
    body = script.text()
    assert "键盘" in body and "已提交" in body


def scenario_no_effect_recovery(script, fixture):
    _profile(script, fixture)
    script.click("保存简介")
    assert f"开发者-{fixture.token}" not in script.text()
    _profile(script, fixture)
    script.click("保存简介")
    assert f"开发者-{fixture.token}" in script.text()


def scenario_append_correction(script, fixture):
    _profile(script, fixture)
    script.click("保存简介")
    assert "旧简介" + f"开发者-{fixture.token}" in script.text()
    _profile(script, fixture)
    script.click("保存简介")
    body = script.text()
    assert f"开发者-{fixture.token}" in body
    assert "旧简介" not in body


def scenario_unknown_profile(script, fixture):
    _profile(script, fixture)
    script.click("保存简介")
    assert "写入结果未知" in script.text()
    script.goto("/forum")
    assert f"开发者-{fixture.token}" in script.text()


def scenario_unknown_checkout(script, fixture):
    script.click("键盘加入购物车")
    script.click("提交订单")
    assert "写入结果未知" in script.text()
    script.goto("/shop")
    body = script.text()
    assert "键盘" in body and "已提交" in body


def scenario_partial_profile_post(script, fixture):
    _profile(script, fixture)
    script.click("保存简介")
    _post(script, fixture)
    script.click("发表帖子")
    body = script.text()
    assert f"开发者-{fixture.token}" in body
    assert f"并行调度-{fixture.token}" not in body
    _post(script, fixture)
    script.click("发表帖子")
    assert f"并行调度-{fixture.token}" in script.text()


def scenario_missing_subscribe_vote(script, fixture):
    script.click("订阅技术版块")
    assert "缺项" in script.text()
    # The missing-target response is a terminal page, so return to the forum
    # to complete the independent requirement.
    script.goto("/forum")
    script.click("点赞技术帖子")
    assert "点赞数：1" in script.text()


def scenario_duplicate_vote(script, fixture):
    script.click("点赞技术帖子")
    script.click("点赞技术帖子")
    assert "点赞数：2" in script.text()


def scenario_missing_checkout(script, fixture):
    script.click("键盘加入购物车")
    script.click("提交订单")
    assert "缺项" in script.text()


SCENARIOS = [
    {"name": "normal_profile", "task": "profile",
     "note": "normal exact replacement", "expect_pass": True,
     "script": scenario_normal_profile},
    {"name": "normal_checkout", "task": "checkout",
     "note": "normal cart plus order", "expect_pass": True,
     "script": scenario_normal_checkout},
    {"name": "no_effect_recovery", "task": "profile",
     "seed": {"bio": "旧简介"}, "faults": {"profile": {"mode": "no_effect_success"}},
     "note": "success-looking no-op, verify then retry", "expect_pass": True,
     "script": scenario_no_effect_recovery},
    {"name": "append_correction", "task": "profile",
     "seed": {"bio": "旧简介"}, "faults": {"profile": {"mode": "append_value"}},
     "note": "old value plus target, verify then exact replace", "expect_pass": True,
     "script": scenario_append_correction},
    {"name": "unknown_profile", "task": "profile",
     "faults": {"profile": {"mode": "commit_lost_receipt"}},
     "note": "committed but 503; query, do not resend", "expect_pass": True,
     "script": scenario_unknown_profile},
    {"name": "unknown_checkout", "task": "checkout",
     "faults": {"checkout": {"mode": "commit_lost_receipt"}},
     "note": "order committed but receipt lost; query only", "expect_pass": True,
     "script": scenario_unknown_checkout},
    {"name": "partial_profile_post", "task": "profile_post",
     "seed": {"title": "旧帖子"},
     "faults": {"post": {"mode": "no_effect_success"}},
     "note": "profile prefix verified, post locally fails then recovers", "expect_pass": True,
     "script": scenario_partial_profile_post},
    {"name": "missing_subscribe_vote", "task": "subscribe_vote",
     "faults": {"subscribe": {"mode": "missing_target"}},
     "note": "composite with one missing target must fail", "expect_pass": False,
     "script": scenario_missing_subscribe_vote},
    {"name": "duplicate_vote", "task": "vote",
     "note": "two likes must fail one-shot grading", "expect_pass": False,
     "script": scenario_duplicate_vote},
    {"name": "missing_checkout", "task": "checkout",
     "faults": {"checkout": {"mode": "missing_target"}},
     "note": "cart present but order target missing must fail", "expect_pass": False,
     "script": scenario_missing_checkout},
]


def run_scripted_scenario(browser, spec, output_dir):
    name = spec["name"]
    task = spec["task"]
    token = f"m2{name}".replace("_", "")
    plan = FaultPlan.from_dict({
        "token": token,
        "seed": spec.get("seed") or {},
        "faults": spec.get("faults") or {},
    })
    fixture = Fixture(token=token, fault_plan=plan)
    scenario_dir = output_dir / "scenarios" / name
    scenario_dir.mkdir(parents=True, exist_ok=True)
    records = []
    body = ""
    script_error = None
    with LocalServer(fixture) as server:
        context = browser.new_context()
        try:
            page = context.new_page()
            page.goto(server.url + initial_path(task))
            script = ScriptedBrowser(page, server.url, records)
            try:
                spec["script"](script, fixture)
            except Exception as exc:
                script_error = f"{type(exc).__name__}: {exc}"
            body = script.text()
        finally:
            context.close()
    report = grade(fixture, task)
    matched = (script_error is None and report["passed"] == spec["expect_pass"])
    result = {
        "kind": "m2_scripted_browser_scenario",
        "scenario": name,
        "task": task,
        "note": spec["note"],
        "expected_pass": spec["expect_pass"],
        "actual_pass": report["passed"],
        "matched": matched,
        "script_error": script_error,
        "decision_source": "scripted_browser_no_model",
        "model_calls": 0,
        "official_score": False,
        "fault_plan": plan.to_dict(),
        "grade": report,
        "final_body_excerpt": body[:1600],
    }
    (scenario_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (scenario_dir / "actions.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8")
    return result


def run_suite(requested_out=None, headed=False):
    output_dir = select_output_dir(requested_out, "m2_scripted")
    started = datetime.now(timezone.utc)
    started_clock = time.perf_counter()
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        try:
            for spec in SCENARIOS:
                results.append(run_scripted_scenario(browser, spec, output_dir))
        finally:
            browser.close()
    all_matched = all(result["matched"] for result in results)
    manifest = {
        "kind": "m2_scripted_environment_check",
        "decision_source": "scripted_browser_no_model",
        "model_calls": 0,
        "official_score": False,
        "started_at": started.isoformat(),
        "seconds": time.perf_counter() - started_clock,
        "all_matched": all_matched,
        "scenario_count": len(results),
        "scenarios": [result["scenario"] for result in results],
        "evidence_dir": str(output_dir),
    }
    (output_dir / "run.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# M2 scripted local fault check", "",
             f"- decision source: `scripted_browser_no_model`; model calls: 0",
             f"- scenarios: {len(results)}; all matched: **{all_matched}**", "",
             "| scenario | task | expected pass | actual pass | matched | writes |",
             "|---|---|---:|---:|---:|---|"]
    for result in results:
        lines.append(
            f"| {result['scenario']} | {result['task']} | {result['expected_pass']} | "
            f"{result['actual_pass']} | {result['matched']} | "
            f"`{json.dumps(result['grade']['write_counts'], ensure_ascii=False)}` |")
    lines.extend(["", "This is a scripted browser environment check, not a model "
                       "acceptance or an official score.", ""])
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(output_dir)
    return 0 if all_matched else 1


def run_agent(requested_out, task, agent_spec, fault_plan_path=None,
              fault_json=None, token=None, headed=False, max_steps=40, timeout=300):
    if fault_plan_path and fault_json:
        raise ValueError("use either --fault-plan or --fault-json, not both")
    if fault_plan_path:
        plan = FaultPlan.from_file(fault_plan_path)
    elif fault_json:
        plan = FaultPlan.from_dict(json.loads(fault_json))
    else:
        plan = FaultPlan.empty()
    fixture_token = token or plan.token or uuid4().hex[:8]
    fixture = Fixture(token=fixture_token, fault_plan=plan)
    output_dir = select_output_dir(requested_out, f"m2_agent_{task}")
    module_name, function_name = agent_spec.split(":")
    module = importlib.import_module(module_name)
    decide = getattr(module, function_name)
    module_path = Path(module.__file__) if getattr(module, "__file__", None) else None
    manifest = {
        "kind": "m2_browser_local_acceptance",
        "decision_source": "external_agent",
        "official_score": False,
        "task": task,
        "token": fixture_token,
        "agent": agent_spec,
        "agent_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest() if module_path else None,
        "fault_plan": plan.to_dict(),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "run.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    records = []
    actions = []
    history = []
    state = {}
    script_error = None
    final_body = ""
    started_clock = time.perf_counter()
    with LocalServer(fixture) as server, sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.goto(server.url + initial_path(task))
            adapter = BrowserAdapter(page, server.url)
            started = time.perf_counter()
            deadline = time.time() + timeout
            state["_execution_deadline"] = deadline
            try:
                for step in range(max_steps):
                    if time.perf_counter() - started > timeout:
                        break
                    observation = adapter.observe()
                    state["_remaining_seconds"] = max(0.0, deadline - time.time())
                    before = time.perf_counter()
                    response = decide(task=task_prompt(task, fixture_token),
                                      observation=observation, history=history,
                                      action_history=actions, state=state)
                    decision_seconds = time.perf_counter() - before
                    action = response["action"] if isinstance(response, dict) else response
                    try:
                        outcome = adapter.act(action)
                    except Exception as exc:
                        outcome = f"{type(exc).__name__}: {exc}"
                    metadata = response if isinstance(response, dict) else {}
                    record = {
                        "time": datetime.now(timezone.utc).isoformat(),
                        "url": observation["url"], "step": step,
                        "action": action, "action_type": action.split()[0],
                        "result": outcome,
                        "decision_seconds": decision_seconds,
                        "model_calls": metadata.get("model_calls"),
                        "tokens": metadata.get("tokens"),
                    }
                    records.append(record)
                    history.append({"observation": observation, "result": outcome})
                    actions.append(action)
                    if outcome == "stopped":
                        break
            except Exception as exc:
                script_error = f"{type(exc).__name__}: {exc}"
            final_body = page.inner_text("body")
        finally:
            context.close()
            browser.close()
    report = grade(fixture, task)
    model_calls = model_call_total(records)
    summary = {
        "kind": "m2_browser_local_acceptance",
        "decision_source": "external_agent",
        "official_score": False,
        "task": task,
        "passed": report["passed"],
        "script_error": script_error,
        "steps": len(records),
        "model_calls": model_calls,
        "seconds": time.perf_counter() - started_clock,
        "grade": report,
        "final_body_excerpt": final_body[:1600],
    }
    manifest.update({
        "status": "completed",
        "passed": report["passed"],
        "script_error": script_error,
        "steps": len(records),
        "model_calls": summary["model_calls"],
        "seconds": summary["seconds"],
    })
    (output_dir / "run.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "actions.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8")
    (output_dir / "result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "result.md").write_text(
        "# M2 local browser acceptance (not official)\n\n" +
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(output_dir)
    return 0 if report["passed"] and script_error is None else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=["scripted"])
    parser.add_argument("--agent", help="module:function with decide() signature")
    parser.add_argument("--task", choices=TASK_NAMES)
    parser.add_argument("--fault-plan", type=Path)
    parser.add_argument("--fault-json")
    parser.add_argument("--token")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--max-steps", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    if args.agent:
        if not args.task:
            parser.error("--agent requires --task")
        raise SystemExit(run_agent(
            args.out, args.task, args.agent, args.fault_plan, args.fault_json,
            args.token, args.headed, args.max_steps, args.timeout))
    raise SystemExit(run_suite(args.out, args.headed))


if __name__ == "__main__":
    main()
