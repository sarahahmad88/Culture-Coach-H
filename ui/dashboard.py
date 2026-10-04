import streamlit as st
from .components import go,summaries,all_attempts,attempt_label
from scoring import recommendation

def render():
    from .design import dashboard_hero,learning_loop
    if dashboard_hero():go('Start Training')
    st.markdown('<div class="section-eyebrow">YOUR PRACTICE, AT A GLANCE</div>',unsafe_allow_html=True)
    rows=[x for x in summaries() if x['mode']=='live' and x['state']=='completed']
    communication=[x['communication_score'] for x in rows if x.get('communication_score') is not None]
    adaptation=[x['adaptation_score'] for x in rows if x.get('adaptation_score') is not None]
    from .visuals import metric_cards,personas,activity_chart
    metric_cards([('Completed live attempts',len(rows),'Saved completed live practice'),
        ('Communication estimate',f'{sum(communication)/len(communication):.0f}/100' if communication else 'Not scored','Average across saved AI-estimated practice scores'),
        ('Scenario adaptation estimate',f'{sum(adaptation)/len(adaptation):.0f}/100' if adaptation else 'Not scored','Experimental; review persona and coverage'),
        ('Recommended level',recommendation(all_attempts(),st.session_state.prefs['level']),'Reviewed-score recommendation gate remains separate')], 'dashboard')
    learning_loop(go)
    st.subheader('Your conversation companions')
    personas()
    st.subheader('Practice activity')
    activity_chart(summaries(), 'dashboard-activity')
    st.caption('Draft recommendation: three completed live scored attempts averaging ≥70 with ≥60% coverage. You may select any level.')
    demo=[x for x in summaries() if x['mode']=='demo' and x['state']=='completed']
    if demo: st.info(f'{len(demo)} scripted demo practice(s) completed. These are separate from live performance.')
    st.subheader('Recent practice')
    attempts=all_attempts()
    if not attempts and not rows and not demo: st.info('Welcome! Your first practice starts with choosing a situation. No history yet.')
    for a in attempts[-3:][::-1]:
        with st.container(border=True):
            st.write(attempt_label(a))
            if st.button('Review attempt',key='dash-'+a.id): st.session_state.review_id=a.id; go('Progress')
    practiced={d.dimension for a in attempts if a.mode=='live' and a.practice_scores for d in a.practice_scores.adaptation.dimensions if d.value is not None}
    st.write('Persona dimensions practiced with evidence: '+(', '.join(practiced) or 'None scored yet'))
    st.subheader('Next practice')
    st.write('Raise a concern with evidence, or agree on responsibilities in a group project.')
