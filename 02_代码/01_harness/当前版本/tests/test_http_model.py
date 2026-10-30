"""Local HTTP service checks; no real credentials or external model calls."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import tempfile, threading, time, unittest
from web_agent.http_model import ApiConfig,HttpModelPort
from web_agent.telemetry import Telemetry


class HttpModelTests(unittest.TestCase):
    def setUp(self):
        self.requests=[]
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.requests.append((self.path,body,self.headers.get('Authorization')))
                if self.path.startswith('/error'):
                    self.send_response(401);self.end_headers();self.wfile.write(b'fake-secret-do-not-log');return
                if self.path.startswith('/redirect'):
                    self.send_response(307);self.send_header('Location','/stolen');self.end_headers();return
                response={'id':'test-request','choices':[{'message':{'content':'READY'}}]}
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
                encoded=json.dumps(response).encode()
                if self.path.startswith('/slow'):
                    for start in range(0,len(encoded),10):
                        self.wfile.write(encoded[start:start+10]);self.wfile.flush();time.sleep(.01)
                else:self.wfile.write(encoded)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True);self.worker.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.temp=tempfile.TemporaryDirectory()
        self.log=Path(self.temp.name)/'calls.jsonl'

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.worker.join();self.temp.cleanup()

    def port(self,path=''):
        return HttpModelPort(ApiConfig(self.base+path,'test-model','fake-secret-do-not-log'),
                             telemetry=Telemetry(path=self.log))

    def test_compatible_body_and_real_call_logged_once(self):
        port=self.port('/v1')
        with port.call_scope(run_id='api',step=1,deadline=time.time()+3,purpose='decision'):
            reply=port.generate([{'role':'user','content':'ready'}],'decision',time.time()+3)
        self.assertEqual(reply.text,'READY')
        path,body,auth=self.requests[0]
        self.assertEqual(path,'/v1/chat/completions')
        self.assertEqual(body['model'],'test-model')
        self.assertEqual(auth,'Bearer fake-secret-do-not-log')
        events=[json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual([e['event'] for e in events],['model_call_start','model_call_end'])
        self.assertNotIn('fake-secret-do-not-log',self.log.read_text())

    def test_http_error_does_not_log_body_or_key(self):
        with self.assertRaisesRegex(RuntimeError,'HTTP 401'):
            self.port('/error').generate([{'role':'user','content':'ready'}],'decision',time.time()+3)
        self.assertNotIn('fake-secret-do-not-log',self.log.read_text())

    def test_redirect_does_not_forward_credentials(self):
        with self.assertRaisesRegex(RuntimeError,'HTTP 307'):
            self.port('/redirect').generate([{'role':'user','content':'ready'}],'decision',time.time()+3)
        self.assertEqual(len(self.requests),1)

    def test_expired_request_never_reaches_service(self):
        with self.assertRaises(TimeoutError):
            self.port().generate([{'role':'user','content':'ready'}],'decision',time.time()-1)
        self.assertEqual(self.requests,[])

    def test_late_complete_response_is_not_reported_as_success(self):
        with self.assertRaises(TimeoutError):
            self.port('/slow').generate([{'role':'user','content':'ready'}],'decision',time.time()+.04)
        events=[json.loads(line)['event'] for line in self.log.read_text().splitlines()]
        self.assertIn('model_call_failed',events)
        self.assertNotIn('model_call_end',events)

    def test_missing_configuration_reports_only_required_keys(self):
        path=Path(self.temp.name)/'model.env';path.write_text('BASE_URL=https://api.example.test/v1\n')
        with self.assertRaisesRegex(ValueError,'BASE_URL, MODEL'):
            ApiConfig.load(path)
