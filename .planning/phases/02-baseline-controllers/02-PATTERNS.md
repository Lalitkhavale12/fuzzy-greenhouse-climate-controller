# Phase 2: Baseline Controllers - Pattern Map

**Mapped:** 2026-09-21
**Files analyzed:** 4 (2 new src modules, 1 test file, 1 notebook + PNG)
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/onoff_controller.py` | service (control law) | request-response (pure step fn) | `src/greenhouse_model.py` | role-match |
| `src/pid_controller.py` | service (control law) | request-response (pure step fn) | `src/greenhouse_model.py` | role-match |
| `tests/test_baseline_controllers.py` | test | batch (24 h loop assertions) | `tests/test_greenhouse_model.py` | exact |
| `notebooks/02_baselines.ipynb` (+ `02_baselines.png`) | notebook (proof) | batch (closed-loop trace + plot) | `notebooks/01_greenhouse_model.ipynb` | exact |

Match-quality note: no existing controller module exists yet, so both `src/` files match on the closest role (pure/stateless NumPy module with caller-owned state) rather than same-role. Test and notebook matches are exact (same conventions, same harness shape).

## Pattern Assignments

### `src/onoff_controller.py` (service, request-response)

**Analog:** `src/greenhouse_model.py` (git-tracked ✓)

**Module-docstring pattern** (lines 1-12):
```python
"""Simulated greenhouse plant — coupled energy + moisture ODEs (MODEL-01).

Verbatim-core copy of RESEARCH.md Pattern 1 (probe-verified 2026-09-20,
numpy 2.4.3). State: T (degC), w (g/kg absolute humidity), per m3 of
...
Pure and stateless (D-15): the caller owns the state and passes it in/out —
the same function drives the controllers, the GA fitness loop, and the
notebooks, with no duplicated logic (PROJECT.md).
"""
```

**Imports pattern** (line 14):
```python
import numpy as np
```

**Constants-as-dict pattern** (lines 16-29): named `params` dict with one-line inline comments per key, values probe-verified:
```python
params = {                          # D-07 named dict — all values probe-verified
    "C_vol": 1.8e4,                 # J/(m3·K) effective volumetric heat capacity (air+structure)
    "U_env": 5.0,                   # W/(m3·K) envelope conduction (≈8 W/m2K glass, A/V≈0.7)
    ...
}
```
Copy for: hysteresis band defaults — either a `DEFAULTS`/`BANDS` dict at module top or keyword defaults (`band_T=0.5, band_RH=3.0` per RESEARCH.md Pattern 1 lines 141-142). Use plain floats, no dataclass.

**Fail-fast asserts pattern** (lines 62-67, 82-83):
```python
expected = {"heater", "fan_cooler", "fogger", "vent"}
assert set(actuators) == expected, f"actuator keys must be exactly {expected}"
for duty in actuators.values():
    assert 0.0 <= duty <= 1.0, "actuator duties must lie in [0, 1]"
...
assert np.isfinite(T_new) and np.isfinite(w_new)
```
Copy for: validate `T_C`, `rh_pct`, setpoints with `assert np.isfinite(...)` at entry (RESEARCH.md Security V5); output duties are 0.0/1.0 literals so they satisfy the plant assert by construction — no clip needed here but keep the literal-only discipline.

**Pure/stateless signature pattern** (line 55): `def step(dt, actuators, weather_at_t, T_C, w_gkg):` — caller owns all state, returns new values, zero module-level mutable state.
Copy for (verbatim from RESEARCH.md Pattern 1, lines 141-156):
```python
def onoff_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None,
               band_T=0.5, band_RH=3.0):
    """Hysteresis on/off. state = {'heat': bool, 'cool': bool, 'fog': bool}."""
    st = {'heat': False, 'cool': False, 'fog': False} if state is None else state
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    if eT > band_T:      st['heat'] = True     # too cold -> full heat
    elif eT < -0.2:      st['heat'] = False    # slight overshoot releases
    if eT < -band_T:     st['cool'] = True     # too hot -> full cool + vent
    elif eT > 0.2:       st['cool'] = False
    if eH > band_RH:     st['fog'] = True      # too dry -> full fog
    elif eH < -1.0:      st['fog'] = False
    out = {'heater': 1.0 if st['heat'] else 0.0,
           'fan_cooler': 1.0 if st['cool'] else 0.0,
           'fogger': 1.0 if st['fog'] else 0.0,
           'vent': 1.0 if st['cool'] else 0.0}   # D-01: vent follows T
    return out, st
