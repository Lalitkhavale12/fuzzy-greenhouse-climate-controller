---
phase: "08"
status: findings
depth: standard
files_reviewed: 7
summary: |
  Phase 08 (theme-export-foundation) verified working: valid light-greenhouse
  theme sidecar, all export byte-builders live in dashboard/helpers.py, all 7
  download buttons are wired with stable filenames and explicit MIME types,
  and python tests/test_dashboard.py passes 11/11. Findings are robustness
  gaps only — unguarded edge cases in the new helpers, a duplicated
  ranking/figure implementation between helpers.py and 04_results.py, and
  minor hygiene nits. No security or data-loss issues; no critical findings.
critical: 0
warning: 3
info: 3
total: 6
---

# Code Review — Phase 08 (theme-export-foundation)

## Summary

Reviewed all 7 Phase 08 files at standard depth: `.streamlit/config.toml` (valid TOML, `[theme]` keys, `base = "light"` per locked decision), `dashboard/helpers.py` (all new defs: `scoreboard_csv_bytes`, `holdout_ranking`, `verdict_text`, `fig_to_png_bytes`, `build_results_figure`), the download-button wiring diffs on all four pages (rest of page code treated as sealed Phase-7), and `tests/test_dashboard.py` (stub + 4 export tests). Independently verified: TOML parses via `tomllib`, CSV bytes are byte-identical to `results/comparison.csv` (1723 bytes), PNG has magic `89 50 4E 47` (144588 bytes), wiring test counts 7 `download_button` calls with the locked filenames/MIME types, and the full suite passes 11/11. Locked decisions (light-only theme, CSV+PNG+TXT only, frozen bytes, `savefig→BytesIO→seek(0)`, verdict reads CSV without recompute) were respected and are not flagged. The 6 findings below are all in new Phase-08 code; nothing critical.

## Findings

### WR-01 — scoreboard_csv_bytes crashes with IndexError on empty file; uses assert for runtime validation
- **Severity:** warning
- **File:** dashboard/helpers.py:55-56
- **Description:** `raw.splitlines()[0]` raises a bare `IndexError` if the CSV is empty (the sibling `load_scoreboard` in `04_results.py:39-40` explicitly guards emptiness, the helper does not), so callers get the wrong exception type outside the documented `ValueError` contract. The header check on line 56 uses `assert`, which is stripped under `python -O`, silently disabling the frozen-artifact guard.
- **Suggestion:** Guard emptiness and raise explicitly:
```python
lines = raw.splitlines()
if not lines:
    raise ValueError("frozen scoreboard is empty: %s" % path)
header = lines[0].decode("utf-8").split(",")
if header != COLUMNS:
    raise ValueError("stale artifact: header != COLUMNS")
```

### WR-02 — verdict_text / holdout_ranking assume well-formed holdout rows; page calls them outside the try block
- **Severity:** warning
- **File:** dashboard/helpers.py:60-77
- **Description:** `holdout_ranking` does `int(r["rank"])` (ValueError on malformed rank); `verdict_text` does `ranked[0]` (IndexError if no `holdout-seed21` rows), `cost["ga_fuzzy"]` / `cost["onoff"]` / `cost["pid"]` (KeyError if any controller is absent from holdout), and `float(...)` (ValueError on bad numbers) — none guarded. `04_results.py:79` calls `verdict_text(rows)` outside the `try/except` at lines 54-58, so a CSV that passes the 8-row/COLUMNS checks but has corrupt holdout rows crashes the page instead of hitting the fail-closed `st.error/st.stop` path.
- **Suggestion:** Either validate inside `verdict_text` (raise `ValueError` on empty ranking / missing controllers) and extend the page's `try` to cover lines 59-80, e.g.:
```python
ranked = holdout_ranking(rows)
if not ranked:
    raise ValueError("no holdout-seed21 rows in scoreboard")
cost = {r["controller"]: float(r["cost"]) for r in ranked}
for c in ("ga_fuzzy", "onoff", "pid"):
    if c not in cost:
        raise ValueError("holdout missing controller: %s" % c)
```
and in `04_results.py` move `ranked = holdout_ranking(rows)` plus the verdict/download block inside guarded handling.

### WR-03 — Ranking, constants, and scoreboard figure implemented twice; page exports the inline copy, helper copy is dead in prod
- **Severity:** warning
- **File:** dashboard/pages/04_results.py:27-29
- **Description:** `ORDER`/`DISPLAY`/`WEATHERS` (helpers.py:42-45 vs 04_results.py:27-29), `holdout_ranking` (helpers.py:60-63 vs 04_results.py:46-49), and the full 3x2 scoreboard figure (`build_results_figure`, helpers.py:123-160 vs inline fig, 04_results.py:85-114) are duplicated. The page's `Download chart (PNG)` button (line 115) serializes the inline `fig`, never `build_results_figure` — so the helper builder is exercised only by the test, and the two figure implementations can drift silently (they already differ structurally: helper paints via `_paint_light`, the page sets facecolors inline). The phase brief states ALL new defs live in helpers with pages as thin wiring; the duplicated `holdout_ranking` and constants violate that.
- **Suggestion:** Make `04_results.py` import the shared pieces (`from dashboard.helpers import ORDER, DISPLAY, WEATHERS, holdout_ranking, build_results_figure`) and build its downloadable/displayed figure via `fig = build_results_figure(rows)`, deleting the local copies. Keeps one source of truth; test then covers the production path.

