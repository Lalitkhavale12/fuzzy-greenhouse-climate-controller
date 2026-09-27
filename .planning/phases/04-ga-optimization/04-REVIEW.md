---
phase: "04"
status: findings
depth: standard
files_reviewed: 4
summary: |
  Phase 04 delivers a correct-by-construction 62-D coupled GA: encode/decode/repair
  round-trips, W1/W2/W3 weights, inf-boundary fitness, tournament-3/BLX-0.5/gaussian/
  elitism-2 operators, single-RNG discipline, hand-as-individual-0, and JSON schema v2
  all trace cleanly against the locked decisions, and tests/test_genetic_algorithm.py
  passes 9/9. No critical defects found, but review surfaces 3 warnings (init-population
  zero-center pinning that contradicts the code's own coupling-gain fix, a SystemExit-as-
  assertion that aborts the standalone runner, a wall-clock timing assertion) and 8 info
  items (stale mutation denominator, provenance-only seed params, over-strict JSON float
  gating, stale/shared-mutable loader cache, unclosed file handles, mutable default arg,
  notebook weight duplication with no artifact guard, run_ga input-validation gaps).
---

# Code Review — Phase 04 (ga-optimization)

## Summary

Reviewed the four Phase 04 files at standard depth: `src/genetic_algorithm.py` (344 lines,
62-D real-valued GA with D-06/A2 cross-coupling), `src/ga_fuzzy_controller.py` (76 lines,
JSON-backed coupled wrapper), `tests/test_genetic_algorithm.py` (259 lines, 9 checks),
and `notebooks/04_ga_optimization.ipynb` (read as JSON, not executed — no jupyter CLI).
Traced encode/decode/repair round-trip, fitness weights + inf boundary, operator shapes,
elitism bookkeeping, RNG discipline, coupling application, and JSON schema against the
locked decisions (tracking-first 1.0/1.0/0.01, 50x50 budget, seed-7/seed-21, coupled-GA-
only, relative holdout bar). Ran `python tests/test_genetic_algorithm.py` from the repo
root: **9/9 PASS** (`hand fitness 641.54`, `tiny GA best 167.38 -> 167.38`). Notebook
lambda arities verified against sealed signatures (`onoff_step`, `pid_step`,
`generate_weather_profile`); artifact `results/ga_optimized_params.json` exists. No
critical (bug/data-loss/security) defects: JSON-only I/O, no eval/pickle/network/secrets,
energy definition includes vent per lock, zero-gain == decoupled proven by test. The
warnings below are real but non-shipping-blockers for a simulation study; the info items
are robustness/maintainability fixes worth taking before Phase 5/7 reuse these modules.

## Findings

### WR-01 — Init jitter pins all six ZO centers at exactly 0.0
- **Severity:** warning
- **File:** src/genetic_algorithm.py:239
- **Description:** `pop[i, :60] = hand[:60] * (1.0 + rng.uniform(-0.2, 0.2, 60))` is
  multiplicative, and every MF group in `FUZZY_MFS` has a ZO center of exactly `0.0`
  (eT, deT, du, eH, deH, dv). `0.0 * anything == 0.0`, so 6 of 60 MF genes have zero
  initial-population diversity — the entire population (minus individual 0) shares
  identical ZO centers and must wait for gaussian mutation to move them. The code proves
  it knows this failure mode: lines 240-243 draw coupling gains from `U(lo, hi)` with
  the comment "hand-scaled jitter would pin every gain at exactly 0.0" — the identical
  fix was not applied to the zero centers.
- **Suggestion:** Use additive jitter or uniform-within-bounds for near-zero genes, e.g.
  ```python
  scale = np.where(np.abs(hand[:60]) < 1e-12, 1.0, hand[:60])
  pop[i, :60] = hand[:60] + scale * rng.uniform(-0.2, 0.2, 60)
  ```
  then rely on `decode()` repair to clip into bounds.

### WR-02 — SystemExit-as-assertion aborts the standalone runner instead of recording FAIL
- **Severity:** warning
- **File:** tests/test_genetic_algorithm.py:62-67
- **Description:** `test_decode_repair_invariants` raises `SystemExit(f"len-{bad} chromosome
  did not raise")` when `decode` fails to reject a bad length. But the `__main__` runner
  (line 253) catches only `except Exception`, and `SystemExit` inherits from
  `BaseException`, so a triggered failure kills the whole runner mid-suite — remaining
  tests never run and no per-test FAIL line is recorded. An assertion mechanism that
  destroys the test report is a test-reliability defect (in scope).
- **Suggestion:** Replace with a plain assertion:
  ```python
  for bad in (59, 61, 63):
      try:
          decode(np.zeros(bad))
      except AssertionError:
          pass
      else:
          raise AssertionError(f"len-{bad} chromosome did not raise")
  ```

