"""Controllers page — all four controllers on shared weather (D-03).

Setpoint + seed sliders rerun the closed loop live (seconds-scale).
Runs its own run_closed_loop loops on shared weather — never the CSV
writer from src.metrics — so the frozen results/comparison.csv stays
untouched. Seeds 7/21 resolve to frozen
files; every other seed generates to an ephemeral tempfile path.

Run:  python -m streamlit run dashboard/app.py
"""

import functools
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import matplotlib.pyplot as plt

import streamlit as st

from src.metrics import run_closed_loop
from src.onoff_controller import onoff_step
from src.pid_controller import pid_step
from src.fuzzy_controller import fuzzy_step
from src.ga_fuzzy_controller import ga_fuzzy_step
from src.weather_profile_generator import generate_weather_profile

NAMES = ["on/off", "PID", "hand fuzzy", "GA fuzzy"]


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
T_sp = st.slider("T setpoint (degC)", 18.0, 30.0, 25.0, 0.5)
RH_sp = st.slider("RH setpoint (%)", 50, 90, 70, 1)
seed = st.slider("weather seed", 1, 50, 21, 1)

hours, runs = run_all_four(T_sp, RH_sp, seed)

fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
for name in NAMES:
    T_h, RH_h, U_h = runs[name]
    ax[0].plot(hours, T_h, label=name, linewidth=1.2)
ax[0].axhline(T_sp, color="k", linestyle="--", linewidth=0.8)
ax[0].set_ylabel("T (degC)")
ax[0].legend(fontsize=8)
ax[0].grid(alpha=0.3)
for name in NAMES:
    T_h, RH_h, U_h = runs[name]
    ax[1].plot(hours, RH_h, label=name, linewidth=1.2)
ax[1].axhline(RH_sp, color="k", linestyle="--", linewidth=0.8)
ax[1].set_ylabel("RH (%)")
ax[1].legend(fontsize=8)
ax[1].grid(alpha=0.3)
for name in NAMES:
    T_h, RH_h, U_h = runs[name]
    ax[2].plot(hours, [u["heater"] for u in U_h], label=name, linewidth=1.2)
ax[2].set_xlabel("hour of day")
ax[2].set_ylabel("heater duty")
ax[2].legend(fontsize=8)
ax[2].grid(alpha=0.3)
fig.suptitle("Closed-loop traces (T_sp %.1f C, RH_sp %d %%, seed %d)"
             % (T_sp, RH_sp, seed))
fig.tight_layout()
st.pyplot(fig)
