# Cross-Cultural Communication Practice

A modular Streamlit learning app based on the three supplied v2.0 PDFs and workflow infographic. It implements configure → scenario → 3/8/15-response practice → evidence → general feedback → learn → retry → progress.

**Start in Scripted demo. No credentials are required.** Demo dialogue and feedback are explicitly scripted. Demo produces no fabricated personal ratings. A separately sourced original Hofstede reference subset now grounds explicitly fictional personas; it is not a reviewed cultural assessment. Live mode runs the five focused CrewAI agents through a scoped Groq SDK transport.

## Browser-only deployment

Follow [DEPLOY.md](DEPLOY.md). Unzip the archive, upload its **contents** to a new GitHub repository using the GitHub website, then deploy `app.py` through Streamlit Community Cloud. No local terminal or Python installation is needed. Select Python 3.12. Demo needs no Secrets; Groq and authenticated history are optional.

## Modes and limits

- **Demo:** two draft fictional scenarios, zero LLM calls, fixed partner prompts, generic reflection feedback, exact learner transcript. Demonstrations are separated from live performance.
- **Live:** configurable Groq model (default `openai/gpt-oss-120b`), CrewAI tasks, stable frozen character and scenario, evidence validation and general feedback. Credentials and a successful hosted smoke test are required to verify this mode with real AI.
- **Cultural scores:** disabled for the supplied reviewed registry, which contains null approved country scores and no approved criteria. A separate reference dataset and authored practice rubric support experimental persona-adaptation estimates. All six framework dimensions appear with N/A or insufficient-evidence status. No numerical overall is fabricated. The deterministic scorer is ready for reviewed criteria, but activating a reviewed scenario also requires controller wiring and expert validation; editing a JSON status alone is not a production activation process.
- **History:** session-only by default. History consent starts off. Optional authenticated Supabase history requires Secrets, the supplied SQL migration and confirmed user accounts. Demo records never go to account history. Session preferences are not promised to survive restarts.
- **Supported contexts:** Workplace and University draft templates. Other contexts are rejected until curated templates exist. Fourteen country labels are offered as contextual inputs; they do not imply an approved cultural dataset.

## Module map

| Module | Responsibility |
|---|---|
| `app.py`, `ui/`, `styles.css` | Navigation and eight wireframe screens plus recovery states |
| `config.py`, `schemas.py` | Settings, exact levels, state and typed contracts |
| `orchestrator.py` | Explicit stages, frozen scenario and completion |
| `session_manager.py` | Accepted rounds, duplicate protection, transitions, exact retry |
| `llm_client.py` | Groq SDK, CrewAI custom BaseLLM, scoped payload filtering, budgets, JSON validation |
| `agents/cultural_context.py` | General contextual guidance, sourced registry limitations |
| `agents/scenario_designer.py` | Selected configuration → draft brief and opening |
| `agents/conversation_partner.py` | Single fictional person’s role-play, current attempt only |
| `agents/behavioral_evaluator.py` | Every learner turn → exact evidence, interpretation, uncertainty |
| `agents/feedback_synthesizer.py` | Validated evidence and scorecard → feedback and lessons |
| `demo_provider.py` | Explicitly scripted credential-free demonstration |
| `knowledge.py`, `data/registry.json` | Versioned provenance, draft templates and lessons; null country values |
| `tools.py` | Stage-specific real retrieval, scoped immutable snapshots |
| `scoring.py` | Evidence/approval gates, weighted arithmetic, coverage and draft recommendations |
| `repository.py`, `data/supabase.sql` | Isolated session store, authenticated optional cloud adapter and RLS |
| `diagnostics.py` | Redacted stage errors and reference IDs |
| `tests/` | Core, widget journeys, provider and storage contract checks |

This is a cloud-hosted application: learners open its deployed URL in a browser. No Python installation or local app launch is needed. Groq calls and optional embedding/classification inference run on the hosted server. Developer tests use `python -m unittest discover -s tests -v`.

See [DECISIONS.md](DECISIONS.md), [TRACEABILITY.md](TRACEABILITY.md), [VALIDATION.md](VALIDATION.md) and [REVIEW.md](REVIEW.md). This is an MVP implementation with explicit validation limits, not a claim of production readiness.

## Optional CultureBank-style analysis

The extension in [NORMS.md](NORMS.md) adds Sentence Transformers retrieval and Transformers zero-shot per-norm adherence/violation estimates. Load research entries in Settings and run analysis from a completed scorecard. It uses an optional CPU dependency profile; the base demo remains credential-free and does not load these models. Experimental scores are kept separate from the official rubric and never unlock progression. Imported community descriptions remain unreviewed research.

## Modern UI

Shadcn summary cards, Streamlit Extras, animated local role personas, Plotly performance charts and Altair activity / experimental norm charts are included in both dependency profiles. See [UI.md](UI.md) for motion settings, evidence gates, and deployment compatibility.

## Countries, model and feedback ratings

Training and Settings offer Pakistan, Japan, Germany, United States, China, Australia, UK, Saudi Arabia, Egypt, Brazil, Mexico, South Africa, France and Greece. These labels do not imply reviewed cultural criteria or complete dataset coverage.

Live mode uses the fixed `GROQ_MODEL = "openai/gpt-oss-120b"`. Older environment or Secrets model overrides do not change this selection. Keep your Groq API key in the host’s Secrets.

