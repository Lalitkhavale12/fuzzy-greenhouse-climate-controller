---
phase: 02-baseline-controllers
plan: 01
type: execute
status: complete
tokens: 36000
key-files:
  created:
    - src/onoff_controller.py
    - src/pid_controller.py
    - tests/test_baseline_controllers.py
    - notebooks/02_baselines.ipynb
    - notebooks/02_baselines.png
decisions:
  - Probe-verified bands/gains used verbatim (band_T=0.5, band_RH=3.0, GAINS per RESEARCH.md); no re-tuning
  - Anti-windup proven via in-test unguarded twin (_pid_unguarded) rather than a runtime flag, keeping the production signature clean
  - Notebook uses 3x2 per-controller panels (T/RH/duties x on-off/PID)
deviations:
  - none
---

# Phase 02 Plan 01: Baseline Controllers Summary

Honest on/off (hysteresis) and dual-loop PID baselines tracking 25 C / 70 %RH on the Phase-1 plant, proven in a 24 h closed loop with a proof notebook feeding the Phase-6 trail.

## Per-task results

### Task 1 (tracer): both controllers end-to-end through step() on seed-7 weather
- Created `src/onoff_controller.py` (`onoff_step` with heat/cool/fog latch dict, fresh-on-None, strict-inequality hold, vent mirrors cooling bit) and `src/pid_controller.py` (`GAINS` Kp_T 0.3/Ki_T 0.03/Kd_T 0, Kp_H 0.03/Ki_H 0.004/Kd_H 0; split-range T output; conditional-integration anti-windup). Both assert `np.isfinite` on T_C/rh_pct/setpoints at entry and emit exactly `{heater, fan_cooler, fogger, vent}` in that insertion order.
- Created `tests/test_baseline_controllers.py` with Phase-1 runner conventions and `test_closed_loop_24h` (1440 x dt=60 s per controller; finite traces, RH in [0,100], T-IAE < 60 C-h, heater/fan mutual exclusion).
- Verify: `python tests/test_baseline_controllers.py` prints PASS + all checks passed; plant suite still green.
- Commit: `2caeca9` feat(02-01): tracer both controllers end-to-end through step()

### Task 2 (expansion): unit contract suite
- Added six checks: `test_onoff_hysteresis` (fresh-at-setpoint all-zero, latch/hold/release, exact-edge hold, cooling mirror), `test_onoff_mutual_exclusion` (reachable-sequence sweep), `test_pid_signs` (cold/hot/dry/at-setpoint), `test_pid_antiwindup_improves` (guarded 1.78 < unguarded 5.72 C-h on saturating night-to-day script), `test_pid_integral_required` (P-only 20.9 > 3x guarded PI), `test_controller_signatures` (live setpoint args, exact keys, [0,1], bit-identical reruns, NaN trips assert).
- Heater switches 278/24 h (< 350 bound, matches research probe). Exactly seven `test_` functions. Suite runs < 5 s.
- Verify: all seven PASS + all checks passed; plant suite still green.
- Commit: `8101a60` feat(02-01): unit contract suite hysteresis signs anti-windup determinism

### Task 3 (expansion): 02_baselines proof notebook plus committed PNG
- `notebooks/02_baselines.ipynb` in Phase-1 cell order (title, imports, weather, run x2 with separate states, saturation note, plot). Imports only from `src/`; no duplicated plant math; gains/bands identical to `src/` defaults.
- Headless exec: on/off T-IAE 7.38 C-h, PID T-IAE 1.08 C-h (both < 60, match suite/probes); RH saturates at 100 structurally, documented as the honest D-03 weakness.
- Verify: `nb-ok` + `png-ok` (>10 KB) + suite still green.
- Commit: `f1ca2d9` feat(02-01): 02_baselines proof notebook plus committed PNG

## Threat mitigations (plan <threat_model>)
- T-02-01: `np.isfinite` entry asserts in both controllers; `step()` finite assert stays as backstop.
- T-02-02: fresh-state-on-None + bit-identical determinism test (local single-process harness, accepted with control).
- T-02-SC: zero new dependencies (numpy/matplotlib only, Agg headless).

## Known stubs
None. No placeholders, TODOs, or mock data paths in created files.
