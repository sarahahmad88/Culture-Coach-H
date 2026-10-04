# Modern interface

The dashboard uses **Streamlit Shadcn UI** summary cards. **Streamlit Extras** styles native feedback metrics and adds spacing. **Altair** shows saved practice activity and per-norm experimental label scores; **Plotly** shows scored dimensions and comparable performance trends with hover details and image export.

## Personas

The dashboard, scenario brief, conversation and feedback show SVG role personas served by the hosted app. They wave when ready, nod while listening, pulse their status while a reply is pending, and remain still during reflection. These are state indicators, not emotional inference or cultural representations. No external avatar or animation service receives user data.

Turn off **Animate practice personas** in Settings to stop motion. The device's reduced-motion preference also stops animation. Labels remain visible with animation disabled.

## Chart interpretation

- Activity counts include saved attempts and distinguish scripted demo from live practice. Enable history in Settings to retain completed activity in the current session.
- Dimension bars require numerical scored live evidence. Missing values never become zero. The current unreviewed registry therefore displays an honest empty state.
- Performance trends require at least two completed, scored live attempts with the same frozen scenario and difficulty. They follow chronological order, use a fixed 0–100 scale, and respect mode, scenario and level filters.
- Norm-analysis charts show each retrieved norm and learner turn separately. Relative classifier label scores are experimental and do not change official performance or progression.
- Numerical dimension and trend data remain available in tables for inspection. The demo produces no fabricated performance graph.

## Install and deployment

The included requirements install the UI automatically. Both base and optional local-model profiles include:

```
streamlit-shadcn-ui==0.1.19
streamlit-extras==0.5.5
plotly==6.3.0
altair==5.5.0
```

These releases match the existing Streamlit 1.49.1 API. The newer Shadcn V2 API requires a separate runtime migration. Streamlit Extras 0.7.8 conflicted with existing dependency constraints; 0.5.5 installed successfully and passed dependency checks. Keep both requirements and constraints files when deploying; consult DEPLOY.md and NORMS.md.

## Validation limits

83 tests pass, including the full Streamlit widget journeys and checks for chart evidence gates, chronological plotting, demo filtering, empty states, and safe persona text. Dependencies pass `pip check`; Streamlit health responds successfully. Browser rendering of Shadcn components, animation playback, responsive layout and keyboard accessibility remain unverified because Chromium is unavailable. AppTest verifies Python/widget flows and chart generation, not browser pixels. Live service validation and expert cultural review remain separate activation steps.

## Feedback rating and cloud use

The completed-feedback screen includes a native Streamlit five-star usefulness widget. Ratings follow history consent, are included in exports and saved metadata, and are independent of cultural scores. The app runs on a cloud server and users interact through a browser. Optional inference runs on that server rather than the user’s device. All 14 countries are selectable in setup and preferences.

## Two practice scorecards

New live feedback displays separate communication and experimental Hofstede-informed adaptation metrics and Plotly bars, with criterion explanations, coverage and transcript/cue evidence. Country reference values appear in a separate table. Progress charts compare only matching frozen scenarios, personas, difficulties and rubric versions. See SCORING.md for the reference dataset, partial country coverage, contrasting profiles and calculation details. Demo illustrates the panels without personal ratings.

## Neon score theme

Score displays use white panels, readable dark text, and bright neon borders and bars. All five communication criteria and six Hofstede dimensions have unique stable colors defined in `ui/score_theme.py`. Communication panels use electric cyan accents and adaptation panels use neon magenta accents; totals and labels use dark ink on white. Dashboard score summaries, feedback cards, criterion bars, rating labels and comparable trend lines use the same palette. Country-reference legends retain dimension colors while reference numbers remain distinct from learner scores. Experimental norm labels use lime (adherence), coral (violation) and yellow (unclear).

Labels, values, coverage and missing-evidence statuses remain explicit, so color is never the sole indicator. CSS includes mobile layout and forced-color support; there is no new flashing or pulsing score animation. No dependencies, scoring rules, APIs or database changes are required. Redeploy the updated cloud source to apply the styling.

## Reference-inspired dashboard and navigation

The supplied layouts inspired a prominent editorial hero, a playful local globe illustration, and three action tiles for the learning loop. The app now uses a warm off-white foundation with lime, electric cyan, magenta, and violet accents, rounded panels, generous spacing, and a compact wordmark. Sidebar navigation pairs each existing label with a distinct SVG icon: dashboard grid, training conversation, progress chart, learning book, and settings sliders. Selection has an accent border and a matching background; native navigation controls and text labels remain available.

The hero speech bubbles gently float when animations are enabled. Settings and the device's reduced-motion preference stop motion. The artwork and navigation icons are local vector assets. Mobile rules stack the hero artwork and wrap cards. Existing category and dimension colors remain stable throughout score displays. The explicit Streamlit light theme covers native inputs, tables, dialogs, and charts. Shadcn summary cards share the white surface.

Navigation icon styling targets the pinned Streamlit DOM. Browser verification of icon placement, responsive sizing, animation playback, contrast, and focus behavior remains pending. No scoring rules, API calls, countries, database structure, or dependencies changed.

## Light-only presentation update

The app defaults explicitly to light mode. The sidebar uses a pale lavender/mint gradient; the hero and cards use white and pastel surfaces; plots use white backgrounds, dark labels, and subtle gray gridlines. Neon colors remain on accents, artwork, scoring bars, borders, and badges. Icon ink and small text use deeper colors for readability on white. Primary action buttons retain lime with dark text. The standalone globe has a white interior. No dark score panels or dark chart backgrounds remain. This update changes presentation only; core workflows, API routing, scoring, retry behavior and data storage are unchanged.
