from schemas import State, Turn, Attempt
ALLOWED = {State.configured:{State.generating,State.incomplete}, State.generating:{State.ready,State.failed,State.incomplete}, State.ready:{State.conversing,State.incomplete}, State.conversing:{State.evaluating,State.incomplete}, State.evaluating:{State.completed,State.incomplete}, State.failed:{State.generating,State.incomplete}, State.completed:set(),State.incomplete:set()}
def transition(a, target):
    if target not in ALLOWED[a.state]: raise ValueError(f'Invalid transition {a.state.value} → {target.value}')
    a.state=target

def accept(a, text, submission_id):
    if a.state!=State.conversing or a.pending_reply: raise ValueError('Conversation is not accepting a new response')
    text=text.strip()
    if not text: raise ValueError('Please enter a response')
    if any(t.submission_id==submission_id for t in a.transcript): return False
    # A repeated consecutive learner response is also considered an accidental resubmission.
    learners=[t for t in a.transcript if t.role=='learner']
    if learners and learners[-1].text==text: return False
    if a.rounds>=a.limit: raise ValueError('Round limit reached')
    a.transcript.append(Turn(role='learner',text=text,submission_id=submission_id))
    if a.rounds==a.limit: transition(a,State.evaluating)
    else: a.pending_reply=True
    return True

def commit_reply(a,text):
    if not a.pending_reply or a.state!=State.conversing: raise ValueError('No pending reply')
    a.transcript.append(Turn(role='partner',text=text)); a.pending_reply=False

def retry(a,mode=None):
    if a.state!=State.completed: raise ValueError('Complete the attempt before retrying')
    return Attempt(config=a.config.model_copy(deep=True),mode=mode or a.mode,state=State.ready,scenario=a.scenario.model_copy(deep=True),context_package=a.context_package.model_copy(deep=True),parent_retry_id=a.id)
