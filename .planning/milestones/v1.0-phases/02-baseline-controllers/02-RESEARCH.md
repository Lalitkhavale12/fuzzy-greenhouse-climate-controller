# Phase 2: Baseline Controllers - Research

**Researched:** 2026-09-21
**Domain:** Classical closed-loop control (on/off hysteresis + dual-loop PID) on a 2-state greenhouse ODE plant (Python/NumPy)
**Confidence:** HIGH

## Summary

Phase 2 delivers the two honest-but-beatable baselines the GA fuzzy must outperform: `src/onoff_controller.py` (hysteresis relay per loop) and `src/pid_controller.py` (dual-loop continuous PID), both closing the loop on the Phase-1 plant and proven in `notebooks/02_baselines.ipynb`. All agent-discretion items (band widths, gains, anti-windup, clamping, state handling) were resolved numerically this session with closed-loop probes against the real `step()` + seed-7 weather — not by analogy.

The probes establish three facts the plan must encode: (1) a T hysteresis half-band of **±0.5 °C** with an asymmetric release, and an RH half-band of **±3 %RH**, track without chatter (278 vs 99 heater switches/24 h across the ±0.5/±1.0 °C candidates); (2) T-loop starting gains **Kp≈0.25–0.3 per °C, Ki≈0.02–0.03, Kd≈0** with conditional-integration anti-windup cut T-IAE from ~3.6 to ~1.0 °C·h, while P-only control leaves IAE ~55 °C·h (I term mandatory); RH-loop gains an order of magnitude smaller (**Kp≈0.02–0.05 per %RH, Ki≈0.002–0.005**); (3) **RH pins at 100 % for long stretches under every tuning** — the fogger injects ~0.44 g/kg/min (≈+5 %RH/min at 25 °C) while the only moisture sinks (vent exchange, cooler condensation) are slaved to the T-loop, so overnight/midday saturation is structural and honest, not a tuning failure (D-03 forbids cross-compensation fixes).

**Primary recommendation:** Build both controllers as pure functions with caller-owned state, returning the exact `{heater, fan_cooler, fogger, vent}` duty dict in [0, 1]; on/off as a hysteresis state machine (±0.5 °C / ±3 %RH, vent = cooling bit); PID as dual positional-form loops with split-range T output, output clamping, and conditional-integration anti-windup starting from the probe-verified gains above; prove with a 24 h dt=60 s closed-loop run per controller in the Phase-1 notebook pattern (Agg headless, imports from `src/`, committed PNG).

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Control is split into a temperature loop and a humidity loop. The T-loop drives heater + fan_cooler + vent; the RH-loop drives fogger only. The vent follows temperature (the stronger coupling).
- **D-02:** The on/off controller uses a hysteresis band (on at wider error, off at narrower error), not a plain threshold — avoids relay chatter in the proof traces.
- **D-03:** Loops stay independent: no feedforward or cross-compensation (e.g. no heater bump to cancel fogger evaporative cooling). Plant physics (D-05 full coupling from Phase 1) sorts out the interaction — simplest, most honest baseline.
- **D-04:** Closed-loop proof tracks fixed setpoints 25 °C / 70 %RH (mid-band classic greenhouse target, inside the Phase-1 D-02 operating band). No scheduling (PROJECT.md out-of-scope). Setpoints pass as function arguments per BASE-03, not baked in.
- **D-05:** Dual-loop PID mirroring the on/off split: T-PID drives heater/fan/vent, RH-PID drives fogger — so the two baselines are directly comparable. No T-only hybrid.
- **D-06:** Proof is `notebooks/02_baselines.ipynb` + PNG, same pattern as Phase 1 (Agg headless, imports from `src/`, no duplicated logic).

