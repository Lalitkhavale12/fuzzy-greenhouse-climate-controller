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
