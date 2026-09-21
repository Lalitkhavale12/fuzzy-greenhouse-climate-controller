---
phase: 01-greenhouse-model-weather
plan: 01
type: execute
subsystem: simulated-greenhouse-plant
tags: [simulation, ode-model, weather-generator, verification-suite, notebook]
requires: []
provides: [model-plant, weather-csv, step-interface, verification-suite]
affects: [02, 03, 04, 05, 06, 07, 08]
tech-stack:
  added:
    - numpy 2.4.3 (np.interp weather sampling, Alduchov-Eskridge helpers)
    - matplotlib 3.10.8 (Agg headless notebook proof plot)
  patterns:
    - fixed forward Euler with (X_v+k_c)*dt < 1 gate (D-13 lock)
    - pure/stateless step() with caller-owned state (D-15)
    - plain-assert pytest-compatible suite, no top-level imports
key-files:
  created:
    - src/weather_profile_generator.py
    - src/greenhouse_model.py
    - src/__init__.py
    - tests/test_greenhouse_model.py
    - weather/weather_profile.csv
    - notebooks/01_greenhouse_model.ipynb
    - notebooks/01_greenhouse_model.png
    - .gitignore
  modified: []
decisions:
  - Fan modeled as active extraction -P_fan*u_c plus condensation dehumidification at supersaturation; vent carries the exchange terms (D-07 verbatim core)
  - 24h sanity bands chosen probe-faithful supersets T[16.5,36.0] w[10.9,38.5] RH[43,100]; empirically confirmed against the actual seed-7 CSV and documented in the test comment
  - Fan/fogger/vapor coupling asserts compare against the all-off reference run (probe coupling rows used differing fixed-weather conditions, so absolute deltas are evidence, not spec)
  - Euler gate enforces dt=60s in every test loop (1h = 60 steps)
metrics:
  duration: ~8m (17:10:42 -> 17:18:58 UTC+0530)
  completed: 2026-09-21
  tasks: 3
  commits: 3
status: complete
requirements: [MODEL-01, MODEL-02, MODEL-03, MODEL-04]
actuals:
  tokens: 5100   # chars/4 over the realized text diff (20398 bytes of 7 text files; PNG artifact excluded)
  tasks: 3
  commits: 3     # rev-list --count dca75bb..HEAD
plan_head_before: dca75bb565b6e6776a26e5c986a154991a221cf7
commits: 3
---

# Phase 1 Plan 1: Simulated Greenhouse Plant Summary

## One-liner

Coupled energy-moisture ODE greenhouse plant (`step()` with 12 probe-verified params, Alduchov-Eskridge saturation helpers, forward-Euler with stability gate), a seedable 15-minute weather CSV generator, a 7-check plain-assert verification suite, and a headless-executable 24h open-loop proof notebook — committed atomically, one per task.

## Deliverables (plan must_haves)

| must_have | Status |
|---|---|
| src/__init__.py package docstring (module importable from src.*) | Done (`54a7f3a`) |
| MODEL-01 plant: step(dt, actuators, weather, T, w) -> (T, w, RH) | Done (`5039451`) |
| fail-fast asserts: exact actuator key set, duties in [0,1], Euler gate | Done — all three in step() |
| params dict, 12 keys probe-verified | Done |
| helpers es_pa / wsat_g_per_kg / relative_humidity (clamped) / daytime_solar / load_weather_profile | Done |
| MODEL-02 verification suite: 7 plain-assert checks against the one production module | Done — 7/7 green |
| MODEL-03 CSV: generator verbatim (seed 7 default, 0..1440 min, RH [30,95], space-delimited header `time_min,temp_C,rh_pct`) | Done (`weather/weather_profile.csv`, 97 rows) |
| MODEL-04 proof notebook: nbformat-4, >=4 code cells, Agg, `from src.greenhouse_model import` + `plt.plot` + `matplotlib.use`, 3 stacked traces | Done (`4daf357`) |
| No duplicated logic between notebooks and src/ | Done — notebook imports step/load_weather_profile/daytime_solar/params only |

## Verification Results

- Automated suite: **7/7 PASS** (`python tests/test_greenhouse_model.py`): coupling directions, bounded/positive 24h, duty linearity, CSV load+interp, generator seedability, step API contract, actuator key set.
- Notebook structural verify (plan's exact one-liner): **PASS** — 4 code cells, all three literals present.
- Notebook headless execution: **PASS** — open-loop 24h yields T [24.43, 41.74] C, w [16.93, 28.63] g/kg, RH [32.2, 88.2] %; PNG saved.
- Generator regression: seed-7 CSV byte-identical on regeneration; T_out 13.61..26.44 C, RH 44.7..87.2 %.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `python tests/test_greenhouse_model.py` failed with `ModuleNotFoundError: No module named 'src'`**
- **Found during:** Task 2 first suite run
- **Issue:** script-mode execution puts `tests/` on sys.path, not the repo root, so the in-body `from src import ...` imports could not resolve.
- **Fix:** runner `__main__` block prepends the repo root to sys.path (keeps the no-top-level-import constraint; pytest adds rootdir itself).
- **Files modified:** tests/test_greenhouse_model.py
- **Commit:** `5039451`

**2. [Rule 1 - Correctness] 24h sanity bands required empirical calibration**
- **Found during:** Task 2 calibration probe
- **Issue:** the plan's task-2 literal bands (T floor 16.8) tracked the probe transcript's seed realization; the actual seed-7 CSV has T_out min 13.61 C, so bands had to be probe-faithful supersets, not probe replicas.
- **Fix:** bands T[16.5,36.0], w[10.9,38.5], RH[43,100] set at Task 1 (documented in test comment); verbatim-model run against the real CSV confirmed 24h T 16.86..33.93 (sealed variant w max 36.92) — inside every band with margin. No further change needed.
- **Files modified:** tests/test_greenhouse_model.py (band choice comment; band values already final)
- **Commit:** `54a7f3a` (band decision) — verified in `5039451`

**3. [Rule 1 - Test fidelity] Fan coupling assert vs all-off reference**
- **Found during:** test-writing (Task 1)
- **Issue:** RESEARCH.md probe coupling rows ran different fixed-weather reference conditions per row (the fan row's -15 g/kg is not reproducible from the verbatim formula at the documented 1h window), so asserting exact probe deltas would be wrong.
- **Fix:** fan/fogger/vent asserts compare against an all-off baseline run — the same relative semantics the probe used ("dw relative to baseline"), with margins (fan w_end ~19.5 vs baseline 29.0).
- **Files modified:** tests/test_greenhouse_model.py
- **Commit:** `54a7f3a`

## Decisions Made

None beyond the locked D-01..D-16 design decisions; this plan executed them. The one execution-level decision (band calibration, deviation 2) is recorded above.

## Known Stubs

None — no placeholder values, no un-wired components, no TODO/FIXME left behind. The CSV is real generated data; the notebook runs end-to-end.

## Threat Flags

None — pure numeric simulation; no network, auth, or trust-boundary surface. File access is read-only CSV load (`np.loadtxt` with validated bounds).

## Self-Check: PASSED

- `src/greenhouse_model.py` exists; `src/weather_profile_generator.py` exists; `tests/test_greenhouse_model.py` exists; `weather/weather_profile.csv` exists; `notebooks/01_greenhouse_model.ipynb` + `.png` exist.
- Commits verified: `54a7f3a`, `5039451`, `4daf357` all present in `git log`.
- Suite re-run green at Task 3 commit time (7/7).