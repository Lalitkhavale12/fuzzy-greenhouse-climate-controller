# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.1 — Dashboard Polish

**Shipped:** 2026-10-06
**Phases:** 3 | **Plans:** 6 | **Sessions:** n/a (single extended session)

### What Was Built
- Greenhouse theme + export center (CSV/TXT/PNG downloads, Phase 8)
- Interactive analysis: scenario A/B, MF drag explorer, convergence replay (Phase 9)
- KPI-first restyle + one-click 10-member evidence ZIP (Phase 10)
- 3D Plant House, overlay chart, sensitivity, robustness table, Pareto, adaptive fuzzy

### What Worked
- Goal-backward verification: verifiers re-proved SUMMARY claims against code + suite instead of trusting them
- Single `dashboard/helpers.py` as the only place for new logic — pages stayed thin, audits stayed mechanical
- Checkbox-gated heavy compute kept the headless suite fast while shipping 10-25 run analyses

### What Was Inefficient
- GSD tooling state (`state.json`, milestone-op) went stale mid-milestone and stayed blind to phases 8-10; closeout needed override backed by the audit
- `milestone.complete` ran twice created a duplicate MILESTONES.md entry (fixed manually)
- An edit typo (`__file` single underscore) and a use-before-def (`cached_robustness`) both escaped authoring — caught only by suite/lint

### Patterns Established
- Frozen artifacts read-only for UI code (BytesIO-only exports, no w-mode opens)
- CSV-arithmetic views (Pareto) over re-simulation where the frozen rows suffice
- Plain-assert standalone test runners; pytest collects them unchanged

### Key Lessons
1. Run the linter before the suite: ruff-F found a real browser-only crash the 80-test suite could not see (stub skips the branch).
2. Never trust tooling counts over directory truth: verify phases/requirements from files, then fix the state.
3. Gate expensive UI compute behind explicit user opt-in; headless imports execute the whole module.

### Cost Observations
- Model mix: n/a (single-session build)
- Sessions: 1 extended session
- Notable: batching related edits per file minimized re-reads; verification (suite ~2 min/run) dominated wall-clock

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.1 | 1 | 3 | Goal-backward verification + lint gate added to workflow |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.1 | 80 | n/a | 0 (plotly/matplotlib already pinned) |

### Top Lessons (Verified Across Milestones)

1. Frozen, read-only artifacts + headless byte-identity tests make UI claims cheap to verify.
