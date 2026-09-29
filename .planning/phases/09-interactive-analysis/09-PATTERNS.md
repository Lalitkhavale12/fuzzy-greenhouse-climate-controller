# Phase 9: Interactive Analysis - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 4 (all modified, zero new files — RESEARCH mandates all new `def`s live in existing `dashboard/helpers.py`)
**Analogs found:** 4 / 4

All analog paths verified git-tracked via `git ls-files` this session (no mirror paths).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `dashboard/helpers.py` (+6 new defs) | service/utility (pure compute) | transform (sim outputs → delta rows; MF dicts → curves; arrays → figs) | `dashboard/helpers.py` itself (existing builders) | exact (self-extension) |
| `dashboard/pages/02_controllers.py` (widget wiring) | page/route (thin wiring) | request-response (sliders → cached sim → plot) | `dashboard/pages/02_controllers.py` lines 36-106 (existing self-pattern) | exact |
| `dashboard/pages/03_ga_explorer.py` (widget wiring) | page/route (thin wiring) | request-response (sliders → sweep/index → overlay plot) | `dashboard/pages/03_ga_explorer.py` lines 31-102 (existing self-pattern) | exact |
| `tests/test_dashboard.py` (+4 new tests) | test | batch (plain-assert standalone suite) | `tests/test_dashboard.py` existing tests (e.g. `test_controllers_helper` lines 153-172) | exact |

New helper `def`s inside `dashboard/helpers.py` classified individually:

| New def | Role | Data Flow | Closest Analog | Match Quality |
|---------|------|-----------|----------------|---------------|
| `scenario_delta` / `run_scenario_pair` | service (pure) | transform | `holdout_ranking` + `verdict_text` (`dashboard/helpers.py:63-106`) | role-match |
| `scratch_mfs_from_deltas` (+ clamp) | service (pure) | transform | `load_optimized_mfs` (`src/ga_fuzzy_controller.py:37-77`) — deepcopy-return + len-5/finite/widths>0 validation shape | role-match |
| `tloop_response_curve` | service (pure) | transform | `infer` (`src/fuzzy_controller.py:45-60`) + MF overlay loop (`03_ga_explorer.py:80-96`) | role+flow match |
| `replay_slice` | utility (pure) | transform | `holdout_ranking` (`dashboard/helpers.py:63-66`) — stateless slice over frozen rows | role-match |
| `build_explorer_figure` / `build_replay_figure` | utility (fig builder) | transform | `build_results_figure` (`dashboard/helpers.py:128-165`) | exact |

## Pattern Assignments

### `dashboard/helpers.py` (service/utility, transform) — EXTEND, no new file

**Analog:** `dashboard/helpers.py` itself (self-extension; module docstring lines 1-21 mandates pages stay thin)

**Imports pattern** (lines 23-33):
```python
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np

from src.metrics import COLUMNS  # frozen column contract, never retyped
```
New defs add (per RESEARCH): `import copy` (deepcopy scratch MFs), local `from src.metrics import all_metrics` inside `scenario_delta`, local `from src.fuzzy_controller import infer` inside `tloop_response_curve`. Keep module-level imports minimal; engine imports stay function-local as RESEARCH examples show.

**Core pure-helper pattern** (lines 63-66, `holdout_ranking` — template for `replay_slice`/`scenario_delta`):
```python
def holdout_ranking(rows):
    """Holdout rows ordered by the CSV rank column (stable: ties keep row order)."""
    holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
    return sorted(holdout, key=lambda r: int(r["rank"]))
```
Copy: one-line docstring stating frozen-input contract, no Streamlit, no I/O, headless-testable. New `scenario_delta(side_a, side_b)` follows this shape — loop `("on/off", "PID", "hand fuzzy", "GA fuzzy")`, `all_metrics(*side[name][:3])` per side, `(B - A)` sign convention, return list-of-dicts (see RESEARCH Pattern 1 lines 163-180 for full body).

