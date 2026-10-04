import streamlit as st
from .components import all_attempts,summaries,attempt_label,handle
from scoring import recommendation
from schemas import State

def render():
    st.title('Your practice progress')
    attempts=all_attempts()
    level=st.selectbox('Filter by level',['All','Beginner','Intermediate','Advanced'])
    scenario=st.selectbox('Filter by scenario',['All','deadline','group_project'])
    mode=st.selectbox('Filter by mode',['All','demo','live'])
    rows=[x for x in summaries() if (level=='All' or x['level']==level) and (scenario=='All' or x['template_id']==scenario) and (mode=='All' or x['mode']==mode)]
    from .visuals import activity_chart,trend_chart
    st.subheader('Activity overview')
    activity_chart(rows, 'progress-activity')
    if not rows: st.info('No saved attempts match these filters. Turn on session history in Settings to retain completed practices.')
    else: st.dataframe(rows,hide_index=True,width='stretch')
    from .practice_results import progress as practice_progress
    practice_progress(attempts,mode,level,scenario)
    scored=[a for a in attempts if a.state==State.completed and a.mode=='live' and a.scorecard and a.scorecard.overall is not None and mode!='demo' and (level=='All' or a.config.level==level) and (scenario=='All' or a.config.template_id==scenario)]
    groups={}
    for a in scored: groups.setdefault((a.scenario.id,a.config.level),[]).append(a)
    for key,items in groups.items():
        if len(items)>1:
            st.write('Same frozen scenario, same difficulty: '+items[0].scenario.title)
            trend_chart(items, 'trend-'+key[0]+'-'+key[1])
            st.dataframe([{'Attempt':a.id[:8],**{d.dimension:d.value for d in a.scorecard.dimensions}} for a in items],hide_index=True)
    if not any(len(v)>1 for v in groups.values()): st.caption('Not enough comparable scored attempts for a trend. Demo completions are practice activity, not evidence of improvement.')
    for a in attempts:
        if a.parent_retry_id:
            parent=next((x for x in attempts if x.id==a.parent_retry_id),None)
            if parent and parent.scenario.id==a.scenario.id:
                st.write(f'Exact retry: {parent.id[:8]} → {a.id[:8]} · {a.config.level}')
                if a.scorecard and parent.scorecard and a.scorecard.overall is not None and parent.scorecard.overall is not None: st.write(f'Overall change: {a.scorecard.overall-parent.scorecard.overall:+d}')
                else: st.caption('No numerical comparison is available. Review the two transcripts to reflect on your choices.')
    st.info('Recommended level: '+recommendation(attempts,st.session_state.prefs['level'])+' (draft product rule)')
    if attempts:
        choices={a.id:a for a in attempts}
        selected=st.selectbox('Review a saved attempt',list(choices),format_func=lambda i:attempt_label(choices[i]))
        if st.button('Open selected feedback'):
            st.session_state.review_id=selected
        a=choices.get(st.session_state.get('review_id'))
        if a:
            from .scorecard import render as show
            show(a)
    if st.session_state.get('cloud'):
        if st.button('Load authenticated history'):
            def load():
                remote=st.session_state.cloud.list()
                for a in remote: st.session_state.repo.save(a,True)
                for x in st.session_state.cloud.summaries():
                    if x['id'] not in st.session_state.repo.records: st.session_state.repo.metadata[x['id']]=x
            handle(load); st.rerun()
    from .components import render_error
    render_error()
