"""Seedable 24h synthetic weather profile generator (D-12, D-10).

Writes (time_min, temp_C, rh_pct) rows at 15-minute resolution — integer
minutes 0..1440 inclusive, 97 rows — to a CSV whose header line is exactly
"time_min,temp_C,rh_pct". Same seed produces a byte-identical file (D-12:
GA reruns must be deterministic). Backbone is a sine day/night cycle with
the temperature peak at t_peak_h and RH anti-correlated (D-11), clipped to
[30, 95]% (D-09). w_out is derived at load time from RH + T, so the model
module never imports from this module (zero coupling).
"""

import numpy as np


def generate_weather_profile(out_path, seed=7, t_mean=20.0, t_amp=6.0,
                             rh_mean=65.0, rh_amp=18.0, t_peak_h=15.0,
                             duration_h=24.0, interval_min=15):
    rng = np.random.default_rng(seed)
    t_min = np.arange(0, int(duration_h*60) + 1, interval_min, dtype=int)  # 0..1440
    t_h   = t_min / 60.0
    phase = 2*np.pi*(t_h - t_peak_h)/24.0
    # cosine so the daily maximum lands exactly at t_peak_h (a sine would peak 6h late)
    T_out = t_mean + t_amp*np.cos(phase) + rng.normal(0, 0.5, t_h.size)     # mild noise
    RH    = np.clip(rh_mean - rh_amp*np.cos(phase) + rng.normal(0, 3.0, t_h.size), 30, 95)  # D-11 anti-correlated
    np.savetxt(out_path, np.column_stack([t_min, T_out, RH]),
               header="time_min,temp_C,rh_pct", comments="", fmt=["%d", "%.2f", "%.2f"])
    return out_path