# Phase 3: Manual Fuzzy Controller - Research

**Researched:** 2026-09-22
**Domain:** Mamdani fuzzy control (dual-loop incremental/velocity-form fuzzy PI) on a 2-state greenhouse ODE plant (Python/NumPy)
**Confidence:** HIGH

## Summary

Phase 3 delivers the hand-tuned Mamdani fuzzy controller that proves the inference engine works on the plant before any GA optimization: `src/fuzzy_controller.py` (dual-loop Mamdani FIS — temperature error + error-rate, humidity error + error-rate — 5 triangular MFs per variable NB..PB, textbook 5x5 rule tables, centroid defuzzification), closing the loop on the Phase-1 plant at fixed 25 °C / 70 %RH setpoints. The decisive finding of this session's probes — run against the real `step()` + seed-7 weather, not by analogy — is architectural: a **positional fuzzy PD (error, error-rate → absolute duty) droops like P-only control (probe T-IAE 30.16 °C·h)**, while the **velocity/incremental form (error, error-rate → Δduty, accumulated with clamp + conditional-integration freeze) reaches T-IAE 2.79 °C·h with zero steady-state error** (mean |eT| 0.006 °C over the last 6 h, 2 heater sign-changes/24 h). The velocity form is the standard textbook "fuzzy PI" architecture (Mamdani's own 1975 steam-engine controller was incremental), uses the MacVicar-Whelan table with its native Δu semantics, and mirrors the Phase-2 PID's split-range output and anti-windup discipline exactly — so the planner should prescribe velocity form, not positional.

The probes also fix every agent-discretion item numerically: MF universes sized to observed signal ranges (T error ±4 °C, T error-rate ±0.5 °C/min, RH error ±30 %RH, RH error-rate ±6 %RH/min, Δu/Δv ±0.1/step), error-rate computed per-minute via `(e − e_prev)/(dt/60)` so horizon changes don't rescale semantics, and MF parameters housed in a `FUZZY_MFS` named dict of centers/widths arrays (same spirit as PID `GAINS`) that Phase 4 encodes directly as the chromosome.

**Primary recommendation:** Build `fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, mfs=FUZZY_MFS)` as two independent incremental Mamdani loops sharing one NumPy inference core (triangular fuzzify → min implication → max aggregation → 201-point centroid); T-loop Δu accumulates on [−1, 1] and split-ranges by sign to heater/fan_cooler+vent, RH-loop Δv accumulates on [0, 1] to fogger; both loops freeze accumulation when saturated pushing further (PID-style conditional integration); prove with the Phase-1/2 notebook pattern (`notebooks/03_fuzzy.ipynb` + PNG, Agg headless, imports from `src/`, nb-ok/png-ok structural check since the jupyter CLI is absent).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Dual-loop fuzzy emitting the full 4-key duty dict `{heater, fan_cooler, fogger, vent}`: T-fuzzy drives heater/fan/vent (vent follows T), RH-fuzzy drives fogger — same split as the baselines, directly comparable, and GA-ready for Phase 4 (both loops' MF parameters become chromosome material). — **Reversibility:** costly — the loop split shapes every closed-loop trace the GA fitness and comparison phases build on.
- **D-02:** Classic textbook diagonal 5x5 rule tables (error × error-rate, NB..PB) from the classical literature — explainable, and gives Phase 4's GA a sane starting chromosome. No plant-custom rule shaping.
- **D-03:** "Controls successfully" means stable tracking: 24 h closed-loop run on seed-7 weather stays finite and bounded around 25 C / 70 %RH with no sustained oscillation. Beating baselines is explicitly NOT required here — on/off T-IAE 7.38 and PID T-IAE 1.08 are reference numbers only; the GA earns the comparison in Phase 4.
- **D-04:** Proof is `notebooks/03_fuzzy.ipynb` + PNG, same pattern as Phases 1–2 (Agg headless, imports from `src/` only, no duplicated logic). Feeds the Phase-6 notebook trail.

### the agent's Discretion
- MF universe ranges and triangle center/width values (hand-tuned starting point the GA reshapes anyway), error-rate computation (finite difference over dt), output MF definitions and scaling to [0, 1] duties, internal state handling (caller-owned vs closure) within the setpoint-as-args signature.
- Proof-notebook cell layout and plot arrangement (MF plots recommended as GA baseline reference, not mandated).

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FUZZ-01 | Mamdani FIS takes temperature error + error rate-of-change (dual-loop variant same for humidity) | Dual incremental loops, error-rate per-minute finite difference; probe-verified closed loop |
| FUZZ-02 | 5 linguistic terms per variable (NB, NS, ZO, PS, PB), triangular shapes | `tri()` one-liner + `FUZZY_MFS` centers/widths dict; universes sized to observed ranges (probe) |
| FUZZ-03 | Rule base ~25 IF-THEN rules (5x5 grid) | MacVicar-Whelan diagonal 5x5 table verbatim below; one shared table, both loops |
| FUZZ-04 | Output is heater/cooler/fan duty cycle | Accumulated Δu split-range by sign (T) + one-sided [0,1] (RH fogger); exact 4-key dict |
| FUZZ-05 | Centroid defuzzification | 201-point discrete centroid over clipped output triangles; probe-verified surface |
| FUZZ-06 | Hand-tuned controller controls the plant successfully (stable 24 h tracking) | Velocity-form probe: T [19.94, 26.04] °C, T-IAE 2.79, 2 zero-crossings/6 h, finite — passes D-03 bar |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Mamdani inference core (fuzzify → infer → centroid) | API / Backend (Python module `src/`) | — | Pure NumPy computation over error scalars; same tier as plant + baselines, no I/O |
| Loop wrappers (error-rate, accumulation, split-range, AW freeze) | API / Backend (`src/fuzzy_controller.py`) | — | Controller law; caller-owned state per Phase-1 D-15 convention |
| MF parameter store (`FUZZY_MFS`) | API / Backend (module-level named dict) | — | Read-only at runtime; Phase 4 encodes it as the chromosome (GA-01) |
| Closed-loop simulation harness | Verification (tests + notebook) | — | 1440-step loop lives in tests/notebook, calling `fuzzy_step()` + `step()` per dt |
| Proof plots (traces + MF shapes) | Notebook | — | Matplotlib Agg headless, imports from `src/` only (D-04) |
| Metrics scoring (IAE/energy) | Later phase (Phase 5) | — | Phase 3 only needs history loggable (lists of T/RH/duties); do not build metrics.py here |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.6 (installed) [VERIFIED: session probe] | Runtime | Project locked to Python 3 (PROJECT.md) |
| NumPy | 2.4.3 (installed) [VERIFIED: session probe] | `np.clip`, `np.linspace`, aggregation math | Project locked to NumPy; Mamdani core is ~40 lines of clip/min/max — no fuzzy library justified |
| Matplotlib | 3.10.8 (installed) [VERIFIED: session probe] | Proof notebook plots (Agg) | Project locked to Matplotlib for notebooks |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none) | — | — | pytest absent (same as Phases 1–2): plain-assert suite run via `python tests/test_fuzzy_controller.py`; jupyter CLI absent: notebook verified by nb-ok/png-ok structural pattern, not nbconvert execution |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-written Mamdani core (~40 lines) | `scikit-fuzzy` (`skfuzzy`) | Rejected: new dependency for fuzzify/infer/defuzz one-liners; hand code keeps the GA chromosome mapping transparent (Phase 4 mutates centers/widths directly) and matches the NumPy-only stack |
| Velocity/incremental form (recommended) | Positional form (output = absolute duty) | Rejected by probe: positional T-IAE 30.16 °C·h (P-only-like droop, no integrator) vs velocity 2.79 °C·h with zero steady-state error. The MW table consequent is natively a Δu — velocity form uses it as designed |
| 201-point discrete centroid | Analytic centroid of clipped triangles | Discrete grid is 3 lines, exact enough (grid 0.01 on [−1,1]; quantization « actuator authority), and the GA fitness loop calls it 1440×2×N times — vectorized grid ops are cheap |

