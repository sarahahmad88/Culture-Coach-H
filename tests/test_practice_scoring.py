"""Synthetic model outputs validate arithmetic/contracts, not cultural accuracy."""
import unittest,json
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from schemas import Attempt,Rating,AdaptationRating,ScenarioDraft
from tests.test_core import config,started
from demo_provider import DemoProvider
from orchestrator import Controller
from practice_scoring import build_rubric,practice_scores,validate_practice,reference
from repository import export_attempts,import_attempts,metadata
from scoring import validate_evaluation
from knowledge import registry
from diagnostics import StageError
from config import CULTURES,DIMENSIONS,Settings
from llm_client import LiveProvider
from tests.test_provider import FakeClient

class SyntheticProvider(DemoProvider):
    def run(self,stage,a):
        if stage=='scenario_designer':
            rubric=build_rubric(a.config)
            return ScenarioDraft(brief='Synthetic scoring integration fixture, not cultural validation.',opening='Please consider these preferences: '+' '.join(c.expectation for c in rubric.adaptation))
        output=super().run(stage,a)
        if stage=='behavioral_evaluator':
            learners=[t for t in a.transcript if t.role=='learner'];cue=a.transcript[0]
            output.communication_ratings=[Rating(criterion_id=c.id,value=3 if i else 0,evidence_turn_ids=[learners[0].id],reason='Synthetic fixture anchor') for i,c in enumerate(a.scenario.practice_rubric.communication)]
            output.adaptation_ratings=[AdaptationRating(criterion_id=c.id,value=4 if i==0 else None,evidence_turn_ids=[learners[0].id] if i==0 else [],reason='Synthetic cue fixture' if i==0 else 'Insufficient observable opportunity',partner_cue_turn_id=cue.id if i==0 else None,partner_cue_quote=cue.text if i==0 else None) for i,c in enumerate(a.scenario.practice_rubric.adaptation)]
        return output

def scored(country='Japan',style='country_informed'):
    c=config().model_copy(update={'other_culture':country,'persona_style':style})
    a=Attempt(config=c,mode='live');controller=Controller(SyntheticProvider());controller.prepare(a);controller.begin(a)
    for i in range(3):controller.submit(a,'I can explain risks and propose a practical option '+str(i),str(i))
    return a

