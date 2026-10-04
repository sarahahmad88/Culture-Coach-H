import unittest,json,math
from schemas import Configuration,Attempt,State,Evaluation,Evidence,Rating,Scenario,ExportBundle
from orchestrator import Controller
from demo_provider import DemoProvider
from session_manager import accept,transition,retry
from scoring import aggregate,validate_evaluation,score,recommendation
from knowledge import registry
from repository import SessionRepository,export_attempts,import_attempts
from diagnostics import StageError,provider_error
from llm_client import sanitize,Budget
from config import Settings,DIMENSIONS

def config(level='Beginner',template='deadline'):
    return Configuration(my_culture='Pakistan' if template=='deadline' else 'Germany',other_culture='Japan' if template=='deadline' else 'United States',context='Workplace' if template=='deadline' else 'University',situation='Discuss a deadline',my_role='Junior employee' if template=='deadline' else 'Student',other_role='Senior manager' if template=='deadline' else 'Fellow student',goal='Raise a concern' if template=='deadline' else 'Request assistance',level=level,template_id=template)
def started(level='Beginner',template='deadline'):
    a=Attempt(config=config(level,template)); c=Controller(DemoProvider());c.prepare(a);c.begin(a);return a,c
class CoreTests(unittest.TestCase):
    def test_all_eight_required(self):
        for k in ['my_culture','other_culture','context','situation','my_role','other_role','goal','level']:
            values=config().model_dump();values.pop(k)
            with self.assertRaises(ValueError): Configuration(**values)
        for k in ['my_culture','other_culture','situation','my_role','other_role','goal']:
            values=config().model_dump();values[k]='   '
            with self.assertRaises(ValueError): Configuration(**values)
    def test_unsupported_context(self):
        values=config().model_dump();values['context']='Business'
        with self.assertRaises(ValueError): Configuration(**values)
    def test_same_culture(self):
        values=config().model_dump();values['other_culture']='Pakistan';Configuration(**values)
    def test_3_8_15_and_final_no_partner(self):
        for level,n in [('Beginner',3),('Intermediate',8),('Advanced',15)]:
            a,c=started(level)
            frozen=a.scenario.model_dump()
            for i in range(n): c.submit(a,f'My evidence and practical option {i}',str(i))
            self.assertEqual(a.rounds,n);self.assertEqual(a.state,State.completed)
            self.assertEqual(sum(t.role=='partner' for t in a.transcript),n)
            self.assertEqual(a.scenario.model_dump(),frozen)
            self.assertIsNone(a.scorecard.overall)
    def test_contrasting_template(self):
        a,c=started(template='group_project')
        self.assertIn('group project',a.scenario.title)
        for i in range(3): c.submit(a,f'We can divide responsibility {i}',str(i))
        self.assertEqual(a.state,State.completed)
    def test_empty_duplicates(self):
        a,c=started()
        with self.assertRaises(ValueError):c.submit(a,' ','x')
        c.submit(a,'A first suggestion','x')
        self.assertFalse(c.submit(a,'A different suggestion','x'))
        self.assertFalse(c.submit(a,'A first suggestion','y'))
        self.assertEqual(a.rounds,1)
    def test_failed_reply_preserves_turn_and_retry(self):
        class Failing(DemoProvider):
            def run(self,s,a):
                if s=='conversation_partner':raise StageError(s,'timeout','Retry')
                return super().run(s,a)
        a,c=started();c.provider=Failing()
        with self.assertRaises(StageError):c.submit(a,'A valid concern','one')
        self.assertEqual(a.rounds,1);self.assertTrue(a.pending_reply)
        with self.assertRaises(ValueError):c.submit(a,'another','two')
        c.provider=DemoProvider();c.reply(a)
        self.assertEqual(a.rounds,1);self.assertFalse(a.pending_reply)
    def test_score_math(self):
        self.assertEqual(aggregate(dict(zip(DIMENSIONS,[2,3,4,2,3,None]))),56)
        self.assertEqual(aggregate({'a':0,'b':5,'c':None},{'a':3,'b':1}),25)
        self.assertIsNone(aggregate({'a':None}));self.assertEqual(aggregate({'a':0}),0)
        for v in [-1,6,float('nan')]:
            with self.assertRaises(ValueError):aggregate({'a':v})
    def test_missing_values_and_score_status(self):
        r=registry();self.assertTrue(all(v is None for c in r['cultures'].values() for v in c['scores'].values()))
        a,c=started()
        for i in range(3):c.submit(a,'option '+str(i),str(i))
        self.assertEqual(a.scorecard.coverage,0)
        self.assertEqual(a.scorecard.dimensions[0].status,'insufficient_evidence')
        self.assertEqual(a.scorecard.dimensions[-1].status,'not_applicable')
    def test_evidence_exact_and_complete(self):
        a,c=started();c.submit(a,'I have a concern','x')
        e=DemoProvider().run('behavioral_evaluator',a)
        validate_evaluation(a,e,registry())
        e.evidence[0].quote='invented quote'
        with self.assertRaises(ValueError):validate_evaluation(a,e,registry())
        with self.assertRaises(ValueError):validate_evaluation(a,Evaluation(evidence=[],ratings=[],uncertainty='x'),registry())
    def test_unapproved_criterion_rejected(self):
        a,c=started();c.submit(a,'I have a concern','x')
        e=DemoProvider().run('behavioral_evaluator',a)
        e.ratings=[Rating(criterion_id='invented',value=5,evidence_turn_ids=[e.evidence[0].turn_id],reason='test')]
        with self.assertRaises(ValueError):validate_evaluation(a,e,registry())
    def test_exact_retry_distinct(self):
        a,c=started()
        for i in range(3):c.submit(a,'option '+str(i),str(i))
        b=retry(a)
        self.assertNotEqual(a.id,b.id);self.assertEqual(b.parent_retry_id,a.id)
        self.assertEqual(b.scenario,a.scenario);self.assertEqual(b.rounds,0)
    def test_incomplete_and_transitions(self):
        a,c=started();transition(a,State.incomplete)
        self.assertEqual(recommendation([a],'Beginner'),'Beginner')
        with self.assertRaises(ValueError):transition(a,State.completed)
    def test_store_isolation_and_no_transcript_save(self):
        a,c=started();r1=SessionRepository();r2=SessionRepository();r1.save(a)
        self.assertFalse(r2.list());r1.list()[0].transcript.clear();self.assertTrue(a.transcript)
        r1.save(a,False);self.assertFalse(r1.list());self.assertNotIn('transcript',r1.metadata[a.id])
        r1.delete();self.assertFalse(r1.metadata)
    def test_export_roundtrip_and_tampering(self):
        a,c=started()
        for i in range(3):c.submit(a,'option '+str(i),str(i))
        raw=export_attempts([a]);self.assertEqual(import_attempts(raw)[0],a)
        data=json.loads(raw);data['attempts'][0]['scorecard']['overall']=99
        with self.assertRaises(ValueError):import_attempts(json.dumps(data))
        with self.assertRaises(ValueError):import_attempts(b'x'*2_000_001)
    def test_payload_adapter_keeps_tool_fields(self):
        obj={'messages':[{'role':'assistant','cache_breakpoint':True,'tool_calls':[{'id':'123','function':{'name':'lookup','arguments':'{}'}}]},{'role':'tool','tool_call_id':'123','content':[{'type':'text','text':'x','cache_control':{'type':'ephemeral'}}]}]}
        result=sanitize(obj);self.assertNotIn('cache_breakpoint',json.dumps(result));self.assertNotIn('cache_control',json.dumps(result))
        self.assertEqual(result['messages'][0]['tool_calls'][0]['id'],'123');self.assertEqual(result['messages'][1]['tool_call_id'],'123')
    def test_budget_and_redaction(self):
        a=Attempt(config=config());b=Budget(a,Settings(max_calls=1));b.reserve()
        with self.assertRaises(StageError):b.reserve()
        e=provider_error('AI',RuntimeError('secret-key and private transcript'))
        self.assertNotIn('secret',str(e));self.assertNotIn('transcript',str(e))
    def test_reviewed_weighted_dimension_and_zero(self):
        a,c=started();c.submit(a,'Testing needs more time','x')
        turn=[t for t in a.transcript if t.role=='learner'][0]
        r=registry();criteria={}
        for i,(dimension,weight) in enumerate([(DIMENSIONS[0],1),(DIMENSIONS[0],3),(DIMENSIONS[3],1)]):
            ident=str(i);criteria[ident]={'id':ident,'status':'approved','version':'test-only','dimension':dimension,'weight':weight,'reviewer':'synthetic test fixture','source':'synthetic fixture, not cultural data','anchors':{str(n):'synthetic anchor '+str(n) for n in range(6)}}
        r['criteria']=criteria
        a.scenario=a.scenario.model_copy(update={'criterion_ids':tuple(criteria),'rubric_version':'test-only','practice_rubric':None})
        e=Evaluation(evidence=[Evidence(turn_id=turn.id,quote=turn.text,observation='Concern expressed',interpretation='Synthetic mapping for arithmetic test only',uncertainty='fixture',dimension_mappings=[DIMENSIONS[0],DIMENSIONS[3]])],ratings=[Rating(criterion_id=str(i),value=v,evidence_turn_ids=[turn.id],reason='Synthetic test anchor') for i,v in enumerate([0,4,5])],uncertainty='fixture')
        validate_evaluation(a,e,r);card=score(a.scenario,e,r)
        self.assertEqual(card.dimensions[0].value,3);self.assertEqual(card.overall,80)
        self.assertAlmostEqual(card.coverage,2/3)
        r['criteria']['0']['status']='unreviewed'
        with self.assertRaises(ValueError):validate_evaluation(a,e,r)
    def test_ids_frozen_and_supported_roles(self):
        a=Attempt(config=config())
        with self.assertRaises(ValueError):a.id='replacement'
        with self.assertRaises(ValueError):a.config.my_role='CEO'
        values=config().model_dump();values['my_role']='CEO'
        with self.assertRaises(ValueError):Configuration(**values)
    def test_tools_narrow_and_prompts(self):
        from tools import TOOL_NAMES,tool_payload
        from agents.common import GUARDRAILS
        self.assertEqual(len(set(TOOL_NAMES.values())),5);self.assertIn('untrusted',GUARDRAILS)
        a,c=started();p=tool_payload('conversation_partner',a)
        self.assertNotIn('criteria',p);self.assertNotIn('api_key',json.dumps(p))
    def test_script_does_not_phrase_score(self):
        for response in ['I respectfully disagree; testing needs more time.','Could we consider a phased release?']:
            a,c=started()
            for i in range(3):c.submit(a,response+str(i),str(i))
            self.assertIsNone(a.scorecard.overall)
            self.assertTrue(a.evaluation.uncertainty)
if __name__=='__main__':unittest.main()
