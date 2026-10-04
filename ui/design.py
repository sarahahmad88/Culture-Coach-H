"""Local vector illustration and layout accents; no external image requests."""
import streamlit as st
from html import escape

def brand():
    st.markdown('<div class="app-topbar"><span class="topbar-wordmark">CROSS<span> / </span>CULTURE</span><span class="topbar-tag">PRACTICE YOUR NEXT CONVERSATION</span><span class="topbar-pill">14 countries · one conversation at a time</span></div>',unsafe_allow_html=True)

def sidebar_intro():
    st.markdown('<div class="sidebar-brand"><div class="brand-orbit" aria-hidden="true">✦</div><div>CROSS /<br><span>CULTURE</span></div></div><p class="sidebar-kicker">YOUR PRACTICE SPACE</p>',unsafe_allow_html=True)

def sidebar_footer(level,cloud):
    st.markdown('<div class="sidebar-level"><span class="sidebar-kicker">YOUR PACE</span><strong>'+escape(level)+'</strong><span>Practice. Reflect. Try again.</span></div>',unsafe_allow_html=True)
    st.caption('Authenticated history enabled' if cloud else 'Session-only history · enable saving in Settings. Session records do not survive a restart.')

def illustration():
    return '''<svg class="hero-world" viewBox="0 0 440 300" role="img" aria-label="Playful illustration of conversations connecting across a globe">
    <defs><linearGradient id="worldGlow" x1="0" x2="1"><stop stop-color="#00f5ff"/><stop offset="1" stop-color="#b56bff"/></linearGradient></defs>
    <circle cx="231" cy="155" r="99" fill="#ffffff" stroke="url(#worldGlow)" stroke-width="2"/>
    <ellipse cx="231" cy="155" rx="46" ry="99" fill="none" stroke="#b4b3d5"/>
    <ellipse cx="231" cy="155" rx="99" ry="35" fill="none" stroke="#b4b3d5"/>
    <path d="M132 155h198M150 100h162M150 210h162" stroke="#b4b3d5" fill="none"/>
    <ellipse cx="231" cy="155" rx="161" ry="51" transform="rotate(-24 231 155)" fill="none" stroke="#b56bff" stroke-width="2" stroke-dasharray="6 8"/>
    <g class="hero-float"><rect x="47" y="58" width="130" height="59" rx="17" fill="#c9ff00"/><path d="M142 117v17l-20-17" fill="#c9ff00"/><circle cx="82" cy="88" r="4" fill="#0b1020"/><circle cx="110" cy="88" r="4" fill="#0b1020"/><circle cx="138" cy="88" r="4" fill="#0b1020"/></g>
    <g class="hero-float-delayed"><rect x="288" y="169" width="113" height="58" rx="17" fill="#ff2ec4"/><path d="M308 227v17l22-17" fill="#ff2ec4"/><path d="M312 189h65M312 203h44" stroke="#0b1020" stroke-width="5" stroke-linecap="round"/></g>
    <circle cx="322" cy="51" r="11" fill="#00f5ff"/><circle cx="118" cy="229" r="8" fill="#ff8c1a"/>
    <path d="M357 95v24m-12-12h24M70 167v18m-9-9h18" stroke="#f5b8ff" stroke-width="3"/>
    <path d="M221 92l13 11-6 21-18-5-12-14zM252 132l29 7 9 25-13 33-21-13-11-32zM190 160l22 10-6 32-17-3-15-22z" fill="#00ffb3" opacity=".72"/>
    </svg>'''

def dashboard_hero():
    motion=' hero-motion' if st.session_state.prefs.get('animations',True) else ''
    with st.container(key='dashboard-hero'):
        st.markdown('<div class="hero-copy'+motion+'"><div class="eyebrow">SMALL PRACTICE. BIGGER PERSPECTIVE.</div><h1>New perspectives.<br><span>Better conversations.</span></h1><p>Build confidence across cultures. Explore a situation, meet a fictional partner, and find your next step.</p>'+illustration()+'<div class="hero-tags"><span>✦ Your pace</span><span>↗ Evidence-led reflection</span><span>◈ A fresh perspective</span></div></div>',unsafe_allow_html=True)
        return st.button('Start Training',type='primary')

def learning_loop(go):
    st.markdown('<div class="section-eyebrow">YOUR LEARNING LOOP</div>',unsafe_allow_html=True)
    for col,(symbol,title,text,label,page) in zip(st.columns(3),[
        ('01','Meet your next challenge','Choose a situation and a fictional partner.','Choose a scenario','Start Training'),
        ('02','See what is working','Explore your communication and adaptation estimates.','Explore your progress','Progress'),
        ('03','Take one idea with you','Find a useful lesson, then try it in practice.','Browse lessons','Learn')]):
        with col:
            with st.container(border=True,key='loop-'+symbol):
                st.markdown('<div class="loop-number">'+symbol+'</div><h3>'+title+'</h3><p class="loop-copy">'+text+'</p>',unsafe_allow_html=True)
                if st.button(label,key='loop-action-'+symbol,width='stretch'):go(page)
