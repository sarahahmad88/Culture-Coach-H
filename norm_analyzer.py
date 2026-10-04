"""Optional semantic retrieval + NLI estimates, isolated from cultural rubric arithmetic."""
import json,hashlib,threading,math
from dataclasses import dataclass
import numpy as np
from culturebank_adapter import NormEntry,matches_culture
from diagnostics import StageError
@dataclass(frozen=True)
class AnalyzerSettings:
    embedding_model: str='sentence-transformers/all-MiniLM-L6-v2'
    classifier_model: str='facebook/bart-large-mnli'
    embedding_revision: str='main'
    classifier_revision: str='main'
    top_k: int=3
    min_similarity: float=.35
    min_confidence: float=.70
    min_margin: float=.15
    max_chunks: int=8
    cpu_threads: int=2
    def validate(self):
        if not 1<=self.top_k<=5 or not 0<=self.min_similarity<=1 or not 0<=self.min_confidence<=1 or not 0<=self.min_margin<=1 or not 1<=self.max_chunks<=8 or not 1<=self.cpu_threads<=8:raise ValueError('Invalid analyzer settings')
        return self
class LocalModels:
    def __init__(self,settings,encoder=None,classifier=None,revisions=None):
        self.settings=settings.validate();self.lock=threading.RLock()
        self.encoder,self.classifier=encoder,classifier
        self.revisions=revisions or {'embedding':settings.embedding_revision,'classifier':settings.classifier_revision}
    @classmethod
    def load(cls,settings):
        try:
            from sentence_transformers import SentenceTransformer
            from transformers import pipeline
            from huggingface_hub import HfApi
        except ImportError:raise StageError('Norm analysis','optional packages missing','Install requirements-norms.txt on the server. The base demo still works.') from None
        try:
            import torch
            torch.set_num_threads(settings.cpu_threads)
            api=HfApi()
            er=api.model_info(settings.embedding_model,revision=settings.embedding_revision).sha
            cr=api.model_info(settings.classifier_model,revision=settings.classifier_revision).sha
            encoder=SentenceTransformer(settings.embedding_model,revision=er,device='cpu',trust_remote_code=False)
            classifier=pipeline('zero-shot-classification',model=settings.classifier_model,revision=cr,device=-1,trust_remote_code=False)
            return cls(settings,encoder,classifier,{'embedding':er,'classifier':cr})
        except Exception:raise StageError('Norm analysis','model loading failed','Check outbound Hugging Face access, disk/RAM and model configuration. No scores were fabricated.') from None
    def corpus(self,texts):
        tokenizer=getattr(self.encoder,'tokenizer',None)
        if tokenizer and any(len(tokenizer(text,truncation=False)['input_ids'])>self.encoder.max_seq_length for text in texts):
            raise StageError('Norm indexing','entry exceeds embedding token limit','Use shorter research entries or a compatible longer-context embedding model. No entry was silently truncated.')
        with self.lock:return np.asarray(self.encoder.encode_document(texts,normalize_embeddings=True),dtype=float)
    def query(self,text):
        tokenizer=getattr(self.encoder,'tokenizer',None)
        if tokenizer and len(tokenizer(text,truncation=False)['input_ids'])>self.encoder.max_seq_length:return None
        with self.lock:return np.asarray(self.encoder.encode_query([text],normalize_embeddings=True),dtype=float)[0]
    def classify(self,premise,labels):
        tokenizer=getattr(self.classifier,'tokenizer',None)
        if tokenizer:
            maximum=min(getattr(tokenizer,'model_max_length',512),1024)
            if any(len(tokenizer(premise,'In this context, '+label+'.',truncation=False)['input_ids'])>maximum for label in labels):return None
        with self.lock:return self.classifier(premise,candidate_labels=labels,hypothesis_template='In this context, {}.',multi_label=False)

def chunks(text,size=450):
    """Exact text segments, no splitting of a word where practical. No silent truncation."""
    start=0
    while start<len(text):
        end=min(start+size,len(text))
        if end<len(text):
            space=text.rfind(' ',start,end)
            if space>start:end=space
        if text[start:end].strip():yield start,end,text[start:end]
        start=end
        while start<len(text) and text[start].isspace():start+=1
