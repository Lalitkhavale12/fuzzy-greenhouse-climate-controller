---
phase: 08-theme-export-foundation
plan: "08"
type: execute
wave: 1
depends_on: []
files_modified:
  - .streamlit/config.toml
  - dashboard/helpers.py
  - dashboard/pages/01_model_sim.py
  - dashboard/pages/02_controllers.py
  - dashboard/pages/03_ga_explorer.py
  - dashboard/pages/04_results.py
  - tests/test_dashboard.py
autonomous: true
requirements:
  - UI-01
  - UI-02

estimate:
  tokens: 60000
  raw_tokens: 30000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - Dashboard boots with light greenhouse chrome (green primary, pale backgrounds, soil-ink text) and every chart stays readable in light mode
    - Scoreboard CSV download bytes are byte-identical to results/comparison.csv
    - Verdict TXT names ga_fuzzy rank 1 with margins, per-term iae_T/iae_H/energy/cost for all four holdout controllers, seeds 7/21, weights 1.0/1.0/0.01
    - Every chart PNG download opens as a valid PNG starting with 89 50 4E 47 magic
    - python tests/test_dashboard.py is all-PASS and results/ + weather/ show zero tracked modifications
  artifacts:
    - .streamlit/config.toml
    - dashboard/helpers.py
    - dashboard/pages/01_model_sim.py
    - dashboard/pages/02_controllers.py
    - dashboard/pages/03_ga_explorer.py
    - dashboard/pages/04_results.py
    - tests/test_dashboard.py
  key_links:
    - helpers.py byte builders to page download_button wiring (bytes plus explicit MIME plus stable filename)
    - results/comparison.csv frozen bytes to scoreboard_csv_bytes passthrough (header asserted equal to COLUMNS)
    - notebook 05 verdict cell logic to verdict_text content (reads CSV, never recomputes)
  assumptions:
    - ASSUMPTION (UI-01 edge, specless probe unclassified): exact readable-contrast threshold for charts under the light theme is eyeballed, not metered; accepted as human screenshot check per 08-VALIDATION.md manual-only row
    - ASSUMPTION (UI-02 edge, specless probe unclassified): download-button click behavior (filenames landing on disk) is browser-side and covered by manual click-through of all 7 buttons, not headless asserts; accepted per 08-VALIDATION.md manual-only row
  prohibitions:
    - never write to results/ or weather/ from dashboard code
    - never add dependencies
    - never restyle matplotlib via theme sidecar
---

<objective>
Deliver Phase 8: greenhouse identity plus export-center plumbing. One light-greenhouse theme sidecar plus one shared byte-builder module (scoreboard CSV, verdict TXT, chart PNG) wired as download buttons on the page where each piece of content lives. Per D-01 through D-04.

Purpose: Theme goes first so every later v1.1 screenshot shows final identity, and the byte builders are the shared primitive Phase 9 (scenario CSVs) and Phase 10 (ZIP bundle) compose.
Output: .streamlit/config.toml, dashboard/helpers.py, thin download-button wiring on all four pages, extended headless suite, all-PASS with frozen artifacts untouched.
</objective>

<execution_context>
@C:/Users/Lalit/.config/opencode/gsd-core/workflows/execute-plan.md
@C:/Users/Lalit/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/08-theme-export-foundation/08-CONTEXT.md
@.planning/phases/08-theme-export-foundation/08-RESEARCH.md
@.planning/phases/08-theme-export-foundation/08-PATTERNS.md
@.planning/research/SUMMARY.md
@dashboard/pages/04_results.py
@tests/test_dashboard.py
</context>

<tasks>

