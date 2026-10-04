# Deploy using only your browser

## 1. Unzip and identify the app files

Download and extract the ZIP. Open the `cross_cultural_app` folder. Its contents include `app.py`, `requirements.txt`, `constraints.txt`, `agents`, `ui`, `data`, `tests`, and documentation. Upload these contents, rather than the outer folder or the ZIP itself.

Enable “show hidden files” in your file browser. The project includes `.streamlit/config.toml` and `.gitignore`; a missing `.streamlit` folder loses theme and analytics settings. It is safe to upload `secrets.example.toml`, which contains placeholders only. Never upload an actual `secrets.toml` or API key.

## 2. Create a GitHub repository and upload

1. Sign in at https://github.com and create a new repository. A private repository is appropriate if you want to control source access.
2. Choose **Add file → Upload files**. Drag the extracted app folder’s **contents** onto the upload page. Commit the upload.
3. Verify that `app.py` and `requirements.txt` appear at the repository root and that `agents`, `ui`, `data` and `tests` are present.
4. If your upload omitted hidden files, use **Add file → Create new file**. Name it `.streamlit/config.toml` and paste the supplied file’s contents. Do the same for `.gitignore`. GitHub creates the folder from the slash in the filename.
5. Confirm there are no credentials in the repository. Do not paste keys into source code or the example file.

## 3. Connect Streamlit Community Cloud

1. Open https://share.streamlit.io and sign in with GitHub.
2. Create a new app and select the repository and branch.
3. Set the main file path to **`app.py`**. If you intentionally uploaded the enclosing folder, use `cross_cultural_app/app.py`; root upload is simpler and makes dependency discovery predictable.
4. Open **Advanced settings**, choose **Python 3.12**, and leave Secrets empty for the demo. The shipped stack was tested under Python 3.12.
5. Save and deploy. Cloud installs `requirements.txt`, which reads `constraints.txt`. Wait for the app to open. Python version changes may require deleting and redeploying the app; keep your settings before doing so.

## 4. First credential-free test

1. Click **Start Training**. Use Pakistan → Japan, Workplace, project meeting, Junior employee → Senior manager, Raise a concern, Intermediate.
2. Keep **Scripted demo** selected. Generate and review the scenario, then begin.
3. Submit eight distinct non-empty responses. The opening is not a round. The eighth response closes practice and shows feedback without an extra question.
4. Expect **“Not enough evidence to score”**, with candidate dimensions marked insufficient evidence and other dimensions N/A. This is intentional: no approved cultural scoring dataset was supplied.
5. Try the same scenario again and check the new attempt ID. Open the targeted lessons.
6. For session progress, enable history in Settings before another attempt. Include transcripts if you want detailed later review. Demo practice is shown separately from live performance.
7. Export your personal attempt JSON. Session-only results can disappear on restart or loss of the browser session.

## 5. Activate live Groq mode

Get a key from https://console.groq.com. In the app’s Community Cloud settings, open **Secrets** and enter:

```toml
GROQ_API_KEY = "YOUR_ACTUAL_KEY"
GROQ_MODEL = "openai/gpt-oss-120b"
```

The app fixes its live model to `openai/gpt-oss-120b`; a stale model override in Secrets does not change this. Save, restart if requested, and select **Live Groq AI** in setup. Your key stays on the server. Do not enter it as a learner response. First perform a Beginner three-response attempt and check generation, reply and evaluation. Live calls were not verified in the delivered environment. Model visibility, quota, payload compatibility and response quality must be confirmed with your account. There is no silent fallback to scripted content.

## 6. Optional persistent history

This is an operator step and requires a Supabase project:

1. At https://supabase.com create a project. In its SQL editor run `data/supabase.sql` once. Inspect the enabled row-level-security policies.
2. Configure Auth and provision confirmed email/password accounts through the project’s supported Auth flow. Self-service sign-up and password recovery are not implemented in this app.
3. Add `SUPABASE_URL` and the project’s public anon/publishable key as `SUPABASE_ANON_KEY` in Streamlit Secrets. **Never use a service-role key.**
4. Sign in from Settings. Login clears prior session data to prevent records from crossing account identities. Export any session-only work first.
5. Enable history and choose whether to save full transcripts or metadata only. Complete a live attempt, then check for a confirmed account write. If saving fails, results stay in session; export or retry saving.
6. Reconnect and load history from Progress. Only the latest 100 records are loaded per request in this MVP; pagination is a documented extension.
7. Test with two actual accounts: each should see only their own rows. Verify deletion removes those rows. Offline mocks do not prove a project’s RLS configuration.

