# Phase 5: Metrics & Comparison - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Delivers the quantified scoreboard across all four controllers: `src/metrics.py` (RMSE, IAE, ISE, settling time, overshoot, total energy from logged sim histories vs setpoint, plus the locked weighted cost + rank) and a machine-readable comparison table (`compare()` returns a columnar structure AND writes `results/comparison.csv`), scored on BOTH seed-7 train and seed-21 holdout weather with the holdout as the primary claim. Consumed by Phase-6 notebooks and the Phase-7 dashboard from the same artifact.

Requirements: METR-01, METR-02.

</domain>

<decisions>
## Implementation Decisions

### Comparison Weather
- **D-01:** Scoreboard runs on BOTH weathers: seed-21 holdout (fresh, unseen — the primary core-value claim) plus seed-7 train as reference. Full generalization story; train numbers are context, holdout numbers are the verdict. — **Reversibility:** costly — the published scoreboard anchors every later claim.

### Table Format
- **D-02:** `compare()` returns a columnar structure AND writes `results/comparison.csv` — notebooks and dashboard read the same artifact. Pandas-free: NO new dependency (PROJECT.md tech + zero-dep convention) — the "DataFrame" is a plain-Python columnar structure (dict of lists / list of dicts) plus `csv`-module file output.

### Settling Definition
- **D-03:** Settled = T stays within ±0.5 °C AND RH within ±3 %RH for the remainder of the run — matches the hysteresis bands, strict but consistent across all four controllers.

### Weighted-Cost Column
- **D-04:** Table carries all six METR-01 metrics PLUS weighted cost (locked 1.0/1.0/0.01 weights, duty-hours energy incl. vent — identical definition to `genetic_algorithm.py:173-174,186`) and a rank column — the core-value verdict readable in one row.

### Proof Shape
- **D-05:** No dedicated Phase-5 notebook (roadmap criteria are `metrics.py` + table only) — the table/CSV is proven by the suite asserting the locked holdout ordering (GA < on/off AND < PID); Phase 6 owns the comparison plots.

### the agent's Discretion
- Columnar structure exact shape (dict-of-lists vs list-of-dicts) within the D-02 constraint; CSV dialect/header details.
- Overshoot definition (peak beyond setpoint, % or absolute) and ISE/RMSE normalization within standard practice.
- Harness shape for running all four controllers on both weathers (reuse `_run_closed_loop` family); runtime budget for the 8 full runs.
- Settling edge semantics (never-settled marker value) within the D-03 band.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**
### Project & Spec
- `.planning/PROJECT.md` — spec constraints for `metrics.py` (RMSE, IAE, ISE, settling time, overshoot, total energy; final comparison table); tech (Python, NumPy — no pandas).
- `.planning/REQUIREMENTS.md` — METR-01/02 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria (3 items), requirement mapping.

### Prior-Phase Contracts
- `.planning/phases/04-ga-optimization/04-CONTEXT.md` — D-01 (weights 1.0/1.0/0.01), D-03 (seed-7 train / seed-21 holdout), D-06 (coupled-vs-decoupled framing for the table narrative).
- `src/genetic_algorithm.py:168-186` — LOCKED duty-hours energy definition (sum over steps of sum over ALL actuators incl. vent, /60) — Phase 5 must be identical.
- `results/ga_optimized_params.json` — schema v2 (mfs + coupling + fitness/weights/seeds/history); GA controller params source.
- `src/ga_fuzzy_controller.py` — `ga_fuzzy_step` + `load_optimized_mfs` (how the GA controller is invoked for scoring).
- `src/onoff_controller.py`, `src/pid_controller.py`, `src/fuzzy_controller.py` — the other three controllers; shared `(T_C, rh_pct, T_sp, RH_sp, state)` signature.
- `weather/weather_profile.csv` — seed-7 train weather; `src/weather_profile_generator.py` for fresh seed-21 generation.
- Reference holdout numbers (04-SUMMARY): GA 114.28 (T 1.66, H 112.44, E 18.13) < on/off 513.75 < PID 645.26.

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `closed_loop_breakdown(mfs, ...)` in `src/genetic_algorithm.py` — already returns (IAE_T, IAE_H, E); metrics.py generalizes this to the six-metric set for ANY controller.
- `_run_closed_loop` harness family (tests/test_fuzzy_controller.py, test_baseline_controllers.py) — the scoring-loop shape (1440 × dt=60, np.interp weather, 20.0/0.65*wsat init, setpoints-as-args).
- `tests/test_*` plain-assert convention with `__main__` runner + in-body imports; `csv` stdlib for file output (weather generator precedent: np.savetxt).

### Established Patterns
- NumPy-only numerics; pure functions; named constants; fail-fast asserts; seeded determinism; atomic per-task `scope(phase-plan):` commits; machine-readable artifacts with frozen schemas (JSON precedent).

### Integration Points
- `results/comparison.csv` (+ returned structure) is consumed by Phase-6 notebooks and the Phase-7 dashboard — column names are a contract; freeze them.
- Energy column MUST equal the GA fitness energy bit-for-bit on the same runs (same definition, same code path ideally — import or duplicate verbatim with a comment pointing at the lock).

</code>

<specifics>
## Specific Ideas

- The scoreboard is the project's receipts: one table where GA sits ranked #1 on holdout weighted cost with per-term breakdown — that table (or its descendant) ends up in the dashboard and final results.
- Pandas-free is a hard constraint surfaced during discussion (not in the roadmap text) — the planner must not introduce it.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 5-Metrics & Comparison*
*Context gathered: 2026-09-27*
