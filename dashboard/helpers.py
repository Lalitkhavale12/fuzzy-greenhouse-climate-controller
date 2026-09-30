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

import copy
import csv
import io
import os
import sys
import zipfile

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

ZIP_MEMBERS = ["comparison.csv", "holdout_verdict.txt",
               "results_scoreboard.png",
               "01_greenhouse_model.png", "02_baselines.png", "03_fuzzy.png",
               "04_ga_optimization.png", "05_comparison.png",
               "06_final_results.png", "ga_optimized_params.json"]


def load_kpi_row(path=SCOREBOARD_PATH):
    """Frozen holdout ga_fuzzy row for uniform KPI cards (WR-01 shared fix).

    Fail-closed ValueError contract (never bare open/assert/next): missing
    file, empty CSV, stale header, wrong row count, absent holdout block,
    or missing ga_fuzzy row all raise ValueError for the page's st.error
    path. Callers wrap in try/except + st.stop (see 04_results.py).
    """
    try:
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError as exc:
        raise ValueError("frozen scoreboard unreadable: %s" % exc)
    if not rows:
        raise ValueError("scoreboard CSV is empty: %s" % path)
    if list(rows[0].keys()) != COLUMNS:
        raise ValueError("stale artifact: header != COLUMNS")
    if len(rows) != 8:
        raise ValueError("expected 4 controllers x 2 weathers, got %d"
                         % len(rows))
    holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
    if not holdout:
        raise ValueError("no holdout-seed21 rows in scoreboard")
    for r in holdout:
        if r["controller"] == "ga_fuzzy":
            return r
    raise ValueError("holdout missing controller: ga_fuzzy")


