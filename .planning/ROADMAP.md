# Roadmap: GA-Optimized Fuzzy Greenhouse Climate Controller

**Granularity:** Standard (5-8 phases)
**Mode:** mvp (vertical slices — each phase delivers an end-to-end working capability)

## Phase 1: Greenhouse Model & Weather
**Goal:** Simulated greenhouse plant that responds to actuator states and outdoor weather.
**Mode:** mvp
**Success Criteria:**
1. `greenhouse_model.py` returns next temperature/humidity from timestep + actuator states using the energy-balance ODE
2. `weather_profile.csv` holds a synthetic day/night temp and humidity cycle and drives the model as outdoor disturbance
3. A simulation run produces stable, physically plausible temperature/humidity traces
4. All four actuator inputs (heater, fan/cooler, fogger, vent) affect the state

**Requirements:** MODEL-01, MODEL-02, MODEL-03, MODEL-04
**Plans:** 1 plan

Plans:
- [x] 01-PLAN.md — coupled ODE greenhouse plant + seedable weather generator + plain-assert suite + proof-of-work notebook (executed, verified 2026-09-21; CR-01 peak fix in db83e9b)

## Phase 2: Baseline Controllers
**Goal:** On/off and PID controllers that track setpoints on the plant — the benchmarks to beat.
**Mode:** mvp
**Success Criteria:**
1. `onoff_controller.py` toggles actuators fully on/off by error threshold
2. `pid_controller.py` returns continuous control signals from P, I, D terms
3. Both controllers drive the model toward temperature and humidity setpoints when plugged into a closed-loop sim
4. Outputs are comparable actuator command structures (duty percentages) shared with later controllers

**Requirements:** BASE-01, BASE-02, BASE-03
**Plans:** 1 plan

Plans:
- [x] 02-PLAN.md — hysteresis on/off + dual-loop PID baselines, 8-check suite, closed-loop proof notebook (executed, verified 2026-09-21; WR-01/WR-02 review fixes in a795b7b)

## Phase 3: Manual Fuzzy Controller
**Goal:** Hand-tuned Mamdani fuzzy controller controls the plant before any GA work.
**Mode:** mvp
**Success Criteria:**
1. `fuzzy_controller.py` implements Mamdani inference: 5 triangular MFs per variable (NB..PB), ~25 rules, centroid defuzz
2. Inputs are temperature error and error rate-of-change (dual-loop variant covers humidity)
3. Outputs heater/cooler/fan duty cycle
4. Hand-tuned parameters control the plant to setpoint — `fuzzy_controller.py` proves it works before GA

**Requirements:** FUZZ-01, FUZZ-02, FUZZ-03, FUZZ-04, FUZZ-05, FUZZ-06
**Plans:** 1 plan

Plans:
- [x] 03-PLAN.md — velocity-form dual-loop Mamdani fuzzy, 9-check suite, closed-loop proof notebook (executed, verified 2026-09-22; WR-01 RH-grid review fix in 9aa65dc)

## Phase 4: GA Optimization
**Goal:** GA tunes fuzzy membership functions so the GA fuzzy controller beats both baselines.
**Mode:** mvp
**Success Criteria:**
1. `genetic_algorithm.py` encodes MF center/width params in a real/binary chromosome
2. Fitness = `w1*IAE_T + w2*IAE_H + w3*energy` via full simulation, lower is better
3. Selection, crossover, gaussian mutation, and elitism all implemented and converging
4. `results/ga_optimized_params.json` saved with the best chromosome
5. `ga_fuzzy_controller.py` loads those params and produces lower weighted-cost than baselines in a holdout run

**Requirements:** GA-01, GA-02, GA-03, GA-04, GA-05

## Phase 5: Metrics & Comparison
**Goal:** Quantified scoreboard across all four controllers.
**Mode:** mvp
**Success Criteria:**
1. `metrics.py` computes RMSE, IAE, ISE, settling time, overshoot, total energy from logged sim history
2. Comparison table covers on/off, PID, manual fuzzy, GA fuzzy
3. Table is machine-readable (CSV/DataFrame) for notebook/dashboard reuse

**Requirements:** METR-01, METR-02

## Phase 6: Milestone Notebooks
**Goal:** Six notebooks document each milestone with plots — the proof-of-work trail.
**Mode:** mvp
**Success Criteria:**
1. Six notebooks exist, each calling into `src/` (no duplicated logic)
2. Notebooks cover: model+weather, baselines, manual fuzzy, GA, metrics/comparison, final results
3. Each produces relevant plots (traces, membership functions, GA convergence, comparison)
4. Notebooks run top-to-bottom against `src/` functions

**Requirements:** PROOF-01

## Phase 7: Streamlit Dashboard
**Goal:** Four-page thin UI wrapper over the finished `src/` library.
**Mode:** mvp
**Success Criteria:**
1. Dashboard has four pages (e.g., Model Sim, Controllers, GA Explorer, Results)
2. Sliders/dropdowns drive the same `src/` functions
3. Charts update live
4. Built last, once everything above is stable

**Requirements:** PROOF-02

---
*Roadmap created: 2026-09-20 (inline — gsd-roadmapper not installed)*