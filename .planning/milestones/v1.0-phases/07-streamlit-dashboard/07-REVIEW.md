---
phase: "07"
status: findings
depth: standard
files_reviewed: 6
summary: |
  All six Phase 07 files were read in full and cross-checked against the src/
  call contracts (step, run_closed_loop, controller steps, load_optimized_mfs,
  COLUMNS). No security issues, no math duplication, no recomputation of frozen
  artifacts, and the suite passes 7/7. Two warnings remain: unhardened frozen-
  artifact loading that crashes pages with raw tracebacks, and a verdict string
  that pairs a dynamic winner name with a hardcoded GA-wins claim.
critical: 0
warning: 2
info: 4
total: 6
---

# Code Review — Phase 07 (streamlit-dashboard)

## Summary

Reviewed the four dashboard pages, the landing page, and the headless test suite
at standard depth: full reads plus verification of every `src/` call signature
(`step(dt, actuators, weather_at_t, T_C, w_gkg)`, `run_closed_loop(step_fn,
weather_path, n, T_sp, RH_sp)`, controller steps accepting `(T, rh, T_sp, RH_sp,
state)` positionally, `load_optimized_mfs` returning deep copies). All calls
match. Locked decisions were respected and not flagged (four-page spec,
JSON/CSV-only reads, slider-driven loops, `python` interpreter, repo-relative
paths via chdir, ephemeral-seed tempfiles). No secrets, injection surfaces, or
user-controlled paths exist — the only path interpolation is `"seed_%d.csv" %
seed` over an int slider value. The two warnings are latent robustness defects,
not live breakage: the frozen artifacts are valid today, so all pages render.

## Findings

### WR-01 — Unhardened frozen-artifact loading crashes pages with raw tracebacks

- **Severity:** warning
- **File:** dashboard/pages/03_ga_explorer.py:30-35; dashboard/pages/04_results.py:30-36
- **Description:** Both pages load their frozen artifacts with no failure
  handling: `open()` + `json.load()` / `csv.DictReader` with direct key access
  (`d["history"]["best"]`, `float(r["cost"])`). A missing, corrupt, or
  schema-drifted artifact raises `FileNotFoundError` / `JSONDecodeError` /
  `KeyError` and kills the page with a raw traceback. In `04_results.py`,
  `rows[0]` (line 34) raises `IndexError` on an empty CSV *before* the
  helpful `len(rows) == 8` assert is reached, so the fail-closed message never
  fires in exactly the case it was written for. The `assert`-based guards
  (`schema_version == 2`, header `== COLUMNS`) are also stripped under
  `python -O`, silently disabling the provenance checks.
- **Suggestion:** Validate explicitly and fail with a page message instead of
  a traceback, e.g.:
  ```python
  import streamlit as st
  try:
      rows = load_scoreboard()
  except (OSError, AssertionError, KeyError, IndexError) as exc:
      st.error("Frozen scoreboard unreadable: %s" % exc)
      st.stop()
  ```
  and replace `assert d["schema_version"] == 2` with `if d.get("schema_version")
  != 2: st.error(...); st.stop()`. Reorder `load_scoreboard` to check
  `if not rows: raise ValueError("scoreboard CSV is empty")` before touching
  `rows[0]`.

### WR-02 — Verdict string pairs dynamic winner with hardcoded GA-wins claim

- **Severity:** warning
- **File:** dashboard/pages/04_results.py:59-60
- **Description:** `winner` is derived dynamically from the CSV rank column,
  but the success message hardcodes the GA claim: `"Verdict: %s ranks #1 on
  holdout — GA < on/off AND GA < PID holds" % DISPLAY[winner]`. If the frozen
  artifact ever changed rank-1 (regenerated CSV, new controller), the page
  would print a self-contradictory verdict such as "Verdict: PID ranks #1 on
  holdout — GA < on/off AND GA < PID holds". The claim must be computed, not
  asserted, given the winner is computed.