<task type="tracer">
  <name>Tracer: theme sidecar plus export slice end-to-end on Results</name>
  <files>.streamlit/config.toml, dashboard/helpers.py, dashboard/pages/04_results.py, tests/test_dashboard.py</files>
  <read_first>
    - .streamlit/config.toml: does not exist yet (greenfield sidecar); source of truth is 08-RESEARCH.md Code Examples greenhouse theme table and 08-PATTERNS.md starter palette
    - dashboard/helpers.py: does not exist yet; source of truth is 08-PATTERNS.md helpers.py section (imports shape, frozen-byte passthrough, ranking copy, verdict mirror, PNG canonical order) plus dashboard/pages/04_results.py lines 30-47 (load_scoreboard and holdout_ranking to reuse, not duplicate)
    - dashboard/pages/04_results.py: the file being wired; source of truth is its own lines 24-27 constants, 62-74 verdict block, 79-104 scoreboard figure
    - tests/test_dashboard.py: the file being stub-extended; source of truth is its lines 26-73 _stub_streamlit shape and lines 174-209 source audits
  </read_first>
  <action>Per D-01 create .streamlit/config.toml with a [theme] table: base light, primaryColor leaf green #2E7D32, backgroundColor pale greenhouse white #F7FAF3, secondaryBackgroundColor misted-glass #E8F0E1, textColor soil-ink #263023, font sans serif; leave theme.sidebar unset and build no dark variant per D-01. Per D-02 and D-04 create dashboard/helpers.py as the ONLY new-code home with exactly three public builders: scoreboard_csv_bytes reading results/comparison.csv in binary mode and asserting the header equals COLUMNS from src.metrics before returning raw bytes; verdict_text taking the already-loaded rows, ranking via the CSV rank column with a stable sort identical to holdout_ranking, formatting winner plus GA-vs-onoff and GA-vs-PID margins plus per-term iae_T, iae_H, energy, cost for all four holdout controllers plus provenance train_seed 7, holdout_seed 21, weights 1.0/1.0/0.01, mirroring notebooks/05_comparison.ipynb cell 5 relative-ordering logic with percent-point-2f cost formatting and never importing compare, evolve, or genetic_algorithm; fig_to_png_bytes taking an in-hand figure and serializing via savefig to BytesIO as PNG at dpi 150 followed by seek(0) and getvalue, never closing the figure so the caller can still st.pyplot it afterwards. Add a build_results_figure helper that rebuilds the scoreboard figure from passed-in rows with explicit light-figure face and ink colors, grid alpha 0.3, and default C-series line colors, keeping the log-scale cost panel and settling annotation semantics of 04_results.py. Use the dashboard/app.py two-dirname sys.path bootstrap depth since helpers.py sits at dashboard level, not the three-dirname pages depth. On 04_results.py add thin wiring only and no new defs beyond the existing load_scoreboard and holdout_ranking: a scoreboard CSV download button with file_name comparison.csv and mime text/csv, a verdict TXT download button fed by verdict_text(rows) with file_name holdout_verdict.txt and mime text/plain, and one chart PNG button fed by fig_to_png_bytes of the page figure with file_name results_scoreboard.png and mime image/png, calling the serializer BEFORE st.pyplot per the canonical order. In tests/test_dashboard.py extend _stub_streamlit with a download_button entry returning None in the SAME task as the first page use, copying the adjacent selectbox entry style. Keep every figure-audit token (savefig, plt.show, Agg, absolute paths, w-opens) out of all pages; all savefig lives in helpers. Using python, the conda 3.14.6 interpreter, never python3 and never any pip or conda install.</action>
  <acceptance_criteria>config.toml parses as TOML with all six theme keys and base light; scoreboard_csv_bytes output equals open of results/comparison.csv in binary mode byte for byte; verdict_text contains ga_fuzzy, all four controller ids, iae_T, iae_H, energy, train_seed 7 markers, holdout_seed 21 markers, and 1.0/1.0/0.01; fig_to_png_bytes output starts with 89 50 4E 47 magic; 04_results.py contains three download_button calls with the exact filenames and MIME values above; python tests/test_dashboard.py prints all-PASS.</acceptance_criteria>
  <verify>
    <automated>python tests/test_dashboard.py</automated>
    <fails_when>any line starts with FAIL, or the run exits nonzero, or the final line is not all checks passed</fails_when>
  </verify>
  <done>The single happy path works end to end: themed app boots, Results page serves byte-identical CSV, notebook-mirroring verdict TXT, and magic-valid PNG, and the suite is green.</done>
  <reversibility rating="reversible">Theme sidecar and new helpers module touch no frozen artifacts; deletable without trace.</reversibility>
