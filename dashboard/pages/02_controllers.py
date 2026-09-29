"""Controllers page — all four controllers on shared weather (D-03).

Setpoint + seed sliders rerun the closed loop live (seconds-scale).
Runs its own run_closed_loop loops on shared weather — never the CSV
writer from src.metrics — so the frozen results/comparison.csv stays
untouched. Seeds 7/21 resolve to frozen
files; every other seed generates to an ephemeral tempfile path.

Run:  python -m streamlit run dashboard/app.py
"""

import csv
import functools
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np

import streamlit as st

from src.metrics import COLUMNS, all_metrics, run_closed_loop
from src.onoff_controller import onoff_step
from src.pid_controller import pid_step
from src.fuzzy_controller import fuzzy_step
from src.ga_fuzzy_controller import ga_fuzzy_step
from src.weather_profile_generator import generate_weather_profile
from dashboard.helpers import build_scenario_figure, fig_to_png_bytes, \
    scenario_delta, holdout_ranking, DISPLAY, build_controller_trace_figure, \
    load_kpi_row


def resolve_weather(seed):
    """Frozen files for seeds 7/21, ephemeral tempfile paths otherwise."""
    if seed == 7:
        return "weather/weather_profile.csv"
    if seed == 21:
        return "weather/holdout_21.csv"
    path = os.path.join(tempfile.mkdtemp(), "seed_%d.csv" % seed)
    generate_weather_profile(path, seed=seed)
    return path


@st.cache_data
def run_all_four(T_sp, RH_sp, seed):
    """4 x 1440-step closed loops on the shared weather path.

    Returns (hours, dict name -> (T_hist, RH_hist, U_hist)).
    """
    path = resolve_weather(seed)
    steps = [
        ("on/off", onoff_step),
        ("PID", functools.partial(pid_step, dt=60.0)),
        ("hand fuzzy", functools.partial(fuzzy_step, dt=60.0)),
        ("GA fuzzy", functools.partial(ga_fuzzy_step, dt=60.0)),
    ]
    runs = {}
    for name, ctl in steps:
        T_h, RH_h, U_h = run_closed_loop(ctl, path, n=1440, T_sp=T_sp, RH_sp=RH_sp)
        runs[name] = (T_h, RH_h, U_h)
    hours = np.arange(0, 1440) / 60.0
    return hours, runs


st.title("Controllers — side-by-side on shared weather")

try:
    kpi = load_kpi_row()
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen scoreboard unreadable: %s" % exc)
    st.stop()
c1, c2, c3, c4 = st.columns(4)
c1.metric("%s holdout cost" % DISPLAY["ga_fuzzy"],
          "%.2f" % float(kpi["cost"]))
c2.metric("%s holdout rank" % DISPLAY["ga_fuzzy"], "#%s" % kpi["rank"])
c3.metric("IAE_T", "%.2f" % float(kpi["iae_T"]))
c4.metric("IAE_H", "%.2f" % float(kpi["iae_H"]))

T_sp = st.slider("T setpoint (degC)", 18.0, 30.0, 25.0, 0.5)
RH_sp = st.slider("RH setpoint (%)", 50, 90, 70, 1)
seed_A = st.slider("weather seed A", 1, 50, 7, 1)
seed_B = st.slider("weather seed B", 1, 50, 21, 1)

# Intentional inline pair (IN-04): run_scenario_pair drops `hours`, which the
# paired-trace figure below needs — so the page calls cached run_all_four
# twice directly (cache keyed per side, same primitive, no drift).
hours_a, runs_a = run_all_four(T_sp, RH_sp, seed_A)
hours_b, runs_b = run_all_four(T_sp, RH_sp, seed_B)
delta_rows = scenario_delta(runs_a, runs_b, T_sp, RH_sp)
st.dataframe(delta_rows)
costs_a = {n: all_metrics(T, RH, U, T_sp, RH_sp)["cost"]
           for n, (T, RH, U) in runs_a.items()}
costs_b = {n: all_metrics(T, RH, U, T_sp, RH_sp)["cost"]
           for n, (T, RH, U) in runs_b.items()}
rank_a = sorted(costs_a, key=costs_a.get).index("GA fuzzy") + 1
rank_b = sorted(costs_b, key=costs_b.get).index("GA fuzzy") + 1
st.write("GA still wins: side A rank %d / side B rank %d" % (rank_a, rank_b))

fig = build_scenario_figure(hours_a, runs_a, runs_b, T_sp, RH_sp,
                            seed_A, seed_B)
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="controllers_traces.png", mime="image/png")
tT, tH, tE = st.tabs(["Temperature", "Humidity", "Energy"])
with tT:
    st.pyplot(build_controller_trace_figure(hours_a, runs_a, runs_b, T_sp,
                                            RH_sp, seed_A, seed_B, "T"))
with tH:
    st.pyplot(build_controller_trace_figure(hours_a, runs_a, runs_b, T_sp,
                                            RH_sp, seed_A, seed_B, "RH"))
with tE:
    st.pyplot(build_controller_trace_figure(hours_a, runs_a, runs_b, T_sp,
                                            RH_sp, seed_A, seed_B, "energy"))

with st.expander("Provenance"):
    st.write("Controllers rerun the src closed loops live on shared weather "
             "(seeds 7/21 resolve to frozen files, other seeds ephemeral). "
             "Scoreboard: results/comparison.csv (8 rows, frozen). "
             "Seeds 7/21, weights 1.0/1.0/0.01.")
