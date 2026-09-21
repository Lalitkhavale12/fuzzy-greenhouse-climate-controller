"""Plain-assert sanity suite for the on/off + PID baseline controllers (BASE-01..03).

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_baseline_controllers.py
"""


def _run_closed_loop(np, controller_step, n=1440):
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
        act, st = controller_step(T, rh, 25.0, 70.0, st)
        wx = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, wx, T, w)
        T_hist.append(T)
        RH_hist.append(rh)
        U_hist.append(act)
    return T_hist, RH_hist, U_hist


def test_onoff_hysteresis():
    from src.onoff_controller import onoff_step

    act, _ = onoff_step(25.0, 70.0, 25.0, 70.0, None)
    assert act == {"heater": 0.0, "fan_cooler": 0.0, "fogger": 0.0, "vent": 0.0}

    act, st = onoff_step(20.0, 70.0, 25.0, 70.0, None)
    assert act["heater"] == 1.0 and act["fan_cooler"] == 0.0

    act, st = onoff_step(24.8, 70.0, 25.0, 70.0, st)
    assert act["heater"] == 1.0                     # inside band holds latch

    act, st = onoff_step(25.0, 70.0, 25.0, 70.0, st)
    assert act["heater"] == 1.0                     # exact edge holds, no toggle

    act, st = onoff_step(25.5, 70.0, 25.0, 70.0, st)
    assert act["heater"] == 0.0                     # narrow release drops latch

    act, _ = onoff_step(26.0, 70.0, 25.0, 70.0, None)
    assert act["fan_cooler"] == 1.0 and act["vent"] == 1.0
    assert act["heater"] == 0.0


def test_onoff_mutual_exclusion():
    from src.onoff_controller import onoff_step

    st = None
    for T in ([20.0] * 5 + [24.8] * 5 + [25.5] * 5 + [26.0] * 5
              + [25.0] * 5 + [24.0] * 5 + [26.5] * 5 + [20.0] * 5):
        act, st = onoff_step(T, 70.0, 25.0, 70.0, st)
        assert not (act["heater"] > 0.0 and act["fan_cooler"] > 0.0), T


def test_pid_signs():
    from src.pid_controller import pid_step

    act, _ = pid_step(20.0, 70.0, 25.0, 70.0, None)
    assert act["heater"] > 0.0 and act["fan_cooler"] == 0.0

    act, _ = pid_step(30.0, 70.0, 25.0, 70.0, None)
    assert act["fan_cooler"] > 0.0 and act["heater"] == 0.0

    act, _ = pid_step(25.0, 50.0, 25.0, 70.0, None)
    assert act["fogger"] > 0.0

    act, _ = pid_step(25.0, 70.0, 25.0, 70.0, None)
    assert all(abs(d) < 1e-9 for d in act.values())


def _pid_unguarded(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None,
                   dt=60.0, gains=None):
    import numpy as np
    from src.pid_controller import GAINS as _G
    gains = _G if gains is None else gains
    st = ({'iT': 0.0, 'pT': None, 'iH': 0.0, 'pH': None}
          if state is None else state)
    eT, eH = T_sp - T_C, RH_sp - rh_pct
    dT = 0.0 if st['pT'] is None else (eT - st['pT']) / dt
    dH = 0.0 if st['pH'] is None else (eH - st['pH']) / dt
    st['pT'], st['pH'] = eT, eH
    st['iT'] += eT * dt                             # no freeze: windup allowed
    st['iH'] += eH * dt
    u = float(np.clip(gains['Kp_T'] * eT + gains['Ki_T'] * st['iT']
                      + gains['Kd_T'] * dT, -1.0, 1.0))
    v = float(np.clip(gains['Kp_H'] * eH + gains['Ki_H'] * st['iH'],
                      0.0, 1.0))
    heat, cool = (u, 0.0) if u > 0 else (0.0, -u)
    return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool},
            st)


def _run_saturating_script(np, fn, gains=None, nights=400, days=200):
    from src.greenhouse_model import step, relative_humidity, wsat_g_per_kg
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st, iae = None, 0.0
    script = ([(10.0, 5.0, 0.0)] * nights       # cold night: heater saturates
              + [(30.0, 8.0, 100.0)] * days)    # hot day: stale integral hurts
    for (T_out, w_out, sol) in script:
        rh = relative_humidity(w, T)
        kw = {} if gains is None else {'gains': gains}
        act, st = fn(T, rh, 25.0, 70.0, st, **kw)
        T, w, rh = step(60.0, act, (T_out, w_out, sol), T, w)
        iae += abs(T - 25.0) / 60.0
    return iae


def test_pid_antiwindup_improves():
    import numpy as np
    from src.pid_controller import pid_step

    guarded = _run_saturating_script(np, pid_step)
    unguarded = _run_saturating_script(np, _pid_unguarded)
    assert guarded < unguarded, (guarded, unguarded)


def test_pid_integral_required():
    import numpy as np
    from src.pid_controller import pid_step, GAINS

    p_only = dict(GAINS, Ki_T=0.0, Ki_H=0.0)
    iae_pi = _run_saturating_script(np, pid_step)
    iae_p = _run_saturating_script(np, pid_step, gains=p_only)
    assert iae_p > 3.0 * iae_pi, (iae_p, iae_pi)   # droop dominates without I


def test_controller_signatures():
    import numpy as np
    from src.onoff_controller import onoff_step
    from src.pid_controller import pid_step

    for fn in (onoff_step, pid_step):
        a, _ = fn(25.0, 70.0, 25.0, 70.0, None)
        b, _ = fn(25.0, 70.0, 22.0, 60.0, None)
        assert a != b                               # setpoints are live args
        assert list(a.keys()) == ["heater", "fan_cooler", "fogger", "vent"]
        assert all(0.0 <= d <= 1.0 for d in a.values())
        r1, _ = fn(24.0, 65.0, 25.0, 70.0, None)
        r2, _ = fn(24.0, 65.0, 25.0, 70.0, None)
        assert r1 == r2                              # fresh-state determinism

    run1 = _run_closed_loop(np, onoff_step, n=120)
    run2 = _run_closed_loop(np, onoff_step, n=120)
    assert run1[0] == run2[0] and run1[1] == run2[1]  # two runs bit-identical

    for fn in (onoff_step, pid_step):
        try:
            fn(float("nan"), 70.0, 25.0, 70.0, None)
            raise SystemExit("NaN T_C did not raise")
        except AssertionError:
            pass


def test_closed_loop_24h():
    import numpy as np
    from src.onoff_controller import onoff_step
    from src.pid_controller import pid_step

    for name, fn in (("onoff", onoff_step), ("pid", pid_step)):
        T_hist, RH_hist, U_hist = _run_closed_loop(np, fn)
        assert len(T_hist) == 1440
        assert all(np.isfinite(T_hist)) and all(np.isfinite(RH_hist))
        assert min(RH_hist) >= 0.0 and max(RH_hist) <= 100.0
        iae_T = sum(abs(T - 25.0) for T in T_hist) / 60.0
        assert np.isfinite(iae_T) and iae_T < 60.0, f"{name} T-IAE {iae_T}"
        for act in U_hist:
            assert list(act.keys()) == ["heater", "fan_cooler", "fogger", "vent"]
            assert all(0.0 <= d <= 1.0 for d in act.values())
            assert not (act["heater"] > 0.0 and act["fan_cooler"] > 0.0)


if __name__ == "__main__":
    import sys, os
    # "python tests/test_baseline_controllers.py" puts tests/ on sys.path, not the
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
