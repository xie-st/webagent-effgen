"""Run the existing local bridge with installed Chromium-based Microsoft Edge."""
from pathlib import Path
import runpy
import sys
from playwright.sync_api import BrowserType

project = Path(__file__).resolve().parents[1]
local = project / '02_代码/02_本地测试环境'
original_launch = BrowserType.launch

def launch_edge(self, *args, **kwargs):
    kwargs['channel'] = 'msedge'
    return original_launch(self, *args, **kwargs)

BrowserType.launch = launch_edge
sys.path.insert(0, str(local))
sys.argv = [str(local / 'm2_runtime_bridge.py'),
            '--runtime-python', str(project / '.local/browser-test-venv/Scripts/python.exe'),
            '--harness-ref', 'f1eb8bc',
            '--out', str(project / '01_文本/05_测试结果/local/m2-takeover-edge-20261030-r2')]
runpy.run_path(str(local / 'm2_runtime_bridge.py'), run_name='__main__')
