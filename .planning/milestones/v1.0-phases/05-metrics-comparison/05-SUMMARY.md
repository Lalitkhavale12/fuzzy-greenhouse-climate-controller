---
phase: 05-metrics-comparison
plan: 01
subsystem: metrics-scoreboard
tags: [metrics, scoreboard, rmse, iae, ise, settling, overshoot, energy, ga-verdict]
requires: [phase-04-ga-params, both-weathers]
provides: [metrics-kernels, compare-harness, comparison-csv]
affects: [phase-06-notebooks, phase-07-dashboard]
tech-stack:
  added: []
  patterns: [pure-numpy-kernels, parameterized-closed-loop, csv-DictWriter-artifact, plain-assert-suite]
key-files:
  created: [src/metrics.py, tests/test_metrics.py, results/comparison.csv]
  modified: []
decisions:
  - "list-of-dicts compare() return (DictWriter/DictReader zero-reshaping round-trip)"
  - "float('inf') never-settled marker (csv 'inf' parses back losslessly)"
  - "rank 1..4 within each weather block (holdout rank is the verdict)"
  - "overshoot absolute positive-side-only per channel (startup transient excluded)"
metrics:
  duration: tracer 3.4s per compare run; suite all-pass; five-suite regression green
  completed: 2026-09-27
status: complete
actuals:
  tokens: 28000
  tasks: 3
  commits: 3
---

# Phase 05 Plan 01: Metrics & Comparison Summary

One table where GA sits ranked #1 on holdout weighted cost — `src/metrics.py` kernels plus `compare()` harness plus `results/comparison.csv`, proven by `tests/test_metrics.py`.

## Per-task results

### Tracer: kernels plus harness plus compare end-to-end to CSV (da9082d)
- Created `src/metrics.py`: kernels rmse/iae (`sum|e|*dt/3600`)/ise/settling_time_min (joint-band last-exit, 0.5/3.0, 0.0 clean, inf final-violation)/overshoot/energy_duty_hours (verbatim `E += sum(act.values()) / 60.0` citing genetic_algorithm.py:187)/weighted_cost (1.0/1.0/0.01), frozen 14-name COLUMNS, CONTROLLERS 4-step table, WEATHERS train-seed7 + holdout-seed21, run_closed_loop with REQUIRED weather_path, all_metrics, compare with per-block rank + single DictWriter.
- Verify: `tracer-ok 8` exit 0.

### Task: full metrics suite proving ordering identity and round-trip (920afbe)
- Created `tests/test_metrics.py`: 9 checks, plain-assert + `__main__` runner, in-body imports, sys.path root-prepend, tempfile round-trip (never clobbers committed CSV), hang guard 600s.
- Verify: `python tests/test_metrics.py` → all 9 PASS, `all checks passed`.

### Task: generate committed scoreboard CSV plus regression gate (7a47a9b)
- `results/comparison.csv`: header == COLUMNS exactly, 8 rows, rank 1..4 per block, GA rank 1 on both blocks.
- Regression: all five suites green (greenhouse_model 7, baseline 8, fuzzy 9, genetic_algorithm 9, metrics 9).
- Verify: suite exit 0 + 8 labeled costs CLI.

## Scoreboard (cost = 1.0*IAE_T + 1.0*IAE_H + 0.01*E)

| controller | train-seed7 | holdout-seed21 |
|------------|------------|----------------|
| ga_fuzzy   | 107.14 (rank 1) | 114.28 (rank 1) |
| onoff      | 502.74 (rank 2) | 513.75 (rank 2) |
| fuzzy      | 641.54 (rank 3) | 644.03 (rank 3) |
| pid        | 643.24 (rank 4) | 645.26 (rank 4) |

Holdout verdict: GA 114.28 < on/off 513.75 AND < PID 645.26 (strict ordering). Train/holdout blocks differ for every controller. Energy identity: 9.4317 == fitness 9.4317 exact `==`.

## Deviations from Plan

None — plan executed exactly as written. No Rule 1-4 triggers: energy verbatim from first write, ordering matched reference numbers on first run, zero new dependencies (NumPy + stdlib csv only).

## Threat flags

None — mitigations implemented as specified: fail-fast finite/non-empty/equal-length asserts in every kernel (T-05-02, suite NaN-injection expects AssertionError), fixed default `results/comparison.csv` with makedirs-on-dirname-only (T-05-01), GA leg via `ga_fuzzy_step` + schema-v2 validation only (T-05-03), zero new deps (T-05-04/T-05-SC).

## Self-Check: PASSED

- `src/metrics.py`, `tests/test_metrics.py`, `results/comparison.csv` all FOUND on disk.
- Commits da9082d, 920afbe, 7a47a9b all FOUND in `git log`.
