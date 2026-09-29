---
phase: "10"
status: findings
depth: standard
files_reviewed: 7
files_reviewed_list:
  - dashboard/helpers.py
  - dashboard/app.py
  - dashboard/pages/01_model_sim.py
  - dashboard/pages/02_controllers.py
  - dashboard/pages/03_ga_explorer.py
  - dashboard/pages/04_results.py
  - tests/test_dashboard.py
summary: |
  Phase 10 (layout-polish-report-bundle) adds a correct in-memory evidence-pack
  ZIP builder plus uniform KPI rows, targeted tabs, and provenance expanders;
  the 17/17 headless suite passes and no security or data-correctness defects
  were found, but the two new code paths replicate a fail-closed gap — the KPI
  header blocks and the evidence-ZIP builder/call-site lack the guarded
  st.error/st.stop idiom the same files use elsewhere, so a missing or
  corrupted frozen artifact crashes the page with a traceback. Two warnings,
  no critical issues.
critical: 0
warning: 2
info: 0
total: 2
---

# Code Review — Phase 10 (layout-polish-report-bundle)

## Summary

Reviewed the 7 Phase 10 files at standard depth (full reads + diff against
pre-Phase-10 base at `c6e3854~1` + static security scan + headless test run).
`evidence_zip_bytes`/`ZIP_MEMBERS` are correct (PK magic, exact 10-member
namelist, byte-identical CSV/JSON members, PNG magic — all asserted green);
the uniform KPI rows render the frozen holdout `ga_fuzzy` row (locked by
`test_layout_elements`); tabs are correctly scoped (Controllers T/RH/energy,
Results train/holdout); provenance expanders exist on all four pages; no
secrets, eval/exec, user-controlled paths, or write-mode opens in the new
code. Two robustness warnings: the new KPI blocks and the new ZIP
builder/call-site skip the fail-closed guards (`try/except` + `st.stop`) that
the same files already use for the scoreboard and GA artifact, so artifact
corruption/missing-file edges raise uncaught (`StopIteration`, bare
`AssertionError`, raw `OSError`) instead of a friendly page error. No
critical (bug/data-loss/security) issues. Sealed Phase-8/9 builders and the
locked decisions (KPI content, tab placement, ZIP membership, stacking) were
not flagged.

## Findings

### WR-01 — New KPI header blocks lack fail-closed guards (bare open/assert/next)

- **Severity:** warning
- **File:** dashboard/pages/01_model_sim.py:62-66
- **Description:** The Phase 10 KPI block opens the frozen scoreboard with a
  bare `open()` (no `try/except`), validates with bare `assert` (stripped
  under `python -O`, and uncaught `AssertionError` renders as a Streamlit
  traceback rather than `st.error`), and resolves the row with
  `next(r for r in holdout_ranking(_rows) if ...)` with no default — a CSV
  missing the `ga_fuzzy` holdout row raises uncaught `StopIteration`, and
  `float(kpi[...])` raises uncaught `ValueError`/`KeyError` on malformed
  cells. The identical block is replicated in `02_controllers.py:69-73` and
  `03_ga_explorer.py:35-39` (both fully unguarded), and in
  `04_results.py:52` the `next(...)` sits *outside* the `try` block
  (`04_results.py:44-50`), whose except tuple
  `(OSError, ValueError, AssertionError, KeyError)` does not include
  `StopIteration` anyway. This contradicts the fail-closed idiom the same
  files already use (`load_scoreboard` + `st.stop` on 04;
  `try/except + st.stop` around the GA artifact on 03). Trigger requires a
  missing/corrupted frozen CSV, so impact is low — robustness gap, not a
  live-data bug — hence warning, not critical.
