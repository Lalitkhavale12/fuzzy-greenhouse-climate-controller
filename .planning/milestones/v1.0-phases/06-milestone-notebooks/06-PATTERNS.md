# Phase 6: Milestone Notebooks - Pattern Map

**Mapped:** 2026-09-28
**Files analyzed:** 5 (2 new notebooks + 2 PNGs + 1 test file; 1 modified notebook)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `notebooks/05_comparison.ipynb` | notebook (artifact-reader scoreboard) | file-I/O (CSV read) + batch plot | `notebooks/01_greenhouse_model.ipynb` | exact (cell shape) |
| `notebooks/05_comparison.png` | build artifact (committed plot) | transform (fig → PNG) | `notebooks/01_greenhouse_model.png` | exact |
| `notebooks/06_final_results.ipynb` | notebook (end-to-end narrative) | file-I/O (CSV+JSON+PNG reads) + batch plot | `notebooks/04_ga_optimization.ipynb` | exact |
| `notebooks/06_final_results.png` | build artifact (committed plot) | transform (fig → PNG) | `notebooks/03_fuzzy.png` | exact |
| `tests/test_notebooks.py` (new audit harness) | test | batch (structural + headless exec) | `tests/test_metrics.py` | role-match |
| `notebooks/04_ga_optimization.ipynb` (modify: F-04-01/02/03) | notebook (fix only) | file-I/O + batch plot | itself (`notebooks/04_ga_optimization.ipynb`) + `notebooks/01_greenhouse_model.ipynb` (id convention) | exact |

All analog paths verified git-tracked via `git ls-files` (2026-09-28): all four `notebooks/0*.ipynb`, `tests/test_metrics.py`, `src/metrics.py`, `src/fuzzy_controller.py`, `src/ga_fuzzy_controller.py` are tracked source. No mirror paths used.

## Pattern Assignments

### `notebooks/05_comparison.ipynb` (notebook, file-I/O + batch plot)

**Analog:** `notebooks/01_greenhouse_model.ipynb` (5 cells: `title/imports/weather/run/plot`; canonical cell shape all of 01–03 follow)

**Notebook JSON envelope** (01 lines 1-6, 103-117): every notebook is `{"cells": [...], "metadata": {"kernelspec"...}, "nbformat": 4, "nbformat_minor": 5}`. Code cells carry `"execution_count": null, "outputs": []` (never commit outputs — proof is the PNG + headless re-run). Every cell carries a stable `"id"` (`title/imports/weather/run/plot` convention).

**Imports pattern** (01 lines 19-28):
```python
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.greenhouse_model import step, load_weather_profile, daytime_solar, params
from src.weather_profile_generator import generate_weather_profile

print("params:", params)
```
Rule: numpy → matplotlib → `use("Agg")` → pyplot → `src.*` → stdlib. 05's src import is `from src.metrics import COLUMNS` (+ stdlib `csv/os`). No pandas (locked D-02). Keep a trailing `print` probe line.

**Weather-guard pattern** (01 lines 37-42 — copy verbatim even though 05 needs no weather; uniformity item):
```python
# Weather input (D-10): regenerate the seed-7 profile only if absent, then load.
import os
CSV = "weather/weather_profile.csv"
if not os.path.exists(CSV):
    generate_weather_profile(CSV, seed=7)
```
For 05: keep the guard verbatim, then load weather arrays the same way (`load_weather_profile` + `np.interp`) OR skip the interp if unused — but the guard substring `generate_weather_profile(CSV, seed=7)` must be present for the mechanical audit (checklist item 6).

