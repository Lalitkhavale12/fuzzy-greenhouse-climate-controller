---
phase: "02"
status: findings
depth: standard
files_reviewed: 4
summary: |
  Both baseline controllers implement the RESEARCH.md control laws faithfully (bands,
  gains, split-range, vent-mirrors-cooling) and all 7/7 checks pass, but adversarial
  probing proved two real robustness defects: the PID RH-loop anti-windup guard is
  one-sided, letting the humidity integrator wind up without bound during the
  documented saturation stretches (600 dry steps to recover after 400 humid steps),
  and onoff_step accepts degenerate inputs that break its own tested mutual-exclusion
  invariant (negative band turns heater+cooler on together; partial state dict raises
  KeyError). Two minor notes (assert-based validation, mutable-default gains) round
  out the report. No security issues found.
critical: 0
warning: 2
info: 2
total: 4
---

# Code Review — Phase 02 (baseline-controllers)

## Summary

Reviewed the four Phase 02 files at standard depth: `src/onoff_controller.py`,
`src/pid_controller.py`, `tests/test_baseline_controllers.py`, and
`notebooks/02_baselines.ipynb` (via JSON inspection — jupyter CLI is absent on this
machine, per instructions). Control-law math was spot-traced against
`.planning/phases/02-baseline-controllers/02-RESEARCH.md` and `python
tests/test_baseline_controllers.py` was executed from the repo root: **7/7 PASS**.
All locked decisions (T-loop vent ownership, hysteresis on/off, independent loops,
setpoints-as-args, dual-loop PID, probe-verified bands/gains, structural RH
saturation, notebook+PNG proof pattern) were treated as intentional and are not
flagged. Implementation matches the research reference code (02-RESEARCH.md:142-150,
177-194) line-for-line on all specified values. Two warnings below are
probe-proven defects, not style nits; no critical/security issues were found.

## Findings

### WR-01 — RH-loop anti-windup is one-sided; humidity integrator winds up without bound during saturation

- **Severity:** warning
- **File:** src/pid_controller.py:34-36
- **Description:** The T-loop freezes its integrator on both saturation sides
  (`u_raw > 1.0 and eT > 0` or `u_raw < -1.0 and eT < 0`, line 31), but the RH-loop
  only freezes upward (`v_raw > 1.0 and eH > 0`, line 35). There is no mirror guard
  for the floor (`v_raw < 0.0 and eH < 0`). While the fogger output is pinned at 0
  with sustained negative error — exactly the "RH pins at 100% for long stretches"
  condition the notebook documents as structural (cell `saturation-note`) — `iH`
  integrates `eH*dt` downward without bound. Proven by probe: 400 steps at
  `rh=100` drives `iH` to **-720,000.0**, after which 600 steps at `rh=50`
  (~10 sim-hours) are needed before `fogger > 0` again. The existing
  `test_pid_antiwindup_improves` only asserts T-loop IAE improvement, so this
  H-loop recovery lag is untested. Effect is degraded (not crashed) control — a
  sluggish fogger after every long humid stretch — and it asymmetrically worsens
  the PID baseline the GA-fuzzy comparison must beat fairly.
- **Suggestion:** Mirror the low-side freeze, symmetric with the T-loop:
```python
if not ((v_raw > 1.0 and eH > 0) or (v_raw < 0.0 and eH < 0)):
    st['iH'] += eH * dt
```
  and extend the test suite with an H-loop recovery assertion (saturate humid, then
  dry; assert fogger responds within N steps).

### WR-02 — onoff_step accepts degenerate inputs that break its own tested invariants

- **Severity:** warning
- **File:** src/onoff_controller.py:15-21
- **Description:** Only finiteness is asserted; `band_T`/`band_RH` are never checked
  `> 0` and the caller-owned `state` dict shape is never validated. Proven by probe:
  (a) `onoff_step(25.3, 70.0, 25.0, 70.0, None, band_T=-0.5)` returns
  `heater=1.0 AND fan_cooler=1.0` — heat commanded while above setpoint, violating
  the mutual-exclusion property `test_onoff_mutual_exclusion` exists to guarantee;
  (b) `onoff_step(25.0, 70.0, 25.0, 70.0, {'heat': True})` raises bare
  `KeyError: 'cool'` at line 36 instead of a diagnostic error. Same gap applies to
  `pid_step` state/gains keys (`gains['Kp_T']`, `st['pT']`). These are garbage-in
  paths today (all in-repo callers pass valid args), but the failure modes are a
  physically contradictory actuation dict and an unhandled exception type.
