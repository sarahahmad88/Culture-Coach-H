import streamlit as st
from uuid import uuid4
from schemas import State
from session_manager import transition
from .components import active,controller,handle,render_error,record

def render():
    a=active()
    st.title('Practice your conversation')
    if a.gemini_fallback_used:st.caption('Gemini fallback was used after a Groq rate or request-size limit in this practice.')
    elif a.secondary_groq_used:st.caption('A second Groq key was used after a rate limit in this practice.')
    from .visuals import personas,dimension_chart,style_metrics
    personas(a)
    st.caption(f'{a.config.my_role} → {a.config.other_role} · {a.config.my_culture} → {a.config.other_culture} · {a.config.context} · {a.config.level} · {a.mode}')
    with st.expander('Scenario and objective'): st.write(a.scenario.brief); st.write(a.scenario.objective)
    if a.scenario.practice_rubric:
        with st.expander('Fictional partner preferences'):
            for criterion in a.scenario.practice_rubric.adaptation:st.write(criterion.label+': '+criterion.expectation)
            st.caption('Adaptation estimates use expectations actually expressed in partner turns. You may negotiate and maintain reasonable boundaries.')
    st.progress(a.rounds/a.limit,text=f'{a.rounds} of {a.limit} learner responses accepted')
    for t in a.transcript:
        with st.chat_message('user' if t.role=='learner' else 'assistant'):
            st.caption('You · '+a.config.my_role if t.role=='learner' else 'Conversation Partner · '+a.config.other_role)
            st.write(t.text)
    render_error()
    if a.state==State.evaluating:
        st.info('Conversation closed. Your final response was accepted; no extra question is required.')
        if st.button('Retry evaluation and feedback',type='primary'):
            handle(lambda:controller().finish(a))
            if a.state==State.completed: record(a)
            st.rerun()
    elif a.pending_reply:
        st.warning('Your response is saved in this session. The partner reply is pending.')
        if st.button('Retry partner reply',type='primary'): handle(lambda:controller().reply(a)); st.rerun()
    else:
        if a.config.level=='Beginner' or (a.config.level=='Intermediate' and a.rounds in [0,3,6]):
            with st.expander('Practice hint',expanded=a.config.level=='Beginner'): st.write('Name the goal, explain your concern or boundary, and invite a practical option. You can use your own words.')
        with st.form('composer-'+a.id+'-'+str(a.rounds),clear_on_submit=True):
            text=st.text_area('Your response',max_chars=3000,height=110)
            send=st.form_submit_button('Send',type='primary')
        if send:
            handle(lambda:controller().submit(a,text,str(uuid4())))
            if a.state==State.completed: record(a)
            st.rerun()
    if st.button('Exit practice and mark incomplete'):
        transition(a,State.incomplete); record(a); st.rerun()