**Artifact-reader core pattern** (established 04 JSON-load cell + stdlib csv convention; RESEARCH.md §Pattern):
```python
import csv
from src.metrics import COLUMNS  # column-name contract, never retyped
CSV_PATH = "results/comparison.csv"
with open(CSV_PATH) as f:
    rows = list(csv.DictReader(f))
assert list(rows[0].keys()) == COLUMNS, "stale artifact: header != COLUMNS"
assert len(rows) == 8, "expected 4 controllers x 2 weathers"
holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
costs = {r["controller"]: float(r["cost"]) for r in holdout}
assert costs["ga_fuzzy"] < costs["onoff"] and costs["ga_fuzzy"] < costs["pid"]
print("verdict: GA < on/off AND GA < PID on holdout — METR-02 HOLDS")
```
Display order for bars: onoff, pid, fuzzy, ga_fuzzy. Plottable panels: `iae_T`, `iae_H`, `energy`, `cost` (+ holdout `barh` ranked by `rank` col). Cost panel SHOULD use log scale (6× range GA ~110 vs 500–645). Do NOT plot `settling_min` (all `inf`) — text annotation instead. Read `rank` column; never recompute ordering.

**savefig pattern** (01 lines 97-100):
```python
plt.suptitle("...")
plt.tight_layout()
plt.savefig("notebooks/05_comparison.png", dpi=120)
plt.show()
```
`plt.show()` is a harmless Agg no-op — keep for uniformity. `dpi=120` is locked; filename must match `NN_name.png` (`05_comparison.png` keeps Phase-7 embedding stable).

---

### `notebooks/06_final_results.ipynb` (notebook, file-I/O + batch plot)

**Analog:** `notebooks/04_ga_optimization.ipynb` (6 cells; the artifact-read + verdict + MF-overlay precedent). Cell-shape still follows 01–03; content follows 04.

**Imports pattern** (04 imports cell verbatim head):
```python
import json
import os
import tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.greenhouse_model import (step, load_weather_profile, daytime_solar,
                                  params, relative_humidity, wsat_g_per_kg)
from src.weather_profile_generator import generate_weather_profile
from src.onoff_controller import onoff_step
from src.pid_controller import pid_step
from src.fuzzy_controller import fuzzy_step, FUZZY_MFS, tri
from src.ga_fuzzy_controller import ga_fuzzy_step, load_optimized_mfs
from src.genetic_algorithm import W1, W2, W3  # locked weights: proof must match fitness
```
For 06: same shape; required src imports are `FUZZY_MFS, LABELS, tri` from `src.fuzzy_controller` + `load_optimized_mfs` from `src.ga_fuzzy_controller` + `COLUMNS` from `src.metrics`; stdlib `csv, json, os`; numpy + matplotlib. Do NOT import evolution entry points (no-inline-evolution threat).

**Cell order** (locked by D-03, RESEARCH.md §06 spec): 1 markdown title `# Final Results: GA-Optimized Fuzzy Wins on Holdout (PROOF-01)` → 2 imports+Agg → 3 verbatim seed-7 weather guard → 4 CSV scoreboard load (assert header == COLUMNS, print 8-row table) → 5 GA artifact load → 6 verdict restatement (relative asserts, restate never recompute) → 7 MF before/after overlays → 8 prior-trail montage (`plt.imread`/`imshow` 2×2 of `notebooks/0{1..4}_*.png`, axis-off) → 9 closing-claim markdown → 10 `savefig("notebooks/06_final_results.png", dpi=120)`.

**GA-artifact load pattern** (04 weather cell verbatim):
```python
JSON = "results/ga_optimized_params.json"
with open(JSON) as _f:
    d = json.load(_f)
assert d["schema_version"] == 2 and d["population"] == 50 and d["generations"] == 50, \
    "stale artifact: expected run-3 schema v2 50x50"
mfs_opt, gains_opt = load_optimized_mfs(JSON)
print("schema v%s" % d.get("schema_version", 1),
      "| train fit %.2f" % d["fitness"], "| coupling", d.get("coupling"))
```
Schema v2 keys on disk: `mfs` (6 groups), `coupling{k_heat,k_vent}` = 0.05/0.05, `fitness` 107.14, `weights{1.0,1.0,0.01}`, `history{best,mean}` 50 gens, `train_seed` 7, `holdout_seed` 21. Prefer `load_optimized_mfs` over raw `json.load` indexing (fail-fast asserts in `src/ga_fuzzy_controller.py:53-75`).

