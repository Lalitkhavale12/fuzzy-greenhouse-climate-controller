"""GA-optimized fuzzy controller (GA-05): same engine, JSON-loaded MFs.

Thin wrapper over fuzzy_step: load_optimized_mfs validates the artifact
schema fail-fast (exact key set, len-5 float lists, widths > 0, all finite)
and ga_fuzzy_step delegates bit-identically to fuzzy_step(mfs=_MFS).

Pure and stateless: caller owns the state dict; state=None means fresh
{'pT', 'pH', 'uT', 'uH'}. JSON-only via stdlib json (never pickle/eval).
"""

import json
import os

import numpy as np

try:
    from src.fuzzy_controller import fuzzy_step
except ImportError:  # `python src/...` puts src/ on sys.path
    from fuzzy_controller import fuzzy_step

KEYS = ("eT", "deT", "du", "eH", "deH", "dv")
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "results", "ga_optimized_params.json")

_MFS = None
_MFS_PATH = None


def load_optimized_mfs(path=DEFAULT_PATH):
    """Load + validate artifact -> MF dict of arrays (lazily cached per path)."""
    global _MFS, _MFS_PATH
    apath = os.path.abspath(path)
    if _MFS is not None and _MFS_PATH == apath:
        return _MFS
    with open(path) as f:
        d = json.load(f)
    assert set(d["mfs"]) == set(KEYS), f"mfs keys must be exactly {KEYS}"
    mfs = {}
    for k in KEYS:
        c, w = d["mfs"][k]["centers"], d["mfs"][k]["widths"]
        assert len(c) == 5 and len(w) == 5, f"group {k} must be len-5"
        assert all(isinstance(x, float) for x in c + w), f"group {k} floats only"
        assert all(np.isfinite(c)) and all(np.isfinite(w)), f"group {k} finite"
        assert all(x > 0.0 for x in w), f"group {k} widths above zero"
        mfs[k] = {"centers": np.array(c), "widths": np.array(w)}
    _MFS, _MFS_PATH = mfs, apath
    return _MFS


def ga_fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0,
                  path=DEFAULT_PATH):
    """GA fuzzy: identical signature/contract to fuzzy_step, tuned MFs."""
    assert np.isfinite(T_C) and np.isfinite(rh_pct)
    assert np.isfinite(T_sp) and np.isfinite(RH_sp)
    assert np.isfinite(dt) and dt > 0
    mfs = load_optimized_mfs(path)
    return fuzzy_step(T_C, rh_pct, T_sp, RH_sp, state, dt, mfs)
