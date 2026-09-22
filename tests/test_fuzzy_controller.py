"""Plain-assert sanity suite for the velocity-form fuzzy controller (FUZZ-01..06).

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_fuzzy_controller.py
"""


def _run_closed_loop(np, controller_step, n=1440, T_sp=25.0, RH_sp=70.0):
    from src.greenhouse_model import (step, load_weather_profile,
                                      daytime_solar, params,
                                      relative_humidity, wsat_g_per_kg)
    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    hours = np.arange(0, n) / 60.0
    T_out_hr = np.interp(hours, t_min, T_out)
    w_out_hr = np.interp(hours, t_min, w_out)
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st = None
    T_hist, RH_hist, U_hist = [], [], []
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = controller_step(T, rh, T_sp, RH_sp, st)
        wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, wx, T, w)
        T_hist.append(T)
        RH_hist.append(rh)
        U_hist.append(act)
    return T_hist, RH_hist, U_hist


def test_fuzzy_signs():
    from src.fuzzy_controller import fuzzy_step

    st = None  # cold plant charges heater within a few accumulated steps
    for _ in range(5):
        act, st = fuzzy_step(20.0, 70.0, 25.0, 70.0, st)
    assert act["heater"] > 0.0 and act["fan_cooler"] == 0.0, act

    st = None  # hot plant drives fan/cooler
    for _ in range(5):
        act, st = fuzzy_step(30.0, 70.0, 25.0, 70.0, st)
    assert act["fan_cooler"] > 0.0 and act["heater"] == 0.0, act

    st = None  # dry air drives fogger
    for _ in range(5):
        act, st = fuzzy_step(25.0, 50.0, 25.0, 70.0, st)
    assert act["fogger"] > 0.0, act

    act, _ = fuzzy_step(25.0, 70.0, 25.0, 70.0, None)
    assert all(abs(d) < 0.05 for d in act.values()), act  # near zero (fogger ~0.015 structural)


def test_error_rate_live():
    from src.fuzzy_controller import fuzzy_step, infer, FUZZY_MFS

    m = FUZZY_MFS
    flat = infer(2.0, 0.0, m["eT"]["centers"], m["eT"]["widths"],
                 m["deT"]["centers"], m["deT"]["widths"],
                 m["du"]["centers"], m["du"]["widths"], -1.0, 1.0)
    ramp = infer(2.0, 0.5, m["eT"]["centers"], m["eT"]["widths"],
                 m["deT"]["centers"], m["deT"]["widths"],
                 m["du"]["centers"], m["du"]["widths"], -1.0, 1.0)
    assert flat != ramp, (flat, ramp)  # de path not dead (Pitfall 3 guard)

    # same fixed error through fuzzy_step: ramped history vs flat history differ
    st_flat = {"pT": 2.0, "pH": 0.0, "uT": 0.0, "uH": 0.0}
    st_ramp = {"pT": 1.5, "pH": 0.0, "uT": 0.0, "uH": 0.0}
    a, _ = fuzzy_step(23.0, 70.0, 25.0, 70.0, st_flat)   # dT = 0.0 C/min
    b, _ = fuzzy_step(23.0, 70.0, 25.0, 70.0, st_ramp)   # dT = +0.5 C/min
    assert a["heater"] != b["heater"], (a, b)


def test_membership_functions():
    from src.fuzzy_controller import tri, FUZZY_MFS, LABELS

    assert LABELS == ("NB", "NS", "ZO", "PS", "PB")
    assert tri(0.0, 0.0, 2.0) == 1.0            # 1.0 at center
    assert tri(2.0, 0.0, 2.0) == 0.0            # 0.0 at one half-width
    assert tri(5.0, 0.0, 2.0) == 0.0            # 0.0 beyond
    assert set(FUZZY_MFS) == {"eT", "deT", "du", "eH", "deH", "dv"}
    for k, v in FUZZY_MFS.items():
        assert len(v["centers"]) == 5 and len(v["widths"]) == 5, k
    # probe universes
    assert FUZZY_MFS["eT"]["centers"][0] == -4.0 and FUZZY_MFS["eT"]["centers"][-1] == 4.0
    assert FUZZY_MFS["deT"]["centers"][-1] == 0.5
    assert FUZZY_MFS["eH"]["centers"][0] == -30.0
    assert FUZZY_MFS["deH"]["centers"][-1] == 6.0
    # 50%-overlap: interior point fires exactly 2 MFs
    n_fire = sum(tri(1.0, c, w) > 0.0
                 for c, w in zip(FUZZY_MFS["eT"]["centers"], FUZZY_MFS["eT"]["widths"]))
    assert n_fire == 2, n_fire


