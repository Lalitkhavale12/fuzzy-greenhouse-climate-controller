"""Real-valued GA tuning the fuzzy membership functions (GA-01..04).

62-D chromosome = 6 MF groups in ORDER x (5 centers + 5 widths) + 2
cross-coupling gains (D-06/A2). Decode repairs every chromosome (sort
clipped centers, clip widths into [w_min, w_max] with w_min > 0, clip
gains into COUPLING_BOUNDS) and allocates fresh dicts/arrays, so the
FUZZY_MFS global is never touched. Fitness is the locked weighted cost
1.0*IAE_T + 1.0*IAE_H + 0.01*duty-hours-energy via the full 1440-step
closed loop over the COUPLED path (decoupled velocity loops first, then
the humidity-driven heater/vent boost), never raising (bad chromosome ->
+inf). Operators: tournament-3, BLX-0.5, per-gene gaussian mutation,
elitism-2, all draws through the single default_rng owned by run_ga.
Individual 0 is the exact hand FUZZY_MFS encoding with ZERO coupling
gains, so the GA never returns worse than hand fuzzy.

NumPy + stdlib json only. Run:  python src/genetic_algorithm.py
"""

import json
import os
import sys

import numpy as np

try:
    from src.greenhouse_model import (step, load_weather_profile,
                                      daytime_solar, params,
                                      relative_humidity, wsat_g_per_kg)
    from src.fuzzy_controller import fuzzy_step, FUZZY_MFS
except ImportError:  # `python src/genetic_algorithm.py` puts src/ on sys.path
    from greenhouse_model import (step, load_weather_profile,
                                  daytime_solar, params,
                                  relative_humidity, wsat_g_per_kg)
    from fuzzy_controller import fuzzy_step, FUZZY_MFS

ORDER = ["eT", "deT", "du", "eH", "deH", "dv"]

# (center_lo, center_hi, w_min > 0, w_max) per variable; centers padded ~50%
# beyond the hand spans, widths bounded away from zero (tri() divides by w).
# D-04a (2026-09-27): du/dv centers span the full [-1,1] defuzz grid so the
# GA can reach bang-bang authority; inputs and widths unchanged.
BOUNDS = {
    "eT": (-6.0, 6.0, 0.2, 6.0),
    "deT": (-0.75, 0.75, 0.025, 0.75),
    "du": (-1.0, 1.0, 0.005, 0.15),
    "eH": (-40.0, 40.0, 1.5, 40.0),
    "deH": (-9.0, 9.0, 0.3, 9.0),
    "dv": (-1.0, 1.0, 0.005, 0.15),
}

W1, W2, W3 = 1.0, 1.0, 0.01  # D-01 locked fitness weights

# D-06/A2: cross-coupling gains appended to the chromosome AFTER the 60 MF
# genes. k_heat/k_vent are duty-per-%RH-excess boosts applied to heater and
# vent AFTER the untouched decoupled velocity loops. Zero gains == decoupled
# (hand-equivalent), so individual 0 stays never-worse-than-hand.
COUPLING_KEYS = ("k_heat", "k_vent")
COUPLING_BOUNDS = {"k_heat": (0.0, 0.05), "k_vent": (0.0, 0.05)}
N_COUPLING = len(COUPLING_KEYS)

CHROM_LEN = 60 + N_COUPLING  # 62
N_STEPS = 1440
DT = 60.0


def _sigmas():
    """Per-gene mutation sigma = 0.1 * allowed range (centers, widths, gains)."""
    sig = np.zeros(CHROM_LEN)
    i = 0
    for k in ORDER:
        lo, hi, wmin, wmax = BOUNDS[k]
        sig[i:i + 5] = 0.1 * (hi - lo)
        i += 5
        sig[i:i + 5] = 0.1 * (wmax - wmin)
        i += 5
    for k in COUPLING_KEYS:  # mechanical extension: same 0.1 * range rule
        lo, hi = COUPLING_BOUNDS[k]
        sig[i] = 0.1 * (hi - lo)
        i += 1
    return sig


