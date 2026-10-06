"""Plain-assert sanity suite for the GA-tuned fuzzy controller (GA-01..05).

D-06/A2: 62-D chromosome (60 MF genes + k_heat/k_vent coupling gains);
fitness and ga_fuzzy_step run the COUPLED path (decoupled loops first,
then the humidity-driven heater/vent boost).

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_genetic_algorithm.py
"""


def test_encode_decode_roundtrip():
    import numpy as np
    from src.fuzzy_controller import FUZZY_MFS
    from src.genetic_algorithm import (encode, decode, ORDER, CHROM_LEN,
                                       COUPLING_KEYS)

    chrom = encode(FUZZY_MFS)
    assert chrom.shape == (CHROM_LEN,), chrom.shape
    assert CHROM_LEN == 62, CHROM_LEN
    mfs, gains = decode(chrom)
    assert set(mfs) == set(ORDER)
    for k in ORDER:  # hand values bit-identical through the round-trip
        assert np.array_equal(mfs[k]["centers"], FUZZY_MFS[k]["centers"]), k
        assert np.array_equal(mfs[k]["widths"], FUZZY_MFS[k]["widths"]), k
    assert set(gains) == set(COUPLING_KEYS)  # default = zero (hand-equiv)
    assert all(g == 0.0 for g in gains.values()), gains
    g2 = {"k_heat": 0.02, "k_vent": 0.013}
    mfs2, back2 = decode(encode(FUZZY_MFS, g2))
    assert back2 == g2, (back2, g2)
    for k in ORDER:
        assert np.array_equal(mfs2[k]["centers"], FUZZY_MFS[k]["centers"]), k


def test_decode_repair_invariants():
    import numpy as np
    from src.genetic_algorithm import (decode, BOUNDS, ORDER, CHROM_LEN,
                                       COUPLING_BOUNDS, COUPLING_KEYS)

    rng = np.random.default_rng(1234)
    for _ in range(20):  # wild chromosomes -> sorted, clipped, finite
        mfs, gains = decode(rng.uniform(-100, 100, CHROM_LEN))
        for k in ORDER:
            c, w = mfs[k]["centers"], mfs[k]["widths"]
            lo, hi, wmin, wmax = BOUNDS[k]
            assert np.all(np.isfinite(c)) and np.all(np.isfinite(w)), k
            assert np.all(c[:-1] <= c[1:]), (k, c)  # ascending
            assert np.all((c >= lo) & (c <= hi)), (k, c)
            assert np.all((w >= wmin) & (w <= wmax)) and np.all(w > 0.0), (k, w)
        for k in COUPLING_KEYS:  # gains clipped into bounds, finite
            lo, hi = COUPLING_BOUNDS[k]
            assert np.isfinite(gains[k]) and lo <= gains[k] <= hi, (k, gains)
    a, _ = decode(rng.uniform(-100, 100, CHROM_LEN))  # fresh arrays, no views
    b, _ = decode(np.zeros(CHROM_LEN))
    a["eT"]["centers"][0] = -999.0
    assert b["eT"]["centers"][0] != -999.0
    legacy_mfs, legacy_g = decode(np.zeros(60))  # len-60 legacy -> zero gains
    assert all(g == 0.0 for g in legacy_g.values()), legacy_g
    for bad in (59, 61, 63):
        try:
            decode(np.zeros(bad))
        except AssertionError:
            pass
        else:
            raise AssertionError(f"len-{bad} chromosome did not raise")


def test_fitness_matches_hand_cost():
    import numpy as np
    from src.fuzzy_controller import FUZZY_MFS, fuzzy_step
    from src.genetic_algorithm import encode, evaluate
    from src.greenhouse_model import (step, load_weather_profile,
                                      daytime_solar, params,
                                      relative_humidity, wsat_g_per_kg)

    t_min, T_out, w_out = load_weather_profile("weather/weather_profile.csv")
    hours = np.arange(0, 1440) / 60.0
    T_hr = np.interp(hours, t_min, T_out)
    w_hr = np.interp(hours, t_min, w_out)
    cost = evaluate(encode(FUZZY_MFS), T_hr, w_hr, hours)
    assert np.isfinite(cost), cost
    T, w, st = 20.0, 0.65 * wsat_g_per_kg(20.0), None  # reference direct loop
    iae_T, iae_H, E = 0.0, 0.0, 0.0
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = fuzzy_step(T, rh, 25.0, 70.0, st)
        T, w, rh = step(60.0, act, (T_hr[i], w_hr[i],
                                    daytime_solar(h, params["A_sol"])), T, w)
        iae_T += abs(T - 25.0) / 60.0
        iae_H += abs(rh - 70.0) / 60.0
        E += sum(act.values()) / 60.0
    ref = 1.0 * iae_T + 1.0 * iae_H + 0.01 * E
    # zero-gain encode == decoupled == hand fuzzy cost exactly
    assert abs(cost - ref) < 1e-9, (cost, ref)
    print(f"hand fitness {cost:.2f} (IAE_T {iae_T:.2f} IAE_H {iae_H:.2f} E {E:.2f})")


