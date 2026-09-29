# Phase 04: GA Optimization - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 6 (5 new files + 1 new dir artifact; `results/` dir bootstrap)
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/genetic_algorithm.py` | service (optimizer) | batch | `src/fuzzy_controller.py` + `tests/test_fuzzy_controller.py::_run_closed_loop` | role-match |
| `src/ga_fuzzy_controller.py` | controller | request-response | `src/pid_controller.py` | exact |
| `tests/test_genetic_algorithm.py` | test | batch (tiny-budget smoke) | `tests/test_fuzzy_controller.py` | exact |
| `results/ga_optimized_params.json` | config (artifact) | file-I/O | `weather/weather_profile.csv` via `src/weather_profile_generator.py` | data-flow-match |
| `notebooks/04_ga_optimization.ipynb` + PNG | notebook (proof) | batch (plot-from-artifact) | `notebooks/03_fuzzy.ipynb` | exact |
| `results/` directory | config (dir bootstrap) | file-I/O | none needed — `mkdir -p` in `run_ga` | no-analog (trivial) |

All analog paths verified git-tracked via `git ls-files` this session (no mirror paths).

## Pattern Assignments

### `src/genetic_algorithm.py` (service/optimizer, batch)

**Analog:** `src/fuzzy_controller.py` (MF structures, injection point) + `tests/test_fuzzy_controller.py` lines 11-30 (fitness harness shape)

**Imports pattern** (`src/fuzzy_controller.py` line 16; test harness lines 12-14):
```python
import numpy as np
# fitness body imports (copy verbatim from tests/test_fuzzy_controller.py:12-14):
from src.greenhouse_model import (step, load_weather_profile,
                                  daytime_solar, params,
                                  relative_humidity, wsat_g_per_kg)
from src.fuzzy_controller import fuzzy_step
```

**Core pattern 1 — chromosome dim + injection point** (`src/fuzzy_controller.py` lines 20-29, 63):
```python
FUZZY_MFS = {
    "eT":  {"centers": np.array([-4., -2., 0., 2., 4.]),       "widths": np.full(5, 2.0)},
    "deT": {"centers": np.array([-0.5, -0.25, 0., 0.25, 0.5]), "widths": np.full(5, 0.25)},
    "du":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},
    "eH":  {"centers": np.array([-30., -15., 0., 15., 30.]),   "widths": np.full(5, 15.0)},
    "deH": {"centers": np.array([-6., -3., 0., 3., 6.]),       "widths": np.full(5, 3.0)},
    "dv":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},
}
def fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, mfs=FUZZY_MFS):
```
60-D layout = 6 keys × (5 centers + 5 widths); fixed decode order `["eT","deT","du","eH","deH","dv"]`. `decode()` must allocate fresh dicts/arrays (`np.array(...)` copies) — module docstring lines 11-13 mandate `FUZZY_MFS` read-only ("never mutated — Phase 4 GA passes mutated copies").

**Core pattern 2 — fitness harness** (`tests/test_fuzzy_controller.py` lines 11-30, copy loop then add IAE/energy):
```python
def _run_closed_loop(np, controller_step, n=1440, T_sp=25.0, RH_sp=70.0):
    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    hours = np.arange(0, n) / 60.0
    T_out_hr = np.interp(hours, t_min, T_out)
    w_out_hr = np.interp(hours, t_min, w_out)
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st = None
    ...
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = controller_step(T, rh, T_sp, RH_sp, st)
        wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, wx, T, w)
```
Fitness = same loop with `fuzzy_step(..., mfs=decode(chrom))`, accumulating `IAE_T = Σ|T−T_sp|/60`, `IAE_H = Σ|RH−RH_sp|/60`, `E = Σ Σ_actuators duty/60`, returning `1.0*IAE_T + 1.0*IAE_H + 0.01*E`. Wrap body in `try/except → return float("inf")` (Pitfall 4: asserts in `fuzzy_step`/`step` fail-fast; never let fitness raise).

**Repair pattern** (derived from `src/fuzzy_controller.py` lines 40-48): per-group `np.sort(np.clip(centers, lo, hi))`, `np.clip(widths, w_min, w_max)` with `w_min > 0` — because `tri()` divides by `w` (line 42: `1.0 - abs(float(x) - c) / w`) and `infer()` clips to `[EC[0], EC[-1]]` (lines 47-48), so zero widths raise and unsorted centers corrupt the interval.

**RNG pattern** (`src/weather_profile_generator.py` line 18): `rng = np.random.default_rng(seed)` owned by `run_ga`; all operator draws through it; never `np.random.*` globals. Init: individual 0 = exact hand encoding, rest = hand × (1 + U(−0.2, 0.2)) then repaired.

**Error handling pattern:** fail-fast asserts on inputs (`fuzzy_step` lines 65-70 style), `try/except → inf` only at the fitness boundary, `np.isfinite` assert on cost before return.

---

### `src/ga_fuzzy_controller.py` (controller, request-response)

**Analog:** `src/pid_controller.py` (exact: dual-loop controller, caller-owned state, module docstring convention)

**Imports pattern** (`src/pid_controller.py` line 13):
```python
import numpy as np
import json  # addition: artifact load (stdlib, JSON-only per Security)
```

**Module + signature pattern** (`src/pid_controller.py` lines 1-11, 19-24):
```python
def pid_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, gains=GAINS):
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    st = {...} if state is None else state
    for k in (...):
        assert k in st, f"state missing key {k!r}"