</task>

<task type="auto">
  <name>Expansion: chart PNG buttons on Model Sim, Controllers, GA Explorer</name>
  <files>dashboard/helpers.py, dashboard/pages/01_model_sim.py, dashboard/pages/02_controllers.py, dashboard/pages/03_ga_explorer.py</files>
  <read_first>
    - dashboard/pages/01_model_sim.py: the file being wired; source of truth is its lines 69-85 figure block plus 08-PATTERNS.md 01 section
    - dashboard/pages/02_controllers.py: the file being wired; source of truth is its lines 46-64 cached run_all_four plus 74-99 figure block, which stays untouched
    - dashboard/pages/03_ga_explorer.py: the file being wired; source of truth is its lines 52-63 convergence fig, 69-90 MF before/after fig2, and the hard zero-def audit at tests/test_dashboard.py lines 198-201
    - dashboard/helpers.py: the file being extended; source of truth is the fig_to_png_bytes serializer from the tracer task plus 08-RESEARCH.md Pitfall 5 no-recompute rule
  </read_first>
  <action>Per D-03 add one chart PNG download button to each chart page, thin wiring only with zero new defs on any page and strictly zero new defs or class statements on 03_ga_explorer.py: on 01_model_sim.py a button with file_name model_sim_chart.png and mime image/png fed by fig_to_png_bytes of the page 3-panel figure; on 02_controllers.py a button with file_name controllers_traces.png and mime image/png fed by fig_to_png_bytes of the page traces figure, taking the already-available hours and runs outputs and never calling compare; on 03_ga_explorer.py two buttons with file_names ga_convergence.png and ga_mfs.png and mime image/png fed by fig_to_png_bytes of fig and fig2 respectively, parameterized by nothing new since the selectbox value stays on the page. In every case call the serializer BEFORE the corresponding st.pyplot call. Add explicit light-figure face and ink colors at figure construction where the existing page code relies on matplotlib defaults, keeping default C-series data colors and grid alpha 0.3 per the existing page idiom. Never import compare, evolve, genetic_algorithm, generate_weather_profile-for-writes, or any path string as download data on any page; data carries bytes only. Using python, the conda 3.14.6 interpreter, never python3 and never any install.</action>
  <acceptance_criteria>01, 02, 03 pages contain 1, 1, 2 download_button calls with the exact filenames above and mime image/png; 03_ga_explorer.py has zero top-level def or class lines; no page contains savefig, plt.show, use of Agg, absolute-path literals, or w-mode opens; python tests/test_dashboard.py prints all-PASS.</acceptance_criteria>
  <verify>
    <automated>python tests/test_dashboard.py</automated>
    <fails_when>any line starts with FAIL, or the run exits nonzero, or test_source_audits names an offending page and token</fails_when>
  </verify>
  <done>A real user can download a valid PNG from every chart on every page, and the headless source audits still hold.</done>
  <reversibility rating="reversible">Page wiring is additive download buttons plus serializer calls; removable per page without touching science.</reversibility>
</task>

