"""Offline protocol and workspace regressions; no real model or platform calls."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
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

ROOT = Path(os.environ["WEBAGENT_WORKSPACE"])
spec = importlib.util.spec_from_file_location("workspace", ROOT / "webagent.py")
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

    def test_bad_output_is_corrected_before_action(self):
        agent = MyAgent()
        agent.reset({"run_id": "one"})
        replies = [SimpleNamespace(text='{"action":"click [999]"}'),
                   SimpleNamespace(text='{"action":"click [17]"}')]
        with patch.object(agent_logic.model, "generate", side_effect=replies) as model:
            self.assertEqual(agent.step(self.request()), {"action": "click [17]"})
            self.assertEqual(model.call_count, 2)

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
        finally:
            if process is not None:
                process.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertFalse(process.process.is_alive())


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copy2(ROOT / "webagent.py", self.root / "webagent.py")
        shutil.copytree(os.environ["WEBAGENT_TEST_HARNESS"], self.root / "harness/v1")
        shutil.copytree(os.environ["WEBAGENT_TEST_SDK"], self.root / "sdk")
        workspace.write_json(self.root / "webagent.json", {
            "schema_version": 1, "default_harness": "v1", "harness_root": "harness",
            "sdk_root": "sdk", "results_root": "results", "connection_file": ".local/agent-connection.json"})

    def tearDown(self):
        self.temporary.cleanup()

    def test_defaults_and_path_escape(self):
        self.assertEqual(workspace.layout(root=self.root)[1], "v1")
        with self.assertRaises(ValueError):
            workspace.layout("../../outside", self.root)
        with self.assertRaises(ValueError):
            workspace.inside(self.root, "../outside")

    def test_official_sdk_tampering_is_detected(self):
        (self.root / "sdk/my_agent.py").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Official SDK changed"):
            workspace.layout(root=self.root)

    def test_snapshots_survive_version_changes(self):
        first, metadata = workspace.new_run(root=self.root)
        original = (first / "snapshot/harness/agent_logic.py").read_bytes()
        (self.root / "harness/v1/agent_logic.py").write_text("changed", encoding="utf-8")
        shutil.copytree(self.root / "harness/v1", self.root / "harness/v2")
        config = workspace.read_json(self.root / "webagent.json")
        config["default_harness"] = "v2"
        workspace.write_json(self.root / "webagent.json", config)
        second, _ = workspace.new_run(root=self.root)
        self.assertNotEqual(first, second)
        self.assertEqual(metadata["harness"], "v1")
        self.assertEqual((first / "snapshot/harness/agent_logic.py").read_bytes(), original)
        self.assertEqual(workspace.read_json(self.root / "results/latest.json")["run_id"], second.name)
        index = (self.root / "results/index.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(index), 2)
        self.assertEqual(workspace.read_json(first / "run.json")["status"], "prepared")


if __name__ == "__main__":
    unittest.main()
