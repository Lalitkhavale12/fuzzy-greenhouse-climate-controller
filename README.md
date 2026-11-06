# GA-Optimized Fuzzy Greenhouse Climate Controller

A simulation-and-control study comparing classical and intelligent greenhouse
climate controllers. A simulated plant (energy-balance ODE driven by actuator
states + outdoor weather) is driven by on/off, PID, hand-tuned Mamdani fuzzy,
GA-optimized fuzzy, and adaptive fuzzy controllers, then scored on
temperature/humidity tracking error, energy use, and step-response metrics.

**Headline result:** GA fuzzy holds rank #1 on the frozen holdout
(weighted cost 114.28 — beats on/off and PID), reproduced end-to-end from
notebooks and dashboard.

## Run

```bash
pip install -r requirements.txt
python -m streamlit run dashboard/app.py     # dashboard → http://localhost:8501
python -m pytest tests/ -q                   # full suite (89 tests, 10 files)
python tests/test_dashboard.py               # headless acceptance suite (23 checks)
python dashboard/helpers.py                  # helpers self-check
```

## Pages

- **Model Sim** — open-loop plant + weather explorer (duty sliders, incl. the
  CO₂ valve dose; 4-panel T / humidity / RH / CO₂ trace)
- **Controllers** — all four controllers side-by-side on shared weather, scenario
  A/B comparison, overlay chart, robustness table
- **GA Explorer** — frozen GA artifact: convergence, MF before/after, MF drag
  explorer, generation replay, MF sensitivity analysis, plus the 5×5 rule-base
  table and a live rule-firing readout for any (error, error-rate) probe
- **Results** — frozen scoreboard + verdict + evidence ZIP, Pareto tradeoff
- **Plant House** — 3D greenhouse, live crop-health from the real closed loop,
  CO₂ enrichment slider

## Capabilities beyond the frozen baseline

- `src/sensors.py` — sensor acquisition layer (`sense_plant`, `tracking_errors`)
  consumed by the adaptive controller
- `src/greenhouse_model.py:step_co2` — CO₂ valve as a fifth actuator; thermal
  core is `step()` verbatim, so 4-actuator traces are bit-identical
- `src/genetic_algorithm.py` — optional 25 rule-weight genes (87-D chromosome),
  `run_ga(..., rule_weights=True)`; artifacts gain `schema_version: 3`
- Frozen results remain the 62-D, schema-2 run: `results/` is never rewritten
  by the dashboard or by these opt-in paths

## Layout

- `src/` — model, controllers, GA, metrics, sensors (read-only for the dashboard)
- `notebooks/01–06` — proof-of-work trail, each calling into `src/`
- `dashboard/` — thin Streamlit wrapper (`helpers.py` holds all shared logic)
- `results/`, `weather/` — frozen artifacts (never written by dashboard code)
- `tests/` — 10 files, 89 pytest tests; `test_dashboard.py` also runs standalone
- `CLAIMS.md` — claim-element → code traceability table
