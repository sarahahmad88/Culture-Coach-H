import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from config import Settings
from llm_client import make_llm,Budget
from diagnostics import StageError
from tests.test_core import started
from tests.test_http_retry import HTTPError

def client(outcome):
    request=Mock(side_effect=outcome if isinstance(outcome,Exception) else None)
    if not isinstance(outcome,Exception):
        request.return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None,content=outcome))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=request)))

class FallbackTests(unittest.TestCase):
    def llm(self,primary,secondary,gemini,settings=None):
        a,_=started()
        settings=settings or Settings(groq_api_key='first-key',groq_api_key_2='second-key',gemini_api_key='google-key')
        return a,make_llm(settings,Budget(a,settings),'behavioral_evaluator',primary,gemini_client=gemini,secondary_client=secondary)

    @patch('http_retry.time.sleep')
    def test_order_and_identical_stage_payload(self,sleep):
        first=client(HTTPError(429));second=client(HTTPError(429));google=client('result')
        a,llm=self.llm(first,second,google)
        transcript=a.model_copy(deep=True).transcript
        self.assertEqual(llm.call([{'role':'user','content':'original context'}]),'result')
        self.assertEqual(first.chat.completions.create.call_count,4)
        self.assertEqual(second.chat.completions.create.call_count,4)
        self.assertEqual(google.chat.completions.create.call_count,1)
        primary=first.chat.completions.create.call_args.kwargs
        self.assertEqual(primary,second.chat.completions.create.call_args.kwargs)
        fallback=google.chat.completions.create.call_args.kwargs
        self.assertEqual(fallback['messages'],primary['messages'])
        self.assertEqual(fallback['model'],'gemini-3.8-flash')
        self.assertEqual(fallback['max_tokens'],10000)
        self.assertNotIn('max_completion_tokens',fallback)
        self.assertEqual(a.calls_used,9);self.assertEqual(a.output_tokens_used,90000)
        self.assertTrue(a.secondary_groq_used);self.assertTrue(a.gemini_fallback_used)
        self.assertEqual(a.transcript,transcript)
        # Subsequent tool/final calls in this stage stay on the selected provider.
        self.assertEqual(llm.call('continued stage'),'result')
        self.assertEqual(first.chat.completions.create.call_count,4)

    @patch('http_retry.time.sleep')
    def test_second_key_success_does_not_contact_gemini(self,sleep):
        first=client(HTTPError(429));second=client('ok');google=client('unused')
        a,llm=self.llm(first,second,google)
        self.assertEqual(llm.call('context'),'ok');google.chat.completions.create.assert_not_called()
        self.assertTrue(a.secondary_groq_used);self.assertFalse(a.gemini_fallback_used)

    @patch('http_retry.time.sleep')
    def test_non_rate_limit_failures_do_not_switch_keys(self,sleep):
        for status in [400,401,403,404,422,503]:
            first=client(HTTPError(status));second=client('unused');google=client('unused')
            a,llm=self.llm(first,second,google)
            with self.assertRaises(StageError):llm.call('context')
            second.chat.completions.create.assert_not_called();google.chat.completions.create.assert_not_called()

    @patch('http_retry.time.sleep')
    def test_duplicate_or_missing_secondary_skipped(self,sleep):
        for second_key in ['', 'first-key']:
            settings=Settings(groq_api_key='first-key',groq_api_key_2=second_key,gemini_api_key='google-key')
            first=client(HTTPError(429));second=client('unused');google=client('ok')
            a,llm=self.llm(first,second,google,settings)
            self.assertEqual(llm.call('context'),'ok');second.chat.completions.create.assert_not_called()
            self.assertFalse(a.secondary_groq_used)

    @patch('http_retry.time.sleep')
    def test_all_keys_exhausted_stop_without_cycling(self,sleep):
        first=client(HTTPError(429));second=client(HTTPError(429));google=client(HTTPError(429))
        a,llm=self.llm(first,second,google)
        with self.assertRaises(StageError) as error:llm.call('context')
        self.assertEqual(error.exception.kind,'quota or rate limit')
        self.assertEqual(a.calls_used,12)
        for c in [first,second,google]:self.assertEqual(c.chat.completions.create.call_count,4)

    @patch('http_retry.time.sleep')
    def test_budget_cannot_be_bypassed_by_fallback(self,sleep):
        settings=Settings(groq_api_key='first-key',groq_api_key_2='second-key',gemini_api_key='google-key',max_calls=4)
        first=client(HTTPError(429));second=client('unused');google=client('unused')
        a,llm=self.llm(first,second,google,settings)
        with self.assertRaises(StageError) as error:llm.call('context')
        self.assertEqual(error.exception.stage,'AI budget')
        second.chat.completions.create.assert_not_called();google.chat.completions.create.assert_not_called()

    def test_secrets_configuration(self):
        settings=Settings.load({'GROQ_API_KEY':'first','GROQ_API_KEY_2':'second','GEMINI_API_KEY':'google','GEMINI_MODEL':'custom-gemini','GROQ_MODEL':'override'})
        self.assertEqual(settings.groq_model,'openai/gpt-oss-120b')
        self.assertEqual(settings.groq_api_key_2,'second')
        self.assertEqual(settings.gemini_api_key,'google');self.assertEqual(settings.gemini_model,'custom-gemini')