def evidence_zip_bytes():
    """Assemble the frozen evidence pack in memory (never touches disk).

    Fixed ZIP_MEMBERS flat-basename allowlist (T-10-01), raw rb.read
    bytes for notebook PNGs + GA JSON (never re-serialized, T-10-03),
    BytesIO-only with close-then-getvalue (T-10-02). Single on-demand
    build, no caching (T-10-04: members total under ~2 MB).
    """
    with open(SCOREBOARD_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    with open(SCOREBOARD_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    buf = io.BytesIO()
    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("comparison.csv", scoreboard_csv_bytes())
            z.writestr("holdout_verdict.txt", verdict_text(rows).encode("utf-8"))
            z.writestr("results_scoreboard.png",
                       fig_to_png_bytes(build_results_figure(rows)))
            for name in ("01_greenhouse_model.png", "02_baselines.png",
                         "03_fuzzy.png", "04_ga_optimization.png",
                         "05_comparison.png", "06_final_results.png"):
                with open(os.path.join(ROOT, "notebooks", name), "rb") as f:
                    z.writestr(name, f.read())
            with open(os.path.join(ROOT, "results", "ga_optimized_params.json"),
                      "rb") as f:
                z.writestr("ga_optimized_params.json", f.read())
    except OSError as exc:
        raise ValueError("frozen evidence input unreadable: %s" % exc)
    return buf.getvalue()


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


def build_scenario_figure(hours, runs_a, runs_b, T_sp, RH_sp, seed_a, seed_b):
    """Paired scenario traces: rows T/RH/heater, columns side A/B.

    One combined figure (never closed); the page serializes it via
    fig_to_png_bytes and shows it with a single st.pyplot call. Full
    1440-step traces (no decimation -- on/off chatter is signal).
    """
    fig, ax = plt.subplots(3, 2, figsize=(12, 9), sharex=True)
    sides = (("A", seed_a, runs_a), ("B", seed_b, runs_b))
    for j, (side, seed, runs) in enumerate(sides):
        for name in DISPLAY.values():
            T_h, RH_h, U_h = runs[name]
            ax[0, j].plot(hours, T_h, label=name, linewidth=1.2)
        ax[0, j].axhline(T_sp, color="k", linestyle="--", linewidth=0.8)
        ax[0, j].set_ylabel("T (degC)")
        ax[0, j].set_title("side %s (seed %d) T" % (side, seed))
        ax[0, j].legend(fontsize=8)
        ax[0, j].grid(alpha=0.3)
        for name in DISPLAY.values():
            T_h, RH_h, U_h = runs[name]
            ax[1, j].plot(hours, RH_h, label=name, linewidth=1.2)
        ax[1, j].axhline(RH_sp, color="k", linestyle="--", linewidth=0.8)
        ax[1, j].set_ylabel("RH (%)")
        ax[1, j].set_title("side %s (seed %d) RH" % (side, seed))
        ax[1, j].legend(fontsize=8)
        ax[1, j].grid(alpha=0.3)
        for name in DISPLAY.values():
            T_h, RH_h, U_h = runs[name]
            ax[2, j].plot(hours, [u["heater"] for u in U_h], label=name,
                           linewidth=1.2)
        ax[2, j].set_xlabel("hour of day")
        ax[2, j].set_ylabel("heater duty")
        ax[2, j].set_title("side %s (seed %d) heater" % (side, seed))
        ax[2, j].legend(fontsize=8)
        ax[2, j].grid(alpha=0.3)
    fig.suptitle("Scenario A (seed %d) vs B (seed %d) -- T_sp %.1f C, RH_sp %d %%"
                 % (seed_a, seed_b, T_sp, RH_sp))
    _paint_light(fig, ax)
    fig.tight_layout()
    return fig


def build_controller_trace_figure(hours, runs_a, runs_b, T_sp, RH_sp,
                                  seed_a, seed_b, group):
    """Single-signal paired traces: side A/B columns for one group (unclosed).

    Controllers-page tab body (T/RH/energy): the same traces as
    build_scenario_figure, one signal per figure so each tab stacks cleanly
    in narrow viewports. group in ("T", "RH", "energy"); "energy" plots
    heater duty (the energy proxy). The page serializes with fig_to_png_bytes
    and shows with a single full-width st.pyplot per tab.
    """
    if group not in ("T", "RH", "energy"):
        raise ValueError("trace group must be T/RH/energy, got %r" % (group,))
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), sharex=True)
    sides = (("A", seed_a, runs_a), ("B", seed_b, runs_b))
    for j, (side, seed, runs) in enumerate(sides):
        for name in DISPLAY.values():
            T_h, RH_h, U_h = runs[name]
            if group == "T":
                ax[j].plot(hours, T_h, label=name, linewidth=1.2)
            elif group == "RH":
                ax[j].plot(hours, RH_h, label=name, linewidth=1.2)
            else:
                ax[j].plot(hours, [u["heater"] for u in U_h], label=name,
                           linewidth=1.2)
        if group == "T":
            ax[j].axhline(T_sp, color="k", linestyle="--", linewidth=0.8)
            ax[j].set_ylabel("T (degC)")
        elif group == "RH":
            ax[j].axhline(RH_sp, color="k", linestyle="--", linewidth=0.8)
            ax[j].set_ylabel("RH (%)")
        else:
            ax[j].set_ylabel("heater duty")
        ax[j].set_xlabel("hour of day")
        ax[j].set_title("side %s (seed %d) %s" % (side, seed, group))
        ax[j].legend(fontsize=8)
        ax[j].grid(alpha=0.3)
    fig.suptitle("Controllers %s traces -- side A (seed %d) vs B (seed %d)"
                 % (group, seed_a, seed_b))
    _paint_light(fig, ax)
    fig.tight_layout()
    return fig


