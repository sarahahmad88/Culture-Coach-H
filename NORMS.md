# CultureBank-style retrieval and experimental dialogue analysis

This extension implements the requested **Sentence Transformers embeddings → relevant cultural descriptions → Transformers zero-shot adherence/violation estimates**. It is optional: the credential-free scripted app and Groq/CrewAI workflow still use the normal dependency profile.

CultureBank contains community-derived contextual descriptions, including diverse views. Its dataset fields are not an expert-approved behavioral scoring rubric. Semantic similarity measures retrieval relevance, and the classifier’s scores are relative NLI label estimates. Neither establishes that a person is culturally correct. This extension never changes the app’s overall score, dimension ratings, approved registry or progression decisions.

## Use in the web app, with browser-only deployment

1. Upload the updated project contents to your GitHub repository, including `culturebank_adapter.py`, `norm_analyzer.py`, `ui/norm_analysis.py`, `requirements-norms.txt` and `constraints-norms.txt`.
2. To enable server-side model inference, open **`requirements.txt` in GitHub’s browser editor and replace its contents with the exact contents of `requirements-norms.txt`**. Keep `constraints-norms.txt` at the repository root. This optional profile includes the base app, Sentence Transformers, Transformers, datasets and CPU PyTorch. It deliberately uses compatible Hub/tokenizer/fsspec versions rather than mixing both constraint profiles.
3. Redeploy/reboot the Streamlit app on Python 3.12. Model downloads need outbound Hugging Face access and sufficient disk/RAM. The default BART model is substantial; resource-limited hosts may need a smaller validated classifier or a host with more memory. CPU dependencies do not include the CUDA package set.
4. Open **Settings → Experimental cultural norm analysis**. Upload a curated CultureBank-style CSV/JSON subset and supply its source. Alternatively, fetch a bounded Reddit/TikTok sample from Hugging Face. The resolved dataset commit is recorded. The first N rows may have no matching Japanese workplace or other selected context; partial samples are not full dataset coverage.
5. Complete a training attempt. Open **Explore relevant norms — experimental** and click **Retrieve norms and analyze learner responses**.
6. Review matching source entries, cosine similarities, exact learner excerpts, per-norm adherence/violation/unclear scores, and uncertainty. Export the research report separately if desired. These estimates are not saved to account history.

The included `data/norms_example.json` demonstrates the format using **fictional general-coaching entries**, not actual CultureBank records or verified Japanese/American norms. If loading that file, name the source “FICTIONAL format example; not CultureBank data.” Agreement values are null. Use real sourced subsets for research and obtain contextual expert review before interpreting cultural implications.

Optional server Secrets can configure models and immutable revisions:

```toml
NORMS_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
NORMS_CLASSIFIER_MODEL = "facebook/bart-large-mnli"
NORMS_EMBEDDING_REVISION = "main"
NORMS_CLASSIFIER_REVISION = "main"
```

`main` is resolved to an immutable commit before loading, and the actual commits appear in the report. You can instead configure specific model commit hashes. Default models are intended here for English input. A different language requires appropriate multilingual models and evaluation; translation is not silently performed.

## Input mapping

| CultureBank-style field | Use |
|---|---|
| `cultural group` or `cultural_group` | Exact normalized culture/alias filter |
| `context` | Included in retrieval and norm hypothesis; must be present |
| `actor_behavior` | Required behavior descriptor; the scoring hypothesis is built from it |
| `actor`, `recipient`, `relation` | Role/relationship context; applicability still requires review |
| `goal`, `recipient_behavior` | Retrieval context |
| `agreement` | Source metadata only; never a learner score or certainty weight |
| `context_tags` | Optional list, or CSV `Workplace|University`, for explicit search filtering |
| `eval_question` | Not used as a norm; benchmark question cannot substitute for actor_behavior |
| source, split, resolved revision | Recorded separately by the adapter |
| uploaded approval status | Ignored; all imported entries are `unreviewed_research` |

Without explicit context tags, a narrow keyword heuristic identifies Workplace or University contexts. Unknown or missing context is excluded rather than forced into the practice. Country aliases use exact names and demonyms for all 14 selectable countries (including UK/United Kingdom/British). They are not inferred via broad substring matching. Subgroup labels are not automatically collapsed into a nation. Adding country labels and aliases does not establish dataset coverage or cultural validity.

## Processing and interpretation

