# Phase 4: GA Optimization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-22
**Phase:** 04-ga-optimization
**Areas discussed:** Fitness weights, GA budget, Holdout proof, Chromosome scope

---

## Fitness weights

| Option | Description | Selected |
|--------|-------------|----------|
| Tracking-first | w1=w2=1.0, w3=0.01 — energy is a tiebreaker | ✓ |
| Balanced | All three terms comparable after normalizing | |
| Energy-frugal | w3 high — gentle actuation over tracking | |

**User's choice:** Tracking-first (recommended).
**Notes:** No follow-up rationale offered; default accepted as presented.

---

## GA budget

| Option | Description | Selected |
|--------|-------------|----------|
| Modest 20x30 | ~600 evals, minutes of runtime, demo-grade convergence | |
| Large 50x50 | ~2500 evals, stronger optimum, overnight-safe | ✓ |

**User's choice:** Large 50x50 (against the recommendation — user opted for optimum quality over runtime).
**Notes:** User explicitly chose the larger budget.

---

## Holdout proof

| Option | Description | Selected |
|--------|-------------|----------|
| Fresh seed | Evolve seed-7, prove on fresh seed — win must generalize | ✓ |
| Same seed-7 | Evolve and prove on seed-7 — simplest, risk of weather-specific win | |

**User's choice:** Fresh seed (recommended).
**Notes:** No follow-up rationale offered; default accepted as presented.

---

## Chromosome scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full MF set | Every center+width, both loops — most tuning power | ✓ |
| Centers only | Widths frozen — smaller space, faster, less expressive | |
| T-loop only | RH loop keeps hand values — cheapest, humidity untuned | |

**User's choice:** Full MF set (recommended).
**Notes:** No follow-up rationale offered; default accepted as presented.

---

## the agent's Discretion

Selection/crossover flavors, mutation sigma, elitism count, exact holdout seed, encode/decode mapping, fitness harness shape, notebook layout — planner/researcher discretion within the locked decisions.

## Deferred Ideas

None — discussion stayed within phase scope.
