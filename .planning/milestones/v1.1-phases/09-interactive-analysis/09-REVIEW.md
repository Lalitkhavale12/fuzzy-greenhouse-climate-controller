---
phase: "09"
status: findings
depth: standard
files_reviewed: 4
summary: |
  Reviewed the four Phase 09 files at standard depth and cross-checked every
  new helper against its src/ contract (infer, all_metrics, run_closed_loop
  actuator dicts, FUZZY_MFS). No critical defects and no security surface:
  no user-controlled paths or weights reach the sim, no eval/exec, frozen
  JSON is schema-gated. Found 3 warnings (single-pass neighbor clamp breaks
  ordering on strongly-violated headless input; Reset-to-frozen button is a
  one-render flash because reassignment cannot move Streamlit widget state;
  tight wall-clock budgets in test_scenario_delta are a flake risk) and
  4 info items (assert-as-validation, unused g_mean, magic 50, page-inline
  pair logic duplicating run_scenario_pair). Verification: 15/15 PASS.
critical: 0
warning: 3
info: 4
total: 7
---

# Code Review — Phase 09 (interactive-analysis)

## Summary

Reviewed the Phase 09 scope (new defs in `dashboard/helpers.py`; widget
wiring in `02_controllers.py` / `03_ga_explorer.py`; 4 new tests in
`tests/test_dashboard.py`) at standard depth, tracing each new call into
its `src/` contract. All contracts line up: `tloop_response_curve` passes
`(EC, EW, DC, DW, OC, OW, -1.0, 1.0)` exactly per `infer()`'s signature;
`scenario_delta` keys (`DISPLAY.values()`) match `run_all_four`'s return
keys and its `all_metrics(T, RH, U, T_sp, RH_sp)` arity; `u["heater"]`
indexing in `build_scenario_figure` matches the actuator dicts
`run_closed_loop` appends; slider half-gaps are nonzero (verified distinct
hand centers), so UI-driven scratch input can never violate ordering. No
security findings: sim entry takes no user paths/weights, no eval/exec/
deserialization of untrusted data, frozen artifacts are schema-gated.
The 7 findings below are all robustness/test-reliability grade — nothing
blocks the locked decisions (free seeds, T-loop-only drags, scrub-only
replay, duty-unit readout, deepcopy scratch) which hold up as implemented.

## Findings

### WR-01 — Single forward clamp pass does not guarantee ordered centers

- **Severity:** warning
- **File:** dashboard/helpers.py:259-272
- **Description:** `scratch_mfs_from_deltas` clamps in one forward pass
  with the upper bound taken from the *raw requested* next value
  (`hi = vals[i + 1] - eps`, line 266), not from an already-clamped
  neighbor. For mildly-violated input (the only case tested) this lands
  ordered, but for strongly-violated headless input it returns descending
  centers despite the "neighbor-clamped" contract. Traced with
  `vals = [4, 2, 0, -2, -4]` against hand `[-4, -2, 0, 2, 4]`:
  `i=0` clamps to `1.999`, then `i=1` gets `lo=2.0 > hi=-0.001` and
  collapses to `-0.001`, cascading to a fully descending output
  `[1.999, -0.001, -2.001, -4.001, -4.0]`. Unreachable via the page
  (sliders are confined to ±half-gap so ordering cannot break through the
  UI), but reachable by any headless caller, and `test_scratch_clamp`
  only exercises a single adjacent inversion so the hole is untested.
- **Suggestion:** Clamp to a fixed point — e.g. a forward min-pass
  followed by a backward max-pass, or iterate until no element moves:
  ```python
  for _ in range(len(clamped)):
      changed = False
      for i in range(1, 5):  # forward: enforce c[i] > c[i-1] + eps
          lo = clamped[i - 1] + eps
          if clamped[i] < lo:
              clamped[i] = lo; changed = True
              warnings.append("%s[%d] clamped to %.4g (neighbor bound)" % (key, i, lo))
      for i in range(3, -1, -1):  # backward: enforce c[i] < c[i+1] - eps
          hi = clamped[i + 1] - eps
          if clamped[i] > hi:
              clamped[i] = hi; changed = True
              warnings.append("%s[%d] clamped to %.4g (neighbor bound)" % (key, i, hi))
      if not changed:
          break
  ```
  and extend `test_scratch_clamp` with a fully-reversed input asserting
  strict increase plus warnings.

### WR-02 — Reset-to-frozen button only flashes frozen curves for one render

- **Severity:** warning
- **File:** dashboard/pages/03_ga_explorer.py:64-67
- **Description:** `if reset: eT_vals = list(hand_eT); du_vals = list(hand_du)`
  rebinds the local Python variables but cannot move Streamlit widget
  state (sliders are keyed by label and retain their dragged values).
  On the click-render the sliders still display dragged positions while
  the scratch curves are computed from hand centers (inconsistent frame),
  and on the very next rerun `reset` is False so the dragged slider
  values flow back into the scratch — the reset silently un-resets
  itself. UI-only, no data corruption, and the stub-based import test
  never exercises it (`button` stubs to `None`), but the labeled behavior
  does not hold. The locked "no session_state" decision blocks the
  canonical fix (keyed sliders + session_state reset).