Completed feedback includes a one-to-five-star usefulness rating. It is separate from learner scores, follows history consent, is included in attempt exports and history metadata, and resets for each retry. Authenticated live history can persist ratings across sessions; demo ratings stay in session.

## Partner role consistency

Conversation requests bind the AI to the selected other person’s role in a request-scoped system instruction. Learner/partner identities and every transcript speaker are explicitly separated. Learner-perspective scenario text and objectives are labeled accordingly. Reply JSON must declare the exact partner role; wrong roles, exact whole-turn copying and explicit learner impersonation are rejected with one bounded repair. The controller never appends a rejected reply, preserving the learner turn for retry. These controls reduce role confusion but do not guarantee semantic fidelity in every generated sentence. Live Groq role-play quality requires hosted validation. Redeploy the updated source and start a fresh practice when replacing an older version that produced swapped-role dialogue.

## Provider recovery and rate-limit fallback

All completion requests use `http_retry.call_with_provider_backoff`: one initial attempt plus at most three retries on connection/timeout failures, HTTP 408/409/429 and 5xx. Exponential delays are 1, 2 and 4 seconds plus 0–0.25 seconds of jitter. Retry-After is a minimum delay. Each provider has a maximum individual wait of 30 seconds and cumulative sleep of 60 seconds per completion request; longer delays stop automatic retries. SDK retries remain disabled. Each HTTP attempt reserves shared call/output budget, including unsuccessful requests. Request timeouts remain 45 seconds; sleep limits are not a total wall-clock deadline.

After Groq HTTP 429 recovery stops, the same request moves to an optional distinct `GROQ_API_KEY_2`, then an optional `GEMINI_API_KEY`. Gemini uses Google's OpenAI-compatible endpoint with configurable `GEMINI_MODEL` (default `gemini-3.8-flash`). Missing keys are skipped; duplicate Groq keys are skipped. The selected fallback stays active for subsequent calls in that stage; a new stage starts with the primary key. A request can make at most twelve HTTP attempts across three configured providers, subject to the shared budget. HTTP 413 request-size rejection skips the second Groq key and goes directly to configured Gemini, with no unchanged-request retry. No fallback occurs for authentication, other invalid requests, persistent connection failures, server failures, or budget exhaustion. All exhausted providers leave the stage pending for manual recovery without re-submitting learner turns.

Failure references now correlate with sanitized cloud log metadata: stage, provider label, exception class, HTTP status, cause class, allowlisted provider status and a safe error-category hint. Exception messages, URLs, headers, credentials and transcript contents are not logged by these diagnostics. The feedback screen discloses when a second Groq key or Gemini was used; full exports retain those flags. Different models can produce different estimates; this does not establish cross-model score comparability.

Groq organization quotas are shared: a second key in the same organization does not create extra organization capacity. Gemini fallback uses Google's quota and may incur its own charges. See DEPLOY.md for server Secrets and the official references. No live provider calls were verified without credentials.

## Two practice scores

See [SCORING.md](SCORING.md). New live attempts include a five-criterion communication score and a separate Hofstede-informed scenario-adaptation score. Each shows coverage, charts and transcript evidence. The latter requires preceding partner cues. Original Hofstede reference values and authored/contrasting personas are shown separately from learner ratings. Missing country references stay N/A; demo stays unscored. Scores are included in exports and saved history. Start a new attempt after redeployment; old attempts are not retroactively scored. These are unvalidated AI estimates, not reviewed cultural judgments.

## HTTP 413 request-size correction

The evaluator now receives one compact authorized snapshot, with the rubric included once and transcript entries retaining exact IDs, speaker roles and complete text. Its closed retrieval tool is executed once server-side before CrewAI evaluation; it is not exposed for redundant model calls. The Behavioral Evaluation Agent still runs through CrewAI, using the same output schema and downstream evidence/cue/rating validation. No transcript is truncated or summarized, and no scoring anchor is removed. Feedback generation no longer receives unused copies of evaluator anchors.

If the complete request still exceeds Groq's accepted size, configured Gemini is tried directly. HTTP 413 is not retried against the same Groq key or switched to another Groq key. Without Gemini, the user gets an explicit size-limit message and retains the pending stage. This reduces duplication and adds recovery; it does not guarantee every request fits every provider quota. The output reservation remains unchanged.

## Feedback tool-input correction

Like evaluation, feedback synthesis now retrieves its frozen authorized bundle once server-side and supplies it directly to the CrewAI agent. No provider tool/function declarations or tool-response messages are needed for these two stages. The feedback prompt requests one Feedback object rather than a tool action, argument array, or copy of the input bundle. Schema repair remains bounded to one additional attempt with stage-specific guidance. Approved lesson-ID checks and validated evaluation/scorecards remain in the controller; a failed feedback attempt leaves evaluation and transcript intact for retry.

The reported `Repaired JSON` output originates in CrewAI's tool-input repair path. It does not mean that a Feedback object was produced or accepted. Removing that unnecessary path addresses the observed malformed argument handling; it does not prove the exact reason Gemini returned HTTP 400. Diagnostics now inspect provider error bodies only to derive allowlisted provider status and known category hints, never logging the raw message. `unknown` is preserved if the body cannot be safely classified.
