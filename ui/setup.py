import streamlit as st
from schemas import Configuration,Attempt,State
from config import LEVELS,CULTURES
from .components import active,controller,handle,render_error

def render():
    st.title('Define your learning context')
    st.caption('Roles are restricted to Junior employee / Senior manager for Workplace, and Student / Fellow student for University.')
    st.caption('Eight required inputs • reviewed cultural scoring is unavailable • draft templates')
    preset=st.selectbox('Practice template',['Deadline concern · Workplace','Group responsibilities · University'])
    deadline=preset.startswith('Deadline')
    with st.form('setup'):
        cols=st.columns(2)
        cultures=CULTURES
        mine=cols[0].selectbox('My culture',cultures,index=cultures.index(st.session_state.prefs['culture']))
        other=cols[1].selectbox("Other person’s culture",cultures,index=1 if deadline else 3)
        context=st.selectbox('Context / Setting',['Workplace','University'],index=0 if deadline else 1)
        situation=st.text_input('Situation',value='Project meeting about an unrealistic two-week deadline' if deadline else 'Group project with unclear responsibilities')
        my_role=cols[0].text_input('My role',value='Junior employee' if deadline else 'Student')
        other_role=cols[1].text_input("Other person’s role",value='Senior manager' if deadline else 'Fellow student')
        goal=st.selectbox('Communication goal',['Raise a concern','Disagree respectfully','Negotiate'] if deadline else ['Request assistance','Give feedback','Resolve conflict','Build trust'],index=0)
        level=st.radio('Experience level',list(LEVELS),index=list(LEVELS).index(st.session_state.prefs['level']),horizontal=True)
        for col,(name,rounds) in zip(st.columns(3),LEVELS.items()):
            with col: st.info(f'{name}\n\n{rounds} responses\n\n'+{'Beginner':'Simple language · high guidance','Intermediate':'Moderate ambiguity · occasional guidance','Advanced':'Competing objectives · minimal guidance'}[name])
        persona_style=st.radio('Persona profile',['Country-informed fictional profile','Contrasting fictional profile'],horizontal=True)
        st.caption('Profiles use the original Hofstede reference matrix where available. Missing data stays missing. Contrasting profiles practice individual variation. Live scores are AI estimates, separate from reviewed cultural scoring.')
        mode=st.radio('Mode',['Scripted demo (no credentials)','Live Groq AI'],horizontal=True)
        st.info('Preview: select roles and a goal, then review and edit the scenario brief before beginning. Same-culture practice is allowed. Workplace and University are the supported draft contexts.')
        generate=st.form_submit_button('Generate Scenario',type='primary')
    if generate:
        def prepare():
            c=Configuration(my_culture=mine,other_culture=other,context=context,situation=situation,my_role=my_role,other_role=other_role,goal=goal,level=level,template_id='deadline' if deadline else 'group_project',persona_style='country_informed' if persona_style.startswith('Country') else 'contrast')
            if mode.startswith('Live') and not st.session_state.server_settings.groq_api_key:
                from diagnostics import StageError
                raise StageError('Setup','missing key','Add GROQ_API_KEY in server Secrets or select Scripted demo.')
            st.session_state.attempt=Attempt(config=c,mode='demo' if mode.startswith('Scripted') else 'live')
            controller().prepare(active())
        handle(prepare); st.rerun()
    render_error()
