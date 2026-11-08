"""Plain-assert suite for metrics kernels + scoreboard (METR-01/02).

Proves the locked holdout ordering (GA cost < on/off AND < PID),
energy bit-identity with the GA fitness loop, and the frozen CSV
contract. Reference holdout numbers only as comments (GA about
114.28, on/off about 513.75, PID about 645.26), never as asserts.

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_metrics.py
"""


def test_metric_kernels_synthetic():
    import numpy as np
    from src.metrics import rmse, iae, ise

    hist = [25.0, 26.0, 27.0]
    sp = 25.0
    assert abs(rmse(hist, sp) - np.sqrt(5.0 / 3.0)) < 1e-12, rmse(hist, sp)
    assert abs(iae(hist, sp) - 3.0 / 60.0) < 1e-12, iae(hist, sp)
    assert abs(ise(hist, sp) - 5.0 / 60.0) < 1e-12, ise(hist, sp)
    assert rmse([sp, sp, sp], sp) == 0.0
    assert iae([sp, sp, sp], sp) == 0.0
    print("synthetic rmse/iae/ise match hand values")


def test_settling_edges():
    from src.metrics import settling_time_min

    n = 60
    # clean run settles at t=0
    assert settling_time_min([25.0] * n, [70.0] * n) == 0.0
    # final-step violation -> never settled
    T = [25.0] * (n - 1) + [30.0]
    assert settling_time_min(T, [70.0] * n) == float("inf")
    RH = [70.0] * (n - 1) + [90.0]
    assert settling_time_min([25.0] * n, RH) == float("inf")
    # mid-run last exit at index 9 -> 10 minutes
    T2 = [25.0] * n
    T2[9] = 30.0
    assert settling_time_min(T2, [70.0] * n) == 10.0
    print("settling edges 0.0 / inf / last-exit minutes hold")


def test_energy_identity():
    import numpy as np
    from src.metrics import run_closed_loop, energy_duty_hours, iae
    from src.fuzzy_controller import fuzzy_step, FUZZY_MFS
    from src.greenhouse_model import load_weather_profile
    from src.genetic_algorithm import closed_loop_breakdown

    T_h, RH_h, U_h = run_closed_loop(fuzzy_step,
                                     "weather/weather_profile.csv")
    E_metrics = energy_duty_hours(U_h)
    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    hours = np.arange(0, 1440) / 60.0
    iae_T, iae_H, E_fit = closed_loop_breakdown(
        FUZZY_MFS, np.interp(hours, t_min, T_out),
        np.interp(hours, t_min, w_out), hours)
    assert E_metrics == E_fit, (E_metrics, E_fit)
    assert abs(iae(T_h, 25.0) - iae_T) < 1e-9, (iae(T_h, 25.0), iae_T)
    assert abs(iae(RH_h, 70.0) - iae_H) < 1e-9
    print(f"energy identity {E_metrics:.4f} == fitness {E_fit:.4f}")


def test_overshoot():
    from src.metrics import overshoot

    assert overshoot([25.0, 26.5, 24.0, 27.0], 25.0) == 2.0
    assert overshoot([25.0, 24.0, 23.0], 25.0) == 0.0  # undershoot ignored
    assert overshoot([70.0, 75.0, 68.0], 70.0) == 5.0
    print("overshoot positive-side-only peaks hold")


def test_compare_shape():
    import time
    from src.metrics import compare, COLUMNS

    frozen = "results/comparison.csv"
    with open(frozen, "rb") as f:
        before = f.read()
    t0 = time.time()
    rows = compare()  # default is read-only: must not touch results/comparison.csv
    dt = time.time() - t0
    assert dt < 600.0, dt  # hang guard only, not a perf bar
    with open(frozen, "rb") as f:
        assert f.read() == before, "compare() default path rewrote the frozen CSV"
    assert len(rows) == 8, len(rows)
    assert len(COLUMNS) == 14, COLUMNS
    for r in rows:
        assert set(r) == set(COLUMNS), set(r)
        assert r["controller"] in ("onoff", "pid", "fuzzy", "ga_fuzzy")
        assert r["weather"] in ("train-seed7", "holdout-seed21")
    ctrls = sorted(r["controller"] for r in rows if r["weather"] == "holdout-seed21")
    assert ctrls == ["fuzzy", "ga_fuzzy", "onoff", "pid"], ctrls
    print(f"compare shape 8 rows x 14 cols in {dt:.1f}s")


def test_holdout_ordering():
    from src.metrics import compare

    rows = compare()
    # GA about 114.28, on/off about 513.75, PID about 645.26 (comments only)
    hold = {r["controller"]: r["cost"] for r in rows
            if r["weather"] == "holdout-seed21"}
    assert hold["ga_fuzzy"] < hold["onoff"], hold
    assert hold["ga_fuzzy"] < hold["pid"], hold
    ga_rank = next(r["rank"] for r in rows if r["weather"] == "holdout-seed21"
                   and r["controller"] == "ga_fuzzy")
    assert ga_rank == 1, ga_rank
    print(f"holdout GA {hold['ga_fuzzy']:.2f} < onoff {hold['onoff']:.2f} "
          f"< pid {hold['pid']:.2f} (rank 1)")


def test_csv_roundtrip():
    import csv
    import os
    import tempfile
    from src.metrics import compare, COLUMNS

    tmp = os.path.join(tempfile.mkdtemp(), "comparison.csv")
    rows = compare(out_path=tmp)  # never clobber results/comparison.csv
    with open(tmp) as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == COLUMNS, reader.fieldnames
        back = list(reader)
    assert len(back) == 8, len(back)
    for r, b in zip(rows, back):
        for c in COLUMNS:
            if isinstance(r[c], str):
                assert b[c] == r[c], (c, b[c], r[c])
            else:
                assert float(b[c]) == r[c], (c, b[c], r[c])
    with open("results/comparison.csv") as f:
        assert csv.DictReader(f).fieldnames == COLUMNS
    print("csv header == COLUMNS with lossless round-trip incl inf")


def test_weathers_distinct():
    from src.metrics import compare

    rows = compare()
    for cname in ("onoff", "pid", "fuzzy", "ga_fuzzy"):
        costs = [r["cost"] for r in rows if r["controller"] == cname]
        assert len(costs) == 2 and costs[0] != costs[1], (cname, costs)
    print("train vs holdout blocks differ for all controllers")


def test_nan_failfast():
    from src.metrics import (rmse, iae, ise, settling_time_min, overshoot,
                             energy_duty_hours, weighted_cost)

    nan = float("nan")
    for fn in (lambda: rmse([25.0, nan], 25.0),
               lambda: iae([25.0, nan], 25.0),
               lambda: ise([25.0, nan], 25.0),
               lambda: settling_time_min([25.0, nan], [70.0, 70.0]),
               lambda: settling_time_min([25.0, 25.0], [70.0, nan]),
               lambda: overshoot([25.0, nan], 25.0),
               lambda: energy_duty_hours([{"heater": nan, "fan_cooler": 0.0,
                                           "fogger": 0.0, "vent": 0.0}]),
               lambda: weighted_cost(nan, 1.0, 1.0),
               lambda: rmse([], 25.0),
               lambda: rmse([25.0], nan)):
        try:
            fn()
        except AssertionError:
            continue
        raise AssertionError(f"expected AssertionError from {fn}")
    print("nan/empty inputs raise AssertionError in every kernel")


if __name__ == "__main__":
    import sys, os
    # "python tests/test_metrics.py" puts tests/ on sys.path, not the
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
