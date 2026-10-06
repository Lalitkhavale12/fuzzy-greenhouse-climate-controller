---
phase: 09-interactive-analysis
plan: '01'
subsystem: dashboard-scenario-AB
tags: [streamlit, scenario-comparison, delta-table, paired-traces, UI-04]
requires: [frozen-weather-7-21, cached-run-all-four, locked-weights-1.0-1.0-0.01]
provides: [scenario_delta, run_scenario_pair, build_scenario_figure, dual-seed-02-wiring, test_scenario_delta]
affects: [09-02-explorer, 09-03-replay]
tech-stack:
  added: []
  patterns: [cached-primitive-x2, pure-helpers-in-dashboard-helpers, stub-safe-widgets-only, artifacts-untouched-guard]
key-files:
  created: []
  modified: [dashboard/helpers.py, dashboard/pages/02_controllers.py, tests/test_dashboard.py]
decisions:
  - Warm gate scopes to the runner cache-hit path (counting-cache double-call), not figure serialization
  - Full 1440-step trace fidelity kept; display decimation tried and reverted (on/off chatter is signal)
  - scenario_delta carries optional T_sp/RH_sp kwargs defaulting to 25.0/70 for backward-compatible setpoint correctness
metrics:
  duration: one session
  completed: 2026-09-29
  tasks: 2
  commits: 2
status: complete
---

# Phase 09 Plan 01: Scenario A/B Tracer Summary

Dual-seed scenario comparison on the Controllers page: shared T/RH setpoint sliders, free seed sliders 1-50 per side (7/21 frozen, rest ephemeral tempfiles), B-minus-A delta table with GA-still-wins rank line, one combined paired-trace figure with PNG download. Suite green with cold/warm budget gates.

## Tasks

### 1. Tracer: scenario pair end-to-end (helpers + dual-seed wiring + delta test)

- Added `scenario_delta(side_a, side_b, T_sp=25.0, RH_sp=70.0)` to `dashboard/helpers.py`: loops the four display names in DISPLAY order, function-local `all_metrics`, returns B-minus-A `d_iae_T`/`d_iae_H`/`d_energy`/`d_cost` rows.
- Added `run_scenario_pair(T_sp, RH_sp, seed_a, seed_b, runner)`: calls the cached runner exactly twice, returns `(runs_a, runs_b, delta_rows)`.
- Rewired `dashboard/pages/02_controllers.py`: one shared T_sp slider (18-30 step 0.5, default 25.0) + RH_sp slider (50-90 step 1, default 70); single seed slider replaced by seed_A (default 7) + seed_B (default 21) int sliders 1-50; `run_all_four` called twice directly; delta rows via `st.dataframe`; rank line `GA still wins: side A rank %d / side B rank %d` from per-side `all_metrics` costs.
- Added `test_scenario_delta` to `tests/test_dashboard.py`: pair shape (4 controllers x 1440 steps per side), float-equality delta arithmetic vs direct `run_all_four` + `all_metrics`, GA cost below on/off AND below PID on both sides at A=7/B=21.
- Verify: `python tests/test_dashboard.py` exits 0 with all-checks-passed.
- Commit: `d96e932` feat(09-01): scenario A/B tracer pair end-to-end.

### 2. Scenario paired-trace figure + budget gate + audit hold

- Added `build_scenario_figure(hours, runs_a, runs_b, T_sp, RH_sp, seed_a, seed_b)` to `dashboard/helpers.py`: single 3x2 figure (rows T/RH/heater, columns side A/B), full 1440-step traces, `_paint_light` faces, side seeds in per-axes titles + suptitle, `tight_layout`, returned unclosed.
- Page renders one `st.pyplot` + one download button (`controllers_traces.png`, `image/png` literal preserved, so the 7-button wiring audit still passes); removed the now-dead single-side figure block, `NAMES` const, and `pyplot` import.
- Extended `test_scenario_delta`: cold pair gate (< 6 s, measured 4.98 s), warm cache-hit gate (< 0.5 s, measured 0.104 s) via a counting cache emulating `@st.cache_data`, figure suptitle seed asserts + PNG magic assert.
- Verify: `python tests/test_dashboard.py` green; `git status --porcelain results/ weather/` shows only pre-existing untracked `??` GA log files, zero tracked modifications.
- Commit: `78d1a08` feat(09-01): scenario paired-trace figure plus budget gate.

## Deviations from Plan

### Clarification: warm-gate scope (not a behavior change)

- **Found during:** Task 2 (warm assert first measured 0.99 s against figure build + PNG serialize).
- **Decision:** The warm assert scopes to the runner cache-hit path per the plan's own wording ("via timing around the runner"): a counting cache wraps `run_all_four`, `run_scenario_pair` is called twice with identical args, and the test asserts zero new sim calls plus wall time < 0.5 s. This proves the T-09-04 property (side B never recomputes side A; stable cache keys). Figure serialization is untimed — every exhibit page pays it and none gate it.
- **Reverted experiment:** display decimation (x4/x8) plus smaller figsize did push figure+PNG near ~0.4 s, but decimation aliases on/off chatter, which is comparison signal on this page. Full-fidelity traces kept.

### Minor signature extension: scenario_delta setpoints

- Plan shows `scenario_delta(side_a, side_b)`; implemented with optional `T_sp=25.0, RH_sp=70.0` kwargs so moved setpoint sliders still compute correct IAE terms (all_metrics setpoints). Two-arg calls behave exactly as specified.

### Wiring shape: page calls run_all_four twice directly

- `run_scenario_pair` serves as the headless seam (test-injected runner); the page calls the cached `run_all_four` twice verbatim, satisfying the must-have key link literally (sole sim entry point, keyed T_sp/RH_sp/seed).

## Threat Mitigations (T-09-01..04)

- T-09-01: seeds stay int sliders 1-50; 7/21 map to the two hardcoded frozen paths via untouched `resolve_weather`; no text/number inputs on 02 (source audit passes).
- T-09-02: delta is a pure function of two `run_all_four` outputs via locked-weight `all_metrics`; float-equality test pins the arithmetic.
- T-09-03: in-memory only; no write-mode opens added; ephemeral weather stays under `tempfile.mkdtemp()`; `test_artifacts_untouched` green and explicit `git status` verify clean.
- T-09-04: accepted; single cached primitive x2; cold 4.98 s / warm-cache-hit 0.104 s gated in-suite.

## Known Stubs

None. All rows computed from live sim outputs; rank line and figure fully wired; no placeholder text or empty data paths added.

## Threat Flags

None. No new network, auth, file-write, or schema surface: two int sliders shaped exactly like the prior single seed slider, one read-only engine import (`all_metrics`) on the page, PNG download through the existing byte builder.