**Verdict pattern** (04 holdout cell verbatim tail):
```python
# Verdict: RELATIVE ordering only — GA below on/off AND below PID, no absolutes.
assert costs["GA fuzzy"] < costs["on/off"], (costs["GA fuzzy"], costs["on/off"])
assert costs["GA fuzzy"] < costs["PID"], (costs["GA fuzzy"], costs["PID"])
print("verdict: GA < on/off AND GA < PID on ...")
```
For 06 keyed by CSV controller names (`ga_fuzzy/onoff/pid`), restating cell-4 values — never recomputing cost from histories.

**MF before/after overlay pattern** (04 `ax[1,1]` eH overlay + 03 full-grid before-reference):
```python
# Source: src/fuzzy_controller.py:20-29 hand values; JSON mfs.eH after-values
import numpy as np
from src.fuzzy_controller import FUZZY_MFS, tri
grid = np.linspace(-40, 40, 400)  # eH universe
for c, w in zip(FUZZY_MFS["eH"]["centers"], FUZZY_MFS["eH"]["widths"]):
    ax.plot(grid, [tri(x, c, w) for x in grid], "C0-", alpha=0.5)   # hand (before)
for c, w in zip(mfs_opt["eH"]["centers"], mfs_opt["eH"]["widths"]):
    ax.plot(grid, [tri(x, c, w) for x in grid], "C1--", alpha=0.8)  # GA (after)
```
Hand `eH` centers `[-30,-15,0,15,30]` widths `15.0` (`src/fuzzy_controller.py:26`); GA `eH` centers `[-4.60,0.19,18.68,32.91,40.0]` widths `[14.82,7.47,17.85,10.04,15.91]`. 03's per-key grid idiom for multi-group panels: `xs = np.linspace(c[0]-wdt[0], c[-1]+wdt[-1], 400)` + per-label `tri` plot loop with `LABELS` legend. Annotate gains `k_heat/k_vent = 0.05/0.05`.

**Montage pattern** (new technique, standard matplotlib, Agg-safe): `plt.imread("notebooks/01_greenhouse_model.png")` + `ax.imshow(img); ax.axis("off")` in a 2×2 panel. Fallback if headless issues: markdown `![]()` links (A1).

---

### `tests/test_notebooks.py` (test, batch) — NEW FILE

**Analog:** `tests/test_metrics.py` (191 lines; plain-assert suite + `__main__` runner — the repo test convention)

**File header/docstring pattern** (test_metrics.py lines 1-13):
```python
"""Plain-assert suite for ... (REQ-IDS).

<what it proves, 2-3 lines>
Pytest-compatible naming (def test_*), but runs standalone because pytest is
not installed (RESEARCH.md Validation Architecture). Imports live inside the
test bodies so the file is runnable in wave-0 ordering.

Run:  python tests/test_notebooks.py
"""
```

**Test-body pattern** (in-body imports; plain asserts; probe print — e.g. lines 16-27, 80-96):
```python
def test_<name>():
    import nbformat  # in-body import
    ...
    assert <structural condition>, <offending value>  # value in message
    print("<human-readable probe line>")
```
Keep the 05-CONTEXT-referenced conventions: `compare()`-style hang guard (`t0 = time.time()` … `assert dt < 600.0`), comments-only reference numbers (never assert absolutes — relative ordering only).

**`__main__` runner pattern** (test_metrics.py lines 173-191 — copy verbatim, only the docstring changes):
```python
if __name__ == "__main__":
    import sys, os
    # "python tests/test_notebooks.py" puts tests/ on sys.path, not the
    # repo root — prepend the root so the in-body `from src import ...` works
    # both standalone and under pytest (which adds rootdir itself).
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
```

