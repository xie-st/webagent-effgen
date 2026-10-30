"""Screenshot boundary regressions: metadata, binding, cache, failures, deadline."""
from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import struct
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from third_party_agent import browser as sdk_browser
from third_party_agent import model as sdk_model

import agent_logic
from my_agent import MyAgent
from web_agent.adapters import official
from web_agent.contracts import Capabilities, ScreenshotReference
from web_agent.model_port import SdkModelPort
from web_agent.policy import EffGenPolicy
from web_agent.runtime import Runtime
from web_agent.screenshots import ScreenshotPort
from web_agent.state import TaskState
from web_agent.telemetry import Telemetry

URL = "http://127.0.0.1:9876/forum"
TEXT = "Tab 0 (current): forum\n[17] button Save\n[18] textbox Name"
IMAGE_ID = "a" * 32


def png_bytes(width=32, height=16) -> bytes:
    """Enough of a PNG for the SDK's signature/IHDR and metadata checks."""
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x02\x00\x00\x00"
        + b"\x00" * 8
    )


def metadata(raw: bytes | None = None, *, width=32, height=16, step=3, **overrides):
    raw = raw if raw is not None else png_bytes(width, height)
    value = {
        "image_id": IMAGE_ID,
        "mime_type": "image/png",
        "width": width,
        "height": height,
        "step": step,
        "byte_size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    value.update(overrides)
    return value


def make_frame(
    *,
    screenshot=None,
    run_id="run-a",
    tab=0,
    observation_version=2,
    url=URL,
    step=3,
    deadline=None,
):
    observation = {"type": "accessibility_tree", "url": url, "text": TEXT, "tab": tab}
    if screenshot is not None:
        observation["screenshot"] = screenshot
    return official.frame_from_request(
        {
            "run_id": run_id,
            "task": "Save profile",
            "observation": observation,
            "step": step,
            "observation_version": observation_version,
            "execution_deadline": deadline if deadline is not None else time.time() + 30,
        },
        step=step,
    )


class FakeBrowser:
    def __init__(self, *, raw=None, error=None, clock=None, advance_after_save=None):
        self.raw = raw
        self.error = error
        self.clock = clock
        self.advance_after_save = advance_after_save
        self.calls = []
        self.thread_ids = []

    def save_screenshot(self, observation, directory):
        self.calls.append((dict(observation), str(directory)))
        self.thread_ids.append(threading.get_ident())
        if self.error is not None:
            raise self.error
        if self.clock is not None and self.advance_after_save is not None:
            self.clock.now += self.advance_after_save
        image = observation["screenshot"]
        path = Path(directory) / (image["image_id"] + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            self.raw if self.raw is not None else png_bytes(
                image["width"], image["height"]
            )
        )
        return path


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now


class FakeSdk:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        text = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        return SimpleNamespace(text=text, request_id="screenshot-fake")


def read_events(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


class AgentScreenshotLifecycleTests(unittest.TestCase):
    def test_stop_rejects_capture_without_appending_after_run_end(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(path=Path(temporary) / "telemetry.jsonl")
            runtime = SimpleNamespace(
                advance=lambda frame, state: {"action": "stop [done]"},
                request_screenshot=lambda *args, **kwargs: self.fail("capture after stop"),
            )
            agent = MyAgent(runtime=runtime, telemetry=telemetry)
            request = {"run_id": "stop-boundary", "task": "test",
                       "observation": {"url": URL, "text": TEXT},
                       "execution_deadline": time.time() + 30}
            agent.reset(request)
            agent.step(request)
            before = read_events(telemetry.path)
            with self.assertRaises(ValueError):
                agent.request_screenshot()
            self.assertEqual(read_events(telemetry.path), before)
            self.assertEqual(before[-1]["event"], "run_end")
            agent.close()


class SdkUpgradeTests(unittest.TestCase):
    def test_bundled_sdk_has_screenshot_api_and_exact_source_fingerprint(self):
        current = Path(official.__file__).resolve().parents[2]
        source = json.loads((current / "sdk/SOURCE.json").read_text(encoding="utf-8"))
        self.assertEqual(
            source["archive_sha256"],
            "ec1a6697656d5e1b6ba328ea4c69601a6c6e82ab9e63f428f23db71afa16feb4",
        )
        self.assertTrue(callable(sdk_browser.get_screenshot))
        self.assertTrue(callable(sdk_browser.save_screenshot))
        self.assertTrue(callable(sdk_browser.get_html))
        self.assertTrue(callable(sdk_browser.get_dom))
        for relative, expected in source["files"].items():
            actual = hashlib.sha256((current / "sdk" / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)
        self.assertIn("third_party_agent/browser.py", source["files"])

    def test_effgen_entry_stays_in_project_not_official_demo(self):
        import my_agent

        current = Path(official.__file__).resolve().parents[2]
        self.assertEqual(Path(my_agent.__file__).resolve(), current / "my_agent.py")
        entry = Path(my_agent.__file__).read_text(encoding="utf-8")
        self.assertIn("EffGenPolicy", entry)
        demo = (current / "sdk/my_agent.py").read_text(encoding="utf-8")
        self.assertIn("from agent_logic import decide", demo)
        self.assertNotIn("EffGenPolicy", demo)


class FrameMetadataTests(unittest.TestCase):
    def test_full_metadata_binds_fields_and_enables_screenshot_capability(self):
        raw = png_bytes()
        frame = make_frame(
            screenshot=metadata(raw), run_id="bound", tab=2,
            observation_version=7, url="http://127.0.0.1:9876/item/1",
        )
        reference = frame.screenshot
        self.assertIsInstance(reference, ScreenshotReference)
        self.assertEqual(reference.image_id, IMAGE_ID)
        self.assertEqual(reference.mime_type, "image/png")
        self.assertEqual((reference.width, reference.height), (32, 16))
        self.assertEqual(reference.byte_size, len(raw))
        self.assertEqual(reference.sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(reference.step, 3)
        self.assertEqual(reference.run_id, "bound")
        self.assertEqual(reference.tab, 2)
        self.assertEqual(reference.observation_version, 7)
        self.assertEqual(reference.url, "http://127.0.0.1:9876/item/1")
        self.assertEqual(frame.capabilities, Capabilities(True, False, True))

        captured = []

        def capture(context, state):
            captured.append(context)
            return {"action": "scroll [down]"}

        Runtime(capture).advance(frame, {})
        self.assertIs(captured[0].screenshot, reference)

    def test_old_observation_without_metadata_keeps_text_only_path(self):
        frame = make_frame()
        self.assertIsNone(frame.screenshot)
        self.assertEqual(frame.capabilities, Capabilities(True, False, False))
        self.assertIsNone(frame.screenshot_observation())
        captured = []

        def capture(context, state):
            captured.append(context)
            return {"action": "scroll [down]"}

        self.assertEqual(Runtime(capture).advance(frame, {}), {"action": "scroll [down]"})
        self.assertIsNone(captured[0].screenshot)

    def test_missing_or_malformed_metadata_is_ignored_not_fatal(self):
        variants = [
            metadata(sha256=None),
            metadata(mime_type="image/jpeg"),
            metadata(image_id="not-hex"),
            metadata(width=0),
            metadata(byte_size=1),
            metadata(step="3"),
        ]
        for value in variants:
            with self.subTest(metadata=value):
                frame = make_frame(screenshot=value)
                self.assertIsNone(frame.screenshot)
                self.assertFalse(frame.capabilities.screenshot)
                self.assertEqual(frame.as_observation()["text"], TEXT)
                with self.assertRaises(ValueError):
                    ScreenshotReference.from_metadata(
                        value,
                        run_id="run-a",
                        tab=0,
                        observation_version=2,
                        url=URL,
                    )

    def test_old_step_metadata_disables_current_frame_capability(self):
        frame = make_frame(screenshot=metadata(step=3), step=4)
        self.assertIsNone(frame.screenshot)
        self.assertFalse(frame.capabilities.screenshot)
        captured = []
        runtime = Runtime(lambda context, state: captured.append(context) or "scroll [down]")
        state = {"_screenshot_reference": metadata(step=3)}
        runtime.advance(frame, state)
        self.assertIsNone(captured[0].screenshot)
        self.assertFalse(captured[0].capabilities.screenshot)
        self.assertNotIn("_screenshot_reference", state)


class ScreenshotPortTests(unittest.TestCase):
    def test_cache_relocates_to_requested_result_directory_without_downloading(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "raw/screenshots"
            transient = Path(temporary) / "transient"
            fake = FakeBrowser()
            port = ScreenshotPort(browser=fake, directory=directory)
            frame = make_frame(screenshot=metadata())
            first = port.capture(frame, directory=transient)
            second = port.capture(frame)
            self.assertEqual(second.result, "cached")
            self.assertEqual(Path(second.path).parent, directory)
            self.assertEqual(Path(second.path).read_bytes(), png_bytes())
            Path(first.path).unlink()
            self.assertTrue(port.capture(frame).ok)
            self.assertEqual(len(fake.calls), 1)

    def test_corrupt_cached_file_is_not_reported_as_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            fake = FakeBrowser()
            port = ScreenshotPort(browser=fake, directory=temporary)
            frame = make_frame(screenshot=metadata())
            first = port.capture(frame)
            Path(first.path).write_bytes(b"corrupt")
            self.assertEqual(port.capture(frame).result, "invalid")
            self.assertEqual(len(fake.calls), 1)

    def test_same_frame_is_cached_and_downloaded_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="cache", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser()
            directory = Path(temporary) / "raw/screenshots"
            port = ScreenshotPort(browser=fake, directory=directory, telemetry=telemetry)
            frame = make_frame(screenshot=metadata())

            first = port.capture(frame, reason="verify")
            second = port.capture(frame, reason="verify")

            self.assertEqual(first.result, "saved")
            self.assertEqual(second.result, "cached")
            self.assertTrue(second.cached)
            self.assertEqual(first.path, second.path)
            self.assertEqual(len(fake.calls), 1)
            self.assertEqual(Path(first.path).read_bytes(), png_bytes())
            self.assertEqual(first.byte_size, len(png_bytes()))
            events = [e for e in read_events(telemetry.path) if e["event"] == "screenshot"]
            self.assertEqual([e["result"] for e in events], ["saved", "cached"])
            self.assertEqual([e["cache_hit"] for e in events], [False, True])
            self.assertEqual(events[0]["image_id"], IMAGE_ID)
            self.assertEqual(events[0]["step"], 3)
            self.assertEqual(events[0]["observation_version"], 2)
            self.assertEqual(events[0]["url"], URL)
            self.assertEqual(events[0]["byte_size"], len(png_bytes()))
            self.assertIsInstance(events[0]["duration_ms"], float)
            self.assertEqual(telemetry.summary()["screenshot_requests"], 2)
            self.assertEqual(telemetry.summary()["screenshot_cache_hits"], 1)
            self.assertEqual(telemetry.summary()["screenshot_saved"], 1)
            self.assertEqual(telemetry.summary()["screenshot_bytes"], len(png_bytes()))
            telemetry.finish("close")
            end = [e for e in read_events(telemetry.path) if e["event"] == "run_end"][-1]
            self.assertEqual(end["screenshot_requests"], 2)
            self.assertEqual(end["screenshot_cache_hits"], 1)
            self.assertEqual(end["screenshot_saved"], 1)
            self.assertEqual(end["screenshot_failed"], 0)
            self.assertEqual(end["screenshot_bytes"], len(png_bytes()))

    def test_from_env_writes_only_the_run_raw_screenshots(self):
        with tempfile.TemporaryDirectory() as temporary:
            fake = FakeBrowser()
            with patch.dict(os.environ, {"WEBAGENT_RUN_DIR": temporary}):
                port = ScreenshotPort.from_env(browser=fake)
                capture = port.capture(make_frame(screenshot=metadata()))
            self.assertEqual(capture.result, "saved")
            self.assertEqual(
                Path(capture.path).parent,
                Path(temporary).resolve() / "raw/screenshots",
            )

    def test_cross_run_tab_observation_or_url_binding_is_rejected_before_download(self):
        raw = png_bytes()
        value = metadata(raw)
        base = make_frame(screenshot=value)
        mismatches = {
            "run": replace(base, run_id="other-run"),
            "tab": replace(base, tab=9),
            "observation": replace(base, observation_version=99),
            "url": replace(base, url="http://127.0.0.1:9876/other"),
        }
        for name, frame in mismatches.items():
            with self.subTest(binding=name), tempfile.TemporaryDirectory() as temporary:
                fake = FakeBrowser(raw=raw)
                telemetry = Telemetry(run_id="bind", path=Path(temporary) / "telemetry.jsonl")
                port = ScreenshotPort(
                    browser=fake,
                    directory=Path(temporary) / "raw/screenshots",
                    telemetry=telemetry,
                )
                result = port.capture(frame)
                self.assertEqual(result.result, "binding_mismatch")
                self.assertFalse(result.ok)
                self.assertEqual(len(fake.calls), 0)
                event = [e for e in read_events(telemetry.path) if e["event"] == "screenshot"][0]
                self.assertEqual(event["result"], "binding_mismatch")
                self.assertEqual(event["cache_hit"], False)

    def test_new_step_never_reuses_old_reference_or_cache_even_with_same_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="step", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser()
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
            )
            old = make_frame(screenshot=metadata(step=3), step=3, observation_version=2)
            # A later frame can retain the same screenshot object and
            # observation version while its own step advances.
            newer = replace(old, step=4)
            self.assertIs(newer.screenshot, old.screenshot)
            self.assertEqual(newer.observation_version, old.observation_version)

            first = port.capture(old)
            second = port.capture(newer)
            self.assertEqual(first.result, "saved")
            self.assertEqual(second.result, "binding_mismatch")
            self.assertIsNone(second.path)
            self.assertEqual(len(fake.calls), 1)
            events = [e for e in read_events(telemetry.path) if e["event"] == "screenshot"]
            self.assertEqual([e["result"] for e in events], ["saved", "binding_mismatch"])
            self.assertEqual(events[1]["cache_hit"], False)
            self.assertIn("step", events[1]["error"])

            state = {}
            runtime = Runtime(
                lambda context, task_state: {"action": "scroll [down]"},
                screenshot_port=port,
            )
            self.assertTrue(runtime.request_screenshot(old, state).ok)
            self.assertIn("_screenshot_reference", state)
            runtime.advance(newer, state)
            self.assertNotIn("_screenshot_reference", state)

    def test_invalid_manual_reference_is_rejected_before_download(self):
        base = make_frame(screenshot=metadata())
        broken = replace(base, screenshot=replace(base.screenshot, width=0))
        with tempfile.TemporaryDirectory() as temporary:
            fake = FakeBrowser()
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
            )
            result = port.capture(broken)
            self.assertEqual(result.result, "invalid_metadata")
            self.assertEqual(len(fake.calls), 0)

    def test_verification_failure_is_removed_and_not_cached(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="invalid", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser(raw=b"not a png")
            directory = Path(temporary) / "raw/screenshots"
            port = ScreenshotPort(browser=fake, directory=directory, telemetry=telemetry)
            frame = make_frame(screenshot=metadata())

            first = port.capture(frame)
            second = port.capture(frame)

            self.assertEqual(first.result, "invalid")
            self.assertEqual(second.result, "invalid")
            self.assertEqual(len(fake.calls), 2)
            self.assertFalse((directory / (IMAGE_ID + ".png")).exists())
            events = [e for e in read_events(telemetry.path) if e["event"] == "screenshot"]
            self.assertEqual([e["result"] for e in events], ["invalid", "invalid"])

    def test_no_current_screenshot_does_not_reuse_previous_path_or_state_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="stale", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser()
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
            )
            with_screenshot = make_frame(screenshot=metadata(step=0), step=0)
            without = make_frame(screenshot=None, step=1)
            state = {}
            runtime = Runtime(lambda context, task_state: {"action": "scroll [down]"}, screenshot_port=port)

            first = runtime.request_screenshot(
                with_screenshot, state, reason="verify"
            )
            self.assertTrue(first.ok)
            self.assertEqual(state["_screenshot_reference"]["path"], first.path)
            runtime.advance(without, state)
            self.assertNotIn("_screenshot_reference", state)

            second = port.capture(without)
            self.assertEqual(second.result, "no_reference")
            self.assertIsNone(second.path)
            self.assertEqual(len(fake.calls), 1)

    def test_ordinary_advance_does_not_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            fake = FakeBrowser()
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
            )
            state = {}
            Runtime(lambda context, task_state: {"action": "scroll [down]"}, screenshot_port=port).advance(
                make_frame(screenshot=metadata()), state
            )
            self.assertEqual(len(fake.calls), 0)
            self.assertNotIn("_screenshot_reference", state)

    def test_explicit_advance_binds_verified_reference_to_context_and_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="request", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser()
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
            )
            frame = make_frame(screenshot=metadata())
            state = {}
            captured = []

            def decide(context, task_state):
                captured.append(context)
                return {"action": "scroll [down]"}

            Runtime(decide, screenshot_port=port).advance(
                frame, state, screenshot_reason="verify"
            )
            self.assertEqual(len(fake.calls), 1)
            self.assertIs(captured[0].screenshot, frame.screenshot)
            self.assertEqual(state["_screenshot_reference"]["image_id"], IMAGE_ID)
            self.assertTrue(state["_screenshot_reference"]["path"].endswith(IMAGE_ID + ".png"))
            self.assertEqual(
                set(state["_screenshot_reference"]),
                set(frame.screenshot.as_dict()) | {"path"},
            )

    def test_my_agent_exposes_explicit_current_frame_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="agent", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser()
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
            )
            sdk = FakeSdk(['{"action":"click [17]"}'])
            agent = MyAgent(
                model_port=SdkModelPort(sdk=sdk, telemetry=telemetry),
                telemetry=telemetry,
                screenshot_port=port,
            )
            agent.reset({"run_id": "agent", "task": "Save profile"})
            source = {
                "run_id": "agent",
                "task": "Save profile",
                "observation": {
                    "type": "accessibility_tree",
                    "url": URL,
                    "text": TEXT,
                    "screenshot": metadata(step=0),
                },
                "step": 0,
                "execution_deadline": time.time() + 30,
            }
            agent.step(source)
            self.assertEqual(len(fake.calls), 0)
            capture = agent.request_screenshot(reason="verify")
            self.assertEqual(capture.result, "saved")
            self.assertEqual(len(fake.calls), 1)
            self.assertIn("_screenshot_reference", agent.state)
            agent.close()


class FailureAndDeadlineTests(unittest.TestCase):
    def test_http_404_and_409_fall_back_to_ax_without_raising(self):
        for status in (404, 409):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                telemetry = Telemetry(run_id="http", path=Path(temporary) / "telemetry.jsonl")
                fake = FakeBrowser(
                    error=RuntimeError(
                        f"Platform screenshot request failed: HTTP {status}"
                    )
                )
                port = ScreenshotPort(
                    browser=fake,
                    directory=Path(temporary) / "raw/screenshots",
                    telemetry=telemetry,
                )
                frame = make_frame(screenshot=metadata())
                state = {}
                runtime = Runtime(
                    lambda context, task_state: {"action": "scroll [down]"},
                    screenshot_port=port,
                )
                result = runtime.advance(frame, state, screenshot_reason="verify")
                self.assertEqual(result, {"action": "scroll [down]"})
                self.assertNotIn("_screenshot_reference", state)
                event = [e for e in read_events(telemetry.path) if e["event"] == "screenshot"][0]
                self.assertEqual(event["result"], f"http_{status}")
                self.assertEqual(event["http_status"], status)
                self.assertEqual(event["cache_hit"], False)
                self.assertEqual(len(fake.calls), 1)

    def test_absolute_deadline_before_request_stops_without_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            clock = FakeClock(1000.0)
            telemetry = Telemetry(run_id="late", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser()
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
                clock=clock,
            )
            frame = make_frame(screenshot=metadata(), deadline=1005.0)
            clock.now = 1006.0
            with self.assertRaises(TimeoutError):
                port.capture(frame)
            self.assertEqual(len(fake.calls), 0)
            event = [e for e in read_events(telemetry.path) if e["event"] == "screenshot"][0]
            self.assertEqual(event["result"], "timeout")
            self.assertEqual(event["duration_ms"], 0.0)

    def test_processing_past_absolute_deadline_is_timeout_and_not_cached(self):
        with tempfile.TemporaryDirectory() as temporary:
            clock = FakeClock(1000.0)
            telemetry = Telemetry(run_id="slow", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser(clock=clock, advance_after_save=10.0)
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
                clock=clock,
            )
            frame = make_frame(screenshot=metadata(), deadline=1005.0)
            with self.assertRaisesRegex(TimeoutError, "processing"):
                port.capture(frame)
            self.assertEqual(len(fake.calls), 1)
            event = [e for e in read_events(telemetry.path) if e["event"] == "screenshot"][0]
            self.assertEqual(event["result"], "timeout")

    def test_screenshot_telemetry_counts_failed_without_touching_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="counts", path=Path(temporary) / "telemetry.jsonl")
            fake = FakeBrowser(error=RuntimeError("Platform screenshot transport failed"))
            port = ScreenshotPort(
                browser=fake,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
            )
            port.capture(make_frame(screenshot=metadata()))
            summary = telemetry.summary()
            self.assertEqual(summary["screenshot_requests"], 1)
            self.assertEqual(summary["screenshot_failed"], 1)
            self.assertEqual(summary["screenshot_cache_hits"], 0)
            self.assertEqual(summary["model_calls"], 0)


