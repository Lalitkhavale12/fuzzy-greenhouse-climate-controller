# Phase 7: Streamlit Dashboard - Pattern Map

**Mapped:** 2026-09-28
**Files analyzed:** 6 (5 new dashboard files + 1 new test file)
**Analogs found:** 6 / 6 (all via git-tracked repo sources; Streamlit API itself has no in-repo analog — RESEARCH.md hasattr probe covers it)

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `dashboard/app.py` | config (entry/landing) | request-response | `tests/test_notebooks.py` lines 222-228 (`__main__` sys.path + chdir runner) | role-match |
| `dashboard/pages/01_Model_Sim.py` | component (page) | request-response | `notebooks/01_greenhouse_model.ipynb` cells 1-3 (open-loop trace loop + 3-panel plot) | exact |
| `dashboard/pages/02_Controllers.py` | component (page) | request-response | `tests/test_baseline_controllers.py` lines 11-30 (`_run_closed_loop`) + `src/metrics.py` lines 126-152 (`run_closed_loop`) + `notebooks/02_baselines.ipynb` cells 2-3 | exact |
| `dashboard/pages/03_GA_Explorer.py` | component (page) | request-response | `notebooks/04_ga_optimization.ipynb` cell 3 (convergence) + `notebooks/06_final_results.ipynb` cell 5 (MF overlay) + `src/ga_fuzzy_controller.py` lines 37-77 (`load_optimized_mfs`) | exact |
| `dashboard/pages/04_Results.py` | component (page) | request-response | `notebooks/05_comparison.ipynb` cells 2-3 (CSV load + grouped bars + rank) + `results/comparison.csv` (frozen contract) | exact |
| `tests/test_dashboard.py` | test | batch | `tests/test_notebooks.py` (full file — plain-assert harness convention) | exact |

## Pattern Assignments

### `dashboard/app.py` (config, request-response)

**Analog:** `tests/test_notebooks.py` lines 222-241 (repo-root path bootstrap + `__main__` runner)

