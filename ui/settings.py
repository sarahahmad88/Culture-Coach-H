import streamlit as st
from config import LEVELS,CULTURES
from repository import export_attempts,import_attempts,SupabaseRepository
from .components import all_attempts,active,handle,render_error

def render():
    st.title('Settings & privacy')
    prefs=st.session_state.prefs
    prefs['animations']=st.checkbox('Animate practice personas',value=prefs.get('animations',True))
    st.caption('Your device’s reduced-motion preference also disables persona animation.')
    prefs['culture']=st.selectbox('Preferred culture',CULTURES,index=CULTURES.index(prefs['culture']))
    prefs['level']=st.selectbox('Preferred level',list(LEVELS),index=list(LEVELS).index(prefs['level']))
    prefs['evidence']=st.checkbox('Display detailed evidence',value=prefs['evidence'])
    prefs['history']=st.checkbox('Save completed / exited attempts to history',value=prefs['history'])
    prefs['transcripts']=st.checkbox('Include transcripts and detailed feedback in saved history',value=prefs['transcripts'],disabled=not prefs['history'])
    st.caption('Preferences last for this browser session. No external analytics are collected. Turning history off stops future history writes; existing saved records remain until you delete them. Turning transcript saving off stores only attempt ID, time, mode, state, level, template ID, reviewed score/coverage, both practice estimates/coverage, rubric version and feedback usefulness rating. Existing full transcripts remain until deletion.')
    st.write('In live mode, selected cultures, roles, goal, scenario and transcript are sent to Groq for generation and feedback. If Gemini fallback is configured, the same stage data may be sent to Google after a Groq rate limit or request-size rejection. Do not include confidential personal information. Scripted demo makes no LLM requests. Active transcript is needed in session memory even when history saving is off.')
    st.info('Session-only mode; progress will not survive a restart.' if not st.session_state.get('cloud') else 'Signed in to optional Supabase history. Only live attempts are written to the account; demo activity stays in this session.')
    settings=st.session_state.server_settings
    st.caption('Second Groq key fallback: '+('enabled' if settings.groq_api_key_2 and settings.groq_api_key_2!=settings.groq_api_key else 'disabled · no distinct server GROQ_API_KEY_2 configured'))
    st.caption('Gemini rate-limit fallback: '+('enabled · '+settings.gemini_model if settings.gemini_api_key else 'disabled · no server GEMINI_API_KEY configured'))
    if settings.supabase_url and settings.supabase_key:
        if not st.session_state.get('cloud'):
            with st.form('login',clear_on_submit=True):
                email=st.text_input('Account email'); password=st.text_input('Account password',type='password')
                login=st.form_submit_button('Sign in to history')
            st.caption('Use an existing confirmed Supabase account. Account creation and recovery are managed through your project administrator; no typed username is treated as login.')
            if login:
                def connect():
                    cloud=SupabaseRepository.login(settings,email,password)
                    # Clear previous session data before crossing an identity boundary.
                    st.session_state.repo.delete(); st.session_state.attempt=None; st.session_state.cloud=cloud
                    from .norm_analysis import clear_norm_data
                    clear_norm_data()
                    from .feedback_rating import clear_rating_widgets
                    clear_rating_widgets()
                    st.session_state.saved.clear(); st.session_state.review_id=None
                handle(connect); st.rerun()
        elif st.button('Sign out and clear account session data'):
            def disconnect():
                st.session_state.cloud.sign_out(); st.session_state.cloud=None
                st.session_state.repo.delete(); st.session_state.attempt=None; st.session_state.saved.clear(); st.session_state.review_id=None
                from .norm_analysis import clear_norm_data
                clear_norm_data()
                from .feedback_rating import clear_rating_widgets
                clear_rating_widgets()
            handle(disconnect); st.rerun()
    else: st.caption('Persistent accounts are inactive. An operator must configure Supabase and apply the supplied RLS migration.')
    from .norm_analysis import configure,clear_norm_data
    configure()
    st.subheader('Your data')
    items={a.id:a for a in all_attempts()}
    if active(): items[active().id]=active()
    if items:
        st.download_button('Export personal attempts / reviewer bundle',export_attempts(list(items.values())),file_name='personal_attempts.json',mime='application/json')
        st.caption('This export contains your transcript. Share it with a reviewer only if you choose. Reviewer checklist is in REVIEW.md.')
    uploaded=st.file_uploader('Import a validated personal attempt export',type=['json'])
    if uploaded and st.button('Validate and import into session'):
        def load():
            attempts=import_attempts(uploaded.getvalue())
            for a in attempts: st.session_state.repo.save(a,True)
        handle(load); st.rerun()
    st.caption('Imported files are untrusted personal records; they are never written to cloud automatically. Scores are recalculated and cultural criteria must pass the server registry review gate.')
    if active() and active().state.value=='completed' and st.session_state.get('cloud') and prefs['history'] and active().mode=='live':
        if st.button('Retry saving current result to account'):
            def save(): st.session_state.cloud.save(active(),prefs['transcripts']); st.session_state.saved.add(active().id)
            handle(save); st.rerun()
        if active().id in st.session_state.saved: st.success('Account write confirmed for this attempt.')
    delete=st.checkbox('I want to delete all attempt records in this session and my connected account')
    if st.button('Delete attempt history',disabled=not delete):
        def clear():
            if st.session_state.get('cloud'): st.session_state.cloud.delete()
            st.session_state.repo.delete(); st.session_state.attempt=None; st.session_state.saved.clear(); st.session_state.review_id=None
            clear_norm_data()
            from .feedback_rating import clear_rating_widgets
            clear_rating_widgets()
        handle(clear); st.rerun()
    st.caption('Deletion removes transcripts, scorecards, feedback and metadata in scope, including the current session attempt. Downloaded exports and copies you shared are outside the app’s control. Your authentication account remains.')
    if st.checkbox('Show developer diagnostics'):
        a=active()
        st.json({'mode':a.mode if a else None,'state':a.state.value if a else None,'calls_used':a.calls_used if a else 0,'reserved_output_tokens':a.output_tokens_used if a else 0,'model':settings.groq_model,'cultural_registry':'draft-1.0; no approved cultural criteria'})
    render_error()