**Structural-audit check body** (RESEARCH.md §Code Examples — nbformat 5.10.4 API; implements the 10-item Uniform-Pattern Audit Checklist):
```python
import nbformat, json
nb = nbformat.read("notebooks/05_comparison.ipynb", as_version=4)
nbformat.validate(nb)                                   # raises on bad schema
codes = [c for c in nb.cells if c.cell_type == "code"]
assert nb.cells[0].cell_type == "markdown" and nb.cells[0].source.startswith("#")
assert all(c.get("id") for c in nb.cells), "every cell needs an id (F-04-01)"
src = "\n".join("".join(c.source) for c in codes)
agg, pp = src.index('use("Agg")'), src.index("import matplotlib.pyplot")
assert agg < pp, "Agg must precede pyplot import"
assert 'generate_weather_profile(CSV, seed=7)' in src, "weather guard"
assert 'dpi=120' in src and 'savefig("notebooks/05_comparison.png"' in src
```
Plus per-notebook loop over all six, PNG `size ≥50 KB` check, headless `exec` of code cells under Agg (probe-verified on 01), and the no-duplication grep (`def `/`class ` scan in 05/06 cells; 05 must not call `compare(`/`compute_metrics`).

**No `conftest.py`, no pytest config** — repo uses no pytest (Wave 0 gap: none needed; nbformat/matplotlib/numpy already installed).

---

### `notebooks/04_ga_optimization.ipynb` (modify — 3 flagged fixes only)

**Analog:** itself + `notebooks/01_greenhouse_model.ipynb` (id convention source)

1. **F-04-01 (required): cell ids.** All six 04 cells lack `id`; 01/02/03 use `"id": "title"/"imports"/"weather"/"run"/"plot"`. Assign `title, imports, weather, verdict, verdict-note, plot` (verdict-note = the markdown verdict-framing cell). Zero behavior change; kills the `MissingIDFieldWarning` (future hard error).
2. **F-04-02 (required): dpi.** Verbatim tail: `fig.savefig("notebooks/04_ga_optimization.png", dpi=100)` → `dpi=120`. Then regenerate PNG headless (re-runs holdout proof cell: 4×1440 seeded loops, deterministic, identical verdict). Commit PNG in the same atomic commit (Pitfall 3).
3. **F-04-03 (opportunistic, same diff): dup `import os`.** `os` imported in imports cell AND re-imported at top of weather cell — collapse to one. 03/04 empty metadata (no kernelspec) is cosmetic — normalize only if free, never standalone.

Sealed-artifact rule: fix ONLY these; 04's live holdout re-runs are locked Phase-4 design, not a D-02 violation (D-02 no-recompute applies to 05 only).

---

## Shared Patterns

### Agg-before-pyplot
**Source:** `notebooks/01_greenhouse_model.ipynb` lines 20-23
**Apply to:** 05, 06 (all code notebooks)
```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```
`use("Agg")` index must precede `import matplotlib.pyplot` index in concatenated code sources (audit checklist item 4). Works without display server or `jupyter` CLI (absent — verified).

### Weather guard (verbatim, seed 7)
**Source:** `notebooks/01_greenhouse_model.ipynb` lines 38-42
**Apply to:** 05, 06 (pattern-uniformity no-op when CSV exists; satisfies mechanical audit on all six identically)
```python
import os
CSV = "weather/weather_profile.csv"
if not os.path.exists(CSV):
    generate_weather_profile(CSV, seed=7)
```
04's isolated `tempfile` seed-21 holdout path (`holdout_csv = os.path.join(tempfile.mkdtemp(), "holdout_21.csv"); generate_weather_profile(holdout_csv, seed=21)`) is locked design, not a deviation — 05/06 must NOT copy it (no simulation in 05/06).

### savefig + committed PNG
**Source:** `notebooks/01_greenhouse_model.ipynb` lines 97-100; 03 multi-panel precedent for figure layout
**Apply to:** 05 (`notebooks/05_comparison.png`), 06 (`notebooks/06_final_results.png`), 04 regen
```python
plt.suptitle("...")
plt.tight_layout()
plt.savefig("notebooks/NN_name.png", dpi=120)
plt.show()
```
`dpi=120` locked. Filenames stable for Phase-7 embedding. Every notebook edit ends with headless re-exec + `savefig` + PNG committed atomically (`scope(phase-plan):` commits).

