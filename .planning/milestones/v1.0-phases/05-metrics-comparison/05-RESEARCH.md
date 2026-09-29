# Phase 5: Metrics & Comparison - Research

**Researched:** 2026-09-27
**Domain:** Closed-loop control performance metrics + scoreboard harness (NumPy-only, stdlib CSV)
**Confidence:** HIGH

## Summary

Phase 5 is a small, fully-local, pure-computation phase: add `src/metrics.py` with six per-run metric kernels (RMSE, IAE, ISE, settling time, overshoot, total energy) plus the locked weighted cost and rank, and a `compare()` harness that runs all four controllers on both weathers (seed-7 train + seed-21 holdout) and writes `results/comparison.csv`. Every input needed already exists in-repo: the locked energy definition, the four controller step functions with a shared call signature, the `_run_closed_loop` harness shape, both weather CSVs, and the GA params artifact.

**Primary recommendation:** Implement metric kernels as pure NumPy functions over logged histories, reuse the `_run_closed_loop` loop verbatim (parameterized by weather path + controller step), compute energy with the byte-identical accumulation from `genetic_algorithm.py`, return a list-of-dicts from `compare()`, and freeze the CSV column contract for Phase-6/7 reuse.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (Comparison Weather):** Scoreboard runs on BOTH weathers: seed-21 holdout (fresh, unseen — the primary core-value claim) plus seed-7 train as reference. Full generalization story; train numbers are context, holdout numbers are the verdict.
- **D-02 (Table Format):** `compare()` returns a columnar structure AND writes `results/comparison.csv` — notebooks and dashboard read the same artifact. Pandas-free: NO new dependency — the "DataFrame" is a plain-Python columnar structure (dict of lists / list of dicts) plus `csv`-module file output.
- **D-03 (Settling Definition):** Settled = T stays within ±0.5 °C AND RH within ±3 %RH for the remainder of the run — matches the hysteresis bands, strict but consistent across all four controllers.
- **D-04 (Weighted-Cost Column):** Table carries all six METR-01 metrics PLUS weighted cost (locked 1.0/1.0/0.01 weights, duty-hours energy incl. vent — identical definition to `genetic_algorithm.py:173-174,186`) and a rank column.
- **D-05 (Proof Shape):** No dedicated Phase-5 notebook — the table/CSV is proven by the suite asserting the locked holdout ordering (GA < on/off AND < PID); Phase 6 owns the comparison plots.

### the agent's Discretion
- Columnar structure exact shape (dict-of-lists vs list-of-dicts) within the D-02 constraint; CSV dialect/header details.
- Overshoot definition (peak beyond setpoint, % or absolute) and ISE/RMSE normalization within standard practice.
- Harness shape for running all four controllers on both weathers (reuse `_run_closed_loop` family); runtime budget for the 8 full runs.
- Settling edge semantics (never-settled marker value) within the D-03 band.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| METR-01 | Computes RMSE, IAE, ISE, settling time, overshoot, total energy from logged T/RH history vs setpoint | Metric kernel formulas + locked energy definition (§ Standard Stack, § Code Examples) |
| METR-02 | Final comparison table across all four controllers (on/off, PID, manual fuzzy, GA fuzzy) | `compare()` harness design + frozen CSV column contract (§ Architecture Patterns) |

## Project Constraints (from AGENTS.md)

- Python 3, NumPy numerics, Streamlit dashboard UI, Matplotlib in notebooks, CSV for weather input, JSON for GA params.
- Order: hand-tuned fuzzy first, GA second; dashboards last (Phase 5 sits between GA and notebooks — it consumes Phase 3/4, feeds Phase 6/7).
- Notebooks must run against `src/` functions with no duplicated logic — `metrics.py`/`compare()` must therefore be importable library code, not notebook-inline code.
- Zero-dep convention (surfaced in 05-CONTEXT.md § Specific Ideas): NO pandas — NumPy + stdlib only.

## Architectural Responsibility Map

