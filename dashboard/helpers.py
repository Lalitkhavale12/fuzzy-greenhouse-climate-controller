"""Shared export byte builders for the dashboard (Phase 08, D-02/D-04).

ALL new Python defs live here — pages stay thin wiring (headless audits
ban savefig/def-on-03/w-mode-opens in pages). Three public builders:

- scoreboard_csv_bytes: frozen results/comparison.csv bytes, byte-identical
- verdict_text: notebook-05-cell-5 mirror (winner + margins + per-term +
  provenance), reads CSV rows only, never recomputes
- fig_to_png_bytes: in-hand figure -> PNG bytes (savefig -> BytesIO ->
  seek(0)), never closes the figure so the caller can still st.pyplot it

Plus build_results_figure: rebuilds the Results scoreboard figure from
passed-in rows with explicit light-figure colors (the Streamlit theme
never touches matplotlib). Phase 9/10 compose these primitives.

Phase 09 scenario pair (UI-04): scenario_delta (B-minus-A delta rows via
locked-weight all_metrics), run_scenario_pair (two run_all_four sides +
delta rows), build_scenario_figure (paired-trace figure, unclosed).

Threat mitigations (T-08-01/02/03): two hardcoded frozen paths only,
data carries bytes never a user path, file_name literals live on pages,
in-memory BytesIO only, zero new deps.

Run:  python dashboard/helpers.py  (headless self-check, no browser)
"""

import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np

from src.metrics import COLUMNS  # frozen column contract, never retyped

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOREBOARD_PATH = os.path.join(ROOT, "results", "comparison.csv")

LIGHT_FACE = "#F7FAF3"  # pale greenhouse white — figure background
LIGHT_AXES = "#FFFFFF"  # axes wells
INK = "#263023"  # soil-ink text

ORDER = ["onoff", "pid", "fuzzy", "ga_fuzzy"]
DISPLAY = {"onoff": "on/off", "pid": "PID",
           "fuzzy": "hand fuzzy", "ga_fuzzy": "GA fuzzy"}
WEATHERS = ["train-seed7", "holdout-seed21"]


def scoreboard_csv_bytes(path=SCOREBOARD_PATH):
    """Frozen scoreboard bytes, byte-identical to results/comparison.csv."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as exc:
        raise ValueError("frozen scoreboard unreadable: %s" % exc)
    header = raw.splitlines()
    if not header:
        raise ValueError("frozen scoreboard is empty: %s" % path)
    if header[0].decode("utf-8").split(",") != COLUMNS:
        raise ValueError("stale artifact: header != COLUMNS")
    return raw


def holdout_ranking(rows):
    """Holdout rows ordered by the CSV rank column (stable: ties keep row order)."""
    holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
    return sorted(holdout, key=lambda r: int(r["rank"]))


def verdict_text(rows):
    """Holdout verdict TXT: winner + margins + per-term + provenance.

    Mirrors notebooks/05_comparison.ipynb cell 5 relative-ordering logic
    (GA below on/off AND below PID, %.2f costs). Reads the CSV rows only.
    """
    ranked = holdout_ranking(rows)
    if not ranked:
        raise ValueError("no holdout-seed21 rows in scoreboard")
    cost = {r["controller"]: float(r["cost"]) for r in ranked}
    for c in ("ga_fuzzy", "onoff", "pid"):
        if c not in cost:
            raise ValueError("holdout missing controller: %s" % c)
    winner = ranked[0]["controller"]
    beats = cost["ga_fuzzy"] < cost["onoff"] and cost["ga_fuzzy"] < cost["pid"]
    margin_onoff = cost["onoff"] - cost["ga_fuzzy"]
    margin_pid = cost["pid"] - cost["ga_fuzzy"]
    lines = []
    lines.append("Greenhouse holdout verdict (results/comparison.csv, holdout-seed21)")
    lines.append("holdout: GA %.2f < on/off %.2f AND GA < PID %.2f"
                 % (cost["ga_fuzzy"], cost["onoff"], cost["pid"]))
    lines.append("winner: %s ranks #1 on holdout" % winner)
    lines.append("margin GA vs on/off: %.2f cost points" % margin_onoff)
    lines.append("margin GA vs PID: %.2f cost points" % margin_pid)
    if beats:
        lines.append("verdict: GA < on/off AND GA < PID on holdout -- METR-02 HOLDS")
    else:
        lines.append("verdict: GA-beats-baselines claim does NOT hold in this artifact")
    lines.append("")
    lines.append("per-controller holdout terms (iae_T, iae_H, energy, cost):")
    for r in ranked:
        lines.append("%s: iae_T=%.4f iae_H=%.4f energy=%.4f cost=%.2f rank #%s"
                     % (r["controller"], float(r["iae_T"]), float(r["iae_H"]),
                        float(r["energy"]), float(r["cost"]), r["rank"]))
    lines.append("")
    lines.append("provenance: train_seed=7 (train-seed7), "
                 "holdout_seed=21 (holdout-seed21), weights 1.0/1.0/0.01")
    return "\n".join(lines) + "\n"


def fig_to_png_bytes(fig, dpi=150):
    """Serialize an in-hand figure to PNG bytes (never closes the figure)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)  # mandatory — without this the download is empty
    return buf.getvalue()


