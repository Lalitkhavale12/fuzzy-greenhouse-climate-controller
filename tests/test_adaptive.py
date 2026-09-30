"""Headless adaptive-fuzzy checks (FUZZ-07).

Plain-assert standalone suite in the tests/test_dashboard.py style.

Run:  python tests/test_adaptive.py
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_gain_rises_under_persistent_error():
    import sys
    sys.path.insert(0, ROOT)
    from src.adaptive_fuzzy import adaptive_fuzzy_step
    st = None
    for _ in range(300):
        _, st = adaptive_fuzzy_step(15.0, 70.0, 25.0, 70.0, st)
    assert st['gT'] > 1.0, st['gT']
    print("gain rises under persistent error: gT=%.2f" % st['gT'])


def test_gain_relaxes_at_setpoint():
    import sys
    sys.path.insert(0, ROOT)
    from src.adaptive_fuzzy import adaptive_fuzzy_step
    st = None
    for _ in range(300):
        _, st = adaptive_fuzzy_step(15.0, 70.0, 25.0, 70.0, st)
    high = st['gT']
    for _ in range(600):
        _, st = adaptive_fuzzy_step(25.0, 70.0, 25.0, 70.0, st)
    assert st['gT'] < high, (st['gT'], high)
    assert 0.5 <= st['gT'] <= 2.0, st['gT']
    print("gain relaxes at setpoint: %.2f -> %.2f" % (high, st['gT']))


def test_duties_bounded_split_range():
    import sys
    sys.path.insert(0, ROOT)
    from src.adaptive_fuzzy import adaptive_fuzzy_step
    st = None
    for i in range(400):
        T = 15.0 + 20.0 * (i / 400.0)
        act, st = adaptive_fuzzy_step(T, 40.0 + 0.1 * i, 25.0, 70.0, st)
        for v in act.values():
            assert 0.0 <= v <= 1.0, act
        assert not (act['heater'] > 0 and act['fan_cooler'] > 0), act
    print("duties bounded, heater/cooler never both on")


def test_frozen_mfs_untouched_and_closed_loop():
    import sys
    sys.path.insert(0, ROOT)
    import numpy as np
    from src.fuzzy_controller import FUZZY_MFS
    from src.adaptive_fuzzy import adaptive_fuzzy_step
    from src.metrics import run_closed_loop
    before = {k: (np.array(v["centers"]), np.array(v["widths"]))
              for k, v in FUZZY_MFS.items()}
    T, RH, _ = run_closed_loop(adaptive_fuzzy_step,
                               os.path.join(ROOT, "weather",
                                            "weather_profile.csv"), n=240)
    assert len(T) == 240 and all(np.isfinite(T)) and all(np.isfinite(RH))
    for k in FUZZY_MFS:
        assert np.array_equal(FUZZY_MFS[k]["centers"], before[k][0]), k
        assert np.array_equal(FUZZY_MFS[k]["widths"], before[k][1]), k
    print("closed-loop ok, frozen MFs untouched")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