<task type="auto">
  <name>Export assertions plus phase gate</name>
  <files>tests/test_dashboard.py</files>
  <read_first>
    - tests/test_dashboard.py: the file being extended; source of truth is its lines 116-129 test_results_helper, 174-209 test_source_audits, 212-217 test_artifacts_untouched, plus 08-RESEARCH.md Validation Architecture pass criteria
    - dashboard/helpers.py: the module under assertion; source of truth is its three builders from the tracer task
    - src/metrics.py lines 30-44: locked weights W1 W2 W3 1.0 1.0 0.01, 14-column COLUMNS, and train-seed7 versus holdout-seed21 weather pairs
  </read_first>
  <action>Add headless export assertions to tests/test_dashboard.py as new test functions following the existing plain-assert standalone style with prints and sys.exit(1) on failure, importing helpers through the same repo-root bootstrap the suite already uses: assert scoreboard_csv_bytes equals the binary read of results/comparison.csv with header equal to COLUMNS; assert fig_to_png_bytes of a rebuilt results figure starts with 89 50 4E 47 magic and is larger than 1 KB; assert verdict_text of load_scoreboard rows contains ga_fuzzy, holdout, iae_T, iae_H, energy, seed 7 and 21 markers, and 1.0/1.0/0.01; assert the page sources contain the seven expected filenames comparison.csv, holdout_verdict.txt, model_sim_chart.png, controllers_traces.png, ga_convergence.png, ga_mfs.png, results_scoreboard.png with MIME values text/csv, text/plain, image/png respectively. Then run the full phase gate: python tests/test_dashboard.py green plus git status --porcelain over results/ and weather/ showing only untracked question-mark lines and zero tracked modifications. Using python, the conda 3.14.6 interpreter, never python3.</action>
  <acceptance_criteria>New export test functions pass headlessly with no browser; full suite prints all checks passed; git status porcelain over results/ and weather/ shows zero tracked modifications; total download buttons across pages equal 7 (3 on Results, 1 plus 1 plus 2 on the chart pages).</acceptance_criteria>
  <verify>
    <automated>python tests/test_dashboard.py</automated>
    <fails_when>any line starts with FAIL, or the run exits nonzero, or the export test functions are absent from the file</fails_when>
  </verify>
  <verify>
    <automated>git status --porcelain results/ weather/</automated>
    <fails_when>any output line does not start with ??, meaning a tracked artifact was modified</fails_when>
  </verify>
  <done>Phase gate holds: exports proven byte-correct headlessly, suite green, frozen artifacts untouched.</done>
  <reversibility rating="reversible">Test-only additions; suite extensions never touch frozen artifacts.</reversibility>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| frozen CSV/JSON to helpers.py | Untrusted-by-convention file bytes cross into download payloads; provenance asserts gate them |
| helpers.py bytes to browser | Generated CSV/TXT/PNG bytes served via st.download_button to the examiner browser |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-08-01 | Tampering | dashboard/helpers.py scoreboard_csv_bytes | medium | mitigate | Read only two hardcoded frozen paths (results/comparison.csv, results/ga_optimized_params.json); data carries bytes never a user path; file_name values are hardcoded literals never interpolated from widget input; header asserted equal to COLUMNS fail-closed |
| T-08-02 | Spoofing | page download_button wiring (7 buttons) | low | mitigate | Explicit mime on every button: text/csv for comparison.csv, text/plain for holdout_verdict.txt, image/png for all five chart PNGs; never omit mime |
| T-08-03 | Tampering | frozen provenance (results/, weather/) | medium | mitigate | In-memory BytesIO only; source audit bans w-mode opens in pages; merge gate git status --porcelain results/ weather/ must show zero tracked modifications |
| T-08-SC | Tampering | installs (npm/pip/cargo) | high | mitigate | Zero new installs enforced; planner rejects any pip or conda install step; no new attack surface by construction |

Note: V2/V3/V4/V6 ASVS categories do not apply (local academic dashboard, no users, sessions, access control, or crypto); V5 input validation applies via T-08-01 hardcoded-path control above.
</threat_model>

<verification>
Theme is invisible to the headless suite, so verification is two-tier: automated headless asserts (CSV byte-identity, PNG 89 50 4E 47 magic, verdict substrings ga_fuzzy plus seeds 7/21 plus weights 1.0/1.0/0.01, full suite all-PASS, tracked-clean gate) run after every task commit per 08-VALIDATION.md sampling rate; manual screenshot eyeball of python -m streamlit run dashboard/app.py for greenhouse chrome plus chart contrast and click-through of all 7 download buttons happens once at end of phase before verify-work. Proven commands reused verbatim: python tests/test_dashboard.py and git status --porcelain results/ weather/.
</verification>

