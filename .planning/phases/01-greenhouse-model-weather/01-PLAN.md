---
phase: 01-greenhouse-model-weather
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/__init__.py
  - src/greenhouse_model.py
  - src/weather_profile_generator.py
  - tests/test_greenhouse_model.py
  - weather/weather_profile.csv
  - notebooks/01_greenhouse_model.ipynb
autonomous: true
requirements: [MODEL-01, MODEL-02, MODEL-03, MODEL-04]
estimate:
  tokens: 60000
  raw_tokens: 40000
  tasks: 3
  confidence: low
must_haves:
  truths:
    - "The plant simulates coupled temperature and absolute-humidity evolution driven by a 4-actuator state and outdoor weather over a full 24h day via the D-01 energy/moisture ODE pair (MODEL-01)."
    - "Each of the four actuators — heater, fan_cooler, fogger, vent — measurably affects the state per its probe-verified direction: heater raises T with w unchanged so RH falls, fan_cooler lowers T and dehumidifies via condensation when supersaturated, fogger lowers T and raises w, vent drives both states toward ambient (MODEL-02)."
    - "Actuator duty maps linearly to a physical rate (D-06): the effect at 50% duty equals half the effect at 100% (MODEL-02)."
    - "weather_profile.csv holds a synthetic 24h day/night temperature and RH cycle at 15-minute resolution — 97 rows, integer minutes 0..1440 — loads through a fail-fast validator, and is linearly interpolated per D-10 (MODEL-03)."
    - "The weather generator is seedable (D-12): two runs with the same seed produce byte-identical CSV output (MODEL-03)."
    - "greenhouse_model.py exposes a pure, stateless step(dt, actuators, weather_at_t, T_C, w_gkg) -> (T_C, w_gkg, rh_pct): two identical calls reproduce identical outputs, missing or unknown actuator keys fail fast, and state is clamped to physical bounds (MODEL-04)."
  artifacts:
    - src/__init__.py
    - src/greenhouse_model.py
    - src/weather_profile_generator.py
    - tests/test_greenhouse_model.py
    - weather/weather_profile.csv
    - notebooks/01_greenhouse_model.ipynb
  key_links:
    - "tests/test_greenhouse_model.py imports params, step, load_weather_profile, relative_humidity from src.greenhouse_model so all 7 checks exercise the one production module"
    - "src/weather_profile_generator.py writes weather/weather_profile.csv, and src.greenhouse_model.load_weather_profile reads that file back and linearly interpolates it with numpy.interp"
    - "notebooks/01_greenhouse_model.ipynb imports step and load_weather_profile from src.greenhouse_model and plots the T/w/RH traces with matplotlib.pyplot"
  assumptions:
    - "MODEL-01 'physically plausible' is verified by the bounded/finite/positive 24h check against the probe bands T in [16.8, 35.8] C, w in [11.0, 38.3] g/kg, RH in [44, 100]% plus coupling-sign asserts; physiological validity beyond D-02 literature defaults is out of scope."
    - "MODEL-03 assumes the generated CSV conforms to the D-09..D-12 contract (single header line, 15-minute rows); load_weather_profile verifies the file rather than assuming."
    - "MODEL-04 is satisfied by the (T_C, w_gkg, rh_pct) 3-tuple — this plan's resolution of D-15/D-16 — and that tuple is the integration anchor for phases 2-7."
  prohibitions:
    - "A physically invalid state may not persist: |T| above 1e3, relative humidity outside [0, 100], or any non-finite value."
    - "Actuator keys may not be silently dropped or ignored — the step API must fail fast on missing and unknown keys."
    - "src/ modules may import nothing beyond the numerical stack numpy, and the test module may import no third-party test framework."
---

<objective>
**As a** climate-control researcher, **I want to** simulate a greenhouse plant whose internal temperature and humidity respond to actuator states and outdoor weather, **so that** I can design and benchmark controllers against a stable, physically plausible plant in later phases (baselines, fuzzy, GA, metrics, dashboard).

