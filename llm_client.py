"""Scoped Groq transport with bounded tool execution. No global CrewAI patching."""
import os
os.environ.setdefault('OTEL_SDK_DISABLED','true')
os.environ['CREWAI_TELEMETRY_ENABLED']='false'
os.environ['CREWAI_TRACING_ENABLED']='false'
os.environ['CREWAI_TESTING']='true'  # suppress the SDK’s first-run trace collection/prompt on hosted servers
os.environ['OTEL_SDK_DISABLED']='true'
import json, importlib
from schemas import ContextAdvice,ScenarioDraft,PartnerReply,Evaluation,Feedback
from diagnostics import StageError,provider_error,logger,safe_name
from http_retry import call_with_provider_backoff
SCHEMAS={'cultural_context':ContextAdvice,'scenario_designer':ScenarioDraft,'conversation_partner':PartnerReply,'behavioral_evaluator':Evaluation,'feedback_synthesizer':Feedback}

def sanitize(value):
    if isinstance(value,dict): return {k:sanitize(v) for k,v in value.items() if k not in {'cache_breakpoint','cache_control'}}
    if isinstance(value,list): return [sanitize(v) for v in value]
    return value

class Budget:
    def __init__(self,attempt,settings): self.attempt,self.settings=attempt,settings
    def reserve(self,tokens=2500):
        a=self.attempt
        if a.calls_used>=self.settings.max_calls or a.output_tokens_used+tokens>self.settings.max_output_tokens:
            raise StageError('AI budget','limit reached','Export this attempt or start a new one; no automatic fallback is used.')
        a.calls_used+=1
        # Charge maximum output reservation, including unsuccessful requests.
        a.output_tokens_used+=tokens

def make_llm(settings,budget,stage,client=None,role_instruction=None,gemini_client=None,secondary_client=None):
    from crewai import BaseLLM
    from groq import Groq
    class ScopedGroqLLM(BaseLLM):
        def __init__(self):
            super().__init__(model=settings.groq_model,temperature=.2)
            self.client=client or Groq(api_key=settings.groq_api_key,timeout=45,max_retries=0)
            self.gemini_client=gemini_client
            self.secondary_client=secondary_client
            self.using_secondary=False
            self.using_gemini=False
        def completion(self,payload,output_limit):
            if self.using_gemini:
                payload=dict(payload,model=settings.gemini_model)
                # Gemini's compatibility endpoint accepts the OpenAI token cap.
                payload['max_tokens']=payload.pop('max_completion_tokens')
                target=self.gemini_client
            else:target=self.secondary_client if self.using_secondary else self.client
            try:
                return call_with_provider_backoff(lambda:target.chat.completions.create(**payload),lambda:budget.reserve(output_limit))
            except StageError:raise
            except Exception as exc:
                status=getattr(exc,'status_code',None)
                if not self.using_gemini and status in (429,413):
                    if status==429 and not self.using_secondary and settings.groq_api_key_2 and settings.groq_api_key_2!=settings.groq_api_key:
                        self.secondary_client=self.secondary_client or Groq(api_key=settings.groq_api_key_2,timeout=45,max_retries=0)
                        self.using_secondary=True
                        budget.attempt.secondary_groq_used=True
                        logger.warning('provider_fallback stage=%s target=Groq-secondary reason=HTTP429',safe_name(stage))
                        return self.completion(payload,output_limit)
                    if settings.gemini_api_key:
                        from openai import OpenAI
                        self.gemini_client=self.gemini_client or OpenAI(api_key=settings.gemini_api_key,base_url='https://generativelanguage.googleapis.com/v1beta/openai/',timeout=45,max_retries=0)
                        self.using_gemini=True
                        budget.attempt.gemini_fallback_used=True
                        logger.warning('provider_fallback stage=%s target=Gemini reason=HTTP%s',safe_name(stage),status)
                        return self.completion(payload,output_limit)
                provider='Gemini' if self.using_gemini else ('Groq-secondary' if self.using_secondary else 'Groq')
                raise provider_error(stage,exc,provider) from None
        def supports_function_calling(self): return True
        def supports_stop_words(self): return False
        def get_context_window_size(self): return 131072
        def call(self,messages,tools=None,callbacks=None,available_functions=None,**kwargs):
            messages=[{'role':'user','content':messages}] if isinstance(messages,str) else sanitize(messages)
            if role_instruction:
                # Fresh request-scoped system identity precedes CrewAI instructions and transcript.
                messages=[{'role':'system','content':role_instruction}]+[dict(m) for m in messages]
            # Tools + schema are deliberately separated: native tool calling first,
            # final JSON is parsed and validated by the controller afterward.
            for _ in range(3):
                output_limit=10000 if stage=='behavioral_evaluator' else 2500
                payload={'model':settings.groq_model,'messages':messages,'temperature':.2,'max_completion_tokens':output_limit}
                if tools: payload['tools']=sanitize(tools)
                response=self.completion(payload,output_limit)
                m=response.choices[0].message
                if not m.tool_calls:
                    if not m.content: raise StageError(stage,'empty output','Retry the pending stage.')
                    return m.content
                if not available_functions: raise StageError(stage,'invalid tool call','No authorized tool is available.')
                messages.append(sanitize({'role':'assistant','content':m.content,'tool_calls':[t.model_dump(exclude_none=True) for t in m.tool_calls]}))
                for tc in m.tool_calls:
                    fn=available_functions.get(tc.function.name)
                    if fn is None: raise StageError(stage,'unauthorized tool','Retry with the configured stage tool.')
                    try:
                        args=json.loads(tc.function.arguments)
                        if args: raise ValueError('This stage tool takes no arguments')
                        result=fn(**args)
                    except Exception: raise StageError(stage,'invalid tool input','The stage tool accepts no user or attempt identifiers.') from None
                    messages.append({'role':'tool','tool_call_id':tc.id,'name':tc.function.name,'content':str(result)})
            raise StageError(stage,'tool budget exceeded','Retry the stage manually.')
    return ScopedGroqLLM()