def test_fitness_never_raises():
    import numpy as np
    from src.genetic_algorithm import evaluate, CHROM_LEN

    hours = np.arange(0, 1440) / 60.0
    T_hr = np.full(1440, 20.0)
    w_hr = np.full(1440, 10.0)
    nasty = [np.full(CHROM_LEN, np.nan), np.full(CHROM_LEN, np.inf),
             np.full(CHROM_LEN, 1e300),
             np.zeros(59), np.zeros(61), np.zeros(63)]
    for c in nasty:  # never raises; float out (finite or inf)
        r = evaluate(c, T_hr, w_hr, hours)
        assert isinstance(r, float) and (np.isfinite(r) or r == float("inf")), r
    assert evaluate(np.zeros(59), T_hr, w_hr, hours) == float("inf")


def test_hand_mfs_untouched():
    import numpy as np
    from src.fuzzy_controller import FUZZY_MFS
    from src.genetic_algorithm import (decode, gaussian_mutate, encode,
                                       evaluate, CHROM_LEN)

    before = {k: (FUZZY_MFS[k]["centers"].copy(), FUZZY_MFS[k]["widths"].copy())
              for k in FUZZY_MFS}
    rng = np.random.default_rng(0)
    chrom = encode(FUZZY_MFS)
    mfs, _ = decode(chrom + rng.normal(0, 1, CHROM_LEN))  # decode churn
    gaussian_mutate(chrom.copy(), rng)
    hours = np.arange(0, 1440) / 60.0
    evaluate(chrom, np.full(1440, 20.0), np.full(1440, 10.0), hours)
    assert set(mfs) == set(FUZZY_MFS)
    for k in FUZZY_MFS:  # global bit-identical after all GA-side churn
        assert np.array_equal(FUZZY_MFS[k]["centers"], before[k][0]), k
        assert np.array_equal(FUZZY_MFS[k]["widths"], before[k][1]), k


def test_coupling_zero_gains_identical():
    from src.fuzzy_controller import FUZZY_MFS, fuzzy_step
    from src.genetic_algorithm import coupled_fuzzy_step

    zero = {"k_heat": 0.0, "k_vent": 0.0}
    for T_C, rh in ((20.0, 70.0), (30.0, 50.0), (24.0, 95.0), (18.0, 88.0)):
        a, _ = coupled_fuzzy_step(T_C, rh, 25.0, 70.0, None, 60.0,
                                  FUZZY_MFS, zero)
        b, _ = fuzzy_step(T_C, rh, 25.0, 70.0, None, 60.0, FUZZY_MFS)
        assert a == b, (T_C, rh, a, b)  # zero boost == decoupled bit-identical
        c, _ = coupled_fuzzy_step(T_C, rh, 25.0, 70.0, None, 60.0,
                                  FUZZY_MFS, None)
        assert c == b, (T_C, rh, c, b)  # gains=None also decoupled


def test_coupling_positive_boost():
    import numpy as np
    from src.fuzzy_controller import FUZZY_MFS, fuzzy_step
    from src.genetic_algorithm import coupled_fuzzy_step

    gains = {"k_heat": 0.03, "k_vent": 0.02}
    # humid: boost raises heater/vent vs decoupled, contract holds
    a, _ = coupled_fuzzy_step(24.0, 95.0, 25.0, 70.0, None, 60.0,
                              FUZZY_MFS, gains)
    b, _ = fuzzy_step(24.0, 95.0, 25.0, 70.0, None, 60.0, FUZZY_MFS)
    assert set(a) == {"heater", "fan_cooler", "fogger", "vent"}
    assert all(np.isfinite(v) and 0.0 <= v <= 1.0 for v in a.values())
    assert a["heater"] >= b["heater"] and a["vent"] >= b["vent"], (a, b)
    assert (a["heater"] > b["heater"]) or (a["vent"] > b["vent"]), (a, b)
    assert a["fan_cooler"] == b["fan_cooler"] and a["fogger"] == b["fogger"]
    # dry (rh below setpoint): no boost, identical to decoupled
    d, _ = coupled_fuzzy_step(24.0, 55.0, 25.0, 70.0, None, 60.0,
                              FUZZY_MFS, gains)
    e, _ = fuzzy_step(24.0, 55.0, 25.0, 70.0, None, 60.0, FUZZY_MFS)
    assert d == e, (d, e)