**Framing note:** ROADMAP.md states the phase-1 goal declaratively ("Simulated greenhouse plant that responds to actuator states and outdoor weather.") rather than in user-story form. The story above is a faithful editorial reframing of that goal for the MVP plan; if you prefer strict `/gsd mvp-phase` framing, run it before executing this plan. The goal line itself is not modified here.

Purpose: Deliver MODEL-01..MODEL-04 — the coupled energy-moisture ODE plant, a seedable 24h weather profile generator plus CSV, a plain-assert sanity suite, and a proof-of-work notebook — the substrate every later phase runs against. No new dependencies beyond the locked numpy stack (RESEARCH.md package audit); pytest is not installed and must not be assumed.

Output: `src/greenhouse_model.py`, `src/weather_profile_generator.py`, `src/__init__.py`, `tests/test_greenhouse_model.py`, `weather/weather_profile.csv`, `notebooks/01_greenhouse_model.ipynb`.

<acceptance_criteria>
- A full 24h open-loop run with vent at 25% and daytime solar stays inside the probe bands (T in [16.8, 35.8] C, w in [11.0, 38.3] g/kg, RH in [44, 100]%), all values finite.
- All four actuators measurably change the state in the probe-verified directions (heater heats with w constant, fan/cooler cools and dehumidifies, fogger cools and humidifies, vent drives both toward ambient).
- The plain-assert suite `python tests/test_greenhouse_model.py` passes all 7 checks and exits zero.
- `weather/weather_profile.csv` exists (97 rows x 3 cols plus header), is byte-identical when regenerated with the same seed, and loads through `load_weather_profile`.
- The notebook imports from `src.greenhouse_model`, executes headlessly, and produces at least one matplotlib plot.
</acceptance_criteria>
</objective>

<execution_context>
@C:/Users/Lalit/.config/opencode/gsd-core/workflows/execute-plan.md
@C:/Users/Lalit/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-greenhouse-model-weather/01-CONTEXT.md
@.planning/phases/01-greenhouse-model-weather/RESEARCH.md
@.planning/phases/01-greenhouse-model-weather/01-PATTERNS.md
@.planning/phases/01-greenhouse-model-weather/01-VALIDATION.md