def scratch_mfs_from_deltas(eT_centers, du_centers, eps=1e-3):
    """Hand MFs deep-copied with dragged eT/du centers, neighbor-clamped."""
    from src.fuzzy_controller import FUZZY_MFS
    scratch = copy.deepcopy(FUZZY_MFS)
    warnings = []
    for key, vals in (("eT", eT_centers), ("du", du_centers)):
        vals = [float(v) for v in vals]
        if len(vals) != 5:
            raise ValueError("%s needs 5 centers, got %d" % (key, len(vals)))
        hand = [float(c) for c in scratch[key]["centers"]]
        clamped = []
        for i, v in enumerate(vals):
            if not np.isfinite(v):
                warnings.append("%s[%d] non-finite input, kept hand %.4g"
                                % (key, i, hand[i]))
                v = hand[i]
            clamped.append(v)
        # fixed-point neighbor ordering (WR-01): iterate forward+backward
        # passes against already-clamped neighbors until nothing moves, so
        # even fully-reversed headless input lands strictly increasing.
        for _ in range(len(clamped)):
            changed = False
            for i in range(1, 5):  # forward: c[i] > c[i-1] + eps
                lo = clamped[i - 1] + eps
                if clamped[i] < lo:
                    clamped[i] = lo
                    changed = True
                    warnings.append("%s[%d] clamped to %.4g (neighbor bound)"
                                    % (key, i, lo))
            for i in range(3, -1, -1):  # backward: c[i] < c[i+1] - eps
                hi = clamped[i + 1] - eps
                if clamped[i] > hi:
                    clamped[i] = hi
                    changed = True
                    warnings.append("%s[%d] clamped to %.4g (neighbor bound)"
                                    % (key, i, hi))
            if not changed:
                break
        scratch[key]["centers"] = np.array(clamped, dtype=float)
    return scratch, warnings


def tloop_response_curve(mfs, n=201, lo=-5.0, hi=5.0):
    """T-loop defuzz slice: du over an eT grid at deT=0 (stateless, ~28 ms)."""
    from src.fuzzy_controller import infer
    grid = np.linspace(lo, hi, n)
    EC, EW = mfs["eT"]["centers"], mfs["eT"]["widths"]
    DC, DW = mfs["deT"]["centers"], mfs["deT"]["widths"]
    OC, OW = mfs["du"]["centers"], mfs["du"]["widths"]
    vals = np.array([infer(float(e), 0.0, EC, EW, DC, DW, OC, OW, -1.0, 1.0)
                     for e in grid])
    return grid, vals