<success_criteria>
Phase 8 succeeds when all four ROADMAP success criteria hold: dashboard loads with greenhouse theme and readable light-mode charts; scoreboard CSV downloads from Results byte-identical to the frozen artifact; verdict TXT downloads naming the winner, margins, per-term breakdown, seeds, and weights; every comparison chart downloads as a valid PNG from its own page; plus the standing gates of suite green and frozen artifacts untouched.
</success_criteria>

<output>
Create no new summary path beyond the phase directory; execution writes .planning/phases/08-theme-export-foundation/08-SUMMARY.md when done
</output>

## Artifacts this phase produces

| File | Change | Contents |
|------|--------|----------|
| .streamlit/config.toml | NEW | Light-greenhouse [theme] sidecar per D-01 (base light, #2E7D32 primary, #F7FAF3 background, #E8F0E1 secondary, #263023 text, sans serif) |
| dashboard/helpers.py | NEW | ALL new defs: scoreboard_csv_bytes, verdict_text, fig_to_png_bytes, build_results_figure per D-02/D-04 |
| dashboard/pages/01_model_sim.py | MODIFIED | One PNG download button wiring only (model_sim_chart.png) per D-03 |
| dashboard/pages/02_controllers.py | MODIFIED | One PNG download button wiring only (controllers_traces.png) per D-03 |
| dashboard/pages/03_ga_explorer.py | MODIFIED | Two PNG download buttons wiring only (ga_convergence.png, ga_mfs.png), zero new defs per D-03 |
| dashboard/pages/04_results.py | MODIFIED | CSV plus verdict TXT plus PNG download buttons wiring only per D-03 |
| tests/test_dashboard.py | MODIFIED | download_button stub entry in the same task as first page use plus headless export assertions |

## Source coverage audit

| Source | Item | Covering task |
|--------|------|---------------|
| GOAL | Greenhouse identity on dashboard | Tracer (config.toml) |
| GOAL | Users take results away as files | Tracer (Results CSV/TXT/PNG) plus Expansion (per-page PNGs) |
| REQ UI-01 | Greenhouse theme via config.toml, readable light charts | Tracer plus Expansion explicit figure colors |
| REQ UI-02 | Scoreboard CSV, chart PNG, verdict TXT downloads | Tracer (CSV/TXT/first PNG) plus Expansion (remaining PNGs) plus Export assertions gate |
| RESEARCH | Byte-builder shapes (passthrough, BytesIO seek(0), MIME table) | Tracer helpers plus Export assertions magic-byte checks |
| RESEARCH | Validation Architecture wave-0 gaps (helpers, sidecar, stub, export asserts) | Tracer (helpers, sidecar, stub) plus Export assertions task |
| RESEARCH | Security Domain (hardcoded paths, explicit MIME, BytesIO-only, zero installs) | All tasks; threat_model T-08-01/02/03/SC |
| CONTEXT D-01 | Light theme, no dark mode, explicit matplotlib colors | Tracer sidecar; Expansion figure colors |
| CONTEXT D-02 | CSV plus PNG plus TXT only, frozen CSV bytes, 89 50 4E 47 magic, notebook-mirroring verdict | Tracer builders; no PDF anywhere |
| CONTEXT D-03 | Downloads where content lives (CSV+TXT Results, PNG per page) | Tracer Results wiring plus Expansion chart-page wiring (7 buttons total) |
| CONTEXT D-04 | Verdict winner plus margins plus per-term IAE_T/IAE_H/E plus seeds 7/21 plus weights 1.0/1.0/0.01, reads CSV never recomputes | Tracer verdict_text; Export assertions substrings |
| Deferred | Dark-mode variant, PDF bundle | Excluded from all tasks per CONTEXT.md deferred list |
