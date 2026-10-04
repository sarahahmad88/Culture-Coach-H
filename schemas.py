"""Validated contracts; country data and learner ratings are separate."""
from enum import Enum
from typing import Literal
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, model_validator
from config import LEVELS, DIMENSIONS
class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
class State(str, Enum):
    configured='configured'; generating='generating'; ready='ready'; conversing='conversing'
    evaluating='evaluating'; completed='completed'; incomplete='incomplete'; failed='failed'
class Configuration(Contract):
    model_config = ConfigDict(extra='forbid', frozen=True)
    my_culture: str = Field(min_length=1, max_length=80)
    other_culture: str = Field(min_length=1, max_length=80)
    context: str
    situation: str = Field(min_length=1, max_length=500)
    my_role: str = Field(min_length=1, max_length=120)
    other_role: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=200)
    level: Literal['Beginner','Intermediate','Advanced']
    template_id: Literal['deadline','group_project'] = 'deadline'
    persona_style: Literal['country_informed','contrast'] = 'country_informed'
    @model_validator(mode='after')
    def required(self):
        for k in ['my_culture','other_culture','situation','my_role','other_role','goal']:
            if not getattr(self,k).strip(): raise ValueError(f'{k} is required')
        if self.context not in ['Workplace','University']: raise ValueError('Only Workplace and University have draft templates')
        if (self.template_id=='deadline') != (self.context=='Workplace'): raise ValueError('Template and context do not match')
        roles=('Junior employee','Senior manager') if self.template_id=='deadline' else ('Student','Fellow student')
        if (self.my_role.strip(),self.other_role.strip())!=roles: raise ValueError('Roles are outside this draft template’s supported configuration')
        goals=['Raise a concern','Disagree respectfully','Negotiate'] if self.template_id=='deadline' else ['Request assistance','Give feedback','Resolve conflict','Build trust']
        if self.goal not in goals: raise ValueError('Goal is outside this draft template’s supported configuration')
        return self
class ContextPackage(Contract):
    registry_version: str
    record_ids: list[str]
    source: str
    supported_contexts: list[str]
    limitations: list[str]
    guidance: list[str]
    relevant_dimensions: list[str]
class PracticeCriterion(Contract):
    model_config=ConfigDict(extra='forbid', frozen=True)
    id: str
    label: str
    expectation: str
    anchors: tuple[str,str,str,str,str,str]
    dimension: str | None = None
    reference_value: float | None = Field(default=None,ge=0,le=100)
class PracticeRubric(Contract):
    model_config=ConfigDict(extra='forbid', frozen=True)
    version: str
    country: str
    profile_style: str
    reference_version: str
    reference_source: str
    source_country: str
    country_scores: tuple[float | None,...]
    communication: tuple[PracticeCriterion,...]
    adaptation: tuple[PracticeCriterion,...]
class Scenario(Contract):
    model_config=ConfigDict(extra='forbid', frozen=True)
    id: str = Field(default_factory=lambda:str(uuid4()))
    template_id: str
    title: str
    brief: str
    character: str
    objective: str
    constraints: tuple[str,...]
    rubric_version: str
    criterion_ids: tuple[str,...] = ()
    relevant_dimensions: tuple[str,...] = ()
    opening: str
    practice_rubric: PracticeRubric | None = None
class ScenarioDraft(Contract):
    brief: str = Field(min_length=10, max_length=3000)
    opening: str = Field(min_length=5, max_length=1000)
class ContextAdvice(Contract):
    guidance: list[str] = Field(max_length=5)
class Reply(Contract):
    text: str = Field(min_length=1, max_length=2500)
class PartnerReply(Reply):
    speaker_role: str = Field(min_length=1,max_length=120)
class Turn(Contract):
    id: str = Field(default_factory=lambda:str(uuid4()))
    role: Literal['learner','partner']
    text: str = Field(min_length=1,max_length=3000)
    submission_id: str | None = None
class Evidence(Contract):
    turn_id: str
    quote: str = Field(min_length=1)
    observation: str
    interpretation: str
    uncertainty: str
    dimension_mappings: list[str] = []
class Rating(Contract):
    criterion_id: str
    value: float | None = Field(default=None,ge=0,le=5)
    evidence_turn_ids: list[str] = []
    reason: str