```
Copy exactly: `ga_fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0)` with the same asserts/state-guard shape (`{'pT','pH','uT','uH'}` keys per `fuzzy_controller.py` lines 68-70), same actuator emission contract (`{'heater','fan_cooler','fogger','vent'}` duties in [0,1], `fuzzy_controller.py` lines 87-89).

**Core pattern — thin wrapper:** `load_optimized_mfs(path)` validates (exact key set `{"eT","deT","du","eH","deH","dv"}`, len-5 float lists, widths > 0, all finite — fail-fast asserts), converts lists → `np.array`, caches module-level lazily; `ga_fuzzy_step` delegates to `fuzzy_step(T_C, rh_pct, T_sp, RH_sp, state, dt, mfs=_MFS)`. Must be bit-identical to `fuzzy_step(mfs=…)` (test asserts this).

**Validation pattern** (`src/pid_controller.py` lines 27-28): `for k in (...): assert k in gains, f"gains missing key {k!r}"` — same shape for JSON key/length validation.

---

### `tests/test_genetic_algorithm.py` (test, batch)

**Analog:** `tests/test_fuzzy_controller.py` (exact)

**File-header pattern** (lines 1-8):
```python
"""Plain-assert sanity suite for ... .

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_genetic_algorithm.py
"""
```

**Harness pattern** (lines 11-30): copy `_run_closed_loop` verbatim (or import the fitness that embeds it); in-body imports (`from src...` inside each `test_*`) so wave-0 ordering works.

**Runner pattern** (lines 236-254): copy the `__main__` block verbatim — `sys.path.insert(0, ...dirname(dirname(abspath)))`, sorted `test_*` discovery, PASS/FAIL prints, `sys.exit(1)` on failure.

**Assertion style:** plain `assert` with diagnostic tuples (e.g. line 39: `assert act["heater"] > 0.0 ..., act`); NaN-guard idiom lines 229-233 (`try: fn(nan,...); raise SystemExit(...) except AssertionError: pass`); determinism idiom lines 226-228 (two short runs bit-identical); regression-guard idiom — snapshot hand `FUZZY_MFS` arrays before GA smoke, assert bit-identical after (anti-aliasing proof, Pitfall 5).

**Required tests** (per RESEARCH Validation Architecture): `test_encode_decode_roundtrip`, `test_decode_repair_invariants`, `test_fitness_matches_hand_cost`, `test_fitness_never_raises`, `test_tiny_ga_monotonic` (pop 4 × gen 2, best never worsens, <30 s), `test_json_schema`, `test_hand_mfs_untouched`. Keep tiny-budget smoke <30 s.

---

### `results/ga_optimized_params.json` (config artifact, file-I/O)

**Analog:** `weather/weather_profile.csv` generation path — `src/weather_profile_generator.py` lines 15-27 (`generate_weather_profile(out_path, seed=...)` + `default_rng(seed)` + atomic write).

**Pattern:** producer-owned seeded write; consumer treats artifact as immutable input. `run_ga` must `os.makedirs("results", exist_ok=True)` before write (dir does not exist yet) and flush best-so-far + history every generation (killed 25-min run still yields an artifact). Schema (frozen for Phase 5/7 consumers):
```json
{"mfs": {"eT": {"centers": [...5...], "widths": [...5...]}, "deT": {...}, "du": {...}, "eH": {...}, "deH": {...}, "dv": {...}},
 "fitness": 0.0, "weights": {"w1": 1.0, "w2": 1.0, "w3": 0.01},
 "train_weather": "weather/weather_profile.csv", "train_seed": 7, "holdout_seed": 21,
 "population": 50, "generations": 50, "rng_seed": 0,
 "history": {"best": [...50...], "mean": [...50...]}}
