# Phase 7: Streamlit Dashboard - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Delivers the four-page thin UI wrapper over the finished `src/` library: `dashboard/app.py` (Model Sim, Controllers, GA Explorer, Results) with sliders/dropdowns driving the same `src/` functions and live-updating charts. No new control logic, no recomputation where a frozen artifact exists, no evolution inside the app. Streamlit 1.56.0 (installed, PROJECT.md tech).

Requirements: PROOF-02.

</domain>

<decisions>
## Implementation Decisions

### Page Set
- **D-01:** Exactly the spec four: Model Sim (plant + weather), Controllers (all four side-by-side), GA Explorer (convergence + MF before/after), Results (scoreboard + verdict). Multipage `dashboard/` app.

### GA Explorer Scope
- **D-02:** Artifact explorer ONLY: convergence curves + MF before/after + elite params from `results/ga_optimized_params.json` (schema v2). NO live evolution in-app (the 25-min run has no place in a UI; not even a tiny demo — the saved artifact is the exhibit).

### Controllers Page
- **D-03:** Side-by-side overlay: setpoint + weather-seed sliders, all four controllers on shared weather in one chart set — the comparison made interactive. Sliders re-run the closed loop live (seconds-scale per the notebook probes).

### Results Source
- **D-04:** Results page reads `results/comparison.csv` (frozen 14-col contract) — table + verdict, instant and always consistent with Phase 5. Never recomputes. — **Reversibility:** reversible — UI-only read path; the artifact stays canonical.

### the agent's Discretion
- Multipage layout mechanics (`dashboard/app.py` + `pages/`) vs single-file navigation within Streamlit conventions; widget choices (slider ranges/steps, dropdown vs radio) within the locked contents.
- Chart library path (matplotlib via st.pyplot reusing notebook-proven plotting vs Streamlit native charts) — reuse wins where a notebook plot already exists.
- Session-state/caching discipline (`st.cache_data` on weather loads + closed-loop runs) for live-update responsiveness.
- Weather-seed handling on the Controllers page (fresh-tempfile generation vs curated seed list) within repo-relative paths.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**
### Project & Spec
- `.planning/PROJECT.md` — dashboard spec (four pages, sliders/dropdowns into same `src/` functions, live charts, built last, thin wrapper).
- `.planning/REQUIREMENTS.md` — PROOF-02 definition and traceability.
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria (4 items), requirement mapping.

### Prior-Phase Contracts
- `src/greenhouse_model.py`, `src/onoff_controller.py`, `src/pid_controller.py`, `src/fuzzy_controller.py`, `src/ga_fuzzy_controller.py` — the wrapped functions; shared `(T_C, rh_pct, T_sp, RH_sp, state)` signature.
- `src/metrics.py` — COLUMNS contract; `compare()` harness the Controllers page mirrors (but does NOT call — page runs its own slider-driven loops).
- `results/comparison.csv` — frozen 14-col contract; Results page ONLY data source.
- `results/ga_optimized_params.json` — schema v2; GA Explorer ONLY data source.
- `notebooks/01-06` — proven plot flows to reuse (traces, bars, convergence, MF overlays, montage).
- `src/weather_profile_generator.py` — seedable weather for the Controllers-page seed slider.

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Every controller + `step()` + `load_weather_profile` + `daytime_solar`: directly callable from Streamlit callbacks (pure functions, no global state).
- Notebook plot cells (Agg) — convertible to `st.pyplot` figures by dropping the Agg backend line.
- `results/comparison.csv` + `csv`/`json` stdlib loading — Results/GA Explorer pages need no compute.
- `_run_closed_loop` harness shapes in tests — the Controllers-page loop pattern.

### Established Patterns
- NumPy-only numerics; pure functions with caller-owned state; frozen artifact contracts; repo-relative paths; atomic per-task `scope(phase-plan):` commits.

### Integration Points
- Dashboard reads (never writes) `results/` artifacts — the CSV/JSON stay canonical; guard against accidental overwrite.
- `weather/` holds only seed-7 + seed-21 CSVs — Controllers-page custom seeds generate to tempfiles (ephemeral, never committed).

</code>

<specifics>
## Specific Ideas

- Thin wrapper means thin: if a page starts growing logic that belongs in `src/`, that's a scope smell — push it down or cut it.
- The Results page is the project's front door for a reviewer: scoreboard + verdict above the fold.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 7-Streamlit Dashboard*
*Context gathered: 2026-09-28*
