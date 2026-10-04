import unittest
from unittest.mock import Mock,patch
from types import SimpleNamespace
from datetime import datetime,timedelta,timezone
from email.utils import format_datetime
from http_retry import call_with_provider_backoff,retry_after
from llm_client import make_llm,Budget
from config import Settings
from diagnostics import StageError
from tests.test_core import started
from tests.test_provider import FakeClient

class HTTPError(Exception):
    def __init__(self,status,header=None):
        self.status_code=status
        self.response=SimpleNamespace(headers={} if header is None else {'retry-after':header})

class RetryTests(unittest.TestCase):
    def test_exponential_recovery_and_per_request_reservation(self):
        request=Mock(side_effect=[HTTPError(429),HTTPError(429),HTTPError(429),'ok']);reserve=Mock()
        with patch('http_retry.time.sleep') as sleep,patch('http_retry.random.uniform',return_value=.1):
            self.assertEqual(call_with_provider_backoff(request,reserve),'ok')
            self.assertEqual([c.args[0] for c in sleep.call_args_list],[1.1,2.1,4.1])
        self.assertEqual(reserve.call_count,4)
    def test_retry_after_is_a_minimum_and_long_waits_stop(self):
        with patch('http_retry.time.sleep') as sleep,patch('http_retry.random.uniform',return_value=0):
            request=Mock(side_effect=[HTTPError(429,'5'),'ok'])
            self.assertEqual(call_with_provider_backoff(request,Mock()),'ok');sleep.assert_called_once_with(5.0)
            sleep.reset_mock();request=Mock(side_effect=HTTPError(429,'120'))
            with self.assertRaises(HTTPError):call_with_provider_backoff(request,Mock())
            sleep.assert_not_called();self.assertEqual(request.call_count,1)
    def test_exhaustion_and_non_429_errors(self):
        with patch('http_retry.time.sleep') as sleep,patch('http_retry.random.uniform',return_value=0):
            request=Mock(side_effect=HTTPError(429))
            with self.assertRaises(HTTPError):call_with_provider_backoff(request,Mock())
            self.assertEqual(request.call_count,4);self.assertEqual(sleep.call_count,3)
            for status in [400,401,403,404,422]:
                sleep.reset_mock();request=Mock(side_effect=HTTPError(status))
                with self.assertRaises(HTTPError):call_with_provider_backoff(request,Mock())
                self.assertEqual(request.call_count,1);sleep.assert_not_called()
    def test_total_wait_budget(self):
        request=Mock(side_effect=HTTPError(429,'30'))
        with patch('http_retry.time.sleep') as sleep:
            with self.assertRaises(HTTPError):call_with_provider_backoff(request,Mock())
            self.assertEqual(request.call_count,3);self.assertEqual(sleep.call_count,2)
    def test_header_parsing(self):
        date=format_datetime(datetime.now(timezone.utc)+timedelta(seconds=10),usegmt=True)
        self.assertTrue(8<=retry_after(HTTPError(429,date))<=10)
        for header in ['junk','-1','nan','inf']:self.assertIsNone(retry_after(HTTPError(429,header)))
        self.assertEqual(retry_after(HTTPError(429,'0')),0)
    def test_adapter_retries_without_transcript_changes_and_counts_budget(self):
        a,c=started();client=FakeClient(a);original=a.model_copy(deep=True);count=[]
        def request(**kw):
            from groq.types.chat import ChatCompletion
            count.append(kw)
            if len(count)<3:raise HTTPError(429)
            return ChatCompletion(id='mock',object='chat.completion',created=0,model='mock',choices=[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'done'}}])
        client.create=request
        llm=make_llm(Settings(groq_api_key='mock'),Budget(a,Settings()),'conversation_partner',client)
        with patch('http_retry.time.sleep'),patch('http_retry.random.uniform',return_value=0):
            self.assertEqual(llm.call([{'role':'user','content':'context'}]),'done')
        self.assertEqual(a.calls_used,original.calls_used+3)
        self.assertEqual(a.output_tokens_used,original.output_tokens_used+7500)
        self.assertEqual(a.transcript,original.transcript);self.assertEqual(count[0],count[1])
    def test_budget_stops_further_http_attempts(self):
        a,c=started();client=FakeClient(a);request=Mock(side_effect=HTTPError(429));client.create=request
        settings=Settings(groq_api_key='mock',max_calls=1)
        llm=make_llm(settings,Budget(a,settings),'conversation_partner',client)
        with patch('http_retry.time.sleep'):
            with self.assertRaises(StageError) as error:llm.call('test')
        self.assertEqual(error.exception.stage,'AI budget');self.assertEqual(request.call_count,1)