```
Key rules: `state=None` → fresh dict inside (never mutable default — Pitfall 5); mutate-and-return the same dict; setpoints are fn args, not baked in (D-04); RH read via shared `relative_humidity()` import, never re-derived.

**Helper-function pattern** (lines 32-52): small pure helpers (`es_pa`, `wsat_g_per_kg`, `relative_humidity`, `daytime_solar`) with one-line docstrings above the main entry point.
Copy for: no extra helpers needed in on/off; if a latch helper is added, keep it private and pure.

---

### `src/pid_controller.py` (service, request-response)

**Analog:** `src/greenhouse_model.py` (git-tracked ✓)

**Imports pattern** (line 14): `import numpy as np` — NumPy only, no scipy/control dependency (RESEARCH.md Alternatives Considered: rejected).

**Constants-as-dict pattern** (lines 16-29): same `params`-dict style.
Copy for (verbatim from RESEARCH.md Pattern 2, lines 177-178):
```python
GAINS = {'Kp_T': 0.3, 'Ki_T': 0.03, 'Kd_T': 0.0,   # per degC
         'Kp_H': 0.03, 'Ki_H': 0.004, 'Kd_H': 0.0}  # per %RH
```
Default-arg style: `def pid_step(..., dt=60.0, gains=GAINS)` — note `GAINS` as default is read-only in the body (never mutated; per-key reads only), so the mutable-default hazard does not apply; `state` still uses `None` → fresh dict.

**Core PID pattern** (verbatim from RESEARCH.md Pattern 2, lines 180-196):
```python
def pid_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, gains=GAINS):
    st = {'iT': 0.0, 'pT': None, 'iH': 0.0, 'pH': None} if state is None else state
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / dt
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / dt
    st['pT'], st['pH'] = eT, eH
    u_raw = gains['Kp_T']*eT + gains['Ki_T']*st['iT'] + gains['Kd_T']*dT
    # conditional integration: freeze T integrator when saturated pushing further
    if not ((u_raw > 1.0 and eT > 0) or (u_raw < -1.0 and eT < 0)):
        st['iT'] += eT * dt
    u = float(np.clip(gains['Kp_T']*eT + gains['Ki_T']*st['iT'] + gains['Kd_T']*dT, -1.0, 1.0))
    v_raw = gains['Kp_H']*eH + gains['Ki_H']*st['iH']
    if not (v_raw > 1.0 and eH > 0):
        st['iH'] += eH * dt
    v = float(np.clip(gains['Kp_H']*eH + gains['Ki_H']*st['iH'], 0.0, 1.0))
    heat, cool = (u, 0.0) if u > 0 else (0.0, -u)   # split-range, never both
    return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)
```
Copy rules: `np.clip` every output every call (Pitfall 6 — unclipped duties crash `step()` lines 64-65); split-range by sign guarantees heater/cooler mutual exclusion; `Kd=0` defaults (Pitfall 4 — no D-on-error on noisy RH); conditional integration, not clamping alone (Pitfall 2 — clamping without the freeze still leaves stale integral, probe IAE 3.7→1.0).

**Fail-fast asserts pattern** (`src/greenhouse_model.py` lines 62-65, 82): same as on/off — `assert np.isfinite(...)` on `T_C`/`rh_pct`/setpoints at entry; output keys exactly the 4-actuator set.

**Module-docstring pattern** (lines 1-12): same shape — one-line purpose + decision refs (BASE-02, D-05) + pure/stateless note. Also import `relative_humidity` from the plant module for any RH conversion — never inline Magnus (RESEARCH.md Don't Hand-Roll).

---

### `tests/test_baseline_controllers.py` (test, batch)

**Analog:** `tests/test_greenhouse_model.py` (git-tracked ✓)

**File-header pattern** (lines 1-9):
```python
"""Plain-assert sanity suite for the simulated greenhouse plant (MODEL-01..04).

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so this file is runnable before src/greenhouse_model.py exists
...
Run:  python tests/test_baseline_controllers.py
"""
```
Copy verbatim shape, retitled to BASE-01..03.

**In-body imports pattern** (lines 19-20, 52, 81, 97): `import numpy as np` and `from src.xxx import ...` live *inside* each `test_*` body, not at module top — keeps the file runnable in wave-0 ordering.
```python
def test_coupling_directions():
    import numpy as np
    from src.greenhouse_model import step, relative_humidity
```

**Loop-helper pattern** (lines 12-15):
```python
def _run_loop(np, step, dt, steps, actuators, weather, T, w):
    for _ in range(steps):
        T, w, _rh = step(dt, actuators, weather, T, w)
    return T, w
```
Copy for: `_run_closed_loop(np, step_fn, ...)` helper per RESEARCH.md Pattern 3 (lines 216-223) — reads `(T, w, RH)`, calls controller → `step()` → appends history; owns plant state AND controller state:
```python
T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
st = None
for i, h in enumerate(hours):
    rh = relative_humidity(w, T)
    act, st = controller_step(T, rh, 25.0, 70.0, st)
    wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
    T, w, rh = step(60.0, act, wx, T, w)
    T_hist.append(T); RH_hist.append(rh); U_hist.append(act)