- **Suggestion:** Either unlock `session_state` for this page and reset
  via widget keys (`st.slider(..., key="eT_0")` +
  `st.session_state["eT_0"] = hand` on click), or — staying within the
  lock — remove/relabel the button (e.g. "Preview frozen this render")
  so the label matches the one-render behavior.

### WR-03 — Wall-clock budgets in test_scenario_delta are tight enough to flake

- **Severity:** warning
- **File:** tests/test_dashboard.py:198,205
- **Description:** `cold_dt < 6.0` for a 2-side × 4-controller × 1440-step
  cold run measured **4.48s** on this machine — only ~1.3× headroom, and
  the suite's own precedent (`test_controllers_helper`) budgets 30s for a
  *single* side (measured 2.45s there). A slower or loaded CI box can
  push the cold pair past 6.0s with zero code change. `warm_dt < 0.5`
  (measured 0.103s) has more margin but the same structural risk.
- **Suggestion:** Relax to budgets with ≥3× observed headroom, e.g.
  `assert cold_dt < 15.0` / `assert warm_dt < 2.0`, keeping the printed
  timings for regression visibility; or degrade the asserts to
  report-only (`print`, no fail) on non-interactive CI.

### IN-01 — assert used for input validation in scratch builder

- **Severity:** info
- **File:** dashboard/helpers.py:257
- **Description:** `assert len(vals) == 5, (key, len(vals))` is stripped
  under `python -O` (leaving a downstream `IndexError` instead of the
  clear failure) and raises `AssertionError` rather than a catchable
  input error, slightly at odds with the warnings-not-crashes posture.
  Unreachable via the page (sliders always yield len-5).
- **Suggestion:** `if len(vals) != 5: raise ValueError("...")`.

### IN-02 — g_mean unpacked but never displayed

- **Severity:** info
- **File:** dashboard/pages/03_ga_explorer.py:108-109
- **Description:** `g, g_best, g_mean = replay_slice(gen, best, mean)` then
  the readout metric shows only `best`; `g_mean` is dead on arrival.
- **Suggestion:** Show both (`"gen %d/50 · best %.2f · mean %.2f"`) or
  unpack as `g, g_best, _g_mean` to mark intent.

### IN-03 — Frozen generation count 50 is a magic literal in three places

- **Severity:** info
- **File:** dashboard/helpers.py:309
- **Description:** `50` is hardcoded in `replay_slice` (`min(50, gen)`),
  `build_replay_figure`, the page slider (`st.slider(..., 1, 50, 50, 1)`)
  and the `/50` readout/title formats. A future artifact with a
  different generation count requires synchronized edits across
  helpers + page + tests.
- **Suggestion:** Define `GEN_COUNT = 50` in `dashboard/helpers.py` and
  import it on the page (`from dashboard.helpers import GEN_COUNT`);
  derive the readout denominator from it.

### IN-04 — Controllers page re-implements the pair logic inline

- **Severity:** info
- **File:** dashboard/pages/02_controllers.py:72-74
- **Description:** The page calls `run_all_four` twice plus
  `scenario_delta` inline, duplicating the pair orchestration that
  `run_scenario_pair` encapsulates for headless use — two call sites
  for "run pair + delta" that can drift (e.g. one side gains a new
  metric pass and the other does not). Noted the mismatch is structural:
  `run_scenario_pair` drops `hours`, which the page needs for the
  figure, so it cannot be reused as-is.
- **Suggestion:** Either have `run_scenario_pair` also return `hours`
  (`return hours_a, runs_a, runs_b, delta_rows`, updating the one test
  call) and use it on the page, or add a one-line comment at 72-74
  noting the inline pair is intentional (hours needed, cache keyed per
  side) so future edits keep both sites in sync.

## Verification

- [x] `python tests/test_dashboard.py` from repo root — **15/15 PASS**
  (11 existing + 4 new: `test_scenario_delta`,
  `test_scratch_purity`, `test_scratch_clamp`, `test_replay_slice`)
- [x] Cold pair 4.48s / warm 0.103s; scenario PNG magic + size ok;
  scratch zero-drag coincides, +0.5 drag dev 0.01441 duty; replay exact
  at gens 1/25/50 with clamps 0→1, 99→50
- [x] `results/` + `weather/` tracked artifacts untouched
  (`test_artifacts_untouched` PASS)
- [x] No source files modified; Streamlit server never launched
  (static review + headless suite only)

## Sign-Off

Phase 09 wiring is sound against its contracts and the locked decisions
hold as implemented. Recommended fix order before ship: WR-01 (clamp
fixed-point + reversed-input test), WR-02 (relabel or session_state
reset), WR-03 (relax timing budgets). IN items are opportunistic cleanup.

_Reviewed: 2026-09-29_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
