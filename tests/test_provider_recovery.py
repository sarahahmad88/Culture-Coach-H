import unittest
from unittest.mock import Mock,patch
import httpx
from groq import APIConnectionError,APITimeoutError
from http_retry import call_with_provider_backoff
from diagnostics import provider_error,StageError
from tests.test_http_retry import HTTPError
from tests.test_core import started
from schemas import State

class ProviderRecoveryTests(unittest.TestCase):
    def connection_error(self,timeout=False):
        request=httpx.Request('POST','https://example.invalid/private')
        return APITimeoutError(request=request) if timeout else APIConnectionError(message='secret transcript',request=request)

    def test_transient_failures_recover_with_identical_budget_rules(self):
        for exc in [self.connection_error(),self.connection_error(True),HTTPError(408),HTTPError(409),HTTPError(500),HTTPError(502),HTTPError(503),HTTPError(504)]:
            with self.subTest(error=type(exc).__name__,status=getattr(exc,'status_code',None)):
                request=Mock(side_effect=[exc,'ok']);reserve=Mock()
                with patch('http_retry.time.sleep') as sleep,patch('http_retry.random.uniform',return_value=0):
                    self.assertEqual(call_with_provider_backoff(request,reserve),'ok')
                    sleep.assert_called_once_with(1.0)
                self.assertEqual(reserve.call_count,2)

    def test_connection_retries_are_bounded_and_unknown_errors_not_retried(self):
        request=Mock(side_effect=self.connection_error())
        with patch('http_retry.time.sleep') as sleep:
            with self.assertRaises(APIConnectionError):call_with_provider_backoff(request,Mock())
            self.assertEqual(request.call_count,4);self.assertEqual(sleep.call_count,3)
            sleep.reset_mock();request=Mock(side_effect=ValueError('unexpected response'))
            with self.assertRaises(ValueError):call_with_provider_backoff(request,Mock())
            request.assert_called_once();sleep.assert_not_called()

    def test_server_retry_after_and_budget_failure(self):
        with patch('http_retry.time.sleep') as sleep:
            request=Mock(side_effect=HTTPError(503,'120'))
            with self.assertRaises(HTTPError):call_with_provider_backoff(request,Mock())
            request.assert_called_once();sleep.assert_not_called()
            request=Mock(side_effect=self.connection_error())
            reserve=Mock(side_effect=[None,StageError('AI budget','limit reached','Stop')])
            with self.assertRaises(StageError):call_with_provider_backoff(request,reserve)
            request.assert_called_once()

    def test_diagnostics_classify_and_log_only_safe_metadata(self):
        cases=[(self.connection_error(),'provider connection'),(self.connection_error(True),'provider timeout'),(HTTPError(503),'provider server error (HTTP 503)'),(HTTPError(422),'invalid provider request'),(ValueError('secret transcript'),'provider request failed')]
        for exc,kind in cases:
            exc.__cause__=httpx.ConnectError('secret API key and transcript')
            with self.assertLogs('diagnostics',level='WARNING') as logs:
                error=provider_error('behavioral_evaluator',exc)
            self.assertEqual(error.kind,kind)
            log=' '.join(logs.output)
            self.assertIn(error.trace_id,log);self.assertIn('ConnectError',log)
            self.assertNotIn('secret',log);self.assertNotIn('https://',log)
            self.assertNotIn('secret',str(error))

    def test_failed_evaluation_preserves_transcript_and_can_resume(self):
        a,controller=started()
        for i in range(a.limit-1):controller.submit(a,f'A response with a reason and option {i}',str(i))
        original=controller.provider.run
        def fail(stage,attempt):
            if stage=='behavioral_evaluator':raise provider_error(stage,self.connection_error())
            return original(stage,attempt)
        with patch.object(controller.provider,'run',side_effect=fail):
            with self.assertRaises(StageError):controller.submit(a,'My final response', 'final')
        self.assertEqual(a.state,State.evaluating);self.assertIsNone(a.evaluation)
        transcript=a.model_copy(deep=True).transcript
        controller.finish(a)
        self.assertEqual(a.state,State.completed);self.assertEqual(a.transcript,transcript)
