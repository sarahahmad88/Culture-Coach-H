# Two separate practice scorecards

New live attempts show **AI-estimated communication** and **Experimental Hofstede-informed scenario adaptation**. Both use a frozen authored rubric, 0–5 criterion ratings, equal weights, exact learner evidence, and deterministic Python calculation. Neither is an expert-validated cultural assessment. The original reviewed cultural score and level-recommendation gate remain separate and inactive.

## General communication

Five criteria are scored: clarity; respect and boundaries; supporting reasons; perspective-taking; and problem-solving. Each has six concrete behavior anchors (0–5) in `practice_scoring.py`. The evaluator supplies a rating, supporting learner turn IDs and a justification. A numerical rating requires validated learner evidence; no evidence means null, not zero. Respectfully challenging an expectation or maintaining a boundary may be effective communication.

## Hofstede-informed adaptation

The partner has authored fictional preferences informed by available national reference values across Hofstede’s six dimensions. This simulation is not a prediction of an individual’s personality. The learner is evaluated against preferences actually expressed by that partner, not against proximity to a country score or compulsory compliance.

A numerical adaptation rating requires an exact partner quote, its turn ID, and learner evidence following that cue. References to a later partner turn, invented quotes, unknown criteria, duplicates and inconsistent versions are rejected. A lack of relevant opportunity stays unscored. Relevance and the quality of the response remain model judgments; mechanical evidence validation does not establish human agreement or scoring validity.

Profiles can be **Country-informed** or **Contrasting** in setup. Contrasting profiles practice individual variation while preserving the source country values. A scenario freezes the selected profile, preferences and both rubrics before the conversation starts. Exact retry preserves that scenario and rubric.

## Reference source and coverage

Source: [Geert Hofstede’s dimension data matrix](https://geerthofstede.com/research-and-vsm/dimension-data-matrix/).

Dataset: the source-provided **2015-12-08 bounded 0–100 variant**, based on the original model. It is kept separate from newer revised Culture Factor data. Provenance, exact download URL, retrieval date and source hash are recorded in `data/hofstede_reference.json`.

The bundled subset covers the 14 app country labels. In this matrix, Egypt, Saudi Arabia and South Africa each have country-specific Long-Term Orientation and Indulgence values, but the other four dimensions are missing. No Arab-country or other regional aggregate is substituted. The UI shows these missing references as N/A and shows **reference coverage separately from evidence coverage**. UK maps to the source row Great Britain; it is not a separate measurement of all UK constituent nations. Greece’s Uncertainty Avoidance uses the source-provided bounded value 100, not the unbounded 112.

The routing bands (<40 / 40–60 / >60) and associated persona preferences are authored simulation choices, not empirically validated personality thresholds. Contrasting profiles reverse the lower/higher preference choices; middle-band preferences remain balanced. All six dimensions are displayed, but only dimensions with a country-specific reference can enter the adaptation rubric. Even available dimensions remain unscored when no relevant cue or learner evidence exists.

**Source use terms:** the source allows researchers to use the data without asking permission and asks prospective commercial users to contact it. This bundle does not claim a blanket commercial reuse license. Commercial operators should obtain the applicable permission from the source.

## Calculation and display

For each scorecard:

`overall / 100 = round(mean of available criterion ratings / 5 × 100)`

`evidence coverage = scored criteria / available rubric criteria`

Reference values do not serve as weights or learner targets. A genuine zero is retained; missing evidence is omitted. If nothing is scored, the overall is null. For example, one rated adaptation criterion out of six available criteria produces 17% evidence coverage, not a complete cultural assessment. A country with two available dimensions shows reference coverage 2/6 independently of its evidence coverage.

The feedback page shows separate overall metrics, dimension/criterion bar charts, explanations, evidence and partner cues. Country reference values appear in a separate table, not overlaid on learner scores. The dashboard summarizes saved live estimates. Progress trends require the same frozen scenario/persona, difficulty and rubric version; unrelated country/profile practices are not presented as comparable improvement. Five-star feedback usefulness remains a separate user rating.

## Cloud activation

1. Upload the updated source and `data/hofstede_reference.json`, including `practice_scoring.py` and `ui/practice_results.py`, then redeploy the cloud app. No new dependencies or database schema migration are required.
2. Start a **new** attempt. Older attempts did not freeze these rubrics and are not retroactively scored.
3. Choose a country/profile and Live Groq AI. Use `GROQ_MODEL = "openai/gpt-oss-120b"` and the existing server-side API key.
4. Complete practice. The evaluator can issue numerical estimates only when sufficient evidence exists. Partial adaptation scores are expected in short conversations.
5. Enable history before completing an attempt to retain results. Scores and coverage are included in metadata-only history; full history and exports also include rubrics and evidence. Existing Supabase JSONB columns support the new fields.

Scripted demo illustrates the UI and flow without personally scoring submitted responses. CultureBank label estimates remain separate and never feed either scorecard. Imports compare frozen rubrics with the server version and recompute both scorecards; altered reference values, criteria or arithmetic are rejected. Imports are untrusted personal records, not proof of authorship or reviewer approval. Older exports without these fields remain readable.

## Validation

Automated tests exercise numerical live scorecards with synthetic model responses, actual CrewAI integration with mocked Groq, arithmetic, missing values, cue chronology, frozen retries, profile variation, imports, metadata and UI charts. These tests do not validate the cultural meaning of profiles, rating reliability, fairness, calibration or hosted Groq quality. Human-reviewer comparisons and browser visual/accessibility checks remain necessary before making validated assessment claims.
