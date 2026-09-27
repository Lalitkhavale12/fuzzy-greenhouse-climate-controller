"""GA-optimized fuzzy controller (GA-05 + D-06/A2): coupled engine, JSON MFs.

Thin wrapper over fuzzy_step: load_optimized_mfs validates the artifact
schema fail-fast (exact MF key set, len-5 float lists, widths > 0, all
finite, plus the A2 "coupling" gains) and ga_fuzzy_step runs the same
engine call as hand fuzzy followed by the humidity-driven heater/vent
boost shared with the fitness loop (apply_coupling in genetic_algorithm).

Pure and stateless: caller owns the state dict; state=None means fresh
{'pT', 'pH', 'uT', 'uH'}. JSON-only via stdlib json (never pickle/eval).
"""

import copy
import json
import os

import numpy as np

try:
    from src.fuzzy_controller import fuzzy_step
    from src.genetic_algorithm import apply_coupling, COUPLING_BOUNDS
except ImportError:  # `python src/...` puts src/ on sys.path
    from fuzzy_controller import fuzzy_step
    from genetic_algorithm import apply_coupling, COUPLING_BOUNDS

KEYS = ("eT", "deT", "du", "eH", "deH", "dv")
COUPLING_KEYS = ("k_heat", "k_vent")
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "results", "ga_optimized_params.json")

_MFS = None
_GAINS = None
_MFS_PATH = None
_MFS_MTIME = None


def load_optimized_mfs(path=DEFAULT_PATH):
    """Load + validate artifact -> (MF dict of arrays, gains dict).

    Schema v2 (A2): "mfs" (six groups) + "coupling" {k_heat, k_vent}.
    Schema v1 (no "coupling" key: run-1/run-2 JSONs) still loads with zero
    gains (hand-equivalent decoupled). Cached per path + mtime (IN-04: a
    rewritten artifact reloads); returns defensive deep copies so callers
    cannot mutate the cache.
    """
    global _MFS, _GAINS, _MFS_PATH, _MFS_MTIME
    apath = os.path.abspath(path)
    mtime = os.path.getmtime(apath)
    if _MFS is not None and _MFS_PATH == apath and _MFS_MTIME == mtime:
        return copy.deepcopy(_MFS), copy.deepcopy(_GAINS)
    with open(path) as f:
        d = json.load(f)
    assert isinstance(d.get("mfs"), dict), "artifact must hold an 'mfs' dict"
    assert isinstance(d.get("coupling", {}), dict), "artifact 'coupling' must be a dict"
    assert set(d["mfs"]) == set(KEYS), f"mfs keys must be exactly {KEYS}"
    mfs = {}
    for k in KEYS:
        c, w = d["mfs"][k]["centers"], d["mfs"][k]["widths"]
        assert len(c) == 5 and len(w) == 5, f"group {k} must be len-5"
        assert all(isinstance(x, (int, float)) and not isinstance(x, bool)
                   for x in c + w), f"group {k} numbers only"
        assert all(np.isfinite(c)) and all(np.isfinite(w)), f"group {k} finite"
        assert all(x > 0.0 for x in w), f"group {k} widths above zero"
        mfs[k] = {"centers": np.array(c, dtype=float),
                  "widths": np.array(w, dtype=float)}
    gains = {}
    for k in COUPLING_KEYS:  # T-04-01 extended: fail-fast on coupling too
        v = d.get("coupling", {}).get(k, 0.0)
        assert isinstance(v, (int, float)) and not isinstance(v, bool), \
            f"coupling {k} number"
        v = float(v)
        assert np.isfinite(v), f"coupling {k} finite"
        lo, hi = COUPLING_BOUNDS[k]
        assert lo <= v <= hi, f"coupling {k} in [{lo}, {hi}]"
        gains[k] = v
    _MFS, _GAINS, _MFS_PATH, _MFS_MTIME = mfs, gains, apath, mtime
    return copy.deepcopy(_MFS), copy.deepcopy(_GAINS)


def ga_fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0,
                  path=DEFAULT_PATH):
    """GA fuzzy: same engine call as hand fuzzy, then the A2 coupling boost."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    mfs, gains = load_optimized_mfs(path)
    act, st = fuzzy_step(T_C, rh_pct, T_sp, RH_sp, state, dt, mfs)
    return apply_coupling(act, rh_pct, RH_sp, gains), st
