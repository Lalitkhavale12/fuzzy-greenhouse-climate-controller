---
phase: 07-streamlit-dashboard
plan: "07"
type: execute
wave: 1
depends_on: []
files_modified:
  - dashboard/app.py
  - dashboard/pages/01_Model_Sim.py
  - dashboard/pages/02_Controllers.py
  - dashboard/pages/03_GA_Explorer.py
  - dashboard/pages/04_Results.py
  - tests/test_dashboard.py
autonomous: true
requirements:
  - PROOF-02
estimate:
  tokens: 60000
  raw_tokens: 30000
  tasks: 3
  confidence: low
must_haves:
  truths:
    - "`python -m streamlit run dashboard/app.py` boots a multipage app with four sidebar pages in numeric order (Model Sim, Controllers, GA Explorer, Results) per D-01"
    - "Model Sim sliders (heater/fan/fogger/vent duties + seed) drive src.greenhouse_model.step open-loop and the 3-panel trace chart updates per D-01"
    - "Controllers page T_sp + RH_sp + seed sliders (seed 1-50, 7/21 resolve to frozen files) rerun all four controllers on shared weather in under 30 s with shared-axes T + shared-axes RH + duty overlay per D-03"
    - "GA Explorer renders convergence (history.best + mean, 50 gens) and MF before/after overlays from results/ga_optimized_params.json ONLY with schema_version == 2 assert, no evolution code per D-02"
    - "Results page renders the 8-row scoreboard plus rank-1 verdict strip from results/comparison.csv ONLY with header == COLUMNS assert, never recomputing per D-04"
    - "Verdict follows CSV rank identity only (no float argsort/comparison) and settling renders as text, never bars"
    - "Cost panels use log scale; `python tests/test_dashboard.py` passes and `git status --porcelain results/ weather/` is clean after helper runs"
    - statement: "Sidebar titles read naturally and charts are visually legible to a reviewer"
      verification: backstop
    - statement: "Flagged assumption (specless-probe unclassified edge PROOF-02/unresolved): thin-wrapper scope boundary — any page logic that belongs in src/ is pushed down or cut; reviewer confirms no scope smell at sign-off"
      verification: backstop
  artifacts:
    - dashboard/app.py
    - dashboard/pages/01_Model_Sim.py
    - dashboard/pages/02_Controllers.py
    - dashboard/pages/03_GA_Explorer.py
    - dashboard/pages/04_Results.py
    - tests/test_dashboard.py
  key_links:
    - "dashboard/pages/*.py -> src/ pure functions (step, run_closed_loop, tri, load_optimized_mfs) via repo-root sys.path + os.chdir bootstrap"
    - "04_Results.py -> results/comparison.csv read-only (header == COLUMNS, 8 rows)"
    - "03_GA_Explorer.py -> results/ga_optimized_params.json read-only (schema_version == 2)"
    - "02_Controllers.py seed slider -> frozen weather files for 7/21, tempfile.mkdtemp paths otherwise"
  prohibitions:
    - never write to results/ or weather/ from dashboard code
    - never run evolution inline in the dashboard
    - never recompute the scoreboard in the Results page
---

<objective>
**As a** project reviewer, **I want to** click through a four-page Streamlit dashboard that drives the finished src/ library with sliders, **so that** I can see the plant respond, compare all four controllers live, inspect the GA artifact, and read the frozen scoreboard verdict without rerunning notebooks.

Purpose: Deliver PROOF-02 as a thin UI wrapper (D-01 through D-04) with zero new control logic, zero new dependencies, and frozen artifacts read-only.
Output: dashboard/app.py + four numbered pages + tests/test_dashboard.py, all green headless.
</objective>

<execution_context>
@C:/Users/Lalit/.config/opencode/gsd-core/workflows/execute-plan.md
@C:/Users/Lalit/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/REQUIREMENTS.md
@.planning/phases/07-streamlit-dashboard/07-CONTEXT.md
@.planning/phases/07-streamlit-dashboard/07-RESEARCH.md
@.planning/phases/07-streamlit-dashboard/07-PATTERNS.md
</context>

<tasks>

