"""Controlled localhost webpage probes; no model or platform calls."""
from pathlib import Path
import json, sys, time, threading
from flask import Flask, request
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root / '02_代码/02_本地测试环境'), str(root / '02_代码/01_harness/当前版本')]
from local_official_adapter import OfficialProtocolAdapter
from web_agent.adapters.official import frame_from_request
from web_agent import recover, verify
from web_agent.runtime import Runtime
from web_agent.state import TaskState

out = root / '01_文本/05_测试结果/local/m2-takeover-edge-20261030-r2'
app = Flask(__name__)
business = {'toggles': 0}
@app.route('/')
def index():
    return '''<h1>Profile</h1><form method="get" action="/">
    <label>Search<input name="q" type="search"></label></form>
    <label>Biography<input value="Old bio"></label><button>Save</button>
    <label>Subscribe<input type="checkbox" onchange="fetch('/toggle',{method:'POST'})"></label>'''
@app.route('/toggle', methods=['POST'])
def toggle():
    business['toggles'] += 1
    return 'saved'

server = make_server('127.0.0.1', 0, app, threaded=True)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
url = f'http://127.0.0.1:{server.server_port}'
def current(adapter, step=0):
    obs = adapter.observe()
    return frame_from_request({'run_id':'probes', 'task':'Change my bio to "New bio"',
        'step':step, 'observation':obs, 'execution_deadline':time.time()+300}, step=step)
report = {}
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        page.goto(url)
        adapter = OfficialProtocolAdapter(page, url)
        f = current(adapter)
        view = verify.parse_ax(f)
        ids = {a.name:a.element_id for a in view.atoms}
        state = TaskState({})
        action = f'type [{ids["Search"]}] [query] [1]'
        Runtime(decision_port=lambda c,s:action).advance(f,state)
        adapter.act(action)
        report['read_only_search'] = {'url_after':page.url,
            'incorrect_pending':state.pending_for(0) is not None,
            'classification':recover.classify_action(action,f).summary}

        page.goto(url)
        f = current(adapter)
        view = verify.parse_ax(f)
        ids = {a.name:a.element_id for a in view.atoms}
        state = TaskState({})
        verify.ensure_goals(f,state)
        recover.register_action(f,state,f'click [{ids["Save"]}]')
        action = f'click [{ids["Subscribe"]}]'
        allowed = recover.guard_action(f,state,action)
        with page.expect_response('**/toggle'):
            adapter.act(action)
        report['autosave_checkbox'] = {'unknown_write_pending':state.pending_for(0) is not None,
            'allowed':True,'classified_draft':allowed.is_draft,
            'actual_business_writes':business['toggles']}

        page.goto(url)
        f = current(adapter)
        view = verify.parse_ax(f)
        bio = next(a for a in view.atoms if a.name=='Biography' and a.role=='textbox')
        adapter.act(f'type [{bio.element_id}] [New bio] [0]')
        via_adapter = page.get_by_role('textbox',name='Biography').input_value()
        page.get_by_role('textbox',name='Biography').fill('Old bio')
        page.get_by_role('textbox',name='Biography').press('End')
        page.get_by_role('textbox',name='Biography').press_sequentially('New bio')
        report['input_semantics_gap'] = {'adapter_type_value':via_adapter,
            'browser_append_value':page.get_by_role('textbox',name='Biography').input_value()}
        page.screenshot(path=str(out/'probe-page.png'))
        browser.close()
finally:
    server.shutdown()
    server.server_close()
(out/'web-probes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
