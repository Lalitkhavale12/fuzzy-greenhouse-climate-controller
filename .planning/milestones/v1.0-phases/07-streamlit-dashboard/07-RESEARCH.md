# Phase 7: Streamlit Dashboard - Research

**Researched:** 2026-09-28
**Domain:** Streamlit 1.56.0 multipage dashboard (thin UI wrapper over NumPy simulation library)
**Confidence:** HIGH

## Summary

Phase 7 wraps the finished `src/` library in a four-page Streamlit multipage app (`dashboard/app.py` + `dashboard/pages/`) with sliders/dropdowns driving the same pure functions the notebooks already prove, and charts rendered via `st.pyplot` by reusing notebook plot code minus the Agg backend line. No new control logic, no new packages, no live evolution, no recomputation of frozen artifacts.

The decisive facts, all established by direct inspection and live probes this session: the full four-controller 1440-step closed loop costs **1.37 s** total (ga_fuzzy 0.99 s dominates), so slider-driven live reruns on the Controllers page are comfortably seconds-scale with no downsampling needed. Every widget and API the plan needs (`cache_data`, `pyplot`, `slider`, `selectbox`, `dataframe`, `metric`, `set_page_config`, `sidebar`, `columns`, `tabs`) exists on the installed Streamlit 1.56.0 [VERIFIED: hasattr probe, this session]. Multipage ordering by numeric filename prefix is confirmed in the installed source (`PAGE_FILENAME_REGEX = re.compile(r"([0-9]*)[_ -]*(.*)\.py")` [VERIFIED: streamlit/source_util.py:58]). pytest is absent so validation follows the repo's plain-assert standalone convention [VERIFIED: probe this session]. The GA artifact is schema v2 with a 50-point `history.best` series [VERIFIED: probe this session].

**Primary recommendation:** Build `dashboard/app.py` + four numbered page files that import `src/` via repo-root `sys.path` insertion, wrap weather loads and closed-loop runs in `st.cache_data`, convert each notebook figure to `st.pyplot` by dropping `matplotlib.use("Agg")`, generate Controllers-page custom-seed weather to `tempfile` paths (never committed), and prove the app headless with import-smoke + compute-helper tests in the existing plain-assert style.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Exactly the spec four: Model Sim (plant + weather), Controllers (all four side-by-side), GA Explorer (convergence + MF before/after), Results (scoreboard + verdict). Multipage `dashboard/` app.
- **D-02:** Artifact explorer ONLY: convergence curves + MF before/after + elite params from `results/ga_optimized_params.json` (schema v2). NO live evolution in-app (the 25-min run has no place in a UI; not even a tiny demo — the saved artifact is the exhibit).
- **D-03:** Side-by-side overlay: setpoint + weather-seed sliders, all four controllers on shared weather in one chart set — the comparison made interactive. Sliders re-run the closed loop live (seconds-scale per the notebook probes).
- **D-04:** Results page reads `results/comparison.csv` (frozen 14-col contract) — table + verdict, instant and always consistent with Phase 5. Never recomputes. — **Reversibility:** reversible — UI-only read path; the artifact stays canonical.

### the agent's Discretion
- Multipage layout mechanics (`dashboard/app.py` + `pages/`) vs single-file navigation within Streamlit conventions; widget choices (slider ranges/steps, dropdown vs radio) within the locked contents.
- Chart library path (matplotlib via st.pyplot reusing notebook-proven plotting vs Streamlit native charts) — reuse wins where a notebook plot already exists.
- Session-state/caching discipline (`st.cache_data` on weather loads + closed-loop runs) for live-update responsiveness.
- Weather-seed handling on the Controllers page (fresh-tempfile generation vs curated seed list) within repo-relative paths.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROOF-02 | Streamlit dashboard with four pages — thin UI wrapper with sliders/dropdowns calling the same `src/` functions, live-updating charts | Multipage mechanics + `sys.path` pattern; per-page compute/chart map reusing notebook-proven plots; `st.cache_data` discipline; 1.37 s measured rerun budget; headless validation plan below |

## Project Constraints (from AGENTS.md)