Single-tier system (local Python library + CSV artifact — no browser/server/CDN/database split applies). Intra-repo ownership map instead:

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Metric kernels (RMSE/IAE/ISE/settling/overshoot/energy/cost) | `src/metrics.py` pure functions | — | PROJECT.md no-duplicated-logic: one canonical implementation consumed by suite, notebooks, dashboard |
| Closed-loop scoring runs (4 controllers × 2 weathers) | `compare()` harness in `src/metrics.py` | existing `_run_closed_loop` shape | Reuse beats rewrite; identical loop = bit-comparable energies |
| Machine-readable artifact | `results/comparison.csv` (+ returned list-of-dicts) | — | Single artifact read by Phase-6 notebooks and Phase-7 dashboard; column names are a frozen contract |
| Correctness proof | `tests/test_metrics.py` plain-assert suite | — | No Phase-5 notebook per D-05; the suite carries the holdout-ordering claim |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| NumPy | 2.4.3 [VERIFIED: python CLI probe this session] | All metric math (mean, abs, sqrt, arg-scans) | Already the project numerics standard; every prior phase uses it |
| `csv` (stdlib) | Python 3.14.6 [VERIFIED: python CLI probe this session] | Write `results/comparison.csv` | Zero-dep convention; weather-generator precedent uses stdlib + `np.savetxt` |
| `json` (stdlib) | Python 3.14.6 | Read `results/ga_optimized_params.json` (GA controller params) | Established artifact pattern; `load_optimized_mfs` already handles schema v2 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `src.genetic_algorithm` (in-repo import) | n/a | Reuse or mirror locked energy/weights: `W1, W2, W3 = 1.0, 1.0, 0.01` [VERIFIED: src/genetic_algorithm.py:50] | Import the weight constants; duplicate the energy accumulation verbatim with a comment pointing at the lock |
| `src.ga_fuzzy_controller.load_optimized_mfs` | n/a | GA controller params source (schema v2: `mfs` + `coupling`) [VERIFIED: src/ga_fuzzy_controller.py:37-77] | GA leg of the scoreboard; wraps `ga_fuzzy_step(T_C, rh_pct, T_sp, RH_sp, state)` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `csv` | pandas DataFrame | REJECTED per D-02: pandas is a new dependency, violates the zero-dep convention, and is unneeded for an 8-row table |
| stdlib `csv` | `np.savetxt` | Viable (weather-generator precedent) but `csv.DictWriter` preserves the header contract explicitly — prefer `csv` |
| list-of-dicts return | dict-of-lists return | Either satisfies D-02; recommend **list-of-dicts** (one dict per table row): round-trips through `csv.DictWriter`/`DictReader` with zero reshaping, and each row carries its own `controller`+`weather` labels |

**Installation:**
```bash
# No new packages. NumPy 2.4.3 already installed (verified 2026-09-27).
pip install numpy  # only if environment changes; do NOT add pandas
```

**Version verification:** `python --version` → `Python 3.14.6`; `numpy.__version__` → `2.4.3` (both probed this session). `python -m pytest` → **not installed** (plain-assert + `__main__` runner convention applies — see Validation Architecture).

## Package Legitimacy Audit

No external packages are installed by this phase (NumPy + stdlib only, both pre-existing). Audit table omitted intentionally — there is nothing new to vet. Planner: do NOT add any install step; gate any proposal to introduce pandas behind `checkpoint:human-verify` (it contradicts locked D-02).

## Architecture Patterns

### System Architecture Diagram

```
weather/weather_profile.csv (seed-7 train) ──┐
weather/holdout_21.csv (seed-21 holdout) ─────┤
                                             ▼
                    ┌─────────────────────────────────┐
                    │ compare(): scoring harness       │
                    │  for each weather × controller:  │
                    │   _run_closed_loop → histories   │
                    │   (T_hist, RH_hist, U_hist)      │
                    └───────────────┬─────────────────┘
                                    ▼
                    ┌─────────────────────────────────┐
                    │ metric kernels (pure functions): │
                    │  rmse/iae/ise per channel        │
                    │  settling_time (locked band)     │
                    │  overshoot per channel           │
                    │  energy (locked duty-hours def)  │
                    │  cost = 1.0·IAE_T+1.0·IAE_H      │
                    │         +0.01·E; rank per weather│
                    └───────────────┬─────────────────┘
                    ▼                               ▼
        list-of-dicts (return)      results/comparison.csv
                    │                               │
                    └───────────┬───────────────────┘
                                ▼
              Phase-6 notebooks + Phase-7 dashboard
```

