# Phase 5: Metrics & Comparison - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 3 (2 new source files + 1 generated artifact)
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/metrics.py` | utility (pure metric kernels + scoreboard harness) | transform (histories → scalars) + batch (4 controllers × 2 weathers) | `src/genetic_algorithm.py` (kernels/energy lock) + `tests/test_fuzzy_controller.py` (loop shape) | exact (same accumulation, same loop) |
| `tests/test_metrics.py` | test | batch (suite asserting ordering + identity + round-trip) | `tests/test_genetic_algorithm.py` + `tests/test_fuzzy_controller.py` | exact |
| `results/comparison.csv` | generated artifact (machine-readable scoreboard) | batch (written once by `compare()`) | `results/ga_optimized_params.json` | role-match (frozen-schema artifact precedent) |

## Pattern Assignments

### `src/metrics.py` (utility, transform + batch)

**Analog A (metric kernels + locked energy):** `src/genetic_algorithm.py`

**Imports pattern** (lines 19-22, plus dual-import fallback lines 24-33):
```python
import json
import os

import numpy as np

try:
    from src.greenhouse_model import (step, load_weather_profile,
                                      daytime_solar, params,
                                      relative_humidity, wsat_g_per_kg)
    from src.fuzzy_controller import fuzzy_step, FUZZY_MFS
except ImportError:  # `python src/genetic_algorithm.py` puts src/ on sys.path
    from greenhouse_model import (step, load_weather_profile,
                                  daytime_solar, params,
                                  relative_humidity, wsat_g_per_kg)
    from fuzzy_controller import fuzzy_step, FUZZY_MFS
```
Copy: `import numpy as np` first-party style; the `try: from src.X / except ImportError: from X` dual-import block so the module runs both as `python src/metrics.py` and as `from src.metrics import ...`. metrics.py needs the same treatment (imports `step`, `load_weather_profile`, `daytime_solar`, `params`, `relative_humidity`, `wsat_g_per_kg` + the four controller steps).

**Locked weights** (line 50):
```python
W1, W2, W3 = 1.0, 1.0, 0.01  # D-01 locked fitness weights
```
Copy: import or re-declare verbatim as `W1, W2, W3 = 1.0, 1.0, 0.01`; `weighted_cost = W1*iae_T + W2*iae_H + W3*E`.

**Core accumulation pattern — the LOCK** (lines 167-188):
```python
def closed_loop_breakdown(mfs, T_out_hr, w_out_hr, hours,
                           T_sp=25.0, RH_sp=70.0, gains=None):
    """Full 1440-step closed loop -> (IAE_T, IAE_H, duty-hours energy E).
    ...
    Energy definition (locked here, Phase 5 metrics.py must be identical):
    E = sum over steps of (sum over actuators of duty) / 60  [duty-hours].
    """
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st, iae_T, iae_H, E = None, 0.0, 0.0, 0.0
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = coupled_fuzzy_step(T, rh, T_sp, RH_sp, st, DT, mfs, gains)
        T, w, rh = step(DT, act,
                        (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"])),
                        T, w)
        iae_T += abs(T - T_sp) / 60.0
        iae_H += abs(rh - RH_sp) / 60.0
        E += sum(act.values()) / 60.0  # duty-hours
    return iae_T, iae_H, E
```
Copy verbatim: init `T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)`; post-step `(T, w, rh)` append/log order; `iae += abs(x - sp) / 60.0` (degree-hours at dt=60 — generalize to `* dt/3600`); `E += sum(act.values()) / 60.0` — MUST include ALL four actuators incl. vent. Add a comment citing `genetic_algorithm.py:187` at the energy line. Generalize `closed_loop_breakdown` from MF-specific to any `controller_step(T, rh, T_sp, RH_sp, state)`.

**Never-raises fitness wrapper** (lines 191-201):
```python
def evaluate(chrom, T_out_hr, w_out_hr, hours, T_sp=25.0, RH_sp=70.0):
    """Fitness: W1*IAE_T + W2*IAE_H + W3*E (coupled path). Never raises."""
    try:
        ...
        cost = W1 * iae_T + W2 * iae_H + W3 * E
        assert np.isfinite(cost)
        return float(cost)
    except Exception:
        return float("inf")