## Troubleshooting

| Symptom | Action |
|---|---|
| `app.py` missing | Check repository root and Streamlit main file path |
| Missing module / install error | Check `requirements.txt` AND `constraints.txt` were uploaded and select Python 3.12. Use build logs; do not remove pins blindly |
| Missing `.streamlit` | Create `.streamlit/config.toml` through GitHub’s file editor |
| Live mode reports missing key | Put the key in Community Cloud Secrets, save, then restart |
| Authentication/model error | Check key permissions and access to `openai/gpt-oss-120b` |
| Quota/rate limit | The app retries HTTP 429 up to three times with exponential backoff and jitter, respecting Retry-After within wait limits. After exhaustion, try configured second Groq key and then Gemini. If all fail, retry the pending stage when quota is available |
| Partner reply fails | Use **Retry partner reply**; do not submit another learner response. The accepted turn is preserved |
| Evidence/feedback fails | Use **Retry evaluation and feedback**. The transcript is unchanged and invalid outputs are rejected |
| Progress is empty | History is opt-in; enable it before an attempt. Session history disappears on restart |
| No practice estimate | Demo remains unscored. Use a new live attempt and check evidence/cue coverage; older attempts have no practice rubric. Reviewed cultural scores remain inactive |
| Supabase login/write fails | Verify confirmed account, Secrets, migration, RLS and public key. Export the session result |
| Mobile sidebar is hidden | Use Streamlit’s sidebar toggle to open compact navigation |

Official references checked during implementation:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python
- https://console.groq.com/docs/models
- https://console.groq.com/docs/model/openai/gpt-oss-120b
- https://docs.crewai.com/en/learn/custom-llm
- https://docs.crewai.com/en/concepts/tools
- https://supabase.com/docs/reference/python/auth-signinwithpassword
- https://supabase.com/docs/reference/python/auth-getuser
- https://supabase.com/docs/reference/python/upsert
- https://supabase.com/docs/guides/database/postgres/row-level-security

## Optional embedding / zero-shot norm analysis

Follow [NORMS.md](NORMS.md) to enable the separate CPU dependency profile, load a sourced CultureBank-style subset in Settings, and run the experimental panel from a completed scorecard. This feature is optional and does not change rubric scoring or progression.

## Updated UI

Upload `ui/visuals.py`, `styles.css`, `UI.md`, and the updated requirements / constraints along with the rest of the source. The requirements already include the community UI libraries. Persona animation can be disabled in Settings and respects device reduced-motion settings. Current unreviewed criteria intentionally leave performance charts empty; saved activity and experimental norm-analysis charts are available separately.

## Cloud architecture and feedback ratings

Learners use the hosted URL; they do not install Python or run a local web app. Streamlit executes application code, session state and optional CPU norm models on the cloud server. Groq handles live generation remotely. Supabase is the optional durable history service. A cloud-hosted app can still have session-only history: hosting does not automatically make session memory persistent.

All 14 countries appear in both culture selectors and Settings. After completing an attempt, choose one to five stars under **Rate this feedback**. Ratings measure feedback usefulness, not cultural performance. Enable history to retain ratings with saved attempts; authenticated live history persists them to Supabase. Existing JSONB metadata/payload columns support the rating without a SQL schema migration. Exported attempt JSON also includes ratings. Deleting history clears ratings and widget state. Retries start unrated.

## Apply the partner-role correction

Replace the repository source with the updated ZIP contents, including `partner_contract.py`, `schemas.py`, `tools.py`, `llm_client.py`, `orchestrator.py`, `demo_provider.py` and both agent prompt files. Redeploy/reboot through Streamlit Community Cloud. There are no new dependencies or database migrations. Start a **new conversation** after updating; existing transcripts retain earlier responses and can carry role confusion forward.

In a live Beginner workplace attempt, confirm the assistant replies as the senior manager while the learner is the junior employee. Try requesting a role switch and confirm the partner keeps its assigned role. Repeat with Student/Fellow student. If a reply fails validation, use Retry partner reply; the learner turn remains accepted. Current automated tests mock Groq and do not replace these hosted checks.

## Apply the HTTP 429 retry update

Upload the updated source, including `http_retry.py`, `llm_client.py` and `diagnostics.py`, then redeploy/reboot the cloud app. No new dependencies or Secrets are required. Automatic retries are limited to three per provider completion request, with 1/2/4-second exponential delays plus jitter. Retry-After is honored without shortening the server delay. A server delay above 30 seconds or cumulative sleep above 60 seconds ends automatic recovery so the user can retry later. Existing request/output budgets remain enforced on every HTTP attempt. Call timeouts remain 45 seconds per HTTP attempt; the sleep budget is not a total wall-clock deadline.