class AdaptationRating(Rating):
    partner_cue_turn_id: str | None = None
    partner_cue_quote: str | None = None
class Evaluation(Contract):
    evidence: list[Evidence]
    ratings: list[Rating]
    communication_ratings: list[Rating] = []
    adaptation_ratings: list[AdaptationRating] = []
    practice_rubric_version: str | None = None
    uncertainty: str
class Feedback(Contract):
    strengths: list[str]
    improvements: list[str]
    alternative: str
    explanation: str
    lesson_ids: list[str]
class DimensionScore(Contract):
    dimension: str
    value: float | None
    status: Literal['scored','not_applicable','insufficient_evidence']
    explanation: str
class Scorecard(Contract):
    overall: int | None
    coverage: float = Field(ge=0,le=1)
    dimensions: list[DimensionScore]
class PracticeScores(Contract):
    communication: Scorecard
    adaptation: Scorecard
    rubric_version: str
class Attempt(Contract):
    id: str = Field(default_factory=lambda:str(uuid4()), frozen=True)
    created_at: str = Field(default_factory=lambda:datetime.now(timezone.utc).isoformat())
    config: Configuration
    mode: Literal['demo','live'] = 'demo'
    state: State = State.configured
    context_package: ContextPackage | None = None
    scenario: Scenario | None = None
    transcript: list[Turn] = []
    pending_reply: bool = False
    evaluation: Evaluation | None = None
    scorecard: Scorecard | None = None
    feedback: Feedback | None = None
    practice_scores: PracticeScores | None = None
    feedback_rating: int | None = Field(default=None,ge=1,le=5,strict=True)
    parent_retry_id: str | None = None
    calls_used: int = 0
    output_tokens_used: int = 0
    gemini_fallback_used: bool = False
    secondary_groq_used: bool = False
    @property
    def rounds(self): return sum(t.role=='learner' for t in self.transcript)
    @property
    def limit(self): return LEVELS[self.config.level]
class ExportBundle(Contract):
    format_version: Literal['1'] = '1'
    attempts: list[Attempt] = Field(max_length=100)
    @model_validator(mode='after')
    def integrity(self):
        ids=[a.id for a in self.attempts]
        if len(ids)!=len(set(ids)): raise ValueError('Duplicate attempt IDs')
        for a in self.attempts:
            if a.rounds > a.limit: raise ValueError('Too many rounds')
            if len({t.id for t in a.transcript})!=len(a.transcript): raise ValueError('Duplicate turn IDs')
            expected='partner'
            for t in a.transcript:
                if t.role!=expected: raise ValueError('Transcript roles must alternate')
                expected='learner' if expected=='partner' else 'partner'
            if a.state==State.completed and (a.rounds!=a.limit or not a.feedback or not a.evaluation or not a.scorecard or not a.scenario or not a.context_package or a.pending_reply): raise ValueError('Invalid completed attempt')
            if a.scenario:
                from knowledge import registry
                from scoring import score, validate_evaluation
                r=registry()
                if a.scenario.template_id not in r['templates']: raise ValueError('Unknown template')
                if a.scenario.template_id!=a.config.template_id: raise ValueError('Scenario configuration mismatch')
                if set(a.scenario.relevant_dimensions)!=set(r['templates'][a.config.template_id]['candidate_dimensions']): raise ValueError('Dimension selection differs from registry')
                if a.scenario.criterion_ids: raise ValueError('Imported cultural criteria require server review; this registry has none approved')
                if a.scenario.practice_rubric:
                    from practice_scoring import build_rubric
                    if a.scenario.practice_rubric!=build_rubric(a.config):raise ValueError('Imported persona/rubric differs from server version')
                if a.practice_scores and not a.evaluation:raise ValueError('Practice scorecards lack evaluation')
                if a.evaluation:
                    validate_evaluation(a,a.evaluation,r)
                    expected=score(a.scenario,a.evaluation,r)
                    if a.scorecard != expected: raise ValueError('Scorecard failed recalculation')
                    from practice_scoring import practice_scores
                    if a.practice_scores != practice_scores(a,a.evaluation):raise ValueError('Practice scorecards failed recalculation')
        return self
