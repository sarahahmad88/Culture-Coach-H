# Requirement traceability

Authority: PRD v2.0 defines scope; Use Cases v2.0 expands interactions; High-Fidelity Wireframes v2.0 defines screen structure. The master build text selects Python, Streamlit, CrewAI and Groq. The infographic is a conceptual example, not evidence for real country scores or user metrics.

## PRD functional requirements

| ID | Implementation | Verification / limitation |
|---|---|---|
| FR-01 User setup | `ui/setup.py`, `schemas.py` | `test_all_eight_required`; culture labels only, no verified country values |
| FR-02 Culture selection | `ui/setup.py`, `schemas.py` | `test_same_culture`; four labels offered, same-culture allowed |
| FR-03 Scenario configuration | `schemas.py`, `ui/setup.py` | `test_unsupported_context`, `test_ids_frozen_and_supported_roles`; only two draft templates and their supported role/goal combinations |
| FR-04 Experience level | `config.py`, setup/conversation UI | `test_3_8_15_and_final_no_partner` |
| FR-05 Dynamic scenario generation | scenario agent, `orchestrator.py` | `test_real_crewai_five_agents_with_mock_groq`; actual live quality unverified |
| FR-06 AI character | scenario/partner agents, frozen `Scenario` | scenario stability assertion, mocked CrewAI journey; live continuity needs review |
| FR-07 Conversation | partner agent, conversation UI | demo journey and mocked live journey |
| FR-08 Round control | `session_manager.py` | 3/8/15, duplicate/empty/failure tests |
| FR-09 Response analysis | evaluator agent, evidence schema | `test_evidence_exact_and_complete`; live interpretation unverified; demo explicitly not analyzed |
| FR-10 Cultural mapping | relevant dimensions, evaluator contract | evidence-mapping validation; maps are exploratory, culture-specific scoring unavailable |
| FR-11 Dimension scoring | `scoring.py` | synthetic reviewed rubric test; no approved cultural criteria in delivered data |
| FR-12 Overall score | `scoring.py` | 56 example, weighted/null/zero tests; no fabricated overall |
| FR-13 Feedback | coach agent, scorecard UI | five-agent mocked journey, full demo widget journey; scripted reflection limitations |
| FR-14 Alternative response | `Feedback`, coach and scorecard | demo and mocked live rendering; not one required phrase |
| FR-15 Explanation | evidence ledger, uncertainty, coach | exact quote validation, ledger UI; human interpretation review required |
| FR-16 Retry | `session_manager.retry`, scorecard | `test_exact_retry_distinct`, complete/retry widget test |
| FR-17 Progress | repositories, progress/dashboard UI | session isolation, metadata-only tests; optional Auth adapter with mocked contracts, live storage/RLS unverified |

## Use cases

| ID | Implementing modules | Test or documented limitation |
|---|---|---|
| UC-01 Start training | dashboard/setup | first-time and complete journey widget tests; no mandatory registration in session demo |
| UC-02 Configure cultural context | setup, schemas, knowledge | all required inputs; limited draft configurations |
| UC-03 Select experience level | config/setup | exact 3/8/15 tests and level UI |
| UC-04 Generate training scenario | context/scenario agents, controller | mocked real CrewAI execution; unsupported setup rejected |
| UC-05 Initialize AI character | frozen Scenario, controller.begin | stable scenario across turns, opening not counted |
| UC-06 Simulated conversation | partner, session manager, conversation | round, empty, duplicate, pending reply and exit tests |
| UC-07 Analyze user response | evaluator, evidence contracts | each learner turn required; exact excerpts validated; live semantic quality not established |
| UC-08 Map behavior to dimensions | evaluator, scoring validation | mapping limited to frozen relevant dimensions; draft mappings only |
| UC-09 Score adaptability | scoring | arithmetic and synthetic expert-anchor gate; cultural scoring unavailable with delivered registry |
| UC-10 Generate feedback/explanation | coach, scorecard | demo and mocked agent journeys; live feedback requires reviewer validation |
| UC-11 Review scorecard | scorecard UI | numeric text/N/A/insufficient evidence, evidence ledger, mock/widget tests |
| UC-12 Retry scenario | retry service, scorecard/progress | preserved frozen rules with new attempt ID and parent link |
| UC-13 Track progress | repositories, progress | saved history only; demo/live separation; trends grouped by frozen scenario + level; no trend from one attempt |
| UC-14 Higher experience level | config/progression | deterministic draft recommendation; no unlock barrier; cultural progression cannot activate without scores |
| UC-15 Reasonable alternatives | evaluator guardrails, null demo assessment | two contrasting strategies receive no forced phrase score; actual model fairness unverified |
| UC-16 AI/knowledge uncertainty | registry, approval gate, uncertainty | missing country values and unapproved criteria tests |
| UC-17 Consistency review | personal export, REVIEW.md | export validation and reviewer checklist; no completed expert validation study |
| UC-18 Privacy/session integrity | repositories, narrow tools, diagnostics | session separation, real Auth identity contract mocks, export recalculation, deletion/failure tests; actual cloud RLS requires two-account verification |

## Wireframe screens and states

| Screen | Module | Verification |
|---|---|---|
| 01 Dashboard | `ui/dashboard.py` | empty/actual-history widgets, mode separation |
| 02 Training Setup | `ui/setup.py` | required inputs, mode/key error, contrasting template widget tests |
| 03 Scenario Brief | `ui/scenario.py` | generated state, Begin Conversation, editable setup |
| 04 AI Conversation | `ui/conversation.py` | accepted-round progress, labels, empty/error/exit journeys |
| Analysis state | controller stage notifications, evaluating branch | actual-stage messages; retries preserve transcript; no invented percentage |
| 05 Scorecard & Feedback | `ui/scorecard.py` | completed widget journey, null/N/A states, exact evidence ledger |
| 06 Progress | `ui/progress.py` | saved attempt/retry UI; insufficient-history message |
| 07 Learn | `ui/learn.py` | actual lesson content, completion and practice controls |
| 08 Settings & Privacy | `ui/settings.py` | consent, export, delete, missing storage setup; Auth mocked |
| Loading/disabled | stage info, pending/evaluating composer exclusion | widget and state tests; single-request Streamlit execution, no mid-request cancel |
| Mobile/keyboard/reduced motion | responsive CSS, Streamlit sidebar and widgets | implemented; real browser visual/accessibility audit remains unverified |

## Optional research extension

The later request for CultureBank-style semantic retrieval/NLI estimates is implemented in `culturebank_adapter.py`, `norm_analyzer.py` and `ui/norm_analysis.py`, connected to Settings and Scorecard. `tests/test_norms.py` verifies import/retrieval/classification contracts with injected models. FR-09/FR-10 and UC-07/UC-08 gain an exploratory evidence panel; FR-11/FR-12 and UC-09 keep the reviewed-rubric gate. This research layer does not resolve the absence of expert cultural criteria.