```
Note only: metrics kernels do the OPPOSITE — fail-fast `assert np.isfinite(...)` (fail loud on NaN, per RESEARCH Pitfall 2/ASVS V5). Do NOT copy the swallow-to-inf behavior into kernels.

---

**Analog B (scoring-loop shape):** `tests/test_fuzzy_controller.py` lines 11-30

```python
def _run_closed_loop(np, controller_step, n=1440, T_sp=25.0, RH_sp=70.0):
    from src.greenhouse_model import (step, load_weather_profile,
                                      daytime_solar, params,
                                      relative_humidity, wsat_g_per_kg)
    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    hours = np.arange(0, n) / 60.0
    T_out_hr = np.interp(hours, t_min, T_out)
    w_out_hr = np.interp(hours, t_min, w_out)
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st = None
    T_hist, RH_hist, U_hist = [], [], []
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = controller_step(T, rh, T_sp, RH_sp, st)
        wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, wx, T, w)
        T_hist.append(T)
        RH_hist.append(rh)
        U_hist.append(act)
    return T_hist, RH_hist, U_hist
```
Copy with ONE change: weather path becomes a required argument (`run_closed_loop(controller_step, weather_path, ...)` — no default, per Pitfall 5 wrong-file guard). Keep: `np.arange(0, n)/60.0` hours, `np.interp` resampling, `20.0 / 0.65*wsat` init, `daytime_solar(h, params["A_sol"])`, post-step append order (Pitfall 4 — never "fix" one leg's logging). Setpoints stay live args (`T_sp=25.0, RH_sp=70.0`).

**Analog C (artifact-write pattern):** `src/genetic_algorithm.py` lines 249-262

```python
def _write_json(path, mfs_lists, gains_lists, best_fit, weights, train_weather,
                train_seed, holdout_seed, population, generations, rng_seed,
                hist_best, hist_mean):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        json.dump({...}, f)
```
Copy: `os.makedirs(dirname, exist_ok=True)` before writing; default `out_path="results/comparison.csv"`. But use `csv.DictWriter` (not `json.dump`, not `np.savetxt`) with the frozen `COLUMNS` fieldnames — one writer instance, `writeheader()` once. `float("inf")` settling serializes as `inf`, parses back via `float("inf")` (Pitfall 3).

**Analog D (settling band constants):** `src/onoff_controller.py` lines 15-16

```python
def onoff_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None,
               band_T=0.5, band_RH=3.0):
```
Copy: default `band_T=0.5, band_RH=3.0` in `settling_time_min(...)` — matches hysteresis bands per D-03. Last-exit scan: last index violating either band → `(index+1)*dt/60` minutes; violation at final step → `float("inf")`; empty violation set → `0.0`.

**Analog E (weather loading — do NOT hand-roll):** `src/greenhouse_model.py` lines 87-101

```python
def load_weather_profile(path):
    arr = np.loadtxt(path, skiprows=1)
    t_min, temp_C, rh_pct = arr[:, 0], arr[:, 1], arr[:, 2]
    assert np.all(np.diff(t_min) > 0), "time column must be strictly increasing"
    assert t_min[0] == 0.0 and t_min[-1] == 1440.0, "time must span 0..1440 min"
    assert np.all((rh_pct >= 0.0) & (rh_pct <= 100.0)), "RH must lie in [0, 100]"
    w_out = rh_pct / 100.0 * wsat_g_per_kg(temp_C)
    return t_min, temp_C, w_out
```
Copy: call `load_weather_profile(weather_path)` inside the harness — never a custom CSV reader. GA leg invokes `ga_fuzzy_step(T, rh, T_sp, RH_sp, state)` from `src/ga_fuzzy_controller.py` lines 80-88 (handles schema-v2 + mtime-aware cache internally — do NOT "optimize" it).

**Frozen column contract** (from RESEARCH.md Code Examples — freeze exactly):
```python
COLUMNS = ["controller", "weather",
           "rmse_T", "rmse_H", "iae_T", "iae_H", "ise_T", "ise_H",
           "settling_min", "overshoot_T", "overshoot_H",
           "energy", "cost", "rank"]
