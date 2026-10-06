---
phase: 10-layout-polish-report-bundle
plan: '02'
subsystem: dashboard-ui03-lock
tags: [streamlit, layout, kpi-cards, tabs, headless-tests, ui-03]
requires: [evidence_zip_bytes, results-kpi-tabs-expander, tab-aware-headless-stub]
provides: [uniform-kpi-all-pages, controllers-trace-tabs, layout-assert-lock]
affects: ["10-03"]
tech-stack:
  added: []
  patterns: [frozen-row-kpi-cards, tabbed-trace-display, static-provenance-expander, recorded-stub-metric-assert]
key-files:
  created: []
  modified: [dashboard/pages/01_model_sim.py, dashboard/pages/02_controllers.py, dashboard/pages/03_ga_explorer.py, dashboard/helpers.py, tests/test_dashboard.py]
decisions:
  - Per-signal trace figures via a new build_controller_trace_figure helper; page keeps one combined-figure download plus three tabbed per-signal views
  - KPI values asserted headless by recording stub st.metric calls, not just source scan
metrics:
  duration: ~30 min
  completed: 2026-09-29
  tasks: 3
  commits: 3
status: complete
---

# Phase 10 Plan 02: Remaining-Pages Restyle + UI-03 Lock Summary

Uniform 4-card KPI rows (GA holdout cost, rank, IAE_T, IAE_H from the frozen rank column) plus static provenance expanders on Model Sim, Controllers, and GA Explorer; T/RH/energy trace tabs on Controllers; headless `test_layout_elements` locking KPI values, tab placement, expanders, and narrow-stacking structure. Full suite green, `results/` + `weather/` clean.

## Tasks

### 1. Restyle 01 Model Sim and 03 GA Explorer: KPI rows plus provenance expanders — DONE (4f698dd)

- `dashboard/pages/01_model_sim.py`: `csv` import; helpers import extended with `holdout_ranking, DISPLAY`; `COLUMNS` import; uniform KPI row after the title (read-only CSV read + header/8-row asserts + `ga_fuzzy` holdout lookup, `%.2f`/`#rank` formatting identical to Results); static provenance `st.expander` at the bottom. Single flow, no tabs; light-figure colors and serialize-then-show ordering untouched; preamble verbatim.
- `dashboard/pages/03_ga_explorer.py`: same KPI row as straight-line `st.*` calls reusing the page's existing shape with no new guard block and no new loader path; bottom provenance expander (schema v2, 50 generations, seeds/weights). Zero new top-level `def`/`class` lines (grep count 0, unchanged).
- Verify: `python tests/test_dashboard.py` green including `test_pages_import`.

### 2. Restyle 02 Controllers: KPI row plus T/RH/energy tabs plus expander — DONE (8025f5f)

- `dashboard/helpers.py`: new `build_controller_trace_figure(hours, runs_a, runs_b, T_sp, RH_sp, seed_a, seed_b, group)` — 1x2 side-A/B figure for one signal group (`T`/`RH`/`energy`, heater duty as the energy proxy), setpoint dashed lines for T/RH, `_paint_light` finish, `ValueError` on bad group. All new logic lives in helpers per the thin-page contract.
- `dashboard/pages/02_controllers.py`: uniform KPI row after the title (same frozen-row shape); sliders, `@st.cache_data run_all_four`, and delta/rank lines untouched; combined figure still built by `build_scenario_figure` and still served by the single `controllers_traces.png` download button (export-wiring count stays 10); `tT, tH, tE = st.tabs(["Temperature", "Humidity", "Energy"])` with `with`-block bodies calling `st.pyplot` on helper-built per-signal figures; static provenance expander at the bottom. No `number_input`/`text_input` added; preamble verbatim.
- Verify: full suite green; helper probe renders T/RH/energy PNG magic headless.

### 3. Lock UI-03 with layout asserts and narrow-stacking source scan — DONE (a83b8d3)

- `tests/test_dashboard.py`: `_Stub` gains a `metric` branch recording `(label, value)` into module-level `_METRIC_CALLS` (returns `None`, behavior-identical to the old `_noop`); new `test_layout_elements` asserting `.metric(`/`st.columns(4)`/`st.expander` per page source, `st.tabs` in 02/04 only, KPI first-four metric values equal to the frozen holdout `ga_fuzzy` row (`['114.28', '#1', '1.66', '112.44']`) on every page via fresh stubbed imports, `st.columns` args restricted to 2/4, and no `st.pyplot` inside a column-`with` block (tab `with` blocks pass; figures stay full-width); `test_source_audits` extended with expander/metric-per-page plus locked tab placement, ban list unchanged.
- Verify: `python tests/test_dashboard.py` prints `all checks passed` (17 tests); `git status --porcelain results/ weather/` clean except pre-existing untracked `ga_evolution*.err/.log`; `st.tabs` present only in `02_controllers` + `04_results` sources.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Layout asserts matched literal `st.metric`, but KPI cards call `c1.metric` on column handles**
- **Found during:** Task 3 (first suite run: `FAIL test_layout_elements` + `FAIL test_source_audits`, `('02_controllers.py', 'metric')`)
- **Issue:** The new asserts searched page sources for the literal `st.metric`, which never appears — KPI cards are invoked on the `st.columns(4)` handles (`c1.metric(...)`), and 01's pre-existing range cards were the only literal matches. Same root cause failed both tests.
- **Fix:** Relaxed both asserts to `".metric(" in src`, which matches column-handle and direct calls alike.
- **Files modified:** tests/test_dashboard.py (committed inside task 3's commit a83b8d3)
- **Commit:** a83b8d3

## Verification

- `python tests/test_dashboard.py` → `all checks passed` (17 tests, incl. new `test_layout_elements`)
- KPI values on all four pages equal the frozen holdout `ga_fuzzy` row (cost 114.28, rank #1, IAE_T 1.66, IAE_H 112.44)
- `git status --porcelain results/ weather/` → clean except pre-existing untracked `ga_evolution*.err/.log` (allowed per plan)
- `grep -l st.tabs dashboard/pages/*.py` → `02_controllers.py`, `04_results.py` only
- `grep -c "^def \|^class " dashboard/pages/03_ga_explorer.py` → 0 (unchanged)

## Threat Flags

None — no new surface beyond the plan's threat model. Mitigations implemented as specified: KPI cards read the frozen holdout rows via the rank column only (`holdout_ranking` + `ga_fuzzy` lookup, recorded-value asserts; never argsort/compare/all_metrics on the KPI path) (T-10-05); source audits extended for tabs/expander placement with the ban list unchanged, 03 keeps zero new top-level defs (T-10-06); figures full-width outside columns, KPI row max 4 narrow text cards, structural source-scan only per locked D-04 (T-10-07, accepted); zero installs (T-10-SC).

## Known Stubs

None.

## Self-Check: PASSED

- `dashboard/pages/01_model_sim.py`, `dashboard/pages/02_controllers.py`, `dashboard/pages/03_ga_explorer.py`, `dashboard/helpers.py`, `tests/test_dashboard.py` all present with new code.
- Commits 4f698dd, 8025f5f, a83b8d3 verified via `git log`.