class RealSdkIntegrationTests(unittest.TestCase):
    def _server(self, raw, status=200):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                seen.append(
                    {
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                    }
                )
                if status != 200:
                    self.send_response(status)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, seen

    def test_real_sdk_browser_saves_inside_active_task_session(self):
        raw = png_bytes()
        server, thread, seen = self._server(raw)
        try:
            with tempfile.TemporaryDirectory() as temporary:
                telemetry = Telemetry(run_id="real", path=Path(temporary) / "telemetry.jsonl")
                fake = FakeBrowser()
                port = ScreenshotPort(
                    browser=sdk_browser,
                    directory=Path(temporary) / "raw/screenshots",
                    telemetry=telemetry,
                )
                frame = make_frame(
                    screenshot=metadata(raw),
                    run_id="real-run",
                    deadline=time.time() + 30,
                )
                endpoint = "http://127.0.0.1:" + str(server.server_port)
                with sdk_model.session(endpoint, "token", "job-1", "real-run", frame.deadline):
                    capture = port.capture(frame)
                self.assertEqual(capture.result, "saved")
                self.assertEqual(Path(capture.path).read_bytes(), raw)
                self.assertEqual(len(fake.calls), 0)
                self.assertEqual(len(seen), 1)
                self.assertIn("/api/client/screenshots/" + IMAGE_ID, seen[0]["path"])
                self.assertIn("job_id=job-1", seen[0]["path"])
                self.assertIn("run_id=real-run", seen[0]["path"])
                self.assertEqual(seen[0]["authorization"], "Bearer token")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_real_sdk_http_404_returns_failed_capture(self):
        server, thread, _ = self._server(b"", status=404)
        try:
            with tempfile.TemporaryDirectory() as temporary:
                telemetry = Telemetry(run_id="real404", path=Path(temporary) / "telemetry.jsonl")
                port = ScreenshotPort(
                    browser=sdk_browser,
                    directory=Path(temporary) / "raw/screenshots",
                    telemetry=telemetry,
                )
                frame = make_frame(
                    screenshot=metadata(),
                    run_id="real-404",
                    deadline=time.time() + 30,
                )
                endpoint = "http://127.0.0.1:" + str(server.server_port)
                with sdk_model.session(endpoint, "token", "job-2", "real-404", frame.deadline):
                    capture = port.capture(frame)
                self.assertEqual(capture.result, "http_404")
                self.assertEqual(capture.http_status, 404)
                self.assertFalse(capture.ok)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class ModelBoundaryTests(unittest.TestCase):
    def test_png_bytes_path_and_metadata_never_enter_model_messages(self):
        raw = png_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Telemetry(run_id="model", path=Path(temporary) / "telemetry.jsonl")
            fake_browser = FakeBrowser()
            port = ScreenshotPort(
                browser=fake_browser,
                directory=Path(temporary) / "raw/screenshots",
                telemetry=telemetry,
            )
            sdk = FakeSdk(['{"action":"click [17]"}'])
            model_port = SdkModelPort(sdk=sdk, telemetry=telemetry)
            runtime = Runtime(
                policy=EffGenPolicy(model_port=model_port, telemetry=telemetry),
                screenshot_port=port,
            )
            frame = make_frame(screenshot=metadata(raw))
            state = {}
            result = runtime.advance(frame, state, screenshot_reason="verify")
            self.assertEqual(result, {"action": "click [17]"})
            self.assertEqual(len(fake_browser.calls), 1)
            self.assertEqual(len(sdk.calls), 1)
            content = "\n".join(message["content"] for message in sdk.calls[0])
            self.assertNotIn(base64.b64encode(raw).decode(), content)
            self.assertNotIn("screenshot", content)
            self.assertNotIn("sha256", content)
            self.assertNotIn(str(Path(temporary)), content)
            self.assertTrue(all(isinstance(m["content"], str) for m in sdk.calls[0]))
            self.assertEqual([m["role"] for m in sdk.calls[0]], ["system", "user"])
            self.assertEqual(state["_screenshot_reference"]["image_id"], IMAGE_ID)
            json.dumps(state["_screenshot_reference"], ensure_ascii=False)

    def test_runtime_request_returns_disabled_without_port(self):
        frame = make_frame(screenshot=metadata())
        state = TaskState()
        capture = Runtime(lambda context, task_state: {"action": "scroll [down]"}).request_screenshot(
            frame, state, reason="verify"
        )
        self.assertEqual(capture.result, "disabled")
        self.assertIsNone(state.screenshot_reference)


if __name__ == "__main__":
    unittest.main()
