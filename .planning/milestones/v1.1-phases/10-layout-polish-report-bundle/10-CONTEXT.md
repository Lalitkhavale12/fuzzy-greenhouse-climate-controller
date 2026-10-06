# Phase 10: Layout Polish + Report Bundle - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Final v1.1 deliverable: presentation-grade restyle across all four dashboard pages (uniform KPI cards, targeted tabs, provenance expanders, clean narrow stacking) plus a one-click ZIP bundle (scoreboard CSV + verdict TXT + notebook PNGs + GA JSON). No new analysis, no control-logic changes, zero new installs.

Requirements: UI-03, UI-07.

</domain>

<decisions>
## Implementation Decisions

### KPI Content
- **D-01:** Uniform KPI cards on every page header: cost + rank + IAE_T/IAE_H — the verdict visible everywhere, same cards everywhere.

### Tab Structure
- **D-02:** Targeted tabs only: Controllers gets T/RH/energy tabs; Results gets train/holdout tabs. Other pages keep their single flow.

### ZIP Contents
- **D-03:** Full evidence pack: scoreboard CSV + verdict TXT + all committed notebook PNGs (01–06) + GA JSON. Built in-memory via stdlib `zipfile` (never temp files).

### Mobile Bar
- **D-04:** Clean stacking: columns stack vertically, no horizontal scroll, controls stay reachable. Verified by column structure + narrow-viewport reasoning (no browser screenshots possible headless).

### the agent's Discretion
- Expander contents (provenance details) per page; card styling within the greenhouse theme; ZIP filename.
- Tab labels and ordering within the locked structure.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**
### Project & Spec
- `.planning/PROJECT.md` — v1.1 milestone (Dashboard Polish) goals and target features.
- `.planning/REQUIREMENTS.md` — UI-03/UI-07 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 10 goal, success criteria (3 items), requirement mapping.
- `.planning/research/SUMMARY.md` + STACK/FEATURES/ARCHITECTURE/PITFALLS.md — v1.1 research (helpers pattern, ZIP-via-zipfile, restyle-last rationale).

### Prior-Phase Contracts
- `dashboard/helpers.py` — ALL new `def`s live here (ZIP builder joins the byte builders); pages stay thin wiring.
- `dashboard/app.py` + `dashboard/pages/01-04` — the four pages to restyle (cards/tabs/expanders) + ZIP button home (Results page).
- `results/comparison.csv` — frozen contract; ZIP reads it byte-for-byte.
- `results/ga_optimized_params.json` — schema v2; ZIP member.
- `notebooks/*.png` (01–06 committed) — ZIP members.
- `tests/test_dashboard.py` — headless suite that must stay green (extended with layout/ZIP asserts).

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `st.metric` + `st.columns` + `st.tabs` + `st.expander` (installed 1.56.0 — verify via hasattr probe like Phase-8 research did).
- `scoreboard_csv_bytes` / `verdict_text` / `fig_to_png_bytes` (Phase-8 byte builders — ZIP composes them, no new serialization).
- stdlib `zipfile` + `io.BytesIO` for the in-memory bundle.
- `test_dashboard.py` audit conventions (no savefig in pages, import smoke, artifacts-untouched guard).

### Established Patterns
- `dashboard/helpers.py` single shared module; pages thin wiring; `src/`/`results/`/`weather/` read-only; frozen-byte provenance asserts; atomic per-task `scope(phase-plan):` commits.

### Integration Points
- ZIP builder reads CSV + TXT (via verdict_text) + PNG bytes (committed files) + JSON — all frozen inputs, pure assembly.
- Restyle touches all four pages' layout code only — no compute, no helper-signature changes.

</code>

<specifics>
## Specific Ideas

- Restyle-once discipline: this is the last visual pass — get the cards/tabs/expanders right everywhere in one go, since no later phase revisits layout.
- The ZIP is the examiner handoff: it should contain everything needed to believe the claim without running anything.

</specifics>

<deferred>
## Deferred Ideas

- Dark-mode variant — still gated on feedback.
- PDF bundle — still deferred (ZIP decided instead).

</deferred>

---

*Phase: 10-Layout Polish + Report Bundle*
*Context gathered: 2026-09-29*
