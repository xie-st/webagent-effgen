"""Explicit local-only API model port; never used by the official SDK entry."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .model_port import SdkModelPort


@dataclass(frozen=True)
class ApiConfig:
    base_url: str
    model: str
    api_key: str = field(repr=False)

    @classmethod
    def load(cls, path=None):
        values = os.environ
        if path:
            from dotenv import dotenv_values
            values = dotenv_values(path, interpolate=False)
        base = values.get('BASE_URL') or values.get('OPENAI_BASE_URL')
        model = values.get('MODEL') or values.get('OPENAI_MODEL')
        key = values.get('DASHSCOPE_API_KEY') or values.get('OPENAI_API_KEY') or values.get('API_KEY')
        if not all(isinstance(value,str) and value.strip() for value in (base,model,key)):
            raise ValueError('API configuration needs BASE_URL, MODEL and an API key; keep credentials outside Git')
        parsed=urlsplit(base)
        if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('API base must be an HTTP(S) URL without embedded credentials/query/fragment')
        return cls(base.rstrip('/'),model,key)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


class _Transport:
    def __init__(self, config):
        self.config=config
        self.scope=lambda: None
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),_NoRedirect())

    def generate(self,messages):
        scope=self.scope()
        remaining=60.0 if scope is None or scope.deadline is None else scope.deadline-time.time()
        if remaining<=0:
            raise TimeoutError('API model deadline reached')
        endpoint=self.config.base_url
        if not endpoint.endswith('/chat/completions'):
            endpoint+='/chat/completions'
        data=json.dumps({'model':self.config.model,'messages':messages,'stream':False}).encode('utf-8')
        request=urllib.request.Request(endpoint,data=data,headers={
            'Content-Type':'application/json','Authorization':'Bearer '+self.config.api_key})
        try:
            with self.opener.open(request,timeout=min(60,remaining)) as response:
                raw=response.read(4*1024*1024+1)
            if scope is not None and scope.deadline is not None and time.time()>=scope.deadline:
                raise TimeoutError('Model API deadline reached while reading response')
            if len(raw)>4*1024*1024:
                raise ValueError('API response exceeds limit')
            result=json.loads(raw)
            text=result['choices'][0]['message']['content']
            if not isinstance(text,str) or not text.strip():
                raise ValueError('API response has no text')
            return SimpleNamespace(text=text,request_id=str(result.get('id','')) or None)
        except urllib.error.HTTPError as exc:
            # Never log server bodies, request headers, config values or secrets.
            raise RuntimeError(f'Model API HTTP {exc.code}') from None
        except TimeoutError:
            raise TimeoutError('Model API timed out') from None
        except (OSError,ValueError,KeyError,IndexError,TypeError):
            raise RuntimeError('Model API transport or response format failed') from None


class HttpModelPort(SdkModelPort):
    def __init__(self,config,*,telemetry=None):
        transport=_Transport(config)
        super().__init__(sdk=transport,telemetry=telemetry)
        transport.scope=self.current_scope

    def generate(self,messages,purpose,deadline):
        scope=self.current_scope()
        effective=deadline if scope.deadline is None else (scope.deadline if deadline is None else min(deadline,scope.deadline))
        with self.call_scope(run_id=scope.run_id,step=scope.step,deadline=effective,purpose=purpose):
            return super().generate(messages,purpose,effective)


def make_runtime(spec,context):
    from .policy import EffGenPolicy
    from .runtime import Runtime
    from .telemetry import Telemetry
    config=ApiConfig.load(os.environ.get('WEBAGENT_MODEL_ENV'))
    output=os.environ.get('WEBAGENT_M3_OUT')
    telemetry=Telemetry(path=str(Path(output)/'raw'/(spec['name']+'-telemetry.jsonl')) if output else None)
    port=HttpModelPort(config,telemetry=telemetry)
    runtime=Runtime(policy=EffGenPolicy(model_port=port,telemetry=telemetry),telemetry=telemetry)
    if context.inputs:
        results={name:({key:value[key] for key in ('last_action','memory','last_readback','url') if key in value}
                       if isinstance(value,dict) and 'last_action' in value else value)
                 for name,value in context.inputs.items()}
        runtime.initial_memory=json.dumps({'dependency_results_reference_only':results},ensure_ascii=False)[:9000]
    return runtime
