---
phase: "01"
status: findings
depth: standard
files_reviewed: 4
summary: |
  Phase 01 delivers the simulated greenhouse plant (coupled T/w energy-moisture ODEs,
  fixed forward Euler with a documented stability gate), a seedable 24h synthetic
  weather CSV generator, and a plain-assert test suite. All 7 checks pass standalone
  (verified by running `python tests/test_greenhouse_model.py`), and the model's unit
  math checks out against the parameter comments. One proven logic bug found: the
  weather generator's `t_peak_h` parameter is misapplied — the sine peaks 6 hours
  late (empirically verified: peak at ~19:45 with default 15.0), contradicting its
  own docstring and shifting the RH profile with it. Additional robustness gaps:
  all validation is done via `assert` (silently stripped under `python -O`), and
  one test fixture is resolved relative to the process CWD. `src/__init__.py` is a
  one-line package docstring, which is acceptable and not flagged.
critical: 1
warning: 2
info: 3
total: 6
---

# Code Review — Phase 01 (greenhouse-model-weather)

## Summary

The core plant model (`src/greenhouse_model.py`) is a clean, stateless forward-Euler
step function with verified unit math (heat capacity 1.8e4 J/m³·K vs W/m³ inputs →
K/s; vent exchange rates match the ACH comments) and correct fail-fast actuator
contract. `src/weather_profile_generator.py` writes deterministic, byte-identical
CSVs for a fixed seed and correctly anti-correlates RH with temperature — but the
documented "peak at t_peak_h" behavior is off by 6 hours, which is a genuine
correctness defect in the phase's primary data artifact. The test suite is
well-structured and all 7 checks pass, but a CWD-relative fixture path makes one
test brittle outside the repo root. No security issues found (no secrets, no
injection surface, no external exec); the findings below are one logic bug, two
robustness/reliability warnings, and three minor items.

## Findings

### CR-01 — Weather generator temperature peak is 6 h late (`t_peak_h` misapplied)
- **Severity:** critical
- **File:** `src/weather_profile_generator.py:21`
- **Description:** `phase = 2*np.pi*(t_h - t_peak_h)/24.0` — a sine reaches its
  maximum at phase π/2, i.e. at `t_peak_h + 6h`, not at `t_peak_h`. The docstring
  (line 7) promises "the temperature peak at t_peak_h", and the default
  `t_peak_h=15.0` (3 PM) is the natural greenhouse reading. Verified empirically:
  running the generator with defaults yields the temperature peak at hour ~19.75
  and the RH minimum (anti-correlated, line 23) at ~19.5 — a full 6-hour shift
  that propagates into every controller/GA/dashboard comparison downstream. The
  existing test (`test_generator_seedability`) only checks byte-identity, so the
  defect is invisible to the suite.
- **Suggestion:** switch to a cosine so the peak lands exactly at `t_peak_h`, and
  add a peak-hour assertion to the test suite:
  ```python
  phase = 2*np.pi*(t_h - t_peak_h)/24.0
  T_out = t_mean + t_amp*np.cos(phase) + rng.normal(0, 0.5, t_h.size)
  RH    = np.clip(rh_mean - rh_amp*np.cos(phase) + rng.normal(0, 3.0, t_h.size), 30, 95)
  ```
  ```python
  # in tests: assert /24*argmax(T_out) is within ±2h of t_peak_h
  ```

### WR-02 — All validation relies on `assert`; guards vanish under `python -O`
- **Severity:** warning
- **File:** `src/greenhouse_model.py:63-67, 82-83, 97-99`
- **Description:** The actuator-key contract, duty-range checks, forward-Euler
  stability gate, finite-state asserts, and the weather-file invariants in
  `load_weather_profile` are all bare `assert`s. Python strips every `assert` under
  `python -O` / `PYTHONOPTIMIZE=1`, after which `step()` can run an unstable
  integration (NaN propagation unchecked) and `load_weather_profile()` accepts
  files that violate the time/RH invariants. This is a documented design choice
  ("fail-fast asserts, D-13"), but the stability gate and the file validation sit
  at an I/O trust boundary (hand-editable CSV) where silent failure is most
  damaging — and the tests deliberately catch `AssertionError`, so any conversion
  is a coordinated change.
- **Suggestion:** raise `ValueError` for the external-file invariants in
  `load_weather_profile`, keep an explicit `if (params["X_v"] + params["k_c"]) * dt >= 1: raise RuntimeError(...)` for the gate, and leave internal invariants as asserts for -O-stripped purity; or document the no-`-O` requirement at module top.

