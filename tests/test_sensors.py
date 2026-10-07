"""Headless sensor acquisition checks (Claim 1 sensor module).

Plain-assert standalone suite in the tests/test_dashboard.py style.

Run:  python tests/test_sensors.py
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_sense_plant_validates():
    import sys
    sys.path.insert(0, ROOT)
    from src.sensors import sense_plant
    assert sense_plant(25.0, 70.0) == {"T_C": 25.0, "rh_pct": 70.0}
    for bad in (float("nan"), float("inf")):
        for fn in (lambda: sense_plant(bad, 70.0),
                   lambda: sense_plant(25.0, bad)):
            try:
                fn()
            except AssertionError:
                pass
            else:
                raise AssertionError("non-finite measurement accepted")
    print("sense_plant validates finite measurements")


def test_tracking_errors_math_and_carryover():
    import sys
    sys.path.insert(0, ROOT)
    from src.sensors import tracking_errors
    st = {'pT': None, 'pH': None}  # caller-owned carryover state
    eT, eH, dT, dH = tracking_errors(20.0, 60.0, 25.0, 70.0, st)
    assert (eT, eH, dT, dH) == (5.0, 10.0, 0.0, 0.0), (eT, eH, dT, dH)
    eT2, eH2, dT2, dH2 = tracking_errors(21.0, 62.0, 25.0, 70.0, st)
    assert (eT2, eH2) == (4.0, 8.0), (eT2, eH2)
    assert (dT2, dH2) == (-1.0, -2.0), (dT2, dH2)  # per-minute rates
    assert st == {'pT': 4.0, 'pH': 8.0}, st
    print("tracking errors exact, rates per-minute, state carried")


def test_adaptive_consumes_sensor_module():
    import sys
    sys.path.insert(0, ROOT)
    from src.adaptive_fuzzy import adaptive_fuzzy_step
    st = None
    for _ in range(5):
        act, st = adaptive_fuzzy_step(20.0, 60.0, 25.0, 70.0, st)
    assert set(act) == {"heater", "fan_cooler", "fogger", "vent"}, act
    assert st['sens'] == {'pT': 5.0, 'pH': 10.0}, st['sens']
    assert all(0.0 <= v <= 1.0 for v in act.values()), act
    print("adaptive_fuzzy_step tracks errors via sensors, duties bounded")


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