**Installation:**
```bash
# Already satisfied — no new packages required for Phase 3
python -c "import numpy, matplotlib; print(numpy.__version__, matplotlib.__version__)"
```

**Version verification:** `python --version` → 3.14.6, NumPy 2.4.3, Matplotlib 3.10.8, nbformat 5.10.4 present, pytest and jupyter CLI both absent — all confirmed via session probe this session [VERIFIED: session probe 2026-09-22].

## Package Legitimacy Audit

No external packages are installed in this phase (NumPy/Matplotlib already installed and accepted in Phase 1; `scikit-fuzzy` explicitly rejected — see Alternatives Considered). Audit table intentionally empty.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────────────┐
                    │  src/ (Phase 3, NumPy-only, pure functions)      │
  setpoints         │                                                 │
  (25 C, 70 %RH ──▶│  fuzzy_controller.py                            │
   fn args, D-04)   │   FUZZY_MFS (named centers/widths dict)         │
                    │   ┌──────────────┐  ┌──────────────┐             │
  plant state       │   │ T-loop       │  │ RH-loop      │             │
  (T_C, RH) ──────▶│   │ eT,deT→Δu→u  │  │ eH,deH→Δv→v  │──▶ actuator │
                    │   │ MW 5x5 table │  │ same table   │   │ dict   │
                    │   └──────────────┘  └──────────────┘   │{heater,│──┼──▶ step(dt, actuators,
                    │   shared infer() core (min-max + centroid)     ││ fan_   │  │    weather_at_t)
                    └────────────────────────┼──────────────────────┼─┘│cooler, │  │
       ┌──────────────────┐  weather         │  ┌────────────────┐  ││ fogger,│  │  greenhouse_model.py
       │ weather_profile  │──▶ disturbance ──┼─▶│ duties [0,1]   │◀─┘│ vent}  │  │  (Phase 1, unchanged)
       │ .csv (seed 7)    │  (T_out, w_out, │  │ u split-range  │   └────────┘  │  caller owns T/w +
       └──────────────────┘   solar)        │  │ v one-sided    │             │  controller state
                                            │  └────────────────┘             │
                                            ▼                               │
                             ┌──────────────────────────────┐               │
                             │ tests/test_fuzzy_            │  FUZZ-01..06   │
                             │   controller.py              │  checks        │
                             │ notebooks/03_fuzzy.ipynb     │  24 h traces + │
                             │ + 03_fuzzy.png               │  MF plots + PNG│
                             └──────────────────────────────┘               │
