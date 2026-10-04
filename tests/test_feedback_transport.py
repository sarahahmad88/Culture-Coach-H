import json
import unittest
from unittest.mock import patch,Mock
import httpx
from openai import OpenAI
from config import Settings
from llm_client import LiveProvider
from orchestrator import Controller
from schemas import State
from demo_provider import DemoProvider
from diagnostics import provider_error,safe_provider_details,StageError
from tests.test_practice_scoring import scored
from tests.test_http_retry import HTTPError
from tests.test_provider_fallback import client
from tools import build_tool

class FeedbackTransportTests(unittest.TestCase):
    def run_feedback(self,outputs):
        a=scored();a.state=State.evaluating;a.feedback=None
        expected=DemoProvider().run('feedback_synthesizer',a)
        before=a.model_copy(deep=True);requests=[];retrievals=[]
        def route(request):
            payload=json.loads(request.content);requests.append(payload)
            output=outputs[len(requests)-1] if outputs else expected.model_dump_json()
            return httpx.Response(200,json={'id':'mock','object':'chat.completion','created':0,'model':'mock','choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':output}}]})
        google=OpenAI(api_key='mock-google',base_url='https://generativelanguage.googleapis.com/v1beta/openai/',http_client=httpx.Client(transport=httpx.MockTransport(route)),max_retries=0)
        first=client(HTTPError(413));original=build_tool
        def spy(stage,attempt):
            tool=original(stage,attempt);fn=tool.func
            def track():retrievals.append(stage);return fn()
            tool.func=track;return tool
        settings=Settings(groq_api_key='mock-primary',gemini_api_key='mock-google')
        try:
            with patch('groq.Groq',return_value=first),patch('openai.OpenAI',return_value=google),patch('tools.build_tool',side_effect=spy):
                Controller(LiveProvider(settings)).finish(a)
        finally:google.close()
        return a,before,requests,retrievals,expected

    def test_actual_openai_sdk_gemini_feedback_request_is_tool_free(self):
        a,before,requests,retrievals,expected=self.run_feedback([])
        self.assertEqual(a.state,State.completed);self.assertEqual(a.feedback,expected)
        self.assertEqual(a.transcript,before.transcript);self.assertEqual(a.evaluation,before.evaluation)
        self.assertEqual(a.practice_scores,before.practice_scores)
        self.assertEqual(retrievals,['feedback_synthesizer']);self.assertEqual(len(requests),1)
        payload=requests[0]
        self.assertNotIn('tools',payload);self.assertNotIn('tool_choice',payload)
        self.assertNotIn('max_completion_tokens',payload)
        self.assertEqual(payload['max_tokens'],2500);self.assertEqual(payload['model'],'gemini-3.8-flash')
        self.assertTrue(all(m['role'] in ('system','user') for m in payload['messages']))
        self.assertTrue(all(isinstance(m['content'],str) for m in payload['messages']))
        self.assertTrue(a.gemini_fallback_used)

    def test_feedback_bundle_array_is_rejected_and_repaired_once(self):
        a=scored();expected=DemoProvider().run('feedback_synthesizer',a)
        result,before,requests,retrievals,_=self.run_feedback(['[{}, {"lessons":[]}]',expected.model_dump_json()])
        self.assertEqual(result.state,State.completed)
        self.assertEqual(len(requests),2);self.assertEqual(retrievals,['feedback_synthesizer'])
        self.assertTrue(all('tools' not in p for p in requests))
        repair='\n'.join(m['content'] for m in requests[-1]['messages'])
        self.assertIn('Do not return a tool action',repair)
        self.assertNotIn('Keep the assigned partner role',repair)
        self.assertEqual(result.evaluation,before.evaluation)

    def test_safe_provider_body_categories_do_not_leak_raw_text(self):
        error=HTTPError(400)
        error.body={'error':{'status':'INVALID_ARGUMENT','message':'tools[0].function_declarations invalid. secret transcript and secret API key'}}
        with self.assertLogs('diagnostics',level='WARNING') as logs:
            result=provider_error('feedback_synthesizer',error,'Gemini')
        log=' '.join(logs.output)
        self.assertIn('provider_status=INVALID_ARGUMENT',log);self.assertIn('reason=tool_schema',log)
        self.assertIn(result.trace_id,log);self.assertNotIn('secret',log)
        error.body={'message':'Missing thought_signature. secret key','status':'PRIVATE SECRET'}
        self.assertEqual(safe_provider_details(error),('unknown','thought_signature'))
        error.body='raw secret';self.assertEqual(safe_provider_details(error),('unknown','unknown'))

    def test_failed_feedback_keeps_validated_evaluation_for_retry(self):
        a=scored();a.state=State.evaluating;a.feedback=None;before=a.model_copy(deep=True)
        first=client(HTTPError(400));settings=Settings(groq_api_key='mock')
        with patch('groq.Groq',return_value=first):
            with self.assertRaises(StageError):Controller(LiveProvider(settings)).finish(a)
        self.assertEqual(a.state,State.evaluating);self.assertIsNone(a.feedback)
        self.assertEqual(a.evaluation,before.evaluation);self.assertEqual(a.transcript,before.transcript)
        Controller(DemoProvider()).finish(a)
        self.assertEqual(a.state,State.completed);self.assertEqual(a.evaluation,before.evaluation)
