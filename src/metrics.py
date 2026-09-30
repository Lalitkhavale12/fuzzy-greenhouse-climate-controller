"""Closed-loop performance metrics + scoreboard harness (METR-01/02).

Pure NumPy kernels over logged (T, RH, U) histories plus the locked
weighted cost and a compare() harness running all four controllers on
both weathers. No pandas, stdlib csv only (D-02).
"""

import csv
import os

import numpy as np

try:
    from src.greenhouse_model import (step, load_weather_profile,
                                      daytime_solar, params,
                                      relative_humidity, wsat_g_per_kg)
    from src.onoff_controller import onoff_step
    from src.pid_controller import pid_step
    from src.fuzzy_controller import fuzzy_step
    from src.ga_fuzzy_controller import ga_fuzzy_step
except ImportError:  # `python src/metrics.py` puts src/ on sys.path
    from greenhouse_model import (step, load_weather_profile,
                                  daytime_solar, params,
                                  relative_humidity, wsat_g_per_kg)
    from onoff_controller import onoff_step
    from pid_controller import pid_step
    from fuzzy_controller import fuzzy_step
    from ga_fuzzy_controller import ga_fuzzy_step

W1, W2, W3 = 1.0, 1.0, 0.01  # locked fitness weights (genetic_algorithm.py:50)

COLUMNS = ["controller", "weather",
           "rmse_T", "rmse_H", "iae_T", "iae_H", "ise_T", "ise_H",
           "settling_min", "overshoot_T", "overshoot_H",
           "energy", "cost", "rank"]
# controller in {"onoff","pid","fuzzy","ga_fuzzy"};
# weather in {"train-seed7","holdout-seed21"};
# rank = 1..4 by cost WITHIN each weather block (holdout block is the verdict)

CONTROLLERS = [("onoff", onoff_step), ("pid", pid_step),
               ("fuzzy", fuzzy_step), ("ga_fuzzy", ga_fuzzy_step)]

WEATHERS = [("train-seed7", "weather/weather_profile.csv"),
            ("holdout-seed21", "weather/holdout_21.csv")]


def _check_hist(hist: list, sp: float, dt: float) -> np.ndarray:
    a = np.asarray(hist, dtype=float)
    assert a.size > 0, "history must be non-empty"
    assert np.all(np.isfinite(a)), "history must be finite"
    assert np.isfinite(sp), "setpoint must be finite"
    assert np.isfinite(dt) and dt > 0, "dt must be positive"
    return a


def rmse(hist: list, sp: float) -> float:
    """Root-mean-square error vs setpoint."""
    e = _check_hist(hist, sp, 60.0) - sp
    return float(np.sqrt(np.mean(e * e)))


def iae(hist: list, sp: float, dt: float = 60.0) -> float:
    """Integral absolute error in degree-hours / %-hours."""
    e = _check_hist(hist, sp, dt) - sp
    return float(np.sum(np.abs(e)) * dt / 3600.0)


def ise(hist: list, sp: float, dt: float = 60.0) -> float:
    """Integral squared error (dt-weighted)."""
    e = _check_hist(hist, sp, dt) - sp
    return float(np.sum(e * e) * dt / 3600.0)


def settling_time_min(T_hist: list, RH_hist: list, T_sp: float = 25.0,
                      RH_sp: float = 70.0, band_T: float = 0.5,
                      band_RH: float = 3.0, dt: float = 60.0) -> float:
    """Joint-band last-exit scan: T within +-band_T AND RH within +-band_RH
    for the remainder of the run. 0.0 when clean, float("inf") when the
    final step violates (never settled)."""
    T = _check_hist(T_hist, T_sp, dt)
    RH = np.asarray(RH_hist, dtype=float)
    assert RH.size > 0 and RH.size == T.size, "histories non-empty equal-length"
    assert np.all(np.isfinite(RH)), "RH history must be finite"
    assert np.isfinite(RH_sp), "RH setpoint must be finite"
    assert np.isfinite(band_T) and np.isfinite(band_RH)
    assert band_T > 0 and band_RH > 0, "bands must be positive"
    bad = np.where((np.abs(T - T_sp) > band_T)
                   | (np.abs(RH - RH_sp) > band_RH))[0]
    if bad.size == 0:
        return 0.0
    if bad[-1] == len(T) - 1:
        return float("inf")  # violates at final step -> never settled
    return float((bad[-1] + 1) * dt / 60.0)