```

Data flow: each dt the harness reads (T, w, RH), calls `fuzzy_step()` (pure function + caller-owned state `{'pT','pH','uT','uH'}`), feeds the returned duty dict to `step()`, appends (T, RH, duties) to history lists. Both loops share one `RULES` table and one `infer()` core; only the MF universes and accumulation bounds differ.

### Recommended Project Structure
```
src/
├── greenhouse_model.py          # UNCHANGED (Phase 1)
├── weather_profile_generator.py # UNCHANGED (Phase 1)
├── onoff_controller.py          # UNCHANGED (Phase 2)
├── pid_controller.py            # UNCHANGED (Phase 2)
├── fuzzy_controller.py          # NEW: FUZZY_MFS dict + infer() core + fuzzy_step()
├── __init__.py
tests/
├── test_greenhouse_model.py     # UNCHANGED
├── test_baseline_controllers.py # UNCHANGED
├── test_fuzzy_controller.py     # NEW: plain-assert suite (FUZZ-01..06)
notebooks/
├── 01_greenhouse_model.ipynb/.png  # UNCHANGED
├── 02_baselines.ipynb/.png         # UNCHANGED
├── 03_fuzzy.ipynb/.png             # NEW: closed-loop proof + MF plots (D-04)
weather/weather_profile.csv     # UNCHANGED (seed-7 disturbance)
```

### Pattern 1: Triangular Fuzzification over a GA-Encodable Named Dict (FUZZ-02, GA-01 ready)
**What:** Every variable (T-error, T-error-rate, Δu, H-error, H-error-rate, Δv) is 5 triangles NB..PB stored as centers + half-widths arrays in one module-level dict. The GA chromosome in Phase 4 is exactly these numbers.
**When to use:** All MF definitions in `fuzzy_controller.py`; executor must not inline magic numbers.

```python
# Source: session probe 2026-09-22 (universes sized to observed signal ranges) [VERIFIED: session probe]
import numpy as np

LABELS = ("NB", "NS", "ZO", "PS", "PB")

FUZZY_MFS = {
    # T-loop: init error +5 C, midday overshoot ~-1..-4 C; max rate ~0.67 C/min at full fan
    "eT":  {"centers": np.array([-4., -2., 0., 2., 4.]),       "widths": np.full(5, 2.0)},
    "deT": {"centers": np.array([-0.5, -0.25, 0., 0.25, 0.5]), "widths": np.full(5, 0.25)},  # C/min
    "du":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},  # duty/step
    # RH-loop: RH pins 60..100 so eH spans [-30,+10]; fogger +2.2 %RH/min at 25 C
    "eH":  {"centers": np.array([-30., -15., 0., 15., 30.]),   "widths": np.full(5, 15.0)},
    "deH": {"centers": np.array([-6., -3., 0., 3., 6.]),       "widths": np.full(5, 3.0)},   # %RH/min
    "dv":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},
}

def tri(x, c, w):
    """Triangular membership in [0,1]. Edge MFs saturate via input clipping in infer()."""
    return float(np.clip(1.0 - abs(float(x) - c) / w, 0.0, 1.0))
```

**Universe rationale (probe-measured):** heater authority 0.333 °C/min, fan 0.667 °C/min, fogger 0.444 g/kg/min ≈ +2.2 %RH/min at 25 °C (wsat(25 °C) = 20.034 g/kg) [VERIFIED: session probe 2026-09-22]. Outer centers sit at ~the largest errors the 24 h run exhibits, so edge saturation is rare but defined (clip, never extrapolate). Width = spacing keeps the partition-of-unity overlap (each interior point fires exactly 2 MFs) — the textbook 50%-overlap triangle layout.

### Pattern 2: MacVicar-Whelan Diagonal 5x5 Rule Table (FUZZ-03, D-02)
**What:** One shared integer table: rows = error NB..PB, cols = error-rate NB..PB, cells = output term index 0..4 (NB..PB). Diagonal (top-left → bottom-right ZO ridge) structure: consequent grows with error and counteracts error-rate — the classical "good control actions" matrix.
**When to use:** Both loops; the table is fixed (FUZZ-07 adaptive rules are v2-deferred).

```python
# Structure: the classical diagonal table (MacVicar-Whelan 1976 lineage —
# diagonal ZO ridge with monotone falloff, corroborated by the 7x7 diagonal
# excerpt [CITED: IIP Series water-bath Mamdani study rule table] and the
# MacVicar-Whelan attribution [CITED: Tzafestas & Papanikolopoulos survey]).
# Exact 5x5 cells: hand-standard, CLOSED-LOOP-PROVEN this session (stable 24 h run below).
RULES = np.array([          # cols: de = NB | NS | ZO | PS | PB
    [0, 0, 0, 1, 2],        # row e = NB (far above setpoint / falling fast...)
    [0, 1, 1, 2, 3],        # row e = NS
    [0, 1, 2, 3, 4],        # row e = ZO (pure damping row: output opposes rate)
    [1, 2, 3, 3, 4],        # row e = PS
    [2, 3, 4, 4, 4],        # row e = PB (far below setpoint -> drive hard)
])  # cells index into (NB, NS, ZO, PS, PB); [VERIFIED: session probe 2026-09-22 — stable]
```

Reading examples: (e=ZO, de=NB) → NB (at setpoint but plunging → brake hard); (e=PB, de=anything) → PS..PB (far cold → heat regardless of rate); (e=ZO, de=ZO) → ZO (the unique equilibrium rule). In velocity form the consequent is Δu, so every cell is direction-correct by construction: positive error → non-negative Δu on the ZO-rate column [0,1,2,3,4].

### Pattern 3: Mamdani Min-Max Inference + Discrete Centroid (FUZZ-05)
**What:** Per rule: firing strength = min(μe, μde) (Mamdani implication); clip the consequent triangle at the strength; aggregate across all 25 rules with max; crisp output = Σ(grid·agg)/Σ(agg) over a fixed grid spanning the output universe. Zero-fire fallback returns 0.0 (Δu = 0 → hold).
**When to use:** The single shared `infer()` core; T-loop grid on [−1,1], RH-loop grid on [0,1].

```python
# Source: session probe 2026-09-22 (surface + closed-loop verified) [VERIFIED: session probe]
def infer(e, de, EC, EW, DC, DW, OC, OW, lo, hi, n=201):
    mu_e = np.array([tri(np.clip(e, EC[0], EC[-1]), c, w) for c, w in zip(EC, EW)])
    mu_d = np.array([tri(np.clip(de, DC[0], DC[-1]), c, w) for c, w in zip(DC, DW)])
    grid = np.linspace(lo, hi, n)
    agg = np.zeros(n)
    for i in range(5):
        if mu_e[i] == 0.0:
            continue
        for j in range(5):
            f = mu_e[i] if mu_e[i] < mu_d[j] else mu_d[j]  # min implication
            if f > 0.0:
                m = np.clip(1.0 - np.abs(grid - OC[RULES[i, j]]) / OW[RULES[i, j]], 0.0, 1.0)
                np.maximum(agg, np.minimum(f, m), out=agg)  # max aggregation
    s = agg.sum()
    return float(np.sum(grid * agg) / s) if s > 0.0 else 0.0
