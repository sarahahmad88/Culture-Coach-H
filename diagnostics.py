from uuid import uuid4
import logging
import re
from groq import APIConnectionError,APITimeoutError
from openai import APIConnectionError as OpenAIConnectionError,APITimeoutError as OpenAITimeoutError

logger=logging.getLogger(__name__)

def safe_name(value):
    return re.sub(r'[^a-zA-Z0-9_.-]','_',value)[:80]

def safe_provider_details(exc):
    """Classify known provider body fields without storing or logging raw text."""
    body=getattr(exc,'body',None)
    error=body.get('error',body) if isinstance(body,dict) else {}
    if not isinstance(error,dict):error={}
    status=error.get('status')
    allowed={'INVALID_ARGUMENT','FAILED_PRECONDITION','PERMISSION_DENIED','NOT_FOUND','RESOURCE_EXHAUSTED','UNAVAILABLE','DEADLINE_EXCEEDED','INTERNAL','UNKNOWN'}
    status=status if isinstance(status,str) and status in allowed else 'unknown'
    message=error.get('message','')
    message=message.lower() if isinstance(message,str) else ''
    hints=[('thought_signature',('thought_signature','thought signature')),
           ('tool_schema',('function_declaration','function declaration','tools[','tool schema')),
           ('tool_context',('tool_call_id','tool call','function response','function call')),
           ('output_schema',('response_format','response schema','json schema')),
           ('token_parameter',('max_tokens','max_completion_tokens','maxoutputtokens')),
           ('request_size',('context window','request too large','token limit')),
           ('temperature_parameter',('temperature',)),('model_parameter',('model',))]
    reason=next((name for name,terms in hints if any(term in message for term in terms)),'unknown')
    return status,reason
class StageError(RuntimeError):
    def __init__(self,stage,kind,action):
        self.stage,self.kind,self.action,self.trace_id=stage,kind,action,str(uuid4())[:8]
        super().__init__(f'{stage}: {kind}. {action} [reference {self.trace_id}]')
def provider_error(stage,exc,provider='Groq'):
    # Deliberately never retain raw exception text, prompts, headers or credentials.
    status=getattr(exc,'status_code',None)
    if status in (401,403): kind,action='authentication',f'Check the server {"GEMINI_API_KEY" if provider=="Gemini" else "GROQ_API_KEY_2" if provider=="Groq-secondary" else "GROQ_API_KEY"}.'
    elif status==429: kind,action='quota or rate limit','Automatic retries reached their request or wait limit. Wait for your provider limit to reset, then retry the pending stage; your response is preserved.'
    elif status==404: kind,action='model unavailable',('Check GEMINI_MODEL in server Secrets.' if provider=='Gemini' else 'Check access to openai/gpt-oss-120b on Groq.')
    elif status==413: kind,action='request too large (HTTP 413)',('Gemini also rejected this request size. Use a supported model/plan that accepts this request; your response is preserved.' if provider=='Gemini' else 'Groq rejected this request size. Configure GEMINI_API_KEY for size-limit fallback, or use a provider plan that accepts this request. Retrying the identical request will not reduce its size; your response is preserved.')
    elif status in (400,422): kind,action='invalid provider request','Check model compatibility and the deployment dependencies.'
    elif isinstance(exc,(APITimeoutError,OpenAITimeoutError)) or status==408: kind,action='provider timeout','Automatic recovery stopped. Retry the pending stage; your response is preserved.'
    elif isinstance(status,int) and 500<=status<=599: kind,action=f'provider server error (HTTP {status})','Automatic recovery stopped. Wait briefly, then retry the pending stage; your response is preserved.'
    elif status==409: kind,action='provider conflict','Automatic recovery stopped. Retry the pending stage; your response is preserved.'
    elif isinstance(exc,(APIConnectionError,OpenAIConnectionError)): kind,action='provider connection',f'Automatic recovery stopped. Retry the pending stage. If it persists, check the cloud server connection to {provider}; your response is preserved.'
    else: kind,action='provider request failed','Retry the pending stage. If it persists, check deployment logs using this reference; your response is preserved.'
    error=StageError(stage,kind,action)
    # Metadata only: no exception message, traceback, headers, URL or user text.
    cause=exc.__cause__
    provider_status,reason=safe_provider_details(exc)
    logger.warning('provider_failure reference=%s stage=%s provider=%s type=%s status=%s cause=%s provider_status=%s reason=%s',
        error.trace_id,safe_name(stage),safe_name(provider),safe_name(type(exc).__name__),
        status if isinstance(status,int) else 'none',safe_name(type(cause).__name__) if cause else 'none',provider_status,reason)
    return error
