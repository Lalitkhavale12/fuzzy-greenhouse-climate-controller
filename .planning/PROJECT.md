# GA-Optimized Fuzzy Greenhouse Climate Controller

## What This Is

A simulation-and-control study comparing classical and intelligent greenhouse climate controllers. A simulated greenhouse plant (energy-balance ODE driven by actuator states and outdoor weather) is controlled by five controllers — on/off, PID, manually-tuned Mamdani fuzzy, GA-optimized fuzzy, and supervisory adaptive fuzzy — then scored on temperature/humidity tracking error, energy use, and step-response metrics. The whole thing is a proof-of-work trail of matplotlib notebooks culminating in a five-page Streamlit dashboard. It is an academic/build project: baselines exist to be beaten by the fuzzy/GA controller.

## Core Value

The GA-optimized fuzzy controller must measurably beat both baselines (on/off and PID) on the combined weighted cost (temperature IAE + humidity IAE + energy) in the simulation, with the comparison reproduced end-to-end from the notebooks. **Met: GA fuzzy holds holdout rank #1 at cost 114.28.**

## Business Context

<!-- Internal academic project — no monetization. -->

## Requirements

### Validated

- ✓ Simulation plant: temperature/humidity energy-balance model — v1.0
- ✓ Synthetic outdoor weather profile (day/night CSV) — v1.0
- ✓ On/off baseline controller — v1.0
- ✓ PID baseline controller — v1.0
- ✓ Manually-tuned Mamdani fuzzy controller (5 MFs/var, ~25 rules, centroid) — v1.0
- ✓ GA optimization of MFs (62-D chromosome, locked weighted fitness, tournament/BLX/gaussian/elitism-2) — v1.0
- ✓ GA-optimized fuzzy controller (loads params from JSON) — v1.0
- ✓ Metrics: RMSE, IAE, ISE, settling time, overshoot, total energy — v1.0
- ✓ Final comparison table across controllers — v1.0
- ✓ Six milestone notebooks calling into src/ — v1.0
- ✓ Streamlit dashboard, thin UI wrapper over src/ — v1.0
- ✓ Dashboard theming, export center (CSV/TXT/PNG), scenario comparison, MF explorer, convergence replay, KPI restyle, evidence ZIP — v1.1
- ✓ 3D Plant House, overlay chart, sensitivity analysis, robustness table, Pareto frontier, adaptive fuzzy (FUZZ-07) — v1.1

### Active

(None — next milestone defines its requirements via `/gsd-new-milestone`)

### Out of Scope

- Real hardware / actuator control — simulation only
- PID tuning automation — standard hand-tuned P, I, D suffices as a baseline
- Type-2 or neuro-fuzzy systems — Mamdani + GA is the deliverable
- Dynamic/adaptive GA operators (self-tuning population, adaptive mutation) — fixed operators suffice (note: distinct from the shipped adaptive *controller*)
- Climate forecasting / humidity setpoint scheduling logic — fixed setpoints per the spec

## Context

- **Shipped:** v1.0 (2026-09-28) + v1.1 Dashboard Polish (2026-10-06). ~3.9k LOC Python across `src/`, `dashboard/`, `tests/`.
- **Stack:** Python 3.14, NumPy, Streamlit 1.56, Matplotlib, Plotly; pytest (80 checks) + ruff-F gate + notebook execution in CI.
- **Domain**: fuzzy logic control, PID vs fuzzy benchmarking, genetic algorithm parameter optimization.
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
  - Streamlit dashboard — five pages, sliders/dropdowns into same `src/` functions, live charts. Built last.

- **Directories**: controllers under `src/`, weather/output data under `weather/`/`results/`.

## Constraints

- **Tech**: Python 3, NumPy (numerics), Streamlit (dashboard UI). Plotting via Matplotlib in notebooks, Plotly for the 3D Plant House. CSV for weather input and GA params (JSON per spec).
- **Order**: hand-tuned fuzzy first, GA second (GA assumes a working fuzzy engine); dashboards last.
- **Compatibility**: notebooks must run against `src/` functions with no duplicated logic.
- **Quality gates**: pytest suite + ruff-F lint + frozen `results/`/`weather/` (dashboard reads only, never writes).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Simulation-only (no hardware) | Spec is a simulation/benchmark study | ✓ Good |
| Mamdani fuzzy, triangular MFs, centroid defuzz | Spec: standard, easiest to encode for GA | ✓ Good |
| Weighted fitness `w1*IAE_T + w2*IAE_H + w3*energy` | Spec | ✓ Good (GA 114.28 beats baselines) |
| Metrics: RMSE, IAE, ISE, settling, overshoot, energy | Spec | ✓ Good |
| Dashboard last, thin wrapper | Spec: requires stable src/ | ✓ Good |
| Single `dashboard/helpers.py` for all shared logic | Zero-def pages, one tested source of truth | ✓ Good |
| Frozen artifacts read-only for dashboard | Reproducibility; BytesIO-only exports | ✓ Good |
| Checkbox-gated heavy compute | Keeps headless suite fast, user opts into 10-25 run analyses | ✓ Good |
| CSV-arithmetic Pareto (no sim) | Frontier from frozen rows is exact and instant | ✓ Good |

## Current Milestone: SHIPPED v1.1 Dashboard Polish (2026-10-06)

Next milestone defines its requirements via `/gsd-new-milestone`.

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
*Last updated: 2026-10-06 — v1.1 Dashboard Polish shipped (v1.0: phases 01–07; core value met, GA 114.28 holdout rank #1)*
