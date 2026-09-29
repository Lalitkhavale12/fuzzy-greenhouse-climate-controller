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
from dashboard.helpers import fig_to_png_bytes

JSON_PATH = "results/ga_optimized_params.json"

st.title("GA Explorer — frozen tuned artifact")

try:
    mfs_opt, gains_opt = load_optimized_mfs(JSON_PATH)
    with open(JSON_PATH) as _f:
        d = json.load(_f)
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen GA artifact unreadable: %s" % exc)
    st.stop()
if not (d.get("schema_version") == 2):
    st.error("stale artifact: schema_version != 2")
    st.stop()
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
fig.patch.set_facecolor("#F7FAF3")  # explicit light figure (theme never touches mpl)
ax.set_facecolor("#FFFFFF")  # explicit light axes, default C-series data colors
ax.tick_params(colors="#263023")
gens = range(1, len(best) + 1)
ax.plot(gens, best, label="best")
ax.plot(gens, mean, label="mean", alpha=0.7)
ax.set_xlabel("generation")
ax.set_ylabel("train weighted cost")
ax.set_title("GA convergence (%dx%d, train seed-%d)"
              % (d["population"], d["generations"], d["train_seed"]))
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
st.download_button("Download convergence chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="ga_convergence.png", mime="image/png")
st.pyplot(fig)

st.subheader("Membership before/after: hand solid vs GA dashed")
MF_KEYS = ["eT", "eH"]
extra = st.selectbox("extra group", ["deT", "du", "deH", "dv"], index=0)
MF_KEYS = MF_KEYS + [extra]
fig2, axes = plt.subplots(1, 3, figsize=(15, 4))
fig2.patch.set_facecolor("#F7FAF3")  # explicit light figure (theme never touches mpl)
for _a in axes:
    _a.set_facecolor("#FFFFFF")  # explicit light axes, default C-series data colors
    _a.tick_params(colors="#263023")
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
st.download_button("Download MF chart (PNG)", data=fig_to_png_bytes(fig2),
                   file_name="ga_mfs.png", mime="image/png")
st.pyplot(fig2)
