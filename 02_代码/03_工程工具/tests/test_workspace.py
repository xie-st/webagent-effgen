"""Check root dispatch and complete-version copying in an isolated project."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class DispatchTests(unittest.TestCase):
    def test_copy_and_run_without_parent_project(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            project.mkdir()
            for name in ("webagent.py", "webagent.json"):
                shutil.copy2(ROOT / name, project / name)
            versions = project / "02_代码/01_harness"
            shutil.copytree(ROOT / "02_代码/01_harness/当前版本", versions / "当前版本",
                            ignore=shutil.ignore_patterns("__pycache__", "results", ".local"))
            def run(*args, cwd=project):
                return subprocess.run([sys.executable, *map(str, args)], cwd=cwd,
                                      capture_output=True, text=True, encoding="utf-8")
            result = run("webagent.py", "check")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("当前版本", result.stdout)
            source_code = (versions / "当前版本/agent_logic.py").read_bytes()
            result = run("webagent.py", "new-version", "v2")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((versions / "v2/version.json").read_text(encoding="utf-8"))["version"], "v2")
            self.assertNotEqual(run("webagent.py", "new-version", "v2").returncode, 0)
            self.assertNotEqual(run("webagent.py", "check", "--version", "../../outside").returncode, 0)
            self.assertEqual(run("webagent.py", "check", "--version", "v2").returncode, 0)
            (versions / "当前版本/agent_logic.py").write_text("changed", encoding="utf-8")
            self.assertEqual((versions / "v2/agent_logic.py").read_bytes(), source_code)
            self.assertEqual(json.loads((project / "webagent.json").read_text(encoding="utf-8"))["default_harness"], "当前版本")
            standalone = Path(temp) / "standalone"
            shutil.copytree(versions / "v2", standalone)
            shutil.rmtree(project)
            self.assertEqual(run(standalone / "run.py", "check", cwd=standalone).returncode, 0)
            result = run(standalone / "run.py", "test", cwd=standalone)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
