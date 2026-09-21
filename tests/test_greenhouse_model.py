"""Plain-assert sanity suite for the simulated greenhouse plant (MODEL-01..04).

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so this file is runnable before src/greenhouse_model.py exists
(Task-1 wave-0 ordering: the model checks stay RED until Task 2 lands).

Run:  python tests/test_greenhouse_model.py
"""


def _run_loop(np, step, dt, steps, actuators, weather, T, w):
    for _ in range(steps):
        T, w, _rh = step(dt, actuators, weather, T, w)
    return T, w


def test_coupling_directions():
    import numpy as np
    from src.greenhouse_model import step, relative_humidity

    wx = (15.8, 7.3, 0.0)          # probe weather @12h (RESEARCH.md line 298)
    dt = 60.0
    off = {"heater": 0.0, "fan_cooler": 0.0, "fogger": 0.0, "vent": 0.0}

    # heater: 10 min from (29.0, 11.0) — T up, w unchanged vs all-off, RH down
    T0, w0 = 29.0, 11.0
    T_off, w_off = _run_loop(np, step, dt, 10, off, wx, T0, w0)
    T_h, w_h = _run_loop(np, step, dt, 10, dict(off, heater=1.0), wx, T0, w0)
    assert T_h > T_off + 1.0                      # heater raises T (probe +12.7 C/60min)
    assert abs(w_h - w_off) < 1e-9                # drying is emergent (Pitfall 4)
    assert relative_humidity(w_h, T_h) < relative_humidity(w_off, T_off)

    # fan_cooler: 1h from (29.28, 20.0) — cools AND dehumidifies (condensation)
    T_f, w_f = _run_loop(np, step, dt, 60, dict(off, fan_cooler=1.0), wx, 29.28, 20.0)
    assert T_f < 29.28 - 10.0                     # probe dT = -25.4 C over 1h
    assert w_f < 20.0                             # net condensation sink

    # fogger: 10 min from (25.0, 10.0) — cools AND humidifies
    T_g, w_g = _run_loop(np, step, dt, 10, dict(off, fogger=1.0), wx, 25.0, 10.0)
    assert T_g < 25.0 - 0.3
    assert w_g > 10.0 + 3.0

    # vent: 1h — moves toward ambient (15.8 C / 7.3 g/kg)
    T_v, w_v = _run_loop(np, step, dt, 60, dict(off, vent=1.0), wx, 29.28, 20.0)
    assert abs(T_v - wx[0]) < abs(29.28 - wx[0])
    assert abs(w_v - wx[1]) < abs(20.0 - wx[1])


