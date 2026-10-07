"""Headless dashboard checks (PROOF-02a-g).

Plain-assert standalone suite in the tests/test_notebooks.py style:
pytest-compatible test_* names, imports inside bodies, runner prints
PASS/FAIL and sys.exit(1) on failure. Streamlit pages call st.* at
import, so the import-smoke test stubs streamlit in sys.modules first.

Run:  python tests/test_dashboard.py
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "dashboard", "app.py")
PAGES_DIR = os.path.join(ROOT, "dashboard", "pages")

EXPECTED_PAGES = ["01_model_sim.py", "02_controllers.py",
                   "03_ga_explorer.py", "04_results.py"]

_METRIC_CALLS = []  # recorded st.metric (label, value) calls, headless KPI proof


def _read(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return f.read()


def _stub_streamlit():
    # Deliberately no teardown: this repo has no pytest, so the standalone
    # runner is the only consumer; pages bind the stub at import and need it
    # for the whole session. Revisit if pytest is ever introduced.
    import sys as _sys

    class _Stub:
        def __getattr__(self, name):
            if name == "cache_data":
                def deco(*dargs, **dkw):
                    if len(dargs) == 1 and callable(dargs[0]) and not dkw:
                        return dargs[0]

                    def wrap(fn):
                        return fn
                    return wrap
                return deco
            if name == "sidebar":
                return self
            if name == "columns":
                def cols(n, *a, **k):
                    n = n if isinstance(n, int) else len(n)
                    return [_Stub() for _ in range(n)]
                return cols
            if name == "tabs":
                def tabs(labels, *a, **k):
                    return [_Stub() for _ in labels]
                return tabs
            if name == "expander":
                def expander(*a, **k):
                    return _Stub()
                return expander
            if name == "slider":
                def slider(label, min_value=None, max_value=None,
                           value=None, *a, **k):
                    if value is not None:
                        return value
                    return min_value if min_value is not None else 0
                return slider
            if name == "selectbox":
                def sb(label, options, index=0, *a, **k):
                    try:
                        return list(options)[index]
                    except Exception:
                        return None
                return sb
            if name == "download_button":
                def dl(label, *a, **k):
                    return None
                return dl
            if name == "metric":
                def metric(label, value=None, *a, **k):
                    _METRIC_CALLS.append((label, value))
                    return None
                return metric

            def _noop(*a, **k):
                return None
            return _noop

        def __call__(self, *a, **k):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    _sys.modules["streamlit"] = _Stub()


def _import_helpers():
    import importlib.util
    import sys as _sys
    _stub_streamlit()
    import matplotlib as _mpl
    _mpl.use("Agg")  # headless figure construction; helpers must not set this
    if ROOT not in _sys.path:
        _sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    path = os.path.join(ROOT, "dashboard", "helpers.py")
    spec = importlib.util.spec_from_file_location("dash_helpers", path)
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["dash_helpers"] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_page(fname):
    import importlib.util
    import sys as _sys
    _stub_streamlit()
    import matplotlib as _mpl
    _mpl.use("Agg")  # headless figure construction; pages must not set this
    path = os.path.join(PAGES_DIR, fname)
    modname = "dashpage_" + fname[:-3].replace("-", "_")
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    _sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def test_page_set():
    import re
    assert os.path.exists(APP), APP
    files = sorted(os.listdir(PAGES_DIR))
    for expect in EXPECTED_PAGES:
        assert expect in files, (expect, files)
    prefixes = [re.match(r"([0-9]+)[_ -]*", f).group(1) for f in files if f.endswith(".py")]
    assert prefixes == sorted(prefixes), prefixes
    src = _read("dashboard/app.py")
    assert "set_page_config" in src, "app.py must call set_page_config"
    assert src.index("set_page_config") < src.index("st.title"), \
        "set_page_config must precede other st.* calls"
    for bad in ("run_closed_loop", "compare(", "savefig", "plt.show"):
        assert bad not in src, ("app.py landing-only", bad)
    print("app + 4 numbered pages present in sidebar order, app landing-only")


def test_pages_import():
    for fname in EXPECTED_PAGES:
        assert os.path.exists(os.path.join(PAGES_DIR, fname)), \
            "missing page file: %s" % fname
        _import_page(fname)
        print(f"import-ok {fname}")


def test_results_helper():
    mod = _import_page("04_results.py")
    rows = mod.load_scoreboard()
    from src.metrics import COLUMNS
    assert list(rows[0].keys()) == COLUMNS, "header != COLUMNS"
    assert len(rows) == 8, "expected 4 controllers x 2 weathers"
    ranked = mod.holdout_ranking(rows)
    assert [r["controller"] for r in ranked] == ["ga_fuzzy", "onoff", "fuzzy", "pid"], \
        [r["controller"] for r in ranked]
    assert ranked[0]["controller"] == "ga_fuzzy", "rank-1 identity must be GA fuzzy"
    src = _read("dashboard/pages/04_results.py")
    assert "compare(" not in src, "Results page must never recompute the scoreboard"
    assert "argsort" not in src, "ranking from rank column, never recomputed"
    print("results helper: 8 rows, COLUMNS header, GA rank 1 on holdout")


def test_controllers_helper():
    import time
    mod = _import_page("02_controllers.py")
    assert mod.resolve_weather(7) == "weather/weather_profile.csv"
    assert mod.resolve_weather(21) == "weather/holdout_21.csv"
    custom = mod.resolve_weather(33)
    assert "weather/" not in custom.replace("\\", "/"), custom
    t0 = time.time()
    hours, runs = mod.run_all_four(25.0, 70.0, 21)
    dt = time.time() - t0
    assert set(runs) == {"on/off", "PID", "hand fuzzy", "GA fuzzy"}, set(runs)
    for name, (T_h, RH_h, U_h) in runs.items():
        assert len(T_h) == 1440 and len(RH_h) == 1440 and len(U_h) == 1440, \
            (name, len(T_h))
    assert dt < 30.0, dt
    from src.metrics import all_metrics
    costs = {n: all_metrics(T, RH, U)["cost"] for n, (T, RH, U) in runs.items()}
    assert costs["GA fuzzy"] < costs["on/off"], costs
    assert costs["GA fuzzy"] < costs["PID"], costs
    print("controllers helper: 4 x 1440 on shared weather in %.2fs, GA wins" % dt)


def test_scenario_delta():
    import time
    mod = _import_page("02_controllers.py")
    helpers = _import_helpers()
    assert mod.resolve_weather(7) == "weather/weather_profile.csv"
    assert mod.resolve_weather(21) == "weather/holdout_21.csv"
    # counting cache emulates @st.cache_data (the headless stub has no
    # cache): stable (T_sp, RH_sp, seed) args must key cache hits so a
    # warm re-render recomputes nothing (T-09-04).
    calls = []
    cache = {}

    def cached_runner(T_sp, RH_sp, seed):
        key = (T_sp, RH_sp, seed)
        if key not in cache:
            calls.append(key)
            cache[key] = mod.run_all_four(T_sp, RH_sp, seed)
        return cache[key]

    t0 = time.time()
    runs_a, runs_b, delta_rows = helpers.run_scenario_pair(
        25.0, 70, 7, 21, cached_runner)
    cold_dt = time.time() - t0
    assert cold_dt < 15.0, cold_dt  # hang guard only (WR-03); measured ~4.5 s
    assert len(calls) == 2, calls  # one cached call per side, never more
    t0 = time.time()
    runs_a2, runs_b2, delta2 = helpers.run_scenario_pair(
        25.0, 70, 7, 21, cached_runner)
    warm_dt = time.time() - t0
    assert len(calls) == 2, calls  # warm call adds zero sim calls
    assert warm_dt < 2.0, warm_dt  # hang guard only (WR-03); measured ~0.1 s
    assert delta2 == delta_rows  # cache-hit recompute is identical
    for runs in (runs_a, runs_b):
        assert set(runs) == {"on/off", "PID", "hand fuzzy", "GA fuzzy"}, \
            set(runs)
        for name, (T_h, RH_h, U_h) in runs.items():
            assert len(T_h) == 1440 and len(RH_h) == 1440 and \
                len(U_h) == 1440, (name, len(T_h))
    from src.metrics import all_metrics
    assert [r["controller"] for r in delta_rows] == \
        ["on/off", "PID", "hand fuzzy", "GA fuzzy"], delta_rows
    for row in delta_rows:
        name = row["controller"]
        ma = all_metrics(*runs_a[name], 25.0, 70)
        mb = all_metrics(*runs_b[name], 25.0, 70)
        assert row["d_iae_T"] == mb["iae_T"] - ma["iae_T"], name
        assert row["d_iae_H"] == mb["iae_H"] - ma["iae_H"], name
        assert row["d_energy"] == mb["energy"] - ma["energy"], name
        assert row["d_cost"] == mb["cost"] - ma["cost"], name
    costs_a = {n: all_metrics(*runs_a[n], 25.0, 70)["cost"] for n in runs_a}
    costs_b = {n: all_metrics(*runs_b[n], 25.0, 70)["cost"] for n in runs_b}
    assert costs_a["GA fuzzy"] < costs_a["on/off"], costs_a
    assert costs_a["GA fuzzy"] < costs_a["PID"], costs_a
    assert costs_b["GA fuzzy"] < costs_b["on/off"], costs_b
    assert costs_b["GA fuzzy"] < costs_b["PID"], costs_b
    import numpy as _np
    hours = _np.arange(0, 1440) / 60.0  # same hours run_all_four returns;
    # figure render is untimed (all exhibit pages pay it; only the sim
    # recompute path is budget-gated)
    fig = helpers.build_scenario_figure(hours, runs_a, runs_b,
                                        25.0, 70, 7, 21)
    title = fig._suptitle.get_text()
    assert "seed 7" in title and "seed 21" in title, title
    png = helpers.fig_to_png_bytes(fig)
    assert png[:4] == b"\x89PNG" and len(png) > 1024, len(png)
    print("scenario delta: 2 x 4 x 1440 pair, B-minus-A float-equal, "
          "GA wins both sides at 7/21, cold %.2fs, warm %.3fs, "
          "paired fig PNG ok" % (cold_dt, warm_dt))


def test_explorer_helper():
    import json
    with open(os.path.join(ROOT, "results/ga_optimized_params.json")) as f:
        d = json.load(f)
    assert d["schema_version"] == 2, "stale artifact: schema_version != 2"
    assert len(d["history"]["best"]) == 50, len(d["history"]["best"])
    assert len(d["history"]["mean"]) == 50, len(d["history"]["mean"])
    from src.ga_fuzzy_controller import load_optimized_mfs
    mfs, gains = load_optimized_mfs(os.path.join(ROOT, "results/ga_optimized_params.json"))
    assert set(mfs) == {"eT", "deT", "du", "eH", "deH", "dv"}, set(mfs)
    for k, g in mfs.items():
        assert len(g["centers"]) == 5 and len(g["widths"]) == 5, (k,)
    src = _read("dashboard/pages/03_ga_explorer.py")
    assert "load_optimized_mfs" in src, "MFs must come via the validated loader"
    assert "genetic_algorithm" not in src, "no evolution entry points on the page"
    for word in ("evolve", "train(", "fit("):
        assert word not in src, ("03 page evolution ref", word)
    print("explorer helper: schema v2, 6 MF groups len-5, 50-gen history")


def test_scratch_purity():
    import inspect
    import numpy as _np
    helpers = _import_helpers()
    from src.fuzzy_controller import FUZZY_MFS
    from src.ga_fuzzy_controller import load_optimized_mfs
    hand = {k: (v["centers"].copy(), v["widths"].copy())
            for k, v in FUZZY_MFS.items()}
    opt_before = load_optimized_mfs(os.path.join(ROOT, "results/ga_optimized_params.json"))[0]
    opt_snap = {k: (v["centers"].copy(), v["widths"].copy())
                for k, v in opt_before.items()}
    eT0 = [float(c) for c in hand["eT"][0]]
    du0 = [float(c) for c in hand["du"][0]]
    scratch, warns = helpers.scratch_mfs_from_deltas(eT0, du0)
    assert warns == [], warns
    grid, hand_vals = helpers.tloop_response_curve(FUZZY_MFS)
    _, zero_vals = helpers.tloop_response_curve(scratch)
    assert _np.allclose(zero_vals, hand_vals), "zero-drag must coincide"
    dragged = [c + (0.5 if i == 2 else 0.0) for i, c in enumerate(eT0)]
    scratch2, _ = helpers.scratch_mfs_from_deltas(dragged, du0)
    _, drag_vals = helpers.tloop_response_curve(scratch2)
    dev = float(_np.abs(drag_vals - hand_vals).max())
    assert dev > 1e-3, dev
    for k in FUZZY_MFS:
        assert _np.array_equal(FUZZY_MFS[k]["centers"], hand[k][0]), k
        assert _np.array_equal(FUZZY_MFS[k]["widths"], hand[k][1]), k
    opt_after = load_optimized_mfs(os.path.join(ROOT, "results/ga_optimized_params.json"))[0]
    for k in opt_snap:
        assert _np.array_equal(opt_after[k]["centers"], opt_snap[k][0]), k
        assert _np.array_equal(opt_after[k]["widths"], opt_snap[k][1]), k
    assert _np.array_equal(scratch["eT"]["widths"], hand["eT"][1]), "widths frozen"
    assert _np.array_equal(scratch["du"]["widths"], hand["du"][1]), "widths frozen"
    probe = (inspect.getsource(helpers.scratch_mfs_from_deltas)
             + inspect.getsource(helpers.tloop_response_curve)
             + inspect.getsource(helpers.build_explorer_figure))
    for bad in ("run_closed_loop", "all_metrics", "weighted_cost"):
        assert bad not in probe, ("explorer readout path", bad)
    print("scratch purity: bit-identical baselines, coincide-at-zero, "
          "+0.5 drag dev %.4g duty, no cost kernels" % dev)


def test_scratch_clamp():
    helpers = _import_helpers()
    from src.fuzzy_controller import FUZZY_MFS
    hand_eT = [float(c) for c in FUZZY_MFS["eT"]["centers"]]
    hand_du = [float(c) for c in FUZZY_MFS["du"]["centers"]]
    bad_eT = [hand_eT[0], hand_eT[3] + 1.0, hand_eT[2], hand_eT[3], hand_eT[4]]
    scratch, warns = helpers.scratch_mfs_from_deltas(bad_eT, hand_du)
    assert warns, "ordering violation must warn"
    c = list(scratch["eT"]["centers"])
    assert all(b - a > 0 for a, b in zip(c, c[1:])), c
    assert all("clamped" in w or "non-finite" in w for w in warns), warns
    print("scratch clamp: %d warning(s), ordered centers, no raise" % len(warns))


def test_replay_slice():
    import inspect
    import json
    helpers = _import_helpers()
    with open(os.path.join(ROOT, "results/ga_optimized_params.json")) as f:
        d = json.load(f)
    assert d["schema_version"] == 2, "stale artifact: schema_version != 2"
    best = d["history"]["best"]
    mean = d["history"]["mean"]
    assert len(best) == 50 and len(mean) == 50, (len(best), len(mean))
    for g in (1, 25, 50):
        gg, b, m = helpers.replay_slice(g, best, mean)
        assert gg == g, (gg, g)
        assert b == float(best[g - 1]), (g, b)
        assert m == float(mean[g - 1]), (g, m)
        readout = "gen %d/50 \u00b7 best %.2f" % (gg, b)
        assert readout == "gen %d/50 \u00b7 best %s" % (g, "%.2f" % b), readout
        fig = helpers.build_replay_figure(best, mean, g)
        title = fig.axes[0].get_title()
        assert ("gen %d/50" % g) in title, title
        assert ("%.2f" % b) in title, title
        lines = fig.axes[0].get_lines()
        assert len(lines) == 3, len(lines)  # best + mean + gen marker
    assert helpers.replay_slice(0, best, mean)[0] == 1, "clamp lo"
    assert helpers.replay_slice(99, best, mean)[0] == 50, "clamp hi"
    probe = (inspect.getsource(helpers.replay_slice)
             + inspect.getsource(helpers.build_replay_figure))
    for bad in ("genetic_algorithm", "evolve", "run_ga", "run_closed_loop",
                "all_metrics", "weighted_cost"):
        assert bad not in probe, ("replay path", bad)
    print("replay slice: exact at 1/25/50, readout + title carry gen/best, "
          "clamped, no recompute kernels")


def test_source_audits():
    import re
    pages = {}
    for fname in os.listdir(PAGES_DIR):
        if fname.endswith(".py"):
            with open(os.path.join(PAGES_DIR, fname)) as f:
                pages[fname] = f.read()
    assert pages, "no pages found"
    for fname, src in pages.items():
        assert 'use("Agg")' not in src and "use('Agg')" not in src, (fname, "Agg")
        assert "plt.show" not in src, (fname, "show")
        assert "savefig" not in src, (fname, "savefig")
        for bad in ("/home/", "/Users/", "C:/", "C:\\"):
            assert bad not in src, (fname, bad)
        for line in src.splitlines():
            if "generate_weather_profile(" in line:
                assert "weather/" not in line.replace("\\", "/"), (fname, line)
    src02 = pages.get("02_controllers.py", "")
    assert "compare(" not in src02, "Controllers page must never call compare()"
    assert "number_input" not in src02 and "text_input" not in src02, \
        "sliders only drive the loop"
    ga_refs = [l for l in src02.splitlines()
               if "genetic_algorithm" in l or re.search(r"\bevolve\b", l)]
    assert not ga_refs, ("02 page evolution refs", ga_refs)
    src03 = pages.get("03_ga_explorer.py", "")
    for line in src03.splitlines():
        s = line.strip()
        assert not s.startswith("def "), (fname, s)
        assert not s.startswith("class "), (fname, s)
    assert "schema_version" in src03 and "(2, 3)" in src03, "03 schema v2/v3 assert"
    src04 = pages.get("04_results.py", "")
    assert "== COLUMNS" in src04, "04 CSV header assert"
    assert "len(rows) == 8" in src04, "04 8-row assert"
    for fname in ("01_model_sim.py", "02_controllers.py",
                  "03_ga_explorer.py", "04_results.py"):
        assert "st.expander" in pages[fname], (fname, "expander")
        assert ".metric(" in pages[fname], (fname, "metric")
    assert "st.tabs" in pages["02_controllers.py"], "02 tabs"
    assert "st.tabs" in pages["04_results.py"], "04 tabs"
    assert "st.tabs" not in pages["01_model_sim.py"], "01 single flow"
    assert "st.tabs" not in pages["03_ga_explorer.py"], "03 single flow"
    for fname, src in pages.items():
        assert 'open(' not in src or '"w"' not in src, (fname, "no writes")
    print("source audits: no Agg/show/savefig, no abs paths, no recompute")


def test_layout_elements():
    import csv
    import re
    pages = {}
    for fname in os.listdir(PAGES_DIR):
        if fname.endswith(".py"):
            with open(os.path.join(PAGES_DIR, fname)) as f:
                pages[fname] = f.read()
    for fname in EXPECTED_PAGES:
        src = pages[fname]
        assert ".metric(" in src, (fname, "metric")
        assert "st.columns(4)" in src, (fname, "columns(4)")
        assert "st.expander" in src, (fname, "expander")
    assert "st.tabs" in pages["02_controllers.py"], "02 tabs"
    assert "st.tabs" in pages["04_results.py"], "04 tabs"
    assert "st.tabs" not in pages["01_model_sim.py"], "01 single flow"
    assert "st.tabs" not in pages["03_ga_explorer.py"], "03 single flow"
    with open(os.path.join(ROOT, "results/comparison.csv")) as f:
        rows = list(csv.DictReader(f))
    holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
    kpi = next(r for r in holdout if r["controller"] == "ga_fuzzy")
    expected = ["%.2f" % float(kpi["cost"]), "#%s" % kpi["rank"],
                "%.2f" % float(kpi["iae_T"]), "%.2f" % float(kpi["iae_H"])]
    for fname in EXPECTED_PAGES:
        del _METRIC_CALLS[:]
        _import_page(fname)
        got = [v for _, v in _METRIC_CALLS[:4]]
        assert got == expected, (fname, got, expected)
    for fname, src in pages.items():
        for m in re.finditer(r"st\.columns\((\d+)", src):
            assert int(m.group(1)) in (2, 4), (fname, m.group(0))
        with_stack = []
        for line in src.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            while with_stack and with_stack[-1][0] >= indent:
                with_stack.pop()
            if stripped.startswith("with "):
                with_stack.append((indent, stripped))
            if "st.pyplot" in stripped:
                for _, w in with_stack:
                    assert "col" not in w.lower(), (fname, w, stripped)
    print("layout elements: KPI rows equal frozen holdout ga_fuzzy row, "
          "tabs locked to 02/04, expanders everywhere, figures full-width")


def test_artifacts_untouched():
    import subprocess
    out = subprocess.run(["git", "status", "--porcelain", "results/", "weather/"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    tracked = [ln for ln in out.splitlines() if not ln.startswith("??")]
    assert not tracked, tracked
    print("results/ + weather/ tracked artifacts untouched")


def test_export_scoreboard_csv():
    helpers = _import_helpers()
    raw = helpers.scoreboard_csv_bytes()
    with open(os.path.join(ROOT, "results/comparison.csv"), "rb") as f:
        frozen = f.read()
    assert raw == frozen, "CSV download bytes must equal the frozen artifact"
    from src.metrics import COLUMNS
    assert raw.splitlines()[0].decode("utf-8").split(",") == COLUMNS, \
        "CSV header != COLUMNS"
    print("export csv: byte-identical to results/comparison.csv, header == COLUMNS")


def test_export_chart_png():
    helpers = _import_helpers()
    mod = _import_page("04_results.py")
    rows = mod.load_scoreboard()
    png = helpers.fig_to_png_bytes(helpers.build_results_figure(rows))
    assert png[:4] == b"\x89PNG", png[:8]
    assert len(png) > 1024, len(png)
    print("export png: 89 50 4E 47 magic, %d bytes" % len(png))


def test_evidence_zip():
    import io
    import zipfile
    helpers = _import_helpers()
    data = helpers.evidence_zip_bytes()
    assert data[:2] == b"PK", data[:8]
    assert len(data) > 1024, len(data)
    z = zipfile.ZipFile(io.BytesIO(data))
    assert z.namelist() == helpers.ZIP_MEMBERS, z.namelist()
    with open(os.path.join(ROOT, "results/comparison.csv"), "rb") as f:
        assert z.read("comparison.csv") == f.read(), "CSV member drift"
    with open(os.path.join(ROOT, "results/ga_optimized_params.json"),
              "rb") as f:
        assert z.read("ga_optimized_params.json") == f.read(), \
            "GA JSON member drift"
    assert z.read("results_scoreboard.png")[:4] == b"\x89PNG", \
        "chart PNG member magic"
    print("evidence zip: PK magic, 10 members, CSV/JSON byte-identical, "
          "PNG magic ok")


def test_export_verdict():
    helpers = _import_helpers()
    mod = _import_page("04_results.py")
    text = helpers.verdict_text(mod.load_scoreboard())
    for s in ("ga_fuzzy", "holdout", "iae_T", "iae_H", "energy",
              "train_seed", "holdout_seed", "7", "21", "1.0/1.0/0.01"):
        assert s in text, s
    for c in ("onoff", "pid", "fuzzy", "ga_fuzzy"):
        assert c in text, c
    print("export verdict: winner+margins+per-term+seeds/weights present")


def test_export_wiring():
    pages = {}
    for fname in os.listdir(PAGES_DIR):
        if fname.endswith(".py"):
            with open(os.path.join(PAGES_DIR, fname)) as f:
                pages[fname] = f.read()
    expect = {
        "04_results.py": [("comparison.csv", "text/csv"),
                          ("holdout_verdict.txt", "text/plain"),
                          ("results_scoreboard.png", "image/png"),
                          ("greenhouse_evidence_pack.zip",
                           "application/zip")],
        "01_model_sim.py": [("model_sim_chart.png", "image/png")],
        "02_controllers.py": [("controllers_traces.png", "image/png"),
                               ("controllers_overlay.png", "image/png")],
        "03_ga_explorer.py": [("ga_convergence.png", "image/png"),
                               ("ga_convergence_replay.png", "image/png"),
                               ("ga_mfs.png", "image/png"),
                               ("ga_explorer_response.png", "image/png"),
                               ("ga_sensitivity.png", "image/png")],
    }
    total = 0
    for fname, pairs in expect.items():
        src = pages[fname]
        for name, mime in pairs:
            assert name in src, (fname, name)
            assert mime in src, (fname, mime)
        total += src.count("download_button")
    assert total == 12, total
    print("export wiring: 12 download buttons with filenames+MIME across pages")
    src04 = pages["04_results.py"]
    assert "evidence_pack" in src04, "ZIP button missing on 04_results"
    assert "application/zip" in src04, "ZIP MIME missing on 04_results"


def test_overlay_figure():
    from dashboard.helpers import build_overlay_figure
    hours = [h / 60.0 for h in range(240)]
    hists = {"on/off": [25.0 + (i % 7) * 0.4 for i in range(240)],
             "PID": [25.0 + (i % 5) * 0.2 for i in range(240)],
             "hand fuzzy": [25.0 + (i % 3) * 0.1 for i in range(240)],
             "GA fuzzy": [25.0 for _ in range(240)]}
    fig = build_overlay_figure(hours, hists, 25.0)
    lines = fig.axes[0].lines
    assert len(lines) == 5, len(lines)  # 4 controllers + setpoint
    _, labels = fig.axes[0].get_legend_handles_labels()
    assert labels == list(hists) + ["setpoint"], labels
    rh_fig = build_overlay_figure(hours, hists, 70.0, series="RH")
    assert len(rh_fig.axes[0].lines) == 5, len(rh_fig.axes[0].lines)
    assert "humidity" in rh_fig.axes[0].get_title(), rh_fig.axes[0].get_title()
    print("overlay figure: 4 traces + setpoint, labels ok (T and RH)")


def test_sensitivity():
    import math
    from dashboard.helpers import mf_sensitivity_costs, \
        build_sensitivity_figure
    base, rows = mf_sensitivity_costs(n=240)
    assert math.isfinite(base), base
    assert len(rows) == 10, len(rows)  # 5 eT centers x 2 shifts
    assert all(math.isfinite(d) for _, d in rows), rows
    fig = build_sensitivity_figure(rows)
    assert len(fig.axes[0].patches) == 10, len(fig.axes[0].patches)
    print("sensitivity: base %.2f, 10 dcosts finite, 10 bars" % base)


def test_robustness():
    import math
    from dashboard.helpers import robustness_table
    rows = robustness_table(n=120)
    assert len(rows) == 25, len(rows)  # 5 controllers x 5 scenarios
    ctrls = {r["controller"] for r in rows}
    assert ctrls == {"on/off", "PID", "hand fuzzy", "GA fuzzy",
                     "adaptive fuzzy"}, ctrls
    scenarios = {r["scenario"] for r in rows}
    assert scenarios == {"seed7", "seed21", "seed13", "heatwave",
                         "coldsnap"}, scenarios
    for r in rows:
        assert math.isfinite(r["cost"]), r
        assert 0.0 <= r["sat_pct"] <= 100.0, r
    print("robustness: 25 rows, costs finite, saturation bounded")


def test_pareto():
    from dashboard.helpers import pareto_frontier, build_pareto_figure
    pts, front = pareto_frontier()
    assert len(pts) == 4, pts  # 4 holdout controllers, frozen rows only
    assert len(front) >= 1, front
    for p in front:  # nothing dominates a frontier point
        assert not any(q[0] <= p[0] and q[1] <= p[1] and q != p
                       for q in pts), p
    fig = build_pareto_figure(pts, front)
    assert "Pareto" in fig.axes[0].get_title()
    print("pareto: 4 points, %d on frontier" % len(front))


def test_rule_table():
    from dashboard.helpers import rule_table, rule_firing
    t = rule_table()
    assert len(t) == 6 and all(len(r) == 6 for r in t), (len(t), len(t[0]))
    assert t[0][1:] == ["NB", "NS", "ZO", "PS", "PB"], t[0]
    assert t[3][3] == "ZO", t[3]  # ZO/ZO cell damps
    f = rule_firing(0.0, 0.0)
    assert len(f) == 5 and all(len(r) == 5 for r in f)
    assert all(0.0 <= v <= 1.0 for r in f for v in r)
    assert f[2][2] == max(v for r in f for v in r), f[2][2]
    print("rule table 5x5 exact, ZO/ZO dominates at origin")


def test_co2_wiring():
    src01 = _read("dashboard/pages/01_model_sim.py")
    assert "step_co2" in src01 and "co2_valve" in src01, "01 CO2 slider+loop"
    assert "CO2 (ppm)" in src01, "01 CO2 trace panel"
    src05 = _read("dashboard/pages/05_plant_house.py")
    assert "co2" in src05.lower(), "05 CO2 enrichment"
    print("CO2 valve wired on 01, enrichment on 05")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    failures = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:
                failures.append(name)
                print(f"FAIL {name}: {exc!r}")
    if failures:
        print(f"{len(failures)} check(s) failed: {failures}")
        sys.exit(1)
    print("all checks passed")
