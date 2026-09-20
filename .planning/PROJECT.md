# GA-Optimized Fuzzy Greenhouse Climate Controller

## What This Is

A simulation-and-control study comparing classical and intelligent greenhouse climate controllers. A simulated greenhouse plant (energy-balance ODE driven by actuator states and outdoor weather) is controlled by four controllers — on/off, PID, manually-tuned Mamdani fuzzy, and GA-optimized fuzzy — then scored on temperature/humidity tracking error, energy use, and step-response metrics. The whole thing is a proof-of-work trail of matplotlib notebooks culminating in a Streamlit dashboard. It is an academic/build project: baselines exist to be beaten by the fuzzy/GA controller.

## Core Value

The GA-optimized fuzzy controller must measurably beat both baselines (on/off and PID) on the combined weighted cost (temperature IAE + humidity IAE + energy) in the simulation, with the comparison reproduced end-to-end from the notebooks.

## Business Context

<!-- Internal academic project — no monetization. -->

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Simulation plant: temperature/humidity energy-balance model driven by actuator states and outdoor weather
- [ ] Synthetic outdoor weather profile (day/night temp/humidity cycle from CSV)
- [ ] On/off baseline controller
- [ ] PID baseline controller
- [ ] Manually-tuned Mamdani fuzzy controller (5 MFs/var, ~25 rules, centroid defuzzification)
- [ ] GA optimization of fuzzy membership functions (real/binary vector chromosome, weighted IAE+energy fitness, selection/crossover/mutation/elitism)
- [ ] GA-optimized fuzzy controller (loads params from JSON)
- [ ] Metrics: RMSE, IAE, ISE, settling time, overshoot, total energy
- [ ] Final comparison table across all four controllers
- [ ] Six milestone notebooks calling into src/
- [ ] Streamlit dashboard (four pages, thin UI wrapper over src/)

### Out of Scope

- Real hardware / actuator control — simulation only
- PID tuning automation — standard hand-tuned P, I, D suffices as a baseline
- Type-2 or neuro-fuzzy systems — Mamdani + GA is the deliverable
- Dynamic/adaptive GA (self-tuning population size, adaptive mutation rates) — fixed operators suffice
- Climate forecasting / humidity setpoint scheduling logic — fixed setpoints per the spec

## Context

- **Domain**: fuzzy logic control, PID vs fuzzy benchmarking, genetic algorithm parameter optimization.
- **Language**: Python. Controllers live in `src/` (or package dir), notebooks import them.
- **Spec constraints** (from the provided build spec):
  - `greenhouse_model.py` — simulated plant; given timestep + actuator states (heater/fan/fogger duty, vent position) returns next internal temp & humidity via simplified energy-balance ODE; consumes `weather_profile.csv` for outdoor disturbance.
  - Actuators: heater (on/off %), fan/cooler (on/off %), fogger (on/off %), vent position.
  - `onoff_controller.py` — actuator fully on if error exceeds threshold, off otherwise.
  - `pid_controller.py` — standard P, I, D.
  - `fuzzy_controller.py` — Mamdani; inputs temp error, temp-error rate-of-change (and same for humidity if dual-loop); 5 linguistic terms (NB, NS, ZO, PS, PB), triangular MFs; ~25 rules (5x5 grid); output heater/cooler/fan duty; centroid defuzz. Must control the model hand-tuned BEFORE GA.
  - `genetic_algorithm.py` — chromosome encodes MF center/width params; fitness runs full sim and returns `w1*IAE_temp + w2*IAE_humidity + w3*energy` (lower better); tournament/roulette selection, single-point/blend crossover, gaussian mutation, elitism; output to `results/ga_optimized_params.json`.
  - `ga_fuzzy_controller.py` — same inference engine, loads params from `ga_optimized_params.json`.
  - `metrics.py` — RMSE, IAE, ISE, settling time, overshoot, total energy from logged sim history; builds final comparison table.
  - Six notebooks — each milestone, plots, calls `src/`. Proof-of-work, not separate logic.
  - Streamlit dashboard — four pages, sliders/dropdowns into same `src/` functions, live charts. Built last.

- **Directories**: controllers under `src/` (or `controllers/`), weather/output data under `weather/`/`results/` or root-level CSVs per spec naming (`weather_profile.csv`, `results/ga_optimized_params.json`). Exact layout is a planning-time decision.

## Constraints

- **Tech**: Python 3, NumPy (numerics), Streamlit (dashboard UI). Plotting via Matplotlib in notebooks. CSV for weather input and GA params (JSON per spec).
- **Order**: hand-tuned fuzzy first, GA second (GA assumes a working fuzzy engine); dashboards last.
- **Compatibility**: notebooks must run against `src/` functions with no duplicated logic.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Simulation-only (no hardware) | Spec is a simulation/benchmark study | — Pending |
| Mamdani fuzzy, triangular MFs, centroid defuzz | Spec: standard, easiest to encode for GA | — Pending |
| Weighted fitness `w1*IAE_T + w2*IAE_H + w3*energy` | Spec | — Pending |
| Metrics: RMSE, IAE, ISE, settling, overshoot, energy | Spec | — Pending |
| Dashboard last | Spec: thin wrapper, requires stable src/ | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-20 after initialization*