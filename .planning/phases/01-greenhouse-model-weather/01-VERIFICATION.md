---
phase: 01-greenhouse-model-weather
status: verified
goal_achieved: true
date: 2026-09-21
---

# Phase 01 (greenhouse-model-weather) Verification Report

**Phase goal (ROADMAP.md Phase 1):** Simulated greenhouse plant that responds to actuator states and outdoor weather.
**Verified:** 2026-09-21 (post fix commit db83e9b)
**Status:** verified — goal achieved, no gaps.

## Roadmap success criteria (4/4 PASS)

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | `greenhouse_model.py` returns next temperature/humidity from timestep + actuator states using the energy-balance ODE | PASS | `src/greenhouse_model.py:55-84` — `step(dt, actuators, weather_at_t, T_C, w_gkg) -> (T_C, w_gkg, rh_pct)` implements the D-01 coupled balances (heater/fan/fogger/vent/solar/envelope, lines 73-79); live-probed: `step(60, all-off, (15.8,7.3,0), 25, 12)` → `(24.85, 12.15, 61.2)` |
| 2 | `weather_profile.csv` holds a synthetic day/night temp and humidity cycle and drives the model as outdoor disturbance | PASS | `weather/weather_profile.csv` — 97 rows × 3 cols + header `time_min,temp_C,rh_pct` (verified shape `(97,3)`, minutes 0..1440 step 15); T 13.51..26.67 C, RH 42.9..88.4 % (day/night cycle); `load_weather_profile` (`src/greenhouse_model.py:87-101`) loads it and `test_bounded_finite_positive_24h` drives `step()` from it |
| 3 | A simulation run produces stable, physically plausible temperature/humidity traces | PASS | `tests/test_greenhouse_model.py:50-76` — 24h open-loop (dt=60, vent 25% + solar) asserts T in [13.5,43.0], w in [9.5,21.0], RH in [31,100], all finite; suite run 2026-09-21: **7/7 PASS**; notebook headless run produces T/w/RH traces + PNG |
| 4 | All four actuator inputs (heater, fan/cooler, fogger, vent) affect the state | PASS | `tests/test_greenhouse_model.py:18-47` `test_coupling_directions` — heater raises T w/ w unchanged, fan_cooler cools + dehumidifies, fogger cools + humidifies, vent drives both toward ambient; exact key set `{heater, fan_cooler, fogger, vent}` enforced (`src/greenhouse_model.py:62-65`, `tests:170-190`) |

## MODEL requirement mapping (MODEL-01..04, all SATISFIED)

| Req | Verdict | Evidence |
|-----|---------|----------|
| MODEL-01 (coupled T/w ODE plant, 24h, D-01) | SATISFIED | `src/greenhouse_model.py:55-84`; 24h bounded/finite check passes |
| MODEL-02 (4 actuators, probe-verified directions + D-06 linear duty) | SATISFIED | `tests:18-47` (directions), `tests:79-91` (50% duty = half of 100% within 1e-6) |
| MODEL-03 (seedable 24h CSV, 97 rows, interp per D-10/D-12) | SATISFIED | `src/weather_profile_generator.py:15-27`; `tests:122-142` (byte-identical regen + peak-hour guard); `tests:94-119` (load + interp); post-fix peak at 915 min = 15.25h, within ±2h of `t_peak_h=15.0` |
| MODEL-04 (pure stateless 3-tuple step API, fail-fast keys, clamped bounds) | SATISFIED | `tests:145-167` (3-tuple, determinism, RH [0,100], missing/unknown key raise); `src/greenhouse_model.py:42-45` RH clamp, `:80` wsat clamp, `:82-83` finite/physical asserts; 12-key D-07 `params` dict (`src/greenhouse_model.py:16-29`) importable |

## Key links (all WIRED)

- `tests/test_greenhouse_model.py` imports `step`, `params`, `load_weather_profile`, `relative_humidity` from `src.greenhouse_model` (in-body imports, lines 20/52/81/97/148/171) — all 7 checks exercise the one production module.
- `src/weather_profile_generator.py:25-26` writes the CSV; `src/greenhouse_model.py:95` reads it back via `np.loadtxt(skiprows=1)`; interpolation via `numpy.interp` (`tests:55-56`).
- `notebooks/01_greenhouse_model.ipynb` — 4 code cells, contains `from src.greenhouse_model import`, `plt.plot`, `matplotlib.use` (structural check re-run this session: 4/True/True/True); no duplicated ODE logic.

## Context items accounted for (not flagged)

- **CR-01 fix verified:** `src/weather_profile_generator.py:21-24` now uses cosine with comment "a sine would peak 6h late"; measured peak 15.25h vs `t_peak_h=15.0` ✓; `test_generator_seedability` carries the peak-hour assertion (`tests:135-142`); CSV + notebook PNG regenerated in db83e9b.
- **Bands recalibrated** (`tests:70-76`, comment documents actuals T 13.79..42.12, w 9.82..19.94, RH 32..100) — probe-faithful-superset procedure, same as before.
- **WR-02/WR-03/IN-04/05/06** accepted as documented non-blocking findings per instruction.
- **SECURITY.md** (threats_open: 0) and **VALIDATION.md** (nyquist_compliant, 7/7) taken as given; suite independently re-run green this session.

## Anti-pattern scan

No TODO/FIXME/XXX/placeholder/stub markers in `src/` or `tests/` outputs reviewed; no `return null/{}/[]` stubs; CSV is real generated data; notebook runs headless. Clean.

## Gaps

None. All 4 roadmap success criteria PASS, MODEL-01..04 SATISFIED, 7/7 suite green, CR-01 fix empirically confirmed.

---
_Verified: 2026-09-21_
_Verifier: gsd-verifier (goal-backward)_
_No source files modified. No commit._
