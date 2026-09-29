# Phase 1: Greenhouse Model & Weather — Pattern Map

**Mapped:** 2026-09-20
**Files analyzed:** 6 (5 new files + 1 generated artifact)
**Analogs found:** 0 / 6 — **greenfield phase; these files become the analogs later phases copy from**

> **Context for the planner:** `git ls-files` confirms the repo tracks only `.planning/` documents and `AGENTS.md`. No `src/`, `tests/`, `notebooks/`, or CSV exists. RESEARCH.md (git-tracked) contains a probe-verified reference implementation of everything this phase builds — its transcript (RESEARCH.md §274-308) was run against NumPy 2.4.3 this session. **Use RESEARCH.md excerpts below as the copy-source; line cites are verbatim against the committed file.**

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/greenhouse_model.py` | model | batch / transform (pure stateless step; loads+interps CSV) | none — first module in repo | no analog (greenfield) |
| `src/weather_profile_generator.py` | utility | file-I/O (CSV write) + transform | none — first module in repo | no analog (greenfield) |
| `src/__init__.py` | config (package marker) | — | none | no analog (greenfield) |
| `tests/test_greenhouse_model.py` | test | batch | none — first test file in repo | no analog (greenfield) |
| `notebooks/01_greenhouse_model.ipynb` | notebook (proof) | batch / visualization | none — first notebook (PROOF-01 milestone 1) | no analog (greenfield) |
| `weather_profile.csv` | data (generated artifact) | file-I/O (written once by generator, D-12) | none — do NOT hand-write; produced by generator | no analog (generated) |

**Pattern source for all files:** `.planning/phases/01-greenhouse-model-weather/RESEARCH.md` (tracked, probe-verified).

---

## Pattern Assignments

### `src/greenhouse_model.py` (model, batch/transform)

**Analog:** none. **Copy from:** RESEARCH.md §"Pattern 1: Coupled Energy + Moisture ODE" (lines 158-210), §"Common Operation 2" (lines 310-323).

**Imports pattern** (derived from RESEARCH.md lines 88-92, 236 — the locked stack; only NumPy):
```python
import numpy as np
```
No scipy, no other imports. `matplotlib` is for notebooks only — never inside `src/`.

**Module-level named-parameter dict** (D-07, RESEARCH.md lines 171-184 — copy verbatim, units in comments):
```python
params = {                          # D-07 named dict — all values probe-verified
    "C_vol": 1.8e4,                 # J/(m3·K) effective volumetric heat capacity (air+structure)
    "U_env": 5.0,                   # W/(m3·K) envelope conduction (≈8 W/m2K glass, A/V≈0.7)
    "P_h":   100.0,                 # W/m3    heater sensible heat at duty 1.0
    "P_fan": 200.0,                 # W/m3    fan/cooler heat extraction at duty 1.0
    "P_fog": 20.0,                  # W/m3    fogger evaporative cooling at duty 1.0
    "m_fog": 7.4e-3,                # g/(kg·s) fogger moisture injection (≈0.44 g/kg/min)
    "ACH":   4.5,                   # air changes/hour — natural vent exchange rate
    "L_v":   1.508,                 # W/(m3·K) vent sensible exchange = rho·cp·ACH/3600
    "X_v":   1.25e-3,               # 1/s      vent moisture exchange = ACH/3600
    "E_base": 2.5e-3,               # g/(kg·s) base transpiration + floor evaporation (no crop)
    "k_c":   1.5e-4,                # 1/s      cooler condensation dehumidification (w>wsat only)
    "A_sol": 100.0,                 # W/m3     daytime solar gain peak, 06:00–18:00 [ASSUMED addition]
}
```

**Saturation + RH helpers** (D-03/D-16, RESEARCH.md lines 313-320 — copy verbatim):
```python
def es_pa(T_C):                                    # Pa
    return 610.94 * np.exp(17.625 * T_C / (T_C + 243.04))

def wsat_g_per_kg(T_C, p_Pa=101325.0):             # g/kg
    return 622.0 * es_pa(T_C) / (p_Pa - es_pa(T_C))