def test_rule_table():
    from src.fuzzy_controller import RULES

    assert RULES.shape == (5, 5)
    assert RULES.min() >= 0 and RULES.max() <= 4
    assert RULES[2, 2] == 2                                  # equilibrium ZO
    assert RULES[:, 2].tolist() == [0, 1, 2, 3, 4]           # ZO-rate column
    assert RULES[2, :].tolist() == [0, 1, 2, 3, 4]           # damping row


def test_output_mapping():
    from src.fuzzy_controller import fuzzy_step

    st = None
    for T in ([20.0] * 5 + [30.0] * 5 + [25.0] * 5 + [22.0] * 5 + [28.0] * 5):
        act, st = fuzzy_step(T, 70.0, 25.0, 70.0, st)
        assert list(act.keys()) == ["heater", "fan_cooler", "fogger", "vent"], act
        assert all(0.0 <= d <= 1.0 for d in act.values()), act
        assert not (act["heater"] > 0.0 and act["fan_cooler"] > 0.0), (T, act)
        assert act["vent"] == act["fan_cooler"], act  # vent mirrors cooling


def test_centroid_defuzz():
    from src.fuzzy_controller import infer, FUZZY_MFS

    m = FUZZY_MFS

    def du(e, de):
        return infer(e, de, m["eT"]["centers"], m["eT"]["widths"],
                     m["deT"]["centers"], m["deT"]["widths"],
                     m["du"]["centers"], m["du"]["widths"], -1.0, 1.0)

    assert du(5.0, 0.0) > 0.05, du(5.0, 0.0)     # strong heat: >half of +-0.1 authority
    assert du(-5.0, 0.0) < -0.05, du(-5.0, 0.0)  # strong cool when far hot
    assert abs(du(0.0, 0.0)) < 1e-9             # equilibrium holds
    assert du(2.0, 0.0) == du(2.0, 0.0)         # bit-identical reruns
    assert du(-3.0, 0.25) == du(-3.0, 0.25)     # (IN-02: no duplicated line)


def test_fogger_ramps_down():
    # WR-01: dv must go negative on soak so the fogger can ramp DOWN, and the
    # equilibrium dv must be exactly 0.0 (full ZO triangle) — not a ratchet.
    from src.fuzzy_controller import fuzzy_step

    st = None
    for _ in range(30):
        act, st = fuzzy_step(25.0, 50.0, 25.0, 70.0, st)   # dry: charge fogger
    high = act["fogger"]
    assert high > 0.0, act
    for _ in range(60):
        act, st = fuzzy_step(25.0, 95.0, 25.0, 70.0, st)   # soaked: dry back
    assert act["fogger"] < high, (high, act)
    st = None
    for _ in range(120):
        act, st = fuzzy_step(25.0, 70.0, 25.0, 70.0, st)   # equilibrium: hold
    assert act["fogger"] < 0.05, act


def _fuzzy_unguarded(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0):
    import numpy as np
    from src.fuzzy_controller import infer, FUZZY_MFS
    st = ({'pT': None, 'pH': None, 'uT': 0.0, 'uH': 0.0}
          if state is None else state)
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / (dt / 60.0)
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / (dt / 60.0)
    st['pT'], st['pH'] = eT, eH
    m = FUZZY_MFS
    du = infer(eT, dT, m["eT"]["centers"], m["eT"]["widths"],
               m["deT"]["centers"], m["deT"]["widths"],
               m["du"]["centers"], m["du"]["widths"], -1.0, 1.0)
    dv = infer(eH, dH, m["eH"]["centers"], m["eH"]["widths"],
               m["deH"]["centers"], m["deH"]["widths"],
               m["dv"]["centers"], m["dv"]["widths"], 0.0, 1.0)
    st['uT'] += du  # no freeze, no clip: unbounded windup (PID _pid_unguarded analog)
    st['uH'] += dv
    u = float(np.clip(st['uT'], -1.0, 1.0))  # clip only at emission for step()
    v = float(np.clip(st['uH'], 0.0, 1.0))
    heat, cool = (u, 0.0) if u > 0 else (0.0, -u)
    return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)