- **Tech:** Python 3, NumPy (numerics), Streamlit (dashboard UI). Matplotlib for plotting. CSV for weather input, JSON for GA params.
- **Order:** dashboards last — Phases 1–6 are complete, so all `src/` contracts below are stable inputs, not moving targets.
- **Compatibility:** notebooks run against `src/` with no duplicated logic — the dashboard inherits the same rule: pages call `src/` functions, never copy their math.
- **Workflow:** repo edits go through GSD commands; planner must keep the atomic `scope(phase-plan):` commit convention noted in CONTEXT.md.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Widget state + rerun orchestration | Streamlit server (dashboard/) | — | Streamlit owns the reactive loop; pages are thin event handlers |
| Simulation numerics (plant step, controllers, metrics) | `src/` library | — | Already pure, stateless, proven; pages call, never reimplement |
| Frozen scoreboard + verdict | `results/` artifacts (read-only) | — | Phase 5/6 contracts are canonical; UI restates, never recomputes |
| Chart rendering | Matplotlib figures via `st.pyplot` | Streamlit native (`st.dataframe`, `st.metric`) for tables/KPIs | Notebook plots are the proven visual spec; native widgets only where no notebook plot exists |
| Ephemeral weather (custom seeds) | `tempfile` paths at request time | `weather/` committed CSVs for seeds 7/21 | Keeps `weather/` frozen; uncommitted by construction |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `streamlit` | 1.56.0 (installed) | Multipage app server, widgets, `st.pyplot`, `st.cache_data` | PROJECT.md tech constraint; already on the project interpreter |
| `numpy` | 2.4.3 (installed) | All numerics via `src/` | Existing project standard |
| `matplotlib` | 3.10.8 (installed) | Figures rendered with `st.pyplot` | Notebook-proven plots convert by deleting one line |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `csv` | — | Results page CSV load | Mandatory (Phase 5 D-02 forbids tabular libs; test_notebooks allowlist enforces) |
| stdlib `json` | — | GA Explorer artifact load | Via `load_optimized_mfs` validated loader, never raw `json.load` for MFs |
| stdlib `tempfile` + `os` | — | Ephemeral custom-seed weather | Controllers-page seed slider; both are on the notebook import allowlist |
| `nbformat` | installed | NOT used by the app — audit tooling only | Validation scripts may parse notebooks; pages must not |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `st.pyplot` (matplotlib reuse) | `st.line_chart` / `st.bar_chart` native | Native charts are less code but cannot reproduce the notebook overlay/montage figures; reuse wins per agent discretion. Use `st.dataframe` + `st.metric` only for the Results scoreboard table and KPI strip, where no notebook plot exists |
| Multipage `dashboard/app.py` + `dashboard/pages/` | Single-file app with `st.tabs` / radio nav | Multipage matches the locked "multipage `dashboard/` app" decision and gives one file per spec page; single-file would tangle four pages' widgets in one namespace |
| `st.cache_data` on runs | `st.session_state` manual memo | `cache_data` is keyed by arguments automatically — slider changes naturally invalidate; hand-rolled session-state memo reimplements cache invalidation badly |

**Installation:**
```bash
# Nothing to install — streamlit 1.56.0, numpy 2.4.3, matplotlib 3.10.8
# already present on the project interpreter (conda python 3.14.6).
# Use `python` (conda), NEVER bare `python3` (a different 3.13 env without streamlit).
```

**Version verification:** Probed live this session — `streamlit 1.56.0`, `numpy 2.4.3`, `matplotlib 3.10.8` on `python` 3.14.6 [VERIFIED: interpreter probe, this session].

## Package Legitimacy Audit

No external packages are installed by this phase — the entire stack is already on the interpreter. Audit covers the relied-upon packages only:

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `streamlit` | PyPI | ~7 yrs (est. 2019) | high | github.com/streamlit/streamlit | OK | Approved — already installed 1.56.0, no install step |
| `numpy` | PyPI | ~20 yrs | high | github.com/numpy/numpy | OK | Approved — existing standard |
| `matplotlib` | PyPI | ~23 yrs | high | github.com/matplotlib/matplotlib | OK | Approved — existing standard |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*No `query package-legitimacy` seam call was needed: zero new installs. If the planner adds any dependency, it must run the legitimacy gate first and gate the install behind `checkpoint:human-verify`.*

## Architecture Patterns

### System Architecture Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │  streamlit run dashboard/app.py  (local only) │
                    │  app.py: set_page_config + landing only       │
                    └──────────────────┬───────────────────────────┘
                                       │ auto-discovers dashboard/pages/
              ┌────────────┬───────────┼────────────┬──────────────┐
              ▼            ▼           ▼            ▼              ▼
     01_Model_Sim  02_Controllers  03_GA_Explorer  04_Results   (numbered => sidebar order)
              │            │           │            │
   sliders ──►│ sliders ──►│  JSON ───►│  CSV ─────►│  (file reads only)
              │            │  read-only │  read-only │
              ▼            ▼           ▼            ▼
     src.greenhouse  src.* 4×     load_optimized_   csv.DictReader
     _model.step +   controller  mfs() + FUZZY_    + COLUMNS assert
     load_weather_   _step +     MFS + tri()        (mirror of 05 cell 3)
     profile         metrics.run_
                     closed_loop
              │            │           │            │
              ▼            ▼           ▼            ▼
        st.pyplot    st.pyplot    st.pyplot     st.dataframe +
        (01 traces)  (02 overlay) (convergence  st.metric verdict
                                  + MF overlay)
