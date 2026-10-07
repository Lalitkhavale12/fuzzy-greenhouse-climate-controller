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
from dashboard.helpers import fig_to_png_bytes, scratch_mfs_from_deltas, \
    tloop_response_curve, build_explorer_figure, replay_slice, \
    build_replay_figure, GEN_COUNT, DISPLAY, load_kpi_row, \
    mf_sensitivity_costs, build_sensitivity_figure, rule_table, rule_firing

JSON_PATH = "results/ga_optimized_params.json"

st.title("GA Explorer — frozen tuned artifact")

try:
    kpi = load_kpi_row()
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen scoreboard unreadable: %s" % exc)
    st.stop()
c1, c2, c3, c4 = st.columns(4)
c1.metric("%s holdout cost" % DISPLAY["ga_fuzzy"],
          "%.2f" % float(kpi["cost"]))
c2.metric("%s holdout rank" % DISPLAY["ga_fuzzy"], "#%s" % kpi["rank"])
c3.metric("IAE_T", "%.2f" % float(kpi["iae_T"]))
c4.metric("IAE_H", "%.2f" % float(kpi["iae_H"]))

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

st.subheader("MF explorer: drag T-loop centers (scratch vs frozen)")
hand_eT = [float(c) for c in FUZZY_MFS["eT"]["centers"]]
hand_du = [float(c) for c in FUZZY_MFS["du"]["centers"]]
eT_gap = float(min(np.diff(sorted(hand_eT))) / 2.0)
du_gap = float(min(np.diff(sorted(hand_du))) / 2.0)
ecols = st.columns(2)
eT_vals = [ecols[0].slider("eT[%d] center" % i, c - eT_gap, c + eT_gap, c, 0.1)
           for i, c in enumerate(hand_eT)]
du_vals = [ecols[1].slider("du[%d] center" % i, c - du_gap, c + du_gap, c, 0.005)
           for i, c in enumerate(hand_du)]
reset = st.button("Preview frozen this render")
if reset:  # one-render preview (WR-02): recompute scratch from hand centers
    # for this render only — sliders keep their values (no session_state
    # by lock), so dragged values flow back on the next rerun.
    eT_vals = list(hand_eT)
    du_vals = list(hand_du)
scratch, drag_warnings = scratch_mfs_from_deltas(eT_vals, du_vals)
for _w in drag_warnings:
    st.warning(_w)
grid, hand_vals = tloop_response_curve(FUZZY_MFS)
_, scratch_vals = tloop_response_curve(scratch)
if not (bool(np.all(np.isfinite(hand_vals)))
        and bool(np.all(np.isfinite(scratch_vals)))):
    st.warning("response sweep non-finite -- showing curves as computed")
dev_max = float(np.abs(scratch_vals - hand_vals).max())
dev_mean = float(np.abs(scratch_vals - hand_vals).mean())
st.metric("surface deviation max-abs (duty units, not closed-loop cost)",
          "%.4f" % dev_max)
st.metric("surface deviation mean-abs (duty units)", "%.4f" % dev_mean)
fig3 = build_explorer_figure(grid, hand_vals, scratch_vals)
st.download_button("Download explorer response (PNG)",
                   data=fig_to_png_bytes(fig3),
                   file_name="ga_explorer_response.png", mime="image/png")
st.pyplot(fig3)

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

st.subheader("Convergence replay (scrub generations)")
gen = st.slider("generation", 1, GEN_COUNT, GEN_COUNT, 1)
g, g_best, _g_mean = replay_slice(gen, best, mean)  # mean shown in figure
st.metric("replay readout", "gen %d/%d · best %.2f" % (g, GEN_COUNT, g_best))
fig_r = build_replay_figure(best, mean, g)
st.download_button("Download replay chart (PNG)", data=fig_to_png_bytes(fig_r),
                   file_name="ga_convergence_replay.png", mime="image/png")
st.pyplot(fig_r)

st.subheader("MF sensitivity: closed-loop cost per center shift")
if st.checkbox("Run sensitivity (10 closed-loop runs, cached)"):
    sens_base, sens_rows = mf_sensitivity_costs()
    st.metric("hand-fuzzy baseline cost (seed 7)", "%.2f" % sens_base)
    st.dataframe([{"param": lab, "dcost": dc} for lab, dc in sens_rows])
    sens_fig = build_sensitivity_figure(sens_rows)
    st.download_button("Download sensitivity (PNG)",
                       data=fig_to_png_bytes(sens_fig),
                       file_name="ga_sensitivity.png", mime="image/png")
    st.pyplot(sens_fig)

st.subheader("Rule base explorer: 5x5 consequents + live firing")
st.dataframe(rule_table())
re_err = st.slider("probe error e", -6.0, 6.0, 0.0, 0.5)
re_rate = st.slider("probe error-rate de", -0.75, 0.75, 0.0, 0.05)
fire = rule_firing(re_err, re_rate)
st.dataframe([["%.2f" % v for v in row] for row in fire])
_flat = [(fire[i][j], i, j) for i in range(5) for j in range(5)]
_best, _bi, _bj = max(_flat)
st.metric("winning rule", "e=%s de=%s -> %s (%.2f)"
          % (["NB", "NS", "ZO", "PS", "PB"][_bi],
             ["NB", "NS", "ZO", "PS", "PB"][_bj],
             rule_table()[_bi + 1][_bj + 1], _best))

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

with st.expander("Provenance"):
    st.write("GA artifact: results/ga_optimized_params.json (schema v2, "
             "50 generations). "
             "Scoreboard: results/comparison.csv (8 rows, frozen). "
             "Seeds 7/21, weights 1.0/1.0/0.01.")
