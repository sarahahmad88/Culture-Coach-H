import streamlit as st
from knowledge import lessons
from .components import go

def render():
    st.title('Learn one thing. Try it in practice.')
    targeted=st.session_state.get('lesson_filter',[])
    only=st.checkbox('Show targeted recommendations only',value=bool(targeted))
    for lesson in lessons():
        if only and lesson['id'] not in targeted: continue
        with st.expander(lesson['title'],expanded=False):
            st.write(lesson['content']); st.caption(lesson['source']+' · Unreviewed draft')
            done=lesson['id'] in st.session_state.completed_lessons
            if st.button('Completed ✓' if done else 'Mark lesson complete',key=lesson['id'],disabled=done): st.session_state.completed_lessons.add(lesson['id']); st.rerun()
            if st.button('Practice this idea',key='practice-'+lesson['id']): st.session_state.attempt=None; go('Start Training')