```

**Weather-load pattern** (lines 54-56, from `test_bounded_finite_positive_24h`):
```python
t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
wx = (np.interp(np.arange(0, 1440, 60), t_min, T_out),
      np.interp(np.arange(0, 1440, 60), t_min, w_out))
```
Copy: same CSV + `np.interp` minute-grid pattern (15-min rows divide evenly into dt=60 s).

**Fail-fast negative-test pattern** (lines 157-167, 180-190): try/except `AssertionError` with `raise SystemExit("<what> did not raise")` inside the try:
```python
try:                                                    # missing key -> fail-fast
    step(60.0, {"heater": 1.0, "fan_cooler": 0.0, "fogger": 0.0}, wx, 25.0, 12.0)
    raise SystemExit("missing-key step() did not raise")
except AssertionError:
    pass
```
Copy for: controller contract checks (8 checks in RESEARCH.md Validation Architecture → Test Map: hysteresis semantics, mutual exclusion, PID signs, anti-windup, P-only ablation, signatures, 24 h integration).

**`__main__` runner pattern** (lines 193-211) — copy verbatim, only the docstring path changes:
```python
if __name__ == "__main__":
    import sys, os
    # "python tests/test_baseline_controllers.py" puts tests/ on sys.path, not the
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
No `conftest.py` — shared harness helper lives inside the test module (RESEARCH.md Wave 0 Gaps).

---

### `notebooks/02_baselines.ipynb` (notebook, batch)

**Analog:** `notebooks/01_greenhouse_model.ipynb` (git-tracked ✓)

**Cell layout** (5 cells, same order — 01 lines 2-102): markdown title → imports → weather → run → plot. New notebook runs the closed-loop harness twice (once per baseline) over the identical 24 h disturbance.

**Imports cell pattern** (01 lines 19-28):
```python
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.greenhouse_model import step, load_weather_profile, daytime_solar, params
from src.weather_profile_generator import generate_weather_profile

print("params:", params)
```
Copy for 02 (verbatim from RESEARCH.md Code Examples, lines 288-293): same Agg-headless header, plus controller imports and RH helpers — no duplicated plant logic:
```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.greenhouse_model import step, load_weather_profile, daytime_solar, params, relative_humidity, wsat_g_per_kg
from src.onoff_controller import onoff_step
from src.pid_controller import pid_step
```

**Weather cell pattern** (01 lines 37-54): regenerate-if-absent + `np.interp` to minute grid:
```python
import os
CSV = "weather/weather_profile.csv"
if not os.path.exists(CSV):
    generate_weather_profile(CSV, seed=7)

t_min, T_out, w_out = load_weather_profile(CSV)
hours = np.arange(0, 1440) / 60.0          # dt = 60 s -> one step per minute
T_out_hr = np.interp(hours, t_min, T_out)
w_out_hr = np.interp(hours, t_min, w_out)
```
Copy verbatim — 02 reuses the identical disturbance; only the `schedule(h)` function is replaced by the two controller calls with separate states per run (Pitfall 5: never share one state dict across both 24 h runs).

**Run cell pattern** (01 lines 63-71): init `(T, w)`, per-minute `step()` loop, append traces, print ranges:
```python
T, w = 29.28, 20.0                  # initial condition (probe-verified baseline)
T_trace, w_trace, rh_trace = [], [], []
for i, h in enumerate(hours):
    ws = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
    T, w, rh = step(60.0, schedule(h), ws, T, w)
    T_trace.append(T); w_trace.append(w); rh_trace.append(rh)
print("T [%.2f, %.2f]  w [%.2f, %.2f]  RH [%.1f, %.1f]" %
      (min(T_trace), max(T_trace), min(w_trace), max(w_trace), min(rh_trace), max(rh_trace)))
```
Copy with `schedule(h)` → controller call per RESEARCH.md Pattern 3 (RH computed via shared helper, setpoints as fn args, history kept loggable as lists of floats/dicts for Phase 5).

**Plot+save pattern** (01 lines 81-100): stacked subplots, `grid(alpha=0.3)`, `suptitle`, `tight_layout()`, `savefig(..., dpi=120)` + `plt.show()`:
```python
plt.figure(figsize=(10, 9))
plt.subplot(3, 1, 1)
plt.plot(hours, T_trace, label="inside T")
...
plt.suptitle("Simulated greenhouse plant - 24h open-loop (vent 25%, heater 80% night, fogger 50% noon)")
plt.tight_layout()
plt.savefig("notebooks/01_greenhouse_model.png", dpi=120)
plt.show()
```
Copy for 02: minimum T-vs-setpoint, RH-vs-setpoint, and duty-stack panels per controller; save to `notebooks/02_baselines.png`, dpi=120, committed alongside the notebook (D-06).