# controller ∈ {"onoff","pid","fuzzy","ga_fuzzy"}; weather ∈ {"train-seed7","holdout-seed21"}
# rank = 1..4 by cost WITHIN each weather block (holdout block is the verdict)
```

---

### `tests/test_metrics.py` (test, batch)

**Analog A:** `tests/test_genetic_algorithm.py`

**File header + in-body import convention** (lines 1-12):
```python
"""Plain-assert sanity suite for the GA-tuned fuzzy controller (GA-01..05).
...
Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_genetic_algorithm.py
"""
```
Copy: same docstring shape (naming the METR-01/02 requirements), same `Run: python tests/test_metrics.py` line, same in-body imports.

**Reference-loop cross-check pattern** (lines 71-98 — `test_fitness_matches_hand_cost`):
```python
    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    hours = np.arange(0, 1440) / 60.0
    T_hr = np.interp(hours, t_min, T_out)
    w_hr = np.interp(hours, t_min, w_out)
    cost = evaluate(encode(FUZZY_MFS), T_hr, w_hr, hours)
    ...
    T, w, st = 20.0, 0.65 * wsat_g_per_kg(20.0), None  # reference direct loop
    iae_T, iae_H, E = 0.0, 0.0, 0.0
    for i, h in enumerate(hours):
        ...
        iae_T += abs(T - 25.0) / 60.0
        iae_H += abs(rh - 70.0) / 60.0
        E += sum(act.values()) / 60.0
    ref = 1.0 * iae_T + 1.0 * iae_H + 0.01 * E
    assert abs(cost - ref) < 1e-9, (cost, ref)
    print(f"hand fitness {cost:.2f} (IAE_T {iae_T:.2f} IAE_H {iae_H:.2f} E {E:.2f})")
```
Copy for `test_energy_identity`: `assert E_metrics == E_fitness` exact `==` (same accumulation order ⇒ bit-identical); reference numbers GA holdout ≈ 114.28 (IAE_T ≈ 1.66, IAE_H ≈ 112.44, E ≈ 18.13) asserted as **strict ordering** (`ga < onoff`, `ga < pid`), never exact equality.

**Holdout comparison shape** (lines 220-240 — `test_tiny_ga_monotonic`):
```python
    tmp = os.path.join(tempfile.mkdtemp(), "ga_tiny.json")
    t0 = time.time()
    res = run_ga(population=4, generations=2, rng_seed=0, out_path=tmp)
    dt = time.time() - t0
    assert dt < 300.0, dt  # hang guard only, not a perf bar (WR-03)
```
Copy: hang-guard pattern for the 8-run `compare()` integration tests (8 × 1440 steps, fuzzy legs dominate); use `tempfile.mkdtemp()` for the CSV round-trip test so the committed `results/comparison.csv` is never clobbered by tests.

**JSON/CSV artifact assert shape** (lines 189-208 — `test_json_schema`):
```python
    with open(tmp) as f:
        d = json.load(f)
    assert set(d) == {"mfs", "coupling", "fitness", "weights", ...}, set(d)
    ...
    assert d["weights"] == {"w1": 1.0, "w2": 1.0, "w3": 0.01}
```
Copy for `test_csv_roundtrip`: `csv.DictReader` back, `assert reader.fieldnames == COLUMNS`, row-count 8, per-row key-set == set(COLUMNS); `float("inf")` settling round-trips.

**Analog B:** `tests/test_fuzzy_controller.py` lines 236-254 (`__main__` runner)

```python
if __name__ == "__main__":
    import sys, os
    # "python tests/test_fuzzy_controller.py" puts tests/ on sys.path, not the
    # repo root — prepend the root so the in-body `from src import ...` works
    # both standalone and under pytest (which adds rootdir itself).
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    failures = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:
                failures.append(name)
                print(f"FAIL {name}: {exc!r}")
    if failures:
        print(f"{len(failures)} check(s) failed: {failures}")
        sys.exit(1)
    print("all checks passed")
