"""Normalize CultureBank-style research records; never promote them to approved rules."""
import csv,io,json,hashlib,re
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
class NormEntry(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    id: str
    cultural_group: str = Field(min_length=1,max_length=100)
    context: str = Field(min_length=1,max_length=400)
    context_tags: tuple[str,...]
    goal: str = Field(default='',max_length=300)
    relation: str = Field(default='',max_length=300)
    actor: str = Field(default='',max_length=150)
    actor_behavior: str = Field(min_length=1,max_length=500)
    recipient: str = Field(default='',max_length=150)
    recipient_behavior: str = Field(default='',max_length=300)
    agreement: float | None = Field(default=None,ge=0,le=1)
    source: str
    source_revision: str
    source_split: str
    license: str
    review_status: Literal['unreviewed_research'] = 'unreviewed_research'
    @property
    def statement(self):
        return f'In {self.context}, {self.actor or "the actor"} {self.actor_behavior}.'
    @property
    def search_text(self):
        return f'Group: {self.cultural_group}. Context: {self.context}. Goal: {self.goal}. Relationship: {self.relation}. {self.statement} Recipient: {self.recipient}; {self.recipient_behavior}.'
ALIASES={'japan':{'japan','japanese'},'pakistan':{'pakistan','pakistani'},'germany':{'germany','german'},'united states':{'united states','american','us','usa'},'china':{'china','chinese'},'australia':{'australia','australian'},'uk':{'uk','united kingdom','british'},'saudi arabia':{'saudi arabia','saudi','saudi arabian'},'egypt':{'egypt','egyptian'},'brazil':{'brazil','brazilian'},'mexico':{'mexico','mexican'},'south africa':{'south africa','south african'},'france':{'france','french'},'greece':{'greece','greek'}}
def normalize_group(value):return ' '.join(str(value).strip().casefold().split())
def matches_culture(entry,culture):
    key=normalize_group(culture)
    return normalize_group(entry.cultural_group) in ALIASES.get(key,{key})
def infer_context_tags(context):
    # Search heuristics, not cultural evidence or approval. Ambiguous rows stay excluded.
    text=context.casefold();tags=[]
    if re.search(r'\b(workplace|office|project meeting|business meeting|at work|corporate|work meeting)\b',text):tags.append('Workplace')
    if re.search(r'\b(university|college|classroom|group project|campus|student project)\b',text):tags.append('University')
    return tuple(tags)
def clean(value):
    if value is None:return ''
    if isinstance(value,float) and value!=value:return ''
    s=str(value).strip()
    return '' if s.casefold() in {'null','none','nan'} else s

def normalize_rows(rows,source,revision,split='custom',license='unspecified',limit=2000):
    if not source.strip() or not revision.strip():raise ValueError('Source and version are required')
    if not isinstance(rows,list) or len(rows)>limit:raise ValueError(f'Use a list containing at most {limit} records')
    entries=[];skipped=0;ids=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Each norm must be an object')
        group=clean(row.get('cultural group',row.get('cultural_group')))
        context=clean(row.get('context'))
        behavior=clean(row.get('actor_behavior'))
        # eval_question is a benchmark question, not a norm. No fallback to it.
        if not group or not context or not behavior:skipped+=1;continue
        tags=row.get('context_tags')
        if tags is None:tags=infer_context_tags(context)
        elif isinstance(tags,str):tags=tuple(x.strip() for x in tags.split('|') if x.strip())
        if not isinstance(tags,(tuple,list)) or any(x not in ['Workplace','University'] for x in tags):raise ValueError('context_tags must contain supported context names')
        if not tags:skipped+=1;continue
        fields={k:clean(row.get(k)) for k in ['goal','relation','actor','recipient','recipient_behavior']}
        agreement=clean(row.get('agreement'))
        payload={'cultural_group':group,'context':context,'actor_behavior':behavior,**fields,'agreement':float(agreement) if agreement else None,'context_tags':tuple(tags),'source':source,'source_revision':revision,'source_split':split,'license':license}
        ident=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:24]
        if ident in ids:continue
        ids.add(ident);entries.append(NormEntry(id=ident,**payload))
    return entries,skipped

def read_entries(raw,filename,source,revision,split='custom',license='unspecified'):
    if len(raw)>2_000_000:raise ValueError('Upload limit is 2 MB')
    text=raw.decode('utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(text))) if filename.lower().endswith('.csv') else json.loads(text)
    return normalize_rows(rows,source,revision,split,license)

def load_culturebank(split='reddit',revision='main',limit=2000):
    """Stream data at a resolved immutable revision. Imports happen only on explicit use."""
    if split not in ['reddit','tiktok'] or not 1<=limit<=2000:raise ValueError('Invalid split or limit')
    from huggingface_hub import HfApi
    from datasets import load_dataset
    resolved=HfApi().dataset_info('SALT-NLP/CultureBank',revision=revision).sha
    dataset=load_dataset('SALT-NLP/CultureBank',split=split,revision=resolved,streaming=True)
    # Bounded raw sample; never claim that the first N rows represent full coverage.
    rows=list(dataset.take(limit))
    entries,skipped=normalize_rows(rows,'https://huggingface.co/datasets/SALT-NLP/CultureBank',resolved,split,'MIT (dataset card)',limit)
    return entries,{'revision':resolved,'split':split,'sampled':len(rows),'usable':len(entries),'skipped':skipped,'sampling':'first N raw rows; partial coverage only'}
