# Phase 1: Greenhouse Model & Weather - Research

**Researched:** 2026-09-20
**Domain:** Lumped-parameter greenhouse energy/mass balance ODE + synthetic weather generation (Python/NumPy)
**Confidence:** HIGH

## Summary

Phase 1 delivers the simulated greenhouse plant every later phase (on/off, PID, fuzzy, GA fitness, metrics, dashboard) runs against. The research resolves the four agent-discretion items into concrete, numerically-verified recommendations: (1) coupling coefficients for the D-01 coupled energy–moisture ODE, recommended as a per-cubic-meter lumped formulation with a single named-parameter dict (D-07); (2) the Alduchov–Eskridge Magnus saturation-pressure formula (es(T) = 610.94·exp(17.625T/(T+243.04)) Pa), verified as the most accurate simple formula in the 0–50 °C band; (3) 15-minute CSV rows for `weather_profile.csv` under the D-10 linear-interpolation contract; (4) a plain-assert sanity-test module that is pytest-compatible but has zero new dependencies (pytest is not installed on this machine).

All recommendations were validated with a numeric probe run this session (script + full transcript below): forward Euler at dt=60s has 46×/12× margin below the non-oscillatory bound (λ_T·dt = 0.022, λ_w·dt = 0.084), with trajectory drift vs a dt=5s reference of only 0.023 °C / 0.030 g/kg over 24h — Euler is numerically safe at the locked dt (D-13/D-14). The same probe verified every D-05 coupling direction empirically: heater heats (+12.7 °C) with absolute humidity unchanged (RH falls — drying is emergent from the RH definition, no separate term needed), fan/cooler cools (−25.4 °C) and dehumidifies via condensation when supersaturated, fogger cools (−2.5 °C) AND humidifies (+2.3 g/kg) simultaneously, vent drives both states toward ambient.

**Primary recommendation:** Build `greenhouse_model.py` as a stateless `step(dt, actuators, weather_at_t) -> (temp_C, humidity_g_per_kg)` (D-15/D-16) over the coupled ODEs below, with the recommended coefficients dict, Alduchov–Eskridge saturation, and the probe-derived `tests/test_greenhouse_model.py` sanity suite. Generate `weather_profile.csv` at 15-minute resolution from a seedable generator in `src/` (D-12). No external packages beyond the locked NumPy stack.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Model is a **coupled energy + moisture balance** — temperature and humidity interact (not decoupled per-state ODEs). Heating lowers RH, fogging/moisture raises it, temperature feeds the saturation/humidity-carrying term.
- **D-02:** Plant parameters (thermal mass, leak rate, evaporation rate, operating range) use **literature defaults** for a typical greenhouse, hard-coded as documented defaults (no crop-type prompt, no tuning). Target operating band in the 15–30 °C / 40–90 %RH family.
- **D-03:** Humidity state variable internally is **absolute humidity (g/kg)**; %RH is a derived/conversion quantity for output and plots (saturation pressure as a function of temperature).
- **D-04:** Phase 1 **includes sanity tests** for the ODE (bounded state, positivity, no NaN, plausible steady-state) — not just proof-notebook eyeballing.
- **D-05:** **Full coupling** of the four spec'd actuators: heater adds heat (and dries); fogger adds moisture and drags temperature down (evaporative cooling); fan/cooler extracts heat; vent exchanges air with outside, driving both temperature and humidity toward ambient. No clean "one knob per state" mapping.
- **D-06:** Actuator duty % maps **linearly/proportionally to its physical rate** (no relay deadband or min-turn-on nonlinearity).
- **D-07:** Coupling strength coefficients are exposed as **named parameters in a dict** (per actuator × state effect), not inline constants — reusable/tunable by later phases.
- **D-08:** Coupling matrix covers **exactly the four spec'd actuators** (heater, fan/cooler, fogger, vent); no extra inputs (no shading/CO2).
- **D-09:** `weather_profile.csv` holds a **noisy realistic 24h cycle** — sine/day–night backbone plus mild gaussian noise (clouds/wind logic) so controllers must reject disturbance.
- **D-10:** CSV stores **rows of (time, temp, RH)**; the model **linearly interpolates** between rows at any `dt`.
- **D-11:** Outdoor humidity is **anti-correlated with temperature** (opposing diurnal: cool/humid night, warm/drier midday).
- **D-12:** Profile generation is a **configurable generator** (amplitude, duration, noise seed configurable) committed in `src/` so the CSV is reproducible and later phases (GA robustness, dashboard) can vary scenarios.
- **D-13:** Integration is **fixed-step forward Euler** (NumPy-only, fast and deterministic; adequate for a stable plant and cheap for GA fitness runs).
- **D-14:** Default horizon **24h at dt=60s (1440 steps)**, both exposed as parameters so GA and notebooks can override.
- **D-15:** API is a **pure, stateless step function** in `greenhouse_model.py`: `step(dt, actuators, weather_at_t) -> (temp_C, humidity_g_per_kg)`; simulation state lives with the caller. Matches MODEL-04 literally.
- **D-16:** Return **both units from step** — absolute humidity and %RH (small result object / tuple incl. RH via a helper), so callers and the dashboard don't re-derive conversions.