SIGMAS = _sigmas()


def encode(mfs, gains=None):
    """MF dict (+ optional gains) -> flat 62-element float vector.

    Layout: 5 centers then 5 widths per group in ORDER, then k_heat, k_vent.
    gains=None means zeros (hand-equivalent: coupled == decoupled).
    """
    assert set(mfs) == set(ORDER), f"MF keys must be exactly {ORDER}"
    parts = []
    for k in ORDER:
        c = np.asarray(mfs[k]["centers"], dtype=float)
        w = np.asarray(mfs[k]["widths"], dtype=float)
        assert c.shape == (5,) and w.shape == (5,), f"group {k} must be len-5"
        assert np.all(np.isfinite(c)) and np.all(np.isfinite(w))
        parts.append(c)
        parts.append(w)
    g = np.zeros(N_COUPLING) if gains is None else np.asarray(
        [gains[k] for k in COUPLING_KEYS], dtype=float)
    assert g.shape == (N_COUPLING,) and np.all(np.isfinite(g)), g
    parts.append(g)
    return np.concatenate(parts).astype(float)


def decode(chrom):
    """62-element vector -> (fresh repaired MF dict, fresh gains dict).

    Accepts len-60 (legacy decoupled: gains default to 0.0) or len-62.
    Sort+clip repair on centers/widths; gains clipped into COUPLING_BOUNDS.
    Never returns views; never touches the FUZZY_MFS global.
    """
    chrom = np.asarray(chrom, dtype=float)
    assert chrom.shape in ((60,), (CHROM_LEN,)), \
        f"chromosome must be len-60 (legacy) or len-{CHROM_LEN}"
    mfs, i = {}, 0
    for k in ORDER:
        lo, hi, wmin, wmax = BOUNDS[k]
        c = np.sort(np.clip(chrom[i:i + 5], lo, hi))
        i += 5
        w = np.clip(chrom[i:i + 5], wmin, wmax)
        i += 5
        mfs[k] = {"centers": np.array(c), "widths": np.array(w)}
    gains = {}
    for j, k in enumerate(COUPLING_KEYS):
        lo, hi = COUPLING_BOUNDS[k]
        raw = float(chrom[i + j]) if chrom.shape == (CHROM_LEN,) else 0.0
        gains[k] = float(np.clip(raw, lo, hi))
    return mfs, gains


def apply_coupling(act, rh_pct, RH_sp, gains):
    """Humidity-driven heater/vent boost AFTER the decoupled velocity loops.

    boost = k * max(0, rh - RH_sp); duties re-clipped to [0, 1], exact
    4-key dict preserved. Zero gains return the input duties unchanged.
    Canonical shared helper: the fitness loop AND ga_fuzzy_controller use it.
    """
    assert set(act) == {"heater", "fan_cooler", "fogger", "vent"}
    assert np.isfinite(rh_pct) and np.isfinite(RH_sp)
    excess = max(0.0, float(rh_pct) - float(RH_sp))  # %RH above setpoint
    out = dict(act)
    out["heater"] = float(np.clip(act["heater"]
                                  + gains["k_heat"] * excess, 0.0, 1.0))
    out["vent"] = float(np.clip(act["vent"]
                                + gains["k_vent"] * excess, 0.0, 1.0))
    assert set(out) == {"heater", "fan_cooler", "fogger", "vent"}
    assert all(np.isfinite(v) and 0.0 <= v <= 1.0 for v in out.values())
    return out


def coupled_fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None,
                       dt=60.0, mfs=FUZZY_MFS, gains=None):
    """Same engine call as hand fuzzy, then the A2 coupling boost.

    The decoupled velocity loops (fuzzy_step) are untouched; state handling
    is theirs. gains=None means zeros (bit-identical to fuzzy_step).
    """
    g = {"k_heat": 0.0, "k_vent": 0.0} if gains is None else gains
    act, st = fuzzy_step(T_C, rh_pct, T_sp, RH_sp, state, dt, mfs)
    return apply_coupling(act, rh_pct, RH_sp, g), st


