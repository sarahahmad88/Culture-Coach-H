"""Session-scoped stores; Supabase requires verified Auth identity and SQL RLS."""
import json
from typing import Protocol
from schemas import Attempt,ExportBundle,State
from diagnostics import StageError
class Repository(Protocol):
    def save(self,a:Attempt,transcripts:bool): ...
    def list(self)->list[Attempt]: ...
    def delete(self): ...
class SessionRepository:
    def __init__(self): self.records={}; self.metadata={}
    def save(self,a,transcripts=True):
        if transcripts:
            self.metadata.pop(a.id,None)
            self.records[a.id]=a.model_copy(deep=True)
        else:
            self.records.pop(a.id,None)
            self.metadata[a.id]=metadata(a)
    def list(self): return list(self.records.values())
    def delete(self): self.records.clear(); self.metadata.clear()
def metadata(a):
    return {'id':a.id,'created_at':a.created_at,'state':a.state.value,'mode':a.mode,'level':a.config.level,'template_id':a.config.template_id,'overall':a.scorecard.overall if a.scorecard else None,'coverage':a.scorecard.coverage if a.scorecard else 0,'feedback_rating':a.feedback_rating,'communication_score':a.practice_scores.communication.overall if a.practice_scores else None,'communication_coverage':a.practice_scores.communication.coverage if a.practice_scores else 0,'adaptation_score':a.practice_scores.adaptation.overall if a.practice_scores else None,'adaptation_coverage':a.practice_scores.adaptation.coverage if a.practice_scores else 0,'practice_rubric_version':a.practice_scores.rubric_version if a.practice_scores else None}
def export_attempts(attempts): return ExportBundle(attempts=attempts).model_dump_json(indent=2)
def import_attempts(raw):
    if len(raw)>2_000_000: raise ValueError('Import limit is 2 MB')
    return ExportBundle.model_validate_json(raw).attempts
class SupabaseRepository:
    def __init__(self,client): self.client=client
    @classmethod
    def login(cls,settings,email,password):
        from supabase import create_client
        try:
            client=create_client(settings.supabase_url,settings.supabase_key)
            response=client.auth.sign_in_with_password({'email':email,'password':password})
            if not response.user or not client.auth.get_user().user: raise ValueError('Unverified login')
            return cls(client)
        except Exception: raise StageError('History login','authentication failed','Check your confirmed account and server Supabase settings.') from None
    def identity(self):
        try:
            user=self.client.auth.get_user().user
            if not user: raise ValueError('No authenticated identity')
            return user.id
        except Exception: raise StageError('History','session expired','Sign out and sign in again. Session results remain available.') from None
    def save(self,a,transcripts=True):
        user=self.identity()
        try:
            row={'id':a.id,'user_id':user,'metadata':metadata(a),'payload':a.model_dump(mode='json') if transcripts else None}
            result=self.client.table('training_attempts').upsert(row,on_conflict='id').execute()
            if not result.data: raise ValueError('Write not confirmed')
        except Exception: raise StageError('History','storage write failed','Result remains in this session. Retry saving or export.') from None
    def list(self):
        user=self.identity()
        try:
            result=self.client.table('training_attempts').select('*').eq('user_id',user).order('created_at').limit(100).execute()
            return import_attempts(json.dumps({'format_version':'1','attempts':[x['payload'] for x in result.data if x['payload']]}))
        except Exception: raise StageError('History','storage read failed','Retry after checking Auth, table schema and RLS.') from None
    def summaries(self):
        user=self.identity()
        try: return [r['metadata'] for r in self.client.table('training_attempts').select('metadata').eq('user_id',user).limit(100).execute().data]
        except Exception: raise StageError('History','metadata read failed','Check table access and retry.') from None
    def delete(self):
        user=self.identity()
        try:
            self.client.table('training_attempts').delete().eq('user_id',user).execute()
            remaining=self.client.table('training_attempts').select('id').eq('user_id',user).limit(1).execute().data
            if remaining: raise ValueError('Deletion not confirmed')
        except Exception: raise StageError('History','storage delete failed','Records may remain; retry deletion.') from None
    def sign_out(self):
        try: self.client.auth.sign_out()
        except Exception: raise StageError('History','sign-out failed','Retry sign-out.') from None
