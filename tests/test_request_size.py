import json
import unittest
from unittest.mock import patch
from tools import tool_payload,build_tool
from tests.test_core import started
from tests.test_provider import FakeClient
from tests.test_provider_fallback import client
from tests.test_http_retry import HTTPError
from llm_client import LiveProvider,make_llm,Budget
from config import Settings
from diagnostics import provider_error,StageError
from schemas import Turn

class RequestSizeTests(unittest.TestCase):
    def test_evaluation_bundle_has_one_complete_rubric_and_exact_turns(self):
        a,_=started('Advanced')
        a.transcript=[Turn(role='learner' if i%2 else 'partner',text=('Exact long response '+str(i)+' ')+'x'*2900) for i in range(30)]
        payload=tool_payload('behavioral_evaluator',a)
        self.assertNotIn('practice_rubric',payload['scenario'])
        self.assertEqual(payload['practice_rubric'],a.scenario.practice_rubric.model_dump())
        self.assertEqual(payload['criteria'],[])
        for actual,turn in zip(payload['transcript'],a.transcript):
            self.assertEqual(actual,{'id':turn.id,'role':turn.role,'text':turn.text})
        self.assertEqual(len(payload['transcript']),30)

    def test_evaluator_retrieves_once_and_sends_snapshot_once(self):
        a,_=started();a.mode='live';fake=FakeClient(a);fake.stage='behavioral_evaluator'
        original=build_tool;retrieved=[]
        def spy(stage,attempt):
            tool=original(stage,attempt);fn=tool.func
            def tracked():retrieved.append(stage);return fn()
            tool.func=tracked
            return tool
        with patch('groq.Groq',return_value=fake),patch('tools.build_tool',side_effect=spy):
            LiveProvider(Settings(groq_api_key='mock')).run('behavioral_evaluator',a)
        self.assertEqual(retrieved,['behavioral_evaluator'])
        self.assertEqual(len(fake.payloads),1)
        self.assertNotIn('tools',fake.payloads[0])
        prompt='\n'.join(m['content'] for m in fake.payloads[0]['messages'])
        rubric=json.dumps(a.scenario.practice_rubric.model_dump(),ensure_ascii=False,separators=(',',':'))
        self.assertEqual(prompt.count(rubric),1)

    def test_413_skips_same_request_retries_and_second_groq_key(self):
        first=client(HTTPError(413));second=client('unused');google=client('ok')
        a,_=started();settings=Settings(groq_api_key='first',groq_api_key_2='second',gemini_api_key='google')
        llm=make_llm(settings,Budget(a,settings),'behavioral_evaluator',first,gemini_client=google,secondary_client=second)
        with patch('http_retry.time.sleep') as sleep:
            self.assertEqual(llm.call('full evaluation context'),'ok');sleep.assert_not_called()
        first.chat.completions.create.assert_called_once();second.chat.completions.create.assert_not_called()
        google.chat.completions.create.assert_called_once();self.assertEqual(a.calls_used,2)
        self.assertTrue(a.gemini_fallback_used);self.assertFalse(a.secondary_groq_used)

    def test_413_without_gemini_is_actionable_and_not_retried(self):
        first=client(HTTPError(413));a,_=started();settings=Settings(groq_api_key='mock')
        llm=make_llm(settings,Budget(a,settings),'behavioral_evaluator',first)
        with patch('http_retry.time.sleep') as sleep:
            with self.assertRaises(StageError) as error:llm.call('full context')
            sleep.assert_not_called()
        first.chat.completions.create.assert_called_once()
        self.assertEqual(error.exception.kind,'request too large (HTTP 413)')
        self.assertIn('GEMINI_API_KEY',str(error.exception))

    def test_feedback_payload_does_not_repeat_evaluator_anchors(self):
        a,controller=started()
        for i in range(a.limit):controller.submit(a,'A reason and option '+str(i),str(i))
        payload=tool_payload('feedback_synthesizer',a)
        self.assertNotIn('practice_rubric',payload['scenario'])
        self.assertEqual(payload['evaluation'],a.evaluation.model_dump())
        self.assertEqual(payload['practice_scores'],a.practice_scores.model_dump())
