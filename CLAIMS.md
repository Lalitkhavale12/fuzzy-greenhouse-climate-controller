# Claim → Code Traceability

Every element asserted in the draft claims, mapped to the code that implements
and the test that proves it. Symbols, not line numbers, so the table survives
refactors — grep the name to land on it.

**Read this first:** the right-hand column is evidence of *implementation*, not
of *novelty*. The frozen results (`results/`, `weather/`) still come from the
62-D, schema-2 run; the CO₂ valve, rule weights and explorer are additive and
opt-in, so the reported 114.28 holdout score is unchanged by them.

Claim numbering follows the draft. Paste the exact claim wording into the left
column when filing — do not let the draft and this table drift apart.

| # | Claim element (draft wording summary) | Implementation | Proof |
|---|---|---|---|
| 1 | Greenhouse climate controller actuating **five** devices: heater, fan/cooler, fogger, vent, **CO₂ valve** | `src/greenhouse_model.py: step`, `step_co2` (4-key core forwarded verbatim); `Q_CO2`, `K_LEAK`, `C_OUT_PPM`; CO₂ flushes by vent exchange under `params["X_v"]` | `tests/test_co2.py`: wrapper bit-identical to `step()`, dosed accumulation, vented flush, 5-key contract enforced |
| 1 | CO₂ concentration state tracked and displayed | `step_co2` returns `(T, w, rh, C_ppm)` with `C_LO..C_HI` clamp; `dashboard/pages/01_model_sim.py` slider + ppm trace panel; `05_plant_house.py` enrichment slider | `tests/test_dashboard.py: test_co2_wiring`; `tests/test_co2.py` |
| 2 | **Sensor acquisition module** producing plant measurements and derived tracking errors | `src/sensors.py: sense_plant`, `tracking_errors`; consumed by `src/adaptive_fuzzy.py` (`state['sens']`) | `tests/test_sensors.py`: 3 checks (acquisition, per-minute rates, adaptive consumes the module) |
| 3 | **Mamdani fuzzy inference** over a 5×5 error / error-rate rule base | `src/fuzzy_controller.py: RULES`, `LABELS`, `tri`, `infer` (min-implication, centroid defuzz), `fuzzy_step` | `tests/test_fuzzy_controller.py` |
| 4 | **Rule-base inspection / exploration** — the rule table and live firing strengths | `dashboard/helpers.py: rule_table`, `rule_firing`; `dashboard/pages/03_ga_explorer.py` probe sliders + winning-rule readout | `tests/test_dashboard.py: test_rule_table` (5×5 exact, ZO/ZO dominates at origin) |
| 5 | **Evolutionary optimisation of the controller**, including **per-rule weights** (87-D chromosome) | `src/genetic_algorithm.py: RW_LO/RW_HI`, `RW_LEN`, `FULL_LEN`, `encode`, `decode`, `init_population(rule_weights=)`, `run_ga(rule_weights=)`, `_write_json(rule_weights=)`; weights applied in `src/fuzzy_controller.py: infer(RW=)` | `tests/test_genetic_algorithm.py: test_rule_weights_87d` (round-trip, clamping, zero-weight silencing, schema-3 save/load, 87-D fitness path) |
| 5 | Optimised parameters load back into the controller | `src/ga_fuzzy_controller.py: load_optimized_mfs`, `load_rule_weights`, `ga_fuzzy_step`; schema 2 and 3 both accepted | `tests/test_genetic_algorithm.py: test_rule_weights_87d`, `test_decode_*` |
| 6 | **Adaptive** gain driven by an EMA of the tracking error | `src/adaptive_fuzzy.py: adaptive_fuzzy_step` (`gT`, `aT` in caller-owned state) | `tests/test_adaptive.py` |
| 6 | Baselines for comparison (on/off with hysteresis, PID with anti-windup) | `src/onoff_controller.py: onoff_step`, `src/pid_controller.py: pid_step` | `tests/test_baseline_controllers.py` |
| — | Scoring: temperature IAE, humidity IAE, **energy as duty-hours over all actuators including vent**, weighted cost, rank | `src/metrics.py: COLUMNS`, `energy_duty_hours` (duty fraction × dt, summed), `weighted_cost` | `tests/test_metrics.py` |

## Known wording fixes before filing

- **Energy claim**: say *duty-cycle fractions* and *duty-hours*, never
  "percentages" of a rated load — `energy_duty_hours` integrates `u` over time
  with no nameplate power, so "percentage of full load" is unsupportable.
- **CO₂ claim scope**: the valve is simulated and operated open-loop (Model Sim)
  or as a dosed setpoint (Plant House). The closed-loop controllers do not dose
  CO₂. State that limitation rather than implying closed-loop CO₂ regulation.
- **Rule weights**: the shipped artifact is schema 2 with no weights; the 87-D
  path is enabled by `run_ga(..., rule_weights=True)`. Say "configurable /
  opt-in" rather than implying the frozen run used it.
