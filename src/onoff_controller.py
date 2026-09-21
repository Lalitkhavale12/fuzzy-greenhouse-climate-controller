"""Hysteresis on/off baseline controller (BASE-01, D-01/D-02/D-04).

Per-loop relay with asymmetric release: on at the wide band edge, off at the
narrow release, strict inequalities so exact band equality holds prior latch
state. T-loop drives heater + fan_cooler + vent (vent mirrors cooling bit),
RH-loop drives fogger only; loops stay independent (D-03).

Pure and stateless: caller owns the state dict, passes it in/out; state=None
means a fresh latch dict (never a mutable default).
"""

import numpy as np


def onoff_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None,
               band_T=0.5, band_RH=3.0):
    """Hysteresis on/off. state = {'heat': bool, 'cool': bool, 'fog': bool}."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(band_T) and np.isfinite(band_RH)
    st = {'heat': False, 'cool': False, 'fog': False} if state is None else state
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    if eT > band_T:
        st['heat'] = True       # too cold -> full heat
    elif eT < -0.2:
        st['heat'] = False      # slight overshoot releases
    if eT < -band_T:
        st['cool'] = True       # too hot -> full cool + vent
    elif eT > 0.2:
        st['cool'] = False
    if eH > band_RH:
        st['fog'] = True        # too dry -> full fog
    elif eH < -1.0:
        st['fog'] = False
    out = {'heater': 1.0 if st['heat'] else 0.0,
           'fan_cooler': 1.0 if st['cool'] else 0.0,
           'fogger': 1.0 if st['fog'] else 0.0,
           'vent': 1.0 if st['cool'] else 0.0}   # D-01: vent follows T
    return out, st
