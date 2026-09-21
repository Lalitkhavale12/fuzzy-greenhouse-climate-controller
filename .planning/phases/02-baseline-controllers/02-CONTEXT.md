# Phase 2: Baseline Controllers - Context

**Gathered:** 2026-09-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Delivers the two classical baselines the fuzzy/GA controller must beat: `onoff_controller.py` (hysteresis on/off per loop) and `pid_controller.py` (dual-loop continuous PID), both closing the loop on the Phase-1 plant (`step(dt, actuators, weather)` -> T/w/RH) and tracking fixed 25 C / 70 %RH setpoints. Proven tracking via a closed-loop proof notebook. Controllers take current state plus setpoint and return actuator commands in the duty structure later controllers share (BASE-03).

Requirements: BASE-01, BASE-02, BASE-03.

</domain>

<decisions>
## Implementation Decisions

### Control Structure
- **D-01:** Control is split into a temperature loop and a humidity loop. The T-loop drives heater + fan_cooler + vent; the RH-loop drives fogger only. The vent follows temperature (the stronger coupling). — **Reversibility:** costly — the actuator mapping shapes every closed-loop trace the GA fitness and comparison phases build on.
- **D-02:** The on/off controller uses a hysteresis band (on at wider error, off at narrower error), not a plain threshold — avoids relay chatter in the proof traces.
- **D-03:** Loops stay independent: no feedforward or cross-compensation (e.g. no heater bump to cancel fogger evaporative cooling). Plant physics (D-05 full coupling from Phase 1) sorts out the interaction — simplest, most honest baseline.

### Setpoints
- **D-04:** Closed-loop proof tracks fixed setpoints 25 C / 70 %RH (mid-band classic greenhouse target, inside the Phase-1 D-02 operating band). No scheduling (PROJECT.md out-of-scope). Setpoints pass as function arguments per BASE-03, not baked in.

### PID Scope
- **D-05:** Dual-loop PID mirroring the on/off split: T-PID drives heater/fan/vent, RH-PID drives fogger — so the two baselines are directly comparable. No T-only hybrid. — **Reversibility:** costly — same trace-dependency rationale as D-01.

### Proof Shape
- **D-06:** Proof is `notebooks/02_baselines.ipynb` + PNG, same pattern as Phase 1 (Agg headless, imports from `src/`, no duplicated logic). Feeds the Phase-6 notebook trail.

### the agent's Discretion
- Exact hysteresis band widths, PID gains (hand-tuned per PROJECT.md — no auto-tuning), anti-windup handling, and output clamping — planner/researcher picks values that track without saturation.
- PID output mapping to [0, 1] duties and internal state handling (caller-owned vs closure) within the BASE-03 signature.
- Proof-notebook cell layout and plot arrangement within the D-06 pattern.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Spec
- `.planning/PROJECT.md` — spec constraints for `onoff_controller.py`, `pid_controller.py`; out-of-scope list (PID tuning automation, setpoint scheduling); directory layout.
- `.planning/REQUIREMENTS.md` — BASE-01..03 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria (4 items), requirement mapping.

### Phase-1 Contract (the plant under control)
- `.planning/phases/01-greenhouse-model-weather/01-CONTEXT.md` — D-01..D-16: coupled physics, actuator effects, stateless `step()` API (D-15), both-units return (D-16).
- `src/greenhouse_model.py` — `step(dt, actuators, weather_at_t)`, `load_weather_profile`, `daytime_solar`, `params`; actuator keys `{heater, fan_cooler, fogger, vent}`, duties [0, 1].
- `weather/weather_profile.csv` — seed-7 outdoor disturbance (peak truly at 15:00 post CR-01 fix).

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/greenhouse_model.py`: `step`, `load_weather_profile`, `daytime_solar`, `params` — the closed-loop sim calls these per timestep; no new plant code needed.
- `weather/weather_profile.csv`: outdoor disturbance input for the proof run.
- `tests/test_greenhouse_model.py`: plain-assert suite convention (no pytest dependency) for the new controller checks.

### Established Patterns
- NumPy-only numerics; pure/stateless functions with caller-owned state; data as CSV under `weather/`; proof notebooks import from `src/` with Agg headless plots + committed PNG.
- Atomic per-task commits with `scope(phase-plan):` message convention.

### Integration Points
- Controller output must be the actuator-command dict `{heater, fan_cooler, fogger, vent}` in [0, 1] duties — the shared structure Phase 3 (fuzzy) and Phase 4 (GA fitness) will reuse.
- Phase 5 (metrics) will score these baselines on IAE + energy — keep the proof-run history loggable.

</code>

<specifics>
## Specific Ideas

- Baselines exist to be beaten: keep them honest but not weak — hysteresis + hand-tuned gains, no deliberate handicapping.
- Direct comparability between on/off and PID matters (same loop split) since the core value compares the GA fuzzy against both.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-Baseline Controllers*
*Context gathered: 2026-09-21*