## Activate the two practice scorecards

Follow [SCORING.md](SCORING.md). Upload the full updated source, including `practice_scoring.py`, `ui/practice_results.py` and `data/hofstede_reference.json`, then redeploy/reboot. No new dependencies or SQL migration are needed. Start a new live attempt to freeze its communication rubric and country-informed/contrasting persona. Both scorecards use AI-estimated evidence-based ratings and Python arithmetic. Partial coverage is expected; the source has four missing country-specific dimensions for Egypt, Saudi Arabia and South Africa. Read the source-use terms in SCORING.md for commercial deployment.

## Configure ordered rate-limit fallback

Redeploy the complete updated source and both requirements/constraints files. Set these in your cloud host's Secrets (never in the repository):

```toml
GROQ_API_KEY = "YOUR_PRIMARY_GROQ_KEY"
GROQ_API_KEY_2 = "YOUR_SECOND_GROQ_KEY"
GEMINI_API_KEY = "YOUR_GOOGLE_AI_STUDIO_KEY"
GEMINI_MODEL = "gemini-3.8-flash"
```

The primary Groq model remains `openai/gpt-oss-120b`. All fallback settings are optional. An exhausted HTTP 429 switches primary Groq → second Groq → Gemini, skipping absent/duplicate keys. HTTP 413 skips the second Groq key and tries configured Gemini directly. Other failures do not trigger provider switching. Gemini uses the pinned OpenAI SDK via Google's documented compatibility endpoint. Set GEMINI_MODEL to a supported text/tool model available to your Google account if the default is unavailable. Reboot after saving Secrets, then start a fresh browser session so cached server settings reload.

Two Groq keys in the same organization share the organization quota; key rotation does not add capacity. See https://console.groq.com/docs/rate-limits and https://console.groq.com/docs/projects. Google configuration and model availability: https://ai.google.dev/gemini-api/docs/openai and https://ai.google.dev/gemini-api/docs/models. Fallback stage context and transcripts are sent to Google; Settings discloses this.

If provider recovery still fails, search the deployment logs for the displayed eight-character reference. The `provider_failure` log contains safe exception/cause classes, provider label and HTTP status. Connection errors point to cloud networking (DNS, TLS, proxy or outbound access); server errors identify the returned 5xx status; authentication errors name the relevant Secrets key. No raw exception body or transcript is retained by these logs. A previous error reference from an older deployment has no matching safe diagnostic log.

At most four HTTP attempts are made per provider, with existing shared attempt/output budgets. Three configured providers can require up to twelve requests, each with a 45-second timeout plus bounded sleeps; this is not an overall request deadline. If all fail, use **Retry evaluation and feedback** or **Retry partner reply** in the current session. Restarting the cloud app can discard session-only work. Real provider smoke tests remain necessary.

## Apply the HTTP 413 correction

Redeploy the complete new package. The evaluator sends one compact snapshot and keeps all transcript text, rubric anchors and evidence-validation rules. If Groq still rejects the request with 413, configure GEMINI_API_KEY and an available GEMINI_MODEL; the app tries Gemini directly. Raising organization/request capacity is another option. A second Groq key alone does not make the same oversized request smaller. No secrets were supplied for a live verification.

The `use_container_width` notice is separate from HTTP 413. Button and dataframe calls now use `width='stretch'`, which the pinned Streamlit 1.49.1 runtime supports. Chart calls retain that runtime's supported API; do not change chart signatures or upgrade runtime pins without a separate compatibility check.

## Apply the feedback request correction

Redeploy the complete updated package, particularly llm_client.py, agents/feedback_synthesizer.py and diagnostics.py. No new Secrets, dependencies, UI changes or database migration are required. Feedback receives one server-retrieved snapshot and returns the validated feedback object without tool calls. After a failure, Retry evaluation and feedback reuses the accepted evaluation in the current session. A cloud reboot can discard session-only attempts; retain any available exports before redeployment.

New failure log entries include `provider_status` (an allowlisted Google status when available) and `reason` (a safe category such as tool_schema, tool_context, thought_signature, output_schema, token_parameter, model_parameter or unknown). These hints classify keywords in the provider response; they are not conclusive diagnoses. Share that sanitized line if a Gemini 400 persists. Never paste raw provider responses or repaired transcript bundles into public logs/issues. The older reference contains only the earlier metadata fields. No live Gemini request was verified here.
