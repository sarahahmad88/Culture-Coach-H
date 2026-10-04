# Implementation decisions and reference conflicts

All three PDFs were extracted in full. Their wireframe screenshots and the infographic were inspected. The initially reported missing image was available at the attached path during implementation.

| Decision | Basis and consequence |
|---|---|
| 56, not pictured 78 | Example 2/3/4/2/3 out of 5 → 56/100 under equal weighting; infographic metrics remain illustrative |
| No approved cultural dataset | Attachments define a framework, not a licensed, reviewed country-score registry. All country values are null. Draft templates are never promoted automatically |
| No numeric demo assessment | Scripted dialogue cannot evaluate arbitrary text. Demo offers generic reflection prompts with exact transcript excerpts and explicit limitations |
| General feedback in live mode | Cultural criteria remain empty and cultural arithmetic returns null. Live evidence analysis and coach feedback can still support practice |
| Equal weights | Equal criterion weights within dimension and equal valid dimension weights by default. Missing evidence is excluded; 0 remains a real rating |
| Python rounding | Formula uses Python `round`, including its ties-to-even behavior. No hardcoded gauge |
| Five focused agents | Implementation requested in master prompt, not mandated by PDFs. CrewAI agents have only one narrow retrieval tool each and no delegation or manager |
| Groq SDK custom BaseLLM | Avoids global library patches and additional provider dependencies. Recursive removal of cache markers preserves native tool-call IDs/arguments. No Gemini dependency/key |
| Structured outputs | Tool phase uses native function calling; final response is parsed and Pydantic-validated. One schema-format repair, with one separate evidence-validation retry. Invalid ratings are never silently accepted |
| General two-template scope | Workplace deadline concern (PRD example) and University group responsibilities (new contrasting fictional draft). Other settings need curated templates; not advertised as supported |
| Culture selection | Four labels are contextual inputs only. Same-culture practice allowed. No personality inference or nationality rating |
| Configuration freeze | All eight selected inputs are passed to scenario generation. Individual character and project constraints are fixed before practice. Edit setup regenerates instead of mutating a running rubric |
| Round definition | Accepted learner responses only; opening is not a round. Final response goes directly to evaluation. Failed partner reply remains pending and retried without adding a turn |
| Duplicate policy | Submission IDs and immediately repeated learner text are rejected. Repeating identical text deliberately requires changing wording; documented usability tradeoff |
| Retry comparison | Exact retry preserves frozen scenario ID, criteria, configuration and character but has new attempt ID/transcript and parent link. New setup is new practice |
| Draft progression | Three live scored current-level attempts, average ≥70 and coverage ≥60%; editable config, recommendation only, not a validated threshold. No automatic cultural recommendation is possible with the current registry |
| Opt-in history | Consent off by default; active conversation always lives in session. Full history optional; metadata-only excludes transcript/evaluation/feedback. Analytics are not collected; no placebo analytics toggle |
| Optional cloud accounts | Supabase is chosen as an optional adapter, not a PDF requirement. Server-verified Auth identity and SQL RLS isolate data. Session store is never described as durable |
| Settings lifetime | Culture, level and display preferences persist only for this session. No unimplemented account preference promise |
| Operator-managed accounts | Existing confirmed account login is implemented. Self-service registration, recovery and account deletion are outside this MVP and documented |
| Reviewer export | Learner-controlled personal JSON export and REVIEW.md support UC-17. No enterprise admin dashboard or automatic rule promotion |
| Accessibility | Explicit labels, textual scores, visible focus, touch-sized controls, responsive columns, reduced-motion CSS and Streamlit compact sidebar. Requires browser/auditor validation, not inferred certification |

Reviewed cultural activation requires licensed/provenanced records, expert-reviewed behavior anchors for all ratings 0–5, a relevant template-to-criterion binding in the controller, mapped evidence, and a reference evaluator study. The seeded registry deliberately cannot generate an authoritative cultural score.

