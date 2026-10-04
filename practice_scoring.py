"""Authored, experimental practice rubrics; distinct from reviewed cultural scores."""
import json
from pathlib import Path
from config import DIMENSIONS
from schemas import PracticeCriterion,PracticeRubric,PracticeScores,DimensionScore,Scorecard
VERSION='practice-v1.0'
GENERAL=[('clarity','Clarity','State the concern, request or position clearly.'),('respect','Respect and boundaries','Acknowledge the partner while maintaining legitimate boundaries.'),('reasons','Supporting reasons','Give relevant explanations or evidence rather than unsupported assertions.'),('perspective','Perspective-taking','Ask about or respond to this person’s expectations without assuming them.'),('solutions','Problem-solving','Offer feasible options or agree clear next steps consistent with scenario constraints.')]
GENERAL_ANCHORS={
 'clarity':('Contradicts or obscures the intended message.','Message is very ambiguous or conflicting.','Main request is partly identifiable but important details are unclear.','States an understandable concern, request or position.','States a clear message with relevant scope and context.','States a precise message and checks understanding when useful.'),
 'respect':('Uses a personal attack, coercion or clearly dismisses a legitimate boundary.','Mostly dismisses the partner or sacrifices an important boundary without discussion.','Some acknowledgement or boundary-setting, but significant relational gaps.','Acknowledges the partner and maintains reasonable boundaries.','Communicates disagreement or boundaries constructively and respectfully.','Balances both parties’ legitimate needs and negotiates respectful alternatives.'),
 'reasons':('Relies on clearly contradicted claims or irrelevant assertions.','Makes a request with little relevant explanation despite an evident opportunity.','Provides some relevant reasoning but leaves important gaps.','Gives a relevant reason or example supporting the request.','Connects specific evidence to the concern and its practical impact.','Uses relevant evidence, acknowledges its limits and addresses trade-offs.'),
 'perspective':('Ignores an explicit relevant partner expectation or relies on a stereotype.','Largely overlooks the partner’s expressed needs.','Partly recognizes the partner’s view without checking important assumptions.','Acknowledges or asks about the partner’s relevant expectations.','Checks assumptions and responds to the expressed expectation.','Integrates both perspectives while negotiating differences and boundaries.'),
 'solutions':('Proposes an option clearly incompatible with the frozen constraints.','Offers an impractical step without addressing visible constraints.','Suggests a partly workable option but leaves major practical gaps.','Offers a feasible option or clear next step.','Offers workable options and clarifies responsibilities or trade-offs.','Agrees or proposes a feasible plan with ownership, checkpoints and contingencies.')}

# These are simulation design choices, not empirically validated individual predictors.
PREFERENCES={
 DIMENSIONS[0]:('Invite open discussion and clarify who owns the decision.','Clarify decision ownership while welcoming respectful questions.','Use a clear decision process and raise concerns through the appropriate decision-maker.'),
 DIMENSIONS[1]:('Emphasize shared commitments, group impact and mutual support.','Balance personal ownership with shared commitments.','Clarify personal responsibility, autonomy and individual contributions.'),
 DIMENSIONS[2]:('Balance the quality of relationships, wellbeing and collaboration.','Balance achievement with collaboration and wellbeing.','Explain how proposals meet explicit achievement and quality goals.'),
 DIMENSIONS[3]:('Explore flexible options and acknowledge what remains uncertain.','Use a practical plan with room to adjust.','Request concrete steps, risks, contingencies and checkpoints.'),
 DIMENSIONS[4]:('Connect the plan to immediate obligations and visible near-term results.','Balance near-term obligations and future consequences.','Consider sustained outcomes, learning and longer-term trade-offs.'),
 DIMENSIONS[5]:('Respect commitments and explain how necessary breaks fit obligations.','Balance commitments with reasonable recovery time.','Protect reasonable downtime and wellbeing alongside commitments.')}

def reference():return json.loads((Path(__file__).parent/'data/hofstede_reference.json').read_text())
def anchors(target):
    return ('Clearly undermines '+target,'Addresses '+target+' ineffectively, with major gaps.','Partly addresses '+target+' with substantial gaps.','Adequately addresses '+target+' in the stated situation.','Addresses '+target+' clearly with relevant reasoning.','Addresses '+target+' effectively while checking trade-offs and preserving reasonable boundaries.')
