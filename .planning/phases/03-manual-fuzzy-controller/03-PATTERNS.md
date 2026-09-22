# Phase 3: Manual Fuzzy Controller - Pattern Map

**Mapped:** 2026-09-22
**Files analyzed:** 4 (src/fuzzy_controller.py, tests/test_fuzzy_controller.py, notebooks/03_fuzzy.ipynb, notebooks/03_fuzzy.png)
**Analogs found:** 3 / 3 files with analogs (+ 1 sub-component with no analog: the Mamdani inference core)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/fuzzy_controller.py` | controller | request-response (pure per-step function) | `src/pid_controller.py` | exact |
| `tests/test_fuzzy_controller.py` | test | batch (1440-step closed loop) | `tests/test_baseline_controllers.py` | exact |
| `notebooks/03_fuzzy.ipynb` (+ `03_fuzzy.png`) | component (proof notebook) | batch (closed-loop run + plots) | `notebooks/02_baselines.ipynb` | exact |

All analog paths verified git-tracked via `git ls-files` (2026-09-22). Secondary analogs: `src/onoff_controller.py` (loop-split reference), `src/greenhouse_model.py` (plant contract + RH helpers).

## Pattern Assignments

### `src/fuzzy_controller.py` (controller, request-response)

**Analog:** `src/pid_controller.py` (44 lines, read in full) — dual-loop, same signature shape, same split-range output, same anti-windup discipline. The Mamdani inference core (`tri`/`RULES`/`infer`/centroid) has NO codebase analog — copy it verbatim from RESEARCH.md Patterns 1–3 (see "No Analog Found" below).

**Module docstring pattern** (`src/pid_controller.py` lines 1-11):
```python
"""Dual-loop positional PID baseline controller (BASE-02, D-05).

T-loop output u in [-1, 1] splits by sign (positive -> heater, negative
magnitude -> fan_cooler + vent, never both); RH-loop output v in [0, 1]
drives fogger only (one-sided). Conditional-integration anti-windup freezes
each integrator when its output is saturated pushing further. Kd defaults
to 0 for both loops (lag-dominated, noisy RH).

Pure and stateless: caller owns the state dict; state=None means fresh
{'iT', 'pT', 'iH', 'pH'}. GAINS is module-level read-only (never mutated).
"""
```
Fuzzy module docstring must state the same contract with fuzzy vocabulary: velocity/incremental form, `state = {'pT','pH','uT','uH'}`, `FUZZY_MFS` module-level read-only (never mutated — GA baseline integrity).

**Imports pattern** (`src/pid_controller.py` line 13; `src/onoff_controller.py` line 12):
```python
import numpy as np
```
NumPy-only numerics. No other imports (no scipy, no scikit-fuzzy — rejected per RESEARCH.md).

**Named parameter dict pattern** (`src/pid_controller.py` lines 15-16):
```python
GAINS = {'Kp_T': 0.3, 'Ki_T': 0.03, 'Kd_T': 0.0,   # per degC
         'Kp_H': 0.03, 'Ki_H': 0.004, 'Kd_H': 0.0}  # per %RH