def closed_loop_breakdown(mfs, T_out_hr, w_out_hr, hours,
                           T_sp=25.0, RH_sp=70.0, gains=None):
    """Full 1440-step closed loop -> (IAE_T, IAE_H, duty-hours energy E).

    Runs the COUPLED path (D-06/A2): decoupled velocity loops first, then
    the humidity-driven heater/vent boost. gains=None == hand decoupled.

    Energy definition (locked here, Phase 5 metrics.py must be identical):
    E = sum over steps of (sum over actuators of duty) / 60  [duty-hours].
    """
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st, iae_T, iae_H, E = None, 0.0, 0.0, 0.0
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = coupled_fuzzy_step(T, rh, T_sp, RH_sp, st, DT, mfs, gains)
        T, w, rh = step(DT, act,
                        (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"])),
                        T, w)
        iae_T += abs(T - T_sp) / 60.0
        iae_H += abs(rh - RH_sp) / 60.0
        E += sum(act.values()) / 60.0  # duty-hours
    return iae_T, iae_H, E


def evaluate(chrom, T_out_hr, w_out_hr, hours, T_sp=25.0, RH_sp=70.0):
    """Fitness: W1*IAE_T + W2*IAE_H + W3*E (coupled path). Never raises."""
    try:
        mfs, gains = decode(chrom)
        iae_T, iae_H, E = closed_loop_breakdown(mfs, T_out_hr, w_out_hr,
                                                hours, T_sp, RH_sp, gains)
        cost = W1 * iae_T + W2 * iae_H + W3 * E
        assert np.isfinite(cost)
        return float(cost)
    except Exception:
        return float("inf")


fitness = evaluate  # alias: the plan names it "fitness", code calls evaluate


def tournament_select(pop, fit, rng, k=3):
    """Best of k randomly drawn individuals (copy, never a view)."""
    k = min(k, len(pop))
    idx = rng.choice(len(pop), size=k, replace=False)
    return pop[idx[np.argmin(fit[idx])]].copy()


def blx_alpha(p1, p2, rng, alpha=0.5):
    """BLX-alpha blend crossover; MF repair applied later in decode()."""
    d = np.abs(p1 - p2)
    lo = np.minimum(p1, p2) - alpha * d
    hi = np.maximum(p1, p2) + alpha * d
    return rng.uniform(lo, hi)


def gaussian_mutate(child, rng, p_gene=1.0 / 60.0, sigmas=SIGMAS):
    """Per-gene gaussian mutation, sigma 0.1 * gene range."""
    mask = rng.random(child.size) < p_gene
    child[mask] += rng.normal(0.0, 1.0, int(mask.sum())) * sigmas[mask]
    return child


def init_population(rng, n):
    """Individual 0 = exact hand encoding + ZERO gains (hand-equivalent).

    Rest = hand * (1 + U(-0.2, 0.2)) on MF genes (mechanical as before);
    gains drawn U(lo, hi) so the population explores coupling from gen 0
    (hand-scaled jitter would pin every gain at exactly 0.0).
    """
    hand = encode(FUZZY_MFS)
    pop = np.empty((n, CHROM_LEN))
    pop[0] = hand
    for i in range(1, n):
        pop[i, :60] = hand[:60] * (1.0 + rng.uniform(-0.2, 0.2, 60))
        for j, k in enumerate(COUPLING_KEYS):
            lo, hi = COUPLING_BOUNDS[k]
            pop[i, 60 + j] = rng.uniform(lo, hi)
    return pop


def _write_json(path, mfs_lists, gains_lists, best_fit, weights, train_weather,
                train_seed, holdout_seed, population, generations, rng_seed,
                hist_best, hist_mean):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"mfs": mfs_lists, "coupling": gains_lists,
                   "fitness": best_fit, "weights": weights,
                   "train_weather": train_weather, "train_seed": train_seed,
                   "holdout_seed": holdout_seed, "population": population,
                   "generations": generations, "rng_seed": rng_seed,
                   "schema_version": 2,  # A2: adds "coupling" (Phase 5/7: read it)
                   "history": {"best": hist_best, "mean": hist_mean}}, f)


