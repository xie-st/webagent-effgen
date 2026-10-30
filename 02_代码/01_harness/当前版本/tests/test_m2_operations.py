"""Operation-level regressions; no task-ID rules or model verdict stubs."""
import json
import time
import unittest
from types import SimpleNamespace

from web_agent import operations
from web_agent.ax import AXTree
from web_agent.contracts import Capabilities, Frame
from web_agent.runtime import Runtime
from web_agent.state import TaskState


def frame(text, step=0, url='https://example.test/post/1'):
    return Frame(task='Use the page', run_id='unit', step=step, url=url, tab=0,
                 observation_version=step, ax=text, deadline=time.time()+100,
                 capabilities=Capabilities(single_tab=True,native_pause=False,screenshot=False))


class OperationsTests(unittest.TestCase):
    def submit(self, text='NEW'):
        state = TaskState()
        before = frame("[1] button 'Save'")
        state.set_draft('5', {'text': text, 'expected': text, 'url': before.url,
                              'role': 'textbox'})
        operations.register(operations.plan('click [1]', before, state), before, state)
        return state

    def test_exact_persistence_rejects_old_plus_new(self):
        state = self.submit()
        operations.resolve(frame("[2] StaticText 'OLDNEW'", 1), state)
        self.assertIsNotNone(state.pending_for(0))
        self.assertFalse(operations.stop_allowed(state))

    def test_exact_persistence_confirms_new(self):
        state = self.submit()
        operations.resolve(frame("[2] StaticText 'NEW'", 1), state)
        self.assertTrue(operations.stop_allowed(state))

    def test_alert_and_draft_do_not_confirm_save(self):
        for text in ("[2] alert ''\n  [3] StaticText 'NEW'",
                     "[2] textbox 'Bio'\n  [3] StaticText 'NEW'"):
            state = self.submit()
            operations.resolve(frame(text, 1), state)
            self.assertFalse(operations.stop_allowed(state))

    def test_unknown_submission_cannot_be_overwritten_by_input(self):
        state = self.submit()
        original = state.pending_for(0)
        now = frame("[2] textbox 'Other' value: ''", 1)
        planned = operations.plan('type [2] [draft] [0]', now, state)
        self.assertIsNotNone(operations.guard(planned, now, state))
        self.assertIs(state.pending_for(0), original)

    def test_unknown_submission_allows_search_without_replacing_pending(self):
        state = self.submit()
        original = state.pending_for(0)
        now = frame("[2] searchbox 'Search' value: ''", 1)
        planned = operations.plan('type [2] [query] [1]', now, state)
        self.assertIsNone(operations.guard(planned, now, state))
        operations.register(planned, now, state)
        self.assertIs(state.pending_for(0), original)

    def test_unrelated_error_does_not_release_unknown_write(self):
        state = self.submit()
        operations.resolve(frame("[3] StaticText 'Password required'", 1), state)
        self.assertIsNotNone(state.pending_for(0))

    def test_delete_redirect_is_not_success(self):
        state = TaskState()
        before = frame("[1] button 'Delete'")
        operations.register(operations.plan('click [1]', before, state), before, state)
        operations.resolve(frame("[2] heading 'Login'", 1, 'https://example.test/login'), state)
        self.assertFalse(operations.stop_allowed(state))

    def test_other_post_cannot_confirm_vote(self):
        state = TaskState()
        before = frame("[1] button 'Upvote first post'")
        operations.register(operations.plan('click [1]', before, state), before, state)
        operations.resolve(frame("[2] button 'Retract upvote other post'", 1), state)
        self.assertIsNotNone(state.pending_for(0))

    def test_applied_vote_cannot_be_undone(self):
        state = TaskState()
        before = frame("[1] button 'Upvote first post'")
        operations.register(operations.plan('click [1]', before, state), before, state)
        now = frame("[2] button 'Retract upvote first post'", 1)
        operations.resolve(now, state)
        self.assertTrue(operations.stop_allowed(state))
        self.assertIsNotNone(operations.guard(operations.plan('click [2]', now, state), now, state))

    def test_checkbox_is_write_and_readback_tracks_it(self):
        state = TaskState()
        before = frame("[1] checkbox 'Autosave' checked: false")
        planned = operations.plan('click [1]', before, state)
        self.assertTrue(planned.write)
        operations.register(planned, before, state)
        operations.resolve(frame("[4] checkbox 'Autosave' checked: true", 1), state)
        self.assertTrue(operations.stop_allowed(state))

    def test_menu_and_compose_link_are_not_commits(self):
        for text in ("[1] button 'Post options' haspopup: menu",
                     "[1] link 'Submit a post' url: https://example.test/submit"):
            self.assertFalse(operations.plan('click [1]', frame(text), TaskState()).write)

    def test_submit_with_popup_cannot_bypass_unknown_write_guard(self):
        state=self.submit()
        now=frame("[7] button 'Preview & Submit' haspopup: menu",1)
        planned=operations.plan('click [7]',now,state)
        self.assertTrue(planned.write)
        self.assertIsNotNone(operations.guard(planned,now,state))

    def test_ambiguous_field_is_not_guessed(self):
        tree = AXTree(frame("[1] textbox 'Bio' value: 'one'\n[2] textbox 'Bio' value: 'two'"))
        self.assertIsNone(tree.find_field({'role':'textbox','name':'Bio','section':''}))

    def test_replace_selection_is_consumed(self):
        state = TaskState()
        before = frame("[1] textbox 'Bio' value: 'OLD'")
        key = AXTree(before).by_id['1'].field_key
        state.arm_replace(key)
        operations.register(operations.plan('type [1] [NEW] [0]', before, state), before, state)
        self.assertFalse(state.replace_armed(key))

    def test_append_tracks_whole_expected_value(self):
        state = TaskState()
        before = frame("[1] textbox 'Bio' value: 'OLD'")
        operations.register(operations.plan('type [1] [NEW] [0]', before, state), before, state)
        self.assertEqual(state.pending_for(0).expected['value'], 'OLDNEW')

    def test_corrected_field_discards_old_id_draft(self):
        state=TaskState()
        key={'role':'textbox','name':'Bio','section':'Profile'}
        for element,text in [('1','WRONG'),('9','RIGHT')]:
            state.set_draft(element,{'url':'https://example.test/post/1','field_key':key,'text':text,'expected':text})
        self.assertEqual(len(state.drafts),1)
        self.assertEqual(next(iter(state.drafts.values()))['expected'],'RIGHT')

    def test_newline_value_is_unescaped(self):
        tree=AXTree(frame(r"[1] textbox 'Bio' value: 'OLD\nNEW'"))
        self.assertEqual(tree.control_value(tree.by_id['1']),'OLD\nNEW')

    def test_focus_change_aborts_replacement(self):
        policy=SimpleNamespace(generate=lambda *_:json.dumps({'action':'type [1] [NEW] [0]'}))
        runtime=Runtime(policy=policy)
        state=TaskState()
        runtime.advance(frame("[1] textbox 'Bio' value: 'OLD'"),state)
        result=runtime.advance(frame("[1] textbox 'Bio' value: 'OLD'\n[2] textbox 'Other' focused: true",1),state)
        self.assertIn('Incomplete',result['action'])

    def test_replacement_compiles_across_fresh_ids_without_extra_model_calls(self):
        calls = []
        def generate(context, state):
            calls.append(1)
            return json.dumps({'action':'type [1] [NEW] [0]'})
        runtime = Runtime(policy=SimpleNamespace(generate=generate))
        state = TaskState()
        self.assertEqual(runtime.advance(frame("[1] textbox 'Bio' value: 'OLD'"),state)['action'], 'click [1]')
        self.assertEqual(runtime.advance(frame("[4] textbox 'Bio' value: 'OLD'",1),state)['action'], 'press [Ctrl+A]')
        self.assertEqual(runtime.advance(frame("[9] textbox 'Bio' value: 'OLD'",2),state)['action'], 'press [Backspace]')
        self.assertEqual(runtime.advance(frame("[11] textbox 'Bio' value: ''",3),state)['action'], 'type [11] [NEW] [0]')
        self.assertEqual(len(calls),1)
        operations.resolve(frame("[13] textbox 'Bio' value: 'NEW'",4),state)
        self.assertEqual(state.last_result['status'],'changed')
        self.assertFalse(operations.stop_allowed(state))

    def test_near_deadline_exits_without_model(self):
        current=frame("[1] heading 'Page'")
        from dataclasses import replace
        current=replace(current, deadline=time.time()+2)
        result=Runtime(decision_port=lambda *_: self.fail('model should not run')).advance(current,TaskState())
        self.assertIn('Incomplete',result['action'])

    def test_append_compiles_to_end_then_type(self):
        policy=SimpleNamespace(generate=lambda *_:json.dumps({'action':'type [1] [NEW] [0]','input_mode':'append'}))
        runtime=Runtime(policy=policy)
        state=TaskState()
        self.assertEqual(runtime.advance(frame("[1] textbox 'Bio' value: 'OLD'"),state)['action'],'click [1]')
        self.assertEqual(runtime.advance(frame("[2] textbox 'Bio' value: 'OLD'",1),state)['action'],'press [Ctrl+End]')
        self.assertEqual(runtime.advance(frame("[3] textbox 'Bio' value: 'OLD'",2),state)['action'],'type [3] [NEW] [0]')
        self.assertEqual(state.pending_for(0).expected['value'],'OLDNEW')

    def test_repeating_same_append_is_blocked(self):
        state=TaskState()
        before=frame("[1] textbox 'Bio' value: 'OLD'")
        operations.register(operations.plan('type [1] [NEW] [0]',before,state),before,state)
        now=frame("[8] textbox 'Bio' value: 'OLDNEW'",1)
        operations.resolve(now,state)
        self.assertIsNotNone(operations.guard(operations.plan('type [8] [NEW] [0]',now,state),now,state))

    def test_unchanged_read_loop_terminates(self):
        runtime=Runtime(decision_port=lambda *_:'press [Tab]')
        state=TaskState()
        for step in range(4):
            result=runtime.advance(frame("[1] heading 'Page'",step),state)
        self.assertIn('Incomplete',result['action'])