```
Copy verbatim (only the filename in the comment changes). Includes the NaN-fail-fast check shape (lines 229-233): call with `float("nan")`, expect `AssertionError`.

---

### `results/comparison.csv` (generated artifact, batch)

**Analog:** `results/ga_optimized_params.json` (schema-v2 frozen artifact precedent)

Shape precedent (single-line JSON, top-level keys):
```
{"mfs": {...six groups...}, "coupling": {"k_heat": ..., "k_vent": ...},
 "fitness": ..., "weights": {"w1": 1.0, "w2": 1.0, "w3": 0.01},
 "train_weather": ..., "train_seed": 7, "holdout_seed": 21, ...,
 "schema_version": 2, "history": {...}}
```
Apply: CSV analog of the frozen-schema contract — `COLUMNS` header is frozen (Phase-6 notebooks + Phase-7 dashboard read it); 8 data rows (4 controllers × 2 weathers); never hand-written, only produced by `compare()`; committed to git like the JSON artifact. CSV dialect precedent: `src/weather_profile_generator.py` lines 25-26 writes header `time_min,temp_C,rh_pct` via `np.savetxt(..., header=..., comments="", fmt=...)` — for comparison.csv prefer `csv.DictWriter` (explicit header contract) over `np.savetxt`.

## Shared Patterns

### Fail-fast asserts (input validation)
**Source:** `src/ga_fuzzy_controller.py` lines 83-85; `src/onoff_controller.py` lines 18-24
**Apply to:** every `metrics.py` kernel + `compare()` harness
```python
assert np.isfinite(T_C) and np.isfinite(rh_pct)
assert np.isfinite(T_sp) and np.isfinite(RH_sp)
assert np.isfinite(dt) and dt > 0
```
Kernels assert: histories non-empty, equal length, all finite (`np.all(np.isfinite(...))`); `dt > 0`; setpoints finite. Suite includes a NaN-injection check expecting `AssertionError`.

### Plain-assert suite with `__main__` runner
**Source:** `tests/test_fuzzy_controller.py` lines 1-8 + 236-254; `tests/test_genetic_algorithm.py` lines 1-12
**Apply to:** `tests/test_metrics.py`
Pytest-compatible `test_*` names, imports inside bodies (wave-0 ordering), `sys.path` root-prepend in `__main__`, PASS/FAIL per test, `sys.exit(1)` on failure. No pytest install step — pytest is absent by design.

### Shared controller call signature
**Source:** `src/onoff_controller.py:15`, `src/ga_fuzzy_controller.py:80`
**Apply to:** `compare()` CONTROLLERS table
All four legs share `(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state)` → `(act_dict, state)` with 4-key duties in [0,1]. Parameterize one loop over `[("onoff", onoff_step), ("pid", pid_step), ("fuzzy", fuzzy_step), ("ga_fuzzy", ga_fuzzy_step)]` — never four bespoke loops (Anti-Pattern: drift breaks energy bit-identity).

### Seeded determinism + bit-identical reruns
**Source:** `tests/test_fuzzy_controller.py` lines 226-228 (`run1 == run2`); `src/weather_profile_generator.py` line 18 (`rng = np.random.default_rng(seed)`)
**Apply to:** `compare()` + holdout weather
Score the committed `weather/holdout_21.csv` (frozen holdout, byte-distinct from train) — never regenerate at score time. Two `compare()` runs are bit-identical; suite asserts train-block ≠ holdout-block (wrong-file guard).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | None — all three files have strong in-repo analogs. Overshoot/settling/RMSE/ISE kernel bodies are textbook NumPy (see RESEARCH.md Patterns 2-3) but their surrounding conventions (asserts, imports, harness) come from the analogs above. |

## Metadata

**Analog search scope:** `src/`, `tests/`, `results/`, `weather/` (full repo — 8 source + 4 test files)
**Files scanned:** 12 (7 read: genetic_algorithm.py, test_fuzzy_controller.py, test_genetic_algorithm.py, weather_profile_generator.py, ga_fuzzy_controller.py §37-88, greenhouse_model.py §87-101, onoff_controller.py §1-30; artifact head: ga_optimized_params.json)
**Git-track gate:** all analog paths verified via `git ls-files` (all 8 tracked — no mirror paths emitted)
**Pattern extraction date:** 2026-09-27
