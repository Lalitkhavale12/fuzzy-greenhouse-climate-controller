# Phase 8: Theme + Export Foundation - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Delivers the dashboard's greenhouse identity plus the export-center foundation later polish reuses: `.streamlit/config.toml` light-greenhouse theme, and `dashboard/helpers.py` byte builders (scoreboard CSV, verdict TXT, chart PNGs) wired as download buttons on every page. No control-logic changes, no frozen-artifact writes, zero new installs.

Requirements: UI-01, UI-02.

</domain>

<decisions>
## Implementation Decisions

### Theme Character
- **D-01:** Light greenhouse theme via `.streamlit/config.toml`: fresh greens + earth tones, light backgrounds, charts stay readable. No dark mode, no toggle (kept out — single-theme discipline).

### Export Formats
- **D-02:** CSV + PNG + TXT only: scoreboard CSV (frozen bytes), per-chart PNGs (BytesIO `savefig` + `seek(0)` + explicit MIME), verdict TXT. No PDF bundle (deferred to Phase 10's ZIP decision if at all).

### Export Placement
- **D-03:** Downloads live where the content lives: scoreboard CSV + verdict TXT on Results, chart PNG buttons on each chart's page (Model Sim, Controllers, GA Explorer, Results).

### Verdict Content
- **D-04:** Full breakdown TXT: winner + margins + per-term IAE_T/IAE_H/E breakdown for all four controllers + seeds/weights provenance (train 7, holdout 21, 1.0/1.0/0.01). Mirrors the notebook verdict cell, never recomputes beyond reading the CSV.

### the agent's Discretion
- Exact palette hex values within the greenhouse family; BytesIO helper shapes inside `dashboard/helpers.py`; button labels/placement within each page; PNG dpi for downloads.
- Chart-figure capture mechanics (rebuilding vs caching figure objects) within the no-recompute rule.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**
### Project & Spec
- `.planning/PROJECT.md` — v1.1 milestone (Dashboard Polish) goals and target features.
- `.planning/REQUIREMENTS.md` — UI-01/UI-02 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 8 goal, success criteria (4 items), requirement mapping.
- `.planning/research/SUMMARY.md` + STACK/FEATURES/ARCHITECTURE/PITFALLS.md — v1.1 research (zero-install constraint, helpers pattern, BytesIO plumbing, build order).

### Prior-Phase Contracts
- `dashboard/app.py` + `dashboard/pages/01-04` — the four pages to theme and instrument (thin wrappers; pages stay thin, logic goes in helpers).
- `results/comparison.csv` — frozen 14-col contract; export reads it byte-for-byte (never regenerates).
- `src/metrics.py` — COLUMNS contract; verdict definition (strict relative ordering).
- `tests/test_dashboard.py` — headless suite that must stay green (import smoke, source audits, artifacts-untouched guard).

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `st.download_button` + `BytesIO` pattern (research-verified on installed 1.56.0); matplotlib `savefig(buf)` for PNG bytes; stdlib `csv`/`json` reads.
- `tests/test_dashboard.py` audit conventions (no `savefig`/`plt.show`/absolute-paths in pages — downloads use BytesIO, not files).
- Notebook verdict cell (04) — the TXT content mirror.

### Established Patterns
- `dashboard/helpers.py` single shared module for ALL new `def`s (forced by headless test audits); pages stay thin wiring; `src/`/`results/`/`weather/` read-only; atomic per-task `scope(phase-plan):` commits.

### Integration Points
- `.streamlit/config.toml` is a zero-code sidecar — invisible to the test suite, screenshot-verified by human.
- Export helpers become the shared primitive Phase 9 (scenario CSVs) and Phase 10 (ZIP bundle) build on — byte-builder function shapes are the contract.

</code>

<specifics>
## Specific Ideas

- Theme first so every later screenshot (and the user's own eyeballing) sees the final identity from the start.
- The export center is plumbing, not UI glitter: correct bytes + MIME + filenames matter more than button styling.

</specifics>

<deferred>
## Deferred Ideas

- Dark-mode variant — gated on user feedback, not built speculatively.
- PDF bundle — deferred; Phase 10 decides ZIP-vs-PDF only if asked.

</deferred>

---

*Phase: 8-Theme + Export Foundation*
*Context gathered: 2026-09-29*
