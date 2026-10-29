"""Select a complete harness version; implementation lives inside each version."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def resolve_version(config, version=None):
    version = version or config["default_harness"]
    if version != "当前版本" and not re.fullmatch(r"v[0-9]+(?:[-_][A-Za-z0-9_-]+)?", version):
        raise ValueError("Version must be 当前版本, v1 or v2_effgen")
    folder = (ROOT / config["harness_root"] / version).resolve()
    if not folder.is_relative_to(ROOT) or not (folder / "run.py").is_file():
        raise ValueError("Complete version not found: " + version)
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "test", "connect", "new-run"):
        command = commands.add_parser(name)
        command.add_argument("--version")
        command.add_argument("--connection-file", type=Path)
        command.add_argument("--results-dir", type=Path)
        if name == "new-run":
            command.add_argument("--kind", choices=("official", "local", "infrastructure"), default="official")
    copy = commands.add_parser("new-version")
    copy.add_argument("name")
    copy.add_argument("--from-version")
    args = parser.parse_args()
    config = json.loads((ROOT / "webagent.json").read_text(encoding="utf-8"))
    if args.command == "new-version":
        source = resolve_version(config, args.from_version)
        if not re.fullmatch(r"v[0-9]+(?:[-_][A-Za-z0-9_-]+)?", args.name):
            raise ValueError("Invalid new version name")
        target = source.parent / args.name
        if target.exists():
            raise ValueError("Version already exists: " + args.name)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns(
            "__pycache__", ".venv*", ".local", ".env", ".env.*", "results", "agent-connection*.json"))
        manifest = json.loads((target / "version.json").read_text(encoding="utf-8"))
        manifest.update(version=args.name, based_on=source.name)
        (target / "version.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (target / "README.md").write_text(
            "# " + args.name + "\n\n复制自 " + source.name + "，包含完整源码、SDK、启动程序和测试。\n"
            "已保存来源版本的阶段状态；日常开发继续在当前版本目录中进行。默认版本未切换。\n\n"
            "检查：`python run.py check`；测试：`python run.py test`；连接：`python run.py connect`。\n",
            encoding="utf-8")
        print(target)
        return 0
    folder = resolve_version(config, args.version)
    env = os.environ.copy()
    env["WEBAGENT_PROJECT_ROOT"] = str(ROOT)
    env["WEBAGENT_RESULTS_ROOT"] = str((args.results_dir or ROOT / config["results_root"]).resolve())
    env["WEBAGENT_CONNECTION_FILE"] = str((args.connection_file or ROOT / config["connection_file"]).resolve())
    command = [sys.executable, str(folder / "run.py"), args.command]
    if args.command == "new-run":
        command.extend(["--kind", args.kind])
    return subprocess.call(command, env=env)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error)) from None