def build_rubric(config):
    data=reference();record=data['countries'][config.other_culture];criteria=[]
    for i,d in enumerate(DIMENSIONS):
        value=record['scores'][d]
        if value is None:continue
        band=0 if value<40 else 2 if value>60 else 1
        if config.persona_style=='contrast':band=2-band
        expectation=PREFERENCES[d][band]
        criteria.append(PracticeCriterion(id='adapt-'+str(i),label=d,dimension=d,reference_value=value,expectation=expectation,anchors=anchors('the expressed preference: '+expectation)))
    return PracticeRubric(version=VERSION,country=config.other_culture,profile_style=config.persona_style,reference_version=data['version'],reference_source=data['source'],source_country=record['source_country'],country_scores=tuple(record['scores'][d] for d in DIMENSIONS),communication=tuple(PracticeCriterion(id=k,label=label,expectation=text,anchors=GENERAL_ANCHORS[k]) for k,label,text in GENERAL),adaptation=tuple(criteria))

def persona_notes(rubric):
    return 'Authored fictional persona preferences ('+rubric.profile_style+'); not a claim about every person from this country: '+' '.join(c.expectation for c in rubric.adaptation)

def validate_practice(a,e):
    rubric=a.scenario.practice_rubric
    if rubric is None:
        if e.communication_ratings or e.adaptation_ratings or e.practice_rubric_version is not None:raise ValueError('Legacy attempt has no practice rubric')
        return
    if rubric!=build_rubric(a.config):raise ValueError('Practice rubric differs from server version')
    if e.practice_rubric_version!=rubric.version:raise ValueError('Practice scoring version mismatch')
    learners={t.id:t for t in a.transcript if t.role=='learner'}
    evidence={x.turn_id for x in e.evidence}
    positions={t.id:i for i,t in enumerate(a.transcript)}
    partners={t.id:t for t in a.transcript if t.role=='partner'}
    for ratings,criteria,is_adaptation in [(e.communication_ratings,rubric.communication,False),(e.adaptation_ratings,rubric.adaptation,True)]:
        ids=[x.criterion_id for x in ratings]
        if len(ids)!=len(set(ids)) or set(ids)!={c.id for c in criteria}:raise ValueError('Practice criteria differ from frozen rubric')
        for rating in ratings:
            if not rating.reason.strip():raise ValueError('Practice rating requires explanation')
            if any(i not in learners or i not in evidence for i in rating.evidence_turn_ids):raise ValueError('Practice evidence refers to an invalid learner turn')
            if is_adaptation and (rating.partner_cue_turn_id is not None or rating.partner_cue_quote is not None):
                cue=partners.get(rating.partner_cue_turn_id)
                if cue is None or not rating.partner_cue_quote or rating.partner_cue_quote not in cue.text:raise ValueError('Invalid optional partner cue')
            if rating.value is None:continue
            if a.mode!='live':raise ValueError('Demo cannot receive personal practice ratings')
            if not rating.evidence_turn_ids or any(i not in learners or i not in evidence for i in rating.evidence_turn_ids):raise ValueError('Practice rating requires learner evidence')
            if is_adaptation:
                cue=partners.get(rating.partner_cue_turn_id)
                if cue is None or not rating.partner_cue_quote or rating.partner_cue_quote not in cue.text:raise ValueError('Adaptation requires exact partner cue evidence')
                if any(positions[cue.id]>=positions[i] for i in rating.evidence_turn_ids):raise ValueError('Partner cue must precede every rated learner turn')

def panel(criteria,ratings,labels=None):
    from scoring import aggregate
    values={x.criterion_id:x for x in ratings};dimensions=[]
    for c in criteria:
        x=values[c.id]
        dimensions.append(DimensionScore(dimension=c.label,value=x.value,status='scored' if x.value is not None else 'insufficient_evidence',explanation=x.reason))
    if labels:
        dimensions=[next((x for x in dimensions if x.dimension==d),DimensionScore(dimension=d,value=None,status='not_applicable',explanation='No country-specific reference value is available in this dataset.')) for d in labels]
    scored=[x for x in dimensions if x.value is not None]
    return Scorecard(overall=aggregate({x.dimension:x.value for x in dimensions}),coverage=len(scored)/len(criteria) if criteria else 0,dimensions=dimensions)

def practice_scores(a,e):
    validate_practice(a,e)
    if a.scenario.practice_rubric is None:return None
    r=a.scenario.practice_rubric
    return PracticeScores(communication=panel(r.communication,e.communication_ratings),adaptation=panel(r.adaptation,e.adaptation_ratings,DIMENSIONS),rubric_version=r.version)
