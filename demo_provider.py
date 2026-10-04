"""Scripted demo, never presented as live AI or an evidence-based evaluation."""
from schemas import ContextAdvice,ScenarioDraft,PartnerReply,Evaluation,Evidence,Feedback,Rating,AdaptationRating
from knowledge import context_for,template_for
class DemoProvider:
    def run(self,stage,a):
        t=template_for(a.config)
        if stage=='cultural_context': return ContextAdvice(guidance=context_for(a.config)['guidance'])
        if stage=='scenario_designer':
            detail=f"You are a {a.config.my_role} ({a.config.my_culture}) speaking to a {a.config.other_role} ({a.config.other_culture}) in a {a.config.context.lower()} setting. Situation: {a.config.situation}. Goal: {a.config.goal}."
            complexity={'Beginner':'Use simple language and focus on one practical next step.','Intermediate':'Balance the relationship, evidence and practical options.','Advanced':'Balance competing objectives, hidden assumptions and stakeholder pressure.'}[a.config.level]
            return ScenarioDraft(brief=detail+'\n\n'+t['brief']+'\n\n'+complexity,opening=t['opening'])
        if stage=='conversation_partner':
            prefix='Thank you for explaining your view. ' if a.config.level=='Beginner' else 'I hear your point. '
            return PartnerReply(speaker_role=a.config.other_role,text=prefix+t['prompts'][(a.rounds-1)%len(t['prompts'])])
        if stage=='behavioral_evaluator':
            return Evaluation(evidence=[Evidence(turn_id=x.id,quote=x.text,observation='A learner response was submitted to the preceding partner prompt.',interpretation='Scripted demo does not infer communication features or judge appropriateness.',uncertainty='Not analyzed by a live model or reviewer.',dimension_mappings=[]) for x in a.transcript if x.role=='learner'],ratings=[],communication_ratings=[Rating(criterion_id=x.id,value=None,reason='Scripted demo does not assess individual responses.') for x in a.scenario.practice_rubric.communication] if a.scenario.practice_rubric else [],adaptation_ratings=[AdaptationRating(criterion_id=x.id,value=None,reason='Scripted demo does not assess adaptation.') for x in a.scenario.practice_rubric.adaptation] if a.scenario.practice_rubric else [],practice_rubric_version=a.scenario.practice_rubric.version if a.scenario.practice_rubric else None,uncertainty='Scripted practice only. Cultural evaluation and numerical scores are unavailable.')
        if stage=='feedback_synthesizer':
            return Feedback(strengths=['You completed the practice and have a transcript to reflect on.'],improvements=['Review whether each response identifies a concern, provides useful evidence, and invites a practical next step. This is a reflection prompt, not a detected weakness.'],alternative='I understand our shared goal. I have a concern about the available time and workload. Could we compare the options and agree on a feasible next step?',explanation='This scripted example makes the concern and invitation explicit. Your own direct or indirect strategy may also work. The demo does not assess your cultural adaptability.',lesson_ids=['concern' if a.config.template_id=='deadline' else 'agreement','variation'])
        raise ValueError('Unknown stage')
