# Phase 1: Greenhouse Model & Weather - Context

**Gathered:** 2026-09-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Delivers the simulated greenhouse plant: `greenhouse_model.py` (a coupled energy–mass ODE returning next temperature and humidity from a timestep plus four actuator inputs) and its driving disturbance source `weather_profile.csv` (a synthetic 24h outdoor profile). Proven physically sound via sanity tests and a plotting notebook. This is the plant every baseline and intelligent controller in later phases, plus the GA fitness loop, will run against — its dynamics and defaults are therefore a lock-in for the whole project.

Requirements: MODEL-01, MODEL-02, MODEL-03, MODEL-04.

</domain>

<decisions>
## Implementation Decisions

### Plant Physics Fidelity
- **D-01:** Model is a **coupled energy + moisture balance** — temperature and humidity interact (not decoupled per-state ODEs). Heating lowers RH, fogging/moisture raises it, temperature feeds the saturation/humidity-carrying term. — **Reversibility:** costly — reworking the state coupling would change the plant's qualitative behavior every controller was tuned against.
- **D-02:** Plant parameters (thermal mass, leak rate, evaporation rate, operating range) use **literature defaults** for a typical greenhouse, hard-coded as documented defaults (no crop-type prompt, no tuning). Target operating band in the 15–30 °C / 40–90 %RH family.
- **D-03:** Humidity state variable internally is **absolute humidity (g/kg)**; %RH is a derived/conversion quantity for output and plots (saturation pressure as a function of temperature).
- **D-04:** Phase 1 **includes sanity tests** for the ODE (bounded state, positivity, no NaN, plausible steady-state) — not just proof-notebook eyeballing.

### Actuator Effects
- **D-05:** **Full coupling** of the four spec'd actuators: heater adds heat (and dries); fogger adds moisture and drags temperature down (evaporative cooling); fan/cooler extracts heat; vent exchanges air with outside, driving both temperature and humidity toward ambient. No clean "one knob per state" mapping.
- **D-06:** Actuator duty % maps **linearly/proportionally to its physical rate** (no relay deadband or min-turn-on nonlinearity).
- **D-07:** Coupling strength coefficients are exposed as **named parameters in a dict** (per actuator × state effect), not inline constants — reusable/tunable by later phases.
- **D-08:** Coupling matrix covers **exactly the four spec'd actuators** (heater, fan/cooler, fogger, vent); no extra inputs (no shading/CO2).

### Weather Profile Shape
- **D-09:** `weather_profile.csv` holds a **noisy realistic 24h cycle** — sine/day–night backbone plus mild gaussian noise (clouds/wind logic) so controllers must reject disturbance. — **Reversibility:** reversible — swap to a pure-sine file and rerun; nothing else changes.
- **D-10:** CSV stores **rows of (time, temp, RH)**; the model **linearly interpolates** between rows at any `dt`.
- **D-11:** Outdoor humidity is **anti-correlated with temperature** (opposing diurnal: cool/humid night, warm/drier midday).
- **D-12:** Profile generation is a **configurable generator** (amplitude, duration, noise seed configurable) committed in `src/` so the CSV is reproducible and later phases (GA robustness, dashboard) can vary scenarios.

### Simulation Framing
- **D-13:** Integration is **fixed-step forward Euler** (NumPy-only, fast and deterministic; adequate for a stable plant and cheap for GA fitness runs). — **Reversibility:** costly — swapping the integrator changes trace shape every downstream metric and comparison is built on.
- **D-14:** Default horizon **24h at dt=60s (1440 steps)**, both exposed as parameters so GA and notebooks can override.
- **D-15:** API is a **pure, stateless step function** in `greenhouse_model.py`: `step(dt, actuators, weather_at_t) -> (temp_C, humidity_g_per_kg)`; simulation state lives with the caller. Matches MODEL-04 literally.
- **D-16:** Return **both units from step** — absolute humidity and %RH (small result object / tuple incl. RH via a helper), so callers and the dashboard don't re-derive conversions. (D-03 keeps the ODE state in g/kg; the return surfaces both.)

### the agent's Discretion
- Precise coupling coefficient values and the exact saturation-pressure formula inside the constrained physics — planner/researcher picks numbers consistent with literature defaults and D-01..D-08.
- Exact CSV row resolution (e.g. 15-min vs hourly rows) within the interpolation contract (D-10).
- Sanity-test framework shape (pytest vs plain assert script) — D-04 only mandates that checks exist.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Spec
- `.planning/PROJECT.md` — spec constraints for `greenhouse_model.py`, `weather_profile.csv`, actuator list, target directory layout. Source-of-truth for scope.
- `.planning/REQUIREMENTS.md` — MODEL-01..04 definitions and traceability.
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria (4 items), requirement mapping.

No external specs — requirements are fully captured in the decisions above plus the project planning docs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — the repository has no `src/` code yet; Phase 1 creates the first module.

### Established Patterns
- No codebase patterns exist yet. Phase 1 sets the convention later phases build on: NumPy-only numerics, pure/stateless functions, data as CSV under `weather/` or root per PROJECT.md (exact layout is a planning-time decision).

### Integration Points
- `greenhouse_model.py` and `weather_profile.csv` are consumed by every later phase (controllers, GA fitness, metrics, notebooks, dashboard). Contract stability (D-15/D-16) is the integration anchor.

</code_context>

<specifics>
## Specific Ideas

- Physical plausibility and stability are explicit goals — the model must produce stable, physically plausible traces, not just "any" heat-up behavior.
- Determinism matters: GA fitness runs the sim repeatedly, so the noisy weather generator must be seedable (D-12).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Greenhouse Model & Weather*
*Context gathered: 2026-09-20*