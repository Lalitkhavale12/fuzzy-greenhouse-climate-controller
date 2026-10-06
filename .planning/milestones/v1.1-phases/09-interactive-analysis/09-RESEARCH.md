# Phase 9: Interactive Analysis - Research

**Researched:** 2026-09-29
**Domain:** Streamlit interactive analysis over frozen simulation artifacts (scenario A/B comparison, MF-center explorer, convergence replay)
**Confidence:** HIGH

## Summary

Phase 9 makes the dashboard interrogable without touching any science: the Controllers page gains a two-scenario side-by-side comparison (free seed sliders per side, shared setpoint sliders, ΔIAE/Δenergy/Δcost table with rank framing), and the GA Explorer page gains a T-loop MF-center drag explorer (10 sliders, scratch-vs-frozen overlay + Δcost readout, reset-to-frozen) plus a scrub-only convergence replay slider over frozen `history.best`/`history.mean`. All computation reuses `src/` kernels and the cached `run_all_four` primitive; all new `def`s live in `dashboard/helpers.py`; frozen artifacts stay untouched; zero new installs.

Two load-bearing measurements taken this session drive the whole design: one `run_all_four` call costs ~1.44 s cold (4 × 1440-step closed loops), so a two-side tick costs ~2.9 s cold and ~0 s warm (cache hits) — inside the seconds-scale budget with no new machinery needed. A 201-point `infer()` defuzz sweep costs ~28 ms — three orders of magnitude cheaper than any closed-loop probe — which settles the agent's-discretion response-curve question decisively in favor of the defuzz surface sweep.

**Primary recommendation:** Reuse the cached `run_all_four(T_sp, RH_sp, seed)` primitive verbatim per scenario side, define the explorer response curve as a stateless `infer()` sweep over eT at deT=0 (28 ms/drag, no sim, no evolution import), implement replay as a stateless slider→index into frozen history arrays (no `session_state`, no recompute), and put every new `def` in `dashboard/helpers.py` because the audit bans top-level `def` on the 03 page.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (Scenario picker):** Free seed sliders per side (1–50): seeds 7/21 resolve to the frozen CSVs, every other seed generates to an ephemeral tempfile (Controllers-page convention). Shared setpoint sliders across both sides so the comparison is apples-to-apples.
- **D-02 (MF scope):** T-loop subset draggable: eT + du centers (10 sliders) where the action is — keeps the panel usable. deT/eH/deH/dv stay frozen. Widths frozen (centers only).
- **D-03 (Replay form):** Slider scrub only over frozen `history.best`/`history.mean` (gen + best-fitness readout). No autoplay timers.
- **D-04 (Explorer compare):** Scratch-vs-frozen overlay: dragged-MF response curve overlaid on the hand-baseline curve plus a Δ cost readout — shows exactly what each drag changes. Reset-to-frozen button restores hand MFs.
- **D-05 (Cross-cutting guards):** Scratch MFs live in deep copies only (never mutate `FUZZY_MFS`/`mfs_opt`); centers clamped between neighbors, widths untouched (frozen); validity warnings instead of crashes; evolution imports banned from exhibit pages (replay reads frozen history only).

### the agent's Discretion
- Response-curve definition for the explorer (defuzz surface sweep vs closed-loop probe) within the overlay+delta requirement.
- Delta-table columns beyond ΔIAE/Δenergy/Δcost; slider granularity within the seconds-scale rerun budget.
- Widget layout (columns/expanders) for the 10 MF sliders + reset button.

### Deferred Ideas (OUT OF SCOPE)
- Autoplay animation for replay — deferred (scrub-only locked; revisit on feedback).
- All-groups MF dragging — deferred (T-loop subset locked; revisit on feedback).
- "Test scratch MFs on scenario A/B" bridge — P3 stretch, needs safety spike first.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-04 | Controllers page compares two weather scenarios side-by-side on shared sliders | Scenario-runner helper shape (cached primitive × 2, shared setpoints, per-side seeds, delta table via `all_metrics`) |
| UI-05 | GA Explorer page lets the user drag MF centers and watch the fuzzy response reshape live (deep-copied MFs, validity-clamped, frozen baseline never mutated) | Scratch-dict construction (deepcopy + neighbor clamping + width freeze) + defuzz-sweep response curve (~28 ms) + overlay/Δcost/reset helpers |
| UI-06 | GA Explorer page replays convergence generation-by-generation over frozen history (slider scrub; no live evolution) | Stateless scrubber (gen slider 1–50 → index into frozen `history.best`/`mean`, readout, marker plot; no recompute) |

## Project Constraints (from AGENTS.md)

