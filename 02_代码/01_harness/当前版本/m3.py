"""Run a browser DAG with a user-configured, contest-approved Runtime factory."""
import argparse
import importlib
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "sdk"))
from web_agent.adapters.browser import BrowserSession, DraftSpec, SiteLimiter, Interrupted, create_context
from web_agent.scheduler import Node, NodeResult, Scheduler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--runtime-factory", default="web_agent.http_model:make_runtime", help="module:function returning Runtime")
    parser.add_argument("--model-env", type=Path, help="local API .env; never committed")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--channel", default="msedge")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--storage-state", type=Path, help="user-provided login state; keep in .local")
    parser.add_argument("--control-file", type=Path, help='local JSON {"pause":true/false}')
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.model_env is not None:
        os.environ['WEBAGENT_MODEL_ENV']=str(args.model_env.resolve())
    os.environ['WEBAGENT_M3_OUT']=str(args.out.resolve())
    module, function = args.runtime_factory.split(":", 1)
    factory = getattr(importlib.import_module(module), function)
    specs = json.loads(args.plan.read_text(encoding="utf-8"))
    if not isinstance(specs,list) or not specs or not all(isinstance(spec,dict) for spec in specs):
        raise ValueError('Plan must be a nonempty array of task objects')
    if args.timeout<=0:
        raise ValueError('Task timeout must be positive')
    args.out.mkdir(parents=True, exist_ok=False)
    sources={str(path.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
             for path in ROOT.rglob('*.py') if '__pycache__' not in path.parts and 'results' not in path.parts}
    for name in ('requirements.lock','requirements-browser.txt','sdk/SOURCE.json'):
        source=ROOT/name
        if source.exists():sources[name]=hashlib.sha256(source.read_bytes()).hexdigest()
    (args.out/'source-manifest.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    deadline, limiter = time.time() + args.timeout, SiteLimiter()

    def pause_requested():
        if args.control_file is None:
            return False
        try:
            return bool(json.loads(args.control_file.read_text(encoding="utf-8"))["pause"])
        except (OSError, ValueError, KeyError):
            # A missing initial file is allowed; malformed updates pause rather
            # than silently resume active browser work.
            return args.control_file.exists()

    def execute(spec, context):
        from playwright.sync_api import sync_playwright
        runtime = factory(spec, context)
        stopped = threading.Event()
        watcher = None
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=args.channel, headless=not args.headed)
            phase='initial_navigation'
            try:
                browser_context = create_context(browser,
                    **({"storage_state": str(args.storage_state)} if args.storage_state else {})
                )
                draft = None
                if "draft" in spec:
                    draft = DraftSpec(spec["draft"]["field_label"], spec["draft"]["text"],
                                      str(args.out / "raw" / (spec["name"] + ".png")))
                session = BrowserSession(browser_context.new_page(), runtime,
                    task=spec["task"], url=spec["url"], deadline=context.deadline,
                    tab=spec["name"], limiter=limiter, cancelled=context.cancelled, draft=draft,
                    readonly=spec.get("readonly", False),read_post_urls=spec.get('read_post_urls',()))

                def controller():
                    previous = False
                    while not stopped.wait(0.1):
                        pause = pause_requested()
                        if pause and not previous:
                            checkpoint = session.pause()
                            (args.out / (spec["name"] + "-checkpoint.json")).write_text(
                                json.dumps(checkpoint, ensure_ascii=False), encoding="utf-8")
                        elif previous and not pause:
                            session.resume()
                        previous = pause
                watcher = threading.Thread(target=controller, daemon=True) if args.control_file else None
                if watcher:
                    watcher.start()
                while True:
                    phase='browser_step'
                    context.check()
                    try:
                        result = session.step()
                    except Interrupted:
                        context.check()
                        time.sleep(0.05)
                        continue
                    if result.stopped:
                        record = {"checkpoint": session.checkpoint(), "events": session.events,
                                  "complete": result.complete}
                        (args.out / (spec["name"] + ".json")).write_text(
                            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                        return NodeResult(record["checkpoint"], result.complete)
            except Exception as exc:
                raw=args.out/'raw';raw.mkdir(exist_ok=True)
                (raw/(spec['name']+'-error.json')).write_text(json.dumps({'type':type(exc).__name__,'phase':phase,'detail':str(exc)},ensure_ascii=False),encoding='utf-8')
                raise
            finally:
                stopped.set()
                if watcher is not None:
                    watcher.join(timeout=1)
                try:
                    if "session" in locals():
                        try:
                            session.close()
                        finally:
                            (args.out / (spec["name"] + "-checkpoint.json")).write_text(
                                json.dumps(session.checkpoint(), ensure_ascii=False), encoding="utf-8")
                finally:
                    try:
                        browser.close()
                    finally:
                        runtime.close()
                        if getattr(runtime,'_telemetry',None) is not None:
                            runtime._telemetry.finish('close')

    nodes = []
    for spec in specs:
        name = spec["name"]
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in name):
            raise ValueError("Node names must be safe filenames")
        nodes.append(Node(name, lambda context, spec=spec: execute(spec, context),
                          tuple(spec.get("deps", ())), tuple(spec.get("reads", ())),
                          tuple(spec.get("writes", ())), spec.get("readonly", False),
                          spec.get("scope", "default-account")))
    started = time.perf_counter()
    result = Scheduler(nodes, workers=args.workers, pause_requested=pause_requested).run(deadline=deadline)
    result.update(seconds=time.perf_counter() - started, model_entry=args.runtime_factory,
                  official_score=False, plan=str(args.plan))
    (args.out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "seconds": result["seconds"]}, ensure_ascii=False))
    return 0 if all(v == "verified" for v in result["status"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
