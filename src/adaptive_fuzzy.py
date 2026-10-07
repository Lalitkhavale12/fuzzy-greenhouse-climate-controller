"""Supervisory adaptive fuzzy controller (FUZZ-07).

Wraps fuzzy_step: the fixed 5x5 Mamdani core drives direction while a
supervisory T-loop gain gT stretches or relaxes heater/cooler/vent duties.
gT adapts on the EMA of |eT| (up when persistent error > 1 C, down when
settled < 0.25 C, clamped to [0.5, 2.0]). Gains live in the caller-owned
state dict next to the fuzzy accumulators, so the engine stays pure and
FUZZY_MFS is never mutated. Call protocol matches run_closed_loop.
"""

import numpy as np

from src.fuzzy_controller import FUZZY_MFS, fuzzy_step
from src.sensors import sense_plant, tracking_errors

_T_KEYS = ("heater", "fan_cooler", "vent")


def adaptive_fuzzy_step(T_C: float, rh_pct: float, T_sp: float = 25.0,
                        RH_sp: float = 70.0, state: dict | None = None,
                        dt: float = 60.0, mfs: dict = FUZZY_MFS,
                        eta: float = 0.02) -> tuple[dict, dict]:
    """Fuzzy step with EMA-error-driven output gain. state adds gT/aT."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    assert np.isfinite(eta) and eta > 0
    st = ({'pT': None, 'pH': None, 'uT': 0.0, 'uH': 0.0,
           'gT': 1.0, 'aT': 0.0, 'sens': {'pT': None, 'pH': None}}
          if state is None else state)
    for k in ('pT', 'pH', 'uT', 'uH', 'gT', 'aT', 'sens'):
        assert k in st, f"state missing key {k!r}"
    reading = sense_plant(T_C, rh_pct)  # validated sensor acquisition
    eT, _eH, _dT, _dH = tracking_errors(
        reading["T_C"], reading["rh_pct"], T_sp, RH_sp, st['sens'], dt)
    st['aT'] = 0.98 * float(st['aT']) + 0.02 * abs(eT)
    if st['aT'] > 1.0:
        st['gT'] = min(2.0, float(st['gT']) + eta)
    elif st['aT'] < 0.25:
        st['gT'] = max(0.5, float(st['gT']) - eta)
    inner = {'pT': st['pT'], 'pH': st['pH'],
             'uT': st['uT'], 'uH': st['uH']}
    act, inner2 = fuzzy_step(T_C, rh_pct, T_sp, RH_sp, inner, dt, mfs)
    for k in ('pT', 'pH', 'uT', 'uH'):
        st[k] = inner2[k]
    g = float(st['gT'])
    out = {k: (float(np.clip(v * g, 0.0, 1.0)) if k in _T_KEYS else v)
           for k, v in act.items()}
    return out, st
