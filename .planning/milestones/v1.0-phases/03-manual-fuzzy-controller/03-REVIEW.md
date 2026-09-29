---
phase: "03"
status: findings
depth: standard
files_reviewed: 3
summary: |
  Reviewed the Phase 03 velocity-form dual-loop Mamdani controller, its 8-check
  suite, and the proof notebook. T-loop math traces clean against 03-RESEARCH.md
  Patterns 1-4 (tri shape, min-max, centroid, per-minute rate, split-range,
  MacVicar-Whelan symmetry) and all 8 tests pass. One real control-logic bug:
  the RH loop defuzzifies over a [0,1]-only grid while its dv MFs are symmetric
  ±0.1, so dv can never go negative — the fogger ratchets up monotonically
  (proven: 1.0 after 120 steps held exactly at setpoint; never decreases once
  over the full 24 h run), the NB/NS dv terms are dead, and the documented
  RH lower-rail anti-windup branch is unreachable. Two minor info items round
  out the report. The T-only FUZZ-06 bar is unaffected.
critical: 0
warning: 1
info: 2
total: 3
---

# Code Review — Phase 03 (manual-fuzzy-controller)

## Summary

Standard-depth review of `src/fuzzy_controller.py` (89 lines), `tests/test_fuzzy_controller.py`
(235 lines, 8 checks), and `notebooks/03_fuzzy.ipynb` (4 code cells + PNG proof). Ran the suite
from the repo root: **8/8 PASS** (`fuzzy T-IAE 2.73`). Traced the inference math cell-by-cell
against `03-RESEARCH.md` Patterns 1–4 and the locked probe verdicts: tri fuzzification,
min-implication / max-aggregation, 201-point centroid with zero-fire 0.0, per-minute error-rate
via `/(dt/60)`, MacVicar-Whelan diagonal table (verified anti-diagonal symmetry and the
damping row/column), velocity accumulation, and split-range output all check out. The T-loop
is correct, including its conditional-integration freeze on both rails. The single substantive
defect is in the RH loop's output universe (WR-01, proven numerically, not pattern-matched).
No secrets, injection surfaces, `eval`, or deserialization risks exist in this NumPy-only scope;
per instructions the `mfs=FUZZY_MFS` read-only default (AR-01), dual-loop 4-key shape, shared
rule table, T-only FUZZ-06 bar, and structural-saturation narrative were not flagged.

## Findings

### WR-01 — RH-loop Δv can never go negative: fogger ratchets up and can never ramp down

- **Severity:** warning
- **File:** src/fuzzy_controller.py:78-86
- **Description:** The RH `infer()` call defuzzifies over `lo=0.0, hi=1.0`, but the `dv` MF set
  is symmetric (`centers [-0.1, -0.05, 0, 0.05, 0.1]`, `widths 0.05`). The NB/NS output
  triangles sit entirely left of the grid, so they contribute exactly 0.0 to `agg` on every
  call; the centroid of a non-negative grid is non-negative, and the zero-fire fallback is
  0.0 — hence `dv >= 0` always and `uH` is monotonically non-decreasing. Three proven
  consequences: (1) at perfect equilibrium `dv(0,0) ≈ 0.015/step` (half-triangle centroid),
  so holding exactly 25.0 C / 70 %RH drives fogger to **1.0 within ~67 steps** and pins it
  there (probed); (2) over the real 24 h closed loop the fogger **never decreases once**
  (`np.diff < 0` nowhere; pinned at 0.557 from hour 6 to hour 24 — probed); a soaked plant
  (`eH = -30`) yields `dv = 0.0`, i.e. no dry-back authority at all; (3) the RH lower-rail
  freeze `v_new < 0.0 and eH < 0` (:85) is **unreachable dead code** (`v_new = uH + dv >= 0`
  always), so the documented "conditional-integration freeze on both rails of both loops"
  holds on only 3 of 4 rails — unlike the mirrored PID, whose positional `v` is genuinely
  bidirectional within [0,1] (`src/pid_controller.py:38-42`). The suite bakes the symptom in
  as "structural" (`test_fuzzy_signs` comment, fogger ~0.015) and never tests a ramp-down,
  which is how this shipped green. The T-only FUZZ-06 bar still passes, but the RH loop is
  effectively write-only-increment: it can add moisture, never withhold it.
- **Suggestion:** Keep the locked [0,1] accumulation/clip bound, but widen the defuzz grid so
  negative increments are representable (exactly as the T-loop already does with [-1,1]):
```python
dv = infer(eH, dH, mfs["eH"]["centers"], mfs["eH"]["widths"],
           mfs["deH"]["centers"], mfs["deH"]["widths"],
           mfs["dv"]["centers"], mfs["dv"]["widths"], -1.0, 1.0)
```
  With this one-line change the equilibrium `dv` becomes exactly 0.0 (full ZO triangle),
  NB/NS terms participate, and the existing lower-rail freeze becomes live with no other
  edits. Add a regression test covering the missing direction, e.g. charge-then-soak plus
  an equilibrium-hold bound:
