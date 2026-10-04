# Validation report

Date: 2026-10-04. Runtime: Python 3.12.14, Linux. The original base profile passed 33 tests in an isolated virtual environment. The updated source passed 46 tests with the installed optional CPU profile (`requirements-norms.txt` and `constraints-norms.txt`). The base deployment profile remains separate.

## Results

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -v` | **46 tests passed (updated source, optional CPU profile)** |
| `pip check` | **No broken requirements found** |
| Streamlit, CrewAI, Groq, Supabase imports | **Passed** |
| `python -m compileall -q .` | **Passed** |
| Streamlit HTTP `/_stcore/health` | **HTTP 200, `ok`** |
| ZIP integrity / source inclusion | Checked during packaging |

Direct installed pins: Streamlit 1.49.1, CrewAI 1.1.0, Groq 0.32.0, Pydantic 2.11.9 and Supabase 2.19.0. The original runtime closure and UI dependency pins are recorded in `constraints.txt`. These are the tested versions, not a claim to use every package’s latest release. Unconstrained installation initially encountered malformed downloads/hash errors; a compatible installed closure was resolved, pinned and then installed into the isolated final environment. The final `pip check` succeeded. Tests use Python’s built-in unittest and Streamlit AppTest, so pytest is not required.

## What was exercised

- Every required setup input; supported context/role validation; same-culture practice.
- Beginner 3, Intermediate 8 and Advanced 15 accepted responses; no extra partner turn after the final learner response.
- Empty and duplicate submissions; failed reply preservation and retry without double-counting.
- Stable scenario across turns; immutable attempt ID/configuration; exact retry gets distinct attempt and parent IDs with the same frozen scenario.
- Null country values; applicable versus irrelevant dimensions; unreviewed criteria rejection.
- 2/3/4/2/3 → 56; weighted, zero and all-null arithmetic; synthetic reviewed behavior-anchor fixture and weighted dimension aggregation/coverage.
- Every learner turn requires exact evidence; invented quotes, missing turns and unsupported criteria are rejected.
- Export round-trip, scorecard recalculation/tampering rejection, import size limit.
- Independent session stores, metadata-only saving, deletion and redacted error messages.
- Groq payload cache-marker removal with native function name/arguments, assistant tool call and tool result IDs preserved; real Python function executed in a mocked native tool exchange.
- **All five actual CrewAI agent/task factories executed**, with their real stage retrieval tools invoked through ReAct, using mocked Groq SDK completion responses. The app controller completed a three-response live-mode journey with provider responses mocked. No live Groq key was used.
- One bounded JSON schema repair and no scripted fallback for missing live credentials.
- Optional Supabase adapter: verified identity contract, user filters, metadata-only writes, expired-session rejection, write failure/redaction, and deletion confirmation with **mocked clients**.
- Streamlit AppTest: first-time screens, full credential-free completion, feedback, targeted lessons, saved progress, exact retry, empty-error handling, incomplete exit, deletion, missing live key and University template.

The Streamlit 1.49 AppTest helper settles an ordinary rerun after explicit app reruns because its element tree can retain removed form nodes. This is test harness handling, not a claim of pixel-level browser verification.

## Not verified and required before broader use

| Area | Status / next step |
|---|---|
| Actual Groq model visibility, quotas, latency and structured output quality | **Not verified**; no credentials supplied. Perform a hosted Beginner live smoke test, then Intermediate/Advanced and error paths |
| Actual Supabase Auth, RLS and durable writes | **Not verified**; no project credentials supplied. Apply SQL, provision accounts and run a two-account isolation/deletion test |
| Cultural country dataset and licensing | **Unavailable**. Delivered numeric values are null. Obtain licensed/provenanced material with expert approval |
| Cultural scoring and evaluator validity | **Not activated**. No reviewed criteria supplied. Synthetic tests validate arithmetic/contracts, not cultural correctness or fairness |
| LLM prompt-injection behavior | Prompts and tool boundaries tested structurally; **no adversarial live-model study**. Agents cannot access arbitrary users, edit rules or calculate scores through tools |
| Desktop/mobile visual layout | **Not visually verified in a browser**. Chromium download failed in this environment; AppTest validates widgets/reruns rather than rendering |
| Keyboard, screen reader, contrast and reduced-motion audit | Labels, focus styles, touch targets and CSS implemented; **independent browser audit pending** |
| Community Cloud deployment | Package and instructions delivered; **not deployed to a user account** |
| Expert evaluation agreement / real learner outcomes | **Not studied**. Use REVIEW.md, independent expert anchors and user research |

## Operational scope

Only Workplace deadline and University group-responsibility draft templates are supported, with documented roles/goals. History consent defaults off. Preferences and session progress are not durable. Optional accounts support existing confirmed login; self-service registration/recovery/account deletion are not implemented. Cloud history reads are capped at 100 records and lack pagination. Mid-request cancellation is not implemented; per-request timeout, call/output budgets, manual stage retry and incomplete exit apply between requests. CrewAI telemetry/tracing are disabled, including its hosted-server first-run trace prompt; no global SDK code is patched.

No claim of production readiness is made. The app is a runnable MVP demonstration and an independently testable starting point for live general communication coaching.

## CultureBank extension verification

The optional stack installed and imported successfully: Sentence Transformers 5.1.1, Transformers 4.57.1, datasets 4.2.0, PyTorch 2.8.0+cpu, Hugging Face Hub 0.35.3 and tokenizers 0.22.1. An fsspec version conflict was corrected to 2025.9.0; the final optional `pip check` reports no broken requirements. `constraints-norms.txt` records the optional inference closure plus UI dependency pins. No CUDA dependency set is installed.

Real public model weights loaded successfully at these revisions:
- `sentence-transformers/all-MiniLM-L6-v2`: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- `facebook/bart-large-mnli`: `d7645e127eaf1aefc7862fd59a17a5aa8558b8ce`

A real local end-to-end smoke test using the explicitly fictional format fixture passed at the default similarity threshold: cosine approximately 0.611, classifier estimates adherence approximately 0.849, violation 0.111 and unclear 0.039. These numbers describe that test fixture/model inference only; they are not validated cultural judgments or a learner score. A less closely aligned synthetic response produced no relevant match at the default threshold, confirming that retrieval coverage and abstention depend on calibration.

A real streamed 10-row Reddit sample from `SALT-NLP/CultureBank` resolved dataset commit `f806940c0c0c0a7807a36642dd05672eb74e8729`. All ten rows were excluded by the required Workplace/University context rules. This verifies dataset access/provenance and honest empty-result handling, not coverage of the target cultures or contexts. Actual CultureBank descriptors were not expert-reviewed or used to enable the official cultural rubric.

The new 13 tests use injected encoders/classifiers for deterministic contract checks and a mocked model resource for the web-panel journey. They cover field/provenance normalization, no auto-approval, culture/context filters, cosine ranking, norm-specific hypotheses and label-order mapping, adherence/violation/unclear values, margin abstention, missing matches, exact text chunks, token-limit abstention, malformed predictions, unchanged official attempt state, example data labeling, and deletion of session analysis. The real model/dataset smoke checks above are additional manual integration checks, not the unit test fixtures.

Still unverified: human cultural assessment accuracy, per-culture retrieval coverage, NLI score calibration/fairness, multilingual performance, resource fit on a user’s deployed Cloud app, and browser visual/accessibility behavior. Live Groq and Supabase remain unverified as in the original report. The research panel’s estimates never affect official scores/progression.

## Modern UI update

The revised source passes **52 tests** in the Python 3.12 test environment with the UI libraries installed. `pip check` succeeds. The 46 existing tests still pass, including mocked inference and full widget journeys. Six new tests check live/demo chart gates, missing values, chronological order and fixed scale, safe persona markup, empty activity, and mode filtering. Streamlit HTTP health returns 200 / `ok`.

Installed UI releases: streamlit-shadcn-ui 0.1.19, streamlit-extras 0.5.5, Plotly 6.3.0 and Altair 5.5.0. Shadcn uses the pre-V2 API compatible with pinned Streamlit 1.49.1. Extras 0.7.8 could not resolve against existing pins; 0.5.5 resolved successfully. Browser pixel checks, animation playback and keyboard testing remain unverified (no Chromium available). Prior local-model smoke tests are historical; this UI update did not repeat model downloads or real inference.

## Cloud country and feedback-rating update

**58 tests passed** on the revised source; dependency checks and compilation pass. Six additional checks cover the 14-country selectors and registry, new country aliases without subgroup collapse, exact model selection despite stale overrides, rating export/range validation/retry reset, history consent, and the feedback-widget interaction/deletion journey. The native `st.feedback` widget uses a test-only AppTest serializer adapter because Streamlit 1.49 treats feedback values as None/int while its test ButtonGroup wrapper assumes a list and formatter. Production Streamlit is unchanged. Browser rendering, actual hosted service calls, resource fit and expert cultural validation remain unverified.

## Partner-role correction

**63 tests passed**; compilation and dependency checks pass. Five new regression tests cover role-separated retrieval payloads for both templates, rejected wrong roles/copied learner turns/explicit learner labels, controller preservation and recovery of pending learner turns, request-scoped system identity ahead of role-switch text, and bounded repair through actual CrewAI execution with mocked Groq. Replies declare the exact partner role. Narrow text checks detect some explicit impersonation but are not a general semantic role classifier. Actual live Groq response quality and browser behavior remain unverified.

## HTTP 429 retry update

**70 tests passed**, with compilation and dependency checks passing. Seven new tests verify exponential jittered recovery, Retry-After minimum delays and long-wait rejection, maximum retries and non-429 behavior, cumulative sleep limits, numeric/date/malformed header parsing, adapter integration with unchanged transcript and per-attempt budget charges, and budget exhaustion before another HTTP request. Sleeps and HTTP failures are mocked: no actual rate-limited live Groq request was made. Sleep budgets are separate from per-request network timeouts.

## Two practice scorecards and persona grounding

**83 tests passed** on the updated source. Compilation and dependency checks pass; Streamlit HTTP health returns 200 / `ok`. Thirteen additional tests cover the country reference subset and missing dimensions, independent scorecards and genuine zero/null arithmetic, partial reference N/A and coverage, partner-cue quotation/chronology, demo abstention, export recomputation and tamper rejection, criterion/evidence validation, frozen retries and contrasting personas, separate metadata, legacy export compatibility, actual CrewAI execution with mocked numerical evaluator output, score-panel and comparable-trend UI flows, and bounded invalid-evaluation recovery while preserving all learner turns.

The original-source CSV was downloaded from the published 2015 bounded 0–100 URL and normalized into a 14-country subset with provenance and source hash. Four dimensions remain missing for Egypt, Saudi Arabia and South Africa. Original-source research/commercial-use terms are documented in SCORING.md. The preference mapping and rubric anchors are authored simulation choices. These tests validate software contracts and arithmetic, not cultural/personality inference, fairness, reliability or agreement with expert raters. No new live Groq/Supabase validation or browser pixel/accessibility review was performed. Scripted demo remains personally unscored. The original reviewed cultural gate remains separate.

## Neon score UI update

**83 existing tests passed** after applying the score theme. Compilation passes. A direct palette check confirms eleven distinct criterion/dimension colors plus three separate score-category colors, and HTML labels remain escaped. The changes affect presentation only: numeric scoring, evidence gates, missing-value behavior and existing UI flows remain covered by the existing suite. Browser rendering, glow appearance, mobile visual layout and screen-reader/keyboard verification remain unverified because no browser engine is available.

## Reference-inspired neon app redesign

**83 existing tests passed** after the dashboard and navigation redesign. Compilation and dependency checks pass. Widget navigation, training, feedback ratings, scoring displays, and progress flows remain covered by the existing tests. This update adds a local SVG hero, five CSS SVG navigation icons, learning-loop action tiles, a dark Streamlit theme, and responsive styling. Browser rendering, actual sidebar icon placement, animation playback, mobile layout, keyboard behavior, and contrast remain unverified. No live service calls or deployment were performed.

## Provider recovery and ordered key fallback

**95 tests passed**. Twelve new checks cover transient network/timeout/408/409/5xx recovery, bounded retries, non-retryable failures, server Retry-After, budget exhaustion, safe diagnostic logs, preserved evaluation recovery, ordered primary/secondary/Gemini routing, identical stage context and Groq model, Gemini token-limit translation, missing/duplicate key skipping, no cycling, and Secrets loading. The full mocked-provider and widget suites still pass. Compilation and dependency checks pass. No real Groq or Google key was supplied, so live Gemini endpoint compatibility, actual model availability, quotas, latency, generated evidence quality and cloud networking remain unverified.

## HTTP 413 and evaluator request size

**100 tests passed**, including five new regression checks. Tests verify a single complete rubric, all thirty maximum-length synthetic transcript turns without truncation, one server-side evaluator retrieval and one mocked provider request, direct Gemini routing on 413 without retrying Groq or using the second Groq key, explicit failure when Gemini is absent, and removal of unused rubric copies from feedback. Existing numerical scoring, mocked CrewAI, key fallback, retries and widget tests still pass. Compilation and dependency checks pass. Live request sizes/tokens accepted by user accounts remain unverified. This test count does not establish the beta's unit-coverage, live integration or UAT targets.

## Light UI update

**100 existing tests passed** after changing the presentation to light mode. The Streamlit theme explicitly uses light mode, and custom sidebar, hero, persona, conversation, score and Plotly surfaces use light backgrounds. Existing unique criterion/dimension neon accents remain. Compilation passes. No backend, scoring or provider behavior changed. Browser rendering, responsive layout and contrast/accessibility audit remain unverified.

## Feedback synthesis request and diagnostics

**104 tests passed**. Four new checks cover the real pinned OpenAI SDK with an injected HTTP transport carrying tool-free Gemini feedback, array/bundle rejection and a single successful schema repair, allowlisted provider-body diagnostics without leaking raw text, and preserved evaluation/transcript after a failed feedback stage and manual recovery. The transport verifies actual serialized messages and token parameters; its responses are mocked, so this is not a live Google compatibility test or provider-quality validation. All previous widget, five-agent CrewAI, numerical scoring, HTTP backoff and key fallback tests pass. Compilation and dependency checks pass. Light UI remains unchanged. The reported 400's exact provider-side cause and live resolution remain unverified.