```

Data flows one way: widgets/artifacts → `src/` calls → matplotlib figure → `st.pyplot`. Nothing flows back to disk — the app performs zero writes to `results/` or `weather/`.

### Recommended Project Structure
```
dashboard/
├── app.py                 # set_page_config + title/landing only; no compute
└── pages/
    ├── 01_Model_Sim.py        # plant + weather explorer
    ├── 02_Controllers.py      # all-four side-by-side overlay, seed slider
    ├── 03_GA_Explorer.py      # convergence + MF before/after + elite params
    └── 04_Results.py          # comparison.csv scoreboard + verdict
tests/
└── test_dashboard.py      # headless checks (import smoke + compute helpers)
```

Page filenames: leading digits set sidebar order via the installed multipage regex `([0-9]*)[_ -]*(.*)\.py` [VERIFIED: streamlit/source_util.py:58, this session]. Underscores render as spaces in the sidebar [ASSUMED].

### Pattern 1: Repo-root `sys.path` insertion in every entry point
**What:** Each page file (and `app.py`) inserts the repo root at `sys.path[0]` before importing `src/`, mirroring the test convention.
**When to use:** Always — Streamlit executes page scripts with the script's directory context, so `src/` is not importable without it.
**Example:**
```python
# Source: tests/test_notebooks.py:223-228 (repo's own runnable convention)
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.greenhouse_model import step, load_weather_profile, daytime_solar, params
```
(Dashboard depth is `dashboard/pages/*.py`, hence three `dirname` levels vs the test file's two. `os.chdir` to root keeps repo-relative artifact paths like `results/comparison.csv` working — same reason the test harness does it [VERIFIED: tests/test_notebooks.py:226-228].)

### Pattern 2: `st.cache_data` on weather loads + closed-loop runs
**What:** Decorate pure, argument-keyed helpers; Streamlit reruns the script on every widget change and recomputes only what the changed arguments invalidate.
**When to use:** Weather CSV loads (keyed by path/seed) and the full 4×1440 closed-loop run (keyed by setpoints + seed). Never cache stateful controller stepping mid-loop — caching wraps the whole run function, not single `step()` calls.
**Example:**
```python
# API presence verified on installed 1.56.0 (hasattr probe, this session);
# rerun-on-widget-change semantics are standard Streamlit behavior [ASSUMED].
import streamlit as st

@st.cache_data
def cached_weather(seed: int):
    import tempfile, os
    from src.weather_profile_generator import generate_weather_profile
    from src.greenhouse_model import load_weather_profile
    if seed in (7, 21):  # frozen committed files, never regenerate
        path = {7: "weather/weather_profile.csv", 21: "weather/holdout_21.csv"}[seed]
    else:  # ephemeral custom seed — tempfile, never committed
        path = os.path.join(tempfile.mkdtemp(), f"seed_{seed}.csv")
        generate_weather_profile(path, seed=seed)
    return load_weather_profile(path)

@st.cache_data
def run_all_four(T_sp: float, RH_sp: float, seed: int):
    from src.metrics import run_closed_loop
    from src.onoff_controller import onoff_step
    from src.pid_controller import pid_step
    from src.fuzzy_controller import fuzzy_step
    from src.ga_fuzzy_controller import ga_fuzzy_step
    # NB: ga_fuzzy_step loads results/ga_optimized_params.json via its
    # validated loader internally — the page passes no MF math.
    ...
```

### Pattern 3: Notebook-plot → `st.pyplot` conversion
**What:** Copy the notebook figure code verbatim, delete the `matplotlib.use("Agg")` line (Streamlit serves its own backend), pass the figure object to `st.pyplot(fig)`. Never call `plt.show()` or `savefig` in pages.
**When to use:** Every chart on every page — each has a notebook original (map below).
**Example:**
```python
# 01 cell pattern -> page pattern (only the last two lines change)
# notebook:  fig.savefig("notebooks/01_greenhouse_model.png", dpi=120); plt.show()
# page:      st.pyplot(fig)   # fig object, not pyplot state — explicit figs only
```

### Per-page compute/chart map (planner: one task per row)

| Page | Sliders/inputs | Compute (all `src/`) | Chart source (convert, don't redesign) |
|------|---------------|----------------------|----------------------------------------|
| 01 Model Sim | fixed-actuator duties (heater/fan/fogger/vent), weather seed or file dropdown | `load_weather_profile` + open-loop `step()` trace loop (01 cell pattern: fixed duties, 24 h) | 01 3-panel traces (inside T vs outdoor T, w, RH) |
| 02 Controllers | T_sp + RH_sp + weather-seed sliders | `run_all_four` helper: `metrics.run_closed_loop` × 4 on shared weather (mirrors `metrics.compare()` loop but does NOT call `compare()` — no CSV write) [VERIFIED: src/metrics.py:126-152,181-197] | 02 overlay grid (T/RH/duty columns per controller) or one shared-axes set; holdout-trace style from 04 cell 3 |
| 03 GA Explorer | none (artifact explorer; maybe MF-group dropdown eT/eH selector) | `load_optimized_mfs` + raw `json.load` for `history.best`, `coupling`, elite params | 04 convergence panel (`history.best` + `mean` vs generations) + 06 MF before/after overlay (`tri` hand-solid vs GA-dashed) |
| 04 Results | none | stdlib `csv.DictReader` + header `== COLUMNS` + `len(rows) == 8` asserts (verbatim 05 cell 3) | 05 grouped bars + holdout `barh` ranking from CSV `rank` column (never `argsort`); `st.dataframe` table + `st.metric` verdict strip above the fold |

### Anti-Patterns to Avoid
- **Page-level metric/MF math:** any `def` of error metrics, centroid, or `tri` clones inside a page — call `src/metrics.py` kernels and `src/fuzzy_controller.py:tri` instead (the 05/06 `test_no_math_in_0506` audit exists precisely because this drift happened before).
- **Calling `metrics.compare()` from the Controllers page:** it writes `results/comparison.csv` as a side effect [VERIFIED: src/metrics.py:191-196] — the page must run its own `run_closed_loop` loops (D-04 reversibility depends on the CSV staying frozen).
- **`plt.show()` / `savefig` / `matplotlib.use("Agg")` in pages:** Agg fights the Streamlit backend; figures go to `st.pyplot(fig)`, nowhere else.
- **Regenerating seed-7/21 into `weather/`:** those two CSVs are frozen; custom seeds go to `tempfile.mkdtemp()` paths following the 04 cell-3 isolated-tempfile precedent.
- **Raw `json.load` of GA MFs for control:** always go through `load_optimized_mfs` (schema-v2 validation, mtime-aware cache, defensive copies) [VERIFIED: src/ga_fuzzy_controller.py:37-77].
- **Compute in `app.py`:** landing page only — any logic there runs on every page navigation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reactive rerun + memoization | Session-state memo dicts, manual dirty flags | `st.cache_data` keyed by (setpoints, seed) | Argument-keyed invalidation is exactly the slider-change semantics; hand memo gets stale-cache bugs |
| Multipage navigation | `st.tabs` mega-file with radio router | `dashboard/app.py` + numbered `dashboard/pages/*.py` | Locked decision D-01; framework routing gives sidebar + deep links free |
| Scoreboard table | Custom HTML/markdown tables | `st.dataframe` over the 8 CSV rows | Sorting/filtering free; matches "reviewer's front door" goal |
| Verdict strip | Computed ranking in the page | Read CSV `rank` column + `st.metric` | 05/06 established rank-reads-never-recomputes; page must not `argsort` |
| MF curves | Reimplementing triangular math for display | `src/fuzzy_controller.py:tri` (the engine's own helper) [VERIFIED: src/fuzzy_controller.py:40-42] | Display-vs-engine drift is a silent correctness bug; 06 cell 6 already proves the pattern |
| Weather synthesis | Inline sine/noise code in a page | `src/weather_profile_generator.py:generate_weather_profile` (seed-deterministic) [VERIFIED: src/weather_profile_generator.py:15-27] | Byte-identical-per-seed guarantee (D-12) lives in that function |

**Key insight:** Every hard problem in this phase (deterministic weather, validated MF loading, metric identity, proven charts) was already solved in Phases 1–6 with tests pinning the behavior. The dashboard's only job is calling those solutions from widgets — any new logic in `dashboard/` is scope smell per CONTEXT.md Specifics.

## Common Pitfalls

### Pitfall 1: `python3` vs `python` interpreter split
**What goes wrong:** `streamlit` imports fine in dev but `ModuleNotFoundError` under a different launcher.
**Why it happens:** `python` is the conda 3.14.6 env carrying streamlit 1.56.0; bare `python3` on PATH is a separate 3.13 interpreter without it (verified this session).
**How to avoid:** All shebangs, docs, and validation commands use conda `python` (`python -m streamlit run dashboard/app.py`, `python tests/test_dashboard.py`).
**Warning signs:** Any command line containing `python3` or `pip3` in phase artifacts.

### Pitfall 2: Frozen-artifact overwrite from the UI process
**What goes wrong:** Reviewer reruns the app and `results/comparison.csv` or `weather/*.csv` silently changes; Phase 5/6 provenance breaks.
**Why it happens:** `metrics.compare()` writes the CSV as a side effect [VERIFIED: src/metrics.py:191-196]; a careless import-and-call or a `generate_weather_profile` pointed at `weather/` overwrites frozen files.
**How to avoid:** Pages never call `compare()`; custom seeds generate under `tempfile.mkdtemp()`; validation includes the `git status --porcelain results/ weather/` clean check (mirrors `test_results_untracked_changes` [VERIFIED: tests/test_notebooks.py:213-218]).
**Warning signs:** `compare(`, `generate_weather_profile(` with a `weather/` target, or any `open(..., "w")` under `dashboard/`.

### Pitfall 3: Full 4×1440 rerun on every keystroke
**What goes wrong:** Typing a setpoint digit-by-digit fires expensive reruns; UI feels laggy.
**Why it happens:** Streamlit reruns the whole page script on each widget delta; without caching each rerun costs the full measured 1.37 s (fuzzy + ga_fuzzy dominate: 0.55 s + 0.99 s [VERIFIED: timing probe, this session]).
**How to avoid:** `st.slider` (discrete steps, fires on release) over `st.number_input` for setpoints/seed; `@st.cache_data` on `run_all_four` so unchanged-argument reruns are instant; coarse slider steps (0.5 °C, 1 %RH, integer seeds).
**Warning signs:** `number_input` or `text_input` driving the closed-loop call; missing `cache_data` on the run helper.

### Pitfall 4: Matplotlib global-state bleed between pages
**What goes wrong:** A figure from one page renders inside another, or successive slider moves overplot onto the same axes.
**Why it happens:** `plt.plot` on the implicit global figure persists across reruns within the session.
**How to avoid:** Construct explicit `fig, ax = plt.subplots(...)` (or `fig = plt.figure(...)`) per render and pass `fig` to `st.pyplot(fig)`; never rely on `plt.gcf()`. The 04/05/06 cells already use the explicit-fig form — copy it.
**Warning signs:** Bare `plt.plot` without a preceding `subplots`/`figure` assignment in page code.

### Pitfall 5: `settling_min = inf` breaks bar charts
**What goes wrong:** `float("inf")` values crash or blank a bar axis.
**Why it happens:** All eight frozen rows carry `settling_min = inf` (verified in `results/comparison.csv:2-9`) — never-settled under the joint band.
**How to avoid:** Follow the 05 cell-4 precedent verbatim: settling is a text annotation, never bars.
**Warning signs:** `settling_min` appearing in any bar-chart data mapping.

### Pitfall 6: Cost panel on a linear scale hides the GA win
**What goes wrong:** Reviewer sees one tall bar and three flat lines; the verdict visual fails.
**Why it happens:** ~6× cost range between GA (~107–114) and PID (~643–645) [VERIFIED: results/comparison.csv].
**How to avoid:** Copy the 05 precedent: cost panel is log-scale (`ax.set_yscale("log")`).
**Warning signs:** A linear cost axis in page code or screenshots.

## Code Examples

Verified patterns from repo sources (all read this session):

### Scoreboard load with provenance asserts (Results page — copy verbatim)
```python
# Source: notebooks/05_comparison.ipynb cell 3 (+ src/metrics.py:32-35 COLUMNS)
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

### Holdout ranking from the rank column (Results page — never recompute)
```python
# Source: notebooks/05_comparison.ipynb cell 4
ORDER = ["onoff", "pid", "fuzzy", "ga_fuzzy"]
DISPLAY = {"onoff": "on/off", "pid": "PID", "fuzzy": "hand fuzzy", "ga_fuzzy": "GA fuzzy"}
holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
ranked = sorted(holdout, key=lambda r: int(r["rank"]))  # stable: ties keep CSV row order
```

### MF before/after overlay (GA Explorer page — eT shown, repeat for deT/du/eH/deH/dv)
```python
# Source: notebooks/06_final_results.ipynb cell 6 (+ src/fuzzy_controller.py:40-42 tri)
import numpy as np
from src.fuzzy_controller import FUZZY_MFS, tri
from src.ga_fuzzy_controller import load_optimized_mfs
mfs_opt, gains_opt = load_optimized_mfs()  # schema-v2 validated, cached per path+mtime
grid = np.linspace(-8, 8, 400)
for c, w in zip(FUZZY_MFS["eT"]["centers"], FUZZY_MFS["eT"]["widths"]):
    a.plot(grid, [tri(x, c, w) for x in grid], "C0-", alpha=0.5)
for c, w in zip(mfs_opt["eT"]["centers"], mfs_opt["eT"]["widths"]):
    a.plot(grid, [tri(x, c, w) for x in grid], "C1--", alpha=0.8)
```

### GA convergence curve (GA Explorer page)
```python
# Source: notebooks/04_ga_optimization.ipynb cell pattern + results/ga_optimized_params.json
# JSON top-level keys: mfs{6 groups}, coupling{k_heat,k_vent}, fitness, weights,
# train_weather, train_seed, holdout_seed, population, generations, rng_seed,
# schema_version==2, history{best[50], mean[50]}
import json
d = json.load(open("results/ga_optimized_params.json"))
assert d["schema_version"] == 2
gens = range(1, len(d["history"]["best"]) + 1)  # 50 generations [VERIFIED: probe]
ax.plot(gens, d["history"]["best"], label="best")
ax.plot(gens, d["history"]["mean"], label="mean", alpha=0.7)
```

### Shared-weather four-controller loop (Controllers page kernel)
```python
# Source: src/metrics.py:126-152 run_closed_loop + notebooks/04 cell 3 pattern
from src.metrics import run_closed_loop
# run_closed_loop(controller_step, weather_path, n=1440, T_sp=25.0, RH_sp=70.0)
#   -> (T_hist, RH_hist, U_hist); weather_path REQUIRED, init T=20.0,
#      w=0.65*wsat(20C), dt=60 [VERIFIED: src/metrics.py:126-152].
# Controller signatures share (T_C, rh_pct, T_sp, RH_sp, state):
#   onoff_step(T,rh,T_sp,RH_sp,state,band_T,band_RH) [src/onoff_controller.py:15]
#   pid_step(T,rh,T_sp,RH_sp,state,dt,gains)         [src/pid_controller.py:19]
#   fuzzy_step(T,rh,T_sp,RH_sp,state,dt,mfs)         [src/fuzzy_controller.py:63]
#   ga_fuzzy_step(T,rh,T_sp,RH_sp,state,dt,path)     [src/ga_fuzzy_controller.py:80]
```

### Isolated custom-seed weather (Controllers page seed slider)
```python
# Source: notebooks/04_ga_optimization.ipynb cell 3 (holdout proof pattern)
import os, tempfile
from src.weather_profile_generator import generate_weather_profile
holdout_csv = os.path.join(tempfile.mkdtemp(), "holdout_21.csv")
generate_weather_profile(holdout_csv, seed=21)  # any slider seed; ephemeral path
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `matplotlib.use("Agg"); plt.show(); savefig` in notebooks | Explicit `fig` + `st.pyplot(fig)` in pages | This phase | Same figure code, interactive backend; Agg line must be deleted or it can fight the server backend |
| Notebook `exec` audit (`test_headless_exec`) | Page-level headless checks (import smoke + helper asserts) | This phase | Streamlit scripts can't be `exec`'d naively (they call `st.*` at import); validation must stub or factor helpers |
| Curated seed-7/21 files only | Seed slider with tempfile generation | This phase (agent discretion) | Interactive exploration without touching frozen `weather/` |

**Deprecated/outdated:**
- `st.experimental_memo` / `st.experimental_singleton`: renamed to `st.cache_data` / `st.cache_resource` long before 1.56 — use only the `st.cache_data` form [ASSUMED: API-history knowledge; the installed API presence itself is VERIFIED].
- `st.set_page_config` after any other `st.*` call: must be the first Streamlit call in `app.py` [ASSUMED: documented constraint, unverifiable headless].

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Underscore filenames render as spaced titles in the sidebar; `st.set_page_config` must precede other `st.*` calls | Architecture Patterns | LOW — cosmetic / one-line reorder; planner adds a human-verify screenshot step anyway |
| A2 | `st.cache_data` hashes (T_sp, RH_sp, seed) args and skips rerun compute on cache hit; Streamlit reruns page script per widget change | Architecture Patterns, Pitfalls | LOW — worst case a redundant 1.37 s rerun; still seconds-scale per probe |
| A3 | `st.dataframe` + `st.metric` + `st.slider`/`st.selectbox` semantics follow standard documented behavior on 1.56 | Standard Stack | LOW — API presence verified; only fine-grained behavior assumed |
| A4 | `streamlit run` discovers `dashboard/pages/*.py` from the main script's directory (standard multipage discovery) | Architecture Patterns | MEDIUM — if discovery differs, app shows one page; validation's `streamlit run --server.headless` smoke + sidebar check would catch it before sign-off |
| A5 | The developing-with-streamlit skill's reference docs stay unavailable (version-matched docs need >=1.57); 1.56 multipage knowledge suffices | Summary | LOW — no API used here postdates multipage stabilization |

## Open Questions

1. **Seed-slider range: curated list vs free integer range?**
   - What we know: Agent discretion allows either; tempfile generation makes any integer safe; frozen 7/21 must resolve to committed files.
   - What's unclear: Whether the user wants a bounded demo range (e.g., 1–50) or curated seeds only.
   - Recommendation: Free integer slider 1–50 with 7/21 resolving to frozen files (demonstrates determinism); confirm at plan review — cheap to change.

2. **Controllers chart: 02-style 3×2 grid vs single shared-axes overlay?**
   - What we know: D-03 says "one chart set"; 02 uses per-controller columns, 04 uses shared holdout traces.
   - What's unclear: Which reads better with four controllers × live updates.
   - Recommendation: Shared-axes T + shared-axes RH + duty panel (04 holdout-trace style) as default; planner notes the alternative.

3. **Results verdict computation: restate CSV text vs derive GA<baselines from costs?**
   - What we know: 04 asserts relative ordering (GA < on/off AND GA < PID); CSV holds the numbers.
   - What's unclear: Whether the verdict strip may compare floats or must only display rank.
   - Recommendation: Display rank column + cost `st.metric`s; verdict string follows rank 1 identity — no `argsort`, no recompute, consistent with D-04.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| conda `python` | Everything | ✓ | 3.14.6 | — (do NOT use `python3`/3.13) |
| Streamlit | App server | ✓ | 1.56.0 | — (none; already installed) |
| NumPy | `src/` numerics | ✓ | 2.4.3 | — |
| Matplotlib | `st.pyplot` figures | ✓ | 3.10.8 | — |
| `dashboard/` dir | Phase deliverable | ✗ (to be created) | — | Create in Wave 0 |
| pytest | Test runner | ✗ | — | Plain-assert standalone scripts (`python tests/test_dashboard.py`), repo convention |
| nbformat | Audit of plot reuse (dev-time) | ✓ | installed | — |
| Browser (for visual check) | Human-verify screenshot | unknown | — | Headless checks gate merge; screenshot is a human checkpoint, not automated |

**Missing dependencies with no fallback:**
- None blocking — all runtime deps installed.

**Missing dependencies with fallback:**
- pytest → plain-assert standalone convention (established in all six test files).

## Validation Architecture

Test framework: plain-assert standalone scripts run with conda `python` (no pytest on the interpreter [VERIFIED: probe]). Conventions mirror `tests/test_notebooks.py`: `def test_*` + `__main__` runner that inserts repo root on `sys.path`, `os.chdir`s to root, and exits nonzero on failure [VERIFIED: tests/test_notebooks.py:222-241].

| Property | Value |
|----------|-------|
| Framework | Plain-assert standalone (`python tests/test_dashboard.py`), pytest-style `test_*` names |
| Config file | none — see Wave 0 |
| Quick run command | `python tests/test_dashboard.py` |
| Full suite command | `python tests/test_baseline_controllers.py; python tests/test_fuzzy_controller.py; python tests/test_genetic_algorithm.py; python tests/test_greenhouse_model.py; python tests/test_metrics.py; python tests/test_notebooks.py; python tests/test_dashboard.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROOF-02a | Four pages present, numbered order, `app.py` landing-only (no `run_closed_loop`/`compare(`/`savefig` in `app.py`) | structural (AST/text scan) | `python tests/test_dashboard.py::test_page_set` | ❌ Wave 0 |
| PROOF-02b | Every page imports (stub `streamlit` + `src` path insert; catches SyntaxError/ImportError without a browser) | unit (import smoke) | `python tests/test_dashboard.py::test_pages_import` | ❌ Wave 0 |
| PROOF-02c | `run_all_four` helper: 4 histories × 1440 steps, shared weather, GA cost < on/off AND < PID on seed-21 | unit (headless compute) | `python tests/test_dashboard.py::test_controllers_helper` | ❌ Wave 0 |
| PROOF-02d | Results helper returns 8 rows, header == COLUMNS, ranking follows CSV rank | unit (headless compute) | `python tests/test_dashboard.py::test_results_helper` | ❌ Wave 0 |
| PROOF-02e | GA Explorer helper: schema_version == 2, 6 MF groups len-5, history.best len 50 | unit (headless compute) | `python tests/test_dashboard.py::test_explorer_helper` | ❌ Wave 0 |
| PROOF-02f | No writes to `results/` or `weather/` during helper runs | unit (git-status guard) | `python tests/test_dashboard.py::test_artifacts_untouched` | ❌ Wave 0 |
| PROOF-02g | Controllers rerun budget: `run_all_four` wall time < 30 s | perf guard | timed assert inside `test_controllers_helper` (measured 1.37 s this session) | ❌ Wave 0 |

Static page-source audits (same file, text-scan style like `test_no_math_in_0506`): no `def ` metric/MF math in 03/04 pages, no `compare(` / `evolve` / `genetic_algorithm` imports in Results page, no `matplotlib.use("Agg")` / `plt.show()` / `savefig` anywhere under `dashboard/`, no absolute paths (`/home/`, `/Users/`, `C:/`), all artifact paths repo-relative.

### Sampling Rate
- **Per task commit:** `python tests/test_dashboard.py`
- **Per wave merge:** full suite command above
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `dashboard/app.py` + `dashboard/pages/01–04` — deliverable itself; import-smoke needs files to exist
- [ ] `tests/test_dashboard.py` — all PROOF-02a–g checks
- [ ] Human checkpoint (not automatable headless): `python -m streamlit run dashboard/app.py` screenshot review of all four pages + slider interaction

*(Framework install: none — plain-assert needs no packages.)*

## Security Domain

`security_enforcement` is enabled (`true` in `.planning/config.json` [VERIFIED: .planning/config.json:49]) and `security_asvs_level` is 1; `security_block_on` is `high`. Surface is small but real: a local-only Streamlit server plus file reads of repo artifacts.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local-only study dashboard; no users, no secrets |
| V3 Session Management | no | No sessions beyond Streamlit's ephemeral widget state |
| V4 Access Control | no | Single-user local process |
| V5 Input Validation | yes | Slider-bounded numeric inputs; seed clamped to int range; artifact asserts fail closed (header == COLUMNS, schema_version == 2) |
| V6 Cryptography | no | No crypto (JSON-only GA artifact via stdlib `json`, never pickle/eval — inherited control from `ga_fuzzy_controller.py`) |

### Known Threat Patterns for Streamlit-local + file-read stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via seed/CSV inputs reaching `open()` | Tampering | Seeds are ints mapped to fixed paths or `tempfile.mkdtemp()`; never interpolate raw widget strings into paths; repo-relative constants only |
| Frozen-artifact overwrite from app process | Tampering / Repudiation | No write calls under `dashboard/`; `git status --porcelain results/ weather/` clean check in validation (mirrors `test_results_untracked_changes`) |
| Accidental artifact mutation via shared cache | Tampering | `load_optimized_mfs` returns defensive deep copies [VERIFIED: src/ga_fuzzy_controller.py:76-77]; page code must not mutate returned arrays |
| New dependency supply chain | Tampering | Zero new installs this phase; any addition runs the Package Legitimacy Gate + `checkpoint:human-verify` |
| Server bound to network interface | Information disclosure | Launch headless/local only (`streamlit run` defaults to localhost); never `--server.address 0.0.0.0` or `--server.enableCORS false` workarounds in docs |

## Sources

### Primary (HIGH confidence)
- Repo sources read this session with line citations: `src/greenhouse_model.py:55-101` (step + weather load), `src/metrics.py:30-44,126-197` (weights/COLUMNS/run_closed_loop/compare), `src/fuzzy_controller.py:18-42` (MF groups + tri), `src/ga_fuzzy_controller.py:37-88` (schema-v2 loader + wrapper), `src/onoff_controller.py:15-42`, `src/pid_controller.py:19-44` (shared signatures), `src/weather_profile_generator.py:15-27` (seed determinism), `tests/test_notebooks.py` (audit conventions), `results/comparison.csv` (8 frozen rows), `results/ga_optimized_params.json` (schema v2, 50-gen history)
- Installed-package probes this session: Streamlit 1.56.0 API `hasattr` sweep, `source_util.py:58` multipage regex, interpreter/numerics versions, 4×1440 timing (1.37 s), pytest-absent/nbformat-present check
- Notebook cell extraction this session: 01/02/03 trace grids, 04 convergence + holdout proof, 05 CSV-load/rank/bars, 06 MF overlay + montage

### Secondary (MEDIUM confidence)
- None — all web/documentation providers are disabled in `.planning/config.json` (all `*_search: false`) and the skill's version-matched docs require Streamlit >= 1.57; no secondary lookup was possible or needed.

### Tertiary (LOW confidence)
- Streamlit multipage runtime semantics (sidebar rendering, rerun-on-widget-change, `cache_data` invalidation, `set_page_config` ordering) — standard framework knowledge, tagged [ASSUMED] inline and centralized in the Assumptions Log (A1–A5).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions probed live on the project interpreter; zero new installs.
- Architecture: HIGH — every compute/chart mapping traces to a read-this-session source cell or function; only framework runtime semantics assumed.
- Pitfalls: HIGH — Pitfalls 2/5/6 cite frozen data read this session; Pitfall 3 cites a timed probe; Pitfalls 1/4 cite verified env/code facts.

**Research date:** 2026-09-28
**Valid until:** 30 days (stable: frozen `src/` contracts, pinned local stack, no external drift surface)
