"""Read-only source/artifact/model-call audit for a frozen official run."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def audit(run):
    metadata = load(run/'run.json')
    artifacts = load(run/'platform-artifacts.json')
    for item in artifacts['files']:
        path = run/item['path']
        raw = path.read_bytes()
        assert len(raw) == item['bytes'], path
        assert hashlib.sha256(raw).hexdigest() == item['sha256'], path
    for relative, digest in metadata['harness_sha256'].items():
        path = run/'snapshot/harness'/relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
    source = load(run/'snapshot/harness/sdk/SOURCE.json')
    for relative, digest in source['files'].items():
        assert hashlib.sha256((run/'snapshot/harness/sdk'/relative).read_bytes()).hexdigest() == digest, relative
    events = [json.loads(line) for line in (run/'telemetry.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    starts = [x for x in events if x['event'] == 'model_call_start']
    ends = [x for x in events if x['event'] in ('model_call_end','model_call_failed')]
    assert Counter(x['call_id'] for x in starts) == Counter(x['call_id'] for x in ends)
    assert len({x['call_id'] for x in starts}) == len(starts)
    counts = Counter(x['run_id'] for x in starts)
    tasks = []
    for path in sorted((run/'raw/jobs').glob('*/detail.json')):
        job = load(path)['job']
        assert job['batch_id'] == artifacts['batch_id']
        rid = job['execution_run_id']
        assert counts[rid] == job['model_usage']['calls'], (rid,counts[rid],job['model_usage']['calls'])
        tasks.append({'task_id':job['task_id'],'score':job['score'],
                      'status':job['status'],'run_id':rid,'calls':counts[rid],
                      'seconds':job['execution_finished']-job['execution_started'],
                      'finish_reason':job['finish_reason']})
    report = load(run/('raw/batch-'+artifacts['batch_id']+'.json'))
    assert len(tasks) == report['total']
    assert sum(x['score'] == 1 for x in tasks) == report['passed']
    assert sum(x['calls'] for x in tasks) == len(starts) == report['model_usage']['calls']
    assert set(counts) == {x['run_id'] for x in tasks}
    screenshots = [x for x in events if x['event'] == 'screenshot']
    for event in screenshots:
        if event.get('result') not in ('saved','cached'):
            continue
        raw = Path(event['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == event['sha256']
    return {'status':'passed','batch_id':report['id'],'sdk_archive_sha256':source['archive_sha256'],
            'source_files':len(metadata['harness_sha256']),'artifact_files':len(artifacts['files']),
            'passed':report['passed'],'total':report['total'],'accuracy':report['accuracy'],
            'model_calls':len(starts),'by_purpose':dict(Counter(x['purpose'] for x in starts)),
            'screenshot_results':dict(Counter(x.get('result') for x in screenshots)),
            'tasks':tasks}


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]).resolve())
    print(json.dumps(result,ensure_ascii=True,indent=2))
