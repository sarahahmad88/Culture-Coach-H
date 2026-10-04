import streamlit as st
from schemas import State
from session_manager import retry
from .components import go

def render(a):
    st.title('Your feedback & next step')
    st.caption(f'{a.config.level} · {a.rounds}/{a.limit} responses · {a.mode} · attempt {a.id[:8]}')
    if a.gemini_fallback_used:st.caption('Gemini fallback was used during this practice after a Groq rate or request-size limit. Estimates may vary between models.')
    elif a.secondary_groq_used:st.caption('A second Groq key was used after a rate limit during this practice.')
    if a.state!=State.completed: st.warning('Incomplete attempt — excluded from completion and progression.'); return
    card=a.scorecard
    from .visuals import personas,dimension_chart,style_metrics
    personas(a, complete=True)
    style_metrics()
    from .practice_results import render as show_practice
    show_practice(a)
    with st.expander('Reviewed cultural assessment — separate and inactive'):
        st.metric('Overall cultural adaptability',f'{card.overall}/100' if card.overall is not None else 'Not enough evidence to score')
        st.caption(f'Reviewed scoring coverage: {card.coverage:.0%}. No reviewed cultural criteria are available. The two practice estimates above use authored rubrics, not validated cultural judgments.')
        for d in card.dimensions:
            st.write(d.dimension+' — '+(f'{d.value:.1f}/5' if d.value is not None else ('N/A' if d.status=='not_applicable' else 'Insufficient evidence')))
        st.caption('Masculinity/Achievement Orientation is a legacy framework label; it does not imply gender-based personality expectations.')
    st.subheader('Strengths')
    for x in a.feedback.strengths: st.write('• '+x)
    st.subheader('Areas to explore')
    for x in a.feedback.improvements: st.write('• '+x)
    st.subheader('One possible response')
    st.info(a.feedback.alternative)
    st.write(a.feedback.explanation)
    st.caption(a.evaluation.uncertainty)
    if st.session_state.prefs['evidence']:
        with st.expander('Evidence ledger — every learner response'):
            for e in a.evaluation.evidence:
                st.write('**Turn '+e.turn_id[:8]+'**'); st.code(e.quote,language=None)
                st.write('Observation: '+e.observation); st.write('Interpretation: '+e.interpretation); st.caption('Uncertainty: '+e.uncertainty)
                if e.dimension_mappings: st.caption('Exploratory dimension mappings (unreviewed): '+', '.join(e.dimension_mappings))
    from .norm_analysis import render as show_norms
    show_norms(a)
    from .feedback_rating import render as rate_feedback
    rate_feedback(a)
    if st.button('Try the same scenario again',type='primary'):
        st.session_state.attempt=retry(a); go('Start Training')
    if st.button('Open targeted lessons'):
        st.session_state.lesson_filter=a.feedback.lesson_ids; go('Learn')
    if st.button('New / similar practice'):
        st.session_state.attempt=None; go('Start Training')
    if st.button('See progress'): go('Progress')