- **Tech:** Python 3, NumPy (numerics), Streamlit (dashboard UI). Matplotlib plotting. CSV weather input, JSON GA params. No new libraries without explicit need — Phase 9 adds zero installs.
- **No duplicated logic:** notebooks/pages call into `src/`; explorer response curve reuses `tri`/`infer`, never reimplements membership math.
- **Order:** dashboards last — `src/`, `results/`, `weather/` are read-only inputs; helpers import readers/kernels only.
- **GSD workflow:** implement via `/gsd-execute-phase`; atomic `scope(phase-plan):` commits per plan.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Scenario closed-loop sims | Helpers (compute) | Pages (wiring) | `run_closed_loop`/`all_metrics` are pure NumPy; pages only pass slider values and render |
| Delta table values | Helpers (compute) | — | Pure function of two `run_all_four` outputs; headless-assertable with no Streamlit |
| MF scratch construction | Helpers (compute) | — | deepcopy + clamp is pure dict/array work; testable without widgets |
| Response curve | Helpers (compute) | Pages (render) | `infer()` sweep returns arrays; page only plots |
| Replay slicing | Helpers (compute) | Pages (wiring) | Index into frozen arrays; no state machine needed |
| Widget layout | Pages (thin wiring) | — | `columns`/`slider`/`selectbox`/`download_button` only; zero `def`s on 03 page |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Streamlit | 1.56.0 [VERIFIED: `python -c "import streamlit"` → 1.56.0 this session] | Scenario sliders, MF sliders, replay slider, overlay plots, delta table | Installed ceiling; all needed widgets (`slider`, `columns`, `selectbox`, `download_button`, `metric`, `dataframe`, `cache_data`) already used on 02/03 pages [VERIFIED: dashboard/pages/02_controllers.py:48,69-71, dashboard/pages/03_ga_explorer.py:44-50] |
| NumPy | 2.4.3 [VERIFIED: import probe this session] | `infer()` sweeps, history slicing, metric arithmetic | Existing `src/` kernel dependency; zero new API surface |
| Matplotlib | 3.10.8 [VERIFIED: import probe this session] | Overlay curve figure, replay marker figure, explicit light-figure colors | Existing page pattern (`fig.patch`/`ax` facecolor + `fig_to_png_bytes`); theme never touches mpl |
| pandas | 3.0.1 [VERIFIED: import probe this session] | Delta table formatting (or plain `st.dataframe` over list-of-dicts as 03 already does) | Already installed; 03 page precedent uses `st.dataframe([...])` [VERIFIED: dashboard/pages/03_ga_explorer.py:48-50] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `copy` | builtin | `copy.deepcopy` scratch MFs | Every scratch construction — the D-05 no-mutation guarantee |
| stdlib `tempfile` + `src.weather_profile_generator.generate_weather_profile` | builtin / in-repo | Ephemeral weather for non-frozen seeds | Reuse `resolve_weather` verbatim per side [VERIFIED: dashboard/pages/02_controllers.py:36-44] |
| `src.metrics.all_metrics` / `weighted_cost` | in-repo | Per-side IAE/energy/cost for the delta table | Delta table derivation; weights locked 1.0/1.0/0.01 [VERIFIED: src/metrics.py:30,119-123] |
| `src.ga_fuzzy_controller.load_optimized_mfs` | in-repo | Frozen `mfs_opt` baseline reference (read-only) | Explorer frozen side of the overlay; returns defensive deep copies [VERIFIED: src/ga_fuzzy_controller.py:37-77] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Defuzz surface sweep | Closed-loop probe (`run_closed_loop` with scratch mfs per drag) | Probe costs ~0.5–1.4 s per drag tick (measured fuzzy 0.54 s + GA 0.8 s single-controller legs this session), kills the "bend in real time" moment, needs a scratch-`mfs` controller-step path that does not exist, and drags the page toward the banned `genetic_algorithm` import. Rejected — and "test scratch MFs on scenarios" is explicitly deferred P3. |
| `st.session_state` replay machine | Stateless slider→index scrubber | `session_state` under the headless stub resolves to a `_noop` function object, not a dict — `st.session_state.replay_gen` read/write breaks the import-smoke test [VERIFIED: tests/test_dashboard.py:33-77]. Stateless slider value *is* the generation index; zero state bugs, zero stub risk. Use stateless. |
| `st.fragment` isolation per side | Plain `@st.cache_data` (existing) | `fragment` is an unknown stub attr → `_noop` → decorator returns `None` → page import fails headless [VERIFIED: tests/test_dashboard.py:70-72]. The existing `cache_data` keyed `(T_sp, RH_sp, seed)` already makes cross-side recompute free. Do not use `fragment`. |

**Installation:** none — zero new installs (locked).

**Version verification:** `python -c "import streamlit"` → 1.56.0; `python --version` → 3.14.6; numpy/matplotlib/pandas → 2.4.3/3.10.8/3.0.1. All probed this session via the conda `python`. Never reference bare `python3` — it lacks streamlit in this environment [ASSUMED — environment quirk reported in phase brief, not re-probed this session].

## Package Legitimacy Audit

No external packages installed in this phase. All computation uses the installed environment (Streamlit/NumPy/Matplotlib/pandas) plus in-repo `src/` modules and stdlib. Audit table not applicable — nothing to gate.

**Packages removed due to SLOP verdict:** none.
**Packages flagged as suspicious (SUS):** none.

## Architecture Patterns

### System Architecture Diagram

```
sliders (02: shared T_sp/RH_sp + seed_A + seed_B)
  │  (thin page wiring, no defs on 03; resolve_weather per side)
  ▼
run_all_four(T_sp, RH_sp, seed) × 2  [@st.cache_data, helpers or 02-cached]
  │  4 × 1440-step run_closed_loop on shared weather per side (~1.44 s cold, ~0 s warm)
  ▼
all_metrics(T,RH,U) per controller per side  [helpers, pure]
  │  iae_T / iae_H / energy / cost (locked weights)
  ▼
delta table ΔIAE_T / ΔIAE_H / Δenergy / Δcost + "does GA still win both sides?" rank line
  + paired trace figure (one combined fig, explicit light colors)

MF sliders (03: 10 × eT/du centers) ──► scratch_mfs = deepcopy(hand) + deltas, neighbor-clamped
  │  widths frozen, validity warnings (never crash)
  ▼
response_curve(scratch) vs response_curve(hand)  [infer() sweep, ~28 ms]
  │  overlaid on one axes + Δcost readout (weighted_cost on sweep proxy — see Pitfall 4)
  ▼
reset-to-frozen button ──► sliders restore hand centers (stateless: key reset / value restore)

gen slider 1..50 ──► history.best[g-1], history.mean[g-1]  [frozen JSON, no recompute]
  │  readout: "gen {g}/50 · best {best:.2f}" + convergence fig with gen marker
  ▼
render only; genetic_algorithm / evolve / run_ga NEVER imported on 02/03
```