def relative_humidity(w_g_per_kg, T_C):            # %  (D-16 helper)
    return 100.0 * w_g_per_kg / wsat_g_per_kg(T_C)
```

**Core ODE pattern** (RESEARCH.md lines 186-200 — derivative functions + stateless step; the step skeleton's state-passing must be completed so the caller owns T/w per D-15):
```python
def dT_dt(T, w, u, T_out, sol):
    u_h, u_c, u_f, u_v = u
    return (params["P_h"]*u_h - params["P_fan"]*u_c - params["P_fog"]*u_f + sol
            + (params["U_env"] + params["L_v"]*u_v) * (T_out - T)) / params["C_vol"]

def dw_dt(T, w, u, w_out):
    u_h, u_c, u_f, u_v = u
    cond = params["k_c"] * u_c * max(w - wsat(T), 0.0)          # condensation only when supersaturated
    return (params["E_base"] + params["m_fog"]*u_f
            + params["X_v"]*u_v * (w_out - w) - cond)

def step(dt, u, weather_at_t):        # D-15 pure/stateless; caller owns state
    T_out, w_out, sol = weather_at_t
    ...
    # one forward-Euler step, then clamp w <= wsat(T) (excess condenses)
```

**Key physics rules (do not deviate):**
- Heater has **NO moisture term** — drying is emergent via RH = w/wsat(T)·100 (RESEARCH.md Pitfall 4, lines 258-261). `dw` from heater = 0.
- Fan/cooler = **active heat extraction** `−P_fan·u_c` + condensation dehumidification only when supersaturated (`max(w − wsat, 0)`), NOT a vent-style exchange (Pitfall 5, lines 264-267).
- Clamp `w = min(w, wsat(T))` after each Euler step (Pitfall 2, line 249) — RH must never exceed 100%.
- Duty → rate is **linear** (D-06): `effect = rate · duty`, no deadband/min-turn-on (line 222).

**Validation / error handling:** fail-fast asserts, no try/except (see Shared Patterns below). Gate on Euler stability when dt is overridable: `assert (params["X_v"] + params["k_c"])*dt < 1` (RESEARCH.md line 243).

**Weather loading:** `np.loadtxt(..., dtype=float)` + asserts (monotonic time, endpoints 0..1440, RH∈[0,100], finite), linear interpolation with `numpy.interp` (RESEARCH.md lines 255-256, 434-442).

---

### `src/weather_profile_generator.py` (utility, file-I/O + transform)

**Analog:** none. **Copy from:** RESEARCH.md §"Pattern 2: Seedable Weather Generator" (lines 212-218), §"Common Operation 3" (lines 325-340).

**Core generation pattern** (RESEARCH.md lines 328-339 — copy verbatim, the probe-consistent backbone; D-11 anti-correlation built in):
```python
def generate_weather_profile(out_path, seed=7, t_mean=20.0, t_amp=6.0,
                             rh_mean=65.0, rh_amp=18.0, t_peak_h=15.0,
                             duration_h=24.0, interval_min=15):
    rng = np.random.default_rng(seed)
    t_min = np.arange(0, int(duration_h*60) + 1, interval_min, dtype=int)  # 0..1440
    t_h   = t_min / 60.0
    phase = 2*np.pi*(t_h - t_peak_h)/24.0
    T_out = t_mean + t_amp*np.sin(phase) + rng.normal(0, 0.5, t_h.size)     # mild noise
    RH    = np.clip(rh_mean - rh_amp*np.sin(phase) + rng.normal(0, 3.0, t_h.size), 30, 95)  # D-11 anti-correlated
    np.savetxt(out_path, np.column_stack([t_min, T_out, RH]),
               header="time_min,temp_C,rh_pct", comments="", fmt=["%d", "%.2f", "%.2f"])
    return out_path
