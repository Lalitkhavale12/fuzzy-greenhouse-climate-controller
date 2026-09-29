# Phase 5: Metrics & Comparison - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-27
**Phase:** 05-metrics-comparison
**Areas discussed:** Comparison weather, Table format, Settling definition, Weighted-cost column

---

## Comparison weather

| Option | Description | Selected |
|--------|-------------|----------|
| Both weathers | Seed-21 holdout primary + seed-7 train reference | ✓ |
| Holdout only | Only the claim weather | |

**User's choice:** Both weathers (recommended).

---

## Table format

| Option | Description | Selected |
|--------|-------------|----------|
| Both | Columnar return + results/comparison.csv | ✓ |
| DataFrame only | Return only | |
| CSV only | File only | |

**User's choice:** Both (recommended).
**Notes:** Pandas-free constraint surfaced by orchestrator (zero-dep convention) — recorded in CONTEXT.md specifics.

---

## Settling definition

| Option | Description | Selected |
|--------|-------------|----------|
| Tight band | ±0.5C / ±3%RH for the remainder — matches hysteresis bands | ✓ |
| Standard 2pct | Classical ±2% convention | |

**User's choice:** Tight band (recommended).

---

## Weighted-cost column

| Option | Description | Selected |
|--------|-------------|----------|
| Add cost + rank | Six metrics + locked weighted cost + rank | ✓ |
| Metrics only | Six metrics; cost stays in Phase 4 | |

**User's choice:** Add cost + rank (recommended).

---

## the agent's Discretion

Columnar shape, CSV dialect, overshoot definition, harness shape, settling edge semantics — planner/researcher discretion within the locked decisions.

## Deferred Ideas

None — discussion stayed within phase scope.
