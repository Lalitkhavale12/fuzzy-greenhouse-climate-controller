# Phase 6: Milestone Notebooks - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Completes the proof-of-work trail: creates `notebooks/05_comparison.ipynb` (scoreboard visual from `results/comparison.csv`) and `notebooks/06_final_results.ipynb` (end-to-end narrative), each with committed PNG, and audits the four existing notebooks (01, 02, 03, 04) for the uniform pattern — fixing only what the audit flags. All six notebooks call into `src/` with no duplicated logic. No new `src/` library code in this phase.

Requirements: PROOF-01.

</domain>

<decisions>
## Implementation Decisions

### Scope of Work
- **D-01:** Create 2 new notebooks (05, 06) + audit the existing 4 (01, 02, 03, 04) against the uniform pattern — fix only what the audit flags. Existing notebooks are otherwise sealed phase artifacts (their phases verified).

### 05 Content
- **D-02:** `05_comparison.ipynb` is the scoreboard made visual: loads `results/comparison.csv` (frozen 14-col contract — never recompute metrics inline), plots grouped bars per metric + cost ranking for both weathers, prints the holdout verdict (GA < on/off AND < PID). No live controller re-runs.

### 06 Content
- **D-03:** `06_final_results.ipynb` is the full end-to-end narrative: plant → all four controllers → holdout verdict → MF before/after → closing claim. Executive summary of the whole project; reads artifacts (CSV, JSON, PNGs) rather than recomputing where a canonical artifact exists.

### Consistency Bar
- **D-04:** Uniform pattern across all six: markdown title cell, Agg setup before pyplot, src-only imports, regen-if-absent weather guard, `savefig` committed PNG at dpi=120. The audit checks these mechanically (nb-ok structural checks); deviations in 01–04 get fixed. — **Reversibility:** reversible — notebook-only edits, no `src/` impact.

### the agent's Discretion
- Plot types/arrangements within the locked contents (bar groupings, trace selections, MF overlay style); markdown narrative wording.
- Audit mechanics (structural JSON checks vs headless cell execution) and fix granularity for flagged deviations.
- PNG filenames following the `NN_name.png` convention.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**
### Project & Spec
- `.planning/PROJECT.md` — six notebooks calling into `src/`, proof-of-work not separate logic.
- `.planning/REQUIREMENTS.md` — PROOF-01 definition and traceability.
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, requirement mapping.

### Prior-Phase Contracts
- `notebooks/01_greenhouse_model.ipynb`, `02_baselines.ipynb`, `03_fuzzy.ipynb`, `04_ga_optimization.ipynb` (+ PNGs) — the four existing trail notebooks; pattern source and audit subjects.
- `results/comparison.csv` — frozen 14-col contract; 05's ONLY data source.
- `results/ga_optimized_params.json` — schema v2; MF before/after source for 06 (hand FUZZY_MFS in `src/fuzzy_controller.py` is the before).
- `src/metrics.py` — COLUMNS contract; verdict definition (strict relative ordering).
- `.planning/phases/05-metrics-comparison/05-CONTEXT.md` — D-02 (pandas-free), D-04 (cost+rank), frozen column contract.

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- All four existing notebooks: cell pattern (markdown title → imports/Agg → weather guard → compute-or-load → plot → savefig) — 05/06 copy the shape.
- `results/comparison.csv` + `csv`/`json` stdlib loading — no recomputation in 05.
- Structural nb-ok/png-ok verify pattern (nbformat present, jupyter CLI absent): JSON cell inspection + PNG size check, plus headless cell execution via python-Agg where behavior matters.

### Established Patterns
- Agg headless before pyplot; src-only imports; regen-if-absent seed-7 weather; committed PNG at dpi=120; atomic per-task `scope(phase-plan):` commits.

### Integration Points
- 05 reads `results/comparison.csv` (frozen contract — column names must match COLUMNS exactly).
- 06 reads CSV + JSON + existing PNGs; its verdict restates (never recomputes) the locked holdout ordering.
- Phase 7 (dashboard) may embed these PNGs — keep filenames stable (`05_comparison.png`, `06_final_results.png`).

</code>

<specifics>
## Specific Ideas

- The trail should read front-to-back: 01 plant → 02 baselines → 03 fuzzy → 04 GA → 05 scoreboard → 06 verdict. 06 is the page you'd show a reviewer first.
- Uniform pattern is about the next reader (and Phase 7 embedding), not aesthetics for its own sake.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 6-Milestone Notebooks*
*Context gathered: 2026-09-28*
