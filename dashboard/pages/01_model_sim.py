"""Model Sim page — slider-driven open-loop plant + weather explorer (D-01).

Fixed duties from sliders replace the 01-notebook schedule(h); the loop
body and 3-panel figure are otherwise verbatim from
notebooks/01_greenhouse_model.ipynb cells 2-4 (Agg line dropped).

Run:  python -m streamlit run dashboard/app.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import matplotlib.pyplot as plt

import streamlit as st

from src.greenhouse_model import step, load_weather_profile, daytime_solar, \
    params, step_co2
from dashboard.helpers import fig_to_png_bytes, DISPLAY, load_kpi_row, \
    ephemeral_weather_path

T_INIT_C, W_INIT = 29.28, 20.0  # probe-verified baseline initial condition


@st.cache_data
def cached_weather(seed):
    """Seed-7 resolves to the frozen file; every other seed is ephemeral."""
    if seed == 7:
        path = "weather/weather_profile.csv"
    else:
        path = ephemeral_weather_path(seed)
    return load_weather_profile(path)


def run_open_loop(heater, fan, fogger, vent, co2, seed):
    """Open-loop 24 h trace -> (hours, T, w, rh, C, T_out, w_out)."""
    t_min, T_out, w_out = cached_weather(seed)
    hours = np.arange(0, 1440) / 60.0  # dt = 60 s -> one step per minute
    T_out_hr = np.interp(hours, t_min, T_out)
    w_out_hr = np.interp(hours, t_min, w_out)
    act = {"heater": heater, "fan_cooler": fan, "fogger": fogger,
           "vent": vent, "co2_valve": co2}
    T, w, C = T_INIT_C, W_INIT, 420.0  # probe-verified ICs + outdoor CO2
    T_trace, w_trace, rh_trace, C_trace = [], [], [], []
    for i, h in enumerate(hours):
        ws = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh, C = step_co2(60.0, act, ws, T, w, C)
        T_trace.append(T)
        w_trace.append(w)
        rh_trace.append(rh)
        C_trace.append(C)
    return hours, T_trace, w_trace, rh_trace, C_trace, T_out_hr, w_out_hr


st.title("Model Sim — open-loop plant + weather")

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

heater = st.slider("heater duty", 0.0, 1.0, 0.8, 0.05)
fan = st.slider("fan/cooler duty", 0.0, 1.0, 0.0, 0.05)
fogger = st.slider("fogger duty", 0.0, 1.0, 0.5, 0.05)
vent = st.slider("vent duty", 0.0, 1.0, 0.25, 0.05)
co2 = st.slider("CO2 valve duty", 0.0, 1.0, 0.0, 0.05)
seed = st.slider("weather seed", 1, 50, 7, 1)

hours, T_trace, w_trace, rh_trace, C_trace, T_out_hr, w_out_hr = run_open_loop(
    heater, fan, fogger, vent, co2, seed)
st.metric("inside T range", "[%.2f, %.2f] degC" % (min(T_trace), max(T_trace)))
st.metric("RH range", "[%.1f, %.1f] %%" % (min(rh_trace), max(rh_trace)))
st.metric("CO2 range", "[%.0f, %.0f] ppm" % (min(C_trace), max(C_trace)))

fig, ax = plt.subplots(4, 1, figsize=(10, 11))
fig.patch.set_facecolor("#F7FAF3")  # explicit light figure (theme never touches mpl)
for _a in ax:
    _a.set_facecolor("#FFFFFF")  # explicit light axes, default C-series data colors
    _a.tick_params(colors="#263023")
ax[0].plot(hours, T_trace, label="inside T")
ax[0].plot(hours, T_out_hr, label="outdoor T", linestyle="--")
ax[0].set_ylabel("Temperature (degC)")
ax[0].legend()
ax[0].grid(alpha=0.3)
ax[1].plot(hours, w_trace, color="C2")
ax[1].plot(hours, w_out_hr, color="C3", linestyle="--")
ax[1].set_ylabel("Abs. humidity (g/kg)")
ax[1].grid(alpha=0.3)
ax[2].plot(hours, rh_trace, color="C4")
ax[2].set_ylabel("RH (%)")
ax[2].grid(alpha=0.3)
ax[3].plot(hours, C_trace, color="C5")
ax[3].set_xlabel("hour of day")
ax[3].set_ylabel("CO2 (ppm)")
ax[3].grid(alpha=0.3)
fig.suptitle("Simulated greenhouse plant - 24h open-loop (slider duties)")
fig.tight_layout()
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="model_sim_chart.png", mime="image/png")
st.pyplot(fig)

with st.expander("Provenance"):
    st.write("Plant: src/greenhouse_model.py step_co2 wrapper (thermal core "
             "is step() verbatim; CO2 accumulates by valve, flushes by vent). "
             "Weather: weather/weather_profile.csv for seed 7 (frozen), "
             "ephemeral profiles otherwise. "
             "Scoreboard: results/comparison.csv (8 rows, frozen). "
             "Seeds 7/21, weights 1.0/1.0/0.01.")