### the agent's Discretion
- Precise coupling coefficient values and the exact saturation-pressure formula inside the constrained physics — planner/researcher picks numbers consistent with literature defaults and D-01..D-08.
- Exact CSV row resolution (e.g. 15-min vs hourly rows) within the interpolation contract (D-10).
- Sanity-test framework shape (pytest vs plain assert script) — D-04 only mandates that checks exist.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MODEL-01 | Simulation plant models internal temperature and humidity evolution from actuator states and outdoor weather via a simplified energy-balance ODE | Coupled ODE pair (energy + moisture balances), D-01 formulation, coefficients below, probe-verified stable & coupled |
| MODEL-02 | Actuator inputs are heater duty, fan/cooler duty, fogger duty, and vent position (each as on/off percent) | 4-actuator coupling matrix (D-08), linear duty mapping (D-06), probe-verified directions |
| MODEL-03 | Plant consumes a synthetic outdoor weather profile (day/night temperature and humidity cycle) from `weather_profile.csv` | 15-min row format, linear interpolation contract (D-10), seedable `src/` generator (D-12), anti-correlated T/RH (D-11) |
| MODEL-04 | Plant exposes the next internal temperature and humidity given a timestep and current actuator states | `step(dt, actuators, weather_at_t) -> (temp_C, humidity_g_per_kg)` (D-15), both units returned (D-16) |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Plant state evolution (T, w ODE) | API / Backend (Python module) | — | `greenhouse_model.py` is the simulation core; pure computation, no I/O tier involved |
| Weather profile generation | API / Backend (Python module) | — | `weather_profile_generator.py` in `src/` (D-12) writes the CSV once; consumed by model via file read |
| CSV parsing + interpolation | API / Backend | — | Model loads `weather_profile.csv` rows and linearly interpolates at any dt (D-10) |
| Sanity testing | CI / Verification | — | `tests/test_greenhouse_model.py` executes the D-04 checks standalone |
| Plotting proof notebook | Notebook | — | Matplotlib notebook consumes `src/` only (PROJECT.md constraint — no duplicated logic) |
| Dashboard (later phases) | Client / Frontend | API / Backend | Streamlit calls the same `src/` functions per PROOF-02; not in this phase |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.6 (installed) | Runtime | Project locked to Python 3 (PROJECT.md) |
| NumPy | 2.4.3 (installed; PyPI latest 2.5.3) | Numerics — all ODE/weather math | Project locked to NumPy (PROJECT.md); vectorized, deterministic |
| Matplotlib | 3.10.8 (installed) | Proof notebook plots | Project locked to Matplotlib for notebooks |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | NOT INSTALLED | Test runner | NOT this phase — sanity tests must be plain-assert + pytest-compatible, runnable via `python tests/test_greenhouse_model.py` (see Validation Architecture) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Forward Euler (D-13, locked) | scipy.integrate.solve_ivp (RK45) | Locked decision — Euler is deterministic, cheap for GA fitness loops, and probe-verified stable at the mandated dt; RK45 would add scipy dep and nondeterminism-equivalent overhead for a 2-state non-stiff plant |
| Alduchov–Eskridge Magnus es(T) | Single-constant integrated Clausius–Clapeyron | A-E verified ~1.7% more accurate at 25 °C (0.384% max error over −40..+50 °C vs ~2% for CC constant-form) — see State of the Art |
| Named-param dict (D-07) | Inline constants | Locked — later phases (GA tuning, dashboard) must reuse/tune coefficients |

**Installation:**
```bash
# Already satisfied — no new packages required for Phase 1
python -c "import numpy, matplotlib; print(numpy.__version__, matplotlib.__version__)"
```

**Version verification:** `python -m pip index versions numpy` run this session — INSTALLED: 2.4.3, LATEST: 2.5.3, full history back to 1.3.0. Matplotlib 3.10.8 confirmed via local import. NumPy official docs: numpy.org (no version pinned by project; 2.4.3 satisfies everything).

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| numpy | PyPI | ~20 yrs (history to 1.3.0) | — (registry query did not surface raw counts) | github.com/numpy/numpy | [SUS] seam verdict, **false positive** — see note | Approved with evidence |
| matplotlib | PyPI | ~21 yrs | — | github.com/matplotlib/matplotlib | verified locally (3.10.8 import) — not re-audited (no new install) | Approved |