### WR-03 — Test depends on CWD-relative weather fixture path
- **Severity:** warning
- **File:** `tests/test_greenhouse_model.py:54`
- **Description:** `load_weather_profile("weather/weather_profile.csv")` resolves
  against the process CWD, not the repo root. The standalone runner fixes
  `sys.path` (line 186) but not the working directory, and pytest does not chdir
  to the rootdir either — so invoking the suite from any directory other than the
  repo root fails with `FileNotFoundError`, even though the imports succeed. This
  reduces test reliability for CI/IDE runners that start elsewhere.
- **Suggestion:** anchor the path to the test file:
  ```python
  import os
  _HERE = os.path.dirname(os.path.abspath(__file__))
  load_weather_profile(os.path.join(_HERE, "..", "weather", "weather_profile.csv"))
  ```

### IN-04 — `wsat_g_per_kg` unguarded at T ≥ 100 °C; silent negative-w path
- **Severity:** info
- **File:** `src/greenhouse_model.py:37-39` (used at `:77`, `:80`)
- **Description:** As T → 100 °C, `es_pa` → 101325 Pa = p, so the denominator
  `p - es` → 0 (division by zero) and goes negative above 100 °C (wsat negative).
  In `step()` the clamp at line 80 then snaps `w_new` negative while the guards
  `abs(T_new) < 1e3` and `np.isfinite(w_new)` still pass — nothing fires, and RH
  silently clamps to 0. Unreachable with the current tuned parameters, but a
  one-line guard would turn a silent garbage state into a fail-fast.
- **Suggestion:** add `assert T_C < 99.0` in `wsat_g_per_kg` (or clamp `w_new >= 0.0`
  in `step` after the min-clamp).

### IN-05 — `load_weather_profile` docstring overstates its validation
- **Severity:** info
- **File:** `src/greenhouse_model.py:91-93` (check at `:97`)
- **Description:** The docstring says it "validates monotonic integer minutes", but
  line 97 only enforces strict monotonicity (`np.diff(t_min) > 0`); fractional
  minutes pass unremarked. The generator always writes integers, so there is no
  current impact — the docstring is simply ahead of the code.
- **Suggestion:** either add `np.all(t_min == np.floor(t_min))` to the assertion or
  reword the docstring to "monotonic minutes".

### IN-06 — `params` is a mutable module-level dict (determinism risk)
- **Severity:** info
- **File:** `src/greenhouse_model.py:16-29`
- **Description:** `step()` reads the `params` dict at call time; any consumer (GA
  fitness loop, notebooks) can mutate a key and permanently skew every later run.
  The stated guarantees — "pure and stateless (D-15)" and deterministic GA reruns
  (D-12) — then silently depend on nobody mutating module globals.
- **Suggestion:** expose `params` read-only, e.g. `params = MappingProxyType({...})`
  (import from `types`), or document it as frozen after import.

## Verification

- [x] All 4 files read in full (`src/__init__.py`, `src/greenhouse_model.py`,
      `src/weather_profile_generator.py`, `tests/test_greenhouse_model.py`)
- [x] `python tests/test_greenhouse_model.py` run from repo root — all 7 checks PASS
- [x] Unit math traced against param comments: `C_vol`/`P_*` → K/s; `L_v` ≈ rho·cp·ACH/3600; `X_v` = ACH/3600 ✓
- [x] Euler stability gate verified: (X_v + k_c)·dt = 1.4e-3·60 = 0.084 < 1 ✓
- [x] Phase-peak claim empirically tested (peak at ~19.75 h with `t_peak_h=15.0`) — bug confirmed
- [x] No secrets, injection surface, or unsafe calls found; `src/__init__.py` marker acceptable
- [x] No source files modified

## Sign-Off

Reviewed by: gsd-code-reviewer (standard depth) — 2026-09-21

Reviewed files: `src/__init__.py`, `src/greenhouse_model.py`,
`src/weather_profile_generator.py`, `tests/test_greenhouse_model.py`

**Verdict:** findings — 1 critical, 2 warnings, 3 info. CR-01 must be fixed before
the generated weather is consumed by the controller/GA phases; WR-02/WR-03 are
recommended fixes before downstream reliance.

---

_Reviewed: 2026-09-21_
_Reviewer: gsd-code-reviewer_
_Depth: standard_