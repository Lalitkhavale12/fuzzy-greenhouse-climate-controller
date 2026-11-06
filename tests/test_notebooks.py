"""Plain-assert audit harness for the six milestone notebooks (PROOF-01).

Implements the 10-item Uniform-Pattern Audit Checklist (06-RESEARCH.md
Validation Architecture): nbformat validate warning-free, markdown title
cell, stable cell ids, Agg-before-pyplot, src-only import allowlist,
seed-7 weather guard, savefig path + dpi=120, PNG on disk >= 50 KB,
headless exec of all code cells under Agg, and no metric/membership math
inside 05/06 cells. Threat mitigations enforced: artifact provenance
asserts (CSV header == COLUMNS, JSON schema v2), repo-relative paths,
no evolution entry points in 05/06.

Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_notebooks.py
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_DIR = os.path.join(ROOT, "notebooks")

# Canonical six, front-to-back trail order (01 plant .. 06 verdict).
NOTEBOOKS = [
    "notebooks/01_greenhouse_model.ipynb",
    "notebooks/02_baselines.ipynb",
    "notebooks/03_fuzzy.ipynb",
    "notebooks/04_ga_optimization.ipynb",
    "notebooks/05_comparison.ipynb",
    "notebooks/06_final_results.ipynb",
]

SEALED_FOUR = NOTEBOOKS[:4]

# Checklist item 5: stdlib/third-party roots allowed besides src.*.
ALLOWED_ROOTS = {"numpy", "matplotlib", "csv", "json", "os", "tempfile"}

# Checklist item 6: verbatim guard substring (04 carries this plus its
# locked isolated seed-21 tempfile path, which 05/06 must NOT copy).
GUARD = "generate_weather_profile(CSV, seed=7)"

# Checklist item 10: recomputation entry points 05 must never call.
RECOMPUTE_CALLS = ("compare(", "compute_metrics", "weighted_cost(",
                   "run_closed_loop(", "evolve", "genetic_algorithm")


def _load(rel):
    import nbformat
    nb = nbformat.read(os.path.join(ROOT, rel), as_version=4)
    return nb


def _code_src(nb):
    return "\n".join("".join(c.source)
                     for c in nb.cells if c.cell_type == "code")


def _present():
    return [r for r in NOTEBOOKS if os.path.exists(os.path.join(ROOT, r))]


def test_notebooks_present():
    present = _present()
    for r in SEALED_FOUR:
        assert r in present, f"sealed notebook missing: {r}"
    assert len(present) >= 4, present
    print(f"notebooks present {len(present)}/6: "
          + ", ".join(p.split('/')[-1][:2] for p in present))


def test_validate_warning_free():
    import warnings
    import nbformat
    for rel in _present():
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            nb = nbformat.read(os.path.join(ROOT, rel), as_version=4)
            nbformat.validate(nb)
        msgs = [str(w.message) for w in caught]
        assert not msgs, (rel, msgs)
    print(f"nbformat validate warning-free on {len(_present())} notebooks")


def test_title_cells():
    for rel in _present():
        nb = _load(rel)
        first = nb.cells[0]
        assert first.cell_type == "markdown", (rel, first.cell_type)
        assert "".join(first.source).lstrip().startswith("#"), rel
    print("cell 0 is a markdown title on all present notebooks")


def test_cell_ids():
    for rel in _present():
        nb = _load(rel)
        missing = [i for i, c in enumerate(nb.cells) if not c.get("id")]
        assert not missing, (rel, missing)
    print("every cell carries a non-empty id (F-04-01 closed)")


def test_agg_order():
    for rel in _present():
        src = _code_src(_load(rel))
        assert 'use("Agg")' in src or "use('Agg')" in src, rel
        agg = src.index("Agg")
        assert "import matplotlib.pyplot" in src, rel
        pp = src.index("import matplotlib.pyplot")
        assert agg < pp, (rel, agg, pp)
    print("matplotlib.use(Agg) precedes pyplot import everywhere")


def test_import_allowlist():
    import re
    for rel in _present():
        src = _code_src(_load(rel))
        assert "pandas" not in src, (rel, "pandas forbidden by D-02")
        for line in src.splitlines():
            s = line.strip()
            m = re.match(r"import\s+([\w\.]+)", s)
            if m:
                root = m.group(1).split(".")[0]
                assert root in ALLOWED_ROOTS, (rel, s)
                continue
            m = re.match(r"from\s+([\w\.]+)\s+import\s+", s)
            if m:
                mod = m.group(1)
                assert mod == "src" or mod.startswith("src.") \
                    or mod.split(".")[0] in ALLOWED_ROOTS, (rel, s)
    print("imports restricted to numpy/matplotlib/csv/json/os/tempfile + src.*")


def test_weather_guard():
    for rel in _present():
        src = _code_src(_load(rel))
        assert GUARD in src, (rel, "seed-7 regen-if-absent guard missing")
    print("seed-7 weather guard present on all present notebooks")


def test_savefig_dpi():
    for rel in _present():
        nb = _load(rel)
        src = _code_src(nb)
        stem = os.path.splitext(os.path.basename(rel))[0]
        expect = f'savefig("notebooks/{stem}.png", dpi=120)'
        assert expect in src, (rel, expect)
        assert "dpi=100" not in src, (rel, "stale dpi=100 (F-04-02)")
    print("savefig NN_name.png at locked dpi=120 everywhere")


def test_png_size():
    for rel in _present():
        stem = os.path.splitext(os.path.basename(rel))[0]
        png = os.path.join(ROOT, "notebooks", stem + ".png")
        assert os.path.exists(png), png
        size = os.path.getsize(png)
        assert size >= 51200, (png, size)
        print(f"png-ok {stem}.png {size} B")


def test_no_math_in_0506():
    for rel in ("notebooks/05_comparison.ipynb",
                "notebooks/06_final_results.ipynb"):
        if rel not in _present():
            continue
        src = _code_src(_load(rel))
        for line in src.splitlines():
            s = line.strip()
            assert not s.startswith("def "), (rel, s)
            assert not s.startswith("class "), (rel, s)
        if rel.endswith("05_comparison.ipynb"):
            for call in RECOMPUTE_CALLS:
                assert call not in src, (rel, call)
            assert '"rank"' in src or "['rank']" in src or '["rank"]' in src, \
                (rel, "ranking must read the CSV rank column")
            assert "argsort" not in src, (rel, "order from rank col, never recomputed")
    print("05/06 cells define no metric/MF math; 05 reads rank, never recomputes")


def test_provenance_asserts():
    for rel in ("notebooks/05_comparison.ipynb",
                "notebooks/06_final_results.ipynb"):
        if rel not in _present():
            continue
        src = _code_src(_load(rel))
        assert "== COLUMNS" in src, (rel, "CSV header must assert equality with COLUMNS")
        assert "len(rows) == 8" in src, (rel, "8-row count assert missing")
        for bad in ("/home/", "/Users/", "C:/", "C:\\"):
            assert bad not in src, (rel, bad)
        assert "evolve" not in src and "genetic_algorithm" not in src, \
            (rel, "no evolution entry points in 05/06")
    if "notebooks/06_final_results.ipynb" in _present():
        src = _code_src(_load("notebooks/06_final_results.ipynb"))
        assert "schema_version" in src and "== 2" in src, "06 JSON schema v2 assert"
        assert "load_optimized_mfs" in src, "06 must load tuned curves via validated loader"
    print("artifact provenance asserts + relative paths hold on 05/06")


def test_headless_exec():
    import time
    # Executing a notebook re-runs its savefig, which rewrites the committed
    # PNG bytes (matplotlib embeds producer metadata). Snapshot them first and
    # restore afterwards so a test run never leaves the working tree dirty.
    pngs = [os.path.join(NB_DIR, rel.split("/")[-1].replace(".ipynb", ".png"))
            for rel in _present()]
    snapshot = {p: open(p, "rb").read() for p in pngs if os.path.exists(p)}
    try:
        for rel in _present():
            nb = _load(rel)
            ns = {}
            t0 = time.time()
            for c in nb.cells:
                if c.cell_type == "code":
                    exec("".join(c.source), ns)
            dt = time.time() - t0
            assert dt < 600.0, (rel, dt)  # hang guard only, not a perf bar
            print(f"exec-ok {rel.split('/')[-1]} in {dt:.1f}s")
    finally:
        for path, blob in snapshot.items():
            with open(path, "wb") as f:
                f.write(blob)


def test_results_untracked_changes():
    import subprocess
    out = subprocess.run(["git", "status", "--porcelain", "results/"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    tracked = [ln for ln in out.splitlines() if not ln.startswith("??")]
    assert not tracked, tracked
    print("results/ tracked artifacts untouched")


if __name__ == "__main__":
    import sys
    # "python tests/test_notebooks.py" puts tests/ on sys.path, not the
    # repo root — prepend the root so the in-body `from src import ...` works
    # both standalone and under pytest (which adds rootdir itself).
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
