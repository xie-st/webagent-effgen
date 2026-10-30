"""Read-only M1 source, platform-original and telemetry acceptance audit."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
OFFICIAL = HERE.parent / '20261030T025026_355479Z_当前版本_66091f22'
M1A = HERE.parent / '20261030T023943_253636Z_当前版本_fb2859f2'
CURRENT = PROJECT / '02_代码/01_harness/当前版本'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def normalized(path):
    return path.read_bytes().replace(b'\r\n', b'\n')

artifacts = read(OFFICIAL / 'platform-artifacts.json')['files']
for artifact in artifacts:
    data = (OFFICIAL / artifact['path']).read_bytes()
    assert len(data) == artifact['bytes'], artifact['path']
    assert hashlib.sha256(data).hexdigest() == artifact['sha256'], artifact['path']

report = read(OFFICIAL / 'report.json')
raw = read(OFFICIAL / report['source'])
assert raw['id'] == report['batch_id']
assert raw['total'] == report['total'] == 4
assert raw['passed'] == report['passed'] == 3
assert raw['accuracy'] == report['accuracy'] == .75
assert raw['model_usage']['calls'] == report['model_usage']['calls'] == 26
events = [json.loads(line) for line in (OFFICIAL / 'telemetry.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
starts = [event for event in events if event['event'] == 'model_call_start']
ends = [event for event in events if event['event'] == 'model_call_end']
assert len(starts) == len(ends) == 26
assert Counter(event['call_id'] for event in starts) == Counter(event['call_id'] for event in ends)
assert all(count == 1 for count in Counter(event['call_id'] for event in starts).values())
assert not [event for event in events if event['event'] in ('model_call_failed', 'model_call_rejected')]
assert Counter(event['purpose'] for event in starts) == {'decision': 23, 'correction': 3}

tasks = []
for summary in report['tasks']:
    task = next(item for item in raw['tasks'] if item['task_id'] == summary['task_id'])
    detail = read(OFFICIAL / 'raw/jobs' / task['id'] / 'detail.json')['job']
    run_id = detail['execution_run_id']
    assert run_id == summary['local_run_id']
    matching = [event for event in starts if event['run_id'] == run_id]
    assert len(matching) == task['model_usage']['calls'] == summary['platform_model_calls']
    assert sorted(event['call_seq'] for event in matching) == list(range(1, len(matching) + 1))
    terminal = [event for event in events if event['event'] == 'run_end' and event['run_id'] == run_id]
    assert len(terminal) == 1 and terminal[0]['end_reason'] == 'stop'
    assert task['score'] == summary['score']
    tasks.append({'task_id': task['task_id'], 'score': task['score'], 'calls': len(matching), 'run_id_matched': True})

source_files = []
for original in (M1A / 'snapshot/harness').rglob('*'):
    if not original.is_file():
        continue
    relative = original.relative_to(M1A / 'snapshot/harness')
    if original.suffix == '.py' or relative.as_posix() in ('requirements.lock', 'requirements.txt', 'version.json'):
        assert normalized(original) == normalized(CURRENT / relative), str(relative)
        assert normalized(original) == normalized(OFFICIAL / 'snapshot/harness' / relative), str(relative)
        source_files.append(relative.as_posix())

result = {'status': 'passed', 'm1a_run': M1A.name, 'm1b_run': OFFICIAL.name,
          'platform_originals_verified': len(artifacts), 'artifact_bytes': sum(item['bytes'] for item in artifacts),
          'passed': 3, 'total': 4, 'accuracy': .75, 'model_calls': 26,
          'purposes': dict(Counter(event['purpose'] for event in starts)), 'tasks': tasks,
          'source_files_match_m1a_and_m1b': len(source_files),
          'line_ending_normalization_only': True, 'current_regression_run': HERE.name}
(HERE / 'm1-acceptance-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
