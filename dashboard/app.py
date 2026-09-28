"""Greenhouse climate controller dashboard — landing page (D-01).

Multipage root: Streamlit auto-discovers dashboard/pages/*.py as sidebar
pages in numeric-prefix order. This file holds page config + landing
markdown only; every page drives the finished src/ library directly.

Run:  python -m streamlit run dashboard/app.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(page_title="Fuzzy Greenhouse Climate Controller", layout="wide")

st.title("GA-Optimized Fuzzy Greenhouse Climate Controller")
st.markdown(
    "Thin UI wrapper over the finished `src/` library — no new control "
    "logic, no recomputation of frozen artifacts.\n\n"
    "- **Model Sim** — move heater/fan/fogger/vent duty sliders and watch "
    "the open-loop plant respond.\n"
    "- **Controllers** — setpoint + weather-seed sliders rerun all four "
    "controllers on shared weather in seconds.\n"
    "- **GA Explorer** — convergence + membership before/after from the "
    "frozen `results/ga_optimized_params.json` artifact.\n"
    "- **Results** — frozen `results/comparison.csv` scoreboard + verdict, "
    "instant and always consistent with Phase 5."
)
