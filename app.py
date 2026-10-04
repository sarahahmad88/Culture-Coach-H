"""Thin Streamlit navigation entry point."""
from pathlib import Path
import streamlit as st
from config import Settings,SAFEGUARD
from repository import SessionRepository
from ui import dashboard,progress,learn,settings
from ui.components import training_page
st.set_page_config(page_title='Cross-Cultural Practice',page_icon='🌍',layout='wide')
st.markdown('<style>'+Path(__file__).with_name('styles.css').read_text()+'</style>',unsafe_allow_html=True)
initial={'page':'Dashboard','repo':SessionRepository(),'attempt':None,'cloud':None,'saved':set(),'prefs':{'culture':'Pakistan','level':'Intermediate','history':False,'transcripts':False,'evidence':True},'completed_lessons':set(),'error':'','review_id':None,'server_settings':Settings.load(st.secrets)}
for k,v in initial.items():
    if k not in st.session_state: st.session_state[k]=v
if 'pending_page' in st.session_state:
    st.session_state.page=st.session_state.pop('pending_page')
    st.session_state.navigation=st.session_state.page
from ui.design import brand,sidebar_intro,sidebar_footer
brand()
if 'navigation' not in st.session_state:st.session_state.navigation=st.session_state.page
with st.sidebar:
    sidebar_intro()
    page=st.radio('Navigation',['Dashboard','Start Training','Progress','Learn','Settings'],index=0,key='navigation')
    sidebar_footer(st.session_state.prefs['level'],st.session_state.cloud)
if page!=st.session_state.page: st.session_state.page=page
with st.empty().container():
    {'Dashboard':dashboard.render,'Start Training':training_page,'Progress':progress.render,'Learn':learn.render,'Settings':settings.render}[st.session_state.page]()
st.divider(); st.caption(SAFEGUARD)