**Fig-builder pattern** (lines 117-126 `_paint_light` + lines 128-165 `build_results_figure`):
```python
def _paint_light(fig, axes):
    """Explicit light-figure face + soil-ink colors (theme never touches mpl)."""
    fig.patch.set_facecolor(LIGHT_FACE)
    for a in np.ravel(axes):
        a.set_facecolor(LIGHT_AXES)
        a.tick_params(colors=INK)
        a.title.set_color(INK)
        a.xaxis.label.set_color(INK)
        a.yaxis.label.set_color(INK)
```
Copy verbatim for `build_explorer_figure` / `build_replay_figure`: `plt.subplots` → plot (`C0-` hand solid vs `C1--` scratch dashed) → `_paint_light(fig, ax)` → `fig.tight_layout()` → `return fig` (never close; page serializes via `fig_to_png_bytes`). Reuse module constants `LIGHT_FACE/LIGHT_AXES/INK` (lines 38-40) and `DISPLAY` (lines 42-44).

**Byte-serialization pattern** (lines 109-114):
```python
def fig_to_png_bytes(fig, dpi=150):
    """Serialize an in-hand figure to PNG bytes (never closes the figure)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)  # mandatory — without this the download is empty
    return buf.getvalue()
```
Reuse as-is; new figures go through this function on the page (never add savefig on helpers beyond this one call site).

**Error handling pattern** (lines 48-60, `scoreboard_csv_bytes`):
```python
try:
    with open(path, "rb") as f:
        raw = f.read()
except OSError as exc:
    raise ValueError("frozen scoreboard unreadable: %s" % exc)
```
Copy: `ValueError("...: %s" % exc)` fail-loud style, `%`-formatting (not f-strings) per file convention. Scratch builder returns `(scratch, warnings:list[str])` instead of raising (D-05 warnings-not-crashes) — warnings rendered via `st.warning` on the page.

---

### `dashboard/pages/02_controllers.py` (page/route, request-response) — MODIFIED, widget wiring ONLY

**Analog:** `dashboard/pages/02_controllers.py` itself, lines 36-106

**Seed/tempfile pattern** (lines 36-44) — reuse verbatim per side, do NOT duplicate:
```python
def resolve_weather(seed):
    """Frozen files for seeds 7/21, ephemeral tempfile paths otherwise."""
    if seed == 7:
        return "weather/weather_profile.csv"
    if seed == 21:
        return "weather/holdout_21.csv"
    path = os.path.join(tempfile.mkdtemp(), "seed_%d.csv" % seed)
    generate_weather_profile(path, seed=seed)
    return path
```

**Cached primitive pattern** (lines 47-65) — the ONLY sim entry point, called twice:
```python
@st.cache_data
def run_all_four(T_sp, RH_sp, seed):
    """4 x 1440-step closed loops on the shared weather path.

    Returns (hours, dict name -> (T_hist, RH_hist, U_hist)).
    """
    path = resolve_weather(seed)
    steps = [
        ("on/off", onoff_step),
        ("PID", functools.partial(pid_step, dt=60.0)),
        ("hand fuzzy", functools.partial(fuzzy_step, dt=60.0)),
        ("GA fuzzy", functools.partial(ga_fuzzy_step, dt=60.0)),
    ]
    runs = {}
    for name, ctl in steps:
        T_h, RH_h, U_h = run_closed_loop(ctl, path, n=1440, T_sp=T_sp, RH_sp=RH_sp)
        runs[name] = (T_h, RH_h, U_h)
    hours = np.arange(0, 1440) / 60.0
    return hours, runs
```

**Slider + trace-plot pattern** (lines 68-106):
```python
st.title("Controllers — side-by-side on shared weather")
T_sp = st.slider("T setpoint (degC)", 18.0, 30.0, 25.0, 0.5)
RH_sp = st.slider("RH setpoint (%)", 50, 90, 70, 1)
seed = st.slider("weather seed", 1, 50, 21, 1)

hours, runs = run_all_four(T_sp, RH_sp, seed)
```
Phase 9 wiring: keep ONE shared `T_sp`/`RH_sp` slider pair; add `seed_A = st.slider(...)` + `seed_B = st.slider(...)`; call `run_all_four(T_sp, RH_sp, seed_A)` and `run_all_four(T_sp, RH_sp, seed_B)`; delta rows from `helpers.scenario_delta`; render via `st.dataframe(rows)` + rank line `"GA still wins: side A rank {ra} / side B rank {rb}"`; one combined figure (not 8 `st.pyplot` calls).

