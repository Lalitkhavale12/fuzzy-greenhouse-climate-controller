---
phase: 04-ga-optimization
plan: 01
status: complete
tokens_estimate: 55000
key_files_created:
  - src/genetic_algorithm.py
  - src/ga_fuzzy_controller.py
  - tests/test_genetic_algorithm.py
  - results/ga_optimized_params.json
  - results/ga_run_log.txt
  - notebooks/04_ga_optimization.ipynb
  - notebooks/04_ga_optimization.png
key_files_modified: []
decisions:
  - "BOUNDS paddings per RESEARCH Pattern 1 (centers ~50% beyond hand spans, w_min > 0)"
  - "Holdout seed locked at 21 on an isolated temp path, never passed to fitness"
  - "Duty-hours energy E = sum_steps(sum_actuators(duty))/60, recorded verbatim in results/ga_run_log.txt for Phase 5"
  - "D-06/A2: GA fuzzy alone cross-coupled — 62-D (60 MF + k_heat/k_vent in [0,0.05] duty per pctRH excess), boost after untouched decoupled loops; baselines + hand fuzzy sealed"
  - "JSON schema v2 adds coupling + schema_version; Phase 5/7 consumers must read coupling; v1 JSONs load with zero gains"
deviations:
  - "[Rule 2 - missing critical] init_population draws coupling gains U(lo,hi), not hand-scaled jitter (hand gains are 0.0 — jitter would pin the whole population at zero and the coupling would never be explored)"
  - "[Schema evolution per A2] JSON gains exact key 'coupling'; plan verify key-set updated accordingly (mfs/coupling/fitness/weights/train_weather/train_seed/holdout_seed/population/generations/rng_seed/schema_version/history)"
---

# Phase 04 Plan 01: GA Optimization Summary

One-liner: 62-D cross-coupled GA (train 109.54 -> 107.14) beats both baselines on fresh seed-21 holdout — GA 114.28 < on/off 513.75 AND < PID 645.26.

## Task results

### 1. Tracer: chromosome to holdout win on a tiny budget — DONE (commit 3b5f468)
Built `src/genetic_algorithm.py` (ORDER eT/deT/du/eH/deH/dv, BOUNDS, encode/decode
with sort/clip repair + fresh arrays, evaluate 1.0*IAE_T+1.0*IAE_H+0.01*duty-hours-E
with try/except->inf, tournament-3, BLX-0.5, per-gene gaussian sigma 0.1*range,
elitism-2, single default_rng, individual 0 = hand encoding, per-generation JSON
flush, script entry), `src/ga_fuzzy_controller.py` (load_optimized_mfs fail-fast
validation + ga_fuzzy_step delegating to fuzzy_step), `tests/test_genetic_algorithm.py`.
Suite green; tiny GA 5-6 s (< 30 s).

### 2. Full 50x50 evolution producing the frozen JSON artifact — DONE (run 3)
- Run 1 (commit 352fa17): decoupled 60-D, train 641.54 -> 632.57; holdout GA 634.87
  < PID but > on/off 513.75 — GA-05 blocked on the on/off leg. SUPERSEDED.
- Run 2 (uncommitted JSON, A1/D-04a widened du/dv bounds): train -> 632.86, holdout
  GA 635.37 — null result; gap 100% wet-side per split probe. SUPERSEDED.
- Run 3 (commit 9a9f669, A2/D-06 cross-coupled 62-D, code commit f945e1b):
  `python src/genetic_algorithm.py --population 50 --generations 50 --seed 0`
  (~35 min wall), train best 109.54 (gen 0, random coupled) -> 107.14 (gen 49),
  monotone (elitism-2), 19/50 improving gens. Individual 0 (hand + zero gains)
  stayed 641.54 — the coupling, not MF retuning, carries the win.
  Elite coupling: k_heat 0.05, k_vent 0.05 (both at upper bound).
  JSON schema v2 at results/ga_optimized_params.json (pop 50, gen 50, rng 0,
  train 7, holdout 21, weights 1.0/1.0/0.01, history best+mean length 50).
  Holdout seed-21 (shared fresh weather): GA 114.28 (T 1.66 / H 112.44 / E 18.13)
  < on/off 513.75 (7.40 / 506.21 / 13.75) AND < PID 645.26 (1.07 / 644.10 / 9.66).
  Hand 644.03 for reference. GA-05 bar MET on both legs — relative ordering only,
  no absolute threshold. Framing: intelligent-coupled vs classical-decoupled.

### 3. Proof notebook with convergence plus holdout plus MF plots — DONE (commit 7e4970a)
`notebooks/04_ga_optimization.ipynb` (D-05 pattern: Agg headless, src-only imports,
train CSV loaded-never-regenerated, fresh seed-21 temp-path holdout never near
fitness, no inline evolution, no duplicated engine logic) plots convergence +
4-controller holdout T/RH traces + eH MF before/after overlay, with a verdict cell
asserting GA < on/off AND GA < PID with per-term IAE_T/IAE_H/E breakdown.
Executes headless, verdict asserts pass; `notebooks/04_ga_optimization.png` saved
beside it. Structural check prints nb-ok.

## Deviations from Plan
See frontmatter deviations (both auto-handled, no user decision needed):
gains-init distribution (Rule 2) and the A2 schema-v2 key addition.

## Blocker (Rule 4) — RESOLVED by user decision D-06/A2
Runs 1-2 blocked on the on/off leg (structural wet-side gap, ~121 pts). User
approved cross-coupling the GA fuzzy alone; run 3 clears the bar (114.28 < 513.75).
Baselines and hand fuzzy untouched throughout (sealed phases). No open blockers.

## Holdout numbers (seed 21, shared fresh weather — run 3)
onoff cost 513.75 (T 7.40 / H 506.21 / E 13.75); PID 645.26 (1.07 / 644.10 / 9.66);
hand 644.03 (2.68 / 641.25 / 9.48); GA 114.28 (1.66 / 112.44 / 18.13).

## Suite status
`python tests/test_genetic_algorithm.py`: all 9 tests PASS (incl. zero-gain
identity + positive-boost coupling tests). Regression green: greenhouse_model,
baseline_controllers, fuzzy_controller suites all pass. Notebook structural
check prints nb-ok with PNG present.

## Threat flags
None — mitigations hold as extended (coupling validated fail-fast on load per
T-04-01, gains clipped in decode per T-04-02, fitness->inf incl. coupled path
per T-04-03, JSON-only stdlib, single seeded RNG, zero new dependencies;
fuzzy_controller.py / onoff / pid / greenhouse_model untouched).