### Agent's Discretion
- Exact hysteresis band widths, PID gains (hand-tuned per PROJECT.md — no auto-tuning), anti-windup handling, and output clamping — planner/researcher picks values that track without saturation.
- PID output mapping to [0, 1] duties and internal state handling (caller-owned vs closure) within the BASE-03 signature.
- Proof-notebook cell layout and plot arrangement within the D-06 pattern.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BASE-01 | On/off controller turns each actuator fully on when error exceeds a threshold, off otherwise | Hysteresis state-machine pattern (D-02) with probe-verified bands ±0.5 °C / ±3 %RH; closed-loop probe tracks T to IAE 6–12 °C·h |
| BASE-02 | PID controller computes a continuous control signal from standard P, I, D terms on error | Dual positional-form PID, split-range T output, conditional-integration anti-windup; probe-verified starting gains; P-only ablation proves I term required |
| BASE-03 | Baseline controllers take current state plus setpoint and return actuator commands | Pure-function signature `(T_C, w_or_rh, T_sp, RH_sp, state) -> ({heater,fan_cooler,fogger,vent} in [0,1], state)`; caller-owned state dict per Phase-1 D-15 convention |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| On/off + PID control law | API / Backend (Python module `src/`) | — | Pure computation over plant state; same tier as the plant, no I/O |
| Closed-loop simulation harness | Verification (tests + notebook) | — | The 1440-step loop lives in tests/notebook, calling `step()` + controller per dt |
| Proof plots | Notebook | — | Matplotlib Agg headless, imports from `src/` only (D-06) |
| Metrics scoring (IAE/energy) | Later phase (Phase 5) | — | Phase 2 only needs history loggable (lists of T/RH/duties); do not build metrics.py here |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.6 (installed) [VERIFIED: session probe] | Runtime | Project locked to Python 3 (PROJECT.md) |
| NumPy | 2.4.3 (installed) [VERIFIED: session probe] | `np.clip`, `np.interp`, traces | Project locked to NumPy; controller math is scalar clip/integrate — no vectorization needed |
| Matplotlib | 3.10.8 (installed) [VERIFIED: session probe] | Proof notebook plots (Agg) | Project locked to Matplotlib for notebooks |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none) | — | — | No test runner (pytest absent, same as Phase 1): plain-assert suite run via `python tests/test_baseline_controllers.py` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-written positional PID (~30 lines) | `scipy.signal`, `python-control` | Rejected: new dependency for a 2-loop student baseline; hand code is inspectable, matches "standard P, I, D" spec literally, and keeps the fuzzy/GA phases dependency-free |
| Velocity-form PID | Positional form (recommended) | Velocity form is bumpless on gain changes, but gains never change at runtime here; positional + clamping + conditional integration is simpler and directly auditable |
| Auto-tuning (Ziegler–Nichols / relay) | Hand-tuned starting gains | PROJECT.md out-of-scope ("PID tuning automation" excluded); Z-N on this plant would also give aggressive gains (large τ≈3600 s, see below) unsuited to a beatable baseline |

**Installation:**
```bash
# Already satisfied — no new packages required for Phase 2
python -c "import numpy, matplotlib; print(numpy.__version__, matplotlib.__version__)"
```

## Package Legitimacy Audit

No external packages are installed in this phase (NumPy/Matplotlib already installed and accepted in Phase 1). Audit table intentionally empty.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | — |

**Packages removed due to [SLOC] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │  src/ (Phase 2, NumPy-only, pure functions)   │
  setpoints         │                                              │
  (25 C, 70 %RH ──▶│  onoff_controller.py ──┐                     │
   fn args, D-04)   │   hysteresis FSM       │  ┌────────────────┐  │
                    │  pid_controller.py ────┼─▶│ actuator dict  │  │
  plant state       │   dual positional PID  │  │ {heater,       │──┼──▶ step(dt, actuators,
  (T_C, w, RH) ───▶│   + anti-windup        │  │  fan_cooler,    │  │    weather_at_t)
                    │                        │  │  fogger, vent} │  │
                    └────────────────────────┼─▶│ duties [0,1]  │◀─┘
                                             │  └────────────────┘
     ┌──────────────────┐  weather            greenhouse_model.py (Phase 1, unchanged)
     │ weather_profile  │──▶ disturbance ──▶  caller owns T/w + controller state (D-15 style)
     │ .csv (seed 7)    │  (T_out, w_out,
     └──────────────────┘   solar)
                                             ▼
                              ┌──────────────────────────────┐
                              │ tests/test_baseline_         │  BASE-01..03 checks
                              │   controllers.py             │  (plain-assert, <5 s)
                              │ notebooks/02_baselines.ipynb │  24 h traces + PNG
                              └──────────────────────────────┘