```

**Conventions:**
- Time column = **integer minutes, 0..1440 inclusive** (97 rows at 15-min; divides evenly into dt=60s) — RESEARCH.md line 218. Never float/hours (Pitfall 3).
- Seeding = `np.random.default_rng(seed)` per call — never module-global `np.random.seed()` (D-12, line 233-234).
- `output_path` is a parameter → CSV location (root vs `weather/`) stays a planning-time/plan choice (RESEARCH.md lines 374-376). No hardcoded path in the function.
- Generator is **committed in `src/`**; CSV is the reproducible artifact (D-12).

---

### `tests/test_greenhouse_model.py` (test, batch)

**Analog:** none (no `tests/` exists; `conftest.py` explicitly NOT needed — RESEARCH.md line 420). **Copy from:** RESEARCH.md §"Validation Architecture" (lines 392-420) + probe transcript asserts (lines 274-308).

**Framework pattern** (RESEARCH.md lines 396-399, 418-420): plain-assert module, pytest-compatible naming, standalone runner — pytest is NOT installed:
```python
def test_<behavior>():
    # plain asserts, zero deps
    assert ...

if __name__ == "__main__":
    # call every test_* function, print PASS/FAIL, exit nonzero on failure
```

**Assertion basis — the 7 checks (VALIDATION.md lines 48-56), expected values from the probe (RESEARCH.md lines 276-308):**

| Check | Assertion source (probe output, line refs) |
|-------|--------------------------------------------|
| MODEL-01 coupling directions | heater ↑T/dw=0/RH↓; fan ↓T; fogger ↓T↑w; vent → ambient both (299-302) |
| MODEL-01 bounded/finite/positive 24h | T∈[16.8,35.8] C, w∈[11.0,38.3] g/kg, RH∈[44,100]%, `np.all(np.isfinite(...))` (304-306) |
| MODEL-01 steady-state settles | \|dT\|<ε, \|dw\|<ε at fixed weather (line 407) |
| MODEL-02 duty linearity | effect at 50% = half of 100% (D-06; probe dt-sweep shows linear scaling, 288-294) |
| MODEL-03 CSV load+interp | known sine CSV reproduces T_out at midpoints within tol (409-410) |
| MODEL-03 seedability | two runs same seed → identical rows (line 410) |
| MODEL-04 API contract | `step(dt, actuators, weather) -> (T, w)` tuple; 2 calls, no state leak (line 411) |

---

### `src/__init__.py` (config, package marker)

**Analog:** none — greenfield. **Pattern:** empty file or single docstring line (e.g. `"""Greenhouse climate simulation core."""`). Exists so later phases import `from src.greenhouse_model import step` (PROJECT.md line 46: controllers live in `src/`, notebooks import them).

---

### `notebooks/01_greenhouse_model.ipynb` (notebook, batch/visualization)

**Analog:** none — this is milestone-1 of the PROOF trail (PROOF-01). **Pattern to set (copied by notebooks 2-6 in Phase 6):**
- Imports: `import numpy as np; import matplotlib.pyplot as plt`, plus `from src.greenhouse_model import step, params` etc.
- **No duplicated logic** — notebooks call `src/` functions only (PROJECT.md lines 56, 65; no inline re-implementation of es/wsat/step).
- Trace plots: T and w/RH vs time over the default 24h @ dt=60s (D-14), with outdoor weather overlaid.

---

### `weather_profile.csv` (data, generated artifact)

**Analog:** none — **not hand-written.** Produced once by `src/weather_profile_generator.py` (D-12) and committed. Header `time_min,temp_C,rh_pct`; integer minutes 0..1440; 15-min rows (RESEARCH.md lines 218, 338). Location (root vs `weather/`) is the planner's call — the generator's `output_path` argument makes either work.

---

## Shared Patterns

### Imports / dependency policy
**Source:** RESEARCH.md lines 68-95, 236. **Apply to:** all `src/` and `tests/` files. Only `import numpy as np`. No scipy, no pytest, no new deps this phase — Matplotlib confined to notebooks. `import numpy, matplotlib` version check: 2.4.3 / 3.10.8 already installed.

### Determinism / seeding
**Source:** RESEARCH.md lines 233-234, 331. **Apply to:** generator + tests. `rng = np.random.default_rng(seed)` per call — never global `np.random.seed()`. Same seed → identical output (asserted in tests).

### Named-parameter dict (D-07)
**Source:** RESEARCH.md lines 171-184. **Apply to:** `greenhouse_model.py` (and by convention all later controllers/GA). All physical coefficients live in the module-level `params` dict with units in comments — later phases tune/GA-optimize by editing the dict, not the code.

### Pure, stateless API (D-15/D-16)
**Source:** RESEARCH.md lines 197-200. **Apply to:** model module. `step(dt, actuators, weather_at_t) -> (temp_C, humidity_g_per_kg)` — state owned by the caller; returns both absolute humidity and %RH (via `relative_humidity`) so controllers/dashboard/notebooks never re-derive conversions (no duplicated logic, PROJECT.md line 65).

### Error handling = fail-fast asserts + physical clamps (NO try/except)
**Source:** RESEARCH.md lines 243, 249, 255-256, 434-442. **Apply to:** model + generator + tests. This is pure local numerics — there is no exception-handling pattern in this codebase and none should be invented:
- `assert` on CSV load: numeric dtype (`np.loadtxt(dtype=float)`), time strictly increasing with endpoints 0..1440, RH∈[0,100], finite — fail fast with a clear message.
- Gate overridable dt: `assert (X_v + k_c)*dt < 1` (Euler non-oscillatory bound, dt_crit ≈ 714s; locked 60s has 12× margin).
- Physical clamp: `w = min(w, wsat(T))` after each step (excess condenses).
- Sanity asserts in tests: `np.all(np.isfinite(...))`, positivity, boundedness.

### Test runner pattern
**Source:** RESEARCH.md lines 392-399, 418-420. **Apply to:** the one test file; also the standard for all later phases (pytest never assumed). `def test_*()` + `if __name__ == "__main__":` runner invoking each test and exiting nonzero on failure. Run via `python tests/test_greenhouse_model.py` (< 5s), after every task commit, wave merge, and before `/gsd-verify-work` (VALIDATION.md lines 30-36).

### Module docstring & unit annotation convention
**Source:** RESEARCH.md lines 171-184 (units inline) + CONTEXT.md D-02 (literature defaults, documented). **Apply to:** all `src/` modules. Every parameter carries its unit in a trailing comment; every function documents its return units (°C, g/kg, %).

---

## No Analog Found

Files with no close match (planner uses RESEARCH.md patterns per row above):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/greenhouse_model.py` | model | batch/transform | No source code exists in repo; RESEARCH.md Pattern 1 (158-210) is the probe-verified reference |
| `src/weather_profile_generator.py` | utility | file-I/O | Same — copy Common Op 3 (325-340) |
| `src/__init__.py` | config | — | Trivial package marker; no prior package |
| `tests/test_greenhouse_model.py` | test | batch | No tests exist; probe transcript (274-308) supplies the expected numeric bounds |
| `notebooks/01_greenhouse_model.ipynb` | notebook | visualization | First of six milestone notebooks (PROOF-01) |
| `weather_profile.csv` | data | file-I/O | Generated artifact (D-12) — never patterned, never hand-written |

**Consequence:** Phase 1 files become the codebase's first analogs. All contracts set here (stateless `step()` signature, `params` dict, plain-assert runner, no-duplicated-logic) are what Phases 2-7 will be mapped against.

---

## Metadata

**Analog search scope:** repo root (`git ls-files` full index; 0 source files tracked — only `.planning/` + `AGENTS.md`)
**Files scanned:** 10 (all tracked)
**Pattern extraction date:** 2026-09-20
**Gate check (#3645):** pattern source RESEARCH.md is git-tracked (`git ls-files` non-empty); no mirror/install paths emitted. The session probe script (`probe_greenhouse.py`) is NOT in the repo — its output is preserved verbatim in the tracked RESEARCH.md transcript (§274-308), which is the compliant reference.