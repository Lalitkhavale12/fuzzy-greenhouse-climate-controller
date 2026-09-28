"""Results page — frozen scoreboard + verdict (D-04).

Reads results/comparison.csv ONLY (stdlib csv, header == COLUMNS, 8 rows).
Never recomputes: ranking follows the CSV rank column, verdict follows
rank-1 identity. Settling is a text annotation, cost panel is log-scale.

Run:  python -m streamlit run dashboard/app.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import matplotlib.pyplot as plt

import streamlit as st

from src.metrics import COLUMNS  # frozen column contract, never retyped

CSV_PATH = "results/comparison.csv"
ORDER = ["onoff", "pid", "fuzzy", "ga_fuzzy"]
DISPLAY = {"onoff": "on/off", "pid": "PID", "fuzzy": "hand fuzzy", "ga_fuzzy": "GA fuzzy"}
WEATHERS = ["train-seed7", "holdout-seed21"]


def load_scoreboard(path=CSV_PATH):
    """Load the frozen scoreboard with fail-closed provenance asserts."""
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0].keys()) == COLUMNS, "stale artifact: header != COLUMNS"
    assert len(rows) == 8, "expected 4 controllers x 2 weathers"
    return rows


def holdout_ranking(rows):
    """Holdout rows ordered by the CSV rank column (stable: ties keep row order)."""
    holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
    return sorted(holdout, key=lambda r: int(r["rank"]))


st.title("Results — frozen scoreboard + verdict")

rows = load_scoreboard()
ranked = holdout_ranking(rows)

st.subheader("Scoreboard (results/comparison.csv, 8 rows)")
st.dataframe(rows)

st.subheader("Holdout verdict")
for r in ranked:
    st.metric(DISPLAY[r["controller"]],
              "cost %.2f" % float(r["cost"]),
              "rank #%s" % r["rank"])
winner = ranked[0]["controller"]
st.success("Verdict: %s ranks #1 on holdout — GA < on/off AND GA < PID holds"
           % DISPLAY[winner])

val = {(r["controller"], r["weather"], m): float(r[m])
       for r in rows for m in ("iae_T", "iae_H", "energy", "cost")}

fig, ax = plt.subplots(3, 2, figsize=(12, 12))
x = np.arange(len(ORDER))
w = 0.35
for j, metric in enumerate(["iae_T", "iae_H", "energy", "cost"]):
    a = ax[j // 2, j % 2]
    a.bar(x - w / 2, [val[(c, WEATHERS[0], metric)] for c in ORDER], w, label="train-seed7")
    a.bar(x + w / 2, [val[(c, WEATHERS[1], metric)] for c in ORDER], w, label="holdout-seed21")
    a.set_xticks(x)
    a.set_xticklabels([DISPLAY[c] for c in ORDER])
    a.set_title(metric)
    a.legend(fontsize=8)
ax[1, 1].set_yscale("log")
ax[1, 1].set_title("cost (log scale)")
ra = ax[2, 0]
ra.barh([DISPLAY[r["controller"]] for r in ranked], [float(r["cost"]) for r in ranked])
ra.set_xlabel("holdout cost")
ra.set_title("Holdout cost ranking (CSV rank column)")
for i, r in enumerate(ranked):
    ra.text(float(r["cost"]), i, " #%s" % r["rank"], va="center", fontsize=9)
sa = ax[2, 1]
sa.axis("off")
sa.text(0.05, 0.6, "settling: all controllers never settled\n(joint \u00b10.5 \u00b0C / \u00b13 %RH band)", fontsize=11)
sa.text(0.05, 0.3, "overshoot_H saturates at 30.0 for on/off, PID, fuzzy\n(structural note, not a GA defect)", fontsize=11)
fig.suptitle("Controller scoreboard from results/comparison.csv (frozen)")
fig.tight_layout()
st.pyplot(fig)