## Shared Patterns

### Caller-owned state (stateless modules)
**Source:** `src/greenhouse_model.py` lines 9-11, 55-61; `src/weather_profile_generator.py` line 18 (`rng = np.random.default_rng(seed)`)
**Apply to:** `src/onoff_controller.py`, `src/pid_controller.py`, and all closed-loop harnesses
- No module-level mutable state; every function takes state in and returns state out.
- `state=None` → fresh dict inside; never a mutable default arg; never reuse one dict across runs (Pitfall 5).
- Determinism check: two runs from `None` must be bit-identical (RESEARCH.md Test Map `test_controller_signatures`).

### Actuator duty-dict contract
**Source:** `src/greenhouse_model.py` lines 62-65 (verbatim, RESEARCH.md lines 302-305)
**Apply to:** both controllers (producers), test integration loop, notebook run cells (consumers)
```python
expected = {"heater", "fan_cooler", "fogger", "vent"}
assert set(actuators) == expected, f"actuator keys must be exactly {expected}"
for duty in actuators.values():
    assert 0.0 <= duty <= 1.0, "actuator duties must lie in [0, 1]"
```
- Exact 4 keys, duties in [0, 1] — the shared structure Phases 3–4 reuse (BASE-03).
- Mutual exclusion: heater and fan_cooler never both > 0 (on/off latch exclusion + PID split-range by sign) — assert in tests.

### Input validation (ASVS V5)
**Source:** `src/greenhouse_model.py` lines 66-67, 82 (`(X_v + k_c)*dt < 1` gate, `np.isfinite` backstop)
**Apply to:** both controller entry points
```python
assert (params["X_v"] + params["k_c"]) * dt < 1, \
    "forward Euler non-oscillatory gate: (X_v + k_c)*dt must be < 1"
...
assert np.isfinite(T_new) and np.isfinite(w_new)
```
- Controllers add `assert np.isfinite(...)` on `T_C`/`rh_pct`/setpoints/state at entry (NaN-poisoning guard, RESEARCH.md Security Domain); plant asserts remain the backstop.

### RH via shared helpers (no duplicated physics)
**Source:** `src/greenhouse_model.py` lines 37-45 (`wsat_g_per_kg`, `relative_humidity` with [0,100] clamp)
**Apply to:** both controllers, test harness, notebook
```python
def relative_humidity(w_g_per_kg, T_C):
    """RH (%) = w/wsat(T)*100, clamped to [0, 100] (D-16; Pitfall 2)."""
    rh = 100.0 * w_g_per_kg / wsat_g_per_kg(T_C)
    return float(min(max(rh, 0.0), 100.0))
```
- PROJECT.md compatibility constraint: notebooks/controllers import from `src/`, never re-derive Magnus.

### Plain-assert test convention (no pytest)
**Source:** `tests/test_greenhouse_model.py` lines 1-9, 193-211
**Apply to:** `tests/test_baseline_controllers.py`
- `def test_*` naming (pytest-compatible), in-body imports, `__main__` runner with `sys.path` prepend; run via `python tests/test_baseline_controllers.py` (< 5 s, short-horizon checks only); wave merge also re-runs `python tests/test_greenhouse_model.py`.

### Proof-notebook convention (Agg headless + committed PNG)
**Source:** `notebooks/01_greenhouse_model.ipynb` cells `imports`/`weather`/`run`/`plot` (lines 13-102)
**Apply to:** `notebooks/02_baselines.ipynb`
- `matplotlib.use("Agg")` before `pyplot` import; weather regenerate-if-absent + `np.interp` minute grid; `savefig("notebooks/02_baselines.png", dpi=120)` + `plt.show()`; headless execute check `jupyter nbconvert --to notebook --execute notebooks/02_baselines.ipynb`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | None — all 4 files have direct analogs. Control-law bodies (hysteresis FSM, positional PID + anti-windup) come from RESEARCH.md session-probe Patterns 1–2, which are probe-verified numerics rather than codebase analogs; the *module shape* around them is covered by `src/greenhouse_model.py` above. |

## Metadata

**Analog search scope:** `src/`, `tests/`, `notebooks/`, `weather/` (full repo — 4 Python files + 1 notebook total; no controllers/services/components directories exist yet)
**Files scanned:** 5 (`src/greenhouse_model.py`, `src/weather_profile_generator.py`, `src/__init__.py`, `tests/test_greenhouse_model.py`, `notebooks/01_greenhouse_model.ipynb`)
**Tracked-source gate (#3645):** all 4 analog paths verified via `git ls-files` — `src/greenhouse_model.py`, `src/weather_profile_generator.py`, `tests/test_greenhouse_model.py`, `notebooks/01_greenhouse_model.ipynb` all tracked; no mirror paths emitted.
**Pattern extraction date:** 2026-09-21
