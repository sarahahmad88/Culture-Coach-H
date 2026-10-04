import streamlit as st
from .components import active,controller,handle,render_error

def render():
    a=active(); s=a.scenario
    st.title('Your scenario brief')
    st.subheader(s.title)
    from .visuals import personas,dimension_chart,style_metrics
    personas(a)
    st.info(f'{a.config.my_culture} → {a.config.other_culture} · {a.config.context} · {a.config.level} · {a.limit} learner responses · {a.mode}')
    with st.container(border=True): st.write(s.brief)
    st.write('**Communication objective:** '+s.objective)
    st.write('**Conversation partner:** '+s.character)
    if s.practice_rubric:
        from .practice_results import profile
        with st.expander('This fictional partner’s preferences and reference data',expanded=True):profile(s.practice_rubric,'brief-'+a.id)
    st.write('**Project constraints:**')
    for x in s.constraints: st.write('• '+x)
    with st.expander('Context, sources and limitations',expanded=True):
        for x in a.context_package.guidance: st.write(x)
        for x in a.context_package.limitations: st.caption(x)
        st.caption(a.context_package.source+' · '+a.context_package.registry_version)
        st.caption('Possible relevant dimensions: '+', '.join(s.relevant_dimensions))
    st.caption('The demo uses scripted role-play and reflection prompts. Live mode uses Groq for scenario and conversation generation and evidence-based general feedback. Neither currently offers authoritative cultural scoring.')
    if st.button('Begin Conversation',type='primary'): handle(lambda:controller().begin(a)); st.rerun()
    if st.button('Edit setup'):
        st.session_state.attempt=None; st.rerun()
    render_error()