**Download pattern** (lines 104-106):
```python
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="controllers_traces.png", mime="image/png")
st.pyplot(fig)
```
Copy for any new Phase 9 figure on this page.

---

### `dashboard/pages/03_ga_explorer.py` (page/route, request-response) — MODIFIED, widget wiring ONLY, zero new `def`s

**Analog:** `dashboard/pages/03_ga_explorer.py` itself, lines 31-102

**Frozen-load pattern** (lines 31-42) — replay + explorer anchor:
```python
try:
    mfs_opt, gains_opt = load_optimized_mfs(JSON_PATH)
    with open(JSON_PATH) as _f:
        d = json.load(_f)
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen GA artifact unreadable: %s" % exc)
    st.stop()
if not (d.get("schema_version") == 2):
    st.error("stale artifact: schema_version != 2")
    st.stop()
best = d["history"]["best"]
mean = d["history"]["mean"]
```
Copy: frozen JSON is the ONLY data source for replay (`history.best`/`history.mean`, len 50 each); `st.error` + `st.stop()` fail-loud style.

**Stub-safe widget pattern** (lines 44-50):
```python
st.subheader("Elite params")
st.metric("train fitness", "%.2f" % d["fitness"])
st.metric("coupling k_heat", "%.3f" % d["coupling"]["k_heat"])
st.dataframe([{"population": d["population"], "generations": d["generations"],
               "train_seed": d["train_seed"], "holdout_seed": d["holdout_seed"],
               "weights": str(d["weights"])}])
```
Phase 9 wiring: 10 MF sliders via `st.columns` (two groups of five, eT + du) — `columns` is stub-safe (returns list of stubs); each slider `st.slider(label, min, max, hand_center, step)`; reset-to-frozen button restores hand centers in memory only (no disk write); replay via `gen = st.slider("generation", 1, 50, 50, 1)` then `g, b, m = replay_slice(gen, best, mean)`.

**Overlay-plot pattern** (lines 80-96) — hand solid vs dragged dashed:
```python
for a, key in zip(axes, MF_KEYS):
    hand_c = FUZZY_MFS[key]["centers"]
    hand_w = FUZZY_MFS[key]["widths"]
    opt_c = mfs_opt[key]["centers"]
    opt_w = mfs_opt[key]["widths"]
    lo = float(min(hand_c.min(), opt_c.min()) - max(hand_w.max(), opt_w.max()))
    hi = float(max(hand_c.max(), opt_c.max()) + max(hand_w.max(), opt_w.max()))
    grid = np.linspace(lo, hi, 400)
    for c, w in zip(hand_c, hand_w):
        a.plot(grid, [tri(x, c, w) for x in grid], "C0-", alpha=0.5)
    for c, w in zip(opt_c, opt_w):
        a.plot(grid, [tri(x, c, w) for x in grid], "C1--", alpha=0.8)
```
Copy styling (`C0-` frozen vs `C1--` scratch, explicit light faces lines 76-79) for `build_explorer_figure(grid, hand_vals, scratch_vals)` — but note the figure BUILDER itself lives in `helpers.py` (audit bans `def` on this page); the page only calls it.

**Convergence-plot pattern** (lines 52-69) — template for replay marker figure:
```python
fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor("#F7FAF3")  # explicit light figure (theme never touches mpl)
ax.set_facecolor("#FFFFFF")  # explicit light axes, default C-series data colors
ax.tick_params(colors="#263023")
gens = range(1, len(best) + 1)
ax.plot(gens, best, label="best")
ax.plot(gens, mean, label="mean", alpha=0.7)
```
Replay adds `ax.axvline(gen, color="k", linestyle="--", linewidth=0.8)` + title `"GA convergence replay — gen %d/50, best %.2f"`.

---

### `tests/test_dashboard.py` (test, batch) — EXTENDED with 4 new tests

**Analog:** `tests/test_dashboard.py` existing tests

**Headless-harness pattern** (lines 26-109): `_stub_streamlit()` (stub with `cache_data` passthrough, `columns`/`slider`/`selectbox`/`download_button` emulation, `_noop → None` fallback) + `_import_helpers()` / `_import_page(fname)` (`importlib.util.spec_from_file_location`, `matplotlib Agg`, `os.chdir(ROOT)`). New tests reuse these three helpers verbatim — no new harness.