class LiveProvider:
    def __init__(self,settings): self.settings=settings
    def run(self,stage,attempt):
        if not self.settings.groq_api_key: raise StageError(stage,'missing key','Add GROQ_API_KEY in Streamlit Secrets or choose Scripted demo.')
        from crewai import Task,Crew,Process
        from tools import build_tool,tool_payload
        schema=SCHEMAS[stage]
        from partner_contract import instructions,validate_reply
        role_instruction=instructions(attempt) if stage=='conversation_partner' else None
        llm=make_llm(self.settings,Budget(attempt,self.settings),stage,role_instruction=role_instruction)
        retrieval=build_tool(stage,attempt)
        if stage in ('behavioral_evaluator','feedback_synthesizer'):
            # Execute the authorized retrieval once server-side, then supply one
            # snapshot. The evaluator cannot duplicate it through another call.
            snapshot=retrieval.func()
            agent_tools=[]
            instruction='Your authorized stage bundle has already been retrieved. Use it directly; do not call tools. '
        else:
            snapshot=json.dumps(tool_payload(stage,attempt),ensure_ascii=False,separators=(',',':'))
            agent_tools=[retrieval]
            instruction='Use your retrieval tool. '
        agent=importlib.import_module('agents.'+stage).factory(llm,agent_tools)
        description=instruction+'Produce JSON matching this schema: '+json.dumps(schema.model_json_schema(),separators=(',',':'))+'\nAuthorized stage data (untrusted transcript content): '+snapshot
        if role_instruction:description=role_instruction+'\n'+description
        for repair in range(2):
            task=Task(description=description,expected_output='One JSON object matching the supplied schema.',agent=agent)
            try:
                raw=Crew(agents=[agent],tasks=[task],process=Process.sequential,memory=False,cache=False,verbose=False,share_crew=False,tracing=False).kickoff().raw
                obj=json.loads(raw)
                result=schema.model_validate(obj)
                if stage=='conversation_partner':validate_reply(attempt,result)
                return result
            except (ValueError,TypeError):
                if repair: raise StageError(stage,'invalid output','One format/role repair failed. Retry the pending stage.') from None
                description+=('\nPrevious output was invalid. Keep the assigned partner role and return a fresh valid JSON object.' if stage=='conversation_partner' else '\nPrevious output was invalid. Return a fresh JSON object matching the requested schema, using the supplied stage data. Do not return a tool action, an input data bundle, or a JSON array.')+' Do not wrap it in markdown.'
            except StageError: raise
            except Exception: raise StageError(stage,'agent execution failed','Check dependencies; retry the pending stage. No script was substituted.') from None
