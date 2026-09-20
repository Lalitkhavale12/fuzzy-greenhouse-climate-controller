# Walking Skeleton — GA-Optimized Fuzzy Greenhouse Climate Controller

**Phase:** 1
**Generated:** 2026-09-20

## Capability Proven End-to-End

A climate-control researcher can run a 24-hour open-loop simulation of a greenhouse plant — coupled temperature and humidity responding to four actuator duties, driven by a generated synthetic weather profile CSV — and see the resulting physically plausible traces plotted, all through plain Python + NumPy with a documented one-line run command.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Language / numerics | Python 3 + NumPy only (numpy 2.4.3 installed) | Locked stack (AGENTS.md); zero new dependencies; numpy is sufficient for the ODE pair, CSV I/O, and interpolation. Matplotlib (3.10.8 installed) for notebook plots only. |
| Plant formulation | Per-m³ lumped coupled energy + moisture ODE pair (D-01), forward Euler at dt=60s (D-13/D-14) | Deterministic and cheap for GA fitness loops; probe-verified 46x/12x margin below the non-oscillatory bound, 0.023 C / 0.030 g/kg drift vs dt=5s over 24h. |
| Controller interface (D-15/D-16) | Pure stateless `step(dt, actuators, weather_at_t, T_C, w_gkg) -> (T_C, w_gkg, rh_pct)` | Caller owns state; identical calls are reproducible — the anchor every later controller and the GA fitness loop builds on. |
| Weather data layer (D-10/D-12) | Seedable `generate_weather_profile()` writes 15-min CSV (97 rows + header); `load_weather_profile()` validates on load and linearly interpolates via numpy.interp | Deterministic, reproducible experiments; fail-fast parsing keeps malformed files out of the simulation. |
| Test runner | Plain-assert single file `python tests/test_greenhouse_model.py` (7 checks, exits nonzero on failure) | pytest NOT installed; plain-assert keeps the suite dependency-free and pytest-compatible for later phases. |
| Error handling | Fail-fast asserts + physical clamps, no try/except | Silent drops and swallowed errors are forbidden; invalid actuator keys and out-of-range CSV rows must raise. |
| Directory layout | `src/` (library), `tests/` (suite), `notebooks/` (proof-of-work), `weather/` (generated data) | Notebooks import from src/ only — no duplicated logic (AGENTS.md compatibility constraint). |

## Stack Touched in Phase 1

- [x] Project scaffold — `src/__init__.py` package marker, `src/greenhouse_model.py`, `src/weather_profile_generator.py`, documented run command (`python tests/test_greenhouse_model.py`)
- [ ] Routing — N/A (library project; the notebook is the primary "route" into the stack)
- [x] Database — one real WRITE: `weather/weather_profile.csv` via savetxt; one real READ: `load_weather_profile()` via np.loadtxt + interp
- [x] UI — one interactive element: the notebook simulates 24h and plots T/w/RH traces with matplotlib (Agg backend)
- [x] Deployment — documented local run command: `python tests/test_greenhouse_model.py` (suite) and notebook execution via any standard Jupyter client

## Out of Scope (Deferred to Later Slices)

- Controllers of any kind (on/off, PID, fuzzy, GA) — phases 2-4
- Dual-loop humidity control, setpoint tracking, closed-loop simulation harness — phases 2-4
- Metrics / comparison scoring (IAE, RMSE, energy) — phase 5
- The full six-notebook proof-of-work trail and the Streamlit dashboard — phases 6-7
- Greenhouse structural/geometric realism, crop models, weather forecasting, real sensor I/O — never planned (simulation study)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: On/off and PID controllers drive this plant to temperature/humidity setpoints (the benchmarks to beat)
- Phase 3: Hand-tuned Mamdani fuzzy controller controls the plant, reusing the same step interface
- Phase 4: GA tunes fuzzy membership functions so the GA fuzzy controller beats both baselines on the weighted cost
- Phase 5: Metrics module scores all four controllers into a machine-readable comparison table
- Phase 6: Six milestone notebooks reproduce the whole proof-of-work trail against src/
- Phase 7: Streamlit dashboard thin-wraps the finished src/ library