<task type="tracer">
  <name>Tracer: app shell + Results page + headless suite scaffold end-to-end</name>
  <files>dashboard/app.py, dashboard/pages/04_Results.py, tests/test_dashboard.py</files>
  <read_first>
    - dashboard/app.py (new — nothing to read; target of this task)
    - .planning/phases/07-streamlit-dashboard/07-PATTERNS.md section 04_Results.py (scoreboard-load + ranking + bar-chart patterns, 05 cell 2/3 verbatim sources)
    - .planning/phases/07-streamlit-dashboard/07-RESEARCH.md Pattern 1 (three-dirname sys.path + os.chdir bootstrap), Validation Architecture (plain-assert harness, PROOF-02a/02b/02d/02f rows), Pitfalls 1/2/4/5/6
    - src/metrics.py lines 32-35 (COLUMNS 14-col contract) and lines 191-196 (compare writes CSV — why pages never call it)
    - results/comparison.csv (8 frozen rows, settling_min inf everywhere)
    - tests/test_notebooks.py lines 222-241 (runner convention) and lines 213-219 (artifact-guard pattern)
  </read_first>
  <acceptance_criteria>
    - dashboard/app.py calls st.set_page_config first, then title + landing markdown only; contains none of the strings run_closed_loop, compare(, savefig, plt.show
    - dashboard/pages/04_Results.py filename keeps the 04_ prefix (sidebar order per streamlit/source_util.py:58 regex); loads results/comparison.csv via csv.DictReader with assert list(rows[0].keys()) == COLUMNS and assert len(rows) == 8
    - Results ranking uses ORDER = onoff/pid/fuzzy/ga_fuzzy with DISPLAY names on/off/PID/hand fuzzy/GA fuzzy, holdout-seed21 filter, sorted by int(rank) only; verdict strip uses st.metric costs + rank-1 identity, no argsort, no float comparison (per D-04)
    - Results charts: grouped bars for iae_T/iae_H/energy/cost with ax.set_yscale(log) on the cost panel; settling_min appears only as text annotation; explicit fig objects passed to st.pyplot(fig); no matplotlib.use(Agg), no plt.show, no savefig
    - tests/test_dashboard.py runs via python tests/test_dashboard.py, iterates test_ callables, prints PASS/FAIL, sys.exit(1) on failure; python tests/test_notebooks.py still passes
    - git status --porcelain results/ weather/ is empty after the suite run
  </acceptance_criteria>
  <action>
    Create dashboard/app.py as landing-only (set_page_config first per RESEARCH Assumption A1, title + one-paragraph four-page guide, repo-root two-dirname sys.path insert + os.chdir to root) per D-01. Create dashboard/pages/04_Results.py with the three-dirname bootstrap, verbatim 05-cell-2 CSV load with COLUMNS + 8-row asserts, ORDER/DISPLAY rank-identity verdict strip with st.dataframe table above the fold and st.metric KPIs, and the 05-cell-3 bar conversion (log cost axis, text settling) per D-04. Create tests/test_dashboard.py in the test_notebooks.py plain-assert style with import smoke that stubs streamlit in sys.modules before importing pages (pages call st.* at import), structural scans (no Agg/show/savefig under dashboard/, no absolute paths /home/ /Users/ C:/, no compare( in 04 page), and the git-status artifact guard over results/ and weather/ per 07-PATTERNS.md test analog. Use python (conda 3.14.6) in every command and docstring, never python3. Zero new installs.
  </action>
  <verify>
    <automated>python tests/test_dashboard.py</automated>
    <fails_when>nonzero exit code, or any line containing FAIL, or missing PASS lines for test_page_set / test_pages_import / test_results_helper / test_artifacts_untouched</fails_when>
    <automated>git status --porcelain results/ weather/</automated>
    <fails_when>any output line appears (clean tree required — dashboard must not write frozen artifacts)</fails_when>
  </verify>
  <done>Multipage app boots headless (import smoke green), Results page restates the frozen scoreboard + verdict from CSV only, suite passes, artifacts untouched.</done>
  <reversibility rating="reversible">UI-only read path; results/comparison.csv stays canonical per D-04</reversibility>
</task>

<task type="auto">
  <name>Expansion: Model Sim + Controllers interactive pages</name>
  <files>dashboard/pages/01_Model_Sim.py, dashboard/pages/02_Controllers.py</files>
  <read_first>
    - dashboard/pages/04_Results.py (tracer output — bootstrap + assert style to mirror)
    - .planning/phases/07-streamlit-dashboard/07-PATTERNS.md sections 01_Model_Sim.py (01 cells 1-3 weather-guard + open-loop + 3-panel chart) and 02_Controllers.py (run_closed_loop signature, cache pattern, tempfile seed pattern, compare( FORBIDDEN)
    - .planning/phases/07-streamlit-dashboard/07-RESEARCH.md Pattern 2 (st.cache_data on whole runs), Pitfalls 2/3/4, per-page compute/chart map rows 01/02
    - notebooks/01_greenhouse_model.ipynb cells 1-3 (schedule loop, 3-panel figure) and notebooks/02_baselines.ipynb cells 2-3 (overlay grid source)
    - src/greenhouse_model.py lines 55-101 (step 4-key actuator asserts + load_weather_profile contract) and src/metrics.py lines 126-152 (run_closed_loop: weather_path required, init T 20.0, w 0.65 times wsat, dt 60, n 1440)
    - src/onoff_controller.py line 15, src/pid_controller.py line 19, src/fuzzy_controller.py line 63, src/ga_fuzzy_controller.py line 80 (shared T_C/rh_pct/T_sp/RH_sp/state signatures)
    - src/weather_profile_generator.py lines 15-27 (generate_weather_profile out_path + seed determinism)
  </read_first>
  <acceptance_criteria>
    - 01_Model_Sim.py sliders: heater/fan/fogger/vent duties 0.0-1.0 step 0.05 plus seed selector; weather resolves seed 7 to weather/weather_profile.csv and other seeds via generate_weather_profile into tempfile.mkdtemp paths only, never into weather/
    - 01 open-loop loop body matches 01 cell 2 shape (hours arange 1440/60, interp outdoor, daytime_solar with params A_sol, step 60.0) with slider duties replacing schedule(h); 3-panel figure copied from 01 cell 3 with savefig/show replaced by st.pyplot(fig)
    - 02_Controllers.py sliders: T_sp 18.0-30.0 step 0.5, RH_sp 50-90 step 1, seed 1-50 step 1 with 7 resolving to weather/weather_profile.csv and 21 to weather/holdout_21.csv, all other seeds to tempfiles; run_all_four helper wrapped in st.cache_data calls metrics.run_closed_loop x4 (onoff/pid/fuzzy/ga_fuzzy) on the shared weather path with n 1440 and a wall-time assert under 30 s (measured 1.37 s)
    - 02 charts use shared-axes T + shared-axes RH + duty panel in the 04 holdout-trace style per D-03; explicit figs only; no number_input/text_input driving the loop; no metrics.compare( import or call anywhere in the file
    - python tests/test_dashboard.py passes including test_controllers_helper asserting 4 histories x 1440 steps, shared weather identity, and GA cost below on/off AND below PID on seed 21
  </acceptance_criteria>
  <action>
    Create 01_Model_Sim.py (three-dirname bootstrap, st.slider duties + cached_weather helper in st.cache_data, verbatim 01-cell loop and 3-panel conversion) and 02_Controllers.py (T_sp/RH_sp/seed sliders per the ranges above, cached_weather with the 7/21 frozen-file branch, st.cache_data run_all_four over the four src step functions with state None fresh per run, shared-axes overlay conversion) per D-01 and D-03. Extend tests/test_dashboard.py with the controllers-helper headless compute check (structure + holdout cost ordering + 30 s perf guard) and page-source scans (no compare(, no evolve/genetic_algorithm in 02 page beyond ga_fuzzy_step import, no Agg/show/savefig, no weather/-targeted generate calls). Keep every artifact path repo-relative and every command on conda python.
  </action>
  <verify>
    <automated>python tests/test_dashboard.py</automated>
    <fails_when>nonzero exit code, or any line containing FAIL, or missing PASS line for test_controllers_helper</fails_when>
    <automated>python tests/test_notebooks.py</automated>
    <fails_when>nonzero exit code, or any line containing FAIL (prior-phase audit harness must stay green)</fails_when>
  </verify>
  <done>A reviewer can move Model Sim duty sliders and Controllers setpoint/seed sliders and watch live charts recompute in seconds with frozen seeds untouched.</done>
  <reversibility rating="reversible">Pages add no src/ changes and write only to tempfiles; delete pages to revert</reversibility>
</task>

<task type="auto">
  <name>Expansion: GA Explorer page + suite completion and guards</name>
  <files>dashboard/pages/03_GA_Explorer.py, tests/test_dashboard.py</files>
  <read_first>
    - dashboard/pages/02_Controllers.py (expansion output — cache + tempfile style to mirror)
    - .planning/phases/07-streamlit-dashboard/07-PATTERNS.md section 03_GA_Explorer.py (loader asserts, convergence + MF overlay verbatim sources, no-math audit)
    - .planning/phases/07-streamlit-dashboard/07-RESEARCH.md per-page map row 03, Anti-Patterns (loader vs raw json, no page tri clones), Pitfall 6 (log scale)
    - notebooks/04_ga_optimization.ipynb cell 3 (convergence panel) and notebooks/06_final_results.ipynb cell 5 (MF before/after overlay)
    - src/ga_fuzzy_controller.py lines 37-77 (load_optimized_mfs schema-v2 validation, mtime cache, deepcopy returns) and src/fuzzy_controller.py lines 18-42 (FUZZY_MFS six groups + tri helper)
    - results/ga_optimized_params.json top-level keys (mfs six groups len-5, coupling k_heat/k_vent, schema_version 2, history.best[50]/mean[50])
  </read_first>
  <acceptance_criteria>
    - 03_GA_Explorer.py loads MFs only via load_optimized_mfs (assert schema_version == 2 via the loader path); raw json.load touches only history.best/mean, coupling, and elite display scalars; page never imports genetic_algorithm and contains no evolve/train/fit/evolution identifiers per D-02
    - Convergence chart plots gens 1-50 history.best solid + history.mean alpha 0.7 with generation/cost labels, converted from 04 cell 3 with st.pyplot(fig)
    - MF before/after overlay imports tri and FUZZY_MFS from src.fuzzy_controller (no local tri/def math), hand curves C0- alpha 0.5 vs GA curves C1-- alpha 0.8 over np.linspace 400 grids, covering at least eT and eH groups with an optional group dropdown for the remaining deT/du/deH/dv
    - Page defines no def/class metric or MF math (mirrors test_no_math_in_0506 scan); no Agg/show/savefig; no open(..., w) anywhere under dashboard/
    - python tests/test_dashboard.py passes all PROOF-02a-g checks (page set, import smoke, controllers helper, results helper, explorer helper with 6 MF groups len-5 + history.best len 50, artifact guard, perf guard) and the full prior-phase chain python tests/test_metrics.py plus python tests/test_notebooks.py stays green
  </acceptance_criteria>
  <action>
    Create 03_GA_Explorer.py (three-dirname bootstrap, loader-first MF access, convergence + before/after conversions, elite params/coupling/weights display via st.metric or st.dataframe) per D-02, then complete tests/test_dashboard.py to the full PROOF-02a-g matrix from RESEARCH Validation Architecture including test_explorer_helper and the static source audits (no def math in 03/04 pages, no Agg/show/savefig, no absolute paths, COLUMNS/8-row/schema asserts present). Keep GAK artifact reads repo-relative on conda python with zero new installs.
  </action>
  <verify>
    <automated>python tests/test_dashboard.py</automated>
    <fails_when>nonzero exit code, or any line containing FAIL, or fewer than 7 PASS lines (one per PROOF-02a-g check)</fails_when>
    <automated>python tests/test_metrics.py</automated>
    <fails_when>nonzero exit code, or any line containing FAIL (Phase 05 scoreboard contract must stay green)</fails_when>
  </verify>
  <done>GA Explorer exhibits the frozen artifact (convergence + tuned MFs + elite params) with no live evolution, and the dashboard suite fully gates the phase.</done>
  <reversibility rating="reversible">Read-only exhibit over the canonical JSON; page deletion reverts cleanly</reversibility>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| reviewer-browser → local Streamlit server | Untrusted widget input (sliders only) crosses into the Python process on localhost |
| dashboard/ pages → repo artifacts | Page code reads frozen results/ CSV and JSON plus weather/ CSVs; writes must never cross this boundary |
| dashboard/ pages → tempfile sandbox | Custom-seed weather synthesis writes only to ephemeral tempfile.mkdtemp paths |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-07-01 | Tampering | 02_Controllers.py seed input → open() | medium | mitigate | Seeds are ints from st.slider 1-50 mapped to fixed paths (7 → weather_profile.csv, 21 → holdout_21.csv) or tempfile.mkdtemp(); never interpolate raw widget strings into paths; suite asserts no weather/-targeted generate calls |
| T-07-02 | Tampering | 04_Results.py / 02_Controllers.py vs results/comparison.csv | high | mitigate | Results reads via csv.DictReader with header == COLUMNS + 8-row asserts; Controllers page never imports or calls metrics.compare(); per-commit git status --porcelain results/ weather/ clean check blocks merges on overwrite |
| T-07-03 | Tampering | 03_GA_Explorer.py shared MF arrays | low | mitigate | All MF display goes through load_optimized_mfs which returns defensive deep copies; page code never mutates returned arrays (source scan in suite) |
| T-07-04 | Information disclosure | streamlit run launch | low | mitigate | Docs and tasks launch local-only via python -m streamlit run dashboard/app.py (localhost default); never pass --server.address 0.0.0.0 or disable CORS in any artifact |
| T-07-SC | Tampering | interpreter package set | high | mitigate | Zero new installs this phase (streamlit 1.56.0 / numpy / matplotlib already on conda python); any added dependency must first pass the Package Legitimacy Gate with a blocking human checkpoint; suite scans for pip/install/requirements changes |
</threat_model>

<verification>
<automated>python tests/test_dashboard.py — all PROOF-02a-g checks green (page set, import smoke, controllers helper + 30 s perf guard, results helper, explorer helper, artifact guard)</automated>
<fails_when>nonzero exit or any FAIL line, or fewer than 7 PASS lines</fails_when>
<automated>python tests/test_metrics.py; python tests/test_notebooks.py — prior-phase contracts stay green</automated>
<fails_when>nonzero exit or any FAIL line in either suite</fails_when>
<automated>git status --porcelain results/ weather/ — empty after all helper runs</automated>
<fails_when>any output line appears</fails_when>
<human-check>python -m streamlit run dashboard/app.py — reviewer screenshots all four pages, moves Controllers sliders (T_sp, RH_sp, seed incl. 7/21/custom), confirms live charts, log-scale cost, text-only settling, and rank-1 GA verdict; confirms no python3 references in docs</human-check>
</verification>

<success_criteria>
- Four numbered pages render from python -m streamlit run dashboard/app.py with sliders driving the same src/ functions and live charts
- GA Explorer shows only the frozen JSON artifact; Results restates only the frozen CSV with rank-identity verdict
- Full headless suite green, prior suites green, frozen artifacts byte-untouched
- No new dependencies, no python3 references, no writes under dashboard/
</success_criteria>

## Artifacts this phase produces

| File | Kind | Purpose |
|------|------|---------|
| dashboard/app.py | new app entry | set_page_config + landing only (D-01 multipage root) |
| dashboard/pages/01_Model_Sim.py | new page | Slider-driven open-loop plant + weather explorer (D-01) |
| dashboard/pages/02_Controllers.py | new page | All-four shared-weather overlay with setpoint + seed sliders (D-03) |
| dashboard/pages/03_GA_Explorer.py | new page | Frozen-artifact exhibit: convergence + MF before/after + elite params (D-02) |
| dashboard/pages/04_Results.py | new page | Frozen scoreboard table + rank verdict (D-04) |
| tests/test_dashboard.py | new suite | Headless PROOF-02a-g gate in plain-assert style |

<output>
Create `.planning/phases/07-streamlit-dashboard/07-01-SUMMARY.md` when done
</output>
