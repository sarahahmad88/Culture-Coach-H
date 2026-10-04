"""Deterministic weighted arithmetic; ratings must pass evidence and approval gates."""
import math
from config import DIMENSIONS, PROGRESSION
from schemas import DimensionScore, Scorecard, State

def aggregate(values,weights=None):
    valid={d:v for d,v in values.items() if v is not None}
    if not valid: return None
    weights=weights or {d:1 for d in valid}
    for d,v in valid.items():
        if not math.isfinite(v) or not 0<=v<=5 or not math.isfinite(weights.get(d,1)) or weights.get(d,1)<=0: raise ValueError('Invalid score/weight')
    return round(100*sum(weights.get(d,1)*v for d,v in valid.items())/(5*sum(weights.get(d,1) for d in valid)))

def validate_evaluation(a,e,r):
    turns={t.id:t.text for t in a.transcript if t.role=='learner'}
    seen=set()
    for x in e.evidence:
        if x.turn_id not in turns or x.quote not in turns[x.turn_id]: raise ValueError('Evidence does not match learner transcript')
        if any(d not in a.scenario.relevant_dimensions for d in x.dimension_mappings): raise ValueError('Unsupported dimension mapping')
        seen.add(x.turn_id)
    if seen!=set(turns): raise ValueError('Every learner turn requires evidence analysis')
    rating_ids=[x.criterion_id for x in e.ratings]
    if len(rating_ids)!=len(set(rating_ids)): raise ValueError('Duplicate criterion')
    if set(rating_ids)!=set(a.scenario.criterion_ids): raise ValueError('Criteria differ from frozen rubric')
    for x in e.ratings:
        c=r['criteria'].get(x.criterion_id)
        if not c or c['status']!='approved' or c['version']!=a.scenario.rubric_version or not c.get('reviewer') or not c.get('source') or set(c.get('anchors',{}))!=set(map(str,range(6))): raise ValueError('Criterion lacks review or behavior anchors')
        if c['dimension'] not in a.scenario.relevant_dimensions: raise ValueError('Irrelevant criterion')
        if x.value is not None:
            if not x.evidence_turn_ids or any(i not in seen for i in x.evidence_turn_ids) or not x.reason.strip(): raise ValueError('Rating requires evidence and justification')
            if any(not any(v.turn_id==i and c['dimension'] in v.dimension_mappings for v in e.evidence) for i in x.evidence_turn_ids): raise ValueError('Rating evidence must map to its dimension')
    from practice_scoring import validate_practice
    validate_practice(a,e)
    return e

def score(scenario,e,r):
    values={}; dimensions=[]
    for d in DIMENSIONS:
        criteria=[r['criteria'][x] for x in scenario.criterion_ids if x in r['criteria'] and r['criteria'][x]['dimension']==d and r['criteria'][x]['status']=='approved']
        ratings={x.criterion_id:x for x in e.ratings}
        applicable=d in scenario.relevant_dimensions
        valid=[(ratings[c['id']].value,c.get('weight',1)) for c in criteria if c['id'] in ratings and ratings[c['id']].value is not None]
        if valid:
            if any(w<=0 or not math.isfinite(w) for _,w in valid): raise ValueError('Invalid criterion weight')
            value=sum(v*w for v,w in valid)/sum(w for _,w in valid)
            values[d]=value; status='scored'; explanation='Weighted mean of reviewed criteria with transcript evidence.'
        else:
            value=None; status='insufficient_evidence' if applicable else 'not_applicable'
            explanation='No reviewed cultural criterion or sufficient evidence.' if applicable else 'Not relevant to this scenario.'
        dimensions.append(DimensionScore(dimension=d,value=value,status=status,explanation=explanation))
    n=len(scenario.relevant_dimensions)
    return Scorecard(overall=aggregate(values,r.get('dimension_weights')),coverage=len(values)/n if n else 0,dimensions=dimensions)

def recommendation(attempts,level):
    from config import LEVELS
    eligible=[a for a in attempts if a.state==State.completed and a.config.level==level and a.mode=='live' and a.scorecard and a.scorecard.overall is not None and a.scorecard.coverage>=PROGRESSION['coverage']]
    levels=list(LEVELS)
    if len(eligible)>=PROGRESSION['attempts'] and sum(a.scorecard.overall for a in eligible[-3:])/3>=PROGRESSION['average']:
        return levels[min(levels.index(level)+1,2)]
    return level