- **Suggestion:** Wrap each KPI header in the established guard, e.g. on
  `01_model_sim.py`:
  ```python
  try:
      with open("results/comparison.csv") as _f:
          _rows = list(csv.DictReader(_f))
      assert list(_rows[0].keys()) == COLUMNS, "stale artifact: header != COLUMNS"
      assert len(_rows) == 8, "expected 4 controllers x 2 weathers"
      kpi = next(r for r in holdout_ranking(_rows) if r["controller"] == "ga_fuzzy")
  except (OSError, ValueError, AssertionError, KeyError, StopIteration) as exc:
      st.error("Frozen scoreboard unreadable: %s" % exc)
      st.stop()
  ```
  Same wrap on 02/03; on 04 move line 52 inside the existing `try` and add
  `StopIteration` to the except tuple. (Better still: share one
  `load_kpi_row()` helper so the block is not quadruplicated.)

### WR-02 — evidence_zip_bytes has no error translation and its call-site is unguarded

- **Severity:** warning
- **File:** dashboard/helpers.py:60-84
- **Description:** The new `evidence_zip_bytes()` opens four frozen inputs
  (scoreboard CSV at line 68, six notebook PNGs at line 79, GA JSON at line
  81) with no `try/except`, unlike its sibling `scoreboard_csv_bytes()` which
  translates `OSError` into `ValueError("frozen scoreboard unreadable: ...")`.
  Its sole call-site (`dashboard/pages/04_results.py:84`,
  `data=evidence_zip_bytes()`) evaluates eagerly on every rerun *outside* the
  page's fail-closed `try` block (lines 44-50), so a missing PNG/JSON raises a
  raw `OSError` traceback on the Results page instead of `st.error + st.stop`.
  Also note the builder re-reads the scoreboard (`DictReader` at line 69 plus
  `scoreboard_csv_bytes()` at line 72) — harmless duplication, mentioned only
  for cleanup, not counted separately. No security concern: all ZIP names are
  flat literals from the fixed `ZIP_MEMBERS` allowlist, no user input reaches
  any path.
- **Suggestion:** Mirror the sibling idiom in the builder:
  ```python
  try:
      with open(SCOREBOARD_PATH, newline="") as f:
          rows = list(csv.DictReader(f))
      ...
  except OSError as exc:
      raise ValueError("frozen evidence input unreadable: %s" % exc)
  ```
  and guard the call-site on `04_results.py` (build the bytes inside the
  existing `try`, or wrap line 84 in its own `try/except (OSError, ValueError)
  → st.error/st.stop`).

## Verification

- [x] Ran `python tests/test_dashboard.py` from repo root: **17/17 PASS**
  (`all checks passed`, zero FAIL lines) — conda `python` 3.14.6 pinned
  interpreter, no browser, no Streamlit server launched
- [x] `test_evidence_zip`: PK magic, 10/10 `ZIP_MEMBERS` namelist-exact,
  CSV/JSON members byte-identical to frozen artifacts, chart PNG magic ok
- [x] `test_layout_elements`: all four pages' first-4 metric values equal the
  frozen holdout `ga_fuzzy` row (cost/rank/IAE_T/IAE_H); tabs locked to
  02/04 only; expanders on all pages; `st.columns` args in (2, 4);
  `st.pyplot` never nested inside a column `with` block (clean stacking)
- [x] `test_export_wiring`: 10 download buttons with exact filenames+MIME
  (incl. `greenhouse_evidence_pack.zip` / `application/zip` on 04)
- [x] Static scan of the Phase 10 diff: no hardcoded secrets, no
  `eval/exec/innerHTML`, no user-controlled file paths, no `"w"`-mode opens
  in pages, no absolute-path literals
- [x] `git diff c6e3854~1..HEAD` confirms review scope = only the Phase 10
  additions (ZIP builder + `build_controller_trace_figure` + KPI/tabs/expander
  blocks + layout/ZIP tests); sealed builders and locked decisions untouched
  and unflagged

## Sign-Off

Phase 10 is **approved with two warnings to address** (WR-01, WR-02 — both
fail-closed robustness gaps in new code, neither a correctness, security, or
data-loss defect under the shipped frozen artifacts). No source files were
modified, nothing was committed, and no server was launched during this
review. Recommended follow-up: apply the two `try/except + st.stop` guards
above, re-run `python tests/test_dashboard.py` (expect 17/17), and close.