Trace the primary claim: holdout weather + GA controller → histories → cost 114.28, rank 1 → CSV row → dashboard table.

### Recommended Project Structure
```
src/
├── metrics.py            # kernels + compare() + __main__ smoke print
tests/
├── test_metrics.py       # plain-assert suite (ordering + energy identity + CSV round-trip)
results/
├── comparison.csv        # 8 rows: 4 controllers × 2 weathers (frozen columns)
```

### Pattern 1: Pure metric kernels over logged histories
**What:** Each kernel is a pure function `(history, setpoint, dt) -> float`. No simulator imports inside kernels — they operate on already-logged lists/arrays, so the suite can unit-test them on synthetic histories without running 1440 steps.
**When to use:** All six METR-01 metrics.
**Example:**
```python
# Standard integral-error conventions adapted to dt=60s runs [ASSUMED standard practice]:
# IAE in degree-hours / %-hours: sum|e| * dt/3600 == sum|e|/60 at dt=60 --
#   identical to the locked fitness accumulation [VERIFIED: src/genetic_algorithm.py:185-187]:
#   "iae_T += abs(T - T_sp) / 60.0" / "iae_H += abs(rh - RH_sp) / 60.0" / "E += sum(act.values()) / 60.0  # duty-hours"
import numpy as np
def iae(hist, sp, dt=60.0):
    e = np.asarray(hist, dtype=float) - sp
    return float(np.sum(np.abs(e)) * dt / 3600.0)
def ise(hist, sp, dt=60.0):
    e = np.asarray(hist, dtype=float) - sp
    return float(np.sum(e * e) * dt / 3600.0)
def rmse(hist, sp):
    e = np.asarray(hist, dtype=float) - sp
    return float(np.sqrt(np.mean(e * e)))
def energy_duty_hours(U_hist):
    # LOCKED — must be identical to genetic_algorithm.closed_loop_breakdown [VERIFIED: src/genetic_algorithm.py:174-175]:
    # "E = sum over steps of (sum over actuators of duty) / 60  [duty-hours]."
    return float(sum(sum(act.values()) for act in U_hist) / 60.0)
def weighted_cost(iae_T, iae_H, E, w1=1.0, w2=1.0, w3=0.01):
    # weights locked [VERIFIED: src/genetic_algorithm.py:50]: "W1, W2, W3 = 1.0, 1.0, 0.01  # D-01 locked fitness weights"
    return float(w1 * iae_T + w2 * iae_H + w3 * E)
```

### Pattern 2: Settling-time as last-exit scan with the locked band
**What:** Settled = T within ±0.5 °C **AND** RH within ±3 %RH for the remainder of the run (D-03). Bands match the on/off hysteresis defaults [VERIFIED: src/onoff_controller.py:15-16]: `def onoff_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, band_T=0.5, band_RH=3.0)`. Scan from the end backwards: find the last index violating either band; settling time = (index+1) minutes (dt=60s → 1 step = 1 min). Never-settled marker: `float("inf")` in memory, serialized as `inf` by the csv module (round-trips via `float("inf")`) — see Pitfall 3.
**When to use:** The single settling-time column (joint T+RH condition — one value, not per-channel).
**Example:**
```python
import numpy as np
def settling_time_min(T_hist, RH_hist, T_sp=25.0, RH_sp=70.0,
                      band_T=0.5, band_RH=3.0, dt=60.0):
    T = np.asarray(T_hist, dtype=float); RH = np.asarray(RH_hist, dtype=float)
    bad = np.where((np.abs(T - T_sp) > band_T) | (np.abs(RH - RH_sp) > band_RH))[0]
    if bad.size == 0:
        return 0.0
    if bad[-1] == len(T) - 1:
        return float("inf")  # violates at final step → never settled
    return float((bad[-1] + 1) * dt / 60.0)
```

