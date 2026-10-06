# Phase 9: Interactive Analysis - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Makes the dashboard interrogable: scenario A/B comparison on the Controllers page (two weather scenarios side-by-side with delta table), interactive MF explorer on the GA Explorer page (drag T-loop centers, watch response reshape vs frozen baseline), and generation-scrub convergence replay over frozen history. All computation reuses `src/` + cached primitives; frozen artifacts untouched; zero new installs.

Requirements: UI-04, UI-05, UI-06.

</domain>

<decisions>
## Implementation Decisions

### Scenario Picker
- **D-01:** Free seed sliders per side (1–50): seeds 7/21 resolve to the frozen CSVs, every other seed generates to an ephemeral tempfile (Controllers-page convention). Shared setpoint sliders across both sides so the comparison is apples-to-apples.

### MF Scope
- **D-02:** T-loop subset draggable: eT + du centers (10 sliders) where the action is — keeps the panel usable. deT/eH/deH/dv stay frozen. Widths frozen (centers only).

### Replay Form
- **D-03:** Slider scrub only over frozen `history.best`/`history.mean` (gen + best-fitness readout). No autoplay timers.

### Explorer Compare
- **D-04:** Scratch-vs-frozen overlay: dragged-MF response curve overlaid on the hand-baseline curve plus a Δ cost readout — shows exactly what each drag changes. Reset-to-frozen button restores hand MFs.

### Cross-Cutting Guards
- **D-05:** Scratch MFs live in deep copies only (never mutate `FUZZY_MFS`/`mfs_opt`); centers clamped between neighbors, widths untouched (frozen); validity warnings instead of crashes; evolution imports banned from exhibit pages (replay reads frozen history only).

### the agent's Discretion
- Response-curve definition for the explorer (defuzz surface sweep vs closed-loop probe) within the overlay+delta requirement.
- Delta-table columns beyond ΔIAE/Δenergy/Δcost; slider granularity within the seconds-scale rerun budget.
- Widget layout (columns/expanders) for the 10 MF sliders + reset button.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**
### Project & Spec
- `.planning/PROJECT.md` — v1.1 milestone (Dashboard Polish) goals and target features.
- `.planning/REQUIREMENTS.md` — UI-04/UI-05/UI-06 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 9 goal, success criteria (5 items), requirement mapping.
- `.planning/research/SUMMARY.md` + STACK/FEATURES/ARCHITECTURE/PITFALLS.md — v1.1 research (cached primitives, MF validity discipline, replay constraints).

### Prior-Phase Contracts
- `dashboard/helpers.py` — ALL new `def`s live here (byte builders precedent); pages stay thin wiring.
- `dashboard/pages/02_controllers.py` — cached `run_all_four` primitive + seed-slider/tempfile pattern to reuse per scenario side.
- `dashboard/pages/03_ga_explorer.py` — JSON load + MF overlay + convergence plot patterns; replay + explorer anchor page.
- `src/fuzzy_controller.py` — `tri`/`infer`/`FUZZY_MFS` (response-curve engine; read-only convention).
- `src/genetic_algorithm.py` — `run_closed_loop` shape reference (never call `run_ga` from UI code).
- `results/ga_optimized_params.json` — schema v2; frozen history + elite params.
- `tests/test_dashboard.py` — headless suite that must stay green (import smoke, source audits, artifacts-untouched guard).

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_all_four`-style cached closed-loop primitive (measure first, budget-gate per the research pitfall).
- `tri`/`infer` for response-surface recomputation over dragged centers (no duplicated inference math).
- Frozen `history.best`/`history.mean` arrays for the replay scrubber.
- `st.cache_data` + `session_state` patterns from existing pages.

### Established Patterns
- `dashboard/helpers.py` single shared module; pages thin wiring; `src/`/`results/`/`weather/` read-only; frozen-byte/CSV-rank provenance asserts; atomic per-task `scope(phase-plan):` commits.

### Integration Points
- Scenario runner reuses the Controllers-page cached primitive per side (fragment-isolated controls keep ticks seconds-scale).
- MF explorer writes scratch dicts only — the frozen baseline shown elsewhere never sees them.
- Replay slider indexes frozen history — no recomputation, no evolution imports.

</code>

<specifics>
## Specific Ideas

- The delta table's real question is "does GA still win?" — keep the rank framing from the scoreboard, not just raw deltas.
- The explorer's magic moment is dragging a center and watching the response curve bend in real time — latency matters more than extra features here.

</specifics>

<deferred>
## Deferred Ideas

- Autoplay animation for replay — deferred (scrub-only locked; revisit on feedback).
- All-groups MF dragging — deferred (T-loop subset locked; revisit on feedback).
- "Test scratch MFs on scenario A/B" bridge — P3 stretch, needs safety spike first.

</deferred>

---

*Phase: 9-Interactive Analysis*
*Context gathered: 2026-09-29*
