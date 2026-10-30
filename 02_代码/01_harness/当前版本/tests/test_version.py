"""Offline protocol and workspace regressions; no real model or platform calls."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch

import agent_logic
from my_agent import MyAgent
from third_party_agent.session import AgentProcess

ROOT = Path(os.environ["WEBAGENT_TEST_VERSION"])
spec = importlib.util.spec_from_file_location("workspace", ROOT / "run.py")
workspace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace)
OBS = {"type": "accessibility_tree", "url": "http://127.0.0.1:9876/forum",
       "text": "Tab 0 (current): forum\n[17] button Save\n[18] textbox Name"}


class ProtocolTests(unittest.TestCase):
    def request(self, run_id="one"):
        return {"run_id": run_id, "task": "Save profile", "observation": OBS,
                "execution_deadline": time.time() + 10}

    def test_current_ids_and_type_syntax(self):
        self.assertEqual(agent_logic.validate_action("type [18] [New name] [0]", OBS),
                         "type [18] [New name] [0]")
        with self.assertRaises(ValueError):
            agent_logic.validate_action("click [999]", OBS)

    def test_unsupported_tabs_and_cross_origin_are_rejected(self):
        for action in ("tab_focus [0]", "goto [https://example.com]", "click"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                agent_logic.validate_action(action, OBS)

    def test_one_action_and_task_memory(self):
        agent = MyAgent()
        agent.reset({"run_id": "one"})
        reply = SimpleNamespace(text=json.dumps({"action": "click [17]", "memory": "Name entered"}))
        with patch.object(agent_logic.model, "generate", return_value=reply) as model:
            self.assertEqual(agent.step(self.request()), {"action": "click [17]"})
            self.assertEqual(agent.state["memory"], "Name entered")
            self.assertEqual(model.call_count, 1)
        agent.reset({"run_id": "two"})
        self.assertEqual(agent.state, {})
        with self.assertRaises(ValueError):
            agent.step(self.request())
        agent.close()

    def test_bad_output_is_corrected_before_action(self):
        agent = MyAgent()
        agent.reset({"run_id": "one"})
        replies = [SimpleNamespace(text='{"action":"click [999]"}'),
                   SimpleNamespace(text='{"action":"click [17]"}')]
        with patch.object(agent_logic.model, "generate", side_effect=replies) as model:
            self.assertEqual(agent.step(self.request()), {"action": "click [17]"})
            self.assertEqual(model.call_count, 2)
        agent.close()

    def test_sdk_spawn_model_binding_and_close(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                data = json.dumps({"text": '{"action":"click [17]"}',
                                   "request_id": "offline-test"}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        process = None
        with tempfile.TemporaryDirectory() as log_directory, patch.dict(
            os.environ, {"WEBAGENT_RUN_DIR": log_directory}
        ):
            try:
                process = AgentProcess(MyAgent, "http://127.0.0.1:" + str(server.server_port),
                                       "offline-test-token", "test-job")
                process.reset({"run_id": "one", "execution_deadline": time.time() + 10})
                self.assertEqual(process.step(self.request()), {"action": "click [17]"})
                self.assertEqual(requests[0]["run_id"], "one")
                self.assertEqual(requests[0]["job_id"], "test-job")
                self.assertIn("messages", requests[0])
                self.assertNotIn("model", requests[0])
                self.assertNotIn("temperature", requests[0])
                self.assertNotIn("api_key", requests[0])
                self.assertEqual([m["role"] for m in requests[0]["messages"]],
                                 ["system", "user"])
                self.assertTrue(all(isinstance(m["content"], str)
                                    for m in requests[0]["messages"]))
            finally:
                if process is not None:
                    process.close()
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
            records = [
                json.loads(line)
                for line in (Path(log_directory) / "telemetry.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
        self.assertFalse(process.process.is_alive())
        calls = [record for record in records if record["event"] == "model_call_start"]
        ends = [record for record in records if record["event"] == "model_call_end"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(ends), 1)
        self.assertLess(records.index(calls[0]), records.index(ends[0]))
        self.assertEqual(calls[0]["request_id"], None)
        self.assertEqual(ends[0]["request_id"], "offline-test")
        self.assertEqual(calls[0]["purpose"], "decision")
        self.assertEqual(calls[0]["step"], 0)
        self.assertEqual(calls[0]["run_id"], "one")
        end = [record for record in records if record["event"] == "run_end"][-1]
        self.assertEqual(end["model_calls"], 1)
        self.assertEqual(end["end_reason"], "close")


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT, self.root, dirs_exist_ok=True)
        config = workspace.read_json(self.root / "version.json")
        config["version"] = "v1"
        workspace.write_json(self.root / "version.json", config)
        self.env_patch = patch.dict(os.environ, {}, clear=False)
        self.env_patch.start()
        os.environ.pop("WEBAGENT_RESULTS_ROOT", None)

    def tearDown(self):
        self.env_patch.stop()
        self.temporary.cleanup()

    def test_defaults_and_path_escape(self):
        self.assertEqual(workspace.layout(root=self.root)[1], "v1")
        with self.assertRaises(ValueError):
            workspace.inside(self.root, "../outside")

    def test_official_sdk_tampering_is_detected(self):
        (self.root / "sdk/my_agent.py").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Official SDK changed"):
            workspace.layout(root=self.root)

    def test_snapshots_survive_version_changes(self):
        first, metadata = workspace.new_run(root=self.root)
        self.assertTrue((first / "raw").is_dir())
        original = (first / "snapshot/harness/agent_logic.py").read_bytes()
        (self.root / "agent_logic.py").write_text("changed", encoding="utf-8")
        config = workspace.read_json(self.root / "version.json")
        config["version"] = "v2"
        workspace.write_json(self.root / "version.json", config)
        second, _ = workspace.new_run(root=self.root)
        self.assertNotEqual(first, second)
        self.assertEqual(metadata["harness"], "v1")
        self.assertIn("third_party_agent/model.py", metadata["sdk_sha256"])
        self.assertTrue((first / "snapshot/harness/run.py").is_file())
        self.assertEqual((first / "snapshot/harness/agent_logic.py").read_bytes(), original)
        self.assertEqual(workspace.read_json(self.root / "results/latest.json")["run_id"], second.name)
        index = (self.root / "results/index.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(index), 2)
        self.assertEqual(workspace.read_json(first / "run.json")["status"], "prepared")

    def test_independent_copy_runs_environment_check(self):
        """A copied version starts with only its own files plus installed deps."""
        env = os.environ.copy()
        env.pop("WEBAGENT_PROJECT_ROOT", None)
        env.pop("WEBAGENT_CONNECTION_FILE", None)
        env.pop("WEBAGENT_RUN_DIR", None)
        result = subprocess.run(
            [sys.executable, str(self.root / "run.py"), "check"],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: environment", result.stdout)
        self.assertIn("effgen=1.3.0", result.stdout)
        self.assertIn("PASS: v1", result.stdout)


if __name__ == "__main__":
    unittest.main()
