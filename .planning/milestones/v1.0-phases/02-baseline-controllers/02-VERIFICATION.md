---
phase: 02-baseline-controllers
status: verified
goal_achieved: true
date: 2026-09-21
suite: tests/test_baseline_controllers.py 8/8 PASS, tests/test_greenhouse_model.py 7/7 PASS
fix_commit: a795b7b
---

# Phase 02 (baseline-controllers) Verification Report

**Phase goal:** On/off and PID controllers that track setpoints on the plant — the benchmarks to beat.
**Verdict:** VERIFIED — goal achieved. No gaps.

## Roadmap success criteria (4/4)

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | `onoff_controller.py` toggles actuators fully on/off by error threshold | PASS | `src/onoff_controller.py:26-37` — latch set/reset on wide band vs narrow asymmetric release with strict inequalities; `tests/test_baseline_controllers.py:33-53` `test_onoff_hysteresis` PASS (fresh-at-setpoint all-zero, latch/hold at 24.8, exact-edge hold at 25.0, release at 25.5, cooling mirror with vent). Spot-check: `onoff_step(20,70,25,70,None)` → `heater 1.0, fan_cooler 0.0` (verified live). |
| 2 | `pid_controller.py` returns continuous control signals from P, I, D terms | PASS | `src/pid_controller.py:15-16` GAINS (Kp_T 0.3/Ki_T 0.03/Kd_T 0, Kp_H 0.03/Ki_H 0.004/Kd_H 0); `:33-42` positional P+I+D with conditional-integration anti-windup both sides; `test_pid_signs` + `test_pid_integral_required` (P-only IAE > 3× guarded PI, proving I term live) both PASS. Spot-check: `pid_step(20,70,25,70,None)` → `heater 1.0, fan_cooler 0.0` continuous (verified live). |
| 3 | Both controllers drive the model toward T/RH setpoints in closed-loop sim | PASS | `tests/test_baseline_controllers.py:182-197` `test_closed_loop_24h` PASS — 1440×dt=60 s per controller on seed-7 weather, finite traces, RH in [0,100], T-IAE < 60 C-h each. Notebook headless exec agrees (on/off 7.38, PID 1.08 C-h per SUMMARY). |
| 4 | Outputs are comparable actuator command structures shared with later controllers | PASS | Both return exactly `{heater, fan_cooler, fogger, vent}` in that insertion order — `src/onoff_controller.py:38-41`, `src/pid_controller.py:44`; asserted per-step in `test_closed_loop_24h:195` and `test_controller_signatures:164`; split-range mutual exclusion (heater vs fan_cooler never both > 0) asserted `:197`. Pluggable into `step()` — closed-loop helper `:22-26` calls `controller_step(T, rh, 25.0, 70.0, st)` then `step(60.0, act, ...)` green. |

## Requirements BASE-01..03 (3/3)

| Req | Verdict | Evidence |
|-----|---------|----------|
| BASE-01 (on/off fully on at threshold error) | SATISFIED | SC-1 evidence above + `test_onoff_mutual_exclusion` PASS (reachable-sequence sweep, heater/fan never both positive). |
| BASE-02 (PID continuous P/I/D signal) | SATISFIED | SC-2 evidence above + `test_pid_antiwindup_improves` PASS (guarded < unguarded IAE) + new `test_pid_humidity_recovery` PASS (post-fix). |
| BASE-03 (state + setpoint in, actuator commands out) | SATISFIED | Setpoints are live fn args (`test_controller_signatures:161-163` — 25/70 vs 22/60 differ); caller-owned state, fresh-on-None, bit-identical reruns (`:166-172`); NaN trips entry assert (`:174-179`). |

## Post-review fixes (a795b7b) — confirmed in code and green suite

- **WR-01 (RH anti-windup two-sided):** `src/pid_controller.py:40` now freezes on both `(v_raw > 1.0 and eH > 0) or (v_raw < 0.0 and eH < 0)`; new `test_pid_humidity_recovery` (`tests/test_baseline_controllers.py:128-142`, 400 humid steps → `|iH| < 1e6`, fogger wakes within 60 dry steps) PASS. Suite is 8/8.
- **WR-02 (degenerate-input guards):** `src/onoff_controller.py:21` band positivity assert + `:23-24` latch-key asserts; `src/pid_controller.py:25-28` state/gains key asserts. Live probe: `onoff_step(..., band_T=-0.5)` now raises `AssertionError: hysteresis bands must be positive` (loud failure, mutual-exclusion invariant protected) instead of the review-time heater+cooler contradiction.
- **IN-01/IN-02:** Accepted as documented (assert-style validation consistent with Phase-1; `gains=GAINS` never mutated in-repo).

## Threat model / validation context (not re-verified, taken as stated)

- SECURITY.md: all 3 PLAN threats closed (threats_open: 0). Entry `np.isfinite` asserts present `src/onoff_controller.py:18-20`, `src/pid_controller.py:21-23`; zero new deps (numpy only in src).
- VALIDATION.md nyquist_compliant, map green. Plant suite 7/7 green — no cross-phase regression (re-ran myself).

## Proof artifacts

- `notebooks/02_baselines.ipynb`: 6 cells, src-only imports verified (`from src.onoff_controller import` ✓, `from src.pid_controller import` ✓, `matplotlib.use("Agg")` ✓, `02_baselines.png` ✓).
- `notebooks/02_baselines.png`: 162,068 bytes (> 10 KB) ✓, no duplicated plant math per REVIEW JSON inspection.

## Gaps

None. All 4 roadmap criteria, all 3 requirements, both review warnings closed with regression tests, both suites green.