class NormAnalyzer:
    def __init__(self,entries,models):
        self.entries=tuple(entries);self.models=models;self.settings=models.settings
        if len(entries)>2000:raise ValueError('Corpus limit is 2000 records')
        self.digest=hashlib.sha256(json.dumps([e.model_dump(mode='json') for e in entries],sort_keys=True).encode()).hexdigest()
        self.embeddings=models.corpus([e.search_text for e in entries]) if entries else np.empty((0,0))
        if entries and (self.embeddings.ndim!=2 or len(self.embeddings)!=len(entries) or not np.isfinite(self.embeddings).all()):raise ValueError('Invalid corpus embeddings')
    def retrieve(self,text,culture,context):
        eligible=[i for i,e in enumerate(self.entries) if matches_culture(e,culture) and context in e.context_tags]
        if not eligible:return [],'no_matching_context'
        query=self.models.query(text)
        if query is None:return [],'query_too_long'
        query=np.asarray(query,dtype=float)
        if query.ndim!=1 or query.shape[0]!=self.embeddings.shape[1] or not np.isfinite(query).all():raise ValueError('Invalid query embeddings')
        # Dot product equals cosine only after normalization; normalize injected models too.
        qnorm=np.linalg.norm(query)
        if qnorm==0:return [],'no_query_signal'
        docs=self.embeddings[eligible];norms=np.linalg.norm(docs,axis=1)
        sims=np.divide(docs@query,norms*qnorm,out=np.full(len(eligible),-1.),where=norms>0)
        hits=[(self.entries[eligible[j]],float(sims[j])) for j in np.argsort(-sims)[:self.settings.top_k] if sims[j]>=self.settings.min_similarity]
        return hits,'retrieved' if hits else 'no_relevant_match'
    def analyze_turn(self,text,culture,context,goal='',learner_role='',partner_prompt='',turn_id='dialogue'):
        if not text.strip():return {'turn_id':turn_id,'status':'empty','matches':[]}
        if len(text)>3000:raise ValueError('Dialogue/turn limit is 3000 characters')
        parts=list(chunks(text))
        if len(parts)>self.settings.max_chunks:return {'turn_id':turn_id,'status':'too_many_chunks','matches':[]}
        outputs=[];statuses=[]
        for start,end,segment in parts:
            # The prior partner prompt is context; only this learner segment is assessed.
            premise=f'Setting: {context}. Goal: {goal[:120]}. Learner role: {learner_role[:80]}. Previous partner: {partner_prompt[:180]}\nLearner response: {segment}'
            hits,status=self.retrieve(premise,culture,context);statuses.append(status)
            for entry,similarity in hits:
                norm=entry.statement
                labels=[f'the learner response follows the described behavior for the applicable actor role: {norm}',f'the learner response contradicts the described behavior for the applicable actor role: {norm}',f'the learner response does not provide enough evidence to judge this behavior or the actor role does not apply: {norm}']
                result=self.models.classify(premise,labels)
                base={'entry':entry.model_dump(mode='json'),'norm':norm,'turn_id':turn_id,'excerpt':segment,'span':[start,end],'retrieval_similarity':similarity}
                if result is None:outputs.append({**base,'classification':'insufficient_evidence','scores':None,'reason':'NLI input exceeds token budget; no silent truncation.'});continue
                scores=dict(zip(result.get('labels',[]),result.get('scores',[])))
                if len(scores)!=3 or set(scores)!=set(labels) or any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in scores.values()):raise ValueError('Malformed zero-shot classifier output')
                if abs(sum(scores.values())-1)>1e-3:raise ValueError('Expected mutually exclusive normalized label scores')
                values=[float(scores[label]) for label in labels]
                ranked=sorted(values,reverse=True);best=int(np.argmax(values))
                confident=ranked[0]>=self.settings.min_confidence and ranked[0]-ranked[1]>=self.settings.min_margin
                classification=['possible_adherence','possible_violation','insufficient_evidence'][best] if confident else 'insufficient_evidence'
                outputs.append({**base,'classification':classification,'scores':dict(zip(['adherence','violation','unclear'],values)),'reason':'Experimental relative NLI label scores; not calibrated cultural correctness probabilities.'})
        mixed=any(x['classification']=='possible_adherence' for x in outputs) and any(x['classification']=='possible_violation' for x in outputs)
        return {'turn_id':turn_id,'status':'mixed_interpretations' if mixed else ('analyzed' if outputs else statuses[-1]),'matches':outputs}
    def analyze_attempt(self,a):
        results=[];prior=''
        for turn in a.transcript:
            if turn.role=='partner':prior=turn.text
            else:results.append(self.analyze_turn(turn.text,a.config.other_culture,a.config.context,a.config.goal,a.config.my_role,prior,turn.id))
        return {'analysis_version':'experimental-1','attempt_id':a.id,'corpus_digest':self.digest,'models':{'embedding':self.settings.embedding_model,'classifier':self.settings.classifier_model,'resolved_revisions':self.models.revisions},'thresholds':{'similarity':self.settings.min_similarity,'confidence':self.settings.min_confidence,'margin':self.settings.min_margin},'review_status':'unreviewed_research','official_score_impact':'none','turns':results}

def main():
    import argparse
    from pathlib import Path
    from culturebank_adapter import read_entries
    parser=argparse.ArgumentParser(description='Experimental norm retrieval and zero-shot NLI estimates')
    parser.add_argument('--entries',required=True);parser.add_argument('--dialogue',required=True,help='UTF-8 file containing a learner response, up to 3000 characters')
    parser.add_argument('--culture',required=True);parser.add_argument('--context',choices=['Workplace','University'],required=True)
    parser.add_argument('--embedding-model',default=AnalyzerSettings.embedding_model);parser.add_argument('--classifier-model',default=AnalyzerSettings.classifier_model)
    parser.add_argument('--goal',default='');parser.add_argument('--role',default='');parser.add_argument('--source',default='custom local research entries');parser.add_argument('--revision',default='local-file');parser.add_argument('--output',required=True)
    args=parser.parse_args();path=Path(args.entries)
    raw=path.read_bytes();entries,skipped=read_entries(raw,path.name,args.source,args.revision)
    analyzer=NormAnalyzer(entries,LocalModels.load(AnalyzerSettings(embedding_model=args.embedding_model,classifier_model=args.classifier_model)))
    report={'models':analyzer.models.revisions,'corpus_digest':analyzer.digest,'skipped_entries':skipped,'official_score_impact':'none','result':analyzer.analyze_turn(Path(args.dialogue).read_text(),args.culture,args.context,args.goal,args.role)}
    Path(args.output).write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