### IN-01 — helpers.py mutates sys.path and process cwd at import time; SCOREBOARD_PATH is cwd-relative
- **Severity:** info
- **File:** dashboard/helpers.py:28-29
- **Description:** `sys.path.insert(0, ...)` + `os.chdir(...)` run on every import, mutating global process state (cwd changes affect all relative opens repo-wide; repeated under Streamlit reruns). `SCOREBOARD_PATH = "results/comparison.csv"` only resolves because of that `chdir`. The pattern is copied from the sealed Phase-7 pages, so it is consistent — but new code need not repeat it.
- **Suggestion:** Anchor paths to the file location instead of cwd, e.g.:
```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOREBOARD_PATH = os.path.join(ROOT, "results", "comparison.csv")
```
and drop the `os.chdir` (keep the `sys.path` shim only if still needed for `src.` imports, or use the same ROOT join).

### IN-02 — __main__ self-check leaks a file handle and sets the Agg backend too late to take effect
- **Severity:** info
- **File:** dashboard/helpers.py:166-172
- **Description:** Line 166 does `open(SCOREBOARD_PATH, "rb").read()` with no `with` block (unclosed handle, `ResourceWarning`). Lines 171-172 call `matplotlib.use("Agg")` after `matplotlib.pyplot` was already imported at line 31, where backend selection is a no-op — the self-check only works headless by accident of environment. Neither affects the Streamlit path (backend selection there is correctly left to the server).
- **Suggestion:**
```python
with open(SCOREBOARD_PATH, "rb") as _f:
    assert scoreboard_csv_bytes() == _f.read()
```
and move `_mpl.use("Agg")` above any `pyplot` import in the `__main__` block (or drop it — the committed self-check already runs headless in CI via `MPLBACKEND=Agg`).

### IN-03 — figure_png_bytes alias adds a second public name with no callers
- **Severity:** info
- **File:** dashboard/helpers.py:109
- **Description:** `figure_png_bytes = fig_to_png_bytes` creates two public names for one function. Nothing in pages, helpers, or tests imports the alias (all call sites use `fig_to_png_bytes`); it doubles the API surface future callers must choose between.
- **Suggestion:** Delete the alias and keep the single `fig_to_png_bytes` name used everywhere; reintroduce only if a Phase 9/10 consumer actually needs the build-key spelling.

## Verification

- [x] `.streamlit/config.toml` parses as valid TOML; `[theme]` keys (`base="light"`, greenhouse green/background/ink, `font="sans serif"`) confirmed via `tomllib`
- [x] `python tests/test_dashboard.py` from repo root: 11/11 PASS (7 existing + 4 export: `test_export_scoreboard_csv`, `test_export_chart_png`, `test_export_verdict`, `test_export_wiring`)
- [x] `scoreboard_csv_bytes()` output is byte-identical to `results/comparison.csv` (1723 bytes, header == `COLUMNS`)
- [x] `fig_to_png_bytes(build_results_figure(rows))` yields PNG magic `89 50 4E 47`, 144588 bytes (> 1024 floor)
- [x] `verdict_text` contains winner + margins + per-term (`iae_T`/`iae_H`/`energy`) + provenance (`train_seed=7`, `holdout_seed=21`, `1.0/1.0/0.01`)
- [x] Wiring: 7 `download_button` calls across pages with locked filenames (`comparison.csv`, `holdout_verdict.txt`, `results_scoreboard.png`, `model_sim_chart.png`, `controllers_traces.png`, `ga_convergence.png`, `ga_mfs.png`) and explicit MIME (`text/csv`, `text/plain`, `image/png`); `savefig` appears only in `helpers.py`, never in pages
- [x] Streamlit server NOT launched (static review only, per instructions); no source files modified; nothing committed
- [ ] Note (test-fidelity limitation, not a finding): the `download_button` stub returns `None` and generic `_noop` swallows `st.stop`, so import tests cannot exercise the fail-closed error path — acceptable for headless wiring checks, but error-path coverage would need a raising `stop` stub

## Sign-Off

Reviewed: 2026-09-29 (standard depth, 7 files). Status: **findings** — 0 critical, 3 warning, 3 info. Phase 08 is functionally correct and export-verified; the warnings are hardening items (wrong-exception edge cases, duplicated ranking/figure sources) recommended before Phase 9/10 composes these primitives. No security issues found.

_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
