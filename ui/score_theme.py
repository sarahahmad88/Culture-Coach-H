"""Stable neon identities for score categories, communication criteria and dimensions."""
from html import escape
from config import DIMENSIONS
CATEGORY_COLORS={'communication':'#00D9FF','adaptation':'#F000FF','reviewed':'#7451CA'}
SCORE_COLORS={
    'Clarity':'#00F5FF',
    'Respect and boundaries':'#39FF14',
    'Supporting reasons':'#FFF01F',
    'Perspective-taking':'#FF2EC4',
    'Problem-solving':'#FF8C1A',
    DIMENSIONS[0]:'#B56BFF',
    DIMENSIONS[1]:'#00FFB3',
    DIMENSIONS[2]:'#FF5078',
    DIMENSIONS[3]:'#4D9EFF',
    DIMENSIONS[4]:'#F5B8FF',
    DIMENSIONS[5]:'#C9FF00',
}
CHART_BACKGROUND='#FFFFFF'
CHART_FOREGROUND='#252A43'

def score_color(label):return SCORE_COLORS.get(label,'#252A43')
def legend_html(labels):
    return '<div class="neon-legend" aria-label="Score color legend">'+''.join(
        '<span class="neon-legend-item"><i aria-hidden="true" style="background:'+score_color(label)+'"></i>'+escape(label)+'</span>' for label in labels)+'</div>'
def rating_html(label,value,status):
    display=f'{value:.1f}/5' if value is not None else ('N/A' if status=='not_applicable' else 'Insufficient evidence')
    return '<div class="neon-rating" style="--score-accent:'+score_color(label)+'"><span>'+escape(label)+'</span><strong>'+escape(display)+'</strong></div>'
def apply_chart_theme(fig):
    fig.update_layout(paper_bgcolor=CHART_BACKGROUND,plot_bgcolor=CHART_BACKGROUND,font={'color':CHART_FOREGROUND},colorway=list(SCORE_COLORS.values()),hoverlabel={'bgcolor':'#FFFFFF','font_color':CHART_FOREGROUND})
    fig.update_xaxes(gridcolor='#E6E4EF',zerolinecolor='#C9C7D8',tickfont={'color':CHART_FOREGROUND},title_font={'color':CHART_FOREGROUND})
    fig.update_yaxes(gridcolor='#E6E4EF',zerolinecolor='#C9C7D8',tickfont={'color':CHART_FOREGROUND},title_font={'color':CHART_FOREGROUND})
    return fig

def summary_html(title,value,description,category):
    color=CATEGORY_COLORS[category]
    return '<div class="neon-summary" style="--category-accent:'+color+'"><div class="neon-summary-title">'+escape(title)+'</div><strong>'+escape(str(value))+'</strong><p>'+escape(description)+'</p></div>'
