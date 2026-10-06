# Phase 08 Plan 01: Theme + Export Foundation — Summary

---
phase: 08-theme-export-foundation
plan: "08"
status: complete
tokens_estimate: 60000
key_files_created:
  - .streamlit/config.toml
  - dashboard/helpers.py
key_files_modified:
  - dashboard/pages/01_model_sim.py
  - dashboard/pages/02_controllers.py
  - dashboard/pages/03_ga_explorer.py
  - dashboard/pages/04_results.py
  - tests/test_dashboard.py
decisions:
  - In-hand figure serialization (fig_to_png_bytes(fig)) over build-key caching — pages keep inline figures, zero new page defs
  - figure_png_bytes kept as alias of fig_to_png_bytes for forward-compat with both names
  - No st.cache_data on byte builders — plain functions stay headless-safe under the test stub
  - Verdict formatter is conditional text (HOLDS / does-NOT-hold), never raises on data
deviations:
  - Rule 1 bug (Task 1): binary CSV header split left a trailing \r on CRLF files (header 'rank\r' != 'rank'); fixed with splitlines()[0] before decode
  - Repair (Task 3): an Edit clobbered the `_import_page` def line; restored immediately, verified by read-back
---

## Objective

Greenhouse identity plus export-center plumbing: one light-greenhouse theme
sidecar plus one shared byte-builder module (scoreboard CSV, verdict TXT,
chart PNG) wired as download buttons on the page where each piece of content
lives (D-01..D-04). 7 buttons total: CSV+TXT+PNG on Results, one PNG each on
Model Sim / Controllers, two PNGs on GA Explorer.

## Task results

### Task 1 — Tracer: theme sidecar plus export slice end-to-end on Results
Commit `1f2322d`. Created `.streamlit/config.toml` (6-key light theme:
base light, primary #2E7D32, bg #F7FAF3, secondary #E8F0E1, text #263023,
sans serif) and `dashboard/helpers.py` (`scoreboard_csv_bytes`,
`verdict_text`, `fig_to_png_bytes` + `figure_png_bytes` alias,
`build_results_figure`, `holdout_ranking`). Wired 3 download buttons on
`04_results.py` (comparison.csv/text/csv, holdout_verdict.txt/text/plain,
results_scoreboard.png/image/png, serializer called before st.pyplot) with
explicit light figure/axes face colors. Extended `_stub_streamlit` with
`download_button` in the same commit. Suite green.

### Task 2 — Expansion: chart PNG buttons on Model Sim, Controllers, GA Explorer
Commit `d72fb53`. One PNG button on 01 (model_sim_chart.png), one on 02
(controllers_traces.png), two on 03 (ga_convergence.png, ga_mfs.png), all
mime image/png, all fed by in-hand `fig_to_png_bytes` before st.pyplot.
Explicit light face/ink colors at each figure construction; default C-series
data colors and grid alpha 0.3 kept. Zero new defs on any page (03 stays
zero-def). No compare/evolve/genetic_algorithm imports, no savefig in pages.
Suite green, 7 total buttons.

### Task 3 — Export assertions plus phase gate
Commit `595adc3`. Four new headless tests in existing plain-assert style:
`test_export_scoreboard_csv` (bytes == frozen file, header == COLUMNS),
`test_export_chart_png` (89 50 4E 47 magic, >1 KB — 144588 bytes),
`test_export_verdict` (ga_fuzzy, all four ids, iae_T/iae_H/energy, seeds,
1.0/1.0/0.01), `test_export_wiring` (7 filenames + 3 MIME values across
pages, total == 7). Full suite 11/11 PASS; `git status --porcelain
results/ weather/` shows only pre-existing `??` untracked GA logs, zero
tracked modifications.

## Verification (gate status)

- Theme parses + boots: TOML 6 keys, base light — PASS (screenshot eyeball deferred to orchestrator/human)
- CSV ==: scoreboard_csv_bytes byte-identical to results/comparison.csv — PASS
- PNG magic: \x89PNG + 144 KB payload — PASS
- Verdict substrings: winner ga_fuzzy rank 1, margins 399.48/530.99, per-term all four, seeds 7/21, weights 1.0/1.0/0.01 — PASS
- Suite green: 11/11, all checks passed — PASS
- Artifacts clean: zero tracked modifications under results/ + weather/ — PASS

## Threat model compliance

- T-08-01: helpers read one hardcoded frozen path (results/comparison.csv); bytes carried, never user paths; header asserted == COLUMNS fail-closed
- T-08-02: explicit mime on all 7 buttons (text/csv, text/plain, 5x image/png)
- T-08-03: BytesIO-only, no w-mode opens in pages, tracked-clean gate held
- T-08-SC: zero installs (conda `python` only, never `python3`)

## Known stubs / deferred

None. Manual screenshot eyeball of `python -m streamlit run dashboard/app.py`
(greenhouse chrome + chart contrast + click-through of all 7 buttons) remains
for the orchestrator/human per 08-VALIDATION.md manual-only rows.