### WR-03 — Wall-clock timing assertion makes the suite flaky on loaded machines
- **Severity:** warning
- **File:** tests/test_genetic_algorithm.py:228-231
- **Description:** `test_tiny_ga_monotonic` asserts `dt < 30.0` on 8 full 1440-step
  closed-loop evaluations. Measured 7.9 s on this machine (~4x margin), but wall-clock
  bounds fail spuriously under CI load, antivirus scans, or slower hardware — a classic
  flaky-test pattern. A red suite caused by machine load erodes trust in the real
  monotonicity assertion on line 235.
- **Suggestion:** Drop the timing assert (monotonicity is the property under test) or
  relax to a generous smoke bound with a comment, e.g. `assert dt < 300.0  # hang guard only`.

### IN-01 — Mutation rate denominator stale at 1/60 for a 62-gene chromosome
- **Severity:** info
- **File:** src/genetic_algorithm.py:221
- **Description:** `gaussian_mutate(child, rng, p_gene=1.0 / 60.0, ...)` keeps the
  pre-coupling denominator: expected mutations per chromosome are 62/60 ≈ 1.033 instead
  of 1.0. Behaviorally negligible, but the literal contradicts the 62-D layout two
  screens up and will confuse the next reader.
- **Suggestion:** `def gaussian_mutate(child, rng, p_gene=1.0 / CHROM_LEN, sigmas=SIGMAS):`
  (name is module-level by then — defined line 61, function defined line 221, fine).

### IN-02 — train_seed/holdout_seed are provenance labels, not functional parameters
- **Severity:** info
- **File:** src/genetic_algorithm.py:271-279
- **Description:** `run_ga(..., train_seed=7, holdout_seed=21, ...)` accepts both seeds
  but never uses them: weather comes solely from the `train_weather` CSV file
  (line 276) and evolution is driven solely by `rng_seed`. A caller passing
  `train_seed=42` gets byte-identical evolution while the JSON records `train_seed: 42`
  as if it parameterized the run — misleading provenance.
- **Suggestion:** Document in the docstring that both seeds are recorded-not-used
  (weather generation is external; cf. notebook cell that generates at seed 7/21), or
  generate the CSV from `train_seed` when the file is missing, mirroring the notebook.

### IN-03 — Over-strict JSON type gating plus non-assert failure modes in schema validation
- **Severity:** info
- **File:** src/ga_fuzzy_controller.py:48-63
- **Description:** (a) Line 53 requires `isinstance(x, float)` for every center/width,
  so a semantically identical hand-authored artifact using JSON ints (e.g.
  `"centers": [-4, -2, 0, 2, 4]`) is rejected — `json.load` yields `int` for `0`.
  Same for coupling gains on line 60. (b) The "fail-fast" contract claims asserts, but
  a missing top-level `"mfs"` key raises bare `KeyError` (line 48) and
  `"coupling": null` raises `AttributeError` on `.get` (line 59), not the documented
  `AssertionError` — inconsistent error surface for malformed artifacts.
- **Suggestion:** Accept ints via `isinstance(x, (int, float)) and not isinstance(x, bool)`,
  and normalize before field access, e.g.
  ```python
  assert isinstance(d.get("mfs"), dict) and isinstance(d.get("coupling", {}), dict)
  ```

### IN-04 — Loader cache has no invalidation and returns shared-mutable globals
- **Severity:** info
- **File:** src/ga_fuzzy_controller.py:42-45
- **Description:** `load_optimized_mfs` caches on abspath only. Re-running the GA
  (which rewrites the JSON every generation) in a long-lived process — e.g. the
  Phase 7 dashboard — silently keeps serving stale params with no reload path.
  It also returns the cached `_MFS`/`_GAINS` objects themselves, so any caller-side
  mutation corrupts all subsequent calls.
- **Suggestion:** Guard on mtime (`os.path.getmtime`) alongside the path, and/or return
  defensive copies; document that the cache is per-path with no TTL.

### IN-05 — Unclosed file handles in test and notebook JSON loads
- **Severity:** info
- **File:** tests/test_genetic_algorithm.py:190; notebooks/04_ga_optimization.ipynb:66
- **Description:** `json.load(open(tmp))` (test) and `json.load(open(JSON))` (notebook
  train-weather cell) never close the handle — missing-`with` pattern. CPython
  refcounting usually hides it, but it emits `ResourceWarning`s elsewhere and on
  Windows a lingering handle can lock the temp file.
- **Suggestion:** `with open(tmp) as f: d = json.load(f)` in both spots
  (`src/genetic_algorithm.py:_write_json` already uses `with` — follow that convention).