**Sim-assert pattern** (lines 153-172, `test_controllers_helper` — template for `test_scenario_delta`):
```python
mod = _import_page("02_controllers.py")
assert mod.resolve_weather(7) == "weather/weather_profile.csv"
assert mod.resolve_weather(21) == "weather/holdout_21.csv"
custom = mod.resolve_weather(33)
assert "weather/" not in custom.replace("\\", "/"), custom
t0 = time.time()
hours, runs = mod.run_all_four(25.0, 70.0, 21)
dt = time.time() - t0
assert set(runs) == {"on/off", "PID", "hand fuzzy", "GA fuzzy"}, set(runs)
for name, (T_h, RH_h, U_h) in runs.items():
    assert len(T_h) == 1440 and len(RH_h) == 1440 and len(U_h) == 1440, \
        (name, len(T_h))
assert dt < 30.0, dt
from src.metrics import all_metrics
costs = {n: all_metrics(T, RH, U)["cost"] for n, (T, RH, U) in runs.items()}
assert costs["GA fuzzy"] < costs["on/off"], costs
assert costs["GA fuzzy"] < costs["PID"], costs
```
Copy for `test_scenario_delta`: pair shape (4 controllers × 1440 per side), delta arithmetic = B−A float equality vs direct `run_all_four` + `all_metrics`, budget gate (cold pair < ~6 s, warm < 0.5 s), GA-wins rank line both sides at default seeds (A=7, B=21).

**Artifact-guard pattern** (lines 175-192, `test_explorer_helper` — template for purity/clamp/replay tests):
```python
import json
with open(os.path.join(ROOT, "results/ga_optimized_params.json")) as f:
    d = json.load(f)
assert d["schema_version"] == 2, "stale artifact: schema_version != 2"
assert len(d["history"]["best"]) == 50, len(d["history"]["best"])
from src.ga_fuzzy_controller import load_optimized_mfs
mfs, gains = load_optimized_mfs(os.path.join(ROOT, "results/ga_optimized_params.json"))
```
Copy for `test_scratch_purity` (snapshot `FUZZY_MFS` centers/widths + `mfs_opt` via `np.array_equal` pre/post-drag; widths untouched; zero-delta curve `np.allclose`; +0.5 drag max-abs deviation > 1e-3), `test_scratch_clamp` (out-of-order drag → clamped + warning + no exception), `test_replay_slice` (gen 1/25/50 → exact `history.best/mean[g-1]`, readout `gen {g}/50 · best {:.2f}`, figure title contains `gen {g}/50`).

**Audit-extension pattern** (lines 195-230, `test_source_audits` — extend word lists, do not restructure):
```python
for line in src03.splitlines():
    s = line.strip()
    assert not s.startswith("def "), (fname, s)
    assert not s.startswith("class "), (fname, s)
```
New asserts ride the existing loops: no `genetic_algorithm`/`evolve`/`run_ga` on 02/03, no `number_input`/`text_input` on 02, no `savefig`/`plt.show`/`use("Agg")`/`"w"` on any page.

---

## Shared Patterns

### Frozen-artifact read-only discipline
**Source:** `dashboard/pages/03_ga_explorer.py:31-42` (load) + `src/ga_fuzzy_controller.py:37-77` (validated loader)
**Apply to:** All new helper defs + both page wirings
```python
mfs_opt, gains_opt = load_optimized_mfs(JSON_PATH)  # fail-fast schema v2, defensive deep copies
```
Never raw-`json.load` MFs without validation; never write to `results/`/`weather/` (audited: no `"w"` opens on pages, `test_artifacts_untouched` gates every merge). Ephemeral weather goes to `tempfile.mkdtemp()`, never `weather/`.