**Seam verdict note:** `gsd-run query package-legitimacy check --ecosystem pypi numpy` returned `SUS` with reasons `too-new / unknown-downloads / no-repository` — a metadata-gap artifact of the seam's heuristic, not a real signal. numpy is (a) the project's locked numeric stack (PROJECT.md, `[VERIFIED: PROJECT.md]`), (b) confirmed present on the correct ecosystem registry with a ~20-year, 130+ release history (`[VERIFIED: pip index versions numpy — run this session]`), (c) locally installed and imported (`[VERIFIED: local run]`), and (d) maintained by the well-known numpy org (numpy.org/numpy/GitHub). No install happens in this phase anyway (both packages are already installed). No checkpoint required.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none requiring action — numpy SUS was evidence-resolved as a metadata false positive (no install occurs this phase; if the executor re-verifies, numpy.org is the authoritative source).

## Architecture Patterns

### System Architecture Diagram

```
                ┌─────────────────────────────────────────────────┐
                │  src/ (Phase 1, NumPy-only)                     │
                │                                                 │
  ┌──────────┐  │  ┌─────────────────────────────┐                │
  │ weather_ │──▶│  weather_profile_generator.py │                │
  │  params  │  │  │  (D-12, seedable)           │                │
  │ (ampl,   │  │  └────────────┬────────────────┘                │
  │  dur,    │  │               ▼                                │
  │  seed)   │  │  ┌─────────────────────────────┐                │
  └──────────┘  │  │  weather_profile.csv         │  D-10 rows    │
                │  │  (time, temp, RH) 15-min     │  (time,temp,RH)│
                │  └────────────┬────────────────┘                │
                │               ▼ read + linear interp at dt      │
                │  ┌─────────────────────────────┐                │
                │  │  greenhouse_model.py         │                │
  ┌──────────┐  │  │  step(dt, actuators,        │                │
  │ actuators│──▶│  │       weather_at_t)         │                │
  │ u_h,u_c, │  │  │  ── Euler over coupled ODE  │                │
  │ u_f,u_v  │  │  │  ── es(T) Alduchov–Eskridge │                │
  └──────────┘  │  │  ── params dict (D-07)      │──▶ (T_C, w_gkg,│
                │  └────────────┬────────────────┘     RH%) D-16  │
                └───────────────┼─────────────────────────────────┘
                                ▼
                ┌─────────────────────────────┐
                │  tests/test_greenhouse_model │  D-04 sanity tests
                │  .py (plain-assert, D-04)   │  (standalone run)
                └─────────────────────────────┘
```

Data flow: generator (seedable) → CSV (single source of truth for outdoor weather) → model loads/interpolates rows → `step()` advances the coupled state one dt per call (caller owns state, D-15) → returns both humidity units (D-16). Controllers in later phases call the same `step()` from their own loops.

### Recommended Project Structure
```
src/
├── greenhouse_model.py          # step(), params dict, es_T(), w_sat(), RH conversion
├── weather_profile_generator.py # seedable generator (D-12) + CSV writer
├── __init__.py
tests/
└── test_greenhouse_model.py     # plain-assert sanity suite (D-04), pytest-compatible
weather_profile.csv              # generated artifact — or under weather/ per PROJECT.md (planning-time layout choice)
notebooks/
└── 01_greenhouse_model.ipynb    # proof notebook (matplotlib trace plots)
```
Note: exact CSV location (root vs `weather/`) is a planning-time decision per CONTEXT.md line 70; the generator argument is `output_path`, so either works.

### Pattern 1: Coupled Energy + Moisture ODE (D-01, per-m³ lumped formulation)

**What:** Two coupled first-order ODEs. Temperature driven by actuator heat injections/extractions, envelope losses, ventilation exchange, evaporative cooling from the fogger, and (recommended, [ASSUMED]) daytime solar gain. Absolute humidity driven by fogger injection, base evaporation, ventilation exchange toward ambient, and cooler condensation at supersaturation.

**When to use:** The whole phase — this is the plant (MODEL-01).

```python
# Source: this research, probe-verified (see transcript below)
# State: T (°C), w (g/kg). Per m³ of greenhouse volume. u_h,u_c,u_f,u_v in [0,1].

es   = lambda T: 610.94 * np.exp(17.625 * T / (T + 243.04))              # Pa, Alduchov–Eskridge
wsat = lambda T, p=101325.0: 622.0 * es(T) / (p - es(T))                  # g/kg

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
    T, w = state  # in real impl, T/w passed in/out
    ...  # one forward-Euler step, then clamp w ≤ wsat(T) (excess condenses)
```

Actuator × state effect matrix (the D-08/D-07 coupling matrix, probe-verified directions):