Additional implementation details: the tested CrewAI version executes tools through its ReAct parser; the custom adapter also supports native tool calls and that path has its own regression test. Hosted-server SDK telemetry/tracing and first-run trace prompts are disabled with explicit environment settings (`CREWAI_TESTING=true` suppresses the SDK’s first-run collection). The scoped Groq adapter does not monkey-patch CrewAI. Supported draft role pairs are Junior employee → Senior manager and Student → Fellow student; other roles are rejected before generation. Supported goals are limited per template so a fixed demo cannot silently contradict the selected configuration.

## CultureBank research extension

The subsequent user request authorizes Sentence Transformers and Transformers as optional server-side inference alongside Groq generation. `culturebank_adapter.py` imports actual CultureBank-style fields, preserves source versions and treats entries as unreviewed research; no dataset agreement becomes a learner score. `norm_analyzer.py` uses culture/context filtering, semantic top-k retrieval and norm-conditioned three-label zero-shot NLI. Provisional similarity/confidence/margin cutoffs permit abstention; the panel never changes approved criteria, overall arithmetic or progression. Norm hypotheses include actor context but role applicability remains a validation limitation. Long inputs are segmented and over-budget model inputs abstain. Public model weights can be cached globally; corpus/query/results stay session-scoped and are removed at identity/deletion boundaries. The optional dependency profile uses CPU PyTorch and compatible Hub/tokenizer/fsspec overrides. NORMS.md explains deployment and limitations.

## Cloud country and rating update

Countries are centralized in `config.CULTURES` and mirrored by null-valued registry records; aliases use exact country names/demonyms and never match arbitrary subgroups. Live configuration uses the fixed `GROQ_MODEL` constant requested by the user. This is a cloud-hosted app: server-side CPU inference is compatible with browser-only client use.

The native Streamlit star widget rates feedback usefulness from 1 to 5. Nullable ratings are part of Attempt, validated on import, included in JSONB history metadata and full exports, and follow existing consent/account isolation rules. Retry creates an unrated attempt. Widget state is cleared at sign-in, sign-out and deletion. No SQL migration is needed for a new JSONB field.

## Partner-role correction

The prior partner instruction did not resolve whose perspective the learner-oriented scenario brief and goal belonged to. `partner_contract.py` binds the selected partner identity independently from learner goals, and the Groq adapter prepends that identity as a request-scoped system message. Retrieval labels learner-perspective fields and role-tags transcript turns. `PartnerReply` requires a speaker role; provider validation permits one bounded format/role repair, and controller validation prevents rejected output from being committed. Narrow text checks reject copied turns and explicit learner labels/role claims. These checks cannot prove the semantic perspective of arbitrary prose; live validation remains necessary.

## HTTP 429 backoff

A dedicated transport-level policy retries only 429 responses, up to three times, with exponential delays and additive jitter. SDK `max_retries=0` prevents multiplying automatic retry layers. Numeric and HTTP-date Retry-After values are respected as minimum delays; over-limit waits return the original failure rather than violating the provider delay. Individual waits cap at 30 seconds and cumulative sleep at 60 seconds per completion request; every attempted request reserves existing call/output budget. Budget errors propagate without retry or misclassification. HTTP retry does not rerun the controller submission, append learner turns, or execute tools again unless a subsequent successful model output requests them. No new dependencies are required.

## Two authored practice rubrics

The user explicitly authorizes both general communication and separate Hofstede-informed adaptation. These use new frozen PracticeRubric/Evaluation fields and PracticeScores, preserving the original reviewed cultural scoring gate. The communication rubric has five criteria with 0–5 anchors. Adaptation uses authored preferences mapped from available original-source country references, requires preceding quoted partner cues, and does not reward proximity to national scores. Missing source dimensions remain absent from adaptation criteria and visible as N/A; regional values are never substituted. Country-informed and contrasting personas share source values and vary authored preferences. Original-source permission language and limitations are included in SCORING.md. The partner/designer receive preferences without evaluator anchors. Python validates evidence, recalculates exports, stores separate history metadata and plots comparable score trends. Sidebar widget identity is stabilized while connecting the new numeric feedback flow.