### Pattern 3: Overshoot as absolute peak excursion beyond setpoint
**What:** `overshoot_T = max(0, max(T_hist - T_sp))` in °C; `overshoot_H = max(0, max(RH_hist - RH_sp))` in %RH [ASSUMED standard-practice adaptation — see Assumptions Log A1]. Absolute units (not %) because the two channels have incommensurable units and the table already carries per-channel RMSE/IAE/ISE. Rationale for positive-side-only: the run starts cold (20 °C vs 25 °C setpoint [VERIFIED: tests/test_fuzzy_controller.py:19]: `T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)`), so the initial −5 °C error is a startup transient, not overshoot; overshoot measures how far control pushes PAST the target.
**When to use:** Both overshoot columns.

### Pattern 4: Scoreboard harness reusing the `_run_closed_loop` shape
**What:** One parameterized loop — `(controller_step, weather_path) -> (T_hist, RH_hist, U_hist)` — copied from the test harness [VERIFIED: tests/test_fuzzy_controller.py:11-30] with two changes: weather path becomes an argument (seed-7 vs seed-21), and the GA leg passes `ga_fuzzy_step` (which loads MFs from JSON internally [VERIFIED: src/ga_fuzzy_controller.py:80-88]). Init, `np.interp` weather resampling, `daytime_solar`, and setpoints-as-args stay identical so energies are bit-comparable with the fitness loop. 8 runs × 1440 steps; estimated wall time under ~2 minutes total [ASSUMED — see A2], dominated by the two fuzzy legs (201-point centroid grid per step).
**When to use:** `compare()` internals.

### Anti-Patterns to Avoid
- **Rewriting the closed loop per controller:** four bespoke loops drift (different init/interp/order) and silently break energy bit-identity. One parameterized loop instead.
- **Normalizing IAE by horizon or by channel range:** the locked fitness uses raw `sum|e|/60`; any normalization makes the cost column incomparable with GA fitness and the reference numbers. Keep raw.
- **Per-channel settling times:** D-03 defines ONE joint condition; two columns invite contradictory "settled" claims. One `settling_min` column.
- **Importing pandas "just for the table":** contradicts locked D-02 and adds a dependency the dashboard/notebooks must then also carry.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Energy accumulation | A new energy formula | Verbatim `sum(act.values())/60.0` per step [VERIFIED: src/genetic_algorithm.py:187] | Any deviation (mean instead of sum, missing vent, /3600) breaks bit-identity with GA fitness and voids the core-value comparison |
| Weather CSV parsing in harness | Custom CSV reader | `load_weather_profile` from `src.greenhouse_model` [VERIFIED: src/greenhouse_model.py:87-101] | Validates monotonic minutes, 0..1440 span, RH bounds; derives `w_out` from RH+T |
| Seed-21 weather | Fresh random weather at score time | Committed `weather/holdout_21.csv` (verified distinct from train: first rows `0 15.94 77.43` vs `0 15.76 78.77`) | Regenerating risks seed/parameter drift; the committed file is the frozen holdout the reference numbers were scored on |
| CSV writing | Manual string formatting | `csv.DictWriter` with frozen fieldnames | Header contract enforced in one place; `inf` serializes parseably |
| GA controller invocation | Direct MF-dict plumbing | `ga_fuzzy_step` + `load_optimized_mfs` [VERIFIED: src/ga_fuzzy_controller.py:80-88] | Handles schema-v2 validation, coupling gains, and mtime-aware caching |

**Key insight:** The scoreboard's only hard requirement is *comparability*: identical loop, identical energy, identical weights. Every reuse decision above serves that single property.

## Common Pitfalls

### Pitfall 1: Energy off by vent or by normalization
**What goes wrong:** Metrics energy differs from GA fitness energy on the same run (e.g., averaging instead of summing, omitting `vent`, dividing by 3600).
**Why it happens:** "Duty-hours" is ambiguous; the lock lives in one code comment.
**How to avoid:** Copy the accumulation verbatim (`E += sum(act.values()) / 60.0` per step) with a comment citing `genetic_algorithm.py:187`; add the energy-identity assert (Validation Architecture V3).
**Warning signs:** GA holdout cost in the table ≠ 114.28 reference.

