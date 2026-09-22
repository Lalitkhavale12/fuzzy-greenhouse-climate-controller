"""Dual-loop incremental (velocity-form) Mamdani fuzzy controller (FUZZ-01..06).

T-loop error+rate -> delta u accumulates on [-1, 1], split by sign
(positive -> heater, negative magnitude -> fan_cooler + vent, never both);
RH-loop error+rate -> delta v accumulates on [0, 1] driving fogger only
(one-sided). Conditional-integration anti-windup freezes each accumulator
when its output is saturated pushing further. Both loops share the
MacVicar-Whelan diagonal 5x5 RULES table; centroid defuzzification over a
201-point grid with zero-fire fallback of 0.0.

Pure and stateless: caller owns the state dict; state=None means fresh
{'pT', 'pH', 'uT', 'uH'}. FUZZY_MFS is module-level read-only (never
mutated — Phase 4 GA passes mutated copies as the chromosome).
"""

import numpy as np

LABELS = ("NB", "NS", "ZO", "PS", "PB")

FUZZY_MFS = {
    # T-loop: init error +5 C, midday overshoot ~-1..-4 C; max rate ~0.67 C/min
    "eT":  {"centers": np.array([-4., -2., 0., 2., 4.]),       "widths": np.full(5, 2.0)},
    "deT": {"centers": np.array([-0.5, -0.25, 0., 0.25, 0.5]), "widths": np.full(5, 0.25)},  # C/min
    "du":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},  # duty/step
    # RH-loop: RH pins 60..100 so eH spans [-30,+10]; fogger +2.2 %RH/min at 25 C
    "eH":  {"centers": np.array([-30., -15., 0., 15., 30.]),   "widths": np.full(5, 15.0)},
    "deH": {"centers": np.array([-6., -3., 0., 3., 6.]),       "widths": np.full(5, 3.0)},   # %RH/min
    "dv":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},
}

RULES = np.array([          # cols: de = NB | NS | ZO | PS | PB
    [0, 0, 0, 1, 2],        # row e = NB (far above setpoint / falling fast...)
    [0, 1, 1, 2, 3],        # row e = NS
    [0, 1, 2, 3, 4],        # row e = ZO (pure damping row: output opposes rate)
    [1, 2, 3, 3, 4],        # row e = PS
    [2, 3, 4, 4, 4],        # row e = PB (far below setpoint -> drive hard)
])  # cells index into (NB, NS, ZO, PS, PB)


def tri(x, c, w):
    """Triangular membership in [0,1]. Edge MFs saturate via input clipping in infer()."""
    return float(np.clip(1.0 - abs(float(x) - c) / w, 0.0, 1.0))


def infer(e, de, EC, EW, DC, DW, OC, OW, lo, hi, n=201):
    """Shared Mamdani min-max core with discrete centroid (zero-fire -> 0.0)."""
    mu_e = np.array([tri(np.clip(e, EC[0], EC[-1]), c, w) for c, w in zip(EC, EW)])
    mu_d = np.array([tri(np.clip(de, DC[0], DC[-1]), c, w) for c, w in zip(DC, DW)])
    grid = np.linspace(lo, hi, n)
    agg = np.zeros(n)
    for i in range(5):
        if mu_e[i] == 0.0:
            continue
        for j in range(5):
            f = mu_e[i] if mu_e[i] < mu_d[j] else mu_d[j]  # min implication
            if f > 0.0:
                m = np.clip(1.0 - np.abs(grid - OC[RULES[i, j]]) / OW[RULES[i, j]], 0.0, 1.0)
                np.maximum(agg, np.minimum(f, m), out=agg)  # max aggregation
    s = agg.sum()
    return float(np.sum(grid * agg) / s) if s > 0.0 else 0.0


def fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, mfs=FUZZY_MFS):
    """Incremental dual-loop Mamdani fuzzy. state = {'pT','pH','uT','uH'}."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    st = {'pT': None, 'pH': None, 'uT': 0.0, 'uH': 0.0} if state is None else state
    for k in ('pT', 'pH', 'uT', 'uH'):  # fail loud on partial state (PID WR-02 convention)
        assert k in st, f"state missing key {k!r}"
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / (dt / 60.0)  # C/min
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / (dt / 60.0)  # %RH/min
    st['pT'], st['pH'] = eT, eH
    du = infer(eT, dT, mfs["eT"]["centers"], mfs["eT"]["widths"],
               mfs["deT"]["centers"], mfs["deT"]["widths"],
               mfs["du"]["centers"], mfs["du"]["widths"], -1.0, 1.0)
    dv = infer(eH, dH, mfs["eH"]["centers"], mfs["eH"]["widths"],
               mfs["deH"]["centers"], mfs["deH"]["widths"],
               mfs["dv"]["centers"], mfs["dv"]["widths"], 0.0, 1.0)
    u_new = st['uT'] + du
    if not ((u_new > 1.0 and eT > 0) or (u_new < -1.0 and eT < 0)):  # AW freeze (PID convention)
        st['uT'] = float(np.clip(u_new, -1.0, 1.0))
    v_new = st['uH'] + dv
    if not ((v_new > 1.0 and eH > 0) or (v_new < 0.0 and eH < 0)):
        st['uH'] = float(np.clip(v_new, 0.0, 1.0))
    u, v = st['uT'], st['uH']
    heat, cool = (u, 0.0) if u > 0 else (0.0, -u)  # split-range, never both
    return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)
