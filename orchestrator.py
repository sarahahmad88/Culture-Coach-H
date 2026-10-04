from schemas import State,ContextPackage,Scenario,Turn
from knowledge import context_for,template_for,registry,lessons
from session_manager import transition,accept,commit_reply
from scoring import validate_evaluation,score
from diagnostics import StageError
from practice_scoring import build_rubric,persona_notes,practice_scores
STAGES={'cultural_context':'Preparing cultural context','scenario_designer':'Building your scenario','conversation_partner':'Conversation Partner is replying','behavioral_evaluator':'Evaluating your responses','feedback_synthesizer':'Preparing your learning feedback'}
class Controller:
    def __init__(self,provider,on_stage=lambda text:None): self.provider,self.on_stage=provider,on_stage
    def run(self,stage,a):
        self.on_stage(STAGES[stage])
        return self.provider.run(stage,a)
    def prepare(self,a):
        transition(a,State.generating)
        try:
            if a.context_package is None:
                base=context_for(a.config)
                guidance=self.run('cultural_context',a)
                # Generated language cannot alter record status or provenance.
                base['guidance']=guidance.guidance
                a.context_package=ContextPackage(**base)
            draft=self.run('scenario_designer',a)
            t=template_for(a.config)
            a.scenario=Scenario(template_id=a.config.template_id,title=t['title'],brief=draft.brief,character=f"{a.config.other_role}: "+t['character']+' '+persona_notes(build_rubric(a.config)),objective=a.config.goal+' — '+t['objective'],constraints=tuple(t['constraints']),rubric_version=registry()['version'],criterion_ids=(),relevant_dimensions=tuple(t['candidate_dimensions']),opening=draft.opening,practice_rubric=build_rubric(a.config))
            transition(a,State.ready)
        except Exception:
            transition(a,State.failed); raise
    def begin(self,a):
        transition(a,State.conversing)
        a.transcript.append(Turn(role='partner',text=a.scenario.opening))
    def submit(self,a,text,submission_id):
        if not accept(a,text,submission_id): return False
        if a.pending_reply: self.reply(a)
        if a.state==State.evaluating: self.finish(a)
        return True
    def reply(self,a):
        if not a.pending_reply: raise ValueError('No pending reply')
        reply=self.run('conversation_partner',a)
        from partner_contract import validate_reply
        try:validate_reply(a,reply)
        except (ValueError,AttributeError):
            raise StageError('Conversation Partner','role contract failed','Your response is preserved. Retry the partner reply; the invalid reply was not added.') from None
        commit_reply(a,reply.text)
    def finish(self,a):
        if a.state!=State.evaluating: raise ValueError('Attempt is not awaiting evaluation')
        r=registry()
        if a.evaluation is None:
            candidate=self.run('behavioral_evaluator',a)
            try: validate_evaluation(a,candidate,r)
            except ValueError:
                # One bounded semantic repair; a repeated invalid evaluation is rejected.
                candidate=self.run('behavioral_evaluator',a)
                try: validate_evaluation(a,candidate,r)
                except ValueError: raise StageError('Evaluation','invalid evidence','A bounded repair failed. Retry evaluation; no score was accepted.') from None
            a.evaluation=candidate
        a.scorecard=score(a.scenario,a.evaluation,r)
        a.practice_scores=practice_scores(a,a.evaluation)
        if a.feedback is None:
            feedback=self.run('feedback_synthesizer',a)
            if any(i not in {l['id'] for l in lessons()} for i in feedback.lesson_ids): raise StageError('Feedback','unknown lesson','Retry feedback; an unsupported resource was rejected.')
            a.feedback=feedback
        transition(a,State.completed)
