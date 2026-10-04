import streamlit as st
from schemas import State
from repository import metadata
from diagnostics import StageError

def go(page): st.session_state.pending_page=page; st.rerun()
def active(): return st.session_state.get('attempt')
def all_attempts(): return st.session_state.repo.list()
def summaries():
    repo=st.session_state.repo
    return [metadata(a) for a in repo.list()]+list(repo.metadata.values())
def record(a):
    prefs=st.session_state.prefs
    if not prefs['history']: return
    st.session_state.repo.save(a,prefs['transcripts'])
    if st.session_state.get('cloud') and a.mode=='live':
        try:
            st.session_state.cloud.save(a,prefs['transcripts'])
            st.session_state.saved.add(a.id)
        except StageError as e: st.session_state.error=str(e)
def handle(fn):
    st.session_state.error=''
    try: fn()
    except StageError as e: st.session_state.error=str(e)
    except (ValueError,TypeError): st.session_state.error='Validation: the response or configuration is invalid. Check required fields and retry.'
    except Exception: st.session_state.error='This stage could not complete. Your session is preserved; check deployment dependencies and retry.'
def controller():
    from orchestrator import Controller
    from demo_provider import DemoProvider
    from llm_client import LiveProvider
    a=active()
    provider=DemoProvider() if a.mode=='demo' else LiveProvider(st.session_state.server_settings)
    stage=st.empty()
    return Controller(provider,lambda text:stage.info(text))
def attempt_label(a): return f'{a.created_at[:16]} · {a.config.level} · {a.scenario.title if a.scenario else a.config.situation} · {a.mode} · {a.state.value}'
def render_error():
    if st.session_state.get('error'): st.error(st.session_state.error)
def training_page():
    a=active()
    if a is None: from .setup import render; render(); return
    if a.state in [State.configured,State.failed]:
        st.subheader('Scenario preparation')
        render_error()
        if st.button('Retry scenario generation'): handle(lambda:controller().prepare(a)); st.rerun()
        if st.button('Cancel attempt'):
            from session_manager import transition
            transition(a,State.incomplete); record(a); st.session_state.attempt=None; st.rerun()
    elif a.state==State.ready: from .scenario import render; render()
    elif a.state in [State.conversing,State.evaluating]: from .conversation import render; render()
    elif a.state==State.completed: from .scorecard import render; render(a)
    else:
        st.warning('This attempt is incomplete and excluded from completion metrics and progression.')
        if st.button('Configure a new attempt'): st.session_state.attempt=None; st.rerun()