```
JSON-only via stdlib `json` — never pickle/eval (Security). `train_seed`/`holdout_seed`/`rng_seed` recorded in-artifact (repudiation guard).

---

### `notebooks/04_ga_optimization.ipynb` + PNG (notebook proof, batch)

**Analog:** `notebooks/03_fuzzy.ipynb` — 6 cells (markdown title / imports / weather-load / closed-loop def / honest-note markdown / plot-and-save).

**Imports pattern** (cell 1): `matplotlib.use("Agg")` headless before `pyplot`; `from src.greenhouse_model import step, load_weather_profile, daytime_solar, params, relative_humidity, wsat_g_per_kg`; `from src.weather_profile_generator import generate_weather_profile`; controller imports from `src/`.

**Weather pattern** (cell 2): `if not os.path.exists(CSV): generate_weather_profile(CSV, seed=7)` — train weather never regenerated; holdout generated once via `generate_weather_profile(holdout_path, seed=21)` on an isolated path never passed to fitness (anti-leakage), only at proof time.

**Loop pattern** (cell 3): `run_closed_loop(controller_step)` with `T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)`, `st = None`, per-step `relative_humidity` → controller → `step(60.0, ...)`; setpoints as function args.

**Critical constraint (Pitfall 2):** evolution must NOT run in a notebook cell (~25 min). Notebook loads `results/ga_optimized_params.json` + history and plots only: convergence curve (best/mean per gen), holdout 4-controller traces (GA vs on/off vs PID vs hand fuzzy on fresh seed), MF before/after. Script entry `python src/genetic_algorithm.py` writes the artifacts the notebook reads. PNG committed alongside (Phases 1-3 precedent: `03_fuzzy.png`).

---

## Shared Patterns

### Seeded determinism (D-12)
**Source:** `src/weather_profile_generator.py:18` — `rng = np.random.default_rng(seed)`; test idiom `tests/test_fuzzy_controller.py:226-228` (two runs bit-identical)
**Apply to:** `src/genetic_algorithm.py` (single `default_rng(rng_seed)` owned by `run_ga`), holdout generation, all tests
```python
rng = np.random.default_rng(seed)
```

### Fail-fast validation
**Source:** `src/greenhouse_model.py:62-67` (actuator key/set + duty bounds asserts); `src/pid_controller.py:25-28` (state/gains key guards); `src/fuzzy_controller.py:65-70`
**Apply to:** `decode` inputs, `load_optimized_mfs` schema check, `ga_fuzzy_step` args, fitness cost finiteness
```python
assert set(actuators) == expected, f"actuator keys must be exactly {expected}"
for duty in actuators.values():
    assert 0.0 <= duty <= 1.0, "actuator duties must lie in [0, 1]"
```

### Controller signature + emission contract
**Source:** `src/pid_controller.py:19` + `:43-44`; `src/fuzzy_controller.py:87-89`
**Apply to:** `src/ga_fuzzy_controller.py::ga_fuzzy_step`
```python
def ga_fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0): ...
heat, cool = (u, 0.0) if u > 0 else (0.0, -u)  # split-range, never both
return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)
```

### Test standalone convention
**Source:** `tests/test_fuzzy_controller.py:1-8` + `:236-254`; `tests/test_baseline_controllers.py` identical
**Apply to:** `tests/test_genetic_algorithm.py`
In-body imports, `test_*` plain asserts, `__main__` runner with root-prepend, `python tests/test_X.py` invocation, no pytest.

### Pass criterion is relative, never absolute
**Source:** RESEARCH §Pattern 2 scale table (humidity ~99% of locked-weight cost; hand fuzzy 641.5 loses to on/off 502.7 on train weather)
**Apply to:** test asserts + notebook verdict — `cost(GA) < cost(onoff)` on shared holdout weather with per-term breakdown (IAE_T, IAE_H, E); no absolute cost threshold anywhere.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `results/` directory bootstrap | config | file-I/O | Trivial — `os.makedirs("results", exist_ok=True)` in `run_ga`; no pattern to copy |
| GA operators (tournament-3, BLX-0.5, Gaussian mutation, elitism-2) | service-subroutine | batch | No optimizer exists in-repo; use RESEARCH.md Code Examples operator snippets (Eshelman & Schaffer BLX-α structure) |

## Metadata

**Analog search scope:** `src/`, `tests/`, `notebooks/`, `weather/` (repo root listing); git-tracked verification via `git ls-files`
**Files scanned:** 8 tracked source files (5 `src/` controllers/model/generator + 2 `tests/` suites + 1 notebook structure dump)
**Pattern extraction date:** 2026-09-27