- **Suggestion:** Derive the claim from data:
  ```python
  cost = {r["controller"]: float(r["cost"]) for r in ranked}
  beats = (cost["ga_fuzzy"] < cost["onoff"]
           and cost["ga_fuzzy"] < cost["pid"])
  st.success("Verdict: %s ranks #1 on holdout" % DISPLAY[winner])
  if beats:
      st.success("GA < on/off AND GA < PID holds")
  else:
      st.warning("GA-beats-baselines claim does NOT hold in this artifact")
  ```

### IN-01 — Hardcoded convergence title contradicts dynamic history length

- **Severity:** info
- **File:** dashboard/pages/03_ga_explorer.py:52
- **Description:** The axes plot `len(best)` generations from the artifact but
  the title hardcodes `"GA convergence (50x50, train seed-7)"`. The page
  already displays population/generations dynamically in the dataframe
  (line 41-43); a re-tuned artifact with different generations would render a
  lying title next to correct data.
- **Suggestion:** `ax.set_title("GA convergence (%dx%d, train seed-%d)" %
  (d["population"], d["generations"], d["train_seed"]))`.

### IN-02 — Magic initial condition in open-loop runner

- **Severity:** info
- **File:** dashboard/pages/01_model_sim.py:44
- **Description:** `T, w = 29.28, 20.0` carries only a trailing comment.
  Numeric literals with physical meaning (initial inside-T and absolute
  humidity) should be named constants, consistent with the `params[...]` style
  used one line above (`params["A_sol"]`).
- **Suggestion:** `T_INIT_C, W_INIT = 29.28, 20.0  # probe-verified baseline`
  at module top, then `T, w = T_INIT_C, W_INIT`.

### IN-03 — Import-smoke test silently skips missing pages

- **Severity:** info
- **File:** tests/test_dashboard.py:107-108
- **Description:** `test_pages_import` uses `continue` when a page file is
  absent, turning a missing deliverable into a silent pass. Presence is
  covered by `test_page_set`, so the gap is masked only if both tests are run
  together; run in isolation (`pytest test_dashboard.py -k pages_import`), a
  deleted page passes.
- **Suggestion:** Replace `continue` with an explicit failure:
  `assert os.path.exists(...), "missing page file: %s" % fname`.

### IN-04 — Streamlit stub permanently replaces sys.modules entry

- **Severity:** info
- **File:** tests/test_dashboard.py:26-70
- **Description:** `_stub_streamlit()` overwrites `sys.modules["streamlit"]`
  with no teardown/restore. The standalone runner is unaffected, but under
  `pytest` the stub leaks into the session: any later test module importing
  real `streamlit` receives the `_Stub` instead, producing confusing
  attribute behavior far from the cause.
- **Suggestion:** Save and restore around use, e.g. a fixture:
  ```python
  import pytest
  @pytest.fixture
  def stub_streamlit():
      import sys as _sys
      real = _sys.modules.get("streamlit")
      _stub_streamlit()
      try:
          yield
      finally:
          if real is not None:
              _sys.modules["streamlit"] = real
          else:
              _sys.modules.pop("streamlit", None)
  ```

## Verification

- [x] Ran `python tests/test_dashboard.py` from repo root — 7/7 PASS
  (`test_artifacts_untouched`, `test_controllers_helper` incl. 4x1440 loops in
  ~1.3s with GA beating on/off and PID, `test_explorer_helper`,
  `test_page_set`, `test_pages_import`, `test_results_helper` with GA rank-1
  on holdout, `test_source_audits`), `results/` + `weather/` untouched
- [x] Streamlit server NOT launched (static review only, per instructions)
- [x] No source files modified; no commits made

## Sign-Off

Phase 07 dashboard code is structurally sound: thin wrappers over `src/`,
no duplicated math, no recomputation paths, locked constraints honored.
Two warnings (WR-01 artifact-load hardening, WR-02 verdict-string logic) and
four info items should be addressed, but none blocks the frozen-artifact
dashboard from shipping as-is — all defects are latent against today's valid
artifacts. Security: clean (no secrets, injection, or unsafe deserialization).

---

_Reviewed: 2026-09-28_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
