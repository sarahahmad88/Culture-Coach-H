"""Optional research panel. No writes to rubric, agents, progression or account history."""
import json,hashlib
import streamlit as st
from culturebank_adapter import read_entries,load_culturebank
from norm_analyzer import AnalyzerSettings,LocalModels,NormAnalyzer
from diagnostics import StageError
from .components import handle,render_error
@st.cache_resource(show_spinner=False)
def public_models(settings):
    # Only public model weights and an inference lock; no corpus, prompt or user results.
    return LocalModels.load(settings)
def clear_norm_data():
    for key in ['norm_entries','norm_source','norm_index','norm_results']:
        st.session_state.pop(key,None)
def configure():
    with st.expander('Experimental cultural norm analysis'):
        st.write('Optional Sentence Transformers retrieval + Transformers zero-shot classification. These research estimates do not change rubric scores, progression, or approved knowledge.')
        st.caption('CultureBank entries are community-derived descriptions. Dataset agreement is not a learner score or proof of correctness. Context tags are search filters, not expert approval. English models are the defaults.')
        uploaded=st.file_uploader('Upload a CultureBank-style research subset',type=['csv','json'],key='norm_upload')
        source=st.text_input('Norm source / provenance',value='Custom uploaded research subset',key='norm_source_input')
        if uploaded and st.button('Load research entries into this session'):
            def load():
                raw=uploaded.getvalue();revision='sha256:'+hashlib.sha256(raw).hexdigest()
                entries,skipped=read_entries(raw,uploaded.name,source,revision)
                clear_norm_data();st.session_state.norm_entries=entries
                st.session_state.norm_source={'source':source,'revision':revision,'usable':len(entries),'skipped':skipped}
            handle(load);st.rerun()
        st.caption('Required columns: cultural group (or cultural_group), context, actor_behavior. Optional: goal, relation, actor, recipient, recipient_behavior, agreement, context_tags. Imported approval labels are ignored. Limit: 2 MB / 2,000 rows.')
        with st.expander('Load a bounded CultureBank sample from Hugging Face'):
            split=st.selectbox('CultureBank split',['reddit','tiktok'])
            revision=st.text_input('Dataset revision',value='main')
            count=st.number_input('Maximum raw rows to sample',min_value=1,max_value=2000,value=500,step=100)
            st.caption('This loads the first N raw rows, which may contain no matching culture/context. The resolved commit is recorded. A curated uploaded subset gives more controlled coverage. Requires the optional datasets package and outbound network access.')
            if st.button('Fetch research sample'):
                def fetch():
                    try:entries,meta=load_culturebank(split,revision,int(count))
                    except ImportError:raise StageError('Norm source','optional packages missing','Install requirements-norms.txt or upload a subset.') from None
                    except Exception:raise StageError('Norm source','dataset download failed','Check the split/revision and Hugging Face access, or upload a subset.') from None
                    clear_norm_data();st.session_state.norm_entries=entries;st.session_state.norm_source=meta
                handle(fetch);st.rerun()
        if st.session_state.get('norm_source'):st.json(st.session_state.norm_source)
        if st.button('Remove research entries and analysis results'):
            clear_norm_data();st.rerun()
        st.caption('Records and analysis results remain in this session only. Model weights may be shared on the cloud server; dialogue embeddings/results are never globally cached. Hosted server inference does not send dialogue to Groq or Hugging Face. Dataset/model downloads contact Hugging Face.')

def render(a):
    with st.expander('Explore relevant norms — experimental'):
        entries=st.session_state.get('norm_entries',[])
        st.caption('Per-norm adherence/violation estimates are relative zero-shot label scores. They are not the app’s 0–5 dimension ratings or a validated cultural assessment.')
        if not entries:st.info('Load a CultureBank-style subset in Settings to enable this analysis.')
        if st.button('Retrieve norms and analyze learner responses',key='norm-analyze-'+a.id,disabled=not entries):
            def analyze():
                server=st.session_state.server_settings
                settings=AnalyzerSettings(embedding_model=server.norms_embedding_model,classifier_model=server.norms_classifier_model,embedding_revision=server.norms_embedding_revision,classifier_revision=server.norms_classifier_revision)
                with st.spinner('Loading server-side models and analyzing relevant norms…'):
                    try:
                        models=public_models(settings)
                        digest=hashlib.sha256(json.dumps([e.model_dump(mode='json') for e in entries],sort_keys=True).encode()).hexdigest()
                        index=st.session_state.get('norm_index')
                        if index is None or index.digest!=digest:index=NormAnalyzer(entries,models);st.session_state.norm_index=index
                        report=index.analyze_attempt(a)
                    except StageError:raise
                    except Exception:raise StageError('Norm analysis','inference failed','Check models/resources or retry. No research result changed your rubric score.') from None
                st.session_state.setdefault('norm_results',{})[a.id]=report
            handle(analyze);st.rerun()
        report=st.session_state.get('norm_results',{}).get(a.id)
        if report:
            from .visuals import norm_chart
            norm_chart(report,'norm-chart-'+a.id)
            st.caption('Unreviewed research · no effect on official score · default thresholds are provisional')
            for turn in report['turns']:
                st.write('**Turn '+turn['turn_id'][:8]+' — '+turn['status'].replace('_',' ')+'**')
                for hit in turn['matches']:
                    st.write(hit['norm']);st.caption('Learner excerpt: '+hit['excerpt'])
                    st.write(hit['classification'].replace('_',' ').capitalize())
                    if hit['scores']:st.write({k:round(v,3) for k,v in hit['scores'].items()})
                    e=hit['entry'];st.caption(f"Retrieval cosine: {hit['retrieval_similarity']:.3f} · source: {e['source']} · revision: {e['source_revision']} · {e['source_split']} · dataset agreement: {e['agreement']}")
                    st.caption(hit['reason'])
            st.download_button('Export experimental norm analysis',json.dumps(report,indent=2),file_name='norm_analysis_'+a.id[:8]+'.json',mime='application/json',key='norm-export-'+a.id)
            st.caption('Export includes learner excerpts and source metadata. Interpret mixed/uncertain results in context; do not average them into a cultural score.')
        render_error()
