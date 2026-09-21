"""Dual-loop positional PID baseline controller (BASE-02, D-05).

T-loop output u in [-1, 1] splits by sign (positive -> heater, negative
magnitude -> fan_cooler + vent, never both); RH-loop output v in [0, 1]
drives fogger only (one-sided). Conditional-integration anti-windup freezes
each integrator when its output is saturated pushing further. Kd defaults
to 0 for both loops (lag-dominated, noisy RH).

Pure and stateless: caller owns the state dict; state=None means fresh
{'iT', 'pT', 'iH', 'pH'}. GAINS is module-level read-only (never mutated).
"""

import numpy as np

GAINS = {'Kp_T': 0.3, 'Ki_T': 0.03, 'Kd_T': 0.0,   # per degC
         'Kp_H': 0.03, 'Ki_H': 0.004, 'Kd_H': 0.0}  # per %RH


def pid_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, gains=GAINS):
    """Positional dual-loop PID. state = {'iT', 'pT', 'iH', 'pH'}."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    st = {'iT': 0.0, 'pT': None, 'iH': 0.0, 'pH': None} if state is None else state
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / dt
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / dt
    st['pT'], st['pH'] = eT, eH
    u_raw = gains['Kp_T'] * eT + gains['Ki_T'] * st['iT'] + gains['Kd_T'] * dT
    # conditional integration: freeze T integrator when saturated pushing further
    if not ((u_raw > 1.0 and eT > 0) or (u_raw < -1.0 and eT < 0)):
        st['iT'] += eT * dt
    u = float(np.clip(gains['Kp_T'] * eT + gains['Ki_T'] * st['iT'] + gains['Kd_T'] * dT, -1.0, 1.0))
    v_raw = gains['Kp_H'] * eH + gains['Ki_H'] * st['iH']
    if not (v_raw > 1.0 and eH > 0):
        st['iH'] += eH * dt
    v = float(np.clip(gains['Kp_H'] * eH + gains['Ki_H'] * st['iH'], 0.0, 1.0))
    heat, cool = (u, 0.0) if u > 0 else (0.0, -u)   # split-range, never both
    return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)
