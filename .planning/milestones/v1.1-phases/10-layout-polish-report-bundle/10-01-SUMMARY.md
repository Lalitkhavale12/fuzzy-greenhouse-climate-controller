---
phase: 10-layout-polish-report-bundle
plan: '01'
subsystem: dashboard-evidence-pack
tags: [streamlit, zipfile, headless-tests, ui-03, ui-07]
requires: []
provides: [evidence_zip_bytes, results-kpi-tabs-expander, tab-aware-headless-stub]
affects: ["10-02", "10-03"]
tech-stack:
  added: []
  patterns: [in-memory-zip-via-stdlib, frozen-byte-provenance, thin-page-wiring]
key-files:
  created: []
  modified: [dashboard/helpers.py, dashboard/pages/04_results.py, tests/test_dashboard.py]
decisions:
  - KPI card titles use DISPLAY["ga_fuzzy"] mapping for cost/rank cards, plain IAE_T/IAE_H labels for term cards
  - Scoreboard tabs split the dataframe view only (train vs holdout rows); CSV download still serves full frozen bytes
  - ZIP filename greenhouse_evidence_pack.zip with MIME application/zip (agent's-discretion default per must_haves)
metrics:
  duration: ~25 min
  completed: 2026-09-29
  tasks: 3
  commits: 3
status: complete
---

# Phase 10 Plan 01: Evidence-Pack Tracer + Results Restyle Summary

One-click in-memory evidence-pack ZIP (stdlib zipfile + BytesIO) built in `dashboard/helpers.py`, served from a download button on the Results page, proven by headless byte asserts; Results page also carries its UI-03 share (uniform 4-card KPI row, Train/Holdout tabs, provenance expander).

## Tasks

### 1. Tracer: evidence_zip_bytes end-to-end through Results download button — DONE (c6e3854)

- `dashboard/helpers.py`: `import zipfile` alongside `io`; ordered `ZIP_MEMBERS` constant (exact 10 flat basenames: comparison.csv, holdout_verdict.txt, results_scoreboard.png, 01_greenhouse_model.png, 02_baselines.png, 03_fuzzy.png, 04_ga_optimization.png, 05_comparison.png, 06_final_results.png, ga_optimized_params.json); `evidence_zip_bytes()` composing only existing builders (`scoreboard_csv_bytes`, `verdict_text`, `fig_to_png_bytes(build_results_figure(rows))`) plus raw `rb.read()` for the six notebook PNGs and GA JSON; `ZIP_DEFLATED`; close-then-`getvalue()` shape. Self-check block extended with PK + namelist asserts.
- `dashboard/pages/04_results.py`: `evidence_zip_bytes` added to the existing helpers import; ZIP `download_button` ("Download evidence pack (ZIP)", `greenhouse_evidence_pack.zip`, `application/zip`) appended after the three existing buttons.
- Verify: `evidence_zip_bytes()` returns PK bytes, 1335833 bytes (>1024); `python dashboard/helpers.py` self-check passes; `grep -c evidence_zip_bytes dashboard/pages/04_results.py` = 2.

### 2. Extend headless stub for tabs and with-blocks plus evidence-ZIP asserts — DONE (bf92e24)

- `tests/test_dashboard.py`: `tabs` branch on `_Stub.__getattr__` mirroring the `columns` handler (one `_Stub` per label); `__enter__`/`__exit__` on `_Stub`; new `test_evidence_zip` (PK magic, `namelist() == ZIP_MEMBERS`, CSV/JSON members byte-equal to frozen files, chart PNG magic); export-wiring audit 9 → 10 with `evidence_pack` + `application/zip` asserts on 04_results source.
- Verify: `python tests/test_dashboard.py` printed `all checks passed`.

### 3. Results-page UI-03 share: uniform KPI row, Train/Holdout tabs, provenance expander — DONE (4df761c)

- `dashboard/pages/04_results.py`: per-controller metric loop replaced with one `st.columns(4)` KPI row reading the already-loaded `ranked` rows via `ga_fuzzy` lookup (`%.2f` cost/IAE_T/IAE_H, `#rank`, DISPLAY label mapping; values equal the frozen holdout row: cost 114.28, rank #1, IAE_T 1.66, IAE_H 112.44); scoreboard dataframe split into `st.tabs(["Train", "Holdout"])` (Train/Holdout labels only on the page); static-text provenance `st.expander` at the bottom (frozen files, seeds 7/21, weights 1.0/1.0/0.01). Preamble verbatim; no savefig/show/Agg/absolute-paths/w-mode opens; figures full-width outside columns; never argsort/compare/all_metrics on the KPI path.
- Verify: full suite green including `test_pages_import`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Stub `expander` fell through to `_noop → None`, crashing every 04_results import once the page used `with st.expander(...)`**
- **Found during:** Task 3 (first suite run after adding tabs/expander to the page: 4 FAILs with `TypeError: 'NoneType' object does not support the context manager protocol`)
- **Issue:** The plan/PATTERNS stub shape added `__enter__/__exit__` to `_Stub` plus a `tabs` branch, but `st.expander(...)` still resolved via the `_noop` fallback returning `None`, so the `with` block crashed. The `tabs` branch was fine (`with tab:` enters a real `_Stub`).
- **Fix:** Added an `expander` branch to `_Stub.__getattr__` returning a fresh `_Stub` per call (same shape as the `tabs`/`columns` handlers).
- **Files modified:** tests/test_dashboard.py (committed inside task 3's commit 4df761c)
- **Commit:** 4df761c

## Verification

- `python tests/test_dashboard.py` → `all checks passed` (16 tests, incl. new `test_evidence_zip`)
- ZIP probe: PK magic, 1335833 bytes
- `git status --porcelain results/ weather/` → clean except pre-existing untracked `ga_evolution*.err/.log` (allowed per plan)
- KPI values match frozen `ga_fuzzy` holdout row (cost 114.27861545714455, rank 1, iae_T 1.6576305484360794, iae_H 112.43965492599315)

## Threat Flags

None — no new surface beyond the plan's threat model. Mitigations implemented as specified: fixed flat-basename `ZIP_MEMBERS` allowlist with exact-namelist assert (T-10-01); BytesIO-only, no w-mode opens under results//weather/, artifacts-untouched gate green (T-10-02); raw `rb.read()` bytes for CSV/JSON/PNG members with byte-equality asserts, KPI/verdict read the CSV rank column (T-10-03); single on-demand build of ~1.3 MB, no caching (T-10-04, accepted); zero installs, stdlib only (T-10-SC).

## Known Stubs

None.

## Self-Check: PASSED

- `dashboard/helpers.py`, `dashboard/pages/04_results.py`, `tests/test_dashboard.py` all present with new code.
- Commits c6e3854, bf92e24, 4df761c verified via `git log`.