### No-mutation guarantee (deepcopy scratch MFs)
**Source:** `src/ga_fuzzy_controller.py:49-50,77` (`copy.deepcopy` on cache hit AND return)
```python
if _MFS is not None and _MFS_PATH == apath and _MFS_MTIME == mtime:
    return copy.deepcopy(_MFS), copy.deepcopy(_GAINS)
...
return copy.deepcopy(_MFS), copy.deepcopy(_GAINS)
```
**Apply to:** `scratch_mfs_from_deltas` — `scratch = copy.deepcopy(FUZZY_MFS)` at construction (RESEARCH Pattern 2); never `FUZZY_MFS[k]["centers"][i] = …`; widths never assigned; neighbor clamp `(prev + eps, next + eps)` against already-clamped neighbors, `eps=1e-3`.

### Engine reuse (never reimplement inference)
**Source:** `src/fuzzy_controller.py:40-60` (`tri` + `infer` with edge-clip, min-implication, max-aggregation, zero-fire → 0.0)
```python
def infer(e, de, EC, EW, DC, DW, OC, OW, lo, hi, n=201):
    mu_e = np.array([tri(np.clip(e, EC[0], EC[-1]), c, w) for c, w in zip(EC, EW)])
```
**Apply to:** `tloop_response_curve` — `infer(float(e), 0.0, EC, EW, DC, DW, OC, OW, -1.0, 1.0)` over 201-point eT grid at deT=0 (~28 ms). Hand MF anchor values at `src/fuzzy_controller.py:20-29` (eT `[-4.,-2.,0.,2.,4.]` w=2.0; du `[-0.1,-0.05,0.,0.05,0.1]` w=0.05).

### Locked cost semantics
**Source:** `src/metrics.py:119-123` (`weighted_cost`, weights locked 1.0/1.0/0.01) + `src/metrics.py:155-170` (`all_metrics` bundle)
```python
def weighted_cost(iae_T, iae_H, E, w1=W1, w2=W2, w3=W3):
    """Locked cost: W1*IAE_T + W2*IAE_H + W3*E with 1.0/1.0/0.01."""
    assert (w1, w2, w3) == (1.0, 1.0, 0.01), "weights locked 1.0/1.0/0.01"
```
**Apply to:** `scenario_delta` (true Δcost via `all_metrics` — the ONLY place "cost" appears unqualified). Explorer readout reports max-abs/mean-abs curve deviation in duty units, or "surface proxy (not closed-loop cost)" — never `weighted_cost` on a sweep (Pitfall 4).

### Stub-safe widget set
**Source:** `tests/test_dashboard.py:33-77` (stub: only `cache_data`, `sidebar`, `columns`, `slider`, `selectbox`, `download_button` faithful; rest `_noop → None`)
**Apply to:** Both page wirings — restrict to `slider`, `selectbox`, `columns`, `download_button`, `metric`, `dataframe`, `warning`, `subheader`, `pyplot`. No `st.fragment` / `st.session_state` / `st.rerun` / `time.sleep` / `with st.` / `@st.` (all stub-unsafe or D-03-banned). Replay is stateless: slider value IS the generation index (`replay_slice`: `g = int(max(1, min(50, gen)))`; `return g, float(best[g-1]), float(mean[g-1])`).

### Validation / warnings-not-crashes
**Source:** `dashboard/pages/03_ga_explorer.py:35-40` (`st.error` + `st.stop()` for artifact faults) + `src/fuzzy_controller.py:65-67` (`assert np.isfinite(...)` fail-loud in engine)
```python
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen GA artifact unreadable: %s" % exc)
    st.stop()
```
**Apply to:** Scratch builder clamps + collects `warnings` list (rendered as `st.warning`, never raise); sweep guarded by `np.isfinite` check → `st.warning("…")`. Slider min/max derived from hand neighbors ± span (UX bound; helper clamp is the guarantee).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| *(none)* | — | — | Every Phase 9 change extends an existing file; RESEARCH explicitly mandates zero new files. All four modified files have exact self-analogs above. |

## Metadata

**Analog search scope:** `dashboard/helpers.py`, `dashboard/pages/02_controllers.py`, `dashboard/pages/03_ga_explorer.py`, `src/fuzzy_controller.py`, `src/metrics.py`, `src/ga_fuzzy_controller.py`, `tests/test_dashboard.py` (targeted reads per orchestrator brief + RESEARCH §Sources; no broad glob sweep needed — all analogs named in CONTEXT/RESEARCH canonical refs)
**Files scanned:** 7
**Pattern extraction date:** 2026-09-29
