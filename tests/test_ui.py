"""Streamlit AppTest exercises real widgets and reruns; no browser pixel claims."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
APP=Path(__file__).resolve().parents[1]/'app.py'
def button(at,label): return next(b for b in at.button if b.label==label)
def radio(at,label): return next(x for x in at.radio if x.label==label)
def checkbox(at,label): return next(x for x in at.checkbox if x.label==label)
class UITests(unittest.TestCase):
    def setUp(self): self.at=AppTest.from_file(str(APP),default_timeout=20).run()
    def ok(self):
        self.assertFalse(list(self.at.exception))
        # AppTest 1.49 can retain removed form nodes across an explicit rerun.
        # Settle one ordinary rerun before collecting the next widget state.
        self.at._run()
        self.assertFalse(list(self.at.exception))
    def nav(self,name): radio(self.at,'Navigation').set_value(name).run();self.ok()
    def setup(self,level='Beginner'):
        self.nav('Start Training');radio(self.at,'Experience level').set_value(level).run();button(self.at,'Generate Scenario').click().run();self.ok()
    def test_complete_retry_learn_progress(self):
        self.ok();button(self.at,'Start Training').click().run();self.ok()
        self.nav('Settings');checkbox(self.at,'Save completed / exited attempts to history').check().run()
        checkbox(self.at,'Include transcripts and detailed feedback in saved history').check().run()
        self.setup();button(self.at,'Begin Conversation').click().run();self.ok()
        for i in range(3):
            self.at.text_area[0].input('Testing needs more time; option '+str(i)).run();button(self.at,'Send').click().run();self.ok()
        self.assertEqual(self.at.session_state['attempt'].state.value,'completed')
        self.assertTrue(any('Not enough evidence' in m.value for m in self.at.metric))
        button(self.at,'Open targeted lessons').click().run();self.ok();self.assertIn('Learn one thing',self.at.title[0].value)
        self.nav('Progress');self.assertEqual(len(self.at.session_state['repo'].list()),1)
        button(self.at,'Open selected feedback').click().run();self.ok()
        button(self.at,'Try the same scenario again').click().run();self.ok()
        self.assertEqual(self.at.session_state['attempt'].rounds,0)
        self.assertTrue(self.at.session_state['attempt'].parent_retry_id)
    def test_empty_error_exit_and_delete(self):
        self.setup();button(self.at,'Begin Conversation').click().run()
        button(self.at,'Send').click().run();self.ok();self.assertEqual(self.at.session_state['attempt'].rounds,0)
        self.assertTrue(list(self.at.error));button(self.at,'Exit practice and mark incomplete').click().run();self.ok()
        self.assertEqual(self.at.session_state['attempt'].state.value,'incomplete')
        self.nav('Settings');checkbox(self.at,'I want to delete all attempt records in this session and my connected account').check().run()
        button(self.at,'Delete attempt history').click().run();self.ok();self.assertIsNone(self.at.session_state['attempt'])
    def test_missing_key_and_contrasting_template(self):
        self.nav('Start Training');radio(self.at,'Mode').set_value('Live Groq AI').run();button(self.at,'Generate Scenario').click().run();self.ok();self.assertTrue(list(self.at.error))
        self.at.selectbox[0].select('Group responsibilities · University').run()
        radio(self.at,'Mode').set_value('Scripted demo (no credentials)').run();button(self.at,'Generate Scenario').click().run();self.ok()
        self.assertEqual(self.at.session_state['attempt'].scenario.template_id,'group_project')
    def test_experimental_panel_analysis_and_delete(self):
        from unittest.mock import patch
        from tests.test_norms import entries,analyzer
        self.setup();button(self.at,'Begin Conversation').click().run();self.ok()
        for i in range(3):
            self.at.text_area[0].input('Schedule concern '+str(i)).run();button(self.at,'Send').click().run();self.ok()
        self.at.session_state['norm_entries']=entries();self.at._run()
        with patch('ui.norm_analysis.public_models',return_value=analyzer().models):
            button(self.at,'Retrieve norms and analyze learner responses').click().run();self.ok()
        a=self.at.session_state['attempt']
        self.assertIn(a.id,self.at.session_state['norm_results'])
        self.assertIsNone(a.scorecard.overall)
        self.nav('Settings')
        checkbox(self.at,'I want to delete all attempt records in this session and my connected account').check().run()
        button(self.at,'Delete attempt history').click().run();self.ok()
        self.assertFalse(self.at.session_state.filtered_state.get('norm_results'))
    def test_first_time_every_screen(self):
        for name in ['Dashboard','Progress','Learn','Settings','Start Training']:self.nav(name)
if __name__=='__main__':unittest.main()
