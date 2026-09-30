"""Plant House page — 3D greenhouse with live crop-health readout.

Sliders pick setpoints + controller + weather seed; the real closed-loop
sim (src/metrics.py run_closed_loop) runs headless. House-mean climate
maps to per-plant health with an illustrative vent-to-wall gradient, and
an hour slider scrubs growth through the 24 h day.

Run:  python -m streamlit run dashboard/app.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import plotly.graph_objects as go

import streamlit as st

from src.onoff_controller import onoff_step
from src.pid_controller import pid_step
from src.fuzzy_controller import fuzzy_step
from src.ga_fuzzy_controller import ga_fuzzy_step
from src.metrics import run_closed_loop
from dashboard.helpers import DISPLAY, load_kpi_row, ephemeral_weather_path

STEPS = {"onoff": onoff_step, "pid": pid_step,
         "fuzzy": fuzzy_step, "ga_fuzzy": ga_fuzzy_step}


@st.cache_data
def cached_weather_path(seed):
    """Seed-7 resolves to the frozen file; every other seed is ephemeral."""
    if seed == 7:
        return "weather/weather_profile.csv"
    return ephemeral_weather_path(seed)


@st.cache_data
def cached_closed_loop(controller_key, T_sp, RH_sp, seed):
    """24 h closed loop -> (T_hist, RH_hist) via the real src/ engine."""
    T_hist, RH_hist, _ = run_closed_loop(
        STEPS[controller_key], cached_weather_path(seed),
        T_sp=T_sp, RH_sp=RH_sp)
    return T_hist, RH_hist


def plant_healths(Tmean, RHmean, T_sp, RH_sp, xs, L):
    """Per-plant health: house-mean climate + vent-to-wall gradient."""
    # ponytail: illustrative +/-1 C linear gradient, not simulated CFD
    offs = (np.asarray(xs, dtype=float) / L - 0.5) * 2.0
    h = 1.0 - np.abs(Tmean + offs - T_sp) / 10.0 \
        - abs(float(RHmean) - float(RH_sp)) / 40.0
    return [float(min(1.0, max(0.0, v))) for v in h]


def greenhouse_figure(healths, hour):
    """Wireframe house + 3x4 grid; height/colour per plant, growth by hour."""
    # ponytail: growth is a linear day-fraction scale, not a growth model
    growth = 0.25 + 0.75 * (int(hour) / 24.0)
    L, W, H = 10.0, 6.0, 3.0
    corners = [(x, y, z) for x in (0, L) for y in (0, W) for z in (0, H)]
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (4, 5), (4, 6), (5, 7), (6, 7),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    ex, ey, ez = [], [], []
    for a, b in edges:
        ex += [corners[a][0], corners[b][0], None]
        ey += [corners[a][1], corners[b][1], None]
        ez += [corners[a][2], corners[b][2], None]
    fig = go.Figure(go.Scatter3d(x=ex, y=ey, z=ez, mode="lines",
                                 line=dict(color="#2E7D32", width=4),
                                 name="house"))
    xs = np.linspace(1.5, L - 1.5, 4)
    ys = np.linspace(1.2, W - 1.2, 3)
    green = np.array([46, 125, 50])
    brown = np.array([121, 85, 72])
    sx, sy, sz, cx, cy, cz, csizes, ccolors = ([] for _ in range(8))
    for x in xs:
        for y in ys:
            h = healths[len(cx)]
            stem = (0.6 + 1.6 * h) * growth
            sx += [x, x, None]
            sy += [y, y, None]
            sz += [0.0, stem, None]
            cx.append(x)
            cy.append(y)
            cz.append(stem + 0.15)
            csizes.append(8 + 14 * h)
            rgb = (brown + (green - brown) * h).astype(int)
            ccolors.append("rgb(%d,%d,%d)" % tuple(rgb))
    fig.add_trace(go.Scatter3d(x=sx, y=sy, z=sz, mode="lines",
                               line=dict(color="#33691E", width=5),
                               name="stems"))
    fig.add_trace(go.Scatter3d(x=cx, y=cy, z=cz, mode="markers",
                               marker=dict(size=csizes, color=ccolors),
                               name="canopy"))
    fig.update_layout(scene=dict(aspectmode="manual",
                                 aspectratio=dict(x=10 / 3.0, y=6 / 3.0, z=1),
                                 xaxis=dict(visible=False),
                                 yaxis=dict(visible=False),
                                 zaxis=dict(visible=False)),
                      margin=dict(l=0, r=0, t=30, b=0),
                      title="Greenhouse crop — hour %d, mean health %.2f"
                            % (int(hour), float(np.mean(healths))),
                      showlegend=False)
    return fig


st.title("Plant House — 3D crop health")

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

T_sp = st.slider("temperature setpoint", 18.0, 30.0, 25.0, 0.5)
RH_sp = st.slider("humidity setpoint", 50.0, 90.0, 70.0, 1.0)
controller = st.selectbox("controller", list(DISPLAY), index=3,
                          format_func=lambda k: DISPLAY[k])
seed = st.slider("weather seed", 1, 50, 7, 1)
hour = st.slider("hour of day", 0, 23, 12, 1)

T_hist, RH_hist = cached_closed_loop(controller, T_sp, RH_sp, seed)
Tmean = float(np.mean(T_hist[-360:]))
RHmean = float(np.mean(RH_hist[-360:]))
grid_x = [x for x in np.linspace(1.5, 8.5, 4) for _ in range(3)]
healths = plant_healths(Tmean, RHmean, T_sp, RH_sp, grid_x, 10.0)
st.metric("mean crop health", "%.2f" % float(np.mean(healths)),
          "inside [%.1f, %.1f] C, [%.0f, %.0f] %%RH"
          % (min(T_hist), max(T_hist), min(RH_hist), max(RH_hist)))
st.plotly_chart(greenhouse_figure(healths, hour), use_container_width=True)

with st.expander("Provenance"):
    st.write("Climate: src/metrics.py run_closed_loop (same engine as the "
             "Controllers page). Health: house-mean |T-T_sp| + |RH-RH_sp| "
             "over the last 6 h mapped to 0..1, plus an illustrative "
             "+/-1 C vent-to-wall gradient and a linear day-fraction growth "
             "scale (display heuristics, not agronomy/CFD). "
             "Weather: weather/weather_profile.csv for seed 7 (frozen), "
             "synthetic otherwise.")
