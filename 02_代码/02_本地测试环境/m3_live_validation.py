"""Actual API + Edge validation; controlled HTTP tasks and public read-only pages."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qs


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-env',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--public',action='store_true')
    parser.add_argument('--only-closed-loop',action='store_true')
    parser.add_argument('--multiline',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    args.out=args.out.resolve();args.out.mkdir(parents=True,exist_ok=False)
    data={'bio':'Old bio','saves':0,'published':0}
    bio_target = 'New bio\n\nEDIT: This news aged well' if args.multiline else 'New bio'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_GET(self):
            if self.path=='/a':
                time.sleep(.6);html='<h1>Record A</h1><p>The identifier is cobalt.</p>'
            elif self.path=='/b':
                time.sleep(.6);html='<h1>Record B</h1><p>The identifier is amber.</p>'
            elif self.path=='/profile':
                html='<h1>Saved biography</h1><pre>'+data['bio']+'</pre>'
            elif self.path=='/edit':
                html='<h1>Edit biography</h1><form action="/save" method="post"><label>Biography<textarea name="bio" oninput="document.querySelector(\'#preview\').textContent=this.value">Old bio</textarea></label><pre id="preview" style="min-height:600px"></pre><button>Save</button></form>'
            elif self.path=='/draft':
                html='<h1>Comment draft</h1><label>Comment<textarea oninput="fetch(\'/publish\',{method:\'POST\'})"></textarea></label><button onclick="fetch(\'/publish\',{method:\'POST\'})">Publish</button>'
            else:
                html='<h1>Dependency result</h1><p>Use the prior read_a result from memory.</p>'
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(html.encode())
        def do_POST(self):
            body=self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
            if self.path=='/save':
                data['bio']=parse_qs(body,keep_blank_values=True)['bio'][0].replace('\r\n','\n');data['saves']+=1
                self.send_response(303);self.send_header('Location','/profile');self.end_headers()
            else:
                data['published']+=1;self.send_response(200);self.end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    reads=[{'name':'read_a','url':base+'/a','task':'Read Record A and report its exact identifier in your final answer. Do not modify anything.','readonly':True,'reads':['catalog'],'scope':'catalog'},
           {'name':'read_b','url':base+'/b','task':'Read Record B and report its exact identifier in your final answer. Do not modify anything.','readonly':True,'reads':['catalog'],'scope':'catalog'}]

    def run(name,plan,workers):
        plan_path=args.out/(name+'-plan.json');plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
        output=args.out/name
        command=[sys.executable,str(root/'webagent.py'),'m3','--plan',str(plan_path),'--model-env',str(args.model_env.resolve()),'--out',str(output),'--workers',str(workers),'--timeout','240']
        started=time.perf_counter()
        with (args.out/(name+'-process.txt')).open('w',encoding='utf-8') as log:
            process=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=280)
        result_path=output/'result.json'
        result=json.loads(result_path.read_text(encoding='utf-8')) if result_path.exists() else {'status':{},'seconds':None}
        observed={};calls=0
        for item in plan:
            node_file=output/(item['name']+'.json')
            if node_file.exists():
                record=json.loads(node_file.read_text(encoding='utf-8'))
                observed[item['name']]=record['checkpoint'].get('last_action')
            telemetry=output/'raw'/(item['name']+'-telemetry.jsonl')
            if telemetry.exists():
                calls+=sum(json.loads(line).get('event')=='model_call_start' for line in telemetry.read_text(encoding='utf-8').splitlines())
        summary={'name':name,'workers':workers,'exit_code':process.returncode,'wall_seconds':round(time.perf_counter()-started,3),
                 'scheduler_seconds':result.get('seconds'),'status':result.get('status'),'answers':observed,'model_calls':calls}
        print(json.dumps(summary,ensure_ascii=False),flush=True)
        return summary

    results=[]
    try:
        combined=reads+[
            {'name':'replace','url':base+'/edit','task':'Replace the biography with exactly the text between BEGIN and END (markers excluded):\nBEGIN\n'+bio_target+'\nEND\nPreserve actual line breaks, not literal backslash sequences. Save once, then check the saved biography before stopping.','readonly':False,'writes':['profile'],'scope':'account'},
            {'name':'draft','url':base+'/draft','task':'Fill the Comment editor with exactly 感谢分享与支持 😊. Do not publish or submit. Stop when this exact draft is ready; the runner will save a screenshot and cancel it.','readonly':False,'writes':['comment-draft'],'scope':'account','draft':{'field_label':'Comment','text':'感谢分享与支持 😊'}},
            {'name':'dependent','url':base+'/dependent','task':'Use the confirmed read_a dependency result in your memory and report the identifier that read_a found. Do not browse elsewhere or modify anything.','deps':['read_a'],'readonly':True,'reads':['catalog'],'scope':'catalog'}]
        result=run('closed-loop',combined,3)
        result['business']=dict(data)
        result['checks']={
            'read_a':'cobalt' in (result['answers'].get('read_a') or '').lower(),
            'read_b':'amber' in (result['answers'].get('read_b') or '').lower(),
            'dependency':'cobalt' in (result['answers'].get('dependent') or '').lower(),
            'saved_exactly_once':data['bio']==bio_target and data['saves']==1,
            'never_published':data['published']==0,
            'draft_screenshot':(args.out/'closed-loop/raw/draft.png').is_file(),
            'all_nodes_complete':len(result['status'])==5 and all(v=='verified' for v in result['status'].values())}
        results.append(result)
        for name,workers in [('serial-first',1),('parallel-second',2),('parallel-first',2),('serial-second',1)]:
            if args.only_closed_loop:break
            result=run(name,reads,workers)
            result['checks']={'correct_answers':'cobalt' in (result['answers'].get('read_a') or '').lower() and 'amber' in (result['answers'].get('read_b') or '').lower()}
            results.append(result)
        if args.public and not args.only_closed_loop:
            plan=[{'name':'example','url':'https://example.com','task':'Read this page and report the exact main heading and current URL. Do not click links or modify anything.','readonly':True,'scope':'example'},
                  {'name':'github','url':'https://github.com/xie-st/webagent-effgen/tree/codex/m2-short-fix','task':'Inspect this repository root and identify the Python launch entry filename. Report the exact filename in your final answer. Only read this page.','readonly':True,'scope':'github'}]
            result=run('public-websites',plan,2)
            result['checks']={'example_heading':'example domain' in (result['answers'].get('example') or '').lower(),
                              'repository_entry':'webagent.py' in (result['answers'].get('github') or '')}
            results.append(result)
    finally:
        server.shutdown();server.server_close()
        (args.out/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if results and all(all(item.get('checks',{}).values()) and item['exit_code']==0 for item in results) else 1


if __name__=='__main__':
    raise SystemExit(main())
