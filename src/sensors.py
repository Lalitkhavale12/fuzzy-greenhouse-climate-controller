"""Sensor acquisition + tracking-error computation (Claim 1).

Receives internal temperature and relative-humidity measurements, validates
them fail-fast, and computes respective errors and rates of change of error
against setpoints. Pure functions; the caller owns the rate state dict
({'pT', 'pH'}), mirroring the controller state convention.
"""

import numpy as np


def sense_plant(T_C: float, rh_pct: float) -> dict:
    """Validate raw measurements -> reading dict (finite asserts)."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    return {"T_C": float(T_C), "rh_pct": float(rh_pct)}


def tracking_errors(T_C: float, rh_pct: float, T_sp: float = 25.0,
                    RH_sp: float = 70.0, state: dict | None = None,
                    dt: float = 60.0) -> tuple[float, float, float, float]:
    """Errors + per-minute error rates; state carries previous errors."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    st = {'pT': None, 'pH': None} if state is None else state
    for k in ('pT', 'pH'):
        assert k in st, f"sensor state missing key {k!r}"
    eT = float(T_sp) - float(T_C)
    eH = float(RH_sp) - float(rh_pct)
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / (dt / 60.0)
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / (dt / 60.0)
    st['pT'], st['pH'] = eT, eH
    return eT, eH, float(dT), float(dH)