```

Data flow: each dt the harness reads (T, w, RH), calls the controller (pure function + caller-owned state), feeds the returned duty dict to `step()`, appends (T, RH, duties) to history lists. The notebook runs this loop twice (once per baseline) over the identical 24 h disturbance.

### Recommended Project Structure
```
src/
├── greenhouse_model.py        # UNCHANGED (Phase 1)
├── weather_profile_generator.py  # UNCHANGED (Phase 1)
├── onoff_controller.py        # NEW: hysteresis FSM, caller-owned state
├── pid_controller.py          # NEW: dual-loop positional PID + anti-windup
├── __init__.py
tests/
├── test_greenhouse_model.py      # UNCHANGED
├── test_baseline_controllers.py  # NEW: plain-assert suite (BASE-01..03)
notebooks/
├── 01_greenhouse_model.ipynb/.png  # UNCHANGED
├── 02_baselines.ipynb/.png         # NEW: closed-loop proof (D-06)
weather/weather_profile.csv     # UNCHANGED (seed-7 disturbance)
```

### Pattern 1: Hysteresis Relay with Asymmetric Release (BASE-01, D-02)
**What:** Each loop keeps one latch bit. Turn ON at the wide error, turn OFF at the narrow error (or slight overshoot), hold in between. Asymmetric release (off-threshold inside the band, not mirrored) prevents limit-cycle hovering at the boundary.
**When to use:** Both loops of `onoff_controller.py`; vent bit = cooling bit (D-01).

```python
# Source: session probe 2026-09-21 (closed-loop vs real step() + seed-7 weather) [VERIFIED]
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

**Band-width rationale (probe-measured, 24 h closed loop, same harness):** [VERIFIED: session probe 2026-09-21]

| band_T (±°C) | band_RH (±%RH) | T-IAE (°C·h) | heater switches/24 h | Verdict |
|---|---|---|---|---|
| 0.3 | 2.0 | 6.4 | 374 | Chattery — ~4 min mean period, no IAE gain over 0.5 |
| **0.5** | **3.0** | **7.4** | **278** | **Recommended: tracks, ~5 min period, fine for sim** |
| 1.0 | 5.0 | 11.7 | 99 | Calm but 1.6× IAE; acceptable fallback if traces look busy |

