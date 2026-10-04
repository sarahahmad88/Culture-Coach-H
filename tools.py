"""Each tool is closed over one request's already-authorized data, with no user ID argument."""
import json
from knowledge import context_for,template_for,lessons
TOOL_NAMES={'cultural_context':'retrieve_cultural_context','scenario_designer':'get_scenario_template','conversation_partner':'get_attempt_context','behavioral_evaluator':'get_evaluation_bundle','feedback_synthesizer':'get_learning_resources'}
def tool_payload(stage,attempt):
    if stage=='cultural_context': return context_for(attempt.config)
    if stage=='scenario_designer':
        from practice_scoring import build_rubric,persona_notes
        profile=build_rubric(attempt.config)
        return {'template':template_for(attempt.config),'context':attempt.context_package.model_dump(),'config':attempt.config.model_dump(),'persona_preferences':persona_notes(profile),'persona_reference':{'country':profile.country,'version':profile.reference_version,'source':profile.reference_source,'profile_style':profile.profile_style}}
    if stage=='conversation_partner':
        scenario=attempt.scenario.model_dump()
        # Role-play sees persona preferences, not evaluator anchors or target ratings.
        scenario.pop('practice_rubric',None)
        # These fields address the learner. Name them explicitly before exposure.
        scenario['learner_perspective_brief']=scenario.pop('brief')
        scenario['learner_objective']=scenario.pop('objective')
        return {'partner_identity':{'speaker':'partner','role':attempt.config.other_role,'culture':attempt.config.other_culture,'character':attempt.scenario.character},
                'learner_identity':{'speaker':'learner','role':attempt.config.my_role,'culture':attempt.config.my_culture,'goal':attempt.config.goal},
                'scenario':scenario,'setting':attempt.config.context,
                'transcript':[{'speaker':t.role,'speaker_role':attempt.config.my_role if t.role=='learner' else attempt.config.other_role,'text':t.text} for t in attempt.transcript],
                'next_speaker':'partner','accepted_rounds':attempt.rounds,'round_limit':attempt.limit,'level':attempt.config.level}
    if stage=='behavioral_evaluator':
        from knowledge import registry
        r=registry()
        scenario=attempt.scenario.model_dump(exclude={'practice_rubric'})
        return {'scenario':scenario,'transcript':[{'id':t.id,'role':t.role,'text':t.text} for t in attempt.transcript],'context':attempt.context_package.model_dump(),'criteria':[r['criteria'][i] for i in attempt.scenario.criterion_ids],'practice_rubric':attempt.scenario.practice_rubric.model_dump() if attempt.scenario.practice_rubric else None,'mode':attempt.mode}
    if stage=='feedback_synthesizer': return {'lessons':lessons(),'evaluation':attempt.evaluation.model_dump(),'scorecard':attempt.scorecard.model_dump(),'practice_scores':attempt.practice_scores.model_dump() if attempt.practice_scores else None,'scenario':attempt.scenario.model_dump(exclude={'practice_rubric'})}
    raise ValueError('Unknown stage')
def build_tool(stage,attempt):
    from crewai.tools import tool
    # Immutable JSON snapshot: an agent cannot change the active attempt through a tool.
    payload=json.dumps(tool_payload(stage,attempt),ensure_ascii=False,separators=(',',':'))
    @tool(TOOL_NAMES[stage])
    def retrieve() -> str:
        """Retrieve only the current authorized stage's frozen context. No arguments."""
        return payload
    return retrieve