```python
st = None
for _ in range(30):
    act, st = fuzzy_step(25.0, 50.0, 25.0, 70.0, st)   # dry: charge fogger
high = act["fogger"]
assert high > 0.0
for _ in range(60):
    act, st = fuzzy_step(25.0, 95.0, 25.0, 70.0, st)   # soaked: must dry back
assert act["fogger"] < high, (high, act)
st = None
for _ in range(120):
    act, st = fuzzy_step(25.0, 70.0, 25.0, 70.0, st)   # equilibrium: hold, not ratchet
assert act["fogger"] < 0.05, act
```
  Note: fixing this changes the closed-loop RH trajectory, so `notebooks/03_fuzzy.png` must
  be regenerated headlessly (Agg) afterward.

### IN-01 — Runtime input validation relies on `assert`, which vanishes under `python -O`

- **Severity:** info
- **File:** src/fuzzy_controller.py:65-70
- **Description:** Finite-input guards (`np.isfinite` on `T_C`/`rh_pct`/setpoints/`dt`, `dt > 0`)
  and the fail-loud state-key loop are all bare `assert`s. Under `python -O` they are
  stripped: NaN then flows into `tri`/`infer` (NaN poisons `agg`, centroid returns NaN) and
  a partial state dict fails later with a bare `KeyError` instead of the intended message.
  The suite itself depends on the `assert` mechanism (`test_closed_loop_24h` expects
  `AssertionError` for NaN), so this is a latent robustness wart, not a live bug — flagged
  info-only because no `-O` usage exists in this project.
- **Suggestion:** Replace with explicit raises (and update the NaN test expectation to match):
```python
if not (np.isfinite(T_C) and np.isfinite(rh_pct)):
    raise ValueError(f"non-finite plant inputs: T_C={T_C!r}, rh_pct={rh_pct!r}")
for k in ('pT', 'pH', 'uT', 'uH'):
    if k not in st:
        raise KeyError(f"state missing key {k!r}")
```

### IN-02 — Unit-level "determinism" asserts are tautological self-comparisons

- **Severity:** info
- **File:** tests/test_fuzzy_controller.py:131-132
- **Description:** `assert du(2.0, 0.0) == du(2.0, 0.0)` (twice; line 132 additionally
  re-checks `du(-3.0, 0.25) == du(-3.0, 0.25)`) compares a pure deterministic function to
  itself in the same process — it cannot fail except via NaN, so it covers "determinism" in
  name only. Real determinism *is* covered at integration level (bit-identical 24 h reruns,
  lines 207–209), which is why this stays info: the duplicate asserts add false-confidence
  coverage rather than a reliability hole.
- **Suggestion:** Drop the duplicated line 132 and make the remaining assert meaningful, e.g.
  determinism across independently constructed MF dicts / fresh states, or rely on the
  integration-level rerun check with a comment pointing at it.

## Verification

- [x] `python tests/test_fuzzy_controller.py` from repo root — 8/8 PASS, `fuzzy T-IAE 2.73`
- [x] Traced inference math against `03-RESEARCH.md` Patterns 1–4 (spot-check): tri shape,
  min-max core, centroid + zero-fire, velocity accumulation, split-range, per-minute rate,
  MF universes (eT ±4 / deT ±0.5 / eH ±30 / deH ±6 / Δ ±0.1), shared diagonal RULES incl.
  anti-diagonal symmetry — all faithful (root-level `RESEARCH.md` does not exist; the
  phase-level `03-RESEARCH.md` was used as the pattern source)
- [x] Probed WR-01 numerically: `dv(0,0)=0.015`, `dv(-30,0)=0.0`, fogger→1.0 after 120 steps
  at setpoint, 24 h fogger monotone non-decreasing (0.557 pinned from 6 h on)
- [x] Notebook verified by JSON read (jupyter CLI absent, per instructions): src-only imports
  (`greenhouse_model`, `weather_profile_generator`, `fuzzy_controller`) + stdlib `os`,
  `matplotlib.use("Agg")` before `pyplot`, seed-7 regen-if-absent weather, setpoints passed
  as args, `savefig("notebooks/03_fuzzy.png")` present and PNG exists on disk
- [x] Actuator contract cross-checked: emitted key order/set matches `step()` expected
  `{"heater","fan_cooler","fogger","vent"}` in `src/greenhouse_model.py:62`
- [x] Anti-windup polarity cross-checked against `src/pid_controller.py:35-41` conventions
- [ ] Notebook not executed (no jupyter CLI; structural JSON verification only, per brief)
- [ ] No exhaustive re-probe of RESEARCH.md signal ranges (spot-check only, per brief)

## Sign-Off

Reviewed: 2026-09-22. Depth: standard. Files reviewed: 3
(`src/fuzzy_controller.py`, `tests/test_fuzzy_controller.py`, `notebooks/03_fuzzy.ipynb`).
Result: 0 critical, 1 warning (RH-loop one-way ratchet, proven), 2 info. The T-loop, rule
table, inference core, suite rigor on the T-side, and notebook proof pattern are sound;
WR-01 should be fixed (one-line grid change + regression test + PNG refresh) before the
Phase-4 GA tunes against this engine, since the GA would otherwise inherit a fogger that
can only ever turn up. No source files modified; no commits made.

_Reviewed: 2026-09-22_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