def _mfs_to_lists(mfs):
    return {k: {"centers": [float(x) for x in mfs[k]["centers"]],
                "widths": [float(x) for x in mfs[k]["widths"]]} for k in ORDER}


def _gains_to_lists(gains):
    return {k: float(gains[k]) for k in COUPLING_KEYS}


def run_ga(population=50, generations=50, rng_seed=0,
           train_weather="weather/weather_profile.csv", train_seed=7,
           holdout_seed=21, out_path="results/ga_optimized_params.json"):
    """Seeded elitism-2 generational GA; flushes best-so-far JSON every gen."""
    rng = np.random.default_rng(rng_seed)  # single RNG: every draw via rng
    t_min, T_out, w_out = load_weather_profile(train_weather)
    hours = np.arange(0, N_STEPS) / 60.0
    T_out_hr = np.interp(hours, t_min, T_out)
    w_out_hr = np.interp(hours, t_min, w_out)

    pop = init_population(rng, population)
    n_elite = min(2, population)
    fit = np.array([evaluate(c, T_out_hr, w_out_hr, hours) for c in pop])
    hist_best, hist_mean = [], []
    order = np.argsort(fit)
    best_idx, best_fit = int(order[0]), float(fit[order[0]])
    best_chrom = pop[best_idx].copy()

    for _ in range(generations):
        hist_best.append(float(best_fit))
        hist_mean.append(float(np.mean(fit[np.isfinite(fit)])))
        _bm, _bg = decode(best_chrom)
        _write_json(out_path, _mfs_to_lists(_bm), _gains_to_lists(_bg),
                    best_fit, {"w1": W1, "w2": W2, "w3": W3}, train_weather,
                    train_seed, holdout_seed, population, generations,
                    rng_seed, list(hist_best), list(hist_mean))
        order = np.argsort(fit)
        if float(fit[order[0]]) < best_fit:
            best_fit = float(fit[order[0]])
            best_chrom = pop[order[0]].copy()
        new_pop = [pop[o].copy() for o in order[:n_elite]]
        while len(new_pop) < population:
            p1 = tournament_select(pop, fit, rng)
            p2 = tournament_select(pop, fit, rng)
            child = gaussian_mutate(blx_alpha(p1, p2, rng), rng)
            new_pop.append(child)
        pop = np.array(new_pop)
        elite_fit = [float(fit[o]) for o in order[:n_elite]]
        offspring_fit = [evaluate(c, T_out_hr, w_out_hr, hours)
                         for c in pop[n_elite:]]
        fit = np.array(elite_fit + offspring_fit)
        order = np.argsort(fit)
        if float(fit[order[0]]) < best_fit:
            best_fit = float(fit[order[0]])
            best_chrom = pop[order[0]].copy()

    hist_best.append(float(best_fit))
    hist_mean.append(float(np.mean(fit[np.isfinite(fit)])))
    # keep history length == generations (drop the pre-gen-0 entry)
    hist_best, hist_mean = hist_best[1:], hist_mean[1:]
    _bm, _bg = decode(best_chrom)
    _write_json(out_path, _mfs_to_lists(_bm), _gains_to_lists(_bg), best_fit,
                {"w1": W1, "w2": W2, "w3": W3}, train_weather, train_seed,
                holdout_seed, population, generations, rng_seed,
                hist_best, hist_mean)
    return {"best_chrom": best_chrom, "best_fit": best_fit,
            "best_gains": dict(_bg),
            "history": {"best": hist_best, "mean": hist_mean}}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Evolve fuzzy MFs (50x50 default).")
    ap.add_argument("--population", type=int, default=50)
    ap.add_argument("--generations", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--train-weather", default="weather/weather_profile.csv")
    ap.add_argument("--out", default="results/ga_optimized_params.json")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    res = run_ga(population=a.population, generations=a.generations,
                 rng_seed=a.seed, train_weather=a.train_weather,
                 out_path=a.out)
    print(f"best fitness {res['best_fit']:.3f} -> {a.out}")
