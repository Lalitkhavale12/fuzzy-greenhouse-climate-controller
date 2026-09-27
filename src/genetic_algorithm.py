"""Real-valued GA tuning the fuzzy membership functions (GA-01..04).

60-D chromosome = 6 MF groups in ORDER x (5 centers + 5 widths). Decode
repairs every chromosome (sort clipped centers, clip widths into
[w_min, w_max] with w_min > 0) and allocates fresh dicts/arrays, so the
FUZZY_MFS global is never touched. Fitness is the locked weighted cost
1.0*IAE_T + 1.0*IAE_H + 0.01*duty-hours-energy via the full 1440-step
closed loop, never raising (bad chromosome -> +inf). Operators:
tournament-3, BLX-0.5, per-gene gaussian mutation, elitism-2, all draws
through the single default_rng owned by run_ga. Individual 0 is the exact
hand FUZZY_MFS encoding, so the GA never returns worse than hand fuzzy.

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

CHROM_LEN = 60
N_STEPS = 1440
DT = 60.0


def _sigmas():
    """Per-gene mutation sigma = 0.1 * allowed range (centers and widths)."""
    sig = np.zeros(CHROM_LEN)
    i = 0
    for k in ORDER:
        lo, hi, wmin, wmax = BOUNDS[k]
        sig[i:i + 5] = 0.1 * (hi - lo)
        i += 5
        sig[i:i + 5] = 0.1 * (wmax - wmin)
        i += 5
    return sig


SIGMAS = _sigmas()


def encode(mfs):
    """MF dict -> flat 60-element float vector (5 centers then 5 widths/group)."""
    assert set(mfs) == set(ORDER), f"MF keys must be exactly {ORDER}"
    parts = []
    for k in ORDER:
        c = np.asarray(mfs[k]["centers"], dtype=float)
        w = np.asarray(mfs[k]["widths"], dtype=float)
        assert c.shape == (5,) and w.shape == (5,), f"group {k} must be len-5"
        assert np.all(np.isfinite(c)) and np.all(np.isfinite(w))
        parts.append(c)
        parts.append(w)
    return np.concatenate(parts).astype(float)


def decode(chrom):
    """60-element vector -> fresh repaired MF dict (sort+clip, never views)."""
    chrom = np.asarray(chrom, dtype=float)
    assert chrom.shape == (CHROM_LEN,), f"chromosome must be len-{CHROM_LEN}"
    mfs, i = {}, 0
    for k in ORDER:
        lo, hi, wmin, wmax = BOUNDS[k]
        c = np.sort(np.clip(chrom[i:i + 5], lo, hi))
        i += 5
        w = np.clip(chrom[i:i + 5], wmin, wmax)
        i += 5
        mfs[k] = {"centers": np.array(c), "widths": np.array(w)}
    return mfs


def closed_loop_breakdown(mfs, T_out_hr, w_out_hr, hours,
                          T_sp=25.0, RH_sp=70.0):
    """Full 1440-step closed loop -> (IAE_T, IAE_H, duty-hours energy E).

    Energy definition (locked here, Phase 5 metrics.py must be identical):
    E = sum over steps of (sum over actuators of duty) / 60  [duty-hours].
    """
    T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
    st, iae_T, iae_H, E = None, 0.0, 0.0, 0.0
    for i, h in enumerate(hours):
        rh = relative_humidity(w, T)
        act, st = fuzzy_step(T, rh, T_sp, RH_sp, st, DT, mfs)
        T, w, rh = step(DT, act,
                        (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"])),
                        T, w)
        iae_T += abs(T - T_sp) / 60.0
        iae_H += abs(rh - RH_sp) / 60.0
        E += sum(act.values()) / 60.0  # duty-hours
    return iae_T, iae_H, E


def evaluate(chrom, T_out_hr, w_out_hr, hours, T_sp=25.0, RH_sp=70.0):
    """Fitness: W1*IAE_T + W2*IAE_H + W3*E. Never raises (bad chrom -> inf)."""
    try:
        mfs = decode(chrom)
        iae_T, iae_H, E = closed_loop_breakdown(mfs, T_out_hr, w_out_hr,
                                               hours, T_sp, RH_sp)
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
    """Individual 0 = exact hand encoding; rest = hand * (1 + U(-0.2, 0.2))."""
    hand = encode(FUZZY_MFS)
    pop = np.empty((n, CHROM_LEN))
    pop[0] = hand
    for i in range(1, n):
        pop[i] = hand * (1.0 + rng.uniform(-0.2, 0.2, CHROM_LEN))
    return pop


def _write_json(path, mfs_lists, best_fit, weights, train_weather, train_seed,
                holdout_seed, population, generations, rng_seed, hist_best,
                hist_mean):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"mfs": mfs_lists, "fitness": best_fit, "weights": weights,
                   "train_weather": train_weather, "train_seed": train_seed,
                   "holdout_seed": holdout_seed, "population": population,
                   "generations": generations, "rng_seed": rng_seed,
                   "history": {"best": hist_best, "mean": hist_mean}}, f)


def _mfs_to_lists(mfs):
    return {k: {"centers": [float(x) for x in mfs[k]["centers"]],
                "widths": [float(x) for x in mfs[k]["widths"]]} for k in ORDER}


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
        _write_json(out_path, _mfs_to_lists(decode(best_chrom)), best_fit,
                    {"w1": W1, "w2": W2, "w3": W3}, train_weather, train_seed,
                    holdout_seed, population, generations, rng_seed,
                    list(hist_best), list(hist_mean))
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
    _write_json(out_path, _mfs_to_lists(decode(best_chrom)), best_fit,
                {"w1": W1, "w2": W2, "w3": W3}, train_weather, train_seed,
                holdout_seed, population, generations, rng_seed,
                hist_best, hist_mean)
    return {"best_chrom": best_chrom, "best_fit": best_fit,
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
