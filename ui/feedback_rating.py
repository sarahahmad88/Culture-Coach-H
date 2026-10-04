"""Learner usefulness rating, kept separate from cultural scores."""
import streamlit as st
from .components import record

def clear_rating_widgets():
    for key in list(st.session_state):
        if key.startswith('feedback-stars-'):
            del st.session_state[key]

def update_rating(a, key):
    value=st.session_state.get(key)
    a.feedback_rating=None if value is None else int(value)+1
    current=st.session_state.get('attempt')
    if current and current.id==a.id:
        current.feedback_rating=a.feedback_rating
    record(a)

def render(a):
    st.subheader('Rate this feedback')
    st.write('How useful was this feedback? Choose one to five stars.')
    key='feedback-stars-'+a.id
    if key not in st.session_state:
        st.session_state[key]=a.feedback_rating-1 if a.feedback_rating is not None else None
    st.feedback('stars',key=key,on_change=update_rating,args=(a,key))
    if a.feedback_rating is not None:
        st.caption(f'Your usefulness rating: {a.feedback_rating}/5. You can change it anytime.')
    st.caption('This rating does not change your performance score. It stays in the current session unless you enable history or export the attempt. With authenticated history enabled, live-attempt ratings are saved to your account under your history preferences.')