1. Normalize/validate records, preserve provenance and deduplicate content. Upload bounds are 2 MB and 2,000 rows.
2. Use `SentenceTransformer.encode_document()` to embed eligible research entries. Normalize embeddings. Corpus embeddings are session-scoped.
3. For each learner turn, combine a bounded preceding partner prompt, role, goal and setting with exact learner text segments. Long learner text is chunked with source offsets; exceeding limits abstains rather than silently discarding the rest.
4. Filter by culture/context, then use `encode_query()` and cosine similarity for top-k retrieval. Default top-k is three and minimum similarity is 0.35. These are provisional engineering choices, not validated cutoffs.
5. For each retrieved descriptor, run `pipeline("zero-shot-classification")` against three **norm-specific hypotheses**: follows the described behavior, contradicts it, or lacks evidence/does not match the actor role. Generic labels without the retrieved norm would not evaluate that norm.
6. With `multi_label=False`, scores are normalized across these three labels. They are not calibrated probabilities of real cultural appropriateness. Default confidence 0.70 and margin 0.15 trigger cautious labels only; ties/weak evidence produce insufficient evidence. Contradictory segment readings remain visible.
7. Return source IDs, revision/split, exact turn/excerpt/span, retrieval similarity, all label scores, model revisions, corpus digest and limitations. Do not convert these scores into the app’s 0–5/100 rubric ratings.

The model checks roles through supplied context and hypotheses; this is not a validated role-alignment system. NLI cannot by itself establish humor, sarcasm, intent, speaker attribution, valid boundaries or whether a social practice is desirable. A full unstructured dialogue string should not be treated as if every speaker’s statement were the learner’s behavior. The web app evaluates learner turns with preceding partner context; the CLI expects a single learner response or excerpt.

## Reusable Python usage

After installing the optional profile on a server, the code can be called from another Python workflow:

```python
from pathlib import Path
from culturebank_adapter import read_entries
from norm_analyzer import AnalyzerSettings, LocalModels, NormAnalyzer

raw = Path("research_subset.json").read_bytes()
entries, skipped = read_entries(
    raw, "research_subset.json",
    source="Your sourced cultural research subset",
    revision="your-version-or-content-hash",
)
models = LocalModels.load(AnalyzerSettings())
analyzer = NormAnalyzer(entries, models)
report = analyzer.analyze_turn(
    "Testing needs three weeks. Could we discuss a phased release?",
    culture="Japan", context="Workplace",
    goal="Raise a concern", learner_role="Junior employee",
    partner_prompt="We need to finish within two weeks.",
)
```

The public-model cache contains only weights and an inference lock. Dialogue queries and results are not globally cached. Local inference does not send dialogue to Hugging Face/Groq; model and dataset downloads contact Hugging Face. Results and research entries are cleared on deletion, login/sign-out identity changes, or the panel’s remove action. Downloaded exports remain outside app control.

For developers, the separate CLI is available from the project folder:

```bash
python norm_analyzer.py --entries research_subset.json --dialogue response.txt \
  --culture Japan --context Workplace --role "Junior employee" \
  --goal "Raise a concern" --source "Your research source" \
  --revision "your-version" --output norm_report.json
```

## Validation and remaining activation work

The extension’s tests cover actual field names, provenance/no auto-approval, missing norm fields, filters/ranking, norm-specific hypotheses, shuffled classifier label order, per-norm scores, confidence/margin abstention, exact chunks, token-budget abstention, malformed outputs, and no modification of the original attempt/scorecard. Model outputs in these tests are injected test fixtures, not real predictions.

The optional CPU dependencies installed and passed `pip check`; a real embedding-to-classifier smoke test passed with the fictional example. A real 10-row CultureBank Reddit sample streamed successfully but yielded no supported-context entries. These checks establish integration, not cultural accuracy. See VALIDATION.md for exact revisions and remaining limits. Before relying on the output, validate retrieval coverage, role/context relevance, false-positive violations, direct/indirect reasonable alternatives, uncertainty handling and score calibration against independently reviewed examples. Dataset agreement does not replace this work. Respectful disagreement and legitimate boundaries must not be penalized because a retrieved community description suggests deference.

Official sources:
- Dataset/schema/license: https://huggingface.co/datasets/SALT-NLP/CultureBank
- Research/provenance: https://aclanthology.org/2024.findings-emnlp.288/
- Embedding retrieval API: https://sbert.net/examples/sentence_transformer/applications/semantic-search/
- Zero-shot pipeline: https://huggingface.co/docs/transformers/main_classes/pipelines
- Default embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- Default classifier: https://huggingface.co/facebook/bart-large-mnli

## Cloud runtime

The application runs on Streamlit Community Cloud or another hosted Python server. Users access a URL from their browser. Optional Sentence Transformers and Transformers models execute on that cloud server’s CPU, not on users’ computers; Groq generation uses the remote Groq API. Select the optional requirements profile on the host only when it has enough memory and download access. No local app installation is required.
