"""JSON-line child process that runs the real harness Runtime.

The local Playwright environment starts this script with the pinned EffGen
interpreter.  The parent owns the browser and fixture; this process owns only
``Runtime``/``TaskState`` and the deterministic local policy.  No fixture,
fault-plan or grading object crosses the process boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback

LOCAL = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonable(value):
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return jsonable(value.as_dict())
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class RuntimeRecorder:
    """Minimal telemetry sink so Runtime state events can be archived."""

    def __init__(self):
        self.events: list[dict] = []

    def _append(self, kind: str, fields: dict) -> dict:
        event = {"kind": kind, **jsonable(fields)}
        self.events.append(event)
        return event

    def goal_plan(self, *, task, source, goals):
        return self._append(
            "goal_plan",
            {
                "task": task,
                "source": source,
                "goal_count": len(goals),
                "goals": list(goals),
            },
        )

    def pending(self, *, step, url, action, pending, expected):
        return self._append(
            "pending_action",
            {
                "step": step,
                "url": url,
                "action": action,
                "pending": pending,
                "expected": expected,
            },
        )

    def verification(
        self,
        *,
        step,
        url,
        observation_version,
        mode,
        source,
        status,
        pending_id=None,
        goal_ids=None,
        checks=None,
        invalid=None,
        deadline=None,
    ):
        return self._append(
            "verification",
            {
                "step": step,
                "url": url,
                "observation_version": observation_version,
                "mode": mode,
                "source": source,
                "status": status,
                "pending_id": pending_id,
                "goal_ids": list(goal_ids or ()),
                "checks": list(checks or ()),
                "invalid": list(invalid or ()),
                "deadline": deadline,
            },
        )

    def write_guard(self, *, step, url, action, pending_id, allowed, reason):
        return self._append(
            "write_guard",
            {
                "step": step,
                "url": url,
                "action": action,
                "pending_id": pending_id,
                "allowed": allowed,
                "reason": reason,
            },
        )

    def recovery(self, *, step, pending_id, from_status, to_status, goal_ids, preserved_prefix, detail):
        return self._append(
            "recovery",
            {
                "step": step,
                "pending_id": pending_id,
                "from_status": from_status,
                "to_status": to_status,
                "goal_ids": list(goal_ids or ()),
                "preserved_prefix": preserved_prefix,
                "detail": detail,
            },
        )

    def progress(self, *, step, url, goals, source):
        return self._append(
            "progress",
            {
                "step": step,
                "url": url,
                "source": source,
                "goals": list(goals),
            },
        )

    def drain(self) -> list[dict]:
        events, self.events = self.events, []
        return events


def snapshot(state: TaskState) -> dict:
    goals = state.goal_checks
    progress = {
        "total": len(goals),
        "verified": sum(1 for goal in goals if goal.status == "verified"),
        "failed": sum(1 for goal in goals if goal.status == "failed"),
        "unknown": sum(1 for goal in goals if goal.status == "unknown"),
        "stale": sum(1 for goal in goals if goal.status == "stale"),
        "pending": sum(1 for goal in goals if goal.status == "pending"),
    }
    return jsonable(
        {
            "task": state.task,
            "goals": [goal.as_dict() for goal in goals],
            "pending": [item.as_dict() for item in state.pending_actions()],
            "drafts": state.drafts,
            "memory": state.memory,
            "identity": state.identity,
            "identity_changes": state.data.get("_identity_changes", []),
            "deadline": state.deadline,
            "remaining_seconds": state.remaining_seconds,
            "recovery_count": state.recovery_count,
            "progress": progress,
        }
    )


def respond(payload: dict) -> None:
    sys.stdout.write(json.dumps(jsonable(payload), ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness-dir", type=Path, required=True)
    parser.add_argument(
        "--policy",
        choices=[
            "scripted",
            "scripted_premature_stop",
            "scripted_guard_probe",
        ],
        default="scripted",
    )
    args = parser.parse_args()

    harness = args.harness_dir.resolve()
    sys.path.insert(0, str(harness))
    sys.path.insert(0, str(LOCAL))

    from web_agent.adapters.official import frame_from_request
    from web_agent.runtime import Runtime
    from web_agent.state import TaskState

    import m2_runtime_policy

    policy = m2_runtime_policy.ScriptedPolicy(
        premature_stop=args.policy == "scripted_premature_stop",
        guard_probe=args.policy == "scripted_guard_probe",
    )
    recorder = RuntimeRecorder()
    runtime = Runtime(policy=policy, telemetry=recorder)
    state = TaskState({})

    try:
        import effgen

        effgen_version = getattr(effgen, "__version__", None)
    except Exception:
        effgen_version = None
    version_file = harness / "version.json"
    try:
        version = json.loads(version_file.read_text(encoding="utf-8"))
    except Exception:
        version = None
    runtime_file = Path(sys.modules["web_agent.runtime"].__file__).resolve()
    verify_file = Path(sys.modules["web_agent.verify"].__file__).resolve()

    respond(
        {
            "ok": True,
            "hello": {
                "python": sys.version.split()[0],
                "executable": sys.executable,
                "effgen": effgen_version,
                "harness_dir": str(harness),
                "harness_version": version,
                "runtime_file": str(runtime_file),
                "runtime_sha256": sha256(runtime_file),
                "verify_file": str(verify_file),
                "verify_sha256": sha256(verify_file),
                "policy": "scripted_policy",
                "model_calls": 0,
            },
        }
    )

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except ValueError:
            respond({"ok": False, "error": {"type": "ProtocolError", "message": "invalid JSON"}})
            continue
        command = request.get("cmd")
        if command == "close":
            try:
                runtime.close()
            except Exception:
                pass
            respond({"ok": True, "closed": True})
            break
        if command == "snapshot":
            respond({"ok": True, "state": snapshot(state), "events": recorder.drain()})
            continue
        if command != "advance":
            respond({"ok": False, "error": {"type": "ProtocolError", "message": command}})
            continue
        payload = request.get("frame") or {}
        try:
            frame = frame_from_request(payload, step=int(payload.get("step", 0)))
            decision = runtime.advance(frame, state)
            respond(
                {
                    "ok": True,
                    "action": decision["action"],
                    "state": snapshot(state),
                    "events": recorder.drain(),
                    "policy_events": policy.drain_events(),
                }
            )
        except Exception as exc:
            policy.note_runtime_error(exc)
            respond(
                {
                    "ok": False,
                    "action": None,
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc)[:2000],
                        "traceback": traceback.format_exc(limit=6)[-4000:],
                    },
                    "state": snapshot(state),
                    "events": recorder.drain(),
                    "policy_events": policy.drain_events(),
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
