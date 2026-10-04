import json
from pathlib import Path
from config import DIMENSIONS
DATA=Path(__file__).parent/'data'/'registry.json'
def registry():
    r=json.loads(DATA.read_text())
    for country in r['cultures'].values():
        if any(v is not None for v in country['scores'].values()) and country['status']!='approved': raise ValueError('Unreviewed numeric cultural data')
    return r

def context_for(config):
    r=registry(); t=r['templates'][config.template_id]
    return {'registry_version':r['version'],'record_ids':[config.template_id], 'source':t['source'],'supported_contexts':[t['context']], 'guidance':['Ask this individual about expectations; nationality does not determine their communication style.','Raise legitimate concerns clearly and respectfully; preserve boundaries.'], 'relevant_dimensions':t['candidate_dimensions'],'limitations':['No approved country scores or culture-specific scoring criteria are supplied.','Templates and lessons are unreviewed drafts; general communication feedback only.']}
def template_for(config): return registry()['templates'][config.template_id]
def lessons(): return registry()['lessons']
