"""Run with .venv-browsergym. Reads genuine BrowserGym AXTree, no LLM."""
from report_paths import new_environment_result
import json
import os
from unittest.mock import patch
from pathlib import Path
import gymnasium as gym
import browsergym.core  # registers openended


def main():
    pw = browsergym.core._get_global_playwright()
    original_launch = pw.chromium.launch
    executable = os.environ.get('WEBAGENT_CHROMIUM')
    # BrowserGym's separate chat browser does not receive pw_chromium_kwargs.
    # Override launch only for this process, keeping installed packages intact.
    override = patch.object(pw.chromium, 'launch',
        lambda **kwargs: original_launch(**{**kwargs, 'executable_path': executable})) if executable else None
    if override:
        override.start()
    env = gym.make('browsergym/openended', task_kwargs={'start_url':
        'data:text/html,<title>Local smoke</title><label>Name<input aria-label="Name"></label><button>Save</button>'},
        headless=True, pw_chromium_kwargs=(
            {'executable_path': os.environ['WEBAGENT_CHROMIUM']}
            if os.environ.get('WEBAGENT_CHROMIUM') else {}))
    try:
        observation, info = env.reset()
        assert observation['axtree_object']['nodes']
        nodes = observation['axtree_object']['nodes']
        field = next(node for node in nodes if node.get('role', {}).get('value') == 'textbox')
        bid = field['browsergym_id']
        observation, *_ = env.step(f"fill('{bid}', 'Smoke')")
        assert any(node.get('value', {}).get('value') == 'Smoke'
                   for node in observation['axtree_object']['nodes'])
        report = {'kind': 'browsergym_smoke_no_model', 'all_passed': True,
                  'observation_keys': sorted(observation.keys()),
                  'axtree_nodes': len(observation['axtree_object']['nodes']),
                  'action_verified': 'fill', 'chromium_override': executable}
        result_dir = new_environment_result()
        path = result_dir / 'browsergym_smoke.json'
        path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        (result_dir / 'run.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
        print(result_dir)
    finally:
        env.close()
        if override:
            override.stop()
        pw.stop()
        browsergym.core._set_global_playwright(None)


if __name__ == '__main__':
    main()
