"""M2 Runtime + local Chromium fault-page integration bridge.

This runner connects the real harness ``Runtime.advance`` loop to the local
fault fixtures and a real Chromium page:

* the parent process uses ``02_代码/02_本地测试环境/.venv`` (Flask + Playwright);
* the child process uses the pinned EffGen interpreter and imports the selected
  ``--harness-dir`` Runtime; the two environments are never mixed;
* a deterministic local policy drives actual browser actions and a local
  verification stub cites the real AX.  Neither reads fixture grade, fault plan,
  write counters or business truth;
* the existing ``m2_grading.grade`` judges the actual fixture state independently.

The harness source and the local bridge sources are snapshotted and hashed in
every result directory.  This is a local synthetic integration check, not an
official score and not a model result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

from local_official_adapter import OfficialProtocolAdapter
from m2_faults import FaultPlan
from m2_grading import TASK_NAMES, grade, initial_path, task_prompt
from sandbox import Fixture, LocalServer

ROOT = Path(__file__).resolve().parent
PROJECT = Path(os.environ.get("WEBAGENT_PROJECT_ROOT", ROOT.parents[1]))
EVIDENCE_ROOT = PROJECT / "01_文本/05_测试结果/local"
DEFAULT_HARNESS = PROJECT / "02_代码/01_harness/当前版本"
DEFAULT_RUNTIME_PYTHON = PROJECT / ".local/m1a-lock-venv/Scripts/python.exe"
HOST = ROOT / "m2_runtime_host.py"

LOCAL_SNAPSHOT_FILES = (
    "m2_runtime_bridge.py",
    "m2_runtime_host.py",
    "m2_runtime_policy.py",
    "m2_ax_text.py",
    "local_official_adapter.py",
    "m2_faults.py",
    "m2_grading.py",
    "sandbox.py",
    "test_m2_runtime_bridge.py",
)

SCENARIOS = [
    {
        "name": "profile_normal",
        "task": "profile",
        "note": "normal exact replacement",
        "expect_pass": True,
    },
    {
        "name": "post_normal",
        "task": "post",
        "note": "normal post title",
        "expect_pass": True,
    },
    {
        "name": "reply_normal",
        "task": "reply",
        "note": "normal reply",
        "expect_pass": True,
    },
    {
        "name": "subscribe_normal",
        "task": "subscribe",
        "note": "normal subscription",
        "expect_pass": True,
    },
    {
        "name": "vote_normal",
        "task": "vote",
        "note": "normal single vote",
        "expect_pass": True,
    },
    {
        "name": "vote_unknown_no_resend",
        "task": "vote",
        "faults": {"vote": {"mode": "commit_lost_receipt"}},
        "note": "vote committed with lost receipt; query, never resend",
        "expect_pass": True,
    },
    {
        "name": "cart_normal",
        "task": "cart",
        "note": "normal cart add",
        "expect_pass": True,
    },
    {
        "name": "checkout_normal",
        "task": "checkout",
        "note": "normal cart plus order",
        "expect_pass": True,
    },
    {
        "name": "profile_no_effect_recovery",
        "task": "profile",
        "seed": {"bio": "旧简介"},
        "faults": {"profile": {"mode": "no_effect_success"}},
        "note": "success-looking no-op; verify, then retry once",
        "expect_pass": True,
    },
    {
        "name": "profile_append_repair",
        "task": "profile",
        "seed": {"bio": "旧简介"},
        "faults": {"profile": {"mode": "append_value"}},
        "note": "old plus target appended; exact replacement on recovery",
        "expect_pass": True,
    },
    {
        "name": "profile_unknown_no_resend",
        "task": "profile",
        "faults": {"profile": {"mode": "commit_lost_receipt"}},
        "policy": "scripted_guard_probe",
        "note": "commit with lost receipt; guard refuses a write, query, never resend",
        "expect_pass": True,
        "minimum_guard_rejections": 1,
    },
    {
        "name": "checkout_unknown_no_resend",
        "task": "checkout",
        "faults": {"checkout": {"mode": "commit_lost_receipt"}},
        "note": "order committed with lost receipt; query, never resend",
        "expect_pass": True,
    },
    {
        "name": "profile_post_partial",
        "task": "profile_post",
        "seed": {"title": "旧帖子"},
        "faults": {"post": {"mode": "no_effect_success"}},
        "note": "profile prefix preserved; post recovers locally",
        "expect_pass": True,
    },
    {
        "name": "profile_premature_stop",
        "task": "profile",
        "policy": "scripted_premature_stop",
        "note": "Runtime must reject the first premature success stop",
        "expect_pass": True,
        "minimum_stop_rejections": 1,
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    values = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        values[path.relative_to(root).as_posix()] = sha256(path)
    return values


def new_evidence_dir(label: str) -> Path:
    folder = EVIDENCE_ROOT / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ") + "_" + label
    )
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def snapshot_sources(output_dir: Path, harness: Path) -> dict:
    snap = output_dir / "snapshot"
    harness_snap = snap / "harness"
    local_snap = snap / "local"
    harness_snap.mkdir(parents=True)
    local_snap.mkdir(parents=True)

    web_agent = harness / "web_agent"
    if not (web_agent / "runtime.py").is_file():
        raise FileNotFoundError(f"harness web_agent/runtime.py not found: {web_agent}")
    shutil.copytree(
        web_agent,
        harness_snap / "web_agent",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    for name in ("version.json", "agent_logic.py", "my_agent.py"):
        source = harness / name
        if source.is_file():
            shutil.copy2(source, harness_snap / name)
    for name in LOCAL_SNAPSHOT_FILES:
        source = ROOT / name
        if source.is_file():
            shutil.copy2(source, local_snap / name)
    hashes = {
        "harness": tree_hashes(harness_snap),
        "local": tree_hashes(local_snap),
    }
    (output_dir / "hashes.json").write_text(
        json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return hashes


class RuntimeChild:
    """One JSON-line child owning Runtime/TaskState for a single scenario."""

    def __init__(self, harness: Path, policy: str, log_path: Path, python: Path):
        self.log_file = log_path.open("w", encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        self.process = subprocess.Popen(
            [
                str(python),
                "-u",
                str(HOST),
                "--harness-dir",
                str(harness),
                "--policy",
                policy,
            ],
            cwd=str(ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.log_file,
            text=True,
            encoding="utf-8",
            errors="strict",
            bufsize=1,
            env=env,
        )
        hello = self._read()
        if not hello.get("ok"):
            raise RuntimeError("Runtime child failed to start: " + json.dumps(hello))
        self.hello = hello["hello"]

    def _read(self):
        line = self.process.stdout.readline()
        if not line:
            code = self.process.poll()
            raise RuntimeError(f"Runtime child closed (exit={code}); see child_stderr.log")
        return json.loads(line)

    def send(self, request: dict) -> dict:
        self.process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        return self._read()

    def close(self):
        try:
            if self.process.poll() is None:
                self.process.stdin.write(json.dumps({"cmd": "close"}) + "\n")
                self.process.stdin.flush()
                self.process.stdout.readline()
        except Exception:
            pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        try:
            self.process.stdin.close()
            self.process.stdout.close()
        except Exception:
            pass
        self.log_file.close()


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def run_scenario(browser, spec: dict, output_dir: Path, harness: Path, args) -> dict:
    name = spec["name"]
    task = spec["task"]
    index = [item["name"] for item in SCENARIOS].index(name) + 1
    token = f"rt{index:02d}"
    plan = FaultPlan.from_dict(
        {
            "token": token,
            "seed": spec.get("seed") or {},
            "faults": spec.get("faults") or {},
        }
    )
    fixture = Fixture(token=token, fault_plan=plan)
    scenario_dir = output_dir / "scenarios" / name
    scenario_dir.mkdir(parents=True, exist_ok=True)
    actions_log: list[dict] = []
    events_log: list[dict] = []
    states_log: list[dict] = []
    history: list[dict] = []
    action_history: list[str] = []
    runtime_errors: list[dict] = []
    stop_accepted = False
    script_error = None
    ended = "max_steps"
    last_observation: dict = {}
    last_grade = None
    final_body = ""
    started = time.perf_counter()
    deadline = time.time() + args.timeout
    child = RuntimeChild(
        harness,
        spec.get("policy", "scripted"),
        scenario_dir / "child_stderr.log",
        args.runtime_python,
    )
    try:
        with LocalServer(fixture) as server:
            context = browser.new_context()
            page = None
            try:
                page = context.new_page()
                page.goto(server.url + initial_path(task))
                adapter = OfficialProtocolAdapter(page, server.url)
                for step in range(args.max_steps):
                    if time.time() > deadline:
                        ended = "timeout"
                        break
                    observation = adapter.observe()
                    last_observation = observation
                    request = {
                        "run_id": f"m2rt-{token}-{name}",
                        "task": task_prompt(task, token),
                        "step": step,
                        "observation_version": observation["version"],
                        "execution_deadline": deadline,
                        "observation": {
                            key: value
                            for key, value in observation.items()
                            if key != "version"
                        },
                        "history": history[-8:],
                        "action_history": action_history[-16:],
                        "previous_receipt": (
                            {"result": actions_log[-1]["result"], "url": actions_log[-1]["url"]}
                            if actions_log
                            else None
                        ),
                    }
                    decision_started = time.perf_counter()
                    response = child.send({"cmd": "advance", "frame": request})
                    decision_seconds = time.perf_counter() - decision_started
                    state = response.get("state") or {}
                    step_events = [
                        {"step": step, **event}
                        for event in response.get("events", [])
                    ] + [
                        {"step": step, **event}
                        for event in response.get("policy_events", [])
                    ]
                    events_log.extend(step_events)
                    states_log.append({"step": step, **state})
                    for event in step_events:
                        if event.get("kind") == "runtime_rejection":
                            runtime_errors.append(event)
                    if not response.get("ok"):
                        error = response.get("error") or {}
                        actions_log.append(
                            {
                                "step": step,
                                "time": datetime.now(timezone.utc).isoformat(),
                                "url": observation["url"],
                                "action": None,
                                "attempted_action": next(
                                    (
                                        event.get("action")
                                        for event in step_events
                                        if event.get("kind") == "policy_decision"
                                    ),
                                    None,
                                ),
                                "result": "runtime_error:" + str(error.get("type")),
                                "runtime_error": error,
                                "decision_seconds": decision_seconds,
                                "goal_progress": state.get("progress"),
                                "model_calls": 0,
                            }
                        )
                        history.append(
                            {
                                "observation": observation,
                                "action": None,
                                "result": "runtime_error",
                            }
                        )
                        continue
                    action = response["action"]
                    outcome = adapter.act(action)
                    if outcome == "stopped":
                        stop_accepted = True
                    actions_log.append(
                        {
                            "step": step,
                            "time": datetime.now(timezone.utc).isoformat(),
                            "url": observation["url"],
                            "action": action,
                            "result": outcome,
                            "decision_seconds": decision_seconds,
                            "goal_progress": state.get("progress"),
                            "pending": state.get("pending"),
                            "model_calls": 0,
                        }
                    )
                    history.append(
                        {"observation": observation, "action": action, "result": outcome}
                    )
                    action_history.append(action)
                    if outcome == "stopped":
                        ended = "stop"
                        break
                final_body = page.inner_text("body")
            except Exception as exc:
                script_error = f"{type(exc).__name__}: {exc}"
                try:
                    final_body = page.inner_text("body") if page is not None else ""
                except Exception:
                    pass
            finally:
                context.close()
    finally:
        child.close()
    last_grade = grade(fixture, task)
    seconds = time.perf_counter() - started
    minimum_rejections = int(spec.get("minimum_stop_rejections", 0))
    stop_attempts = sum(
        1
        for event in events_log
        if event.get("kind") == "policy_decision" and event.get("stop")
    )
    stop_rejections = sum(
        1
        for event in events_log
        if event.get("kind") == "runtime_rejection"
        and "Cannot stop" in str(event.get("error", ""))
    )
    guard_rejections = sum(
        1
        for event in events_log
        if event.get("kind") == "runtime_rejection"
        and (
            event.get("error_type") == "WriteGuardError"
            or "write result is unknown" in str(event.get("error", ""))
        )
    )
    minimum_guard_rejections = int(spec.get("minimum_guard_rejections", 0))
    matched = (
        script_error is None
        and ended == "stop"
        and last_grade["passed"] == spec["expect_pass"]
        and stop_rejections >= minimum_rejections
        and guard_rejections >= minimum_guard_rejections
    )
    result = {
        "kind": "m2_runtime_browser_scenario",
        "scenario": name,
        "task": task,
        "token": token,
        "note": spec["note"],
        "expected_pass": spec["expect_pass"],
        "actual_pass": last_grade["passed"],
        "matched": matched,
        "decision_source": "scripted_policy",
        "runtime": "actual_Runtime.advance",
        "browser": "Chromium via Playwright",
        "model_calls": 0,
        "official_score": False,
        "fault_plan": plan.to_dict(),
        "seed": spec.get("seed") or {},
        "steps": len(actions_log),
        "ended": ended,
        "seconds": seconds,
        "script_error": script_error,
        "stop_attempts": stop_attempts,
        "stop_rejections": stop_rejections,
        "guard_rejections": guard_rejections,
        "stop_accepted": stop_accepted,
        "expected_stop_rejections": minimum_rejections,
        "expected_guard_rejections": minimum_guard_rejections,
        "runtime_errors": runtime_errors,
        "runtime_state": states_log[-1] if states_log else None,
        "runtime_child": child.hello,
        "actor_goal_checks_advisory_only": (
            states_log[-1].get("goals") if states_log else None
        ),
        "grade": last_grade,
        "final_body_excerpt": final_body[:1200],
    }
    _write_jsonl(scenario_dir / "actions.jsonl", actions_log)
    _write_jsonl(scenario_dir / "runtime_events.jsonl", events_log)
    _write_jsonl(scenario_dir / "state.jsonl", states_log)
    (scenario_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (scenario_dir / "final_ax.txt").write_text(
        last_observation.get("text", ""), encoding="utf-8"
    )
    (scenario_dir / "final_body.txt").write_text(final_body, encoding="utf-8")
    return result


def interpreter_facts() -> dict:
    facts = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
    }
    try:
        from importlib import metadata

        facts["playwright"] = metadata.version("playwright")
        facts["flask"] = metadata.version("flask")
    except Exception:
        pass
    return facts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--harness-dir",
        type=Path,
        default=DEFAULT_HARNESS,
        help="fixed harness source directory; defaults to the current version",
    )
    parser.add_argument(
        "--runtime-python",
        type=Path,
        default=DEFAULT_RUNTIME_PYTHON,
        help="pinned EffGen interpreter used by the Runtime child",
    )
    parser.add_argument("--harness-ref", default=None, help="optional frozen git ref label")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--max-steps", type=int, default=24)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--only", nargs="*", choices=[item["name"] for item in SCENARIOS])
    args = parser.parse_args()
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    harness = args.harness_dir.resolve()
    if not (harness / "web_agent/runtime.py").is_file():
        parser.error(f"--harness-dir lacks web_agent/runtime.py: {harness}")
    if not args.runtime_python.is_file():
        parser.error(f"--runtime-python not found: {args.runtime_python}")

    if args.out is not None:
        output_dir = Path(args.out)
        output_dir.mkdir(parents=True, exist_ok=False)
    else:
        output_dir = new_evidence_dir("m2_runtime_bridge")

    hashes = snapshot_sources(output_dir, harness)
    started_at = datetime.now(timezone.utc)
    started_clock = time.perf_counter()
    scenarios = [
        spec for spec in SCENARIOS if not args.only or spec["name"] in args.only
    ]
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        try:
            for spec in scenarios:
                results.append(
                    run_scenario(browser, spec, output_dir, harness, args)
                )
                print(
                    json.dumps(
                        {
                            "scenario": results[-1]["scenario"],
                            "passed": results[-1]["actual_pass"],
                            "matched": results[-1]["matched"],
                            "stop_rejections": results[-1]["stop_rejections"],
                            "guard_rejections": results[-1]["guard_rejections"],
                        },
                        ensure_ascii=False,
                    )
                )
        finally:
            browser.close()

    all_matched = all(result["matched"] for result in results)
    runtime_hello = results[0].get("runtime_child") if results else None
    manifest = {
        "kind": "m2_runtime_browser_integration",
        "official_score": False,
        "model_calls": 0,
        "decision_source": "scripted_policy",
        "runtime": "actual_Runtime.advance",
        "browser": "Chromium via Playwright",
        "harness_dir": str(harness),
        "harness_ref": args.harness_ref,
        "harness_snapshot_hashes": {
            "runtime_sha256": hashes["harness"].get("web_agent/runtime.py"),
            "verify_sha256": hashes["harness"].get("web_agent/verify.py"),
        },
        "runtime_child": runtime_hello,
        "interpreters": {
            "browser": interpreter_facts(),
            "runtime": {
                "executable": str(args.runtime_python),
                "effgen": (
                    runtime_hello.get("effgen") if runtime_hello else "1.3.0 (pinned)"
                ),
            },
        },
        "started_at": started_at.isoformat(),
        "seconds": time.perf_counter() - started_clock,
        "all_matched": all_matched,
        "scenario_count": len(results),
        "scenarios": [result["scenario"] for result in results],
        "evidence_dir": str(output_dir),
        "command": " ".join([Path(sys.executable).name, *sys.argv]),
    }
    (output_dir / "run.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# M2 Runtime + local Chromium integration",
        "",
        "- decision source: `scripted_policy` (deterministic stub, not a model)",
        "- runtime: actual `Runtime.advance`; browser: Chromium via Playwright",
        "- model calls: 0; local synthetic result, not an official score",
        f"- harness: `{harness}`; ref: `{args.harness_ref or 'not supplied'}`",
        f"- scenarios: {len(results)}; all matched: **{all_matched}**",
        "",
        "| scenario | task | expected pass | actual pass | matched | stop rejections | guard rejections | writes |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result['scenario']} | {result['task']} | {result['expected_pass']} | "
            f"{result['actual_pass']} | {result['matched']} | {result['stop_rejections']} | "
            f"{result['guard_rejections']} | "
            f"`{json.dumps(result['grade']['write_counts'], ensure_ascii=False)}` |"
        )
    lines.extend(
        [
            "",
            "The grade is computed by `m2_grading.grade` from actual fixture state and the",
            "original task; Runtime `goal_checks` are stored as advisory only.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(output_dir)
    return 0 if all_matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