External corroboration: Eurotherm's PID-tuning guide names **1 °C** as the typical on/off hysteresis [CITED: https://www.eurotherm.com/en/temperature-control-en/principles-of-pid-control-and-tuning]; RKC controller defaults use **2 °C** [CITED: websearch RKC catalog excerpt]; Omron's technical guide illustrates **0.8 °C** [CITED: websearch Omron guide excerpt]; room-thermostat practice is ~0.5–1 °C (1–2 °F) [CITED: https://www.isa.org/intech-home/2017/may-june/features/optimizing-to-the-tune-of-a-pid-equation]. The recommended ±0.5 °C sits inside this industrial envelope.

### Pattern 2: Dual Positional PID with Split-Range T Output + Conditional-Integration Anti-Windup (BASE-02, D-05)
**What:** Two independent positional loops. T-loop output `u ∈ [-1, 1]` splits by sign (positive → heater, negative → fan_cooler + vent — never both, mirroring the on/off mutual exclusion). RH-loop output `v ∈ [0, 1]` drives fogger only (one-sided: fogger can only add moisture). Integrators freeze when the output is saturated *in the direction of the error* (conditional integration); outputs hard-clamped to [0, 1].
**When to use:** `pid_controller.py`, entire phase.

```python
# Source: session probe 2026-09-21 (gains verified closed-loop) [VERIFIED]
import numpy as np

GAINS = {'Kp_T': 0.3, 'Ki_T': 0.03, 'Kd_T': 0.0,   # per degC
         'Kp_H': 0.03, 'Ki_H': 0.004, 'Kd_H': 0.0}  # per %RH

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

**Gain rationale (probe-measured, T-loop only, fogger off, 24 h closed loop):** [VERIFIED: session probe 2026-09-21]

| Gains (Kp_T, Ki_T) | Anti-windup | T-IAE (°C·h) | T range (°C) |
|---|---|---|---|
| 0.25, 0.02 | no | 3.7 | [20.3, 28.8] |
| 0.25, 0.02 | **conditional integration** | **1.1** | [20.3, 26.1] |
| 0.30, 0.03 | conditional integration | 1.0 | [20.3, 25.9] |
| 0.10, 0.0 (P-only) | — | 54.6 | droop-dominated — **proves the I term is mandatory** |

First-principles cross-check [ASSUMED, analytic]: holding 25 °C against a 14 °C night needs duty `U·(T−T_out)/P_h = 5·11/100 ≈ 0.55`, against 20 °C needs ≈0.25 [VERIFIED arithmetic on probe-verified params src/greenhouse_model.py:16-29]. Kp≈0.3 reaches full authority at ~3 °C error — consistent. Thermal time constant `C_vol/U_env = 3600 s` sealed (≈1 h) confirms a slow process where Ki≈0.02–0.03 (with error·dt in °C·s) and Kd=0 are the textbook starting point for lag-dominated loops [ASSUMED]. RH gains are ~10× smaller because fogger authority is fierce: full fog adds 0.444 g/kg/min ≈ +2.2 %RH/min at 25 °C (wsat(25 °C)=20.034 g/kg [VERIFIED: session probe]), and 10 min of fog drove 60→98 %RH [VERIFIED: session probe].

### Pattern 3: Closed-Loop Harness (24 h, dt=60 s, seed-7 weather)
**What:** The single loop the tests and notebook share conceptually: interpolate weather to the minute grid, add `daytime_solar`, call controller → `step()` → append history. Caller owns plant state AND controller state (Phase-1 D-15 style).
**When to use:** `tests/test_baseline_controllers.py` (short-horizon assertions) and `notebooks/02_baselines.ipynb` (full 24 h proof).

```python
# Source: Phase-1 notebook pattern (notebooks/01_greenhouse_model.ipynb, read this session)
T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
st = None
for i, h in enumerate(hours):                      # hours = arange(0,1440)/60
    rh = relative_humidity(w, T)
    act, st = controller_step(T, rh, 25.0, 70.0, st)   # setpoints are fn args (D-04)
    wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
    T, w, rh = step(60.0, act, wx, T, w)
    T_hist.append(T); RH_hist.append(rh); U_hist.append(act)
```

### Anti-Patterns to Avoid
- **Plain threshold on/off (no hysteresis):** chatters every step when error hovers near zero; D-02 explicitly forbids it.
- **Heater + cooler simultaneously on:** wastes energy and fights the plant; both on/off (latch exclusion) and PID (split-range by sign) must guarantee mutual exclusion — assert it in tests.
- **Unclamped / unguarded integrator:** overnight error (+5 °C × hours) winds the integral to huge values, then midday cooling arrives late (probe: IAE 3.7→1.0 with the guard). Always pair clamping with conditional integration (clamping alone still leaves a stale integral to unwind).
- **Derivative on error with noisy RH:** RH jumps ~±3 % per step from weather noise; D-on-error amplifies it into fogger chatter. Keep Kd=0 for both loops (thermal/moisture lags dominate; D buys nothing here) [ASSUMED].
- **"Fixing" RH saturation with cross-compensation:** tempting (vent-on-humid, heater-bump), but D-03 locks loops independent. The saturation is the honest baseline the fuzzy must beat — document it, don't engineer around it.
- **Duplicating plant math in controllers/notebook:** controllers read RH via the shared `relative_humidity()` helper; no re-derivation (PROJECT.md constraint).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Saturation-pressure / RH conversion | Inline Magnus copy in controller module | Import `relative_humidity`, `wsat_g_per_kg` from `src/greenhouse_model.py` | Single source of truth; duplicate constants drift (Phase-1 Pitfall) |
| Weather interpolation | Custom resampler | `np.interp(hours, t_min, T_out)` pattern from Phase-1 notebook | Proven pattern; 15-min rows divide evenly into dt=60 s |
| PID auto-tuning | Ziegler–Nichols / relay experiment harness | Hand-tuned gains above (PROJECT.md excludes tuning automation) | Extra experiment code + aggressive Z-N gains unsuited to a beatable baseline |
| Metrics (IAE/RMSE/energy) | `metrics.py` in this phase | Plain history lists; Phase 5 owns scoring | Out of phase scope; keep proof-run history loggable (lists of floats/dicts) |

**Key insight:** the only new numerics in this phase are a latch bit and a leaky-sum integrator — both a few lines. Everything else (plant, weather, plots, tests convention) is reuse of Phase-1 assets.

## Common Pitfalls

### Pitfall 1: RH pinned at 100 % looks like a bug — it is structural
**What goes wrong:** Developer sees RH flat at 100 % overnight, assumes fogger logic inverted, "fixes" polarity or adds vent-on-humid.
**Why it happens:** Fogger injects 0.444 g/kg/min with no modulation (on/off) while `E_base` constantly adds 2.5e-3 g/kg/s and the vent (the only sink besides supersaturation condensation) follows the T-loop, which is heating with vent closed on cold nights [VERIFIED: probe params + closed-loop traces RH=[67,100] on/off, [60,100] PID].
**How to avoid:** Expect it; assert RH ∈ [0,100] (never >100) rather than asserting tight RH tracking. Document the saturation honestly in the notebook — it is exactly the weakness GA-fuzzy will exploit.
**Warning signs:** Fogger duty stuck at 1.0 for hours; RH flatlines at exactly 100.0.

### Pitfall 2: Integral windup through actuator saturation
**What goes wrong:** Midday temperature overshoots to ~29 °C even though steady-state gains look right.
**Why it happens:** Cold-night error (+5 °C for hours) charges the integrator; at sunrise the stale integral keeps the heater on while the sun already heats (probe: no-AW IAE 3.5–3.7 vs AW 1.0) [VERIFIED: session probe].
**How to avoid:** Conditional integration (freeze when saturated pushing further) + output clamp, as in Pattern 2. Verify with the AW on/off test below.
**Warning signs:** Heater duty = 1.0 persisting 1–2 h after T crosses setpoint.

### Pitfall 3: Relay chatter from too-narrow bands
**What goes wrong:** Heater toggles every 1–2 steps; traces look noisy; (later) energy metric inflated by switching if Phase 5 counts cycles.
**Why it happens:** Heater moves 0.33 °C/min and fan 0.67 °C/min [VERIFIED: session probe], so a ±0.1 °C band flips every step.
**How to avoid:** ±0.5 °C / ±3 %RH minimum (bands table above); asymmetric release (−0.2 °C / −1 %RH) so release isn't a second knife-edge.
**Warning signs:** >350 heater switches/24 h in the proof run.

### Pitfall 4: Derivative kick / noise amplification
**What goes wrong:** Fogger duty oscillates wildly step to step.
**Why it happens:** D-on-error differentiates weather-noise steps (±0.5 °C / ±3 %RH noise per CSV row) amplified by 1/dt=1/60 s⁻¹.
**How to avoid:** Kd=0 both loops (recommended defaults); if D is ever tried, use D-on-measurement with a first-order filter — planner should not schedule D work (discretion allows Kd=0 as "handling").
**Warning signs:** Duty traces visibly noisier than error traces.

### Pitfall 5: State-aliasing between runs (mutable default / shared dict)
**What goes wrong:** Second controller in the notebook inherits the first run's integrator/latch; comparison invalid.
**Why it happens:** Mutable default `state={}` or reusing one dict across both 24 h runs.
**How to avoid:** `state=None` → fresh dict inside (Pattern 1/2); notebook constructs separate states per run; test asserts two runs from `None` are bit-identical (determinism check).
**Warning signs:** Re-running a notebook cell changes the trace.

### Pitfall 6: Duties outside [0, 1] crash `step()`
**What goes wrong:** PID overshoot yields duty 1.2 or −0.1 → `step()` fail-fast assert fires mid-notebook.
**Why it happens:** Missing `np.clip` on outputs. Plant asserts are exact-key + [0,1]-range [VERIFIED: src/greenhouse_model.py:62-65 — `assert set(actuators) == expected`, `assert 0.0 <= duty <= 1.0`].
**How to avoid:** Clip every output, every call; test feeds controller outputs directly into `step()` for 1440 steps (integration test below catches it).
**Warning signs:** AssertionError from greenhouse_model mid-run.

## Code Examples

### Closed-loop proof cell (notebook, follows 01 pattern)
```python
# Source: Phase-1 notebook cells (imports/run/plot), adapted to closed loop
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.greenhouse_model import step, load_weather_profile, daytime_solar, params, relative_humidity, wsat_g_per_kg
from src.onoff_controller import onoff_step
from src.pid_controller import pid_step
# ... weather load + interp identical to 01 (t_min/T_out_hr/w_out_hr, hours grid)
# run run_closed_loop twice (onoff_step, pid_step), plot T vs setpoint + outdoor,
# RH vs setpoint, duty stacks; savefig("notebooks/02_baselines.png", dpi=120)
```

### Plant contract the controllers must satisfy (verbatim)
```python
# Source: src/greenhouse_model.py:62-65, read this session [VERIFIED]
expected = {"heater", "fan_cooler", "fogger", "vent"}
assert set(actuators) == expected, f"actuator keys must be exactly {expected}"
for duty in actuators.values():
    assert 0.0 <= duty <= 1.0, "actuator duties must lie in [0, 1]"
```
Controller param anchors (verbatim values the gain math rests on) [VERIFIED: src/greenhouse_model.py:16-29]:
`"C_vol": 1.8e4`, `"U_env": 5.0`, `"P_h": 100.0`, `"P_fan": 200.0`, `"P_fog": 20.0`, `"m_fog": 7.4e-3`, `"ACH": 4.5`, `"L_v": 1.508`, `"X_v": 1.25e-3`, `"E_base": 2.5e-3`, `"k_c": 1.5e-4`, `"A_sol": 100.0`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| P-only / PI without AW for slow thermal loops | PI + conditional-integration (or back-calculation) anti-windup as default | Standard practice since Åström–Wittenmark; conditional integration is the textbook minimal AW | Probe confirms: 3.5× IAE reduction on this plant |
| On/off without hysteresis on slow plants | Hysteresis (or time-proportioning PWM) always | Industrial default (Eurotherm/RKC/Omron docs above) | Chatter-free relay traces suitable as published baselines |
| D-heavy tuning for temperature | PI-dominant, D≈0 or D-on-measurement for lag-dominated loops | Modern tuning rules (e.g. ISA McMillan appendices: scan <10 % of reset time; filter noisy PV) [CITED: websearch ISA excerpt] | Justifies Kd=0 default; avoids noise-driven fogger chatter |

**Deprecated/outdated:**
- Ziegler–Nichols ultimate-gain tuning for this phase: excluded by PROJECT.md (no tuning automation); would over-aggress on a τ≈1 h plant.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Kd=0 suffices; D adds nothing on lag-dominated T/RH loops | Pattern 2, Pitfall 4 | Low — planner may schedule a D-ablation check; worst case a small overshoot improvement is left on the table, baseline stays honest |
| A2 | Recommended bands/gains transfer to the executor's identical harness (same dt=60, seed-7 CSV, T0=20 °C init) | Patterns 1–2 | Low — values are probe-verified on that exact harness; any init/horizon change needs a re-run of the same probe, not new theory |
| A3 | Fogger RH authority (~+5 %RH/min at 25 °C) makes tight RH tracking impossible for baselines — accepted as honest | Pitfall 1 | Low — matches locked D-03; Phase 5 metrics will show it for all controllers equally |
| A4 | P-only IAE ≈55 °C·h generalizes (droop ≈ sustained-error/Kp) | Pattern 2 | Negligible — textbook droop, ablation included as a test |

## Open Questions

1. **Exact notebook plot arrangement (overlaid vs per-controller panels)**
   - What we know: D-06 locks the Phase-1 pattern (Agg, imports from `src/`, PNG); cell layout is agent's discretion.
   - What's unclear: planner/executor taste — 2×3 panel grid vs overlaid traces.
   - Recommendation: planner picks; require at minimum T-vs-setpoint, RH-vs-setpoint, and duty-stack panels per controller, so Phase-6 trail reuse is trivial.

2. **Whether PID needs any D for the Phase-5 overshoot metric**
   - What we know: Kd=0 tracks well (IAE ~1.0); overshoot is scored later, not here.
   - What's unclear: whether a small filtered D would reduce the ~1 °C midday overshoot without noise cost.
   - Recommendation: no D work in this phase (discretion permits Kd=0); note as a non-blocking follow-up if Phase 5 overshoot looks bad.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | ✓ | 3.14.6 | — |
| NumPy | Controller math, harness | ✓ | 2.4.3 | — |
| Matplotlib | Proof notebook (Agg) | ✓ | 3.10.8 | — |
| pytest | Test runner | ✗ | — | Plain-assert suite via `python tests/test_baseline_controllers.py` (Phase-1 convention) |
| scipy / python-control | — (rejected) | — | — | Not needed — hand-written PID |

**Missing dependencies with no fallback:** none — locked stack fully installed.
**Missing dependencies with fallback:** pytest — replaced by plain-assert module (established Phase-1 pattern).

## Validation Architecture

> `.planning/config.json` has `workflow.nyquist_validation: true` → this section is required. pytest is absent: suite is a plain-assert module with `def test_*()` + `__main__` runner (Phase-1 convention).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Plain-assert module, pytest-compatible naming; run standalone, NOT via pytest |
| Config file | none — Wave 0 creates `tests/test_baseline_controllers.py` with `if __name__ == "__main__":` runner (copy the Phase-1 runner incl. `sys.path` prepend) |
| Quick run command | `python tests/test_baseline_controllers.py` (< 5 s; short-horizon checks only) |
| Full suite command | `python tests/test_baseline_controllers.py` (single file; same command) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BASE-01 | Hysteresis semantics: at T=25/RH=70 with fresh state all duties 0; at T=20 (e=−5) heater=1; heater stays 1 at T=24.8 (inside band) and drops at T=25.5; cooling mirror (T=26→fan=vent=1) | unit | `python tests/test_baseline_controllers.py::test_onoff_hysteresis` | ❌ Wave 0 |
| BASE-01 | Mutual exclusion: heater and fan_cooler never both >0 across a 24 h on/off run | unit | same file (`test_onoff_mutual_exclusion`) | ❌ Wave 0 |
| BASE-02 | PID signs: cold (T=20) → heater>0, fan=0; hot (T=30) → fan>0, heater=0; dry (RH=50) → fogger>0; at setpoint with fresh state all ≈0 | unit | same file (`test_pid_signs`) | ❌ Wave 0 |
| BASE-02 | Anti-windup: same gains with/without guard over a saturating night→day run — guarded IAE_T strictly lower (probe margin ~3.5×) | unit | same file (`test_pid_antiwindup_improves`) | ❌ Wave 0 |
| BASE-02 | P-only ablation: Ki=0 variant shows large droop (IAE ≫ guarded PI) — proves I term live | unit | same file (`test_pid_integral_required`) | ❌ Wave 0 |
| BASE-03 | Signature/contract: setpoints are fn args (25/70 vs 22/60 give different outputs); output keys exactly `{heater,fan_cooler,fogger,vent}`, all in [0,1]; fresh-state determinism (two runs bit-identical) | unit | same file (`test_controller_signatures`) | ❌ Wave 0 |
| BASE-01/02/03 | Closed-loop integration: each controller drives `step()` for 1440×dt=60 s on seed-7 weather without assert/NaN; T-IAE finite and < 60 °C·h (loose honesty bound — probe actuals 1–12); RH ∈ [0,100] throughout | integration | same file (`test_closed_loop_24h`, ~2–5 s) | ❌ Wave 0 |
| BASE-01/02 | Notebook proof: `notebooks/02_baselines.ipynb` executes headless (`jupyter nbconvert --execute` or `python -m nbconvert`) and writes `notebooks/02_baselines.png` | manual-only (notebook) | `jupyter nbconvert --to notebook --execute notebooks/02_baselines.ipynb --output /tmp/02_exec.ipynb` + `Test-Path notebooks/02_baselines.png` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python tests/test_baseline_controllers.py`
- **Per wave merge:** same + `python tests/test_greenhouse_model.py` (no plant regression)
- **Phase gate:** both suites green + notebook executes headless + PNG exists before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_baseline_controllers.py` — the sole test file; covers BASE-01..03 (8 checks above). Create with the `__main__` runner + `sys.path` prepend copied from Phase 1.
- [ ] `tests/conftest.py` — NOT needed (no pytest; shared harness helper `_run_closed_loop` lives inside the test module).
- [ ] Framework install — none required.

## Security Domain

> `.planning/config.json` has `security_enforcement: true` → this section is required. Phase-2 surface: local pure functions, file-adjacent notebook, no network/users/secrets.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no users/identity) |
| V3 Session Management | no | — (stateless + caller-owned dicts) |
| V4 Access Control | no | — (local module) |
| V5 Input Validation | yes | Validate setpoint/duty numerics at controller entry: finite floats, duties clipped to [0,1] via `np.clip`; reject unknown actuator keys (plant already fail-fasts — controllers must never emit them) |
| V6 Cryptography | no | — (no secrets, no TLS) |

### Known Threat Patterns for Python/NumPy control loop

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| NaN setpoint/state poisoning (NaN propagates → all duties NaN → `step()` assert fires or silent bad traces) | Tampering / DoS | `assert np.isfinite(...)` on inputs in controller entry + existing `step()` finite assert as backstop [VERIFIED: src/greenhouse_model.py:82] |
| Mutable-state aliasing across runs (one run's integrator corrupts the next comparison) | Tampering (integrity) | Fresh-state-on-`None` convention + bit-identical determinism test (Pitfall 5) |
| Supply-chain (new deps) | Supply chain | Zero new dependencies this phase — nothing to audit |

## Project Constraints (from AGENTS.md)

- Tech: Python 3, NumPy (numerics), Streamlit (dashboard UI); Matplotlib in notebooks; CSV weather input, JSON GA params. → This phase: Python + NumPy + Matplotlib only, no new deps.
- Order: hand-tuned fuzzy first, GA second; dashboards last. → Baselines must expose the duty-dict contract Phases 3–4 reuse; keep proof history loggable.
- Compatibility: notebooks run against `src/` functions with no duplicated logic. → D-06 proof pattern; controllers import RH helpers from the plant module.

## Sources

### Primary (HIGH confidence)
- Session closed-loop probes 2026-09-21 (Python 3.14.6 + NumPy 2.4.3, real `step()` + seed-7 CSV): authority rates (0.333/0.667/0.067 °C/min, 0.444 g/kg/min), hold-duty arithmetic, bands table, gains table, AW ablation, P-only ablation, RH-saturation traces — `[VERIFIED: session probe]` throughout.
- `src/greenhouse_model.py` contract lines 62-65 + params dict lines 16-29, read this session [VERIFIED: src/greenhouse_model.py:16-29,62-65].
- `notebooks/01_greenhouse_model.ipynb` + `tests/test_greenhouse_model.py` patterns, read this session (harness + runner conventions).
- Phase-1 RESEARCH.md probe transcript (heater +12.7 °C/h, fan −25.4 °C/h, fogger −2.5 °C/+2.3 g/kg/h) — consistent with this session's per-minute rates.

### Secondary (MEDIUM confidence)
- Eurotherm "Principles of PID Control and Tuning" — 1 °C typical hysteresis; P/I/D roles; time-proportioning [CITED: https://www.eurotherm.com/en/temperature-control-en/principles-of-pid-control-and-tuning].
- ISA McMillan PID appendices — scan-rate/filter rules, self-regulating loop character [CITED: websearch ISA excerpt].
- ISA InTech on/off room-temperature hysteresis practice (1–2 °F) [CITED: https://www.isa.org/intech-home/2017/may-june/features/optimizing-to-the-tune-of-a-pid-equation].
- RKC catalog (2 °C hysteresis default) + Omron temperature-controller guide (0.8 °C example) [CITED: websearch excerpts].

### Tertiary (LOW confidence)
- Textbook slow-loop tuning heuristics behind Kp/Ki first-principles cross-check and Kd=0 default — tagged [ASSUMED] inline; probes carry the evidentiary weight.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — locked by PROJECT.md/CONTEXT.md; versions verified on the machine this session; zero new deps.
- Architecture: HIGH — patterns are thin wrappers over probe-verified numerics (bands, gains, AW) measured on the exact plant + weather harness.
- Pitfalls: HIGH — RH saturation, windup, chatter, and aliasing all demonstrated or mechanically implied by probes; industrial docs corroborate bands.

**Research date:** 2026-09-21
**Valid until:** 2026-10-21 (30 days — stable domain; classical control + locked plant, no fast-moving deps)
