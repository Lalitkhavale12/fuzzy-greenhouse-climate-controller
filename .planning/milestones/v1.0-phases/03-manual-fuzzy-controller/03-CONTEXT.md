# Phase 3: Manual Fuzzy Controller - Context

**Gathered:** 2026-09-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Delivers the hand-tuned Mamdani fuzzy controller that proves the inference engine works on the plant before any GA optimization: `fuzzy_controller.py` (dual-loop Mamdani FIS — temperature error + error-rate, humidity error + error-rate — 5 triangular MFs per variable NB..PB, textbook 5x5 rule tables, centroid defuzzification), closing the loop on the Phase-1 plant and tracking fixed 25 C / 70 %RH setpoints stably for 24 h. Emits the same 4-key duty dict the baselines share, so Phase 4's GA can tune its MF parameters in place. Proven via a closed-loop proof notebook.

Requirements: FUZZ-01, FUZZ-02, FUZZ-03, FUZZ-04, FUZZ-05, FUZZ-06.

</domain>

<decisions>
## Implementation Decisions

### Controller Scope
- **D-01:** Dual-loop fuzzy emitting the full 4-key duty dict `{heater, fan_cooler, fogger, vent}`: T-fuzzy drives heater/fan/vent (vent follows T), RH-fuzzy drives fogger — same split as the baselines, directly comparable, and GA-ready for Phase 4 (both loops' MF parameters become chromosome material). — **Reversibility:** costly — the loop split shapes every closed-loop trace the GA fitness and comparison phases build on.

### Rule Base
- **D-02:** Classic textbook diagonal 5x5 rule tables (error × error-rate, NB..PB) from the classical literature — explainable, and gives Phase 4's GA a sane starting chromosome. No plant-custom rule shaping.

### Success Bar (FUZZ-06)
- **D-03:** "Controls successfully" means stable tracking: 24 h closed-loop run on seed-7 weather stays finite and bounded around 25 C / 70 %RH with no sustained oscillation. Beating baselines is explicitly NOT required here — on/off T-IAE 7.38 and PID T-IAE 1.08 are reference numbers only; the GA earns the comparison in Phase 4.

### Proof Shape
- **D-04:** Proof is `notebooks/03_fuzzy.ipynb` + PNG, same pattern as Phases 1–2 (Agg headless, imports from `src/` only, no duplicated logic). Feeds the Phase-6 notebook trail.

### the agent's Discretion
- MF universe ranges and triangle center/width values (hand-tuned starting point the GA reshapes anyway), error-rate computation (finite difference over dt), output MF definitions and scaling to [0, 1] duties, internal state handling (caller-owned vs closure) within the setpoint-as-args signature.
- Proof-notebook cell layout and plot arrangement (MF plots recommended as GA baseline reference, not mandated).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Spec
- `.planning/PROJECT.md` — spec constraints for `fuzzy_controller.py` (Mamdani, inputs, 5 terms, ~25 rules, centroid, must work hand-tuned BEFORE GA); out-of-scope list (type-2/neuro-fuzzy, dynamic GA).
- `.planning/REQUIREMENTS.md` — FUZZ-01..06 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria (4 items), requirement mapping.

### Prior-Phase Contracts
- `.planning/phases/02-baseline-controllers/02-CONTEXT.md` — D-01..D-06: loop split, hysteresis, setpoints-as-args, notebook pattern; shared duty-dict contract.
- `.planning/phases/01-greenhouse-model-weather/01-CONTEXT.md` — D-01..D-16: coupled physics, stateless `step()` API (D-15), both-units return (D-16).
- `src/greenhouse_model.py` — `step(dt, actuators, weather_at_t)`, `load_weather_profile`, `daytime_solar`, `params`; actuator keys `{heater, fan_cooler, fogger, vent}`, duties [0, 1].
- `src/onoff_controller.py`, `src/pid_controller.py` — baseline loop-split reference (T owns vent; fogger-only RH loop); controller signature pattern `(T_C, rh_pct, T_sp, RH_sp, state)` returning `(duties, state)`.
- `weather/weather_profile.csv` — seed-7 outdoor disturbance (peak truly at 15:00 post CR-01 fix).

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/greenhouse_model.py`: `step`, `load_weather_profile`, `daytime_solar`, `params`, `relative_humidity`, `wsat_g_per_kg` (RH helpers per PROJECT.md compatibility note).
- `src/pid_controller.py`: `GAINS` dict pattern (named parameter dict — fuzzy MF params should follow the same named-dict shape so GA can encode them); caller-owned-state + `state=None` fresh convention; `np.clip` output discipline; finite-input asserts.
- `tests/test_baseline_controllers.py`: plain-assert suite convention, `_run_closed_loop` harness pattern reusable for the fuzzy proof test.
- `notebooks/02_baselines.ipynb`: proof-notebook cell pattern (Agg, regenerate-if-absent weather, closed-loop run, savefig PNG).

### Established Patterns
- NumPy-only numerics; pure functions with caller-owned state; named parameter dicts; fail-fast asserts (finite inputs, exact key sets); data as CSV under `weather/`; proof notebooks import from `src/` with committed PNGs; atomic per-task `scope(phase-plan):` commits.

### Integration Points
- Fuzzy output must be the exact 4-key dict `{heater, fan_cooler, fogger, vent}` in [0, 1] — the shared structure Phases 4 (GA fitness + chromosome) and 5 (metrics) consume.
- MF parameters must live in a named, GA-encodable structure (dict of centers/widths) — Phase 4 encodes them as the chromosome; hand values here are the starting point.
- Phase 5 scores this controller on IAE + energy — keep the proof-run history loggable.

</code>

<specifics>
## Specific Ideas

- The engine matters more than the tuning: textbook rules + reasonable hand triangles that track stably are the deliverable; GA does the winning.
- Membership-function plots in the proof notebook would give Phase 6 a before/after visual against GA-tuned MFs — suggested, not mandated.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 3-Manual Fuzzy Controller*
*Context gathered: 2026-09-21*