- **Suggestion:**
```python
assert band_T > 0 and band_RH > 0, "hysteresis bands must be positive"
for k in ('heat', 'cool', 'fog'):
    assert k in st, f"state missing latch key {k!r}"
```
  (and the analogous key check for `pid_step` state/gains). Cheap, matches the
  existing assert style, converts silent nonsense into loud failure.

### IN-01 — Runtime input validation relies on assert (stripped under python -O)

- **Severity:** info
- **File:** src/onoff_controller.py:18-20, src/pid_controller.py:21-23
- **Description:** NaN/non-finite rejection is implemented with `assert`, which the
  interpreter removes under `python -O`, silently disabling the guard the
  `test_controller_signatures` NaN check depends on (`AssertionError` is the
  expected outcome). Consistent with apparent Phase-1 style, so noted as info only.
- **Suggestion:** Keep asserts for internal invariants; raise `ValueError` for
  externally-supplied readings (`T_C`, `rh_pct`, setpoints, `dt`). Update the NaN
  test to expect `ValueError`.

### IN-02 — Mutable module-level dict as default argument (gains=GAINS)

- **Severity:** info
- **File:** src/pid_controller.py:19
- **Description:** The default `gains` parameter binds the live module-level `GAINS`
  object. The function never mutates it, so the hazard is latent rather than live —
  but any caller that mutates the received/default dict in place (or via
  `pid_step.__defaults__`) silently retunes every future default call, including
  cross-test contamination. The test suite already defensively copies
  (`dict(GAINS, Ki_T=0.0, ...)`), which signals the same unease.
- **Suggestion:**
```python
def pid_step(..., gains=None):
    gains = GAINS if gains is None else gains
```

## Verification

- [x] `python tests/test_baseline_controllers.py` from repo root — 7/7 PASS
  (`test_closed_loop_24h`, `test_controller_signatures`, `test_onoff_hysteresis`,
  `test_onoff_mutual_exclusion`, `test_pid_antiwindup_improves`,
  `test_pid_integral_required`, `test_pid_signs`; "all checks passed")
- [x] Control-law math spot-traced vs 02-RESEARCH.md: bands 0.5C/3%RH (:159-164),
  asymmetric release -0.2C/-1%RH (:262, ref impl :146-150), GAINS Kp 0.3/Ki 0.03/Kd 0
  + Kp_H 0.03/Ki_H 0.004 (:177-178), conditional integration (:169-194) — all match;
  release literals and Kd=0-D-on-error handling are spec'd, not flagged
- [x] Notebook JSON verified without execution (no jupyter CLI): 6 cells, src-only
  imports (`greenhouse_model`, `weather_profile_generator`, `onoff_controller`,
  `pid_controller`), `matplotlib.use("Agg")`, seed-7 CSV guard matching
  `generate_weather_profile(out_path, seed=7, ...)` signature, PNG proof artifact
  present (`notebooks/02_baselines.png`, 162 KB, same timestamp as ipynb)
- [x] WR-01 proven by saturation/recovery probe (iH=-720,000 after 400 humid steps;
  600 dry steps to fogger>0); WR-02 proven by negative-band probe (heater+cooler
  both 1.0) and partial-state probe (KeyError: 'cool')
- [x] Explicitly NOT flagged (locked/intentional): vent-mirrors-cooling, hysteresis
  bands+gains+AW scheme, independent loops, setpoints-as-args, RH saturation
  physics, hardcoded -0.2/-1.0 releases (research-spec'd), `src/__init__.py` untouched
- [x] No source files modified; no commits made

## Sign-Off

- **Reviewed:** 2026-09-21
- **Reviewer:** the agent (gsd-code-reviewer)
- **Depth:** standard
- **Status:** findings (0 critical, 2 warning, 2 info — 4 total)
- **Recommendation:** Fix WR-01 (one-line guard + H-loop recovery test) and WR-02
  (input guards) before Phase 05 metrics lock the baselines in; IN-01/IN-02 are
  safe to defer. No security concerns; otherwise the phase is solid and the
  notebook+PNG proof pattern is intact.