### IN-06 — Mutable default arg binds the FUZZY_MFS global at def time
- **Severity:** info
- **File:** src/genetic_algorithm.py:154-155
- **Description:** `def coupled_fuzzy_step(..., mfs=FUZZY_MFS, gains=None)` binds the
  module-global dict as a default. Nothing today mutates it (`decode` allocates fresh
  dicts; `fuzzy_step` treats mfs read-only; `test_hand_mfs_untouched` guards this), so
  this is latent — but a future in-place tweak through the default would silently
  corrupt the global hand baseline the whole study compares against. (Mirrors the sealed
  `fuzzy_step` convention, so keep the signature; just note the hazard.)
- **Suggestion:** Add one line to the docstring: "mfs default is the FUZZY_MFS global —
  never mutate it in place; decode() fresh copies instead." Optionally use the
  `state=None` sentinel pattern already used two parameters over.

### IN-07 — Notebook duplicates cost weights as literals and guards no artifact provenance
- **Severity:** info
- **File:** notebooks/04_ga_optimization.ipynb:114; notebooks/04_ga_optimization.ipynb:66-70
- **Description:** (a) The holdout cost is recomputed as `iae_T + iae_H + 0.01 * E`
  instead of importing `W1, W2, W3` from `src.genetic_algorithm` — if the locked
  weights ever change, fitness and proof silently diverge. (b) The notebook prints
  `schema_version` and history length but never asserts them; a stale smoke-test
  artifact (e.g. a 1-gen `run_ga` debug JSON left at `results/`) would run the full
  holdout proof on garbage and fail at the verdict assert with a confusing message.
- **Suggestion:** `from src.genetic_algorithm import W1, W2, W3` and
  `costs[name] = W1*iae_T + W2*iae_H + W3*E`; add
  `assert d["schema_version"] == 2 and d["population"] == 50 and d["generations"] == 50`
  right after load.

### IN-08 — run_ga input-validation gaps, dead sys.path insert, NaN-history edge
- **Severity:** info
- **File:** src/genetic_algorithm.py:237; src/genetic_algorithm.py:291; src/genetic_algorithm.py:340
- **Description:** (a) `run_ga(population=0)` crashes with bare `IndexError` at
  `pop[0] = hand` (line 237) — no guard that population >= 1; reachable from the CLI
  via `--population 0`. (b) The `sys.path.insert` in the `__main__` block (line 340)
  executes after all imports already resolved at module top — dead code. (c)
  `hist_mean` uses `np.mean(fit[np.isfinite(fit)])` (line 291): an all-inf population
  yields `nan` with a RuntimeWarning, and `json.dump` then emits a non-standard `NaN`
  token. Practically unreachable today (individual 0 + elitism keep a finite best), but
  a latent invalid-JSON path.
- **Suggestion:** `assert population >= 1 and generations >= 0` at `run_ga` entry;
  delete line 340 (the try/except import at lines 25-34 already handles both layouts);
  guard the mean with `np.mean(...) if np.any(np.isfinite(fit)) else float("inf")`.

## Verification

- [x] Ran `python tests/test_genetic_algorithm.py` from repo root — 9/9 PASS, "all checks passed"
- [x] Traced encode/decode/repair round-trip (incl. len-60 legacy path, bad-length rejection) — matches plan
- [x] Traced fitness weights (1.0/1.0/0.01), duty-hours energy incl. vent, inf boundary — matches plan
- [x] Traced operators (tournament-3, BLX-0.5, per-gene gaussian, elitism-2 w/ fitness carryover) — shapes correct
- [x] Traced RNG discipline (single `default_rng` owns all draws) and hand-as-individual-0 — matches plan
- [x] Traced coupling application (post-loop heater/vent boost, zero-gain identity) shared by fitness loop and wrapper — matches D-06/A2
- [x] Traced JSON schema v2 keys incl. `coupling`, weights, seeds, history length == generations — matches plan
- [x] Read notebook JSON cell-by-cell (no execution — jupyter CLI absent); verified sealed-call arities and holdout isolation (fresh seed-21 temp path)
- [x] Security scan: no eval/exec/pickle, no secrets, no network, file writes confined to caller-chosen `out_path` — no findings
- [ ] Did NOT re-run 50x50 evolution (~35 min wall) — per instruction, spot-checked mechanics only

## Sign-Off

Reviewed: 2026-09-27 (standard depth, 4 files). Status: **findings** — 0 critical, 3 warnings, 8 info (11 total).
No source files modified, nothing committed. The GA core is sound and the 9/9 suite passes;
WR-01 is the one finding worth fixing before treating GA results as fully explored, WR-02/WR-03
protect the suite itself, and the IN items are cheap hardening before Phase 5/7 reuse.

_Reviewed: 2026-09-27_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
