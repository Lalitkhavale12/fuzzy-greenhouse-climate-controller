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
**Plans:** 1 plan

Plans:

- [x] 04-PLAN.md — 62-D cross-coupled GA (tournament/BLX/gaussian/elitism-2), run-3 JSON, holdout GA 114.28 beats both baselines (executed, verified 2026-09-27; D-06/A2 cross-coupling after run-1/run-2 decoupled block)

## Phase 5: Metrics & Comparison

**Goal:** Quantified scoreboard across all four controllers.
**Mode:** mvp
**Success Criteria:**

1. `metrics.py` computes RMSE, IAE, ISE, settling time, overshoot, total energy from logged sim history
2. Comparison table covers on/off, PID, manual fuzzy, GA fuzzy
3. Table is machine-readable (CSV/DataFrame) for notebook/dashboard reuse

**Requirements:** METR-01, METR-02
**Plans:** 1 plan

Plans:

- [x] 05-PLAN.md — metrics.py six kernels + compare() scoreboard (8x14 CSV, GA rank 1 both weathers), 9-check suite (executed, verified 2026-09-27)

## Phase 6: Milestone Notebooks

**Goal:** Six notebooks document each milestone with plots — the proof-of-work trail.
**Mode:** mvp
**Success Criteria:**

1. Six notebooks exist, each calling into `src/` (no duplicated logic)
2. Notebooks cover: model+weather, baselines, manual fuzzy, GA, metrics/comparison, final results
3. Each produces relevant plots (traces, membership functions, GA convergence, comparison)
4. Notebooks run top-to-bottom against `src/` functions

**Requirements:** PROOF-01
**Plans:** 1 plan

Plans:

- [x] 06-PLAN.md — 05_comparison + 06_final_results notebooks, 13-check audit harness, 04 uniformity fixes (executed, verified 2026-09-28; clean review, 0 findings)

## Phase 7: Streamlit Dashboard

**Goal:** Four-page thin UI wrapper over the finished `src/` library.
**Mode:** mvp
**Success Criteria:**

1. Dashboard has four pages (e.g., Model Sim, Controllers, GA Explorer, Results)
2. Sliders/dropdowns drive the same `src/` functions
3. Charts update live
4. Built last, once everything above is stable

**Requirements:** PROOF-02
**Plans:** 1 plan

Plans:

- [x] 07-PLAN.md — 4-page dashboard (Model Sim, Controllers, GA Explorer, Results) + 7-check headless suite, server boot-verified (executed, verified 2026-09-28; 6 review findings fixed in fcbac94)

---

## Milestones

- ✅ **v1.0 MVP** - Phases 1-7 (shipped 2026-09-28, core value met: GA 114.28 beats both baselines)
- 🚧 **v1.1 Dashboard Polish** - Phases 8-10 (in progress)

## v1.1 Phases (Dashboard Polish)

**Milestone Goal:** Make the Streamlit dashboard interactive and presentation-grade without touching control logic or frozen artifacts. Zero new installs; one new shared module (`dashboard/helpers.py`) + theme sidecar; `src/`/`results/`/`weather/` read-only.

- [ ] **Phase 8: Theme + Export Foundation** - Greenhouse theme sidecar + export-center byte builders
- [ ] **Phase 9: Interactive Analysis** - Scenario comparison + MF explorer + GA convergence replay
- [ ] **Phase 10: Layout Polish + Report Bundle** - KPI-first restyle across all pages + one-click ZIP report

## v1.1 Phase Details

### Phase 8: Theme + Export Foundation

**Goal**: Dashboard has greenhouse identity and users can take results away as files.
**Depends on**: Phase 7
**Requirements**: UI-01, UI-02
**Success Criteria** (what must be TRUE):

  1. Dashboard loads with greenhouse theme (green primary, tinted backgrounds) and charts stay readable in light mode
  2. User can download the scoreboard CSV from the Results page
  3. User can download the verdict summary (who won and by how much)
  4. User can download any comparison chart as PNG

**Plans:** 1 plan

Plans:

- [x] 08-PLAN.md — greenhouse theme sidecar + helpers.py byte builders (CSV/TXT/5 PNGs) + 7 download buttons (executed, verified 2026-09-29; 6 review findings fixed in 8366016)

**UI hint**: yes

### Phase 9: Interactive Analysis

**Goal**: Users can interrogate the results interactively — different weather, reshaped fuzzy sets, generation-by-generation convergence.
**Depends on**: Phase 8
**Requirements**: UI-04, UI-05, UI-06
**Success Criteria** (what must be TRUE):

  1. User can pick two weather scenarios and see their traces side-by-side on shared sliders
  2. A delta table shows ΔIAE/Δenergy/Δcost between the two scenarios (does GA still win?)
  3. User can drag MF centers and watch the fuzzy response curve reshape live, with reset-to-frozen and validity warnings instead of crashes
  4. User can scrub a generation slider to replay GA convergence with gen + best-fitness readout
  5. Dragging MF sliders never mutates the frozen baseline shown elsewhere

**Plans**: 3 plans
**UI hint**: yes

Plans:
**Wave 1**

- [x] 09-01-PLAN.md — scenario A/B tracer: pair helpers + dual-seed 02 wiring + delta test

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-02-PLAN.md — MF explorer: scratch/sweep/overlay helpers + 10-slider 03 wiring

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-03-PLAN.md — convergence replay: slice/marker helpers + gen-slider 03 wiring (executed, verified 2026-09-29; 7 review findings fixed in 796bfde)

**UI hint**: yes

### Phase 10: Layout Polish + Report Bundle

**Goal**: Every page reads as presentation-grade and examiners leave with one file.
**Depends on**: Phase 9
**Requirements**: UI-03, UI-07
**Success Criteria** (what must be TRUE):

  1. All four pages show metric-card KPI rows, tabbed T/RH/energy traces, and expanders for provenance
  2. Layout stacks vertically and stays usable in a narrow/mobile viewport
  3. User can download one ZIP containing scoreboard CSV + verdict summary + chart PNGs

**Plans**: TBD
**UI hint**: yes

## v1.1 Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. Theme + Export Foundation | 0/TBD | Not started | - |
| 9. Interactive Analysis | 0/TBD | Not started | - |
| 10. Layout Polish + Report Bundle | 0/TBD | Not started | - |

---
*Roadmap created: 2026-09-20 (inline — gsd-roadmapper not installed)*
