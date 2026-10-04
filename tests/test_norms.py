import unittest,json
import numpy as np
from culturebank_adapter import normalize_rows,read_entries,matches_culture
from norm_analyzer import AnalyzerSettings,LocalModels,NormAnalyzer,chunks
from tests.test_core import started
class Encoder:
    def encode_document(self,texts,**kw):return np.array([[1.,0.] if 'schedule' in t else [0.,1.] for t in texts])
    def encode_query(self,texts,**kw):return np.array([[1.,0.]])
class Classifier:
    def __init__(self,scores=(.8,.1,.1)):self.scores=scores;self.calls=[]
    def __call__(self,text,candidate_labels,**kw):
        self.calls.append((text,candidate_labels,kw))
        return {'labels':candidate_labels[::-1],'scores':list(self.scores)[::-1]}
def entries():
    rows=[{'cultural group':'Japanese','context':'workplace project meeting','actor':'employee','actor_behavior':'explains a schedule concern','agreement':.8,'review_status':'approved'}, {'cultural_group':'Japanese','context':'university group project','actor_behavior':'requests help'}, {'cultural_group':'American','context':'workplace project meeting','actor_behavior':'explains schedule constraints'}]
    return normalize_rows(rows,'synthetic tests only','test-v1')[0]
def analyzer(scores=(.8,.1,.1),**kw):
    settings=AnalyzerSettings(**kw)
    models=LocalModels(settings,Encoder(),Classifier(scores))
    return NormAnalyzer(entries(),models)
class NormTests(unittest.TestCase):
    def test_actual_column_names_provenance_and_no_auto_approval(self):
        e=entries()[0]
        self.assertEqual(e.cultural_group,'Japanese');self.assertEqual(e.agreement,.8)
        self.assertEqual(e.review_status,'unreviewed_research');self.assertEqual(e.source_revision,'test-v1')
        with self.assertRaises(ValueError):e.actor_behavior='changed'
    def test_missing_fields_eval_question_not_norm_and_duplicates(self):
        rows=[{'cultural group':'Japanese','context':'office','eval_question':'What should someone do?'}, {'cultural group':'Japanese','context':'office','actor_behavior':'asks for clarification'}]
        values,skipped=normalize_rows(rows+[rows[1]],'synthetic','v1')
        self.assertEqual(skipped,1);self.assertEqual(len(values),1)
    def test_culture_context_filter_and_ranking(self):
        a=analyzer();hits,status=a.retrieve('schedule concern','Japan','Workplace')
        self.assertEqual(status,'retrieved');self.assertEqual(len(hits),1);self.assertAlmostEqual(hits[0][1],1)
        self.assertEqual(a.retrieve('schedule','Pakistan','Workplace')[1],'no_matching_context')
        self.assertEqual(a.retrieve('schedule','Japan','University')[1],'no_relevant_match')
    def test_zero_shot_scores_are_per_norm_and_hypotheses_use_norm(self):
        a=analyzer();report=a.analyze_turn('Testing needs three weeks.','Japan','Workplace',learner_role='Junior employee',partner_prompt='Can we finish in two weeks?')
        hit=report['matches'][0]
        self.assertEqual(hit['classification'],'possible_adherence');self.assertEqual(hit['scores']['adherence'],.8)
        text,labels,opts=a.models.classifier.calls[0]
        self.assertIn('Testing needs',text);self.assertIn('Previous partner',text)
        self.assertTrue(all('schedule concern' in x for x in labels));self.assertFalse(opts['multi_label'])
    def test_violation_unclear_and_margin_abstention(self):
        for scores,expected in [((.1,.8,.1),'possible_violation'),((.1,.1,.8),'insufficient_evidence'),((.45,.4,.15),'insufficient_evidence')]:
            hit=analyzer(scores).analyze_turn('I refuse.','Japan','Workplace')['matches'][0]
            self.assertEqual(hit['classification'],expected)
    def test_no_matching_entries_no_classifier_calls(self):
        a=analyzer();report=a.analyze_turn('My concern','Pakistan','Workplace')
        self.assertEqual(report['status'],'no_matching_context');self.assertFalse(a.models.classifier.calls)
    def test_chunks_exact_spans_and_no_full_dialogue_truncation(self):
        text=('A schedule concern needs context. '*50).strip()
        parts=list(chunks(text));self.assertTrue(len(parts)>1)
        for start,end,segment in parts:self.assertEqual(segment,text[start:end])
        report=analyzer().analyze_turn(text,'Japan','Workplace')
        self.assertEqual(len(report['matches']),len(parts))
        self.assertEqual(analyzer().analyze_turn('','Japan','Workplace')['status'],'empty')
        with self.assertRaises(ValueError):analyzer().analyze_turn('x'*3001,'Japan','Workplace')
    def test_token_limit_abstains_instead_of_silent_truncation(self):
        a=analyzer();a.models.classifier.tokenizer=type('Tokenizer',(),{'model_max_length':2,'__call__':lambda self,*args,**kw:{'input_ids':list(range(10))}})()
        hit=a.analyze_turn('My concern','Japan','Workplace')['matches'][0]
        self.assertIsNone(hit['scores']);self.assertIn('no silent truncation',hit['reason'])
    def test_malformed_scores_rejected(self):
        with self.assertRaises(ValueError):analyzer((.8,.8,.8)).analyze_turn('My concern','Japan','Workplace')
    def test_attempt_analysis_does_not_modify_score_or_transcript(self):
        a,c=started()
        for i in range(3):c.submit(a,'My concern '+str(i),str(i))
        before=a.model_dump_json();report=analyzer().analyze_attempt(a)
        self.assertEqual(a.model_dump_json(),before);self.assertEqual(len(report['turns']),3)
        self.assertEqual(report['official_score_impact'],'none');self.assertIn('resolved_revisions',report['models'])
    def test_json_csv_and_size_validation(self):
        raw=b'cultural group,context,actor_behavior\nJapanese,office,asks a question\n'
        es,n=read_entries(raw,'x.csv','synthetic','v1');self.assertEqual(len(es),1)
        with self.assertRaises(ValueError):read_entries(b'x'*2_000_001,'x.csv','s','v')
    def test_example_is_separate_research_not_approved_knowledge(self):
        from pathlib import Path
        p=Path(__file__).resolve().parents[1]/'data'/'norms_example.json'
        values,skipped=read_entries(p.read_bytes(),p.name,'FICTIONAL format example; not CultureBank data','example-v1')
        self.assertEqual(len(values),2);self.assertTrue(all(v.agreement is None for v in values))
if __name__=='__main__':unittest.main()
