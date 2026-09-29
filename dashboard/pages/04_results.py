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

import streamlit as st

from src.metrics import COLUMNS  # frozen column contract, never retyped
from dashboard.helpers import (ORDER, DISPLAY, WEATHERS, holdout_ranking,
                               build_results_figure, fig_to_png_bytes,
                               scoreboard_csv_bytes, verdict_text,
                               evidence_zip_bytes)

CSV_PATH = "results/comparison.csv"


def load_scoreboard(path=CSV_PATH):
    """Load the frozen scoreboard with fail-closed provenance asserts."""
    try:
        with open(path) as f:
            rows = list(csv.DictReader(f))
    except OSError as exc:
        raise ValueError("frozen scoreboard unreadable: %s" % exc)
    if not rows:
        raise ValueError("scoreboard CSV is empty")
    assert list(rows[0].keys()) == COLUMNS, "stale artifact: header != COLUMNS"
    assert len(rows) == 8, "expected 4 controllers x 2 weathers"
    return rows


st.title("Results — frozen scoreboard + verdict")

try:
    rows = load_scoreboard()
    ranked = holdout_ranking(rows)
    txt = verdict_text(rows)
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen scoreboard unreadable: %s" % exc)
    st.stop()

st.subheader("Scoreboard (results/comparison.csv, 8 rows)")
st.dataframe(rows)
st.download_button("Download scoreboard (CSV)", data=scoreboard_csv_bytes(),
                   file_name="comparison.csv", mime="text/csv")

st.subheader("Holdout verdict")
for r in ranked:
    st.metric(DISPLAY[r["controller"]],
              "cost %.2f" % float(r["cost"]),
              "rank #%s" % r["rank"])
winner = ranked[0]["controller"]
cost = {r["controller"]: float(r["cost"]) for r in ranked}
beats = cost["ga_fuzzy"] < cost["onoff"] and cost["ga_fuzzy"] < cost["pid"]
st.success("Verdict: %s ranks #1 on holdout" % DISPLAY[winner])
if beats:
    st.success("GA < on/off AND GA < PID holds")
else:
    st.warning("GA-beats-baselines claim does NOT hold in this artifact")
st.download_button("Download verdict (TXT)", data=txt,
                   file_name="holdout_verdict.txt", mime="text/plain")

fig = build_results_figure(rows)  # single source of truth (helpers.py)
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="results_scoreboard.png", mime="image/png")
st.download_button("Download evidence pack (ZIP)", data=evidence_zip_bytes(),
                   file_name="greenhouse_evidence_pack.zip",
                   mime="application/zip")
st.pyplot(fig)
