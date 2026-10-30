"""Check actor isolation and truthful metadata through the real browser runner."""
import json
from pathlib import Path
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

import m2_acceptance as acceptance


class AcceptanceTests(unittest.TestCase):
    def test_default_output_folder_and_partial_unknown_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(acceptance, 'EVIDENCE_ROOT', Path(directory)):
                result = acceptance.new_evidence_dir('check')
                self.assertTrue(result.is_dir())
                self.assertTrue(result.name.endswith('_check'))
        self.assertIsNone(acceptance.model_call_total([{'model_calls': 2}, {}]))
        self.assertIsNone(acceptance.model_call_total([]))
        self.assertEqual(acceptance.model_call_total([{'model_calls': 2}, {'model_calls': 0}]), 2)

    def test_browser_actor_receives_no_judge_truth_and_one_fixed_deadline(self):
        seen = []
        actor = ModuleType('m2_isolation_probe')

        def decide(**request):
            self.assertEqual(set(request), {'task', 'observation', 'history', 'action_history', 'state'})
            for section in ('observation', 'state'):
                self.assertTrue({'grade', 'fault_plan', 'write_counts', 'business_state',
                                 'expected', 'requirements'}.isdisjoint(request[section]))
            seen.append(request['state']['_execution_deadline'])
            self.assertGreater(request['state']['_remaining_seconds'], 0)
            self.assertLessEqual(request['state']['_remaining_seconds'], 30)
            return ({'action': 'scroll [down]', 'model_calls': 2} if len(seen) == 1
                    else {'action': 'stop'})

        actor.decide = decide
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'run'
            with patch.dict('sys.modules', {'m2_isolation_probe': actor}):
                status = acceptance.run_agent(output, 'profile', 'm2_isolation_probe:decide',
                    fault_json='{"faults":{"profile":"commit_lost_receipt"}}',
                    timeout=30, max_steps=3)
            result = json.loads((output/'result.json').read_text(encoding='utf-8'))
        self.assertEqual(status, 1)
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0], seen[1])
        self.assertIsNone(result['model_calls'])
        self.assertIsNone(result['script_error'])
        self.assertGreater(result['seconds'], 0)
        self.assertFalse(result['passed'])


if __name__ == '__main__':
    unittest.main()