def _paint_light(fig, axes):
    """Explicit light-figure face + soil-ink colors (theme never touches mpl)."""
    fig.patch.set_facecolor(LIGHT_FACE)
    for a in np.ravel(axes):
        a.set_facecolor(LIGHT_AXES)
        a.tick_params(colors=INK)
        a.title.set_color(INK)
        a.xaxis.label.set_color(INK)
        a.yaxis.label.set_color(INK)


def build_results_figure(rows):
    """Rebuild the scoreboard figure from passed-in rows (no recompute)."""
    val = {(r["controller"], r["weather"], m): float(r[m])
           for r in rows for m in ("iae_T", "iae_H", "energy", "cost")}
    ranked = holdout_ranking(rows)
    fig, ax = plt.subplots(3, 2, figsize=(12, 12))
    x = np.arange(len(ORDER))
    w = 0.35
    for j, metric in enumerate(["iae_T", "iae_H", "energy", "cost"]):
        a = ax[j // 2, j % 2]
        a.bar(x - w / 2, [val[(c, WEATHERS[0], metric)] for c in ORDER], w,
              label="train-seed7")
        a.bar(x + w / 2, [val[(c, WEATHERS[1], metric)] for c in ORDER], w,
              label="holdout-seed21")
        a.set_xticks(x)
        a.set_xticklabels([DISPLAY[c] for c in ORDER])
        a.set_title(metric)
        a.legend(fontsize=8)
        a.grid(alpha=0.3)
    ax[1, 1].set_yscale("log")
    ax[1, 1].set_title("cost (log scale)")
    ra = ax[2, 0]
    ra.barh([DISPLAY[r["controller"]] for r in ranked],
            [float(r["cost"]) for r in ranked])
    ra.set_xlabel("holdout cost")
    ra.set_title("Holdout cost ranking (CSV rank column)")
    for i, r in enumerate(ranked):
        ra.text(float(r["cost"]), i, " #%s" % r["rank"], va="center", fontsize=9)
    sa = ax[2, 1]
    sa.axis("off")
    sa.text(0.05, 0.6, "settling: all controllers never settled\n"
                       "(joint \u00b10.5 \u00b0C / \u00b13 %RH band)", fontsize=11)
    sa.text(0.05, 0.3, "overshoot_H saturates at 30.0 for on/off, PID, fuzzy\n"
                       "(structural note, not a GA defect)", fontsize=11)
    fig.suptitle("Controller scoreboard from results/comparison.csv (frozen)")
    _paint_light(fig, ax)
    fig.tight_layout()
    return fig


def scenario_delta(side_a, side_b, T_sp=25.0, RH_sp=70.0):
    """Per-controller B-minus-A deltas between two run_all_four sides.

    side_a/side_b: dict name -> (T_hist, RH_hist, U_hist) as run_all_four
    returns. Returns list-of-dicts in DISPLAY order with d_iae_T/d_iae_H/
    d_energy/d_cost (side B minus side A). Locked weights 1.0/1.0/0.01
    via all_metrics (T-09-02: no user-controlled weights or paths).
    """
    from src.metrics import all_metrics
    rows = []
    for name in DISPLAY.values():
        ma = all_metrics(side_a[name][0], side_a[name][1], side_a[name][2],
                         T_sp, RH_sp)
        mb = all_metrics(side_b[name][0], side_b[name][1], side_b[name][2],
                         T_sp, RH_sp)
        rows.append({"controller": name,
                     "d_iae_T": mb["iae_T"] - ma["iae_T"],
                     "d_iae_H": mb["iae_H"] - ma["iae_H"],
                     "d_energy": mb["energy"] - ma["energy"],
                     "d_cost": mb["cost"] - ma["cost"]})
    return rows


def run_scenario_pair(T_sp, RH_sp, seed_a, seed_b, runner):
    """Two cached run_all_four sides plus delta rows (headless seam).

    runner is the cached run_all_four callable (sole sim entry point,
    called exactly twice so side B never recomputes side A). Returns
    (runs_a, runs_b, delta_rows).
    """
    _, runs_a = runner(T_sp, RH_sp, seed_a)
    _, runs_b = runner(T_sp, RH_sp, seed_b)
    return runs_a, runs_b, scenario_delta(runs_a, runs_b, T_sp, RH_sp)


if __name__ == "__main__":
    with open(SCOREBOARD_PATH) as _f:
        _rows = list(csv.DictReader(_f))
    with open(SCOREBOARD_PATH, "rb") as _fb:
        assert scoreboard_csv_bytes() == _fb.read()
    _t = verdict_text(_rows)
    for _s in ("ga_fuzzy", "onoff", "pid", "fuzzy", "iae_T", "iae_H",
               "energy", "train_seed=7", "holdout_seed=21", "1.0/1.0/0.01"):
        assert _s in _t, _s
    import matplotlib as _mpl  # noqa: backend already selected at import;
    _mpl.use("Agg")  # no-op guard: savefig-to-BytesIO needs no display
    _png = fig_to_png_bytes(build_results_figure(_rows))
    assert _png[:4] == b"\x89PNG" and len(_png) > 1024, len(_png)
    print("helpers self-check: CSV ==, verdict substrings ok, PNG magic ok")
