"""Presentation only: local animated personas and evidence-aware interactive charts."""
from html import escape
import altair as alt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_shadcn_ui as shadcn
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.metric_cards import style_metric_cards
from .score_theme import score_color,apply_chart_theme,legend_html,CATEGORY_COLORS,summary_html

PALETTE = {'demo': '#b56bff', 'live': '#00f5ff'}
CHART_CONFIG = {'displaylogo': False, 'scrollZoom': False}


def metric_cards(items, key):
    for i, (col, item) in enumerate(zip(st.columns(len(items)), items)):
        with col:
            category={'Communication estimate':'communication','Scenario adaptation estimate':'adaptation'}.get(item[0])
            if category:st.markdown(summary_html(*item,category),unsafe_allow_html=True)
            else:shadcn.metric_card(title=item[0], content=str(item[1]), description=item[2], key=f'{key}-{i}')


def persona_html(label, role, state, partner=False, motion=True):
    """Escape every user/model string; SVG uses no remote assets or scripts."""
    color = '#b56bff' if partner else '#00f5ff'
    return f'''<div class="persona {'partner' if partner else 'learner'} {'motion' if motion else ''} {escape(state, quote=True)}">
    <svg class="persona-figure" viewBox="0 0 120 120" role="img" aria-label="{escape(label, quote=True)} avatar">
    <circle cx="60" cy="60" r="56" fill="{color}" opacity=".10"/>
    <path d="M25 110 Q25 73 60 73 Q95 73 95 110" fill="{color}"/>
    <g class="persona-head"><circle cx="60" cy="49" r="26" fill="#f2c9a5"/>
    <path d="M34 45 Q30 16 60 20 Q87 19 86 44 Q74 29 57 35 Q45 40 34 45" fill="#25354d"/>
    <g class="persona-eyes"><circle cx="50" cy="49" r="2.5" fill="#25354d"/><circle cx="70" cy="49" r="2.5" fill="#25354d"/></g>
    <path d="M52 61 Q60 68 68 61" fill="none" stroke="#80574d" stroke-width="2.5" stroke-linecap="round"/></g>
    <path class="persona-arm" d="M85 86 Q107 82 103 64" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
    </svg><div><strong>{escape(label)}</strong><p>{escape(role)}</p><span class="persona-status">{escape(state.replace('-', ' ').capitalize())}</span></div></div>'''


def personas(a=None, complete=False):
    motion = st.session_state.prefs.get('animations', True)
    partner_state = 'ready'
    if complete: partner_state = 'reflection'
    elif a and a.pending_reply: partner_state = 'reply-pending'
    elif a and a.state.value == 'evaluating': partner_state = 'reflection'
    elif a and a.state.value == 'conversing': partner_state = 'listening'
    roles = (a.config.my_role, a.config.other_role) if a else ('Communication learner', 'Practice companion')
    left, right = st.columns(2)
    with left: st.markdown(persona_html('You', roles[0], 'reflection' if complete else 'ready', motion=motion), unsafe_allow_html=True)
    with right: st.markdown(persona_html('Conversation partner', roles[1], partner_state, True, motion), unsafe_allow_html=True)
    st.caption('Illustrated role-play personas. Animation shows conversation state; it does not infer emotions or cultural traits.')
    add_vertical_space(1)


def activity_chart(rows, key='activity'):
    if not rows:
        st.info('Your activity chart will appear after you save a practice attempt.')
        return
    df = pd.DataFrame(rows)
    df['Practice type'] = df['mode'].map({'demo': 'Scripted demo', 'live': 'Live practice'})
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X('state:N', title='Attempt status'), y=alt.Y('count():Q', title='Saved attempts', axis=alt.Axis(tickMinStep=1)),
        color=alt.Color('Practice type:N', scale=alt.Scale(domain=['Scripted demo', 'Live practice'], range=['#b56bff', '#00f5ff'])),
        tooltip=['Practice type:N', 'state:N', alt.Tooltip('count():Q', title='Attempts')]
    ).properties(height=250)
    st.altair_chart(chart, use_container_width=True, key=key)
    st.caption('Saved practice activity. Completion counts do not measure cultural performance.')


def dimension_chart(card, mode, key, empty_message='Performance chart awaits reviewed evidence. Missing dimensions remain unscored.'):
    available = [d for d in card.dimensions if d.status == 'scored' and d.value is not None] if mode == 'live' else []
    if not available:
        st.info(empty_message)
        return
    fig = go.Figure(go.Bar(x=[d.value for d in available], y=[d.dimension for d in available], orientation='h', marker_color=[score_color(d.dimension) for d in available], text=[f'{d.value:.1f}/5' for d in available], textposition='inside', textfont={'color':'#071020','size':14}, hovertemplate='%{y}<br>%{x:.1f} / 5<extra></extra>'))
    fig.update_layout(xaxis={'range': [0, 5], 'title': 'Evidence-based dimension score / 5'}, yaxis={'autorange': 'reversed'}, height=360, margin={'l': 10, 'r': 20, 't': 20, 'b': 40})
    apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True, key=key, config=CHART_CONFIG, theme=None)
    st.markdown(legend_html([d.dimension for d in available]),unsafe_allow_html=True)
    st.dataframe([{'Dimension': d.dimension, 'Score / 5': d.value} for d in available], hide_index=True)


def trend_chart(items, key):
    ordered = sorted(items, key=lambda a: (a.created_at, a.id))
    fig = go.Figure(go.Scatter(x=list(range(1, len(ordered)+1)), y=[a.scorecard.overall for a in ordered], mode='lines+markers', line={'color': CATEGORY_COLORS['reviewed'], 'width': 3}, customdata=[a.id[:8] for a in ordered], hovertemplate='Practice %{x}<br>Score %{y} / 100<br>Attempt %{customdata}<extra></extra>'))
    fig.update_layout(xaxis={'title': 'Chronological comparable practice', 'dtick': 1}, yaxis={'title': 'Overall score / 100', 'range': [0, 100]}, height=300, margin={'l': 10, 'r': 20, 't': 20, 'b': 40})
    apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True, key=key, config=CHART_CONFIG, theme=None)


def norm_chart(report, key):
    rows = [{'Turn': t['turn_id'][:8], 'Norm': str(i+1), 'Label': label.replace('_', ' '), 'Relative score': value}
            for t in report['turns'] for i, hit in enumerate(t['matches']) for label, value in (hit.get('scores') or {}).items()]
    if not rows: return
    df = pd.DataFrame(rows)
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Relative score:Q', scale=alt.Scale(domain=[0, 1]), title='Relative zero-shot label score'),
        y=alt.Y('Label:N'), color=alt.Color('Label:N', scale=alt.Scale(domain=['adherence','violation','unclear'],range=['#39FF14','#FF5078','#FFF01F']),legend=None),
        tooltip=['Turn:N', 'Norm:N', 'Label:N', alt.Tooltip('Relative score:Q', format='.3f')]
    ).facet(row=alt.Row('Turn:N', title='Learner turn'), column=alt.Column('Norm:N', title='Retrieved norm')).resolve_scale(y='shared')
    st.altair_chart(chart, use_container_width=True, key=key)
    st.caption('Experimental model label scores, not calibrated probabilities or learner performance. Each norm is shown separately.')


def style_metrics():
    style_metric_cards(background_color='#ffffff', border_color='#e6e4ee', border_left_color='#00f5ff', border_radius_px=14, box_shadow=False)
