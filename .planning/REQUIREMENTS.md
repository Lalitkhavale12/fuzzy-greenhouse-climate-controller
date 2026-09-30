# Requirements: GA-Optimized Fuzzy Greenhouse Climate Controller

**Defined:** 2026-09-20
**Core Value:** The GA-optimized fuzzy controller must measurably beat both baselines (on/off and PID) on the combined weighted cost (temperature IAE + humidity IAE + energy) in the simulation, with the comparison reproduced end-to-end from the notebooks.

## v1 Requirements

### Simulation Plant (MODEL)

- [ ] **MODEL-01**: Simulation plant models internal temperature and humidity evolution from actuator states and outdoor weather via a simplified energy-balance ODE
- [ ] **MODEL-02**: Actuator inputs are heater duty, fan/cooler duty, fogger duty, and vent position (each as on/off percent)
- [ ] **MODEL-03**: Plant consumes a synthetic outdoor weather profile (day/night temperature and humidity cycle) from `weather_profile.csv`
- [ ] **MODEL-04**: Plant exposes the next internal temperature and humidity given a timestep and current actuator states

### Baseline Controllers (BASE)

- [ ] **BASE-01**: On/off controller turns each actuator fully on when error exceeds a threshold, off otherwise
- [ ] **BASE-02**: PID controller computes a continuous control signal from standard P, I, D terms on error
- [ ] **BASE-03**: Baseline controllers take current state plus setpoint and return actuator commands

### Fuzzy Controller (FUZZ)

- [ ] **FUZZ-01**: Mamdani-type fuzzy inference system takes temperature error and temperature error rate-of-change as inputs (dual-loop variant includes the same for humidity)
- [ ] **FUZZ-02**: Membership functions use 5 linguistic terms per variable (NB, NS, ZO, PS, PB) with triangular shapes
- [ ] **FUZZ-03**: Rule base of ~25 IF-THEN rules (5x5 grid)
- [ ] **FUZZ-04**: Output is heater/cooler/fan duty cycle
- [ ] **FUZZ-05**: Defuzzification uses the centroid method
- [ ] **FUZZ-06**: Hand-tuned fuzzy controller controls the greenhouse model successfully before GA optimization begins (proves the engine works)

### Genetic Algorithm Optimization (GA)

- [ ] **GA-01**: Chromosome encodes the membership function parameters (center/width of each triangular MF) as a real-valued or binary vector
- [ ] **GA-02**: Fitness function runs the full simulation and returns `w1 * IAE_temperature + w2 * IAE_humidity + w3 * energy` (lower is better)
- [ ] **GA-03**: Uses tournament or roulette selection, single-point or blend crossover, gaussian mutation, and elitism (keep top 1-2 per generation)
- [ ] **GA-04**: Best chromosome saved to `results/ga_optimized_params.json`
- [ ] **GA-05**: GA-optimized fuzzy controller uses the same inference engine but loads MF parameters from `ga_optimized_params.json` instead of hand-picked values

### Metrics & Comparison (METR)

- [ ] **METR-01**: Computes RMSE, IAE, ISE, settling time, overshoot, and total energy from a simulation run's logged temperature/humidity history versus setpoint
- [ ] **METR-02**: Produces final comparison table across all four controllers (on/off, PID, manual fuzzy, GA fuzzy)

### Documentation & Proof (PROOF)

- [ ] **PROOF-01**: Six milestone notebooks, each calling into `src/` and documenting a milestone with plots (no duplicated logic)
- [ ] **PROOF-02**: Streamlit dashboard with four pages — thin UI wrapper with sliders/dropdowns calling the same `src/` functions, live-updating charts

## v1.1 Requirements (Milestone: Dashboard Polish)

### Theming & Layout (UI)

- [x] **UI-01**: Dashboard applies a greenhouse theme via `.streamlit/config.toml` with readable charts in light mode
- [x] **UI-03**: Pages use metric cards, tabs, and expanders with mobile-friendly columns

### Export (UI)

- [x] **UI-02**: Dashboard exports comparison results to disk — scoreboard CSV, chart PNG, and verdict summary downloads (promoted from Deferred)
- [x] **UI-07**: Dashboard bundles exports into a one-click ZIP report

### Interactive Analysis (UI)

- [x] **UI-04**: Controllers page compares two weather scenarios side-by-side on shared sliders
- [x] **UI-05**: GA Explorer page lets the user drag MF centers and watch the fuzzy response reshape live (deep-copied MFs, validity-clamped, frozen baseline never mutated)
- [x] **UI-06**: GA Explorer page replays convergence generation-by-generation over frozen history (slider scrub; no live evolution)

## v2 Requirements

### Deferred

- **FUZZ-07**: Adaptive rule base (beyond fixed 5x5 grid)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real hardware / actuator control | Pure simulation study per spec |
| Type-2 or neuro-fuzzy systems | Mamdani + GA is the deliverable |
| Online / adaptive GA during runtime | GA runs offline to tune MFs only |
| Weather forecasting | Synthetic profile only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MODEL-01 | Phase 1 | Pending |
| MODEL-02 | Phase 1 | Pending |
| MODEL-03 | Phase 1 | Pending |
| MODEL-04 | Phase 1 | Pending |
| BASE-01 | Phase 2 | Pending |
| BASE-02 | Phase 2 | Pending |
| BASE-03 | Phase 2 | Pending |
| FUZZ-01 | Phase 3 | Pending |
| FUZZ-02 | Phase 3 | Pending |
| FUZZ-03 | Phase 3 | Pending |
| FUZZ-04 | Phase 3 | Pending |
| FUZZ-05 | Phase 3 | Pending |
| FUZZ-06 | Phase 3 | Pending |
| GA-01 | Phase 4 | Pending |
| GA-02 | Phase 4 | Pending |
| GA-03 | Phase 4 | Pending |
| GA-04 | Phase 4 | Pending |
| GA-05 | Phase 4 | Pending |
| METR-01 | Phase 5 | Pending |
| METR-02 | Phase 5 | Pending |
| PROOF-01 | Phase 6 | Pending |
| PROOF-02 | Phase 7 | Pending |
| UI-01 | Phase 8 | Verified |
| UI-02 | Phase 8 | Verified |
| UI-03 | Phase 10 | Verified |
| UI-04 | Phase 9 | Verified |
| UI-05 | Phase 9 | Verified |
| UI-06 | Phase 9 | Verified |
| UI-07 | Phase 10 | Verified |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓
- v1.1 requirements: 7 total (UI-01..UI-07)
- Mapped to phases: 7 (Phase 8: UI-01, UI-02; Phase 9: UI-04, UI-05, UI-06; Phase 10: UI-03, UI-07)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-20*
*Last updated: 2026-09-20 after initial definition*