### Artifact validation (fail-closed reads)
**Source:** `src/ga_fuzzy_controller.py` lines 53-75 (`load_optimized_mfs` asserts); `src/metrics.py` lines 30-38 (`W1/W2/W3`, `COLUMNS`); 04 assert cells
**Apply to:** all 05/06 artifact-reading cells
- CSV: `assert list(rows[0].keys()) == COLUMNS` + `assert len(rows) == 8` before plotting.
- JSON: `assert d["schema_version"] == 2 and d["population"] == 50 and d["generations"] == 50` + `load_optimized_mfs(JSON)` (exact key set, len-5, widths > 0, finite, coupling bounds).
- JSON-only via stdlib `json` — never pickle/eval (module contract). Repo-relative paths only (`weather/`, `results/`, `notebooks/`).
- `results/comparison.csv` is byte-guarded: `git status --porcelain results/` must show untouched after the phase (05/06 never rewrite it).

### Relative verdict asserts (no absolutes)
**Source:** `tests/test_metrics.py` lines 99-112 (`test_holdout_ordering`); 04 verdict cell
**Apply to:** 05 verdict cell, 06 verdict restatement, `tests/test_notebooks.py` holdout check
```python
hold = {r["controller"]: r["cost"] for r in rows
        if r["weather"] == "holdout-seed21"}
assert hold["ga_fuzzy"] < hold["onoff"], hold
assert hold["ga_fuzzy"] < hold["pid"], hold
```
Reference numbers live in comments only (GA ~114.28, on/off ~513.75, PID ~645.26) — never as asserts (re-litigating absolutes violates Phase-4 Amendment A2).

### MF math source (`tri`, `FUZZY_MFS`)
**Source:** `src/fuzzy_controller.py` lines 18-29 (`LABELS`, `FUZZY_MFS`), line 40-42 (`tri`)
**Apply to:** 06 MF panel (03 plot cell is the layout precedent: `gridspec` + per-key `tri` loops + `LABELS` legends)
```python
def tri(x, c, w):
    """Triangular membership in [0,1]. Edge MFs saturate via input clipping in infer()."""
    return float(np.clip(1.0 - abs(float(x) - c) / w, 0.0, 1.0))
```
Any new MF/cost math in a cell is a defect — import from `src/`, never inline (audit greps 05/06 cells for `def `).

### Test-file convention
**Source:** `tests/test_metrics.py` (docstring + in-body imports + `__main__` runner, lines 1-13 + 173-191)
**Apply to:** `tests/test_notebooks.py`
Plain asserts with offending value in message + `print` probe line per test; `sys.path` root-prepend in `__main__`; sequential full-suite command `python tests/test_*.py` each self-running.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| *(none)* | — | — | Every deliverable has a tracked analog: 05←01 (cell shape), 06←04 (artifact/verdict/MF), harness←test_metrics.py, PNGs←existing PNGs |

Genuinely new techniques with no repo precedent (planner: use RESEARCH.md, not codebase): 06 cell-8 `imread`/`imshow` PNG montage (standard matplotlib, fallback markdown `![]()`); 05 log-scale/broken-axis cost panel (presentational, planner discretion); headless `exec`-under-Agg verification harness shape (probe-verified on 01, no `jupyter` CLI exists).

## Metadata

**Analog search scope:** `notebooks/`, `tests/`, `src/`, `results/` (all git-tracked; `git ls-files` verified)
**Files scanned:** 4 notebooks (JSON cell-by-cell) + `tests/test_metrics.py` + `src/metrics.py` + `src/fuzzy_controller.py` + `src/ga_fuzzy_controller.py` + `results/comparison.csv` + `results/ga_optimized_params.json` (via RESEARCH.md verified reads)
**Pattern extraction date:** 2026-09-28