### Recommended Project Structure

No new files. All new `def`s in the existing module (audit-forced):

```
dashboard/
├── helpers.py          # ALL new defs: scenario_pair, scenario_delta_table,
│                       #   scratch_mfs_from_deltas, clamp_centers,
│                       #   tloop_response_curve, replay_slice (+ fig builders)
└── pages/
    ├── 02_controllers.py  # MODIFIED: shared setpoints + seed_A/seed_B + delta table wiring
    └── 03_ga_explorer.py  # MODIFIED: 10 sliders + overlay + reset + replay wiring, zero new defs
src/ results/ weather/  # UNTOUCHED, read-only
tests/test_dashboard.py # EXTENDED: helper-level asserts (same commit as helpers)
```

### Pattern 1: Scenario-pair runner (one cached primitive, called twice)

**What:** Keep `run_all_four(T_sp, RH_sp, seed)` as the *only* simulation entry point. The pair helper calls it twice with different seeds and derives metrics per side with `all_metrics`. Shared setpoint sliders guarantee apples-to-apples; per-side seed sliders (1–50) resolve via the existing `resolve_weather` (7/21 frozen, rest ephemeral tempfile).
**When to use:** UI-04 implementation, in `dashboard/helpers.py`.
**Example:**
```python
# Source: dashboard/pages/02_controllers.py:36-65 (existing primitive, reused verbatim shape)
def resolve_weather(seed):
    """Frozen files for seeds 7/21, ephemeral tempfile paths otherwise."""
    if seed == 7:
        return "weather/weather_profile.csv"
    if seed == 21:
        return "weather/holdout_21.csv"
    path = os.path.join(tempfile.mkdtemp(), "seed_%d.csv" % seed)
    generate_weather_profile(path, seed=seed)
    return path

# New in helpers.py (pure, headless-testable; cache decorator lives at call site
# or on a thin wrapper — stub-safe because cache_data passthrough is verified
# [VERIFIED: tests/test_dashboard.py:36-43]):
def scenario_delta(side_a, side_b):
    """side = (T_hist, RH_hist, U_hist) per controller -> delta-row dicts.

    side_a/side_b: dict name -> (T_h, RH_h, U_h) as run_all_four returns.
    Returns list of {controller, d_iae_T, d_iae_H, d_energy, d_cost} with
    (B - A) sign convention, plus per-side cost dicts for the rank line.
    """
    from src.metrics import all_metrics
    rows = []
    for name in ("on/off", "PID", "hand fuzzy", "GA fuzzy"):
        ma = all_metrics(*side_a[name][:3])  # (T_h, RH_h, U_h); setpoints shared
        mb = all_metrics(*side_b[name][:3])
        rows.append({"controller": name,
                     "d_iae_T": mb["iae_T"] - ma["iae_T"],
                     "d_iae_H": mb["iae_H"] - ma["iae_H"],
                     "d_energy": mb["energy"] - ma["energy"],
                     "d_cost": mb["cost"] - ma["cost"]})
    return rows
```
Tick budget (measured this session): single side 1.44 s cold (onoff 0.06 + PID 0.04 + fuzzy 0.54 + GA 0.80 s); two-side cold tick ≈ 2.9 s — inside the seconds-scale budget; warm ticks are cache hits (~0 s). Slider granularity stays at the existing steps (T 0.5 °C, RH 1 %, seed int 1) [VERIFIED: dashboard/pages/02_controllers.py:69-71] — no finer granularity needed, coarser only if a cold tick ever exceeds ~5 s.

### Pattern 2: Scratch-MF construction (deepcopy + deltas + neighbor clamping)

**What:** Scratch dicts start as `copy.deepcopy(FUZZY_MFS)` (hand baseline — the D-04 overlay compares dragged response against the *hand* curve, and reset restores hand). Ten slider values overwrite `eT` (5) + `du` (5) centers only. Each center is clamped to `(prev + eps, next + eps)` with a small eps (1e-6 relative or 1e-3 absolute); widths are never touched; ordering violations produce `st.warning`, never an exception.
**When to use:** UI-05 implementation, in `dashboard/helpers.py`.
**Example:**
```python
# Source: src/fuzzy_controller.py:20-29 hand MF values (read-only convention, line 12-13)
#   "eT":  {"centers": np.array([-4., -2., 0., 2., 4.]),       "widths": np.full(5, 2.0)},
#   "du":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},
import copy
import numpy as np
from src.fuzzy_controller import FUZZY_MFS

DRAG_GROUPS = ("eT", "du")  # 5 + 5 = 10 sliders; deT/eH/deH/dv frozen per D-02

def scratch_mfs_from_deltas(eT_centers, du_centers, eps=1e-3):
    """Deep-copied hand MFs with dragged centers, neighbor-clamped.

    Returns (scratch_dict, warnings:list[str]). FUZZY_MFS untouched.
    Widths frozen — never assigned here.
    """
    scratch = copy.deepcopy(FUZZY_MFS)
    warnings = []
    for key, vals in (("eT", eT_centers), ("du", du_centers)):
        vals = [float(v) for v in vals]
        clamped = []
        for i, v in enumerate(vals):
            lo = vals[i - 1] + eps if i > 0 else -np.inf  # neighbor clamp
            hi = vals[i + 1] - eps if i < 4 else np.inf
            # clamp against already-clamped neighbors so ordering is guaranteed
            lo = clamped[-1] + eps if i > 0 else lo
            c = min(max(v, lo), hi)
            if c != v:
                warnings.append("%s[%d] clamped to %.4g (neighbor bound)" % (key, i, c))
            clamped.append(c)
        scratch[key]["centers"] = np.array(clamped, dtype=float)
    return scratch, warnings
```

