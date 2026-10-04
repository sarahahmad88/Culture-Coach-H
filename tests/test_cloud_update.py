import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from config import CULTURES,GROQ_MODEL,Settings
from culturebank_adapter import normalize_rows,matches_culture
from knowledge import registry
from repository import export_attempts,import_attempts,metadata,SessionRepository
from session_manager import retry
from tests.test_core import started
from ui.feedback_rating import update_rating
APP=Path(__file__).resolve().parents[1]/'app.py'
class CloudUpdateTests(unittest.TestCase):
    def complete(self):
        a,c=started()
        for i in range(3):c.submit(a,'A practical option '+str(i),str(i))
        return a
    def test_all_countries(self):
        self.assertEqual(len(CULTURES),14);self.assertEqual(set(CULTURES),set(registry()['cultures']))
        at=AppTest.from_file(str(APP)).run();at.radio[0].set_value('Start Training').run()
        for label in ['My culture','Other person’s culture']:
            self.assertEqual(next(x for x in at.selectbox if x.label==label).options,CULTURES)
        next(x for x in at.selectbox if x.label=='My culture').select('China').run()
        next(x for x in at.selectbox if x.label=='Other person’s culture').select('Greece').run()
        next(b for b in at.button if b.label=='Generate Scenario').click().run()
        self.assertFalse(list(at.exception));self.assertEqual(at.session_state['attempt'].config.other_culture,'Greece')
        at.radio[0].set_value('Settings').run()
        self.assertEqual(next(x for x in at.selectbox if x.label=='Preferred culture').options,CULTURES)
    def test_model(self):
        self.assertEqual(Settings.load({'GROQ_MODEL':'old-model'}).groq_model,GROQ_MODEL)
        self.assertEqual(GROQ_MODEL,'openai/gpt-oss-120b')
    def test_aliases(self):
        for country,group in zip(CULTURES[4:],['Chinese','Australian','British','Saudi Arabian','Egyptian','Brazilian','Mexican','South African','French','Greek']):
            e=normalize_rows([{'cultural_group':group,'context':'office','actor_behavior':'asks a question'}],'test','v1')[0][0]
            self.assertTrue(matches_culture(e,country));self.assertFalse(matches_culture(e.model_copy(update={'cultural_group':group+' subgroup'}),country))
    def test_rating_export_validation_retry(self):
        a=self.complete();a.feedback_rating=5
        self.assertEqual(import_attempts(export_attempts([a]))[0].feedback_rating,5)
        self.assertEqual(metadata(a)['feedback_rating'],5);self.assertIsNone(retry(a).feedback_rating)
        with self.assertRaises(ValueError):a.feedback_rating=6
        with self.assertRaises(ValueError):a.feedback_rating=0
    def test_consent(self):
        from ui import feedback_rating,components
        a=self.complete();repo=SessionRepository();key='feedback-stars-'+a.id
        class StateDict(dict):
            def __getattr__(self,name):return self[name]
        state=StateDict({key:4,'attempt':a,'repo':repo,'prefs':{'history':False,'transcripts':True},'cloud':None})
        with patch.object(feedback_rating.st,'session_state',state),patch.object(components.st,'session_state',state):
            update_rating(a,key);self.assertEqual(a.feedback_rating,5);self.assertEqual(repo.list(),[])
            state['prefs']['history']=True;state[key]=1;update_rating(a,key)
            self.assertEqual(repo.list()[0].feedback_rating,2)
    def test_widget_deletion(self):
        a=self.complete();at=AppTest.from_file(str(APP)).run();at.session_state['attempt']=a
        at.radio[0].set_value('Start Training').run()
        self.assertFalse(list(at.exception));self.assertEqual(len(at.get('button_group')),1)
        key='feedback-stars-'+a.id
        at.get('button_group')[0].set_value([4]).run();self.assertFalse(list(at.exception));self.assertEqual(a.feedback_rating,5)
        at.radio[0].set_value('Settings').run()
        next(x for x in at.checkbox if x.label=='I want to delete all attempt records in this session and my connected account').check().run()
        next(x for x in at.button if x.label=='Delete attempt history').click().run()
        self.assertFalse(list(at.exception));self.assertNotIn(key,at.session_state.filtered_state)
