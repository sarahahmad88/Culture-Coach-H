import unittest,json
from types import SimpleNamespace
from unittest.mock import patch
from config import Settings
from schemas import Attempt
from llm_client import LiveProvider,make_llm,Budget
from demo_provider import DemoProvider
from orchestrator import Controller
from tools import TOOL_NAMES
from tests.test_core import config
class FakeClient:
    def __init__(self,a):
        self.a=a;self.stage='cultural_context';self.chat=SimpleNamespace(completions=self);self.payloads=[];self.tool_stages=set()
    def create(self,**kw):
        from groq.types.chat import ChatCompletion
        self.payloads.append(kw)
        if self.stage in ('behavioral_evaluator','feedback_synthesizer'):
            self.tool_stages.add(self.stage)
            message={'role':'assistant','content':DemoProvider().run(self.stage,self.a).model_dump_json()}
        elif self.stage not in self.tool_stages:
            self.tool_stages.add(self.stage)
            message={'role':'assistant','content':f'Thought: I need the authorized context.\nAction: {TOOL_NAMES[self.stage]}\nAction Input: {{}}'}
        else:message={'role':'assistant','content':DemoProvider().run(self.stage,self.a).model_dump_json()}
        return ChatCompletion(id='mock',object='chat.completion',created=0,model='mock',choices=[{'index':0,'finish_reason':'stop','message':message}])
class ProviderTests(unittest.TestCase):
    def test_real_crewai_five_agents_with_mock_groq(self):
        a=Attempt(config=config(),mode='live');client=FakeClient(a)
        class Provider(LiveProvider):
            def run(self,stage,attempt):client.stage=stage;return super().run(stage,attempt)
        from tools import build_tool as original
        executed=set()
        def spy(stage,attempt):
            tool=original(stage,attempt);fn=tool.func
            def tracked(): executed.add(stage);return fn()
            tool.func=tracked
            return tool
        with patch('groq.Groq',return_value=client),patch('tools.build_tool',side_effect=spy):
            c=Controller(Provider(Settings(groq_api_key='mock-key')));c.prepare(a);c.begin(a)
            for i in range(3):c.submit(a,f'My legitimate concern and option {i}',str(i))
        self.assertEqual(a.state.value,'completed')
        self.assertEqual(client.tool_stages,set(TOOL_NAMES))
        self.assertIsNone(a.scorecard.overall)
        self.assertEqual(executed,set(TOOL_NAMES))
        self.assertNotIn('cache_breakpoint',json.dumps(client.payloads))
        self.assertTrue(all(x['model']=='openai/gpt-oss-120b' for x in client.payloads))
    def test_native_adapter_tool_fields_and_execution(self):
        from groq.types.chat import ChatCompletion
        a=Attempt(config=config());client=FakeClient(a);payloads=[];executed=[]
        def native(**kw):
            payloads.append(kw)
            message={'role':'assistant','content':'done'} if len(payloads)>1 else {'role':'assistant','content':None,'tool_calls':[{'id':'id-1','type':'function','function':{'name':'authorized_lookup','arguments':'{}'}}]}
            return ChatCompletion(id='mock',object='chat.completion',created=0,model='mock',choices=[{'index':0,'finish_reason':'stop','message':message}])
        client.create=native
        llm=make_llm(Settings(groq_api_key='mock'),Budget(a,Settings()),'cultural_context',client)
        def lookup(): executed.append(True);return 'real retrieved value'
        result=llm.call([{'role':'user','content':'lookup','cache_breakpoint':True}],tools=[{'type':'function','function':{'name':'authorized_lookup','parameters':{'type':'object','properties':{}}}}],available_functions={'authorized_lookup':lookup})
        self.assertEqual(result,'done');self.assertEqual(len(executed),1)
        self.assertEqual(payloads[1]['messages'][-1]['tool_call_id'],'id-1')
        self.assertEqual(payloads[1]['messages'][-1]['content'],'real retrieved value')
        self.assertNotIn('cache_breakpoint',json.dumps(payloads))
    def test_no_live_key_has_no_script_fallback(self):
        a=Attempt(config=config(),mode='live')
        from diagnostics import StageError
        with self.assertRaises(StageError):LiveProvider(Settings()).run('cultural_context',a)
        self.assertIsNone(a.context_package)
    def test_schema_repair_is_bounded(self):
        a=Attempt(config=config(),mode='live');client=FakeClient(a)
        count=[]
        def bad(**kw):
            from groq.types.chat import ChatCompletion
            count.append(kw)
            return ChatCompletion(id='mock',object='chat.completion',created=0,model='mock',choices=[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'{"not_the_schema":1}'}}])
        client.create=bad
        with patch('groq.Groq',return_value=client):
            from diagnostics import StageError
            with self.assertRaises(StageError):LiveProvider(Settings(groq_api_key='mock')).run('cultural_context',a)
        self.assertEqual(len(count),2)
if __name__=='__main__':unittest.main()
