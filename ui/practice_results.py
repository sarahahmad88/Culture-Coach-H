"""Two distinct estimated practice scores plus source and evidence displays."""
import plotly.graph_objects as go
import streamlit as st
from config import DIMENSIONS
from .visuals import dimension_chart,CHART_CONFIG
from .score_theme import CATEGORY_COLORS,legend_html,rating_html,apply_chart_theme

def profile(rubric,key):
    st.caption('National reference data is separate from individual preferences and learner scores.')
    st.markdown(legend_html(DIMENSIONS),unsafe_allow_html=True)
    st.dataframe([{'Dimension':d,'Country reference / 100':value,'Persona expectation':next((c.expectation for c in rubric.adaptation if c.dimension==d),'Unavailable in this dataset')}
                  for d,value in zip(DIMENSIONS,rubric.country_scores)],hide_index=True,width='stretch')
    st.caption(f'{rubric.country} · source country: {rubric.source_country} · {rubric.reference_version} · {rubric.profile_style}')
    st.markdown('[Original Hofstede reference source]('+rubric.reference_source+')')
    st.caption('Authored simulation mapping: <40 lower band, 40–60 middle band, >60 higher band. Contrasting profiles reverse the lower/higher authored preferences. These bands are design choices, not validated personality predictions. Missing country-specific dimensions are not replaced by regional averages. UK uses the source label Great Britain.')

def render(a):
    scores=a.practice_scores
    if not scores:
        st.info('This older attempt has no frozen practice rubric. Start a new practice to get the two score panels.')
        return
    left,right=st.columns(2)
    for col,card,title,key in [(left,scores.communication,'AI-estimated communication score','communication'),(right,scores.adaptation,'Experimental Hofstede-informed scenario adaptation','adaptation')]:
        with col:
            with st.container(key='score-'+key):
                st.subheader(title)
                st.markdown(legend_html([d.dimension for d in card.dimensions]),unsafe_allow_html=True)
                st.metric('Overall / 100',str(card.overall) if card.overall is not None else 'Not scored')
                available=sum(d.status!='not_applicable' for d in card.dimensions)
                scored=sum(d.value is not None for d in card.dimensions)
                st.caption(f'Evidence coverage: {card.coverage:.0%} · {scored}/{available} available criteria scored')
                if key=='adaptation':st.caption(f'Country reference coverage: {available}/6 dimensions. Unavailable references are N/A.')
                dimension_chart(card,a.mode,key+'-'+a.id,empty_message='No numerical practice estimate yet. Demo responses and missing evidence remain unscored.')
                with st.expander('Ratings and explanations'):
                    for d in card.dimensions:
                        st.markdown(rating_html(d.dimension,d.value,d.status),unsafe_allow_html=True)
                        st.caption(d.explanation)
    st.caption('Equal criterion weights. Python calculates overall = mean of available ratings ÷ 5 × 100. Missing evidence is never zero. These are unvalidated AI practice estimates; neither changes reviewed cultural scores or level recommendations.')
    if a.mode=='demo':st.info('Scripted demo illustrates the panels without assessing your responses. Switch to Live Groq AI for estimated practice scores.')
    with st.expander('Persona grounding and country reference values'):
        profile(a.scenario.practice_rubric,'profile-'+a.id)
    if st.session_state.prefs['evidence']:
        by_id={t.id:t for t in a.transcript}
        with st.expander('Practice scoring evidence'):
            for rating in [*a.evaluation.communication_ratings,*a.evaluation.adaptation_ratings]:
                st.write('**'+rating.criterion_id+'** · '+rating.reason)
                for ident in rating.evidence_turn_ids:
                    st.caption('Learner turn '+ident[:8]);st.write(by_id[ident].text)
                cue=getattr(rating,'partner_cue_turn_id',None)
                if cue:st.caption('Preceding partner cue '+cue[:8]);st.write(rating.partner_cue_quote)

def progress(attempts,mode,level,scenario):
    st.subheader('Estimated practice score trends')
    found=False
    for kind,title in [('communication','Communication'),('adaptation','Hofstede-informed adaptation')]:
        eligible=[a for a in attempts if a.mode=='live' and mode!='demo' and a.state.value=='completed' and a.scenario and a.practice_scores and getattr(a.practice_scores,kind).overall is not None and (level=='All' or a.config.level==level) and (scenario=='All' or a.config.template_id==scenario)]
        groups={}
        for a in eligible:groups.setdefault((a.scenario.id,a.config.level,a.practice_scores.rubric_version),[]).append(a)
        for group,items in groups.items():
            if len(items)<2:continue
            found=True;items=sorted(items,key=lambda a:(a.created_at,a.id))
            st.write(title+' · same frozen persona/scenario, difficulty and rubric')
            fig=go.Figure(go.Scatter(x=list(range(1,len(items)+1)),y=[getattr(a.practice_scores,kind).overall for a in items],mode='lines+markers',line={'color':CATEGORY_COLORS[kind],'width':3},marker={'size':9,'color':CATEGORY_COLORS[kind]},hovertemplate='Practice %{x}<br>Estimate %{y} / 100<extra></extra>'))
            fig.update_layout(yaxis={'range':[0,100],'title':title+' / 100'},xaxis={'title':'Chronological comparable practice','dtick':1},height=280)
            apply_chart_theme(fig)
            st.plotly_chart(fig,use_container_width=True,key='practice-trend-'+kind+'-'+group[0],config=CHART_CONFIG,theme=None)
            st.dataframe([{'Attempt':a.id[:8],'Estimate / 100':getattr(a.practice_scores,kind).overall,'Coverage':getattr(a.practice_scores,kind).coverage} for a in items],hide_index=True)
    if not found:st.caption('Save at least two scored live attempts with the same frozen scenario, persona, difficulty and rubric to see a comparable trend. Demo activity is not performance.')