```
Copy as `FUZZY_MFS` with centers/widths arrays per RESEARCH.md Pattern 1 (keys `eT/deT/du/eH/deH/dv`, each `{"centers": np.array([...5...]), "widths": np.full(5, ...)}`). Same role: named, GA-encodable, module-level read-only. Probe-verified starting values in RESEARCH.md 03-RESEARCH.md lines 159-168 (T error ±4 °C, T rate ±0.5 °C/min, RH error ±30 %RH, RH rate ±6 %RH/min, Δu/Δv ±0.1/step).

**Signature + asserts + state pattern** (`src/pid_controller.py` lines 19-28):
```python
def pid_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, gains=GAINS):
    """Positional dual-loop PID. state = {'iT', 'pT', 'iH', 'pH'}."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    st = {'iT': 0.0, 'pT': None, 'iH': 0.0, 'pH': None} if state is None else state
    for k in ('iT', 'pT', 'iH', 'pH'):  # WR-02: fail loud on partial state
        assert k in st, f"state missing key {k!r}"
    for k in ('Kp_T', 'Ki_T', 'Kd_T', 'Kp_H', 'Ki_H', 'Kd_H'):
        assert k in gains, f"gains missing key {k!r}"
```
Copy with fuzzy signature `fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, mfs=FUZZY_MFS)`, fresh state `{'pT': None, 'pH': None, 'uT': 0.0, 'uH': 0.0}`, key-check loop over `('pT','pH','uT','uH')`. Never a mutable default (`state=None` → fresh dict inside; Pitfall 5). No `gains`-key check needed (mfs keys accessed directly), but keep the fail-loud state-key loop verbatim.

**Error + error-rate pattern** (`src/pid_controller.py` lines 29-32):
```python
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / dt
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / dt
    st['pT'], st['pH'] = eT, eH
```
Copy, but divide by `(dt / 60.0)` for per-minute rate (Pitfall 3 — per-second units leave the D path dead inside the ZO triangle): `dT = 0.0 if st['pT'] is None else (eT - st['pT']) / (dt / 60.0)`.

**Accumulation + conditional-integration freeze + clip pattern** (`src/pid_controller.py` lines 33-42):
```python
    u_raw = gains['Kp_T'] * eT + gains['Ki_T'] * st['iT'] + gains['Kd_T'] * dT
    # conditional integration: freeze T integrator when saturated pushing further
    if not ((u_raw > 1.0 and eT > 0) or (u_raw < -1.0 and eT < 0)):
        st['iT'] += eT * dt
    u = float(np.clip(gains['Kp_T'] * eT + gains['Ki_T'] * st['iT'] + gains['Kd_T'] * dT, -1.0, 1.0))
    v_raw = gains['Kp_H'] * eH + gains['Ki_H'] * st['iH']
    # freeze H integrator when saturated pushing further (both sides — WR-01)
    if not ((v_raw > 1.0 and eH > 0) or (v_raw < 0.0 and eH < 0)):
        st['iH'] += eH * dt
    v = float(np.clip(gains['Kp_H'] * eH + gains['Ki_H'] * st['iH'], 0.0, 1.0))
```
Copy with accumulator semantics: `u_new = st['uT'] + du` / `v_new = st['uH'] + dv`, freeze when saturated pushing further on both rails of both loops, `np.clip` every accumulation every call (Pitfall 6 — unclipped duties crash `step()`). T-loop bounds [−1, 1], RH-loop bounds [0, 1]. Full prescribed body in RESEARCH.md Pattern 4 (03-RESEARCH.md lines 229-251).

**Split-range output pattern** (`src/pid_controller.py` lines 43-44; loop split corroborated by `src/onoff_controller.py` lines 38-41):
```python
    heat, cool = (u, 0.0) if u > 0 else (0.0, -u)   # split-range, never both
    return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)
```
Copy verbatim (vent mirrors cooling duty — D-01). Key order `["heater", "fan_cooler", "fogger", "vent"]` is asserted by tests; keep it.

---

### `tests/test_fuzzy_controller.py` (test, batch)

**Analog:** `tests/test_baseline_controllers.py` (218 lines, read in full).

**File header + harness pattern** (lines 1-30):
```python
"""Plain-assert sanity suite for the on/off + PID baseline controllers (BASE-01..03).

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_fuzzy_controller.py
"""


def _run_closed_loop(np, controller_step, n=1440):
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
        act, st = controller_step(T, rh, 25.0, 70.0, st)
        wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, wx, T, w)
        T_hist.append(T)
        RH_hist.append(rh)
        U_hist.append(act)
    return T_hist, RH_hist, U_hist
```
Copy the harness verbatim (adapted to call `fuzzy_step`), keep in-body imports and the module docstring convention (update requirement IDs to FUZZ-01..06). Required checks per RESEARCH.md Validation Architecture (03-RESEARCH.md lines 422-430): `test_fuzzy_signs`, `test_error_rate_live`, `test_membership_functions`, `test_rule_table`, `test_output_mapping`, `test_centroid_defuzz`, `test_accumulator_antiwindup`, `test_closed_loop_24h` (1440 steps, finite + bounded, T-IAE < 60 loose bound, RH ∈ [0,100], < 12 zero-crossings in last 6 h, setpoints-as-args, fresh-state determinism, NaN raises AssertionError).

**Sign/mutual-exclusion test pattern** (lines 66-79, 56-63):
```python
def test_pid_signs():
    from src.pid_controller import pid_step

    act, _ = pid_step(20.0, 70.0, 25.0, 70.0, None)
    assert act["heater"] > 0.0 and act["fan_cooler"] == 0.0

    act, _ = pid_step(30.0, 70.0, 25.0, 70.0, None)
    assert act["fan_cooler"] > 0.0 and act["heater"] == 0.0

    act, _ = pid_step(25.0, 50.0, 25.0, 70.0, None)
    assert act["fogger"] > 0.0

    act, _ = pid_step(25.0, 70.0, 25.0, 70.0, None)
    assert all(abs(d) < 1e-9 for d in act.values())
```
Note for fuzzy: velocity form accumulates, so cold-T needs "a few steps" before heater > 0, and at-setpoint with fresh state all duties ≈ 0 (first-call Δ ≈ 0) — adapt thresholds per RESEARCH.md, keep the structure.

**Anti-windup comparison test pattern** (lines 82-125): `_pid_unguarded` (no-freeze variant) + `_run_saturating_script` (400 cold-night + 200 hot-day steps, IAE accumulation) + `test_pid_antiwindup_improves` asserting `guarded < unguarded`. Copy the structure for `test_accumulator_antiwindup` with a never-freeze fuzzy variant.

**24 h integration test pattern** (lines 182-197):
```python
def test_closed_loop_24h():
    import numpy as np
    from src.onoff_controller import onoff_step
    from src.pid_controller import pid_step

    for name, fn in (("onoff", onoff_step), ("pid", pid_step)):
        T_hist, RH_hist, U_hist = _run_closed_loop(np, fn)
        assert len(T_hist) == 1440
        assert all(np.isfinite(T_hist)) and all(np.isfinite(RH_hist))
        assert min(RH_hist) >= 0.0 and max(RH_hist) <= 100.0
        iae_T = sum(abs(T - 25.0) for T in T_hist) / 60.0
        assert np.isfinite(iae_T) and iae_T < 60.0, f"{name} T-IAE {iae_T}"
        for act in U_hist:
            assert list(act.keys()) == ["heater", "fan_cooler", "fogger", "vent"]
            assert all(0.0 <= d <= 1.0 for d in act.values())
            assert not (act["heater"] > 0.0 and act["fan_cooler"] > 0.0)
```
Copy with `fuzzy_step` (single controller, no loop needed), plus the FUZZ-06 extras: oscillation check, setpoints-as-args, bit-identical determinism, NaN-raises (see `test_controller_signatures` lines 155-179 for those three idioms).

**Runner pattern** (lines 200-218) — copy verbatim including the `sys.path` prepend comment:
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

---

### `notebooks/03_fuzzy.ipynb` + `03_fuzzy.png` (component/proof, batch)

**Analog:** `notebooks/02_baselines.ipynb` (6 cells, extracted verbatim via JSON probe).

**Cell 1 — imports** (headless Agg + `src/`-only imports):
```python
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.greenhouse_model import step, load_weather_profile, daytime_solar, params, relative_humidity, wsat_g_per_kg
from src.weather_profile_generator import generate_weather_profile
from src.onoff_controller import onoff_step
from src.pid_controller import pid_step

T_SP, RH_SP = 25.0, 70.0
print("params:", params)
```
Fuzzy version swaps the last two import lines for `from src.fuzzy_controller import fuzzy_step, FUZZY_MFS, LABELS`. Title markdown cell must document setpoints, seed-7 weather, shared duty-dict contract, and separate state per run (Cell 0 pattern).

**Cell 2 — weather regen-if-absent** (copy verbatim):
```python
# Weather input: regenerate the seed-7 profile only if absent, then load.
import os
CSV = "weather/weather_profile.csv"
if not os.path.exists(CSV):
    generate_weather_profile(CSV, seed=7)

t_min, T_out, w_out = load_weather_profile(CSV)
hours = np.arange(0, 1440) / 60.0          # dt = 60 s -> one step per minute
T_out_hr = np.interp(hours, t_min, T_out)
w_out_hr = np.interp(hours, t_min, w_out)
```

**Cell 3 — closed-loop run** (copy structure, single controller + IAE print):
```python
# Closed loop, once per baseline, over the identical disturbance.
# Separate controller states per run; setpoints pass as function args.
def run_closed_loop(controller_step):
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st = None
    T_hist, RH_hist, U_hist = [], [], []
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = controller_step(T, rh, T_SP, RH_SP, st)
        ws = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, ws, T, w)
        T_hist.append(T); RH_hist.append(rh); U_hist.append(act)
    return T_hist, RH_hist, U_hist
```
Adaptation: single fuzzy run (no on/off-vs-PID column loop); RECOMMENDED per CONTEXT.md agent's discretion: MF-shape subplot panel (5 triangles per variable) as the GA before/after baseline for Phase 6.

**Cell 5 — plot + savefig** (copy layout idioms): `plt.figure(figsize=(12, 10))`, T-vs-setpoint (+ outdoor dashed on first column), RH-vs-setpoint, duty stacks over `("heater", "fan_cooler", "fogger", "vent")`, `plt.grid(alpha=0.3)`, `plt.savefig("notebooks/03_fuzzy.png", dpi=120)`, `plt.show()`. Honest-saturation markdown note (Cell 4 pattern) must be kept: RH pins at 100 % structurally (fuzzy probe RH [66.3, 100]), not a tuning defect.

---

## Shared Patterns

### Controller function signature + caller-owned state
**Source:** `src/pid_controller.py:19-26`, `src/onoff_controller.py:15-24`
**Apply to:** `src/fuzzy_controller.py`
`(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, <params>=<MODULE_DICT>)` returning `(duties, state)`. Setpoints are live args (never module constants). `state=None` → fresh dict inside; partial state fails loud via key loop. No mutable defaults anywhere.

### Finite-input asserts + output discipline
**Source:** `src/pid_controller.py:21-23,37,42`, `src/greenhouse_model.py:62-65`
**Apply to:** `src/fuzzy_controller.py` (all numeric entry args; `np.clip` every accumulation; input clipping to MF universes in `infer()`)
```python
expected = {"heater", "fan_cooler", "fogger", "vent"}
assert set(actuators) == expected, f"actuator keys must be exactly {expected}"
for duty in actuators.values():
    assert 0.0 <= duty <= 1.0, "actuator duties must lie in [0, 1]"
```
The plant fail-fasts on key set + [0, 1] range — the controller must never emit anything else.

### Loop split + vent-follows-T
**Source:** `src/pid_controller.py:43-44`, `src/onoff_controller.py:38-41`
**Apply to:** `src/fuzzy_controller.py`, `tests/test_fuzzy_controller.py` (mutual-exclusion assert), `notebooks/03_fuzzy.ipynb`
T-loop drives heater/fan_cooler/vent (vent mirrors cooling), RH-loop drives fogger only; heater and cooler never simultaneously > 0; loops stay independent (no cross-compensation — D-03/Phase-2 D-03).

### Named parameter dict (GA-encodable)
**Source:** `src/pid_controller.py:15-16`, `src/greenhouse_model.py:16-29` (`params` dict precedent)
**Apply to:** `src/fuzzy_controller.py` (`FUZZY_MFS`)
Module-level, read-only at runtime (never assigned into), consumed as a default arg so Phase 4 can pass mutated copies as the chromosome.

### RH helpers — import, don't duplicate
**Source:** `src/greenhouse_model.py:37-45` (`wsat_g_per_kg`, `relative_humidity` with [0, 100] clamp)
**Apply to:** `tests/test_fuzzy_controller.py`, `notebooks/03_fuzzy.ipynb`
Single source of truth (Phase-2 precedent; RESEARCH.md "Don't Hand-Roll").

### Plain-assert suite + standalone runner
**Source:** `tests/test_baseline_controllers.py:1-8,200-218`
**Apply to:** `tests/test_fuzzy_controller.py`
pytest-compatible `test_*` naming, in-body imports (wave-0 ordering), `__main__` runner with `sys.path` prepend. No `conftest.py` (no pytest installed). Run command: `python tests/test_fuzzy_controller.py`.

### Proof-notebook contract
**Source:** `notebooks/02_baselines.ipynb` cells 1-3, 5
**Apply to:** `notebooks/03_fuzzy.ipynb`
Agg headless, imports from `src/` only (no duplicated logic), regen-if-absent seed-7 weather, per-minute `np.interp` weather, `savefig` PNG at dpi=120 committed alongside. Verification is nb-ok/png-ok structural (jupyter CLI absent).

## No Analog Found

| File / Component | Role | Data Flow | Reason |
|------------------|------|-----------|--------|
| Mamdani inference core (`tri` + `RULES` 5x5 + `infer` min-max + 201-point centroid) inside `src/fuzzy_controller.py` | utility (pure numerics) | transform | No fuzzy logic exists anywhere in the codebase yet — nothing to copy. Planner must prescribe RESEARCH.md Patterns 1–3 verbatim (03-RESEARCH.md lines 149-221): `tri()` one-liner, `LABELS = ("NB","NS","ZO","PS","PB")`, `RULES` diagonal table with equilibrium cell `RULES[2,2]==2` and ZO-rate column `[0,1,2,3,4]`, `infer()` with input clipping to universes + zero-fire fallback returning 0.0. |

## Metadata

**Analog search scope:** `src/` (5 modules), `tests/` (2 suites), `notebooks/` (2 notebooks + PNGs), `weather/` — full repo inventory via directory listing.
**Files scanned:** 9 (all tracked source files in scope).
**Pattern extraction date:** 2026-09-22