### Pitfall 2: IAE convention mismatch
**What goes wrong:** IAE computed as `mean|e|` or `sum|e|*dt` (degree-seconds) instead of degree-hours.
**Why it happens:** Textbook IAE is the raw integral; the codebase convention folds `/3600` in via `/60` at dt=60.
**How to avoid:** Use `sum|e| * dt/3600` generally (= `/60` at dt=60); assert `metrics.iae == closed_loop_breakdown` IAE terms on a shared run.
**Warning signs:** Reference check fails: GA holdout IAE_T should be ≈ 1.66, IAE_H ≈ 112.44.

### Pitfall 3: Never-settled marker breaks the CSV
**What goes wrong:** Using `None` for never-settled crashes `csv` float round-trip or downstream `float()` parsing; using `-1` collides with "settled at t=0" semantics.
**Why it happens:** In-memory sentinel vs serialized form not decided up front.
**How to avoid:** `float("inf")` in memory → csv writes `inf` → `float("inf")` parses back losslessly. Document in the `compare()` docstring.
**Warning signs:** `ValueError` in Phase-6 notebook CSV load.

### Pitfall 4: RH history logged pre-step vs post-step
**What goes wrong:** Off-by-one alignment between T_hist/RH_hist and setpoint (RH logged before `step()` update vs after).
**Why it happens:** The harness appends post-step `(T, rh)` [VERIFIED: tests/test_fuzzy_controller.py:26-29] while the controller saw pre-step RH — both defensible, but mixing conventions across legs corrupts comparisons.
**How to avoid:** Reuse the harness append order verbatim for all four legs; never "fix" one leg's logging.
**Warning signs:** Train-leg numbers differ from GA fitness history on identical weather.

### Pitfall 5: Scoring the wrong weather file
**What goes wrong:** Both table blocks silently scored on seed-7 (e.g., hardcoded path), making the "holdout" claim false.
**Why it happens:** `_run_closed_loop` hardcodes `"weather/weather_profile.csv"` [VERIFIED: tests/test_fuzzy_controller.py:15].
**How to avoid:** Weather path is a required argument of the harness (no default); suite asserts the two blocks' T_hist differ.
**Warning signs:** Train cost == holdout cost for any controller.

### Pitfall 6: `ga_fuzzy_step` I/O cost × 1440 × 2 runs
**What goes wrong:** Fear that JSON reload per step makes the GA legs slow.
**Why it happens:** `load_optimized_mfs` is called every step.
**How to avoid:** No action — it caches per path+mtime and returns deep copies of tiny dicts [VERIFIED: src/ga_fuzzy_controller.py:46-50]. Just don't "optimize" it.
**Warning signs:** None expected; total runtime stays in the low minutes.

## Code Examples

### Frozen CSV column contract (for Phase-6/7 reuse)
```python
# Recommended fieldnames — freeze exactly these strings [ASSUMED naming; see A3]:
COLUMNS = ["controller", "weather",
           "rmse_T", "rmse_H", "iae_T", "iae_H", "ise_T", "ise_H",
           "settling_min", "overshoot_T", "overshoot_H",
           "energy", "cost", "rank"]
# controller ∈ {"onoff","pid","fuzzy","ga_fuzzy"}; weather ∈ {"train-seed7","holdout-seed21"}
# rank = 1..4 by cost within each weather block (holdout block is the verdict)
```