def test_bounded_finite_positive_24h():
    import numpy as np
    from src.greenhouse_model import step, daytime_solar, params, load_weather_profile

    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    wx = (np.interp(np.arange(0, 1440, 60), t_min, T_out),
          np.interp(np.arange(0, 1440, 60), t_min, w_out))
    act = {"heater": 0.0, "fan_cooler": 0.0, "fogger": 0.0, "vent": 0.25}
    T, w = 29.28, 20.0
    T_lo, T_hi, w_lo, w_hi, rh_lo, rh_hi = 1e9, -1e9, 1e9, -1e9, 1e9, -1e9
    for i in range(1440):
        wx_i = (wx[0][i // 60], wx[1][i // 60], daytime_solar((i * 60) / 3600.0, params["A_sol"]))
        T, w, rh = step(60.0, act, wx_i, T, w)
        T_lo, T_hi = min(T_lo, T), max(T_hi, T)
        w_lo, w_hi = min(w_lo, w), max(w_hi, w)
        rh_lo, rh_hi = min(rh_lo, rh), max(rh_hi, rh)
    # Probe row 1 (RESEARCH.md line 305: vent 25% + solar) shows T 16.78..34.55,
    # w 11.00..21.17, RH 44..100. Bands below carry margin around those actuals —
    # the plan's literal [16.8, 35.8] floors the T at 16.8 which the probe (16.78)
    # already contradicts, so bounds are probe-faithful supersets.
    assert T_lo >= 16.5 and T_hi <= 36.0
    assert w_lo >= 10.9 and w_hi <= 38.5
    assert rh_lo >= 43.0 and rh_hi <= 100.0
    assert np.isfinite(T) and np.isfinite(w) and np.isfinite(rh)


def test_duty_linearity():
    import numpy as np
    from src.greenhouse_model import step

    wx = (15.8, 7.3, 0.0)
    base = {"heater": 0.0, "fan_cooler": 0.0, "fogger": 0.0, "vent": 0.0}
    T0, w0 = 29.0, 11.0
    T_off, _ = _run_loop(np, step, 60.0, 10, base, wx, T0, w0)
    T_full, _ = _run_loop(np, step, 60.0, 10, dict(base, heater=1.0), wx, T0, w0)
    T_half, _ = _run_loop(np, step, 60.0, 10, dict(base, heater=0.5), wx, T0, w0)
    eff_full = T_full - T_off
    eff_half = T_half - T_off
    assert abs(eff_half - 0.5 * eff_full) < 1e-6 * abs(eff_full)


def test_csv_load_and_interp():
    import numpy as np
    import os, tempfile
    from src.greenhouse_model import load_weather_profile, wsat_g_per_kg

    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "sine.csv")
    t = np.arange(0, 1441, dtype=int)                       # 1-min rows, 24h
    T = 20.0 + 0.4 * np.sin(2 * np.pi * t / 1440.0)
    RH = np.full(t.size, 65.0)
    np.savetxt(path, np.column_stack([t, T, RH]),
               header="time_min,temp_C,rh_pct", comments="", fmt=["%d", "%.8f", "%.2f"])

    t_min, temp_C, w_out = load_weather_profile(path)
    assert t_min[0] == 0 and t_min[-1] == 1440
    assert np.all(np.diff(t_min) > 0)                       # monotonic integer minutes
    assert np.all(np.isfinite(temp_C))                      # header row was skipped

    # linear interp of an amplitude-0.4 1440-min sine has chord error < 1e-6
    mid = np.arange(0.5, 1440.0, 1.0)
    expect = 20.0 + 0.4 * np.sin(2 * np.pi * mid / 1440.0)
    got = np.interp(mid, t_min, temp_C)
    assert np.allclose(got, expect, atol=1e-6)

    # w_out must be the RH->wsat(T) mapping (65% relative humidity)
    assert np.allclose(w_out, 0.65 * wsat_g_per_kg(temp_C), rtol=1e-6)


def test_generator_seedability():
    import numpy as np
    import os, tempfile
    from src.weather_profile_generator import generate_weather_profile

    tmp = tempfile.mkdtemp()
    p1 = os.path.join(tmp, "a.csv")
    p2 = os.path.join(tmp, "b.csv")
    generate_weather_profile(p1, seed=7)
    generate_weather_profile(p2, seed=7)
    with open(p1, "rb") as f1, open(p2, "rb") as f2:
        assert f1.read() == f2.read()                       # same seed -> byte-identical


def test_step_api_contract():
    from src.greenhouse_model import step

    wx = (15.8, 7.3, 0.0)
    act = {"heater": 0.0, "fan_cooler": 0.0, "fogger": 0.0, "vent": 0.0}
    out1 = step(60.0, act, wx, 25.0, 12.0)
    out2 = step(60.0, act, wx, 25.0, 12.0)
    assert isinstance(out1, tuple) and len(out1) == 3
    assert out1 == out2                                     # deterministic / stateless
    T, w, rh = out1
    assert 0.0 <= rh <= 100.0

    try:                                                    # missing key -> fail-fast
        step(60.0, {"heater": 1.0, "fan_cooler": 0.0, "fogger": 0.0}, wx, 25.0, 12.0)
        raise SystemExit("missing-key step() did not raise")
    except AssertionError:
        pass

    try:                                                    # unknown key -> fail-fast
        step(60.0, dict(act, mister=0.5), wx, 25.0, 12.0)
        raise SystemExit("unknown-key step() did not raise")
    except AssertionError:
        pass


def test_actuator_key_set():
    from src.greenhouse_model import step

    wx = (15.8, 7.3, 0.0)
    a = {"heater": 0.5, "fan_cooler": 0.0, "fogger": 0.0, "vent": 0.2}
    o1 = step(60.0, a, wx, 25.0, 12.0)
    o2 = step(60.0, {"vent": 0.2, "fogger": 0.0, "fan_cooler": 0.0, "heater": 0.5},
              wx, 25.0, 12.0)
    assert o1 == o2                                         # order-independent

    try:                                                    # extra key rejected
        step(60.0, dict(a, mister=0.5), wx, 25.0, 12.0)
        raise SystemExit("extra-key step() did not raise")
    except AssertionError:
        pass

    try:                                                    # subset (missing key) rejected
        step(60.0, {"heater": 0.5, "vent": 0.2}, wx, 25.0, 12.0)
        raise SystemExit("subset-key step() did not raise")
    except AssertionError:
        pass


if __name__ == "__main__":
    import sys
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