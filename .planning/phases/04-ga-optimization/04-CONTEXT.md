# Phase 4: GA Optimization - Context

**Gathered:** 2026-09-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Delivers the genetic algorithm that tunes the fuzzy membership functions so the GA-fuzzy controller beats both baselines: `genetic_algorithm.py` (real-valued chromosome, tournament selection, blend/single-point crossover, gaussian mutation, elitism, seeded RNG), fitness `1.0*IAE_T + 1.0*IAE_H + 0.01*energy` via full 24 h simulation, budget 50 individuals × 50 generations evolved on seed-7 weather; best chromosome saved to `results/ga_optimized_params.json`; `ga_fuzzy_controller.py` (same velocity-form inference engine, loads MF params from JSON) proven at lower weighted cost than both baselines in a holdout run on a fresh weather seed. Proof via convergence + comparison notebook.

Requirements: GA-01, GA-02, GA-03, GA-04, GA-05.

</domain>

<decisions>
## Implementation Decisions

### Fitness Weights
- **D-01:** Tracking-first fitness: `w1 = w2 = 1.0`, `w3 = 0.01` — temperature and humidity IAE dominate; energy is a tiebreaker. The GA chases the lowest tracking error first, thrift second.

### GA Budget
- **D-02:** Large budget: population 50 × 50 generations (~2500 full-sim fitness evals). Stronger optimum at longer runtime; still overnight-safe. Seeded RNG for reproducible reruns (D-12 determinism family).

### Holdout Proof (GA-05)
- **D-03:** Evolve on seed-7 weather, prove on a FRESH seed (e.g. seed-21): all four controllers (on/off, PID, hand fuzzy, GA fuzzy) run the holdout comparison on weather the GA never saw — the win must generalize, not memorize. — **Reversibility:** costly — the holdout seed anchors the core-value claim every later comparison references.

### Chromosome Scope
- **D-04:** Full MF set: every center + width in `FUZZY_MFS`, both loops (T and RH) — largest search space, most tuning power for the 50×50 budget. Rule table and engine stay fixed (textbook table, velocity form — GA tunes shapes only, not structure).
- **D-04a (amendment 2026-09-27, user-approved after blocked 50×50 run 1):** output-MF center bounds widened to the full [-1.0, 1.0] defuzz grid for `du` and `dv` only — the locked ±0.1 output universe capped fogger authority at 0.1/step, structurally unable to match bang-bang recovery on humidity-dominated fitness. Input universes (eT/deT/eH/deH), width bounds, rule table, and engine unchanged; hand chromosome remains a valid interior point and individual 0. — **Reversibility:** costly — same trace-dependency rationale as D-01; run-1 JSON is superseded, not comparable.

### Proof Shape
- **D-05:** Proof is `notebooks/04_ga_optimization.ipynb` + PNG, same pattern as Phases 1–3 (Agg headless, imports from `src/` only, no duplicated logic): convergence curve + holdout comparison traces (+ MF before/after plots, recommended). Feeds the Phase-6 notebook trail.

### the agent's Discretion
- Selection flavor (tournament vs roulette), crossover flavor (single-point vs blend), mutation sigma schedule (fixed per PROJECT.md — no adaptive rates), elitism count (1–2 per spec), exact fresh holdout seed value.
- Chromosome encode/decode mapping details within the full-MF-set scope; fitness evaluation harness shape (reuse `_run_closed_loop` family).
- Proof-notebook cell layout and plot arrangement within the D-05 pattern.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Spec
- `.planning/PROJECT.md` — spec constraints for `genetic_algorithm.py` (chromosome, fitness, operators, elitism, JSON output), `ga_fuzzy_controller.py` (same engine, loads JSON); out-of-scope list (dynamic/adaptive GA — fixed operators suffice).
- `.planning/REQUIREMENTS.md` — GA-01..05 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria (5 items), requirement mapping.

### Prior-Phase Contracts
- `.planning/phases/03-manual-fuzzy-controller/03-CONTEXT.md` — D-01..D-04: dual-loop split, textbook table, stable-tracking bar, notebook pattern; FUZZY_MFS is GA chromosome material, hand values are the starting point.
- `src/fuzzy_controller.py` — velocity-form engine (`fuzzy_step`, `infer`, `tri`), `FUZZY_MFS` named dict (centers/widths per eT/deT/du/eH/deH/dv), MacVicar-Whelan RULES; read-only convention (never mutate in place — GA passes copies).
- `src/greenhouse_model.py` — `step(dt, actuators, weather_at_t)`; actuator keys, duties [0, 1].
- `src/onoff_controller.py`, `src/pid_controller.py` — baselines to beat (reference: on/off T-IAE 7.38, PID T-IAE 1.08, hand fuzzy T-IAE 2.68).
- `weather/weather_profile.csv` — seed-7 evolution weather; generator is seedable for the fresh holdout seed.
- `src/weather_profile_generator.py` — `generate_weather_profile(out_path, seed=...)` for holdout weather generation.

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/fuzzy_controller.py`: the engine GA tunes — `infer()` must accept an MF-dict argument (it does: `mfs` param) so fitness evals can inject chromosome-decoded dicts without touching the module global.
- `src/greenhouse_model.py`: `step`, `load_weather_profile`, `daytime_solar`, `params` — fitness eval harness (1440 × dt=60 s per eval).
- `tests/test_fuzzy_controller.py`: `_run_closed_loop`-style harness pattern reusable for fitness evaluation; plain-assert convention.
- `src/weather_profile_generator.py`: seedable generator — fresh holdout weather is one call away.
- `tests/test_baseline_controllers.py`: baseline runners for the holdout comparison.

### Established Patterns
- NumPy-only numerics; pure functions with caller-owned state; named parameter dicts (GAINS → FUZZY_MFS → chromosome); fail-fast asserts; seeded determinism (D-12); proof notebooks import from `src/` with committed PNGs; atomic per-task `scope(phase-plan):` commits.

### Integration Points
- `results/ga_optimized_params.json` is the handoff artifact Phase 5 (metrics) and Phase 7 (dashboard GA explorer) consume — schema stability matters.
- `ga_fuzzy_controller.py` must expose the same `(state, setpoint) -> (duties, state)` signature as every other controller so Phase 5 scores it identically.
- Fitness history (best-per-generation) should be loggable — the convergence plot and Phase-6 trail need it.

</code>

<specifics>
## Specific Ideas

- The core value is decided here: the holdout comparison on fresh weather is the single most important plot in the project — it must show GA fuzzy below both baselines on the weighted cost.
- 50×50 was chosen over 20×30 for optimum quality; runtime is accepted (each eval is a full 24 h sim — researcher should measure per-eval cost and confirm overnight-safety).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-GA Optimization*
*Context gathered: 2026-09-22*
