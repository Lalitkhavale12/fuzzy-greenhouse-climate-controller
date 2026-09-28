"""GA Explorer page — frozen-artifact exhibit (D-02).

Convergence + membership before/after + elite params from
results/ga_optimized_params.json ONLY. MFs come through the validated
load_optimized_mfs loader; raw json touches history/coupling/scalars.
No evolution code anywhere on this page.

Run:  python -m streamlit run dashboard/app.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import matplotlib.pyplot as plt

import streamlit as st

from src.fuzzy_controller import FUZZY_MFS, tri
from src.ga_fuzzy_controller import load_optimized_mfs

JSON_PATH = "results/ga_optimized_params.json"

st.title("GA Explorer — frozen tuned artifact")

mfs_opt, gains_opt = load_optimized_mfs(JSON_PATH)
with open(JSON_PATH) as _f:
    d = json.load(_f)
assert d["schema_version"] == 2, "stale artifact: schema_version != 2"
best = d["history"]["best"]
mean = d["history"]["mean"]

st.subheader("Elite params")
st.metric("train fitness", "%.2f" % d["fitness"])
st.metric("coupling k_heat", "%.3f" % d["coupling"]["k_heat"])
st.metric("coupling k_vent", "%.3f" % d["coupling"]["k_vent"])
st.dataframe([{"population": d["population"], "generations": d["generations"],
               "train_seed": d["train_seed"], "holdout_seed": d["holdout_seed"],
               "weights": str(d["weights"])}])

st.subheader("Convergence (50 generations)")
fig, ax = plt.subplots(figsize=(10, 4))
gens = range(1, len(best) + 1)
ax.plot(gens, best, label="best")
ax.plot(gens, mean, label="mean", alpha=0.7)
ax.set_xlabel("generation")
ax.set_ylabel("train weighted cost")
ax.set_title("GA convergence (50x50, train seed-7)")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
st.pyplot(fig)

st.subheader("Membership before/after: hand solid vs GA dashed")
MF_KEYS = ["eT", "eH"]
extra = st.selectbox("extra group", ["deT", "du", "deH", "dv"], index=0)
MF_KEYS = MF_KEYS + [extra]
fig2, axes = plt.subplots(1, 3, figsize=(15, 4))
for a, key in zip(axes, MF_KEYS):
    hand_c = FUZZY_MFS[key]["centers"]
    hand_w = FUZZY_MFS[key]["widths"]
    opt_c = mfs_opt[key]["centers"]
    opt_w = mfs_opt[key]["widths"]
    lo = float(min(hand_c.min(), opt_c.min()) - max(hand_w.max(), opt_w.max()))
    hi = float(max(hand_c.max(), opt_c.max()) + max(hand_w.max(), opt_w.max()))
    grid = np.linspace(lo, hi, 400)
    for c, w in zip(hand_c, hand_w):
        a.plot(grid, [tri(x, c, w) for x in grid], "C0-", alpha=0.5)
    for c, w in zip(opt_c, opt_w):
        a.plot(grid, [tri(x, c, w) for x in grid], "C1--", alpha=0.8)
    a.plot([], [], "C0-", label="hand %s" % key)
    a.plot([], [], "C1--", label="GA %s" % key)
    a.set_title("MF before/after: %s" % key)
    a.legend(fontsize=8)
    a.grid(alpha=0.3)
fig2.suptitle("coupling k_heat/k_vent = %.3f/%.3f"
              % (gains_opt["k_heat"], gains_opt["k_vent"]))
fig2.tight_layout()
st.pyplot(fig2)
