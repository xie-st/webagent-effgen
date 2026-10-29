"""Stable workspace entry point. Uses only the Python standard library."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Workspace paths must remain inside the project")
    return path


def layout(version=None, root=ROOT):
    config = read_json(root / "webagent.json")
    version = version or config["default_harness"]
    if not re.fullmatch(r"v[0-9]+(?:[-_][A-Za-z0-9_-]+)?", version):
        raise ValueError("Version must look like v1 or v2_effgen")
    harness = inside(root, config["harness_root"] + "/" + version)
    sdk = inside(root, config["sdk_root"])
    if not (harness / "my_agent.py").is_file():
        raise ValueError("Harness version has no my_agent.py: " + version)
    if not (sdk / "third_party_agent/__main__.py").is_file():
        raise ValueError("Official SDK is missing")
    source = read_json(sdk / "SOURCE.json")
    for name, expected in source["files"].items():
        if hashlib.sha256(inside(sdk, name).read_bytes()).hexdigest() != expected:
            raise ValueError("Official SDK changed: " + name)
    return config, version, harness, sdk


def source_hashes(folder):
    return {
        f.relative_to(folder).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(folder.rglob("*"))
        if f.is_file() and "__pycache__" not in f.parts
    }


def python_env(harness, sdk):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(harness), str(sdk)))
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def git_state(root):
    def git(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    try:
        return {"commit": git("rev-parse", "HEAD"),
                "dirty": bool(git("status", "--porcelain", "--untracked-files=normal"))}
    except FileNotFoundError:
        return {"commit": None, "dirty": None}


def new_run(version=None, kind="official", root=ROOT):
    config, version, harness, sdk = layout(version, root)
    revision = git_state(root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    run_id = stamp + "_" + version + "_" + uuid4().hex[:8]
    results = inside(root, config["results_root"])
    run = results / "runs" / run_id
    run.mkdir(parents=True, exist_ok=False)
    snapshot = run / "snapshot"
    ignore = shutil.ignore_patterns("__pycache__", ".git", ".venv*", ".env*", "agent-connection*.json")
    shutil.copytree(harness, snapshot / "harness", ignore=ignore)
    shutil.copytree(sdk, snapshot / "sdk", ignore=ignore)
    shutil.copy2(root / "webagent.json", snapshot / "webagent.json")
    shutil.copy2(root / "webagent.py", snapshot / "webagent.py")
    metadata = {
        "schema_version": 1, "run_id": run_id, "kind": kind, "harness": version,
        "started_at": datetime.now(timezone.utc).isoformat(), "status": "prepared",
        "git": revision, "python": sys.version, "python_executable": sys.executable,
        "harness_sha256": source_hashes(snapshot / "harness"),
        "sdk_archive_sha256": read_json(sdk / "SOURCE.json")["archive_sha256"],
        "sdk_sha256": source_hashes(snapshot / "sdk"),
        "launcher_sha256": hashlib.sha256((root / "webagent.py").read_bytes()).hexdigest(),
        "official_score": None, "platform_run_ids": [],
    }
    write_json(run / "run.json", metadata)
    (run / "result.md").write_text(
        "# " + run_id + "\n\n状态：已创建，尚未执行或导入评测结果。\n\n"
        "测试对象与代码指纹见 run.json。官方运行编号填入 platform_run_ids；"
        "下载结果放入 raw/，通过率、耗时、调用量与结论写在本文。\n",
        encoding="utf-8")
    with (results / "index.jsonl").open("a", encoding="utf-8") as index:
        index.write(json.dumps({"run_id": run_id, "harness": version, "kind": kind,
                                "path": run.relative_to(results).as_posix()}, ensure_ascii=False) + "\n")
    write_json(results / "latest.json", {"run_id": run_id, "path": run.relative_to(results).as_posix()})
    return run, metadata


def finish_run(run, metadata, status, exit_code):
    metadata.update(status=status, exit_code=exit_code,
                    finished_at=datetime.now(timezone.utc).isoformat())
    write_json(run / "run.json", metadata)


def check(version=None):
    config, version, harness, sdk = layout(version)
    code = ("import pathlib,my_agent,agent_logic,third_party_agent; "
            "print('harness=' + str(pathlib.Path(my_agent.__file__).parent)); "
            "print('sdk=' + str(pathlib.Path(third_party_agent.__file__).parent)); "
            "assert callable(my_agent.MyAgent); assert callable(agent_logic.decide)")
    subprocess.run([sys.executable, "-c", code], cwd=harness,
                   env=python_env(harness, sdk), check=True)
    # Read only the shape, never print the server URL or token.
    connection = inside(ROOT, config["connection_file"])
    if connection.exists():
        value = read_json(connection)
        if not all(isinstance(value.get(k), str) and value[k] for k in ("server", "token")):
            raise ValueError("Connection configuration is incomplete")
    print("PASS: " + version + "; SDK hashes verified; connection=" +
          ("configured" if connection.exists() else "not configured"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "connect", "new-run", "test"):
        command = commands.add_parser(name)
        command.add_argument("--version", help="Defaults to webagent.json default_harness")
        if name == "new-run":
            command.add_argument("--kind", choices=("official", "local", "infrastructure"), default="official")
    args = parser.parse_args()
    if args.command == "check":
        check(args.version)
        return 0
    if args.command == "new-run":
        run, _ = new_run(args.version, args.kind)
        print(run)
        return 0
    if args.command == "test":
        run, metadata = new_run(args.version, "infrastructure")
        tests = run / "snapshot/tests"
        shutil.copytree(ROOT / "02_代码/04_工程工具/tests", tests,
                        ignore=shutil.ignore_patterns("__pycache__"))
        metadata["tests_sha256"] = source_hashes(tests)
        # Test the selected frozen harness and SDK, not a module cached by the caller.
        env = python_env(run / "snapshot/harness", run / "snapshot/sdk")
        env["WEBAGENT_TEST_HARNESS"] = str(run / "snapshot/harness")
        env["WEBAGENT_TEST_SDK"] = str(run / "snapshot/sdk")
        env["WEBAGENT_WORKSPACE"] = str(ROOT)
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(tests), "-v"],
                                cwd=run, env=env, capture_output=True, text=True, encoding="utf-8")
        output = result.stdout + result.stderr
        (run / "test-output.txt").write_text(output, encoding="utf-8")
        print(output, end="")
        finish_run(run, metadata, "passed" if result.returncode == 0 else "failed", result.returncode)
        (run / "result.md").write_text(
            "# 工程检查\n\n" + ("通过" if result.returncode == 0 else "失败") +
            "；具体用例见 test-output.txt。\n\n测试版本：" + metadata["harness"] +
            "。验证版本定位、导入、SDK 完整性、单步协议、状态隔离与结果快照。"
            "使用模拟模型响应，未连接平台或运行真实模型，官方成绩未填写。\n", encoding="utf-8")
        print(run)
        return result.returncode
    check(args.version)
    config = read_json(ROOT / "webagent.json")
    if not inside(ROOT, config["connection_file"]).is_file():
        raise ValueError("Place your connection file at " + config["connection_file"])
    run, metadata = new_run(args.version, "official")
    metadata["status"] = "client_running"
    write_json(run / "run.json", metadata)
    print("Session results: " + str(run), flush=True)
    status, exit_code = "client_failed", 1
    try:
        exit_code = subprocess.call(
            [sys.executable, "-m", "third_party_agent", "connect", "--connection-file",
             str(inside(ROOT, config["connection_file"])), "--agent", "my_agent:MyAgent"],
            cwd=run / "snapshot/harness",
            env=python_env(run / "snapshot/harness", run / "snapshot/sdk"))
        status = "client_closed" if exit_code == 0 else "client_failed"
    except KeyboardInterrupt:
        status, exit_code = "client_interrupted", 130
    finally:
        finish_run(run, metadata, status, exit_code)
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error)) from None