def _run_saturating_script(np, fn, nights=400, days=200):
    from src.greenhouse_model import step, relative_humidity, wsat_g_per_kg
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st, iae = None, 0.0
    script = ([(10.0, 5.0, 0.0)] * nights       # cold night: heater saturates
              + [(30.0, 8.0, 100.0)] * days)    # hot day: stale integral hurts
    for (T_out, w_out, sol) in script:
        rh = relative_humidity(w, T)
        act, st = fn(T, rh, 25.0, 70.0, st)
        T, w, rh = step(60.0, act, (T_out, w_out, sol), T, w)
        iae += abs(T - 25.0) / 60.0
    return iae


def test_accumulator_antiwindup():
    import numpy as np
    from src.fuzzy_controller import fuzzy_step

    guarded = _run_saturating_script(np, fuzzy_step)
    unguarded = _run_saturating_script(np, _fuzzy_unguarded)
    assert guarded < unguarded, (guarded, unguarded)


def test_closed_loop_24h():
    import numpy as np
    from src.fuzzy_controller import fuzzy_step

    T_hist, RH_hist, U_hist = _run_closed_loop(np, fuzzy_step)
    assert len(T_hist) == 1440
    assert all(np.isfinite(T_hist)) and all(np.isfinite(RH_hist))
    assert min(RH_hist) >= 0.0 and max(RH_hist) <= 100.0
    iae_T = sum(abs(T - 25.0) for T in T_hist) / 60.0
    assert np.isfinite(iae_T) and iae_T < 60.0, f"fuzzy T-IAE {iae_T}"
    print(f"fuzzy T-IAE {iae_T:.2f}")
    for act in U_hist:
        assert list(act.keys()) == ["heater", "fan_cooler", "fogger", "vent"]
        assert all(0.0 <= d <= 1.0 for d in act.values())
        assert not (act["heater"] > 0.0 and act["fan_cooler"] > 0.0)
    tail = [T - 25.0 for T in T_hist[-360:]]  # no sustained oscillation
    crossings = sum(1 for a, b in zip(tail, tail[1:]) if (a < 0) != (b < 0))
    assert crossings < 12, crossings

    a, _ = fuzzy_step(24.0, 65.0, 25.0, 70.0, None)
    b, _ = fuzzy_step(24.0, 65.0, 22.0, 60.0, None)
    assert a != b  # setpoints are live args
    r1, _ = fuzzy_step(24.0, 65.0, 25.0, 70.0, None)
    r2, _ = fuzzy_step(24.0, 65.0, 25.0, 70.0, None)
    assert r1 == r2  # fresh-state determinism
    run1 = _run_closed_loop(np, fuzzy_step, n=120)
    run2 = _run_closed_loop(np, fuzzy_step, n=120)
    assert run1[0] == run2[0] and run1[1] == run2[1]  # two runs bit-identical
    try:
        fuzzy_step(float("nan"), 70.0, 25.0, 70.0, None)
        raise SystemExit("NaN T_C did not raise")
    except AssertionError:
        pass


if __name__ == "__main__":
    import sys, os
    # "python tests/test_fuzzy_controller.py" puts tests/ on sys.path, not the
    # repo root — prepend the root so the in-body `from src import ...` works
    # both standalone and under pytest (which adds rootdir itself).
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    failures = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:
                failures.append(name)
                print(f"FAIL {name}: {exc!r}")
    if failures:
        print(f"{len(failures)} check(s) failed: {failures}")
        sys.exit(1)
    print("all checks passed")