Copy-source discipline: RESEARCH.md (git-tracked, probe-verified this session) is the verbatim reference implementation. Every coefficient, formula, and assertion bound in the actions below cites its RESEARCH/PATTERNS/VALIDATION line range — copy from there, do not retype from memory.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Wave-0 — package marker, seedable weather generator, 7-check plain-assert suite, and the generated CSV</name>
  <files>src/__init__.py, src/weather_profile_generator.py, tests/test_greenhouse_model.py, weather/weather_profile.csv</files>
  <read_first>
    - RESEARCH.md Common Operation 3 (lines 325-339): the generator to copy verbatim (backbone, defaults, savetxt header/format).
    - RESEARCH.md "Validation Architecture" (lines 390-420): the test-module contract, quick/full run command, and test pattern.
    - 01-VALIDATION.md lines 39-56: the 7-check matrix and the wave-0 note (model checks stay RED until Task 2 — do NOT run the suite as this task's verify).
    - 01-PATTERNS.md lines 97-155 (generator + test + package-marker patterns) and lines 174-201 (shared patterns: fail-fast asserts, determinism, docstrings).
  </read_first>
  <action>
    Create `src/__init__.py` as a package marker: module docstring naming the package ("GA-Optimized Fuzzy Greenhouse Climate Controller — simulation and control library") and no executable logic (per PATTERNS.md config/package-marker pattern).

    Create `src/weather_profile_generator.py` by copying RESEARCH.md Common Operation 3 (lines 325-339) verbatim: a `generate_weather_profile(out_path, seed=7, duration_h=24.0, interval_min=15, ...)` function using default_rng(seed) with the exact defaults rh_mean 65.0, rh_amp 18.0, t_peak_h 15.0, sigma_T 0.5, sigma_RH 3.0; sine day/night backbone with the temperature peak at t_peak_h, RH anti-correlated (D-11) and clipped to [30, 95] (D-09); monotonically increasing integer minutes 0..1440 step 15; np.savetxt with header line exactly "time_min,temp_C,rh_pct" (dtype float, skiprows-compatible), row format %d, %.2f, %.2f. Keep a module docstring stating D-12 seedability and D-10 15-minute contract. The module must be importable without importing anything from src.greenhouse_model (zero coupling to the model module).

    Create `tests/test_greenhouse_model.py` with the seven probe-based checks defined in VALIDATION.md lines 48-56, all imports INSIDE the test function bodies so the file is runnable before src.greenhouse_model exists, no third-party test framework (plain assert runner per PATTERNS.md test-runner pattern):
    1. test_coupling_directions — open-loop sign asserts sourced from RESEARCH.md probe transcript (lines 274-308): heater raises T with w unchanged (RH falls); fan_cooler lowers T and dehumidifies via condensation when supersaturated; fogger lowers T AND raises w; vent moves both states toward ambient.
    2. test_bounded_finite_positive_24h — 24h run at dt=60, vent 25%, daytime solar; assert T in [16.8, 35.8], w in [11.0, 38.3], RH in [44, 100], and all values finite (probe bands, RESEARCH.md line 406).
    3. test_duty_linearity — D-06: effect at 50% duty equals half of the effect at 100% (within 1e-6 relative tolerance).
    4. test_csv_load_and_interp — D-10: build a small known sine CSV in a temp file, load via load_weather_profile, assert monotonic integer minutes and that interpolated midpoints reproduce the sine within 1e-6 tolerance; also assert the header row is skipped.
    5. test_generator_seedability — D-12: two generate_weather_profile runs to different temp paths with seed 7 produce byte-identical file contents.
    6. test_step_api_contract — D-15/D-16: step returns a 3-tuple (T_C, w_gkg, rh_pct); two identical calls with identical inputs return identical outputs (stateless); returned RH is within [0, 100]; a missing actuator key provokes a fail-fast exception; an unknown actuator key provokes a fail-fast exception.
    7. test_actuator_key_set — exactly the keys {heater, fan_cooler, fogger, vent} are accepted, order-independent.
    End the file with an if __name__ == "__main__" runner that invokes each test, prints PASS/FAIL per check, and exits nonzero on any failure.

    Generate `weather/weather_profile.csv` with `python -c "from src.weather_profile_generator import generate_weather_profile; generate_weather_profile('weather/weather_profile.csv')"` (default seed 7) and add the file to the run.
  </action>
  <verify>
    <automated>python -c "from src.weather_profile_generator import generate_weather_profile; import numpy as np; a=np.loadtxt('weather/weather_profile.csv', dtype=float, skiprows=1); generate_weather_profile('weather/_dup.csv'); assert open('weather/weather_profile.csv','rb').read()==open('weather/_dup.csv','rb').read(); assert a.shape==(97,3); assert (a[:,0]==np.arange(0,1441,15)).all(); assert np.all(a[:,2]>=30) and np.all(a[:,2]<=95); print('gen-ok')"</automated>
    <fails_when>
      <condition>the two CSV files differ (generator not seedable),</condition>
      <condition>shape is not (97,3), minutes are not 0..1440 step 15, or RH escapes [30,95].</condition>
    </fails_when>
  </verify>
  <done>The package marker, generator, and 7-check suite exist as specified; weather/weather_profile.csv is generated from seed 7 and the determinism/shape/RH one-liner above passes.</done>
</task>

<task type="auto">
  <name>Task 2: Coupled ODE plant — stateless step API with Euler gate and fail-fast actuator handling</name>
  <files>src/greenhouse_model.py</files>
  <read_first>
    - RESEARCH.md Pattern 1 (lines 158-210): the probe-verified reference implementation to copy — params dict, es_pa, wsat_g_per_kg, relative_humidity, daytime_solar, step, and load_weather_profile signatures.
    - RESEARCH.md Common Operation 2 (lines 310-323): saturation-pressure and RH-conversion helpers.
    - RESEARCH.md Common Pitfalls 1, 2, 4, 5 (lines 240-268) and RESEARCH.md lines 84 (Euler-vs-solver decision), 11 (stability margins).
    - 01-PATTERNS.md lines 26-95 (model patterns: named-param dict D-07, lodader, gate) and lines 176-193 (imports policy, determinism, stateless API, fail-fast).
  </read_first>
  <action>
    Create `src/greenhouse_model.py` by copying RESEARCH.md Pattern 1 (lines 158-210) and Common Operation 2 (lines 310-323) verbatim, including:
    - Module-level `params` dict (D-07) with the exact probe-verified coefficients: heater_power 100.0, fan_power 200.0, fog_power 20.0, mist_rate 7.4e-3, thermal_capacity 1.8e4, air_exchange_rate 1.25e-3, condensation_rate 1.5e-4, solar_gain 100.0, base_evap 2.5e-3, latent_heat_vol 1.508.
    - `es_pa(T_C)` = 610.94 * exp(17.625*T/(T+243.04)) (Alduchov-Eskridge Magnus, Pa); `wsat_g_per_kg(T_C)` from it; `relative_humidity(w_gkg, T_C)` = 100 * w/wsat, clamped to [0, 100] (Pitfall 2).
    - `daytime_solar(t_hour, A_sol)` = A_sol * sin(pi*(t_hour-6)/12) for 06:00-18:00, else 0.0.
    - `step(dt, actuators, weather_at_t, T_C, w_gkg)` implementing the D-01 coupled energy/moisture balances (heater, fan/cooler with condensation sink when supersaturated, fogger humidification + cooling, vent exchange, solar, base evaporation), the linear duty mapping effect = rate * duty (D-06), forward Euler with the gate `assert (params["air_exchange_rate"] + params["condensation_rate"]) * dt < 1` (D-13/D-14; dt_crit ~714s, locked 60s has 12x margin), w clamped at wsat (Pitfall 1/2), returning the 3-tuple (T_C, w_gkg, rh_pct) per D-15/D-16.
    - `load_weather_profile(path)` -> (t_minutes, temp_C, w_out_gkg): np.loadtxt(dtype=float, skiprows=1) then fail-fast asserts — numeric data, monotonically increasing minutes within [0, 1440], RH within [0, 100], all finite — deriving w_out_gkg at load from RH and T via es_pa/wsat_g_per_kg; linear interpolation via numpy.interp (D-10).
    - Fail-fast actuator handling: the step function asserts `actuators` contains exactly the keys {heater, fan_cooler, fogger, vent} and nothing else, asserts each duty is within [0, 1], and raises on any missing or unknown key (Pitfall: silent drops are forbidden; no try/except anywhere — error handling is assert + clamp per PATTERNS.md).
    - Module docstring stating the plant role, D-01 formulation, and D-15/D-16 3-tuple contract.
    NO other modules may be imported (the only import is numpy); no solver library (Euler is locked by D-13); do not add a heater moisture sink (Pitfall 4 — drying is emergent from the RH definition); do not replace the fan with a pure exchange term (Pitfall 5).
  </action>
  <verify>
    <automated>python tests/test_greenhouse_model.py</automated>
    <fails_when>
      <condition>any of the 7 checks fails (runner exits nonzero),</condition>
      <condition>the module imports anything other than numpy,</condition>
      <condition>a missing or unknown actuator key does not raise.</condition>
    </fails_when>
  </verify>
  <done>The full plain-assert suite passes and exits zero; step() is stateless, fails fast, and stays inside the probe bands on a 24h run; the model imports only numpy.</done>
</task>

<task type="auto">
  <name>Task 3: Proof-of-work notebook — simulate 24h against the generated weather and plot the traces</name>
  <files>notebooks/01_greenhouse_model.ipynb</files>
  <read_first>
    - 01-PATTERNS.md lines 159-167 (notebook pattern: imports from src only, no duplicated logic).
    - ROADMAP.md Phase 6 note (notebooks must call into src/ with no duplicated logic).
    - The Task 1-generated `weather/weather_profile.csv` schema (header time_min,temp_C,rh_pct) and Task 2's step/load_weather_profile signatures for the notebook calls.
  </read_first>
  <action>
    Create `notebooks/01_greenhouse_model.ipynb` as a valid notebook JSON (nbformat 4) with markdown cells explaining the experiment and code cells that:
    1. Set matplotlib to the Agg backend (headless-safe: no GUI backend on this machine).
    2. Import step and load_weather_profile ONLY from src.greenhouse_model (no logic duplicated in the notebook; no reimplementation of the ODE or helpers).
    3. Load `weather/weather_profile.csv` via load_weather_profile and build the time axis from the returned minutes array.
    4. Run a 24h open-loop simulation at dt=60 with a realistic actuator schedule (e.g., vent 25%, heater cycling in the cool hours, fogger bursts in the hot dry hours) by calling step in a loop, recording T, w, and RH each step.
    5. Produce matplotlib plots of the three state traces (T, w, RH) over the day plus the outdoor temperature from the CSV, with axis labels and a legend; do not raise if display is absent (Agg).
    The notebook must contain the literal call pattern `from src.greenhouse_model import` in a code cell and at least one `plt.plot` call.
  </action>
  <verify>
    <automated>python tests/test_greenhouse_model.py; python -c "import json; nb=json.load(open('notebooks/01_greenhouse_model.ipynb')); cells=[c for c in nb['cells'] if c['cell_type']=='code']; assert len(cells)>=4; src='\n'.join(''.join(c['source']) for c in cells); assert 'from src.greenhouse_model import' in src and 'plt.plot' in src and 'matplotlib.use' in src; print('nb-ok')"</automated>
    <fails_when>
      <condition>the suite regresses (exits nonzero),</condition>
      <condition>the notebook has fewer than 4 code cells,</condition>
      <condition>the literal pattern `from src.greenhouse_model import` is absent from its code cells,</condition>
      <condition>no code cell contains a `plt.plot` call or a matplotlib backend selection.</condition>
    </fails_when>
  </verify>
  <done>The notebook is valid nbformat-4 JSON, imports only from src.greenhouse_model, executes headlessly (Agg), contains the required import/plot literals, and the suite remains green.</done>
</task>

</tasks>

## Artifacts this phase produces

| Artifact | Contract (source) |
|---|---|
| `params` dict in `src/greenhouse_model.py` | D-07 named dict, probe-verified coefficients (RESEARCH.md 171-201) |
| `es_pa(T_C)`, `wsat_g_per_kg(T_C)`, `relative_humidity(w_gkg, T_C)` | Alduchov-Eskridge Magnus; RH clamped [0,100] (RESEARCH.md 310-323, Pitfall 2) |
| `daytime_solar(t_hour, A_sol)` | sin backbone, 06:00-18:00 window (RESEARCH.md Pattern 1) |
| `step(dt, actuators, weather_at_t, T_C, w_gkg) -> (T_C, w_gkg, rh_pct)` | D-01 ODE pair, D-06 linear duty, D-13 Euler + gate, D-15/D-16 3-tuple (RESEARCH.md 158-210) |
| `load_weather_profile(path) -> (t_minutes, temp_C, w_out_gkg)` | D-10 np.loadtxt + fail-fast asserts + numpy.interp (RESEARCH.md Pattern 1) |
| `generate_weather_profile(out_path, seed=7, ...)` in `src/weather_profile_generator.py` | D-12 seedable, D-10 15-min rows, D-11 anti-correlated RH (RESEARCH.md 325-339) |
| `tests/test_greenhouse_model.py` — 7 checks + runner | VALIDATION.md 48-56; plain-assert, imports-in-bodies, exit nonzero on failure |
| `weather/weather_profile.csv` | 97 rows x 3 cols + header, generated from seed 7 |
| `src/__init__.py` | package marker, docstring only (PATTERNS.md 153-157) |
| `notebooks/01_greenhouse_model.ipynb` | nbformat 4, imports from src only, Agg backend, plots T/w/RH + outdoor T |

## Wave Structure

Wave 1 (this plan, parallel-ready): Task 1 -> Task 2 -> Task 3 is a within-plan chain (task 2 needs the wave-0 suite; task 3 needs the model and CSV). No other phase-1 plan exists, so there is no cross-plan parallelism to exploit.

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| CSV file -> load_weather_profile | Untrusted file content crosses into the simulation (malformed rows, out-of-range RH, non-monotonic time) |
| actuators dict -> step | Caller-supplied actuator keys/values cross the API boundary (missing/unknown keys, out-of-range duties) |
| weather generator output -> simulation | Generated CSV feeds the model's outdoor disturbance path |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-01-01 | Tampering | load_weather_profile CSV parser | high | mitigate | Fail-fast validation on load per RESEARCH.md V5: numeric dtype, monotonic minutes within [0,1440], RH within [0,100], finite values — parse errors raise before any simulation step |
| T-01-02 | DoS | step() Euler numerics | medium | mitigate | Euler gate assert (X_v + k_c)*dt < 1 plus w clamped at wsat and RH clamped to [0,100] (Pitfalls 1-2) prevent NaN/overflow blow-up |
| T-01-03 | Spoofing | step() actuators argument | medium | mitigate | Exact-key-set assert {heater, fan_cooler, fogger, vent} + duty clamp [0,1] + fail-fast raise on missing/unknown keys; silent drops are forbidden |
| T-01-04 | Tampering | generate_weather_profile | low | accept | Deterministic internal code (std-lib numpy only), no external input crosses this function; audit visibility via D-12 seedability test |
| T-01-05 | DoS | numpy.interp time interpolation | low | accept | Covered by T-01-01 load-time validation — interp only ever receives validated monotonic minutes |
| T-01-SC | Tampering | python package installs | high | mitigate | Package-legitimacy gate satisfied pre-plan: ZERO installs planned; numpy 2.4.3 + matplotlib 3.10.8 already installed per RESEARCH.md package audit (lines 96-107); no checkpoint needed |
</threat_model>

<verification>
- `python tests/test_greenhouse_model.py` exits 0 after every task commit and at phase end (VALIDATION.md lines 24-25: quick run = full suite, single file, <5s).
- Generator determinism/shape one-liner (task 1 verify) passes for the committed weather/weather_profile.csv.
- Notebook structural verify (task 3) passes: >=4 code cells, `from src.greenhouse_model import` present, `plt.plot` and `matplotlib.use` present.
- All wave-0 gap notes in VALIDATION.md (per-task map, lines 43-56) flip from RED to GREEN.
</verification>

<success_criteria>
- All six files exist under src/, tests/, weather/, notebooks/ as listed in files_modified, and weather/weather_profile.csv is committed.
- The 7-check plain-assert suite passes end-to-end; coupling directions, probe bands, D-06 linearity, D-10 interp + load, D-12 seedability, and the D-15/D-16 3-tuple contract are all asserted as runnable checks (no manual-only verification).
- The notebook executes headlessly and produces the three state trace plots plus outdoor temperature, importing every numerical/logic piece from src/.
- A later phase can `from src.greenhouse_model import step, load_weather_profile, params` and run a closed-loop simulation against this plant with a 60s timestep — the stated interface contract in this plan's must_haves.
</success_criteria>

<output>
Create `.planning/phases/01-greenhouse-model-weather/01-01-SUMMARY.md` when done
</output>