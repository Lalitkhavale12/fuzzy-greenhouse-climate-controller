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


def _read(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return f.read()


def _stub_streamlit():
    # Deliberately no teardown: this repo has no pytest, so the standalone
    # runner is the only consumer; pages bind the stub at import and need it
    # for the whole session. Revisit if pytest is ever introduced.
    import sys as _sys
    import types as _types

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

            def _noop(*a, **k):
                return None
            return _noop

        def __call__(self, *a, **k):
            return None

    _sys.modules["streamlit"] = _Stub()


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
    assert "schema_version" in src03 and "== 2" in src03, "03 schema v2 assert"
    src04 = pages.get("04_results.py", "")
    assert "== COLUMNS" in src04, "04 CSV header assert"
    assert "len(rows) == 8" in src04, "04 8-row assert"
    for fname, src in pages.items():
        assert 'open(' not in src or '"w"' not in src, (fname, "no writes")
    print("source audits: no Agg/show/savefig, no abs paths, no recompute")


def test_artifacts_untouched():
    import subprocess
    out = subprocess.run(["git", "status", "--porcelain", "results/", "weather/"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    tracked = [ln for ln in out.splitlines() if not ln.startswith("??")]
    assert not tracked, tracked
    print("results/ + weather/ tracked artifacts untouched")


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
