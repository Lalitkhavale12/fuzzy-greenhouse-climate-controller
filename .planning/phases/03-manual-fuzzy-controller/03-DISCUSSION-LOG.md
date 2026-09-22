# Phase 3: Manual Fuzzy Controller - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-21
**Phase:** 03-manual-fuzzy-controller
**Areas discussed:** Controller scope, Rule base, Success bar

---

## Controller scope

| Option | Description | Selected |
|--------|-------------|----------|
| Dual-loop full-dict | T-fuzzy drives heater/fan/vent, RH-fuzzy drives fogger; mirrors baselines, GA-ready | ✓ |
| T-only fuzzy | Fuzzy handles temperature only; humidity stays on Phase-2 logic | |

**User's choice:** Dual-loop full-dict (recommended).
**Notes:** No follow-up rationale offered; default accepted as presented.

---

## Rule base

| Option | Description | Selected |
|--------|-------------|----------|
| Textbook table | Classic diagonal 5x5 from the literature; explainable, sane GA starting chromosome | ✓ |
| Plant-custom rules | Rules shaped around this plant's quirks; potentially better now, less standard | |

**User's choice:** Textbook table (recommended).
**Notes:** No follow-up rationale offered; default accepted as presented.

---

## Success bar

| Option | Description | Selected |
|--------|-------------|----------|
| Stable tracking | 24h finite/bounded, no sustained oscillation; GA earns the comparison later | ✓ |
| Beat on/off | Hand-tuned fuzzy already beats on/off T-IAE 7.38 | |
| Match PID | Hand-tuned fuzzy matches PID T-IAE ~1.08; risks long tuning loops | |

**User's choice:** Stable tracking (recommended).
**Notes:** Phase-2 numbers (7.38 / 1.08) kept as reference only, not acceptance bars.

---

## the agent's Discretion

MF ranges/centers/widths, error-rate computation, output MF definitions and scaling, internal state handling, notebook cell layout — planner/researcher discretion within the locked decisions.

## Deferred Ideas

None — discussion stayed within phase scope.