```

**Probe surface sanity (T-loop):** e=+5,de=0 → u +0.837 (full heat when far cold); e=−5,de=0 → −0.837; e=0,de=0 → 0.0 (equilibrium holds) [VERIFIED: session probe 2026-09-22].

### Pattern 4: Velocity-Form Dual Loop with Split-Range Output + Conditional-Integration Freeze (FUZZ-01, FUZZ-04)
**What:** Each loop accumulates its Δ output (`uT += Δu`, clamped) instead of emitting absolute duties. T-loop accumulates on [−1,1] and split-ranges by sign (positive → heater, negative magnitude → fan_cooler + vent — never both, mirroring PID Pattern 2). RH-loop accumulates on [0,1] to fogger only (one-sided). Accumulation freezes when saturated *and pushing further* (conditional integration, mirroring PID anti-windup). Error-rate is per-minute: `(e − e_prev)/(dt/60)`.
**When to use:** `fuzzy_step()` — the entire controller.

```python
# Source: session probe 2026-09-22 (24 h closed-loop numbers below) [VERIFIED: session probe]
def fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, mfs=FUZZY_MFS):
    """Incremental dual-loop Mamdani fuzzy. state = {'pT','pH','uT','uH'}."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    st = {'pT': None, 'pH': None, 'uT': 0.0, 'uH': 0.0} if state is None else state
    for k in ('pT', 'pH', 'uT', 'uH'):  # fail loud on partial state (PID WR-02 convention)
        assert k in st, f"state missing key {k!r}"
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / (dt / 60.0)  # C/min
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / (dt / 60.0)  # %RH/min
    st['pT'], st['pH'] = eT, eH
    du = infer(eT, dT, *mfs["eT"], *mfs["deT"], *mfs["du"], -1.0, 1.0)
    dv = infer(eH, dH, *mfs["eH"], *mfs["deH"], *mfs["dv"], 0.0, 1.0)
    u_new = st['uT'] + du
    if not ((u_new > 1.0 and eT > 0) or (u_new < -1.0 and eT < 0)):  # AW freeze (PID convention)
        st['uT'] = float(np.clip(u_new, -1.0, 1.0))
    v_new = st['uH'] + dv
    if not ((v_new > 1.0 and eH > 0) or (v_new < 0.0 and eH < 0)):
        st['uH'] = float(np.clip(v_new, 0.0, 1.0))
    u, v = st['uT'], st['uH']
    heat, cool = (u, 0.0) if u > 0 else (0.0, -u)  # split-range, never both
    return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)
```

**Closed-loop probe result (24 h, dt=60 s, seed-7 weather, T0=20 °C):** [VERIFIED: session probe 2026-09-22]
T range [19.94, 26.04] °C, T-IAE **2.79** °C·h (vs on/off 7.38, PID 1.08 — reference only per D-03), RH [66.3, 100] % (structural saturation, same as baselines), finite throughout, **2 zero-crossings in last 6 h** (no sustained oscillation), mean |eT| last 6 h = **0.006 °C** (integrator kills droop), 2 heater sign-changes/24 h (smooth), energy ≈ 8.05 duty-h. Passes the D-03/FUZZ-06 bar with margin and preserves headroom for the GA to earn.

### Pattern 5: Closed-Loop Harness (reuse Phase-2 `_run_closed_loop`)
**What:** Identical harness to `tests/test_baseline_controllers.py:11-30` — init T=20.0, w=0.65·wsat(20), per-minute weather interp + `daytime_solar`, controller → `step()` → append. Copy the helper into the fuzzy suite (conftest NOT needed — no pytest).
**When to use:** `tests/test_fuzzy_controller.py` integration test + `notebooks/03_fuzzy.ipynb` proof run.

### Anti-Patterns to Avoid
- **Positional fuzzy PD (output = absolute duty):** droops ~1.25 °C mean error (probe T-IAE 30.16) because nothing integrates — the exact P-only failure Phase 2 proved (IAE ~55). Velocity form is not optional polish; it is the integral action.
- **Unclamped accumulator:** overnight error (+5 °C × hours) winds uT to the rail and it sticks; always pair the [−1,1]/[0,1] clamp with the conditional-integration freeze (clamping alone leaves stale accumulation — PID Pitfall 2, same mechanism).
- **Error-rate in per-second units:** (e−e_prev)/60 yields values ~0.005 that sit entirely inside the ZO triangle — the D term goes dead. Use per-minute `(dt/60)` normalization so the ±0.5 universe means something at any dt.
- **Heater + cooler simultaneously on:** structurally impossible via split-range by sign — assert it in tests (same as Phase 2).
- **"Fixing" RH saturation with cross-compensation:** vent-on-humid or heater-bump breaks locked loop independence (Phase-2 D-03); saturation is the honest baseline the GA will exploit.
- **Duplicating plant math / metrics in this phase:** import `relative_humidity`/`wsat_g_per_kg` from the plant; keep history as plain lists for Phase 5 (no `metrics.py` here).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy inference engine | `scikit-fuzzy` dependency | ~40-line `tri` + `infer` above | New dep for one-liners; hand code keeps GA chromosome mapping transparent and stack NumPy-only |
| Saturation/RH conversion | Inline Magnus copy in fuzzy module | Import `relative_humidity`, `wsat_g_per_kg` from `src/greenhouse_model.py` | Single source of truth (Phase-2 precedent) |
| Weather interpolation | Custom resampler | `np.interp(hours, t_min, T_out)` Phase-1 pattern | Proven; 15-min rows divide evenly into dt=60 s |
| Metrics (IAE/RMSE/energy) | `metrics.py` in this phase | Plain history lists; Phase 5 owns scoring | Out of scope; keep proof-run history loggable |
| Defuzzification analytics | Closed-form centroid of clipped triangles | 201-point discrete centroid | 3 lines, quantization 0.01 « actuator authority, vectorized-cheap for GA fitness loops |

**Key insight:** the only new numerics in this phase are triangular fuzzification and min-max-centroid inference — both a few lines each. The control-theoretic content (velocity form ≈ PI, conditional-integration freeze, split-range) is reuse of Phase-2 PID insights in linguistic clothing.

## Common Pitfalls

### Pitfall 1: Positional form droop (THE phase-defining trap)
**What goes wrong:** Fuzzy controller tracks 1–2 °C below setpoint all night; T-IAE ~30 °C·h; notebook looks like a failure next to PID's 1.08.
**Why it happens:** Positional fuzzy PD has no integrator — at steady state it needs error to hold output (u ≈ Kp-like surface × e), exactly the P-only droop Phase 2 measured (IAE ~55) [VERIFIED: session probe — positional prototype T-IAE 30.16, T range [20.17, 26.1]].
**How to avoid:** Velocity form (Pattern 4): accumulate Δu so zero error holds any duty; probe reaches mean |eT| 0.006 °C over the last 6 h [VERIFIED: session probe 2026-09-22].
**Warning signs:** Proof trace sits persistently off-setpoint without oscillating; heater duty flat at a mid value overnight.

### Pitfall 2: Accumulator windup through saturation
**What goes wrong:** Midday overshoot to ~28 °C+ even though the rule table looks right.
**Why it happens:** Cold-night error charges uT to the +1 rail for hours; at sunrise the stale accumulation keeps heating (same mechanism as PID Pitfall 2, probe margin 3.5× there).
**How to avoid:** Conditional-integration freeze when saturated pushing further + hard clamp, as in Pattern 4 (both loops, both rail sides — PID WR-01 precedent).
**Warning signs:** Heater duty = 1.0 persisting 1–2 h after T crosses setpoint.

### Pitfall 3: Dead error-rate from unit mismatch
**What goes wrong:** Controller behaves like a fuzzy P (sluggish, overshooty); de membership always ~ZO.
**Why it happens:** `(e − e_prev)/dt` with dt=60 s gives °C/s values ~100× smaller than the per-minute universe.
**How to avoid:** Divide by `(dt/60)` (per-minute rate); test asserts a scripted 0.5 °C/min ramp fuzzifies off-ZO.
**Warning signs:** Damping row of the table never fires in a rule-coverage check.

### Pitfall 4: Edge-MF gaps (inputs beyond outer centers return 0)
**What goes wrong:** At e=+6 °C (beyond PB center +4) all μ=0 → no rules fire → Δu=0 → controller goes limp exactly when it should push hardest.
**Why it happens:** Triangles have finite support; inputs outside the universe fuzzify to all-zero.
**How to avoid:** Clip inputs to the universe in `infer()` (Pattern 3) so edges saturate to full NB/PB membership; zero-fire fallback returns 0.0 as backstop only.
**Warning signs:** Flat duty response to extreme scripted errors in unit tests.

### Pitfall 5: State-aliasing between runs (mutable default / shared dict)
**What goes wrong:** Second loop/run inherits the first run's `uT` accumulator; comparison invalid.
**Why it happens:** Mutable default `state={}` or reusing one dict across runs (Phase-2 Pitfall 5, same mechanism; worse here because `uT` carries control authority, not just history).
**How to avoid:** `state=None` → fresh dict inside (Pattern 4); notebook constructs separate states per run; test asserts two runs from `None` are bit-identical.
**Warning signs:** Re-running a notebook cell changes the trace.

### Pitfall 6: Duties outside [0, 1] crash `step()`
**What goes wrong:** Accumulated u overshoots → `step()` fail-fast assert fires mid-notebook.
**Why it happens:** Missing `np.clip` on accumulation. Plant asserts are exact-key + [0,1]-range [VERIFIED: src/greenhouse_model.py:62-65].
**How to avoid:** Clip every accumulation, every call; integration test feeds outputs directly into `step()` for 1440 steps.
**Warning signs:** AssertionError from greenhouse_model mid-run.

### Pitfall 7: RH pinned at 100 % looks like a fuzzy bug — it is structural
**What goes wrong:** Developer sees RH flat at 100 %, assumes fogger rules inverted, flips polarity.
**Why it happens:** Same mechanism as Phase-2 Pitfall 1: fogger injects 0.444 g/kg/min while the only sinks are vent (T-slaved) and condensation; one-sided fogger authority cannot dry [VERIFIED: probe RH [66.3,100] for fuzzy, matching on/off [67,100] / PID [60,100] precedent].
**How to avoid:** Expect it; assert RH ∈ [0,100], never tight RH tracking; document honestly in the notebook.
**Warning signs:** Fogger duty stuck at 1.0 for hours; RH flatlines at exactly 100.0.

## Code Examples

### Closed-loop proof cell (notebook, follows 02 pattern + MF plots)
```python
# Source: Phase-2 notebook pattern (notebooks/02_baselines.ipynb, read this session)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.greenhouse_model import step, load_weather_profile, daytime_solar, params, relative_humidity, wsat_g_per_kg
from src.fuzzy_controller import fuzzy_step, FUZZY_MFS, LABELS
# ... weather load + interp identical to 02 (t_min/T_out_hr/w_out_hr, hours grid)
# run_closed_loop(fuzzy_step) over 1440 steps; plot T vs setpoint + outdoor,
# RH vs setpoint, duty stacks; RECOMMENDED (D-discretion): MF-shape subplot panel
# (5 triangles per variable) as the GA before/after baseline for Phase 6;
# savefig("notebooks/03_fuzzy.png", dpi=120)
```

### Plant contract the controller must satisfy (verbatim)
```python
# Source: src/greenhouse_model.py:62-65, read this session [VERIFIED: src/greenhouse_model.py:62-65]
expected = {"heater", "fan_cooler", "fogger", "vent"}
assert set(actuators) == expected, f"actuator keys must be exactly {expected}"
for duty in actuators.values():
    assert 0.0 <= duty <= 1.0, "actuator duties must lie in [0, 1]"
```
Controller param anchors (verbatim values the universe sizing rests on) [VERIFIED: src/greenhouse_model.py:16-29]:
`"C_vol": 1.8e4`, `"U_env": 5.0`, `"P_h": 100.0`, `"P_fan": 200.0`, `"P_fog": 20.0`, `"m_fog": 7.4e-3`, `"ACH": 4.5`, `"L_v": 1.508`, `"X_v": 1.25e-3`, `"E_base": 2.5e-3`, `"k_c": 1.5e-4`, `"A_sol": 100.0`.
Baseline output discipline to mirror [VERIFIED: src/pid_controller.py:15-44, src/onoff_controller.py:15-42]: `GAINS` named-dict pattern, caller-owned-state + `state=None` convention, `np.clip` outputs, finite-input asserts, vent-follows-T split.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Positional fuzzy PD (u = F(e,de)) for regulation | Incremental fuzzy PI (Δu = F(e,de), accumulate + AW) as default for setpoint regulation | Standard since Mamdani & Assilian 1975 (incremental steam-engine controller); textbook fuzzy-PI equivalence (e.g. Jantzen tutorial) | Probe confirms: 30.16 → 2.79 T-IAE on this plant; zero steady-state error |
| Fuzzy toolbox dependency (MATLAB/skfuzzy) for Mamdani | Hand-coded min-max-centroid core for small rule bases | Practice for embedded/small FIS (25 rules ≈ 40 lines) | Keeps GA chromosome mapping transparent; zero new deps |
| P-only / PI without AW for slow thermal loops | PI + conditional-integration anti-windup as default | Åström–Wittenmark; Phase-2 probe 3.5× IAE reduction | Same freeze reused for the fuzzy accumulators |

**Deprecated/outdated:**
- Ziegler–Nichols-style scaling for fuzzy output gains: excluded by analogy with PROJECT.md (no tuning automation); Δu universe ±0.1/step is the probe-verified starting point the GA reshapes.
- Spline interpolation of weather rows: D-10 locks linear interpolation (Phase-1 precedent).

## Assumptions Log

> Claims tagged `[ASSUMED]` in this research — planner and discuss-phase use this table to identify decisions needing user confirmation.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact 5x5 cell values are the hand-standard diagonal table (textbook structure corroborated, not byte-copied from a single authoritative page) | Pattern 2 | Low — closed-loop probe proves this table stabilizes the plant (T-IAE 2.79); any single-cell deviation preserves the diagonal monotone structure the stability rests on |
| A2 | Δu universe ±0.1/step reaches full authority in ~10–20 steps — fast enough for τ≈1 h plant, slow enough to avoid chatter | Pattern 1/4 | Low — probe shows 2 heater sign-changes/24 h; GA reshapes widths anyway (hand values are explicitly the starting point) |
| A3 | RH-loop universes (±30 error, ±6 rate) transfer from fogger-authority arithmetic rather than a closed-loop sweep | Pattern 1 | Low — RH is structurally saturated under every controller; loop only needs correct sign behavior (dry → fog), which the table guarantees |
| A4 | 201-point centroid grid quantization (0.01 duty) is negligible vs actuator authority | Pattern 3 | Negligible — 0.33 °C/min per full duty dwarfs 0.01 steps; GA fitness noise dominates |
| A5 | Velocity-form fuzzy PI counts as "Mamdani + centroid + duty output" per FUZZ-01/04/05 (consequent is Δduty, accumulated duty is the emitted signal) | Pattern 4 | Low — matches Mamdani's original incremental architecture and the spec's "output duty cycle" literally (the dict holds duties); flag in notebook text for the examiner |

**If this table is empty:** n/a — 5 assumed claims above need no user confirmation (all low/negligible risk, GA revisits tuning), but the planner must not silently switch architecture (positional) or table cells.

## Open Questions

1. **MF subplot panel layout in the proof notebook**
   - What we know: D-04 locks the Phase-1/2 pattern (Agg, imports from `src/`, PNG); MF plots recommended as GA baseline reference, not mandated (agent's discretion).
   - What's unclear: planner/executor taste — 6 MF panels + 3 trace panels vs traces only.
   - Recommendation: planner requires at minimum the 3 trace panels (T, RH, duties) + 1 MF-shape figure (all 6 variables or T-loop trio); Phase 6 reuses the MF figure for the before/after GA visual.

2. **Whether the executor re-runs the architecture probe or trusts it**
   - What we know: velocity-vs-positional verdict rests on this session's probe (same harness the suite reuses: 1440×dt=60 s, seed-7, T0=20 °C).
   - What's unclear: nothing material — the suite's integration test re-proves stability on the executor's machine by construction.
   - Recommendation: no re-probe task; the `test_closed_loop_24h` bound (T-IAE < 60, finite, RH ∈ [0,100], oscillation check) re-verifies the claim automatically.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | ✓ | 3.14.6 | — |
| NumPy | Inference core, harness | ✓ | 2.4.3 | — |
| Matplotlib | Proof notebook (Agg) | ✓ | 3.10.8 | — |
| nbformat | Notebook JSON inspection | ✓ | 5.10.4 | — |
| pytest | Test runner | ✗ | — | Plain-assert suite via `python tests/test_fuzzy_controller.py` (Phases-1/2 convention) |
| jupyter CLI | Notebook execution | ✗ | — | nb-ok structural check + headless python-Agg run (Phase-2 precedent) |
| scipy / scikit-fuzzy | — (rejected) | — | — | Not needed — hand-written core |

**Missing dependencies with no fallback:** none — locked stack fully installed.
**Missing dependencies with fallback:** pytest → plain-assert module; jupyter CLI → nb-ok/png-ok structural pattern (`02-PLAN.md:134-135` precedent).

## Validation Architecture

> `.planning/config.json` has `workflow.nyquist_validation: true` → this section is required. pytest and jupyter CLI are both absent: suite is a plain-assert module with `def test_*()` + `__main__` runner (Phase-1/2 convention); notebook proof is structural nb-ok + png-ok (Phase-2 precedent).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Plain-assert module, pytest-compatible naming; run standalone, NOT via pytest |
| Config file | none — Wave 0 creates `tests/test_fuzzy_controller.py` with `if __name__ == "__main__":` runner (copy the Phase-2 runner incl. `sys.path` prepend + in-body imports) |
| Quick run command | `python tests/test_fuzzy_controller.py` (< 10 s; inference core is 25-rule × 201-grid NumPy per step) |
| Full suite command | `python tests/test_fuzzy_controller.py` (single file; same command) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FUZZ-01 | Loop semantics: cold T=20 → heater>0 after a few steps (accumulator charges); hot T=30 → fan>0; dry RH=50 → fogger>0; at setpoint with fresh state all duties ≈0 (first call Δ≈0) | unit | `python tests/test_fuzzy_controller.py` (`test_fuzzy_signs`) | ❌ Wave 0 |
| FUZZ-01 | Error-rate live: scripted +0.5 °C/min ramp at fixed error gives different Δu than flat error (de path not dead — Pitfall 3 guard) | unit | same file (`test_error_rate_live`) | ❌ Wave 0 |
| FUZZ-02 | MF shape: `tri(c,w)` = 1 at center, 0 beyond ±w; `FUZZY_MFS` has keys eT/deT/du/eH/deH/dv with 5 centers + 5 widths each; 50%-overlap (interior point fires exactly 2 MFs) | unit | same file (`test_membership_functions`) | ❌ Wave 0 |
| FUZZ-03 | Rule table: `RULES` is 5x5 with cells in 0..4; equilibrium cell RULES[2,2]==2 (ZO); ZO-rate column == [0,1,2,3,4] (monotone drive); damping row RULES[2,:]==[0,1,2,3,4] (opposes rate) | unit | same file (`test_rule_table`) | ❌ Wave 0 |
| FUZZ-04 | Split-range + mutual exclusion: heater and fan_cooler never both >0 across scripted errors AND a 24 h run; keys exactly `{heater,fan_cooler,fogger,vent}`, all in [0,1]; vent == fan_cooler (D-01) | unit + integration | same file (`test_output_mapping`) | ❌ Wave 0 |
| FUZZ-05 | Centroid: e=+5,de=0 → Δu>0.3 (strong heat); e=−5,de=0 → Δu<−0.3; e=0,de=0 → Δu≈0 (probe: ±0.837/0.0); determinism (same inputs → bit-identical) | unit | same file (`test_centroid_defuzz`) | ❌ Wave 0 |
| FUZZ-02/05 | Anti-windup: saturating night→day script — frozen accumulator variant IAE strictly lower than never-freeze variant (PID `test_pid_antiwindup_improves` precedent) | unit | same file (`test_accumulator_antiwindup`) | ❌ Wave 0 |
| FUZZ-06 | Closed-loop integration: 1440×dt=60 s on seed-7 weather without assert/NaN; finite + bounded; T-IAE < 60 °C·h (loose honesty bound — probe actual 2.79); RH ∈ [0,100]; no sustained oscillation (< 12 zero-crossings of T−25 in last 6 h — probe actual 2); setpoints-as-args (25/70 vs 22/60 differ); fresh-state determinism (two runs bit-identical); NaN input raises AssertionError | integration | same file (`test_closed_loop_24h`) | ❌ Wave 0 |
| FUZZ-06 | Notebook proof: `notebooks/03_fuzzy.ipynb` structural nb-ok + `notebooks/03_fuzzy.png` png-ok (>10 KB) | manual-only (notebook) | nb-ok one-liner + `Test-Path`/size check (02-PLAN.md:134-135 precedent) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python tests/test_fuzzy_controller.py`
- **Per wave merge:** same + `python tests/test_baseline_controllers.py` + `python tests/test_greenhouse_model.py` (no plant/baseline regression)
- **Phase gate:** all three suites green + nb-ok prints `nb-ok` + `notebooks/03_fuzzy.png` > 10 KB before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_fuzzy_controller.py` — the sole test file; covers FUZZ-01..06 (9 checks above). Create with the `__main__` runner + `sys.path` prepend + in-body imports copied from Phase 2.
- [ ] `tests/conftest.py` — NOT needed (no pytest; shared `_run_closed_loop` helper lives inside the test module).
- [ ] Framework install — none required.

## Security Domain

> `.planning/config.json` has `security_enforcement: true` (ASVS level 1, block on high) → this section is required. Phase-3 surface: local pure functions + file-adjacent notebook; no network/users/secrets.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no users/identity) |
| V3 Session Management | no | — (stateless + caller-owned dicts) |
| V4 Access Control | no | — (local module) |
| V5 Input Validation | yes | Finite-float asserts on (T_C, rh_pct, setpoints, dt) at `fuzzy_step` entry; `np.clip` every accumulation; input clipping to MF universes in `infer()`; exact 4-key duty dict (plant fail-fasts otherwise) |
| V6 Cryptography | no | — (no secrets, no TLS) |

### Known Threat Patterns for Python/NumPy control loop

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| NaN poisoning (NaN setpoint/state → all duties NaN → silent bad traces or `step()` assert) | Tampering / DoS | `assert np.isfinite(...)` on all numeric inputs at entry + existing `step()` finite assert as backstop [VERIFIED: src/greenhouse_model.py:82]; suite asserts NaN raises |
| Mutable-state aliasing across runs (one run's `uT` accumulator corrupts the next comparison — higher stakes than PID: accumulator carries control authority) | Tampering (integrity) | Fresh-state-on-`None` convention + bit-identical determinism test (Pitfall 5) |
| MF-dict mutation at runtime (caller passes `mfs` and the controller writes into it → GA baseline corrupted) | Tampering (integrity) | Treat `FUZZY_MFS` as read-only: never assign into `mfs` arrays inside `infer()`/`fuzzy_step()` (read-only indexing only); document the convention in the module docstring |
| Supply chain (new deps) | Supply chain | Zero new dependencies this phase — nothing to audit |

## Project Constraints (from AGENTS.md)

- Tech: Python 3, NumPy (numerics), Streamlit (dashboard UI); Matplotlib in notebooks; CSV weather input, JSON GA params. → This phase: Python + NumPy + Matplotlib only, no new deps (`scikit-fuzzy` rejected).
- Order: hand-tuned fuzzy first, GA second; dashboards last. → MF params must live in the named `FUZZY_MFS` dict (GA-encodable chromosome material); keep proof history loggable for Phase 5.
- Compatibility: notebooks run against `src/` functions with no duplicated logic. → D-04 proof pattern; import RH helpers from the plant module.

## Sources

### Primary (HIGH confidence)
- Session closed-loop probes 2026-09-22 (Python 3.14.6 + NumPy 2.4.3, real `step()` + seed-7 CSV): positional-vs-velocity verdict (30.16 vs 2.79 T-IAE), surface sanity (±0.837/0.0), authority rates (0.333/0.667 °C/min, +2.2 %RH/min), wsat(25 °C)=20.034 g/kg, 24 h stability trace (T [19.94,26.04], 2 crossings/6 h, mean|eT| 0.006) — `[VERIFIED: session probe]` throughout.
- `src/greenhouse_model.py` contract lines 62-65 + params dict lines 16-29, read this session [VERIFIED: src/greenhouse_model.py:16-29,62-65].
- `src/pid_controller.py` GAINS/state/clip/AW conventions + `src/onoff_controller.py` loop-split, read this session [VERIFIED: src/pid_controller.py:15-44, src/onoff_controller.py:15-42].
- `tests/test_baseline_controllers.py` harness + runner conventions, read this session; Phase-2 SUMMARY reference numbers (on/off 7.38, PID 1.08 T-IAE) per 02-SUMMARY.md:42.
- Phase-2 notebook structural-check precedent (nb-ok/png-ok one-liners) per 02-PLAN.md:134-135 (jupyter CLI absent).

### Secondary (MEDIUM confidence)
- Tzafestas & Papanikolopoulos survey — MacVicar-Whelan (1976) table attribution [CITED: websearch excerpt].
- IIP Series water-bath Mamdani study — 7x7 diagonal rule table corroborating the diagonal-ZO-ridge structure [CITED: websearch excerpt].
- IntechOpen Mamdani-type FLC chapter (Iancu) — min implication / max aggregation / centroid pipeline [CITED: websearch excerpt].
- Control Engineering "Fuzzy Logic and Expert Systems" — error/change-in-error rule-matrix practice [CITED: https://www.controleng.com/advanced-process-control-fuzzy-logic-and-expert-systems].

### Tertiary (LOW confidence)
- Exact 5x5 cell values as "the" hand-standard table — tagged [ASSUMED] A1; the probe carries the evidentiary weight (closed-loop stability), not the citation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — locked by PROJECT.md/CONTEXT.md; versions verified on the machine this session; zero new deps.
- Architecture: HIGH — velocity-vs-positional verdict and all universes probe-measured on the exact plant + weather harness; rule-table structure textbook-corroborated.
- Pitfalls: HIGH — droop, windup, dead-rate, edge-gap, aliasing all demonstrated or mechanically implied by probes; RH saturation inherits Phase-2 precedent.

**Research date:** 2026-09-22
**Valid until:** 2026-10-22 (30 days — stable domain; classical fuzzy control + locked plant, no fast-moving deps)