### `compare()` skeleton
```python
import csv, os
CONTROLLERS = [("onoff", onoff_step), ("pid", pid_step),
               ("fuzzy", fuzzy_step), ("ga_fuzzy", ga_fuzzy_step)]
WEATHERS = [("train-seed7", "weather/weather_profile.csv"),
            ("holdout-seed21", "weather/holdout_21.csv")]
def compare(out_path="results/comparison.csv"):
    rows = []
    for wname, wpath in WEATHERS:
        block = []
        for cname, cstep in CONTROLLERS:
            T_h, RH_h, U_h = run_closed_loop(cstep, wpath)  # 1440 × dt=60
            m = all_metrics(T_h, RH_h, U_h)                 # six metrics + cost
            block.append({"controller": cname, "weather": wname, **m})
        for i, r in enumerate(sorted(block, key=lambda r: r["cost"]), 1):
            r["rank"] = i
        rows.extend(block)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="") as f:
        csv.DictWriter(f, fieldnames=COLUMNS).writeheader()
        for r in rows:  # inf settling serializes as "inf", parses back exactly
            f.writeheader() if False else None
            csv.DictWriter(f, fieldnames=COLUMNS)  # (use one writer; shown inline for brevity)
    return rows  # list-of-dicts: the D-02 columnar structure
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Step-response metrics (rise time, % overshoot of a step) | Disturbance-rejection metrics over a 24h run (IAE/RMSE energy + last-exit settling) | N/A — domain adaptation | Classical step metrics don't apply (no step input; setpoint constant, weather disturbs); use § Architecture Patterns adaptations |
| pandas scoreboard | stdlib csv + list-of-dicts | D-02 (locked this phase) | Zero new dependencies; columns frozen as plain strings |

**Deprecated/outdated:** None in scope.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Overshoot = absolute peak excursion beyond setpoint per channel (°C / %RH), positive-side-only | Pattern 3 | LOW — planner confirms in discuss; alternative (% of setpoint) only rescales, doesn't reorder |
| A2 | 8 full runs complete in low single-digit minutes on a laptop | Pattern 4 | LOW — even 10× slower is still suite-tolerable; planner sets a timeout budget |
| A3 | Exact CSV column names (`rmse_T`, `settling_min`, …) | Code Examples | MEDIUM — names become the Phase-6/7 contract; planner freezes them in PLAN.md and discuss-phase confirms |

## Open Questions

1. **Should `rank` be computed per weather block or globally?**
   - What we know: D-04 requires a rank column; D-01 names holdout the verdict.
   - Recommendation: rank 1–4 **within each weather block** (two #1s, one per block) — train rank is context, holdout rank is the verdict. Global rank would let train numbers contaminate the verdict ordering.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | everything | ✓ | 3.14.6 | — |
| NumPy | metric math, harness | ✓ | 2.4.3 | — |
| pytest | test runner | ✗ | — | Plain-assert + `__main__` runner (established convention, all 4 existing suites) |
| jupyter CLI | notebooks | ✗ (noted in prior phases) | — | None needed — D-05: no Phase-5 notebook |
| pandas | nothing (explicitly excluded) | ✗ (absent = desired) | — | stdlib `csv` per D-02 |
| `weather/holdout_21.csv` | holdout block | ✓ | committed, byte-distinct from train | Regenerate via `generate_weather_profile(path, seed=21)` only if missing |

**Missing dependencies with no fallback:** None — the phase is fully executable as-is.
**Missing dependencies with fallback:** pytest → plain-assert convention (no action).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Plain-assert suite, pytest-compatible names, in-body imports, `__main__` runner (repo convention) |
| Config file | none — see Wave 0 (no pytest/jupyter installed; consistent with all prior phases) |
| Quick run command | `python tests/test_metrics.py` |
| Full suite command | `python tests/test_metrics.py` + rerun of prior suites (`test_baseline_controllers.py`, `test_fuzzy_controller.py`, `test_genetic_algorithm.py`) for no-regression |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| METR-01 | RMSE/IAE/ISE kernels match hand-computed values on synthetic histories | unit | `python tests/test_metrics.py::test_metric_kernels_synthetic` | ❌ Wave 0 |
| METR-01 | Settling: joint-band last-exit incl. never-settled `inf` + settled-at-0 edge cases | unit | `python tests/test_metrics.py::test_settling_edges` | ❌ Wave 0 |
| METR-01 | Energy bit-identical to `closed_loop_breakdown` on a shared fuzzy run | unit | `python tests/test_metrics.py::test_energy_identity` (`assert E_metrics == E_fitness`) | ❌ Wave 0 |
| METR-01 | Overshoot absolute peak beyond setpoint per channel on synthetic histories | unit | `python tests/test_metrics.py::test_overshoot` | ❌ Wave 0 |
| METR-02 | `compare()` returns 8 rows (4 controllers × 2 weathers), all frozen columns present and finite (except `inf` settling) | integration | `python tests/test_metrics.py::test_compare_shape` | ❌ Wave 0 |
| METR-02 | Holdout ordering: GA cost < on/off cost AND < PID cost (core-value verdict) | integration | `python tests/test_metrics.py::test_holdout_ordering` | ❌ Wave 0 |
| METR-02 | CSV written, header == COLUMNS, round-trips to returned rows | integration | `python tests/test_metrics.py::test_csv_roundtrip` | ❌ Wave 0 |
| METR-02 | Train vs holdout blocks differ (wrong-file guard) | integration | `python tests/test_metrics.py::test_weathers_distinct` | ❌ Wave 0 |

Pass criteria (concrete): holdout reference numbers from 04-SUMMARY — GA cost ≈ 114.28 (IAE_T ≈ 1.66, IAE_H ≈ 112.44, E ≈ 18.13) < on/off ≈ 513.75 < PID ≈ 645.26. Assert **strict ordering** (`ga < onoff`, `ga < pid`), not exact equality — exact values are brittle to harness drift while ordering is the locked claim. Energy identity uses exact `==` (same accumulation order ⇒ bit-identical). NaN-injection: `metrics` kernels raise `AssertionError` on non-finite input (fail-fast convention).

### Sampling Rate
- **Per task commit:** `python tests/test_metrics.py`
- **Per wave merge:** full suite (all five test files, each standalone-runnable)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_metrics.py` — covers METR-01/02 per map above (largest gap; suite-first)
- [ ] `results/comparison.csv` — generated artifact, asserted by round-trip test (not hand-written)
- [ ] Framework install: none — plain-assert convention, no install step

