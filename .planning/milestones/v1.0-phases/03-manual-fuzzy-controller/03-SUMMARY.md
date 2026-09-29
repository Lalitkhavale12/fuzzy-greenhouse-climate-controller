---
phase: 03-manual-fuzzy-controller
plan: "03"
subsystem: control
tags: [fuzzy, mamdani, velocity-form, closed-loop, proof-notebook]
requires: [01-greenhouse-model-weather, 02-baseline-controllers]
provides: [fuzzy-controller, fuzzy-suite, fuzzy-proof-notebook]
affects: [04-ga-optimization, 05-metrics, 06-dashboard-trail]
tech-stack:
  added: []
  patterns: [velocity-form-fuzzy-PI, macvicar-whelan-table, min-max-centroid, split-range, conditional-integration-freeze]
key-files:
  created: [src/fuzzy_controller.py, tests/test_fuzzy_controller.py, notebooks/03_fuzzy.ipynb, notebooks/03_fuzzy.png]
  modified: []
decisions:
  - Explicit mfs centers/widths indexing in fuzzy_step (plan star-unpack yields dict keys)
  - Near-zero (0.05) at-setpoint bound; fogger ~0.015 first call is structural one-sided-grid centroid
  - Authority-relative centroid thresholds (0.05 of +-0.1 du universe, not 0.3)
  - Unbounded-windup unguarded AW variant mirroring PID precedent
metrics:
  duration: single-session
  completed: 2026-09-22
  tokens_estimate: 55000
status: complete
---

# Phase 03 Plan 01: Manual Fuzzy Controller Summary

Hand-tuned velocity-form Mamdani fuzzy controller tracking 25 C / 70 %RH stably for 24 h on seed-7 weather (T-IAE 2.73 C-h, below the 60 honesty bound, 2 crossings in last 6 h), emitting the exact 4-key duty dict the GA and metrics phases consume, proven via plain-assert suite plus proof notebook plus PNG with zero new dependencies.

## Per-Task Results

### Task 1 — Tracer: end-to-end velocity-form fuzzy loop (commit a093dd7)
Created `src/fuzzy_controller.py`: LABELS 5-tuple, FUZZY_MFS named centers/widths dict at probe universes (eT ±4 C, deT ±0.5 C/min, eH ±30, deH ±6/min, du/dv ±0.1/step), MacVicar-Whelan diagonal RULES (equilibrium RULES[2,2]=2, ZO column and damping row [0,1,2,3,4]), tri helper, shared infer core (input clipping, min-implication, max-aggregation, 201-point centroid, zero-fire 0.0), and fuzzy_step (finite asserts, fail-loud pT/pH/uT/uH keys, per-minute error-rate, T [-1,1] split-range with vent=fan_cooler, RH [0,1] to fogger, conditional-integration freeze both rails both loops). Verified: at-setpoint near zero, cold charges heater (0.1 first step), 240-step smoke finite with mutual exclusion.

### Task 2 — Expansion: plain-assert fuzzy suite FUZZ-01..06 (commit d94c746)
Created `tests/test_fuzzy_controller.py` (8 checks, standalone runner, in-body imports): signs, error-rate liveness (flat vs +0.5 C/min ramp differ), MF shape/overlap/universes, RULES table, output mapping (exact key order, [0,1], mutual exclusion, vent mirror), centroid surface + determinism, anti-windup freeze strictly improving IAE, 24 h integration (1440 steps, T-IAE 2.73, RH [66.3,100], <12 crossings, setpoints-as-args, bit-identical reruns, NaN raises). All green; baseline and plant suites still green.

### Task 3 — Expansion: proof notebook 03_fuzzy plus PNG (commit 7033de0)
Created `notebooks/03_fuzzy.ipynb` (Agg, imports from src only, regen-if-absent seed-7 weather, single fuzzy run printing T-IAE 2.73, trace + duty + 6-panel MF-shape figure, honest RH-saturation note, savefig dpi 120) and `notebooks/03_fuzzy.png` (294 KB). nb-ok structural check passes; no duplicated plant/inference logic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Star-unpacking an mfs dict yields keys, not arrays**
- Found during: Task 1 (tracer verify crashed with numpy clip UFuncNoLoopError on `<U1` dtype)
- Issue: plan/RESEARCH snippet `infer(eT, dT, *mfs["eT"], ...)` iterates dict keys ("centers","widths" strings)
- Fix: explicit `mfs["eT"]["centers"], mfs["eT"]["widths"]` ordering in both infer calls
- Commit: a093dd7

**2. [Rule 1 - Bug] Plan tracer threshold `<1e-9` contradicts one-sided RH grid math**
- Found during: Task 1 (fresh at-setpoint call returns fogger 0.015, not <1e-9)
- Issue: ZO triangle centered at 0 on the [0,1]-only RH grid centroids to ~0.014 by construction; plan acceptance criteria say "near zero" but the verify literal demands exact zero
- Fix: verify against near-zero bound 0.05 (fogger 0.015 structural, T-loop duties exact 0); acceptance criteria honored
- Commit: a093dd7

**3. [Rule 1 - Bug] Centroid must_have thresholds exceed the locked output universe**
- Found during: Task 2 (`du(5,0)` returns 0.1 — full du authority — never >0.3)
- Issue: must_have "delta above +0.3" is unreachable with the non-negotiable du universe ±0.1/step; RESEARCH probe's ±0.837 surface numbers predate the final ±0.1 scaling
- Fix: authority-relative thresholds >0.05 / <-0.05 (half of full ±0.1 authority); intent (surface spans authority, centered holds) preserved
- Commit: d94c746

**4. [Rule 2 - Missing critical] Unguarded AW variant must wind up unbounded to mirror PID precedent**
- Found during: Task 2 (clip-every-step unguarded variant scored 4.60 vs guarded 4.76 — freeze looked worse)
- Issue: clipping the unguarded accumulator to [-1,1] each step leaves only a sub-rail edge effect, unlike PID's unbounded `_pid_unguarded` integrator that produced the 3.5x margin
- Fix: unguarded variant accumulates unclipped/unfrozen (clip only at emission for step()); frozen variant now strictly wins
- Commit: d94c746

## Threat Flags

None — no new surface. All `<threat_model>` mitigations implemented: finite-float asserts on every numeric entry arg (T-03-01, NaN suite test), input clipping to MF universes + zero-fire 0.0 fallback (T-03-02), np.clip every accumulation + conditional-integration freeze both rails both loops (T-03-03), fresh-state-on-None + fail-loud key loop + bit-identical determinism test (T-03-04), FUZZY_MFS read-only documented in module docstring, never assigned (T-03-05), zero new dependencies (T-03-SC).

## Self-Check

- src/fuzzy_controller.py, tests/test_fuzzy_controller.py, notebooks/03_fuzzy.ipynb, notebooks/03_fuzzy.png all present
- Commits a093dd7, d94c746, 7033de0 on main, no unintended deletions
- All three suites green; nb-ok prints; PNG 294 KB; no new packages