**Imports / path-bootstrap pattern** (lines 222-228):
```python
if __name__ == "__main__":
    import sys
    # "python tests/test_notebooks.py" puts tests/ on sys.path, not the
    # repo root — prepend the root so the in-body `from src import ...` works
    # both standalone and under pytest (which adds rootdir itself).
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
Page depth is `dashboard/pages/*.py`, hence THREE `dirname` levels (not two) — per RESEARCH.md Pattern 1. `os.chdir` to root keeps repo-relative artifact paths (`results/comparison.csv`) working.

**Landing-only constraint:** `app.py` holds `st.set_page_config` (must be the first `st.*` call) + title/landing markdown only. No `run_closed_loop` / `compare(` / `savefig` in `app.py` — any logic there runs on every page navigation (RESEARCH.md Anti-Patterns).

**Error handling pattern:** none in-repo for Streamlit server errors — fail closed on artifact asserts (header/schema checks raise, Streamlit shows the traceback; no silent fallback).

---

### `dashboard/pages/01_Model_Sim.py` (component, request-response)

**Analog:** `notebooks/01_greenhouse_model.ipynb` cells 1-3

**Imports pattern** (01 cell 0, verbatim minus Agg):
```python
import numpy as np
import matplotlib.pyplot as plt  # NO matplotlib.use("Agg") — fights the Streamlit backend

from src.greenhouse_model import step, load_weather_profile, daytime_solar, params
from src.weather_profile_generator import generate_weather_profile
```

**Weather-guard pattern** (01 cell 1):
```python
CSV = "weather/weather_profile.csv"
if not os.path.exists(CSV):
    generate_weather_profile(CSV, seed=7)
t_min, T_out, w_out = load_weather_profile(CSV)
hours = np.arange(0, 1440) / 60.0          # dt = 60 s -> one step per minute
T_out_hr = np.interp(hours, t_min, T_out)
w_out_hr = np.interp(hours, t_min, w_out)
```
`load_weather_profile` contract (`src/greenhouse_model.py` lines 87-101): `np.loadtxt(path, skiprows=1)`, asserts monotonic minutes spanning 0..1440 and RH in [0,100], returns `(t_min, temp_C, w_out_gkg)` with `w_out` derived via `wsat()`.

**Core open-loop pattern** (01 cell 2 — fixed duties, 24 h):
```python
def schedule(h):
    heater = 0.8 if (h < 6.0 or h >= 20.0) else 0.0
    fogger = 0.5 if (12.0 <= h < 15.0) else 0.0
    ...  # vent 25% always per cell comment
T, w = 29.28, 20.0
T_trace, w_trace, rh_trace = [], [], []
for i, h in enumerate(hours):
    ws = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
    T, w, rh = step(60.0, schedule(h), ws, T, w)
    T_trace.append(T); w_trace.append(w); rh_trace.append(rh)
```
Page adds slider-driven duties (heater/fan/fogger/vent) replacing the fixed `schedule(h)`; loop body is otherwise verbatim. `step` signature (`src/greenhouse_model.py` line 55): `step(dt, actuators, weather_at_t, T_C, w_gkg)` with fail-fast asserts on the exact 4-key actuator dict.

**Chart pattern** (01 cell 3 → page): copy the 3-panel figure verbatim, replace the last two lines:
```python
# notebook:  fig.savefig("notebooks/01_greenhouse_model.png", dpi=120); plt.show()
# page:      st.pyplot(fig)   # fig object, not pyplot state — explicit figs only
```
Construct explicit `fig, ax = plt.subplots(...)` per render; never bare `plt.plot` on global state (Pitfall 4).

---

### `dashboard/pages/02_Controllers.py` (component, request-response)

**Analog:** `tests/test_baseline_controllers.py` lines 11-30 + `src/metrics.py` lines 126-152 + `notebooks/02_baselines.ipynb` cells 2-3

**Closed-loop kernel pattern** — use `src/metrics.py:run_closed_loop`, do NOT copy the test-local `_run_closed_loop` (lines 11-30 shown for shape reference only):
```python
# Source: tests/test_baseline_controllers.py:11-30 (shape reference — page calls src instead)
def _run_closed_loop(np, controller_step, n=1440):
    from src.greenhouse_model import (step, load_weather_profile,
                                      daytime_solar, params,
                                      relative_humidity, wsat_g_per_kg)
    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    ...
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st = None
    ...
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = controller_step(T, rh, 25.0, 70.0, st)
        wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, wx, T, w)
```
Authoritative call (`src/metrics.py` lines 126-137):
```python
def run_closed_loop(controller_step, weather_path, n=1440,
                    T_sp=25.0, RH_sp=70.0):
    assert isinstance(weather_path, (str, os.PathLike)) and str(weather_path), \
        "weather_path required"
```
Shared controller signature — all four take `(T_C, rh_pct, T_sp, RH_sp, state)`: `onoff_step` (`src/onoff_controller.py:15`), `pid_step` (`src/pid_controller.py:19`), `fuzzy_step` (`src/fuzzy_controller.py:63`), `ga_fuzzy_step` (`src/ga_fuzzy_controller.py:80`). Caller owns state; `state=None` = fresh.

**Caching pattern** (RESEARCH.md Pattern 2 — no in-repo analog, API presence verified on installed 1.56.0):
```python
@st.cache_data
def run_all_four(T_sp: float, RH_sp: float, seed: int):
    from src.metrics import run_closed_loop
    from src.onoff_controller import onoff_step
    from src.pid_controller import pid_step
    from src.fuzzy_controller import fuzzy_step
    from src.ga_fuzzy_controller import ga_fuzzy_step
    ...
```
Never cache single `step()` calls — wrap the whole run. `st.slider` (discrete, fires on release) over `st.number_input`; coarse steps (0.5 °C, 1 %RH, integer seeds). Measured budget: full 4×1440 loop = 1.37 s.

**Custom-seed weather pattern** (`notebooks/04_ga_optimization.ipynb` cell 2):
```python
import os, tempfile
from src.weather_profile_generator import generate_weather_profile
holdout_csv = os.path.join(tempfile.mkdtemp(), "holdout_21.csv")
generate_weather_profile(holdout_csv, seed=21)  # any slider seed; ephemeral path
```
Seeds 7/21 resolve to frozen `weather/weather_profile.csv` / `weather/holdout_21.csv` — never regenerate those. `generate_weather_profile` signature (`src/weather_profile_generator.py` lines 15-17): `generate_weather_profile(out_path, seed=7, t_mean=20.0, t_amp=6.0, rh_mean=65.0, rh_amp=18.0, t_peak_h=15.0, ...)`; same seed → byte-identical file.

**Chart pattern** (`notebooks/02_baselines.ipynb` cell 3 + 04 holdout traces): shared-axes T + shared-axes RH + duty panel (04 holdout-trace style, default per RESEARCH.md OQ-2). Explicit figs → `st.pyplot(fig)`.

**FORBIDDEN:** never call `metrics.compare()` from this page — it writes `results/comparison.csv` (`src/metrics.py` lines 191-196), breaking D-04 reversibility.

---

### `dashboard/pages/03_GA_Explorer.py` (component, request-response)

**Analog:** `notebooks/04_ga_optimization.ipynb` cell 3 + `notebooks/06_final_results.ipynb` cell 5 + `src/ga_fuzzy_controller.py` lines 37-77

**Validated MF loader pattern** (`src/ga_fuzzy_controller.py` lines 37-50) — ALWAYS via loader, never raw `json.load` for control/display MFs:
```python
def load_optimized_mfs(path=DEFAULT_PATH):
    global _MFS, _GAINS, _MFS_PATH, _MFS_MTIME
    apath = os.path.abspath(path)
    mtime = os.path.getmtime(apath)
    if _MFS is not None and _MFS_PATH == apath and _MFS_MTIME == mtime:
        return copy.deepcopy(_MFS), copy.deepcopy(_GAINS)
```
Validation asserts (lines 53-65): `set(d["mfs"]) == set(KEYS)` where `KEYS = ("eT","deT","du","eH","deH","dv")`, len-5 centers+widths, numbers-only, finite, widths > 0. Returns defensive deep copies — page must not mutate returned arrays. Raw `json.load` is allowed ONLY for `history.best`/`mean`, `coupling`, elite params (display scalars).

**Convergence pattern** (`notebooks/04_ga_optimization.ipynb` cell 3):
```python
gens = np.arange(1, len(d["history"]["best"]) + 1)
ax[0, 0].plot(gens, d["history"]["best"], label="best")
ax[0, 0].plot(gens, d["history"]["mean"], label="mean", alpha=0.7)
ax[0, 0].set_xlabel("generation")
ax[0, 0].set_ylabel("train weighted cost")
```
Artifact facts (verified this session): top-level keys `mfs, coupling, fitness, weights, train_weather, train_seed, holdout_seed, population, generations, rng_seed, schema_version==2, history{best[50], mean[50]}`; `coupling = {k_heat: 0.05, k_vent: 0.05}`.

**MF before/after pattern** (`notebooks/06_final_results.ipynb` cell 5 — eT shown, repeat for deT/du/eH/deH/dv or eT/eH minimum):
```python
from src.fuzzy_controller import FUZZY_MFS, tri
from src.ga_fuzzy_controller import load_optimized_mfs
mfs_opt, gains_opt = load_optimized_mfs()
grid = np.linspace(lo, hi, 400)
for c, w in zip(FUZZY_MFS[key]["centers"], FUZZY_MFS[key]["widths"]):
    a.plot(grid, [tri(x, c, w) for x in grid], "C0-", alpha=0.5)
for c, w in zip(mfs_opt[key]["centers"], mfs_opt[key]["widths"]):
    a.plot(grid, [tri(x, c, w) for x in grid], "C1--", alpha=0.8)
```
`tri` (`src/fuzzy_controller.py` lines 40-42): `float(np.clip(1.0 - abs(float(x) - c) / w, 0.0, 1.0))`. Hand `FUZZY_MFS` groups (`src/fuzzy_controller.py` lines 20-29): eT centers ±4/width 2.0, deT ±0.5/0.25, du ±0.1/0.05, eH ±30/15.0, deH ±6/3.0, dv ±0.1/0.05. No page-level `tri` clones — import the engine's own helper.

**No-math audit:** page defines no `def` metric/MF math (mirrors `test_no_math_in_0506`, `tests/test_notebooks.py` lines 161-177).

---

### `dashboard/pages/04_Results.py` (component, request-response)

**Analog:** `notebooks/05_comparison.ipynb` cells 2-3 + `results/comparison.csv`

**Scoreboard-load pattern** (05 cell 2 — copy verbatim):
```python
# Source: notebooks/05_comparison.ipynb cell 2 (+ src/metrics.py:32-35 COLUMNS)
import csv
from src.metrics import COLUMNS  # == ["controller","weather","rmse_T","rmse_H",
                                 #     "iae_T","iae_H","ise_T","ise_H","settling_min",
                                 #     "overshoot_T","overshoot_H","energy","cost","rank"]
CSV_PATH = "results/comparison.csv"
with open(CSV_PATH) as f:
    rows = list(csv.DictReader(f))
assert list(rows[0].keys()) == COLUMNS, "stale artifact: header != COLUMNS"
assert len(rows) == 8, "expected 4 controllers x 2 weathers"
```
`COLUMNS` (`src/metrics.py` lines 32-35); rank = 1..4 by cost WITHIN each weather block. stdlib `csv` only — tabular libs forbidden (test allowlist enforces).

**Ranking pattern** (05 cell 3 — never recompute):
```python
ORDER = ["onoff", "pid", "fuzzy", "ga_fuzzy"]
DISPLAY = {"onoff": "on/off", "pid": "PID", "fuzzy": "hand fuzzy", "ga_fuzzy": "GA fuzzy"}
holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
ranked = sorted(holdout, key=lambda r: int(r["rank"]))  # stable: ties keep CSV row order
```
No `argsort`, no cost comparison for ordering — verdict strip follows rank-1 identity + `st.metric` costs. Table via `st.dataframe` (8 rows), KPIs via `st.metric`.

**Bar-chart pattern** (05 cell 3): grouped bars for `iae_T/iae_H/energy/cost` across both weathers; cost panel is LOG-scale (`ax.set_yscale("log")` — ~6× GA-vs-PID range crushes GA on linear); holdout `barh` ranking from CSV `rank`; `settling_min` is a TEXT annotation only (`inf` everywhere — never bars).

---

### `tests/test_dashboard.py` (test, batch)

**Analog:** `tests/test_notebooks.py` (entire file — the repo's only test-suite analog and the mandated style template)

**Harness pattern** (lines 1-17 docstring + 222-241 runner):
```python
"""Plain-assert ... suite ... (PROOF-02x).

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_dashboard.py
"""
```
Runner (lines 230-241): `sys.path.insert(0, <root>); os.chdir(<root>)`, iterate `sorted(globals().items())` for `test_*` callables, print `PASS/FAIL`, `sys.exit(1)` on failure.

**Structural-scan pattern** (mirrors `test_no_math_in_0506`, lines 161-177 + `test_provenance_asserts`, lines 180-196):
```python
# test_no_math_in_0506 shape: read page source as text, assert absences
for line in src.splitlines():
    s = line.strip()
    assert not s.startswith("def "), (rel, s)
    assert not s.startswith("class "), (rel, s)
```
Apply to dashboard pages: no `def ` metric/MF math in 03/04 pages; no `compare(` / `evolve` / `genetic_algorithm` in Results page; no `matplotlib.use("Agg")` / `plt.show()` / `savefig` anywhere under `dashboard/`; no absolute paths (`/home/`, `/Users/`, `C:/`); `== COLUMNS`, `len(rows) == 8`, `schema_version ... == 2`, `load_optimized_mfs` presence asserts.

**Artifact-guard pattern** (mirrors `test_results_untracked_changes`, lines 213-219):
```python
def test_results_untracked_changes():
    import subprocess
    out = subprocess.run(["git", "status", "--porcelain", "results/"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    tracked = [ln for ln in out.splitlines() if not ln.startswith("??")]
    assert not tracked, tracked
```
Extend to `weather/` for the dashboard suite (custom seeds must use tempfiles).

**Headless-validation pattern** (mirrors `test_headless_exec`, lines 199-210): Streamlit pages call `st.*` at import so naive `exec` fails — stub `streamlit` in `sys.modules` before import-smoke, and factor compute into importable helpers (`run_all_four`, results/explorer loaders) tested directly with plain asserts + 30 s perf guard (measured 1.37 s).

## Shared Patterns

### Repo-root path bootstrap
**Source:** `tests/test_notebooks.py` lines 227-228; `tests/test_baseline_controllers.py` lines 205-206 (identical two-liner)
**Apply to:** `dashboard/app.py`, all four page files, `tests/test_dashboard.py`
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```
(Three `dirname` levels for `dashboard/pages/*.py`; two for `dashboard/app.py` and `tests/`.) All artifact paths repo-relative (`results/...`, `weather/...`) — never absolute.

### Fail-fast asserts (no silent fallback)
**Source:** `src/metrics.py` lines 47-53 (`_check_hist`); `src/greenhouse_model.py` lines 95-99 (weather validation); `src/ga_fuzzy_controller.py` lines 53-65 (schema validation)
**Apply to:** all page files (CSV header, row count, schema_version, slider-range clamping)
```python
a = np.asarray(hist, dtype=float)
assert a.size > 0, "history must be non-empty"
assert np.all(np.isfinite(a)), "history must be finite"
```
Pages assert provenance (`header == COLUMNS`, `len(rows) == 8`, `schema_version == 2`) and let failures raise — Streamlit surfaces the traceback; no try/except fallback to stale data.

### Controller-call discipline
**Source:** `src/metrics.py` lines 126-152 (`run_closed_loop` — init `T=20.0, w=0.65*wsat(20)`, `st=None`, `dt=60`, `n=1440`)
**Apply to:** `01_Model_Sim.py`, `02_Controllers.py`
Caller owns state dicts; fresh run = `state=None`; setpoints pass as function args (never baked into controller modules — `test_controller_signatures`, `tests/test_baseline_controllers.py` lines 155-168). NaN inputs raise `AssertionError` (lines 174-179) — sliders make NaN unreachable.

### Frozen-artifact read-only rule
**Source:** `tests/test_notebooks.py` lines 213-219 (`test_results_untracked_changes`); `src/metrics.py` lines 191-196 (`compare()` writes CSV)
**Apply to:** all page files + `tests/test_dashboard.py`
Zero `open(..., "w")` / `compare(` / `weather/`-targeted `generate_weather_profile(` under `dashboard/`. Custom seeds → `tempfile.mkdtemp()` (04 cell-2 precedent). Validation runs `git status --porcelain results/ weather/` clean check.

### Explicit-figure matplotlib discipline
**Source:** `notebooks/05_comparison.ipynb` cell 3 (`fig, ax = plt.subplots(3, 2, ...)`); `notebooks/06_final_results.ipynb` cell 5 (`fig = plt.figure(...); gs = fig.add_gridspec(...)`)
**Apply to:** all four page files
Explicit `fig` construction → `st.pyplot(fig)`; delete `matplotlib.use("Agg")`; no `plt.show()` / `savefig` in pages.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| *(none — all six files have repo analogs)* | — | — | Streamlit server API (`st.slider`, `st.cache_data`, `st.pyplot`, `st.dataframe`, `st.metric`, multipage discovery) has no in-repo precedent (`dashboard/` is greenfield), but RESEARCH.md covers it via live hasattr probe + `source_util.py:58` regex verification on the installed 1.56.0 — planner should cite RESEARCH.md §Standard Stack / Pattern 2 / Assumptions A1-A5, not search for a code analog |

## Metadata

**Analog search scope:** `src/` (8 modules), `tests/` (6 files), `notebooks/*.ipynb` (cells 01/02/04/05/06 extracted this session), `results/comparison.csv` + `results/ga_optimized_params.json` (probed this session)
**Files scanned:** ~16 source/notebook/artifact files
**Git-track gate:** all 14 cited analog paths verified via `git ls-files` (non-empty = tracked); no mirror/untracked paths emitted
**Pattern extraction date:** 2026-09-28