### Pattern 3: Response curve — defuzz surface sweep (RECOMMENDED, settles agent's discretion)

**What:** `du = infer(eT, deT=0, ...)` swept over a fixed eT grid (201 points, ~28 ms measured this session). Overlay: hand curve (solid) + scratch curve (dashed) on one axes, same before/after styling the page already uses (`C0-` hand vs `C1--` GA [VERIFIED: dashboard/pages/03_ga_explorer.py:88-93]). Δ readout: recompute both sweeps and report a cheap scalar — max-abs deviation plus the `weighted_cost` *of the sweep proxy is NOT a true closed-loop cost*, so label it honestly (see Pitfall 4).
**When to use:** UI-05 live reshape; every slider tick.
**Example:**
```python
# Source: src/fuzzy_controller.py:45-60 (infer signature + centroid core)
def tloop_response_curve(mfs, n=201, lo=-5.0, hi=5.0):
    """T-loop defuzz surface slice: du over eT grid at deT=0. Pure, ~28 ms."""
    from src.fuzzy_controller import infer
    grid = np.linspace(lo, hi, n)
    EC, EW = mfs["eT"]["centers"], mfs["eT"]["widths"]
    DC, DW = mfs["deT"]["centers"], mfs["deT"]["widths"]
    OC, OW = mfs["du"]["centers"], mfs["du"]["widths"]
    vals = np.array([infer(float(e), 0.0, EC, EW, DC, DW, OC, OW, -1.0, 1.0)
                     for e in grid])
    return grid, vals
```
Why not the closed-loop probe: ~0.5–1.4 s per drag tick destroys the "watch the curve bend in real time" moment (CONTEXT specifics), needs a scratch-`mfs` step path that does not exist in `metrics.run_closed_loop` (its `controller_step` signature takes no `mfs` arg [VERIFIED: src/metrics.py:126-152]), and pulls the page toward the banned `genetic_algorithm` import. The deferred P3 bridge covers closed-loop testing later with its own safety spike.

### Pattern 4: Replay scrubber (stateless slider → frozen index)

**What:** `gen = st.slider("generation", 1, 50, 50, 1)`; `best, mean, g = replay_slice(gen)` indexes the frozen arrays; readout line + convergence figure with a vertical marker at `gen`. No recompute, no evolution import, no `session_state`.
**When to use:** UI-06 implementation, split helper (pure) + page (slider + marker plot).
**Example:**
```python
# Source: results/ga_optimized_params.json schema v2 + 50-len history
# [VERIFIED this session: hist lens 50/50; page asserts schema_version==2,
#  dashboard/pages/03_ga_explorer.py:38-42]
def replay_slice(gen, history_best, history_mean):
    """1-based gen -> (gen, best_val, mean_val). Pure indexing, no recompute."""
    g = int(max(1, min(50, gen)))
    return g, float(history_best[g - 1]), float(history_mean[g - 1])
```

