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
python tests/test_dashboard.py               # headless acceptance suite (21 checks)
python dashboard/helpers.py                  # helpers self-check
```

## React + FastAPI stack

Same `src/` engine behind a REST API and a React (Vite) frontend:

```bash
python -m uvicorn api.main:app --port 8000   # API → http://localhost:8000
cd frontend && npm install && npm run dev    # UI → http://localhost:5173
python tests/test_api.py                     # API acceptance suite (6 checks)
```

## Pages

- **Model Sim** — open-loop plant + weather explorer (duty sliders)
- **Controllers** — all four controllers side-by-side on shared weather, scenario
  A/B comparison, overlay chart, robustness table
- **GA Explorer** — frozen GA artifact: convergence, MF before/after, MF drag
  explorer, generation replay, MF sensitivity analysis
- **Results** — frozen scoreboard + verdict + evidence ZIP, Pareto tradeoff
- **Plant House** — 3D greenhouse, live crop-health from the real closed loop

## Layout

- `src/` — model, controllers, GA, metrics (read-only for the dashboard)
- `notebooks/01–06` — proof-of-work trail, each calling into `src/`
- `dashboard/` — thin Streamlit wrapper (`helpers.py` holds all shared logic)
- `results/`, `weather/` — frozen artifacts (never written by dashboard code)
- `tests/test_dashboard.py` — standalone plain-assert suite, no pytest needed