## Security Domain

Required (security_enforcement enabled, ASVS level 1). Surface is minimal: local pure functions + one CSV artifact; no network, no auth, no sessions.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | n/a — local batch computation, no users |
| V3 Session Management | no | n/a |
| V4 Access Control | no | n/a — output path is a fixed repo-relative artifact, not user-supplied |
| V5 Input Validation | yes | Fail-fast asserts on histories (finite, non-empty, equal length), setpoints, dt>0; `load_optimized_mfs` schema validation reused for GA leg |
| V6 Cryptography | no | n/a |
| V14 Configuration | partial | No new dependencies (supply chain surface unchanged); `csv` stdlib only |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSV overwrite of unintended path (if `out_path` parameterized) | Tampering | Default to fixed `results/comparison.csv`; `os.makedirs(exist_ok=True)` on the dirname only; never join unsanitized segments into the path |
| NaN/inf poisoning from sim divergence silently scored | Tampering (integrity) | Fail-fast `np.isfinite` asserts in every kernel; suite NaN-injection check |
| Malicious `ga_optimized_params.json` (artifact tampering → skewed scoreboard) | Tampering | JSON-only load via existing `load_optimized_mfs` validation (never pickle/eval); schema asserts fail loud |
| Supply-chain via new dependency | Tampering | Zero new dependencies — pandas or any helper addition requires human checkpoint |

## Sources

### Primary (HIGH confidence)
- `src/genetic_algorithm.py:50,167-188` (read this session) — locked weights, energy definition, IAE accumulation
- `src/onoff_controller.py:15-16` (read this session) — hysteresis bands backing D-03
- `src/ga_fuzzy_controller.py:37-88` (read this session) — schema v2 + `ga_fuzzy_step` invocation
- `tests/test_fuzzy_controller.py:11-30` (read this session) — `_run_closed_loop` harness shape, init, interp
- `src/greenhouse_model.py:87-101` (read this session) — weather loading contract
- `src/weather_profile_generator.py:15-27` (read this session) — seed-7 default, CSV dialect
- CLI probes this session — Python 3.14.6, NumPy 2.4.3, pytest absent; `weather/holdout_21.csv` present and byte-distinct from train

### Secondary (MEDIUM confidence)
- 05-CONTEXT.md canonical refs — reference holdout numbers (GA 114.28 < on/off 513.75 < PID 645.26), schema-v2 provenance

### Tertiary (LOW confidence)
- Standard control-metric definitions (RMSE/IAE/ISE/last-exit settling/peak overshoot) — textbook practice adapted to this run shape, tagged [ASSUMED] at each use; see Assumptions Log

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions probed live; zero new deps
- Architecture: HIGH - all contracts read from source-of-truth files this session
- Pitfalls: HIGH - derived from the actual locked definitions and harness code, not generic advice

**Research date:** 2026-09-27
**Valid until:** 30 days (stable domain — in-repo contracts; only A1–A3 need planner confirmation)
