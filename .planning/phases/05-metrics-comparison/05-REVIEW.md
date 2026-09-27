---
phase: "05"
status: findings
depth: standard
files_reviewed: 3
summary: |
  Phase 05 (metrics-comparison) is in strong shape: all six metric kernels, the
  locked weighted cost (1.0/1.0/0.01), and the 4x2 scoreboard harness are
  correct; energy bit-identity with genetic_algorithm.py:187 is exact;
  results/comparison.csv satisfies the frozen contract (header == COLUMNS,
  8 rows, GA rank 1 on holdout with strict relative ordering); and
  python tests/test_metrics.py passes 9/9. Two minor info-level robustness
  nits only — no blockers, no likely-bug warnings.
critical: 0
warning: 0
info: 2
total: 2
---

# Code Review — Phase 05 (metrics-comparison)

## Summary

Reviewed `src/metrics.py` (203 lines), `tests/test_metrics.py` (191 lines), and
`results/comparison.csv` (header + 8 rows) at standard depth, cross-checking
the two locked contracts by direct read: weights against
`src/genetic_algorithm.py:50` (`W1, W2, W3 = 1.0, 1.0, 0.01` — match) and the
energy definition against `src/genetic_algorithm.py:187`
(`E += sum(act.values()) / 60.0` — character-identical to `src/metrics.py:115`;
the prompt's ":186" is off by one, the in-code ":187" reference is the correct
one). The CSV verifies clean: header equals the frozen 14-column COLUMNS,
8 data rows in controller order per weather block, holdout GA cost ~114.28 <
on/off ~513.75 and < PID ~645.26 with GA rank 1. Test run from the repo root
passes 9/9 and rewrites the artifact byte-identically (git shows no
modification). No bugs, no security issues, no dead logic found — two
info-level robustness nits below.

## Findings

### IN-01 — run_closed_loop rejects pathlib.Path with a misleading message
- **Severity:** info
- **File:** src/metrics.py:133
- **Description:** The wrong-file guard asserts
  `isinstance(weather_path, str)`, so a caller passing a `pathlib.Path`
  (e.g. `Path("weather/holdout_21.csv")`) fails with `"weather_path
  required"` — misleading, since a path *was* supplied, only of the wrong
  type. All current callers pass `str`, so nothing breaks today.
- **Suggestion:** Accept any path-like:
  ```python
  assert isinstance(weather_path, (str, os.PathLike)) and str(weather_path), \
      "weather_path required"
  weather_path = os.fspath(weather_path)
  ```

### IN-02 — Unreachable branch guard in compare() output-dir creation
- **Severity:** info
- **File:** src/metrics.py:190-192
- **Description:** `d = os.path.dirname(os.path.abspath(out_path))` is never
  empty (abspath always contains a directory component), so `if d:` is always
  true and the guard is dead — harmless defensive code, flagged only as
  dead-branch clutter.
- **Suggestion:** Drop the conditional and call `os.makedirs(d,
  exist_ok=True)` unconditionally, or leave as-is; no behavior change either
  way.

## Verification

- [x] Read `src/metrics.py` in full — kernels (rmse/iae/ise/settling/
      overshoot/energy/weighted_cost), `run_closed_loop`, `all_metrics`,
      `compare` all trace correctly; asserts match the fail-fast contract
      asserted by `test_nan_failfast`
- [x] Read `tests/test_metrics.py` in full — 9 `test_*` functions, relative
      (never exact-value) holdout ordering, tmp-path CSV round-trip that never
      clobbers the committed artifact
- [x] Read `results/comparison.csv` — header == frozen COLUMNS (14 cols),
      8 rows, per-block controller order, holdout GA rank 1,
      GA (114.28) < on/off (513.75) and < PID (645.26)
- [x] Energy bit-identity verified by direct comparison:
      `src/metrics.py:115` == `src/genetic_algorithm.py:187`
- [x] Weights verified by direct comparison: `src/metrics.py:30` ==
      `src/genetic_algorithm.py:50` (1.0/1.0/0.01)
- [x] Ran `python tests/test_metrics.py` from repo root — 9/9 PASS,
      "all checks passed"
- [x] `git status` shows no modifications to reviewed files (test-run rewrite
      of the CSV is byte-identical); weather inputs
      `weather/weather_profile.csv` and `weather/holdout_21.csv` both present
- [x] No source files modified; nothing committed

## Sign-Off

Two info-level nits, zero critical, zero warning. Phase 05 meets its locked
contracts (both weathers, pandas-free columnar return + CSV, remainder-of-run
settling with inf marker, six metrics + locked cost + per-block rank, strict
relative holdout ordering). Safe to proceed; IN-01/IN-02 are optional polish.

_Reviewed: 2026-09-27T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