class PracticeTests(unittest.TestCase):
    def test_reference_values_and_missing_country_dimensions(self):
        self.assertEqual(set(reference()['countries']),set(CULTURES))
        self.assertEqual(reference()['countries']['China']['scores']['Power Distance'],80)
        self.assertEqual(reference()['countries']['Greece']['scores']['Uncertainty Avoidance'],100)
        for country in ['Saudi Arabia','Egypt','South Africa']:
            r=build_rubric(config().model_copy(update={'other_culture':country}))
            self.assertEqual(sum(x is None for x in r.country_scores),4)
            self.assertEqual(len(r.adaptation),2)
    def test_independent_scores_zero_missing_and_coverage(self):
        a=scored();self.assertEqual(a.practice_scores.communication.overall,48)
        self.assertEqual(a.practice_scores.communication.coverage,1)
        self.assertEqual(a.practice_scores.adaptation.overall,80)
        self.assertAlmostEqual(a.practice_scores.adaptation.coverage,1/6)
        self.assertIsNone(a.scorecard.overall)
        self.assertEqual(a.practice_scores.communication.dimensions[0].value,0)
        self.assertIsNone(a.practice_scores.adaptation.dimensions[1].value)
    def test_partial_reference_is_na_not_zero(self):
        a=scored('Egypt');card=a.practice_scores.adaptation
        self.assertEqual(sum(d.status=='not_applicable' for d in card.dimensions),4)
        self.assertEqual(card.overall,80);self.assertEqual(card.coverage,.5)
    def test_cue_must_be_real_and_precede_rated_turns(self):
        a=scored();e=a.evaluation.model_copy(deep=True)
        e.adaptation_ratings[0].partner_cue_quote='fabricated'
        with self.assertRaises(ValueError):validate_practice(a,e)
        e=a.evaluation.model_copy(deep=True);cue=[t for t in a.transcript if t.role=='partner'][-1]
        e.adaptation_ratings[0].partner_cue_turn_id=cue.id;e.adaptation_ratings[0].partner_cue_quote=cue.text
        with self.assertRaises(ValueError):validate_practice(a,e)
    def test_demo_abstains_and_rejects_numeric_ratings(self):
        a,c=started()
        for i in range(3):c.submit(a,'My demonstration response '+str(i),str(i))
        self.assertIsNone(a.practice_scores.communication.overall);self.assertIsNone(a.practice_scores.adaptation.overall)
        e=a.evaluation.model_copy(deep=True);e.communication_ratings[0].value=5;e.communication_ratings[0].evidence_turn_ids=[a.transcript[1].id]
        with self.assertRaises(ValueError):validate_practice(a,e)
    def test_export_recomputes_and_rejects_tampered_persona_or_scores(self):
        a=scored();raw=export_attempts([a]);self.assertEqual(import_attempts(raw)[0],a)
        for field in ['score','persona','criterion']:
            data=json.loads(raw);record=data['attempts'][0]
            if field=='score':record['practice_scores']['communication']['overall']=99
            elif field=='persona':record['scenario']['practice_rubric']['country_scores'][0]=99
            else:record['evaluation']['communication_ratings'][0]['criterion_id']='unknown'
            with self.assertRaises(ValueError):import_attempts(json.dumps(data))
    def test_duplicate_and_invalid_learner_evidence_rejected(self):
        a=scored();e=a.evaluation.model_copy(deep=True);e.communication_ratings.append(e.communication_ratings[0])
        with self.assertRaises(ValueError):validate_practice(a,e)
        e=a.evaluation.model_copy(deep=True);e.communication_ratings[0].evidence_turn_ids=[a.transcript[0].id]
        with self.assertRaises(ValueError):validate_practice(a,e)
    def test_frozen_retry_and_contrasting_profile(self):
        from session_manager import retry
        a=scored();b=retry(a)
        self.assertEqual(a.scenario.practice_rubric,b.scenario.practice_rubric);self.assertIsNone(b.practice_scores)
        typical=build_rubric(config().model_copy(update={'other_culture':'China'}))
        contrast=build_rubric(config().model_copy(update={'other_culture':'China','persona_style':'contrast'}))
        self.assertEqual(typical.country_scores,contrast.country_scores)
        self.assertNotEqual(typical.adaptation[0].expectation,contrast.adaptation[0].expectation)
    def test_metadata_contains_two_separate_scores(self):
        row=metadata(scored());self.assertEqual(row['communication_score'],48);self.assertEqual(row['adaptation_score'],80)
        self.assertIsNone(row['overall']);self.assertEqual(row['practice_rubric_version'],'practice-v1.0')
    def test_legacy_export_still_loads_without_new_scores(self):
        a,c=started()
        a.scenario=a.scenario.model_copy(update={'practice_rubric':None})
        for i in range(3):c.submit(a,'Legacy practice '+str(i),str(i))
        self.assertIsNone(import_attempts(export_attempts([a]))[0].practice_scores)
    def test_mocked_crewai_produces_both_numerical_scorecards(self):
        a=Attempt(config=config(),mode='live');client=FakeClient(a)
        original=client.create
        def create(**kw):
            if client.stage=='behavioral_evaluator':
                from groq.types.chat import ChatCompletion
                return ChatCompletion(id='mock',object='chat.completion',created=0,model='mock',choices=[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':SyntheticProvider().run(client.stage,a).model_dump_json()}}])
            return original(**kw)
        client.create=create
        class Provider(LiveProvider):
            def run(self,stage,attempt):client.stage=stage;return super().run(stage,attempt)
        with patch('groq.Groq',return_value=client):
            c=Controller(Provider(Settings(groq_api_key='mock')));c.prepare(a);c.begin(a)
            for i in range(3):c.submit(a,'My concern and option '+str(i),str(i))
        self.assertEqual(a.practice_scores.communication.overall,48);self.assertEqual(a.practice_scores.adaptation.overall,80)
    def test_ui_numeric_panels_and_comparable_trends(self):
        a=scored();b=scored();b.scenario=a.scenario
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run()
        at.session_state['attempt']=a;at.radio[0].set_value('Start Training').run();at._run()
        self.assertFalse(list(at.exception));self.assertEqual(len(at.get('plotly_chart')),2)
        self.assertTrue(any(m.value=='48' for m in at.metric));self.assertTrue(any(m.value=='80' for m in at.metric))
        at.session_state['repo'].save(a,True);at.session_state['repo'].save(b,True)
        next(x for x in at.radio if x.label=='Navigation').set_value('Progress').run();at._run();self.assertFalse(list(at.exception));self.assertEqual(len(at.get('plotly_chart')),2)
        next(x for x in at.selectbox if x.label=='Filter by mode').select('demo').run()
        self.assertFalse(list(at.exception));self.assertEqual(len(at.get('plotly_chart')),0)

    def test_invalid_adaptation_gets_bounded_repair_without_losing_turns(self):
        class Broken(SyntheticProvider):
            evaluations=0
            def run(self,stage,a):
                out=super().run(stage,a)
                if stage=='behavioral_evaluator':
                    self.evaluations+=1
                    out.adaptation_ratings[0].partner_cue_quote='Not in the transcript'
                return out
        a=Attempt(config=config(),mode='live');provider=Broken();c=Controller(provider)
        c.prepare(a);c.begin(a)
        for i in range(2):c.submit(a,'An option '+str(i),str(i))
        with self.assertRaises(StageError):c.submit(a,'A final option','2')
        self.assertEqual(provider.evaluations,2);self.assertEqual(a.rounds,3)
        self.assertEqual(a.state.value,'evaluating');self.assertIsNone(a.evaluation);self.assertIsNone(a.practice_scores)
        c.provider=SyntheticProvider();c.finish(a)
        self.assertEqual(a.state.value,'completed');self.assertEqual(a.rounds,3)