def overshoot(hist: list, sp: float) -> float:
    """Positive-side-only absolute peak beyond setpoint (startup undershoot
    from the cold 20 C init is a transient, not overshoot)."""
    a = _check_hist(hist, sp, 60.0)
    return float(max(0.0, np.max(a - sp)))


def energy_duty_hours(U_hist: list) -> float:
    """Total duty-hours over ALL actuators incl. vent.

    LOCKED — identical to genetic_algorithm.closed_loop_breakdown
    (genetic_algorithm.py:187): E += sum(act.values()) / 60.0 per step.
    """
    assert len(U_hist) > 0, "U history must be non-empty"
    E = 0.0
    for act in U_hist:
        assert set(act) == {"heater", "fan_cooler", "fogger", "vent"}, \
            f"actuator keys {set(act)}"
        assert all(np.isfinite(v) and 0.0 <= v <= 1.0
                   for v in act.values()), "duties in [0,1]"
        E += sum(act.values()) / 60.0  # duty-hours (genetic_algorithm.py:187)
    return float(E)


def weighted_cost(iae_T: float, iae_H: float, E: float, w1: float = W1,
                  w2: float = W2, w3: float = W3) -> float:
    """Locked cost: W1*IAE_T + W2*IAE_H + W3*E with 1.0/1.0/0.01."""
    assert np.isfinite(iae_T) and np.isfinite(iae_H) and np.isfinite(E)
    assert (w1, w2, w3) == (1.0, 1.0, 0.01), "weights locked 1.0/1.0/0.01"
    return float(w1 * iae_T + w2 * iae_H + w3 * E)


def run_closed_loop(controller_step, weather_path: str, n: int = 1440,
                    T_sp: float = 25.0, RH_sp: float = 70.0) -> tuple[list, list, list]:
    """1440 x dt=60 closed loop -> (T_hist, RH_hist, U_hist).

    weather_path is REQUIRED (no default): both table blocks must score
    their own frozen file, never a hardcoded default (wrong-file guard).
    """
    assert isinstance(weather_path, (str, os.PathLike)) and str(weather_path), \
        "weather_path required"
    weather_path = os.fspath(weather_path)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    t_min, T_out, w_out = load_weather_profile(weather_path)
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


def all_metrics(T_hist: list, RH_hist: list, U_hist: list,
                T_sp: float = 25.0, RH_sp: float = 70.0) -> dict:
    """Bundle the six METR-01 metrics plus locked cost (no rank)."""
    m = {
        "rmse_T": rmse(T_hist, T_sp),
        "rmse_H": rmse(RH_hist, RH_sp),
        "iae_T": iae(T_hist, T_sp),
        "iae_H": iae(RH_hist, RH_sp),
        "ise_T": ise(T_hist, T_sp),
        "ise_H": ise(RH_hist, RH_sp),
        "settling_min": settling_time_min(T_hist, RH_hist, T_sp, RH_sp),
        "overshoot_T": overshoot(T_hist, T_sp),
        "overshoot_H": overshoot(RH_hist, RH_sp),
    }
    m["energy"] = energy_duty_hours(U_hist)
    m["cost"] = weighted_cost(m["iae_T"], m["iae_H"], m["energy"])
    return m


def compare(out_path: str = "results/comparison.csv") -> list:
    """Scoreboard: 4 controllers x 2 weathers -> list of 8 dicts + CSV.

    Rows carry exactly the COLUMNS keys. rank 1..4 by cost WITHIN each
    weather block (sorted-stable: equal-cost ties keep first-seen order).
    settling float("inf") serializes as "inf", parsing back losslessly
    via float("inf").
    """
    rows = []
    for wname, wpath in WEATHERS:
        block = []
        for cname, cstep in CONTROLLERS:
            T_h, RH_h, U_h = run_closed_loop(cstep, wpath)
            m = all_metrics(T_h, RH_h, U_h)
            block.append({"controller": cname, "weather": wname, **m})
        for i, r in enumerate(sorted(block, key=lambda r: r["cost"]), 1):
            r["rank"] = i
        rows.extend(block)
    d = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(d, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    for r in compare():
        print(r["controller"], r["weather"],
              f"cost={r['cost']:.2f} rank={r['rank']}")
