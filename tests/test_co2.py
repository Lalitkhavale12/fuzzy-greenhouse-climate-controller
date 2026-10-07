"""Headless CO2 valve checks (Claim 1 fifth actuator).

Plain-assert standalone suite in the tests/test_dashboard.py style.

Run:  python tests/test_co2.py
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACT5 = {"heater": 0.0, "fan_cooler": 0.0, "fogger": 0.0, "vent": 0.0,
        "co2_valve": 0.0}


def test_wrapper_matches_core():
    import sys
    sys.path.insert(0, ROOT)
    from src.greenhouse_model import step, step_co2
    act4 = dict(list(ACT5.items())[:4])
    wx = (20.0, 10.0, 0.0)
    T, w, rh = step(60.0, act4, wx, 25.0, 15.0)
    T2, w2, rh2, C2 = step_co2(60.0, dict(ACT5), wx, 25.0, 15.0, 420.0)
    assert (T, w, rh) == (T2, w2, rh2), "4-key core must be bit-identical"
    assert C2 == 420.0, C2  # valve shut, at outdoor baseline: equilibrium
    print("wrapper bit-identical to step(), equilibrium at 420 ppm")


def test_accumulates_and_flushes():
    import sys
    sys.path.insert(0, ROOT)
    from src.greenhouse_model import step_co2, C_OUT_PPM
    wx = (20.0, 10.0, 0.0)
    act = dict(ACT5, co2_valve=1.0)
    C = C_OUT_PPM
    for _ in range(600):  # 10 h dosed, vent shut
        _, _, _, C = step_co2(60.0, act, wx, 25.0, 15.0, C)
    assert C > 900.0, C  # enrichment accumulates toward ~1400 ppm
    assert C <= 2000.0, C  # clamp band holds
    vent = dict(ACT5, vent=1.0)
    for _ in range(600):  # 10 h flushed
        _, _, _, C = step_co2(60.0, vent, wx, 25.0, 15.0, C)
    assert abs(C - C_OUT_PPM) < 5.0, C  # back to outdoor baseline
    print("accumulates dosed, flushes vented, clamps held")


def test_key_contract_and_params_untouched():
    import sys
    sys.path.insert(0, ROOT)
    from src.greenhouse_model import step_co2, params
    wx = (20.0, 10.0, 0.0)
    try:
        step_co2(60.0, {"heater": 0.0}, wx, 25.0, 15.0, 420.0)
    except AssertionError:
        pass
    else:
        raise AssertionError("4-key dict accepted by 5-key wrapper")
    assert "co2_valve" not in params and "C_OUT_PPM" not in params, \
        "locked D-07 params dict untouched"
    print("5-key contract enforced, params dict untouched")


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