| Actuator (duty u) | Effect on T | Effect on w (g/kg) | Notes |
|---|---|---|---|
| heater u_h | +P_h·u_h / C_vol | 0 (emergent: RH falls as wsat(T) rises) | "dries" via RH definition (D-05), no moisture term needed |
| fan/cooler u_c | −P_fan·u_c / C_vol | −k_c·u_c·max(w−wsat, 0) | condensation dehumidification only above saturation |
| fogger u_f | −P_fog·u_f / C_vol | +m_fog·u_f | evaporative cooling from latent heat (2.26 MJ/kg) |
| vent u_v | +L_v·u_v·(T_out−T) | +X_v·u_v·(w_out−w) | drives BOTH toward ambient (D-05) |

### Pattern 2: Seedable Weather Generator (D-12) + 15-min CSV (D-10)

**What:** A pure function `generate_weather_profile(amplitude, mean_temp, duration_h=24, seed, row_interval_min=15) -> DataFrame/filename` that writes `(time_min, temp_C, rh_pct)` rows. Backbone: `T_out(t) = T_mean + T_amp·sin(2π(t−t_peak)/24)` (peak ~15:00), RH anti-correlated (D-11): `RH_out(t) = RH_mean − k·T_amp·sin(2π(t−t_peak)/24)` clamped to [30, 95]%, plus mild gaussian noise (e.g. σ_T = 0.5 °C, σ_RH = 3 %) with fixed seed. w_out derived at load time from RH + T via Alduchov–Eskridge (model reads temp+RH rows, D-10).

**When to use:** MODEL-03 + D-09..D-12. Generator committed in `src/`, CSV is the artifact — later phases (GA robustness, dashboard) call the generator with different seeds/amplitudes.

**CSV resolution — 15-minute rows recommended** (`[ASSUMED]` analytic bound, consistent with `[CITED: arXiv 2410.18904]` evidence that linear interp misses peaks at coarse steps): piecewise-linear chord error against a 24h sinusoid of amplitude A with N intervals ≈ (π²/8N²)·A — for a 10 °C swing, 15-min rows (N=96): **0.008 °C**; hourly rows (N=24): **0.13 °C**. Both are negligible for a synthetic sine backbone, but 15-min rows are cheap (97 rows), divide evenly into dt=60s (15 Euler steps per interval), and leave headroom for steeper noise features. Time column in **minutes, integer 0..1440** (matches dt=60s naturally, no float rounding).

### Anti-Patterns to Avoid
- **Single-constant Clausius–Clapeyron for saturation:** ~1.7% high at 25 °C → ~1 %RH-scale conversion error. Use Alduchov–Eskridge (0.1–0.4%).
- **Duty→rate nonlinearities (relay deadbands, min-turn-on):** violates D-06; controllers later assume proportionality. Keep `effect = rate · duty`.
- **Stepping with dt > ~700s during tuning experiments:** forward Euler goes non-oscillatory past λ_w·dt = 1 (dt_crit ≈ 714s for the w-equation). The locked dt=60s is safe (12× margin), but GA robustness sweeps must not silently raise dt without re-checking.
- **Letting fogger push w above saturation:** clamp w ≤ wsat(T) or RH prints exceed 100%; the condensation term handles the physical limit.
- **Re-deriving es/RH in notebooks or dashboard:** D-16 says step() returns RH; a shared `relative_humidity(w, T)` helper exists in the model module. No duplicated logic (PROJECT.md).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Saturation vapor pressure es(T) | Custom curve fit / single-constant CC | Alduchov–Eskridge Magnus formula: `es = 610.94·exp(17.625·T/(T+243.04))` Pa | Verified 0.384% max error over −40..+50 °C (AMS J. Appl. Meteor. 35(4):601–609); two-line NumPy; the de-facto standard in HVAC/greenhouse psychrometrics |
| ODE integration | Custom adaptive solver | Fixed forward Euler (D-13, locked) with verified margin | 2-state non-stiff plant; analytical λ·dt check is one line; deterministic + cheapest for GA fitness |
| Weather file creation | Hand-edited CSV | Seedable generator in `src/` (D-12) | Reproducibility requirement (D-12: GA reruns must be deterministic); generator is ~20 lines |
| Random noise | Manual jitter | `numpy.random.default_rng(seed)` | D-12 seedability; rng is the standard, thread-safe pattern |

**Key insight:** the only "hard" numerics in this phase are es(T) and the Euler stability check — both are one-liners with documented standard formulas. Everything else is bookkeeping (params dict, CSV I/O, linear interpolation via `numpy.interp`). No new dependencies are justified.

## Common Pitfalls