def test_json_schema():
    import json
    import os
    import tempfile
    import numpy as np
    from src.genetic_algorithm import run_ga, decode, COUPLING_KEYS
    from src.ga_fuzzy_controller import load_optimized_mfs, ga_fuzzy_step
    from src.fuzzy_controller import fuzzy_step
    from src.genetic_algorithm import apply_coupling

    tmp = os.path.join(tempfile.mkdtemp(), "ga_smoke.json")
    res = run_ga(population=3, generations=1, rng_seed=0, out_path=tmp)
    assert np.isfinite(res["best_fit"]), res
    assert set(res["best_gains"]) == set(COUPLING_KEYS)
    with open(tmp) as f:
        d = json.load(f)
    assert set(d) == {"mfs", "coupling", "fitness", "weights",
                      "train_weather", "train_seed", "holdout_seed",
                      "population", "generations", "rng_seed",
                      "schema_version", "history"}, set(d)
    assert set(d["mfs"]) == {"eT", "deT", "du", "eH", "deH", "dv"}
    for k in d["mfs"]:
        assert len(d["mfs"][k]["centers"]) == 5
        assert len(d["mfs"][k]["widths"]) == 5
        assert all(isinstance(x, float) for x in
                   d["mfs"][k]["centers"] + d["mfs"][k]["widths"])
        assert all(x > 0.0 for x in d["mfs"][k]["widths"])
    assert set(d["coupling"]) == set(COUPLING_KEYS)
    assert all(isinstance(v, float) and np.isfinite(v)
               for v in d["coupling"].values())
    assert d["weights"] == {"w1": 1.0, "w2": 1.0, "w3": 0.01}
    assert d["holdout_seed"] == 21 and d["population"] == 3
    assert d["generations"] == 1 and len(d["history"]["best"]) == 1
    assert len(d["history"]["mean"]) == 1
    mfs, gains = load_optimized_mfs(tmp)  # wrapper == engine + boost
    for T_C, rh in ((20.0, 70.0), (30.0, 50.0), (24.0, 95.0)):
        a, _ = ga_fuzzy_step(T_C, rh, 25.0, 70.0, None, 60.0, tmp)
        b, st = fuzzy_step(T_C, rh, 25.0, 70.0, None, 60.0, mfs)
        assert a == apply_coupling(b, rh, 70.0, gains), (T_C, rh, a, b)
    ref, ref_g = decode(res["best_chrom"])
    for k in ref:
        assert np.array_equal(mfs[k]["centers"], ref[k]["centers"]), k
    assert gains == ref_g, (gains, ref_g)


def test_tiny_ga_monotonic():
    import os
    import tempfile
    import time
    import numpy as np
    from src.fuzzy_controller import FUZZY_MFS
    from src.genetic_algorithm import run_ga

    before = np.concatenate([FUZZY_MFS[k]["centers"] for k in FUZZY_MFS])
    tmp = os.path.join(tempfile.mkdtemp(), "ga_tiny.json")
    t0 = time.time()
    res = run_ga(population=4, generations=2, rng_seed=0, out_path=tmp)
    dt = time.time() - t0
    assert dt < 300.0, dt  # hang guard only, not a perf bar (WR-03)
    assert np.isfinite(res["best_fit"]), res
    hist = res["history"]["best"]
    assert len(hist) == 2, hist
    assert hist[-1] <= hist[0] + 1e-12, hist  # elitism-2: never worsens
    assert np.array_equal(np.concatenate(
        [FUZZY_MFS[k]["centers"] for k in FUZZY_MFS]), before)
    print(f"tiny GA best {hist[0]:.2f} -> {hist[-1]:.2f} in {dt:.1f}s")


if __name__ == "__main__":
    import sys, os
    # "python tests/test_genetic_algorithm.py" puts tests/ on sys.path, not the
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