def build_explorer_figure(grid, hand_vals, scratch_vals):
    """Frozen-hand solid vs scratch dashed response overlay (unclosed)."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(grid, hand_vals, "C0-", label="frozen hand response")
    ax.plot(grid, scratch_vals, "C1--", label="scratch (dragged)")
    ax.set_xlabel("eT (degC)")
    ax.set_ylabel("du (duty/step)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    _paint_light(fig, ax)
    fig.tight_layout()
    return fig


GEN_COUNT = 50  # frozen artifact generation count (IN-03: single source)


def replay_slice(gen, history_best, history_mean):
    """1-based gen -> (gen, best_val, mean_val). Pure clamp-and-index.

    Stateless scrubber over the frozen len-50 history arrays (D-03):
    no recompute, no timers, no training imports. Out-of-range headless
    calls clamp to 1-50 (T-09-09); the page slider is int-only 1-50.
    """
    g = int(max(1, min(GEN_COUNT, gen)))
    return g, float(history_best[g - 1]), float(history_mean[g - 1])


def build_replay_figure(best, mean, gen):
    """Convergence plot with a dashed vertical marker at gen (unclosed)."""
    g = int(max(1, min(50, gen)))
    fig, ax = plt.subplots(figsize=(10, 4))
    gens = range(1, len(best) + 1)
    ax.plot(gens, best, label="best")
    ax.plot(gens, mean, label="mean", alpha=0.7)
    ax.axvline(g, color="k", linestyle="--", linewidth=0.8)
    ax.set_xlabel("generation")
    ax.set_ylabel("train weighted cost")
    ax.set_title("GA convergence replay -- gen %d/50, best %.2f"
                 % (g, float(best[g - 1])))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    _paint_light(fig, ax)
    fig.tight_layout()
    return fig


_EPH_DIR = None


def ephemeral_weather_path(seed):
    """Synthetic weather path inside one shared temp dir (no per-seed leak)."""
    global _EPH_DIR
    from src.weather_profile_generator import generate_weather_profile
    import tempfile
    if _EPH_DIR is None:
        _EPH_DIR = tempfile.mkdtemp(prefix="gh_weather_")
    path = os.path.join(_EPH_DIR, "seed_%d.csv" % int(seed))
    if not os.path.exists(path):
        generate_weather_profile(path, seed=int(seed))
    return path


def build_overlay_figure(hours, t_hists, T_sp):
    """All-controller T traces on shared axes + setpoint dashed (no recompute)."""
    fig, ax = plt.subplots(figsize=(10, 4))
    for name in t_hists:
        ax.plot(hours, t_hists[name], label=name)
    ax.axhline(float(T_sp), color="k", linestyle="--", linewidth=1,
               label="setpoint")
    ax.set_xlabel("hour of day")
    ax.set_ylabel("inside T (degC)")
    ax.set_title("All four controllers — one axes (does GA hold the line?)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    _paint_light(fig, ax)
    fig.tight_layout()
    return fig


def mf_sensitivity_costs(delta=0.5, n=1440):
    """Hand-fuzzy eT center +/-delta -> closed-loop cost each (seed 7 frozen).

    Returns (base_cost, rows) with rows = [(label, dcost)] for 5 centers x 2
    shifts. Perturbed MFs go through scratch_mfs_from_deltas, so neighbor
    clamping applies exactly as in the explorer.
    """
    from src.fuzzy_controller import FUZZY_MFS, fuzzy_step
    from src.metrics import run_closed_loop, all_metrics
    hand_eT = [float(c) for c in FUZZY_MFS["eT"]["centers"]]
    hand_du = [float(c) for c in FUZZY_MFS["du"]["centers"]]
    wpath = os.path.join(ROOT, "weather", "weather_profile.csv")

    def _cost(mfs):
        T, RH, U = run_closed_loop(
            lambda T_, rh_, Ts_, Rs_, st_: fuzzy_step(
                T_, rh_, Ts_, Rs_, st_, 60.0, mfs),
            wpath, n=n)
        return all_metrics(T, RH, U)["cost"]

    base_mfs, _ = scratch_mfs_from_deltas(hand_eT, hand_du)
    base = _cost(base_mfs)
    rows = []
    for i, c in enumerate(hand_eT):
        for s in (-float(delta), float(delta)):
            vec = list(hand_eT)
            vec[i] = c + s
            mfs, _ = scratch_mfs_from_deltas(vec, hand_du)
            rows.append(("eT[%d] %+.1f" % (i, s), _cost(mfs) - base))
    return base, rows


def build_sensitivity_figure(rows):
    """Horizontal diverging bars of dcost per MF shift (unclosed)."""
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    colors = ["#C62828" if v > 0 else "#2E7D32" for v in vals]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(labels, vals, color=colors)
    ax.axvline(0.0, color="k", linewidth=0.8)
    ax.set_xlabel("delta closed-loop cost vs hand baseline")
    ax.set_title("MF sensitivity: which center shift hurts/helps most")
    ax.grid(alpha=0.3, axis="x")
    _paint_light(fig, ax)
    fig.tight_layout()
    return fig


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
    _zip = evidence_zip_bytes()
    assert _zip[:2] == b"PK" and len(_zip) > 1024, len(_zip)
    import zipfile as _zf
    assert _zf.ZipFile(io.BytesIO(_zip)).namelist() == ZIP_MEMBERS, \
        _zf.ZipFile(io.BytesIO(_zip)).namelist()
    print("helpers self-check: CSV ==, verdict substrings ok, PNG magic ok, "
          "ZIP PK + 10 members ok")
