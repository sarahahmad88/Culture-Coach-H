import unittest
from types import SimpleNamespace
from repository import SupabaseRepository
from schemas import Attempt
from tests.test_core import config
from diagnostics import StageError
class Query:
    def __init__(self,c):self.c=c
    def upsert(self,row,**kw):self.c.row=row;return self
    def select(self,*args):self.c.selects.append(args);return self
    def eq(self,k,v):self.c.filters.append((k,v));return self
    def order(self,*args):return self
    def limit(self,*args):return self
    def delete(self):self.c.deleting=True;return self
    def execute(self):
        if self.c.fail:raise RuntimeError('private backend details')
        if self.c.deleting:self.c.row=None;self.c.deleting=False;return SimpleNamespace(data=[])
        return SimpleNamespace(data=[self.c.row] if self.c.row else [])
class Client:
    def __init__(self,user='user-A'):
        self.row=None;self.filters=[];self.selects=[];self.fail=False;self.deleting=False
        self.auth=SimpleNamespace(get_user=lambda:SimpleNamespace(user=SimpleNamespace(id=user)))
    def table(self,n):assert n=='training_attempts';return Query(self)
class StorageTests(unittest.TestCase):
    def test_server_identity_and_metadata_only(self):
        c=Client();r=SupabaseRepository(c);a=Attempt(config=config());r.save(a,False)
        self.assertEqual(c.row['user_id'],'user-A');self.assertIsNone(c.row['payload'])
        self.assertNotIn('transcript',c.row['metadata']);self.assertEqual(r.summaries()[0]['id'],a.id)
        self.assertIn(('user_id','user-A'),c.filters)
    def test_failure_redacted_and_source_retained(self):
        c=Client();c.fail=True;r=SupabaseRepository(c);a=Attempt(config=config())
        with self.assertRaises(StageError) as got:r.save(a)
        self.assertNotIn('private',str(got.exception));self.assertEqual(a.state.value,'configured')
    def test_expired_identity_prevents_write(self):
        c=Client();c.auth.get_user=lambda:SimpleNamespace(user=None)
        with self.assertRaises(StageError):SupabaseRepository(c).save(Attempt(config=config()))
        self.assertIsNone(c.row)
    def test_delete_uses_identity_and_checks_remaining(self):
        c=Client();r=SupabaseRepository(c);r.save(Attempt(config=config()),False);r.delete()
        self.assertIsNone(c.row);self.assertEqual(c.filters,[('user_id','user-A'),('user_id','user-A')])
if __name__=='__main__':unittest.main()