### Anti-Patterns to Avoid
- **New `run_closed_loop` call sites outside the cached primitive:** doubles uncached work and trips the "never recompute" audits. Always go through `run_all_four(T_sp, RH_sp, seed)` × 2.
- **Top-level `def`/`class` on 03 page:** the audit fails any line starting with `def `/`class ` on 03 [VERIFIED: tests/test_dashboard.py:219-223]. All helpers in `dashboard/helpers.py`.
- **`savefig`/`plt.show`/`use("Agg")`/absolute paths/`"w"` opens on any page:** all banned by `test_source_audits` [VERIFIED: tests/test_dashboard.py:195-230]. Figures serialize via `fig_to_png_bytes` in helpers.
- **`number_input`/`text_input` on 02:** banned ("sliders only drive the loop") [VERIFIED: tests/test_dashboard.py:214-215]. Seeds are `st.slider(1, 50)`; nothing else.
- **`st.fragment` / `st.session_state` / `st.rerun` / `time.sleep` autoplay:** stub-unsafe (`_noop` returns `None`) and D-03 bans autoplay. Stateless sliders only.
- **In-place MF edits (`FUZZY_MFS[k]["centers"][i] = …`):** corrupts every page for the whole session (module-global). Deepcopy always; assert `np.array_equal(FUZZY_MFS[k]["centers"], HAND_SNAPSHOT)` in tests after drags.
- **Importing `genetic_algorithm`, `evolve`, `run_ga`, `train(`, `fit(` on 02/03:** banned by source audits [VERIFIED: tests/test_dashboard.py:187-191,216-218]. Replay reads the frozen JSON only.
- **Regenerating seeds 7/21:** `resolve_weather` maps them to frozen CSVs; never call `generate_weather_profile` for those seeds (frozen-seed regeneration breaks provenance).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Membership evaluation | Custom triangle/centroid code | `tri` + `infer` from `src.fuzzy_controller` [VERIFIED: src/fuzzy_controller.py:40-60] | Edge-MF saturation via input clipping, zero-fire 0.0 fallback, and the shared RULES table are subtle; duplicates drift from the engine the GA actually tuned |
| Weighted cost | Custom cost formula | `weighted_cost` / `all_metrics` from `src.metrics` (weights locked 1.0/1.0/0.01) | Any retyped weight breaks METR-02 comparability; `all_metrics` bundles all six metrics + cost in one call [VERIFIED: src/metrics.py:119-123,155-170] |
| Frozen MF loading | Raw `json.load` + hand-rolled validation | `load_optimized_mfs` (fail-fast schema v2, defensive deep copies) | Len-5/finite/widths>0/coupling-bounds checks already encoded; returns copies so callers cannot mutate the cache [VERIFIED: src/ga_fuzzy_controller.py:37-77] |
| PNG download bytes | Custom buffer code | `fig_to_png_bytes` in helpers (savefig→BytesIO→seek(0), never closes) | The seek(0)-or-empty-download and never-close-so-`st.pyplot`-still-works subtleties are already handled [VERIFIED: dashboard/helpers.py:109-114] |
| Optimizer / evolution | Any live GA in the dashboard | Frozen `history.best`/`mean` arrays (len 50 each, measured this session) | Live evolution takes minutes and risks JSON overwrite; replay is pure slicing |

**Key insight:** Phase 9 is pure composition — cached sims, engine kernels, frozen arrays, and byte builders that already exist. Every custom reimplementation either breaks an audit, drifts from the tuned engine, or reintroduces a pitfall the v1.1 research already solved.

## Common Pitfalls

