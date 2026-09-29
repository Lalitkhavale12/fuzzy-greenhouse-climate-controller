"""Model Sim page — slider-driven open-loop plant + weather explorer (D-01).

Fixed duties from sliders replace the 01-notebook schedule(h); the loop
body and 3-panel figure are otherwise verbatim from
notebooks/01_greenhouse_model.ipynb cells 2-4 (Agg line dropped).

Run:  python -m streamlit run dashboard/app.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import matplotlib.pyplot as plt

import streamlit as st

from src.greenhouse_model import step, load_weather_profile, daytime_solar, params
from src.weather_profile_generator import generate_weather_profile
from dashboard.helpers import fig_to_png_bytes

T_INIT_C, W_INIT = 29.28, 20.0  # probe-verified baseline initial condition


@st.cache_data
def cached_weather(seed):
    """Seed-7 resolves to the frozen file; every other seed is ephemeral."""
    if seed == 7:
        path = "weather/weather_profile.csv"
    else:
        path = os.path.join(tempfile.mkdtemp(), "seed_%d.csv" % seed)
        generate_weather_profile(path, seed=seed)
    return load_weather_profile(path)


def run_open_loop(heater, fan, fogger, vent, seed):
    """Open-loop 24 h trace -> (hours, T_trace, w_trace, rh_trace, T_out_hr, w_out_hr)."""
    t_min, T_out, w_out = cached_weather(seed)
    hours = np.arange(0, 1440) / 60.0  # dt = 60 s -> one step per minute
    T_out_hr = np.interp(hours, t_min, T_out)
    w_out_hr = np.interp(hours, t_min, w_out)
    act = {"heater": heater, "fan_cooler": fan, "fogger": fogger, "vent": vent}
    T, w = T_INIT_C, W_INIT  # probe-verified baseline initial condition
    T_trace, w_trace, rh_trace = [], [], []
    for i, h in enumerate(hours):
        ws = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, ws, T, w)
        T_trace.append(T)
        w_trace.append(w)
        rh_trace.append(rh)
    return hours, T_trace, w_trace, rh_trace, T_out_hr, w_out_hr


st.title("Model Sim — open-loop plant + weather")
heater = st.slider("heater duty", 0.0, 1.0, 0.8, 0.05)
fan = st.slider("fan/cooler duty", 0.0, 1.0, 0.0, 0.05)
fogger = st.slider("fogger duty", 0.0, 1.0, 0.5, 0.05)
vent = st.slider("vent duty", 0.0, 1.0, 0.25, 0.05)
seed = st.slider("weather seed", 1, 50, 7, 1)

hours, T_trace, w_trace, rh_trace, T_out_hr, w_out_hr = run_open_loop(
    heater, fan, fogger, vent, seed)
st.metric("inside T range", "[%.2f, %.2f] degC" % (min(T_trace), max(T_trace)))
st.metric("RH range", "[%.1f, %.1f] %%" % (min(rh_trace), max(rh_trace)))

fig, ax = plt.subplots(3, 1, figsize=(10, 9))
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
ax[2].set_xlabel("hour of day")
ax[2].set_ylabel("RH (%)")
ax[2].grid(alpha=0.3)
fig.suptitle("Simulated greenhouse plant - 24h open-loop (slider duties)")
fig.tight_layout()
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="model_sim_chart.png", mime="image/png")
st.pyplot(fig)