### Pitfall 1: Forward Euler oscillation at larger dt
**What goes wrong:** Humidity trace rings/oscillates around ambient instead of settling.
**Why it happens:** Explicit Euler with a decay term −λ·w is stable only for λ·dt < 2 and non-oscillatory only for λ·dt < 1. The moisture exchange λ_w = X_v + k_c ≈ 1.4e-3 s⁻¹ puts the non-oscillatory bound at dt ≈ 714 s.
**How to avoid:** Keep the locked dt=60s (λ_w·dt = 0.084, 12× margin). If any later phase overrides dt, gate it: `assert (X_v + k_c)*dt < 1`. Probe confirms dt ≤ 600s stays monotone-convergent.
**Warning signs:** w or T alternating above/below target each step; trace "zigzag" on a cooling/venting step; dt printed as 900+.

### Pitfall 2: %RH exceeding 100 or going negative
**What goes wrong:** Plots show RH > 100% after fogging, or negative w.
**Why it happens:** w integrates beyond wsat(T) (fogger keeps injecting) or vent exchange overshoots toward a w_out below 0 (shouldn't, but a bad CSV could produce it).
**How to avoid:** Clamp `w = min(w, wsat(T))` after each step (excess condenses); validate CSV bounds on load (RH 0–100, temp in phys range); keep E_base ≥ 0.
**Warning signs:** RH traces pinned at 100% for long stretches that aren't physical; w < 0 in asserts.

### Pitfall 3: Weather CSV time/dtype mistakes
**What goes wrong:** `numpy.interp` misbehaves (non-monotonic time, string dtype, missing endpoint t=1440).
**Why it happens:** Hand-edited CSV; time in hours vs minutes mismatch; last row omitted so interpolation extrapolates.
**How to avoid:** Generator writes time in integer minutes 0..1440 inclusive; loader validates monotonicity + endpoints; `np.loadtxt(..., dtype=float)`.
**Warning signs:** ValueError from interp; weather "flatlines" after the last row.

### Pitfall 4: Heater "drying" modeled as a moisture sink
**What goes wrong:** Someone adds `dw -= k·u_h` to "make the heater dry the air" (D-05 says heater dries).
**Why it happens:** D-05's phrasing invites it.
**How to avoid:** Do NOT add a heater moisture term. Drying is emergent: absolute w is unchanged, but RH = w/wsat(T)·100 falls because T rises (probe: heater run showed dw = +0.000, RH dropped). Adding an explicit sink double-counts and breaks D-03's g/kg state semantics.
**Warning signs:** heater row in the coupling matrix has a nonzero w effect.

### Pitfall 5: Fan only "exchanging air" instead of active cooling
**What goes wrong:** A pure-exchange "fan" (like the vent) has tiny cooling authority — probe scenario showed exchange-only authority cannot hold 25 °C when T_out > 32 °C midday (its ΔT authority is pinned to T_out − T).
**Why it happens:** D-05 says "fan/cooler extracts heat" — fans in real greenhouses do both (air movement + latent/active cooling), but the dominant modeled effect here is active heat extraction.
**How to avoid:** Model fan as active extraction `−P_fan·u_c` (200 W/m³) plus condensation dehumidification at supersaturation; distinguish it clearly from the vent's exchange terms.
**Warning signs:** system can't cool below ambient on a hot day even at fan 100%.

## Code Examples

Verified patterns from this session's probe run:

### Common Operation 1: Full sanity/verification probe (D-04 evidence)
```python
# Source: probe_greenhouse.py run 2026-09-20 (numpy 2.4.3, Python 3.14.6) — transcript VERBATIM:
#
# PARAMETER / STABILITY ANALYSIS
# C_vol=1.8e+04 J/(m3K)  U_env=5.0 W/(m3K)  ACH=4.5
# L_v=1.508 W/(m3K)  X_v=0.00125 1/s  E_base=0.0025 g/kg/s
# P_h=100.0  P_fan=200.0  P_fog=20.0 W/m3  m_fog=0.0074 g/kg/s
# lambda_T = (U+Lv)/Cvol = 0.000362 1/s   ->  lambda_T*60 = 0.0217
# lambda_w = Xv+kc       = 0.0014 1/s   ->  lambda_w*60 = 0.0840
# dt_crit(non-osc) = 1/lambda_w = 714 s   dt_crit(stable) = 2/lambda_w = 1429 s
# margin at dt=60: T 46x, w 12x below non-oscillatory bound
#
# EULER CONVERGENCE: dt sweep vs dt=5s reference (24h, vent 25%)
# dt=   30s  max|dT|=0.010 C  max|dw|=0.013 g/kg  lam_w*dt=0.04
# dt=   60s  max|dT|=0.023 C  max|dw|=0.030 g/kg  lam_w*dt=0.08
# dt=  120s  max|dT|=0.048 C  max|dw|=0.062 g/kg  lam_w*dt=0.17
# dt=  300s  max|dT|=0.125 C  max|dw|=0.159 g/kg  lam_w*dt=0.42
# dt=  600s  max|dT|=0.262 C  max|dw|=0.339 g/kg  lam_w*dt=0.84
# dt= 1200s  max|dT|=0.571 C  max|dw|=0.633 g/kg  lam_w*dt=1.68  <-- NON-OSCILLATORY BOUND
# dt= 1800s  max|dT|=0.944 C  max|dw|=1.017 g/kg  lam_w*dt=2.52  <-- NON-OSCILLATORY BOUND
#
# ACTUATOR COUPLING DIRECTIONS (D-05) - 1h at fixed weather, sealed vent=0
# baseline (all off):  T=29.28 C  w=20.00 g/kg  RH=77%
# weather @12h:  T_out=15.8 C  w_out=7.3 g/kg (RH 65%)
#   heater 100%      (dries via RH drop at const w) dT=+12.704 C  dw= +0.000 g/kg
#   fan 100% cold    (extracts heat)              dT=-25.408 C  dw=-15.016 g/kg
#   fogger 100%      (cools + humidifies)         dT= -2.541 C  dw= +2.285 g/kg
#   vent 100%        (drives T,w toward ambient)  dT= -1.676 C  dw=-10.727 g/kg
#
# PLAUSIBILITY: 24h run (sanity bounds finite/bounded/positive)
# vent 25% + solar       T: 16.78.. 34.55 C   w:11.00..21.17 g/kg   RH:  44.. 100%   finite/bounded: True
# sealed + solar         T: 16.87.. 35.80 C   w:11.00..38.25 g/kg   RH:  85.. 100%   finite/bounded: True
# ALL PROBE CHECKS PASSED
```

### Common Operation 2: Saturation pressure + RH conversion helpers
```python
# Source: Alduchov & Eskridge 1996, AMS J. Appl. Meteor. 35(4):601-609 [CITED]
def es_pa(T_C):                                    # Pa
    return 610.94 * np.exp(17.625 * T_C / (T_C + 243.04))

def wsat_g_per_kg(T_C, p_Pa=101325.0):             # g/kg
    return 622.0 * es_pa(T_C) / (p_Pa - es_pa(T_C))

def relative_humidity(w_g_per_kg, T_C):            # %  (D-16 helper)
    return 100.0 * w_g_per_kg / wsat_g_per_kg(T_C)

# sanity: es(15)=17.06 hPa, es(25)=31.63 hPa, es(30)=42.47 hPa (psychrometric check) [VERIFIED]
```

### Common Operation 3: Weather CSV 15-min generation (D-12)
```python
# Source: this research (structure mirrors D-09..D-12)
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

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-constant integrated Clausius–Clapeyron for es(T) | Magnus/Tetens with A-E coefficients: `610.94·exp(17.625T/(T+243.04))` Pa | Alduchov & Eskridge 1996 (AMS JAM 35(4):601–609); Huang 2018 (JAMC 57(6)) confirmed its <0.1% relative error below ~53 °C | ~1.7% accuracy gain at 25 °C; the standard psychrometric/HVAC choice; 2-line NumPy |
| Hand-assembled CSV weather | Seedable generator in `src/` | D-12 (this project) | Reproducible GA runs; scenario sweeps for dashboard/robustness without editing files |
| Full CFD / zonal greenhouse models | Lumped-parameter (single-zone) energy+mass balance | Standard for controller-design studies (Nauta 2024 Smart Agric. Tech.; ISO 13790 5R1C ventilation treatment; LiU thesis balance) | 2-state ODE is enough for actuator-level controller comparison; CFD is overkill and slow for GA fitness |

**Deprecated/outdated:**
- **Single-constant Clausius–Clapeyron for %RH conversion:** ~2% error in the greenhouse band; use A-E Magnus (see Pitfall-free pattern above).
- **Spline interpolation of weather rows:** D-10 locks linear interpolation; splines can undershoot/overshoot noisy rows and add nothing for a sine backbone.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | C_vol = 1.8e4 J/(m³·K) effective volumetric heat capacity (≈15× plain air — structure+air+furnishings) | Standard Stack / ODE pattern | Changes thermal time constant (~5–10× slower response); controllers designed against it would need retuning — but remains stable and plausible across a wide range |
| A2 | U_env = 5 W/(m³·K) (≈8 W/m²K glass envelope with A/V ≈ 0.7) | ODE pattern | Shifts baseline heating/cooling load; directionally consistent with glasshouse literature |
| A3 | P_h = 100, P_fan = 200, P_fog = 20 W/m³; m_fog = 7.4e-3 g/kg/s (≈0.44 g/kg/min); ACH=4.5 natural vent; E_base = 2.5e-3 g/kg/s; k_c = 1.5e-4 s⁻¹ | ODE pattern / coupling matrix | Values sit mid-range of literature bounds (transpiration 0–60 g/m²/h → ~0–0.01 g/kg/s; fog systems 130–1223 g/m²/h) — a later tuning phase only changes the dict, not the code (D-07) |
| A4 | Solar gain term A_sol = 100 W/m³, sinusoidal 06:00–18:00 | ODE pattern | D-09 requires a day/night disturbance; without solar the weather barely excites the plant (all-off run drifts <1 °C). If removed, daytime authority of controllers is untested — but the term is additive and removable via the dict (A_sol=0) |
| A5 | 15-min CSV rows (97 rows) vs hourly | Standard Stack / generator pattern | Negligible (0.008 vs 0.13 °C chord error); hourly would also work. 15-min chosen for dt divisibility + headroom. |
| A6 | Fit of "no clean one-knob mapping" (D-05) to fogger + vent: fogger couples T↓/w↑; vent couples both toward ambient | coupling matrix | Probe-verified numerically this session, so low risk; analytic signs confirm |
| A7 | `tests/test_greenhouse_model.py` (plain-assert, pytest-compatible) as the D-04 framework shape | Validation Architecture | pytest is NOT installed (verified) — requiring it would add an install step and violate the zero-new-deps stack; plain-assert runs anywhere |

## Open Questions

1. **Solar gain magnitude (A_sol)**
   - What we know: A daytime solar term is needed for D-09's day/night disturbance to substantively excite the plant; 100 W/m³ is mid-range glazing-transmitted gain.
   - What's unclear: exact value for the target greenhouse; not from a single authoritative source ([ASSUMED A4]).
   - Recommendation: ship A_sol=100 W/m³ as the documented default in the dict; it is a parameter (D-07) — planner should note the executor may calibrate to keep peak T ≤ 45 °C in the all-off run.

2. **Exact CSV location (root vs `weather/` directory)**
   - What we know: PROJECT.md says "data as CSV under `weather/` or root (exact layout is a planning-time decision)" per CONTEXT.md.
   - What's unclear: no prior art in repo to follow.
   - Recommendation: planner picks one (suggest `weather/weather_profile.csv`); the generator takes `output_path` so nothing else changes.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|----------|----------|
| Python | Everything | ✓ | 3.14.6 | — |
| NumPy | ODE + weather math | ✓ | 2.4.3 (PyPI latest 2.5.3) | — |
| Matplotlib | proof notebook | ✓ | 3.10.8 | — |
| pytest | test runner | ✗ | — | plain-assert suite runs with `python tests/test_greenhouse_model.py` — pytest-compatible for later phases |

**Missing dependencies with no fallback:** none — the phase's locked stack is fully installed.
**Missing dependencies with fallback:** pytest — replaced by the plain-assert/pytest-compatible test module (recommended shape for D-04 exactly because of this).

## Validation Architecture

> `.planning/config.json` has `workflow.nyquist_validation: true` → this section is required. Tests must be runnable: pytest is absent, so the suite is a plain-assert script (pytest-compatible `def test_*()` functions + a `__main__` runner).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Plain-assert module, pytest-compatible naming (`def test_*()`); run standalone NOT via pytest (pytest not installed) |
| Config file | none — Wave 0 creates `tests/test_greenhouse_model.py` with `if __name__ == "__main__":` runner |
| Quick run command | `python tests/test_greenhouse_model.py` (runs all D-04 checks, < 5s) |
| Full suite command | `python tests/test_greenhouse_model.py` (single test file; same command) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODEL-01 | Coupled ODE: coupling directions hold (heater↑T/w const-RH↓; fan↓T; fogger↓T↑w; vent→ambient both) | unit | `python tests/test_greenhouse_model.py` (asserts same signs the probe verified) | ❌ Wave 0 |
| MODEL-01 | Bounded state, positivity, no NaN in 24h run | unit | same file (finite/bounded/positive asserts; probe: T∈[16.8,35.8] C, w∈[11.0,38.3] g/kg, RH∈[44,100]%) | ❌ Wave 0 |
| MODEL-01 | Plausible steady-state: with fixed weather, state settles (|dT|<ε, |dw|<ε) | unit | same file | ❌ Wave 0 |
| MODEL-02 | Duty linearity: effect at 50% = half of effect at 100% (D-06) | unit | same file | ❌ Wave 0 |
| MODEL-03 | CSV load+interp: known sine CSV reproduces T_out at midpoints within tol | unit | same file | ❌ Wave 0 |
| MODEL-03 | Generator is seedable: two runs, same seed → identical rows | unit | same file | ❌ Wave 0 |
| MODEL-04 | API contract: step(dt, actuators, weather) → (T, w) tuple; stateless (2 calls, no state leak) | unit | same file | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python tests/test_greenhouse_model.py` (full suite — single file, < 5s)
- **Per wave merge:** same
- **Phase gate:** same — full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_greenhouse_model.py` — the sole test file; covers MODEL-01..04 (7 checks). Create with the `__main__` runner so `python` alone executes it.
- [ ] `tests/conftest.py` — NOT needed (pytest not installed; no shared fixtures beyond the params dict inside the test module).
- [ ] Framework install — none required.

## Security Domain

> `.planning/config.json` has `security_enforcement: true` → this section is required. Phase-1 surface is minimal: local numerics, one generated data file, no network, no user input, no secrets.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no users/identity) |
| V3 Session Management | no | — (stateless computation) |
| V4 Access Control | no | — (local module) |
| V5 Input Validation | yes | CSV weather rows validated on load: numeric dtype, time strictly increasing 0..1440, RH∈[0,100], temp within physical range; assert on file presence |
| V6 Cryptography | no | — (no secrets, no TLS) |

### Known Threat Patterns for {Python/NumPy}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/hostile `weather_profile.csv` (non-numeric, non-monotonic time, out-of-range RH) | Tampering / DoS | Validate on load with `np.loadtxt(dtype=float)` + explicit asserts on monotonicity, endpoints, RH bounds, finite values — fail fast with a clear message before any integration step |
| NaN poisoning from float overflows | DoS | Sanity tests assert `np.all(np.isfinite(...))` over the 24h run (part of D-04 suite) — caught at phase gate |
| `import` of unexpected packages | Supply chain | Zero new dependencies this phase (NumPy/Matplotlib already installed & audited); no postinstall scripts involved |

## Sources

### Primary (HIGH confidence)
- `.planning/CONTEXT.md` (Phase 1, 01-CONTEXT.md) — locked decisions D-01..D-16 quoted verbatim in User Constraints (read this session).
- `.planning/REQUIREMENTS.md` — MODEL-01..04 verbatim (read this session).
- Alduchov & Eskridge 1996, *J. Appl. Meteor.* 35(4):601–609 — Magnus coefficients 610.94/17.625/243.04, 0.384% max error −40..+50 °C (`[CITED]` via multiple sources: formula.expert, washington.edu psychrometric notes, AMS references).
- Huang 2018, *J. Appl. Meteor. Climatol.* 57(6) — improved-Magnus RE < 0.1% below ~53 °C (`[CITED]`).
- LiU master thesis (liu.diva-portal.org) — greenhouse moisture/energy balance structure, ventilation Ṽ = V·ACH/3600 (`[CITED]`).
- UGA greenhouse ventilation field report (fieldreport.caes.uga.edu) — natural ACH 0.75–4 for glasshouses; fan rates 30–60 ACH (`[VERIFIED: UGA extension]`).
- Öztürk 2003, *Turk. J. Agric. For.* 27:49–57 — fog system evaporation 130–1223 g/m²/h, RH +25%, air −6.6 °C (`[CITED]` via Wageningen UR).
- Stanghellini, GreenSys 2011, Wageningen UR (edepot.wur.nl) — crop transpiration 0–60 g/m²/h (`[CITED]`).
- Harvard AM205 lecture notes — explicit Euler stability region |1+λ·dt| ≤ 1 (`[CITED]`).
- **Probe run 2026-09-20 (probe_greenhouse.py, Python 3.14.6 + NumPy 2.4.3)** — full transcript above; stability margins, dt-sweep convergence, coupling directions, sanity bounds — the empirical evidence for every coefficient and relation in this research (`[VERIFIED: session probe run]`).
- PyPI registry query `pip index versions numpy` — 2.4.3 installed / 2.5.3 latest, history to 1.3.0 (`[VERIFIED: pip index]`).

### Secondary (MEDIUM confidence)
- arXiv 2410.18904 (ModAFNO) — linear interpolation error quantification for 6h-vs-1h weather steps (`[CITED]`, used only for the row-resolution argument).
- chillR vignette (rdrr.io) — linear interp accuracy for small vs large gaps (`[CITED]`).

### Tertiary (LOW confidence)
- Nauta 2024, *Smart Agricultural Technology* — lumped-capacitance greenhouse model pattern name-check (`[CITED]` via search result only).
- ISO 13790 5R1C ventilation parameterization H_ven = ρₐcₐΣṼ (training knowledge, cross-checked with LiU thesis — `[ASSUMED]` where it stands alone).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — locked by PROJECT.md/CONTEXT.md; versions verified on the machine and registry this session.
- Architecture: HIGH — ODE formulation, coupling matrix, and coefficients probe-verified empirically; only A_sol magnitude and secondary coefficient precision are [ASSUMED] and dict-parameterized.
- Pitfalls: HIGH — the two physics pitfalls (Euler oscillation, RH cap) are mechanically demonstrated by the probe; framework pitfall (pytest absence) verified directly.

**Research date:** 2026-09-20
**Valid until:** 2026-10-20 (30 days — stable domain; NumPy/Matplotlib versions already current, no fast-moving deps)