### Pitfall 1: Two-side tick blows the seconds-scale budget
**What goes wrong:** Cold two-side tick feels sluggish; devs add coarser sliders or background threads.
**Why it happens:** 8 × 1440-step loops per tick (~2.9 s cold measured). Warm ticks are free (cache), but first paint and seed changes pay full price.
**How to avoid:** Keep the ONE cached primitive called twice (cache keyed on args — changing side B never recomputes side A); one combined figure, not 8 `st.pyplot` calls; keep existing slider granularity; budget-gate in tests (cold pair < ~6 s, warm < 0.5 s).
**Warning signs:** New uncached `run_closed_loop` call sites; per-side figures multiplying; tick latency complaints on first paint only (that's the cold cache — expected, not a bug).

### Pitfall 2: Scratch drags mutate the frozen baseline
**What goes wrong:** Dragging eT centers on the explorer shifts curves on the Controllers page too — the module-global `FUZZY_MFS` was edited in place.
**Why it happens:** `scratch = FUZZY_MFS` (alias, not copy) or `scratch[k]["centers"] = slider_array` where the array is a view; `np` views share memory silently.
**How to avoid:** `copy.deepcopy` at construction; never assign into `FUZZY_MFS` or `mfs_opt`; headless bit-identity test (`np.array_equal` against pre-drag snapshot) after simulated drags; also assert `mfs_opt` (loaded via the deepcopy-returning loader) is unaffected.
**Warning signs:** Any `FUZZY_MFS[...][...] =` or `mfs_opt[...][...] =` line outside tests; missing `copy` import in helpers.

### Pitfall 3: Invalid fuzzy sets — unordered centers, zero widths, NaN curves
**What goes wrong:** A dragged center crosses its neighbor → overlapping/inverted triangles → `infer()` returns garbage or flat 0.0; page shows a dead curve with no explanation.
**Why it happens:** Raw slider values written straight into centers with no ordering enforcement.
**How to avoid:** Neighbor clamping (`c[i-1]+eps`, `c[i+1]-eps` against already-clamped neighbors) in the helper; widths frozen (never exposed); `np.isfinite` check on the sweep with `st.warning("…")` instead of raising; slider min/max bounds derived from hand neighbors ± range so gross violations are unreachable.
**Warning signs:** Sweep returns all-zeros or NaN; no `warnings` list in the scratch-builder signature; `try/except: st.stop()` around slider code (warnings-not-crashes per D-05).

### Pitfall 4: Δcost readout mislabeled — sweep proxy vs true closed-loop cost
**What goes wrong:** Explorer shows "Δcost: −3.2" computed from the response-curve sweep, and readers (or the planner) mistake it for the locked weighted-cost victory margin.
**Why it happens:** The defuzz sweep has no IAE/energy semantics — it is a control-surface slice, not a simulation. Any scalar derived from it is a *shape-change indicator*, not METR-02 cost.
**How to avoid:** Label honestly: report max-abs curve deviation (duty units) as the primary "what changed" scalar, plus optionally the mean-abs deviation; if a cost-like number is shown, prefix it "surface proxy (not closed-loop cost)". The true Δcost readout belongs to the scenario delta table (UI-04), which uses real `all_metrics`. Tests assert the explorer readout function never calls `run_closed_loop`/`all_metrics`.
**Warning signs:** `weighted_cost(` imported into explorer helpers; "cost" shown next to a response curve without the word "proxy".

### Pitfall 5: New widgets break the headless import-smoke suite
**What goes wrong:** Page uses `st.fragment`, `st.session_state`, `st.rerun`, `st.tabs`, or `st.expander` in a way the stub does not emulate → import fails or returns `None` where a value is needed.
**Why it happens:** The stub only emulates `cache_data`, `sidebar`, `columns`, `slider`, `selectbox`, `download_button` faithfully; everything else is `_noop → None` [VERIFIED: tests/test_dashboard.py:33-77]. `tabs`/`expander` as bare calls are fine (return ignored); as context managers or decorators they are not.
**How to avoid:** Restrict Phase 9 widgets to the stub-safe set: `slider`, `selectbox`, `columns`, `download_button`, `metric`, `dataframe`, `warning`, `subheader`, `pyplot`. Use `columns` for the 10-slider layout (two groups of five) — no tabs/expanders needed. If tabs/expanders are wanted, extend the stub in the SAME commit (established Phase 8 precedent per v1.1 research).
**Warning signs:** `with st.` or `@st.` decorators on pages; `st.session_state.` attribute access; CI import-smoke failure immediately after adding a widget.

### Pitfall 6: Frozen artifacts get dirtied during interactive work
**What goes wrong:** `results/` or `weather/` shows as modified after click-through — provenance destroyed.
**Why it happens:** Ephemeral weather written into `weather/` instead of `tempfile.mkdtemp()`; JSON "reset" writing back to `results/`; `compare(` called from page code.
**How to avoid:** Reuse `resolve_weather` verbatim (non-frozen seeds → `tempfile.mkdtemp()` paths, never `weather/`) [VERIFIED: dashboard/pages/02_controllers.py:36-44]; reset-to-frozen restores *slider values in memory only*; `test_artifacts_untouched` runs after every change [VERIFIED: tests/test_dashboard.py:233-239].
**Warning signs:** `"w"` in any page source; `generate_weather_profile(` lines referencing `weather/`; `git status results/ weather/` non-clean.

## Code Examples

### Scenario pair + delta table (helpers, pure)

```python
# Source: src/metrics.py:155-170 (all_metrics) + 02_controllers.py:47-65 (primitive shape)
def run_scenario_pair(T_sp, RH_sp, seed_a, seed_b, runner):
    """runner = cached run_all_four. Returns (runs_a, runs_b, delta_rows)."""
    _, runs_a = runner(T_sp, RH_sp, seed_a)
    _, runs_b = runner(T_sp, RH_sp, seed_b)
    return runs_a, runs_b, scenario_delta(runs_a, runs_b)
# Page renders delta_rows via st.dataframe + rank line:
# "GA still wins: side A rank {ra} / side B rank {rb}" (rank framing per CONTEXT specifics)
```

### Explorer overlay figure (helpers builds, page shows + downloads)

```python
# Source: 03_ga_explorer.py:71-102 (before/after styling precedent: C0- hand vs C1-- GA)
def build_explorer_figure(grid, hand_vals, scratch_vals):
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#F7FAF3")
    ax.set_facecolor("#FFFFFF")
    ax.tick_params(colors="#263023")
    ax.plot(grid, hand_vals, "C0-", label="frozen hand response")
    ax.plot(grid, scratch_vals, "C1--", label="scratch (dragged)")
    ax.set_xlabel("eT (degC)")
    ax.set_ylabel("du (duty/step)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig  # page: st.download_button(fig_to_png_bytes(fig)) + st.pyplot(fig)
```

### Replay figure with generation marker (helpers builds)

```python
# Source: 03_ga_explorer.py:52-69 (convergence plot precedent)
def build_replay_figure(best, mean, gen):
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#F7FAF3")
    ax.set_facecolor("#FFFFFF")
    ax.tick_params(colors="#263023")
    gens = range(1, len(best) + 1)
    ax.plot(gens, best, label="best")
    ax.plot(gens, mean, label="mean", alpha=0.7)
    ax.axvline(gen, color="k", linestyle="--", linewidth=0.8)
    ax.set_xlabel("generation")
    ax.set_ylabel("train weighted cost")
    ax.set_title("GA convergence replay — gen %d/50, best %.2f" % (gen, best[gen - 1]))
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-scenario Controllers page (seed slider 1–50, default 21) | Two-side pair on shared setpoints with delta table | This phase (UI-04) | Examiner Q1 ("does GA still win on different weather?") answered without notebooks |
| Static MF before/after plot (hand vs GA, frozen) | Draggable scratch overlay (hand vs dragged) + reset | This phase (UI-05) | Demo moment: live cause→effect on the control surface |
| Full 50-gen convergence plot | Scrub-only replay slider + gen marker + readout | This phase (UI-06) | Storytelling: convergence as an interrogable moment, zero recompute |

**Deprecated/outdated:**
- `st.experimental_*` APIs: long removed; use `st.cache_data` (already the page pattern).
- Autoplay via `time.sleep` loops: banned by D-03 scrub-only lock; revisit only on user feedback.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Bare `python3` lacks streamlit (use conda `python`); reported in phase brief, not re-probed | Standard Stack | Low — planner gates commands on `python`, suite runs under `python` already |
| A2 | 10-slider `columns` layout (two groups of five) fits without tabs/expanders | Architecture Patterns | Low — layout is the agent's discretion; columns are stub-safe, fallback is selectbox group picker (already stub-safe) |
| A3 | Cold two-side tick ~2.9 s stays acceptable; no fragment isolation needed | Pattern 1 / Pitfall 1 | Medium — if user hardware is slower, planner adds coarser setpoint steps or a "run comparison" gate; warm ticks unaffected |

## Open Questions

1. **Delta-table extra columns (the agent's discretion)**
   - What we know: ΔIAE_T/ΔIAE_H/Δenergy/Δcost required; rank framing requested ("does GA still win?").
   - What's unclear: whether per-side absolute costs add value beyond deltas.
   - Recommendation: deltas + per-side GA cost + rank line ("GA rank #N side A / #M side B"); skip RMSE/ISE/settling (METR-02 verdict needs cost only).

2. **MF slider ranges**
   - What we know: hand eT centers `[-4., -2., 0., 2., 4.]`, du centers `[-0.1, -0.05, 0., 0.05, 0.1]` [VERIFIED: src/fuzzy_controller.py:22-24, read this session]; neighbor clamping enforced in helper.
   - What's unclear: exact slider min/max/step per center.
   - Recommendation: per-center range = hand neighbor midpoint ± span (step 0.1 eT / 0.005 du), clamped in helper regardless; planner need not over-specify — helper clamp is the guarantee, slider bounds are UX.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| conda `python` + Streamlit | All UI | ✓ [VERIFIED: probe this session] | 3.14.6 / 1.56.0 | — |
| NumPy / Matplotlib / pandas | Sweeps, figs, tables | ✓ [VERIFIED: probe this session] | 2.4.3 / 3.10.8 / 3.0.1 | — |
| `weather/weather_profile.csv`, `weather/holdout_21.csv` | Frozen seeds 7/21 | ✓ [VERIFIED: `resolve_weather` asserts + suite green this session] | — | — |
| `results/ga_optimized_params.json` schema v2, history len 50 | Replay + frozen baseline | ✓ [VERIFIED: probe this session, 50/50] | — | — |
| `tests/test_dashboard.py` green baseline | Merge gate | ✓ [VERIFIED: ran this session, all checks passed] | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none — zero new installs by design.

## Validation Architecture

Test framework: standalone plain-assert suite `tests/test_dashboard.py` (pytest-compatible `test_*` names, Streamlit stubbed in `sys.modules`, `matplotlib Agg` headless; runner prints PASS/FAIL, `sys.exit(1)` on failure). No config file. Quick run: `python tests/test_dashboard.py` (~30 s including the 1440-step sim asserts). Full suite: same command (single suite) + `git status --porcelain results/ weather/` clean (artifacts-untouched guard is a test inside the suite [VERIFIED: tests/test_dashboard.py:233-239]).

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-04 | Pair runner returns 4 controllers × 1440 steps per side; delta rows = B−A for iae_T/iae_H/energy/cost; shared-setpoint rank line correct | unit (helper-level, headless) | `python tests/test_dashboard.py::test_scenario_delta` (new) | ❌ Wave 0 |
| UI-04 | Cold pair tick < ~6 s, warm (cache-hit) recompute < 0.5 s | performance budget | timing asserts inside `test_scenario_delta` | ❌ Wave 0 |
| UI-05 | Scratch builder deep-copies: `FUZZY_MFS` + `mfs_opt` bit-identical after drags; widths untouched; centers ordered | unit (no-mutation guard) | `python tests/test_dashboard.py::test_scratch_purity` (new) | ❌ Wave 0 |
| UI-05 | Overlay curves differ on drag (max-abs deviation > 0 for a nonzero delta) and coincide at zero delta | unit | asserts inside `test_scratch_purity` or `test_explorer_curve` (new) | ❌ Wave 0 |
| UI-05 | Out-of-order drag clamped, warning emitted, no exception | unit | `python tests/test_dashboard.py::test_scratch_clamp` (new) | ❌ Wave 0 |
| UI-06 | Replay indexing: gen 1/25/50 → exact `history.best/mean[g-1]`; readout format `gen {g}/50 · best {:.2f}` | unit | `python tests/test_dashboard.py::test_replay_slice` (new) | ❌ Wave 0 |
| UI-04/05/06 | Source audits hold: no new `def` on 03, no savefig/show/Agg/abs-paths/`"w"` on pages, no `genetic_algorithm`/`evolve`/`run_ga` on 02/03, no `compare(`/`number_input`/`text_input` on 02 | static audit (existing test, extended word lists if needed) | `python tests/test_dashboard.py::test_source_audits` (existing) | ✅ |
| UI-04/05/06 | Pages import under stubbed Streamlit; `results/`+`weather/` untouched | smoke + artifact guard (existing) | `python tests/test_dashboard.py::test_pages_import`, `test_artifacts_untouched` (existing) | ✅ |

### Sampling Rate
- **Per task commit:** `python tests/test_dashboard.py`
- **Per wave merge:** `python tests/test_dashboard.py` + `git status --porcelain results/ weather/` (must show only `??` untracked, never tracked modifications)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_dashboard.py::test_scenario_delta` — covers UI-04 (pair shape, delta arithmetic, budget gate, GA-wins rank line both sides at default seeds)
- [ ] `tests/test_dashboard.py::test_scratch_purity` — covers UI-05 (deepcopy bit-identity, widths frozen, overlay differs-on-drag / coincides-at-zero)
- [ ] `tests/test_dashboard.py::test_scratch_clamp` — covers UI-05 (neighbor clamping + warnings-not-crashes; may fold into purity test)
- [ ] `tests/test_dashboard.py::test_replay_slice` — covers UI-06 (frozen indexing 1/25/50, readout format, no-evolution-import assertion already covered by existing audit)
- [ ] Stub extension — only if a non-stub-safe widget is chosen (recommendation avoids this; no gap by default)

*(Existing test infrastructure — stub, Agg headless, audit helpers — covers everything else; no framework install needed.)*

**Concrete pass criteria (for the planner's verification steps):**
1. `python tests/test_dashboard.py` → `all checks passed` (exit 0).
2. Delta table spot-check: at default seeds (A=7, B=21, T_sp=25.0, RH_sp=70) the helper's per-side costs reproduce `run_all_four` + `all_metrics` values to float equality, and GA cost < on/off AND < PID on both sides (matches the frozen-verdict direction the suite already asserts for seed 21 [VERIFIED: tests/test_dashboard.py:168-171]).
3. Overlay check: zero-delta scratch curve `np.allclose` hand curve; a +0.5 eT-center drag yields max-abs deviation > 1e-3 duty units (proves the drag path is live end-to-end).
4. Frozen-baseline check: `FUZZY_MFS` centers/widths and `load_optimized_mfs` outputs `np.array_equal` pre/post-drag snapshots.
5. Replay check: `replay_slice(1/25/50)` equals `history.best/mean[g-1]` exactly; figure title contains `gen {g}/50`.
6. `git status --porcelain results/ weather/` shows no tracked modifications after full click-through.

## Security Domain

`security_enforcement: true`, ASVS level 1 (`security_block_on: high`) per `.planning/config.json` [VERIFIED: .planning/config.json:47-50, read this session]. No auth/session/crypto surface — dashboard is a local analytical app. Applicable slice:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local Streamlit, no users |
| V3 Session Management | no | Stateless sliders only (no `session_state` by design) |
| V4 Access Control | no | Single-user local app |
| V5 Input Validation | **yes** | Slider-bound numeric inputs (see below); helper-level clamping + finiteness checks |
| V6 Cryptography | no | No secrets, no transport |
| V14 Configuration | partial | No new deps; frozen paths hardcoded; in-memory only (no disk writes from UI) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Slider float → code injection / path traversal | Tampering | Seeds are `int` sliders 1–50; `resolve_weather` maps to two hardcoded frozen paths or `tempfile.mkdtemp()` — user input never becomes a path [VERIFIED: dashboard/pages/02_controllers.py:36-44]. No `text_input`/`number_input` on 02 (audit-banned). |
| Out-of-range centers → engine garbage / crash | Denial of service (local) | Neighbor clamping + widths>0 invariant (widths frozen) + `np.isfinite` sweep check → `st.warning`, never raise (D-05 warnings-not-crashes). |
| Baseline mutation across pages | Tampering (integrity) | `copy.deepcopy` scratch dicts; no-mutation headless guard; `load_optimized_mfs` already returns defensive copies [VERIFIED: src/ga_fuzzy_controller.py:50,77]. |
| Frozen-artifact overwrite | Tampering (integrity) | In-memory only; no `"w"` opens on pages (audited); ephemeral weather to tempfiles; `test_artifacts_untouched` gate. |
| Supply-chain via new deps | Tampering | Zero new installs locked — nothing to audit; `genetic_algorithm` import banned on exhibit pages removes the heaviest-footgun module from UI reach. |

## Sources

### Primary (HIGH confidence)
- Direct code reads this session: `dashboard/pages/02_controllers.py` (primitive + tempfile pattern), `dashboard/pages/03_ga_explorer.py` (JSON + overlay + convergence precedent), `dashboard/helpers.py` (helpers-only-defs + `fig_to_png_bytes` + `_paint_light`), `src/fuzzy_controller.py:20-29` (hand MF values) + `:45-60` (`infer` core), `src/metrics.py:30,119-170` (locked weights, `all_metrics`, `run_closed_loop`), `src/ga_fuzzy_controller.py:37-77` (validated loader, deep-copy cache), `src/genetic_algorithm.py:133-188` (`apply_coupling`, `coupled_fuzzy_step(mfs, gains)`, `closed_loop_breakdown`), `tests/test_dashboard.py` (stub shape, audit word lists, budget + rank asserts), `.planning/config.json` (nyquist + security enforcement on)
- Live measurements this session: `run_all_four` ≈ 1.44 s/side (legs 0.06/0.04/0.54/0.80 s); 201-point `infer()` sweep ≈ 28 ms; history lens 50/50; Streamlit 1.56.0 / Python 3.14.6 / NumPy 2.4.3 / Matplotlib 3.10.8 / pandas 3.0.1; suite green (`all checks passed`)
- `.planning/research/SUMMARY.md` + `PITFALLS.md` (v1.1 milestone research — cached primitives, MF validity discipline, replay constraints; built on, not re-researched)

### Secondary (MEDIUM confidence)
- None needed — every load-bearing claim is grounded in repo reads or live probes above.

### Tertiary (LOW confidence)
- None — no finding rests on a single unverified source.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — installed-env probes + page-import precedent, all this session.
- Architecture: HIGH — helper shapes derived from existing tested code + measured budgets; response-curve choice decided by a 50× cost measurement, not opinion.
- Pitfalls: HIGH — each maps to a named audit assertion or a measured number; stub-hazard pitfalls verified against the stub source.

**Research date:** 2026-09-29
**Valid until:** 30 days (stable domain — frozen artifacts, pinned Streamlit, no external APIs)
