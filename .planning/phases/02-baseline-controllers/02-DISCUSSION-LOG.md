# Phase 2: Baseline Controllers - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-21
**Phase:** 02-baseline-controllers
**Areas discussed:** Control structure, Setpoints, PID scope, Proof shape

---

## Control structure

| Option | Description | Selected |
|--------|-------------|----------|
| Vent follows T | T-loop drives heater + fan_cooler + vent; RH-loop drives fogger only | ✓ |
| Vent follows RH | RH-loop drives fogger + vent; T-loop drives heater + fan_cooler | |
| Arbitrated vent | Both loops compute vent demand; take max | |
| Plain threshold | Separate on/off thresholds per loop; may chatter | |
| Hysteresis band | On at wider error, off at narrower error | ✓ |
| Independent loops | Each loop watches its own error; physics sorts out interaction | ✓ |
| Heater compensates | Feedforward heater bump to cancel fogger evaporative cooling | |

**User's choice:** Vent follows T; hysteresis band; independent loops (all recommended options).
**Notes:** No follow-up rationale offered; defaults accepted as presented.

---

## Setpoints

| Option | Description | Selected |
|--------|-------------|----------|
| 25°C / 70%RH | Mid-band classic greenhouse target, inside D-02 band | ✓ |
| 22°C / 65%RH | Cooler/drier, easier tracking, less saturation | |

**User's choice:** 25°C / 70%RH (recommended).
**Notes:** BASE-03 already fixes setpoint-as-argument, so no interface question needed.

---

## PID scope

| Option | Description | Selected |
|--------|-------------|----------|
| Dual-loop PID | T-PID drives heater/fan/vent, RH-PID drives fogger — mirrors on/off split | ✓ |
| T-only PID | PID on temperature only; humidity stays on/off logic — hybrid baseline | |

**User's choice:** Dual-loop PID (recommended).
**Notes:** Direct comparability between baselines matters for the core-value comparison.

---

## Proof shape

| Option | Description | Selected |
|--------|-------------|----------|
| Notebook + PNG | 02_baselines.ipynb with closed-loop traces, Phase-1 pattern | ✓ |
| Script-only proof | Plain-assert verification, no notebook artifact | |

**User's choice:** Notebook + PNG (recommended).
**Notes:** Feeds the Phase-6 notebook trail.

---

## the agent's Discretion

Hysteresis widths, PID gains, anti-windup, output clamping, internal state handling, notebook cell layout — planner/researcher discretion within the locked decisions.

## Deferred Ideas

None — discussion stayed within phase scope.
