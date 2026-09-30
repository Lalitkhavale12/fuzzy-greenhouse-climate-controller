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

from dashboard.helpers import DISPLAY, load_kpi_row

st.set_page_config(page_title="Fuzzy Greenhouse Climate Controller", layout="wide")

st.title("GA-Optimized Fuzzy Greenhouse Climate Controller")
st.markdown(  # ui-ux-pro-max card pattern: injected once, styles all pages
    "<style>"
    '[data-testid="stMetric"]{background:#FFFFFF;border:1px solid #DCE7D4;'
    "border-radius:12px;padding:12px 16px;"
    "box-shadow:0 1px 3px rgba(38,48,35,.08);}"
    '[data-testid="stMetricLabel"]{color:#475569;}'
    "h1{letter-spacing:-.02em;}h2{color:#2E7D32;}"
    "</style>",
    unsafe_allow_html=True,
)
try:
    kpi = load_kpi_row()
    st.success("Headline: %s ranks #1 on the frozen holdout — weighted cost "
               "%.2f (IAE_T %.2f, IAE_H %.2f), beating on/off and PID."
               % (DISPLAY["ga_fuzzy"], float(kpi["cost"]),
                  float(kpi["iae_T"]), float(kpi["iae_H"])))
except (OSError, ValueError, AssertionError, KeyError):
    st.warning("Frozen scoreboard unreadable — pages will report the fault.")
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
    "instant and always consistent with Phase 5.\n"
    "- **Plant House** — 3D greenhouse with live crop-health from the real "
    "closed loop."
)
