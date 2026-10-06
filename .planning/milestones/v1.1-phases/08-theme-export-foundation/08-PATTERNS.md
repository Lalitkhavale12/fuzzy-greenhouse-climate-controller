# Phase 08: Theme + Export Foundation - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 7 (2 new, 5 modified)
**Analogs found:** 6 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.streamlit/config.toml` (NEW) | config | N/A (static sidecar) | none — greenfield sidecar | no-analog |
| `dashboard/helpers.py` (NEW) | utility (byte builders) | file-I/O + transform | `src/metrics.py` (pure kernels + COLUMNS contract) + `dashboard/pages/04_results.py` lines 30-47 (scoreboard readers to move) | role-match |
| `dashboard/pages/01_model_sim.py` (MOD) | component/view | request-response | itself (`dashboard/pages/01_model_sim.py`) | exact |
| `dashboard/pages/02_controllers.py` (MOD) | component/view | request-response | itself (`dashboard/pages/02_controllers.py`) | exact |
| `dashboard/pages/03_ga_explorer.py` (MOD) | component/view | request-response | itself (`dashboard/pages/03_ga_explorer.py`) | exact |
| `dashboard/pages/04_results.py` (MOD) | component/view | request-response | itself (`dashboard/pages/04_results.py`) | exact |
| `tests/test_dashboard.py` (MOD) | test | N/A (headless harness) | itself (`tests/test_dashboard.py` lines 26-73 stub) | exact |

## Pattern Assignments

### `.streamlit/config.toml` (NEW) (config, N/A)

**Analog:** none — directory absent (RESEARCH.md Environment Availability confirms `.streamlit/` ✗ absent). No TOML/config files exist in repo (no `*.toml`, no `*.cfg` found; repo is py+csv+json+ipynb only).

**Starter palette** (from 08-RESEARCH.md Code Examples — planner/user may adjust hexes within greenhouse family):
```toml
[theme]
base = "light"
primaryColor = "#2E7D32"
backgroundColor = "#F7FAF3"
secondaryBackgroundColor = "#E8F0E1"
textColor = "#263023"
font = "sans serif"
```

**Rules:** `base = "light"` is load-bearing (single-theme discipline, no dark variant — CONTEXT.md D-01). Leave `[theme.sidebar]` unset. Zero test surface — human screenshot is the acceptance check.

---

### `dashboard/helpers.py` (NEW) (utility, file-I/O + transform)

**Analogs:** `src/metrics.py` (pure-function module shape) + `dashboard/pages/04_results.py` lines 30-47 (logic to relocate) + figure idiom from pages 01/02/04.

**Imports pattern** — copy from `src/metrics.py` lines 8-11 and `dashboard/pages/04_results.py` lines 10-22:
```python
import csv
import io
import os

import matplotlib.pyplot as plt
import streamlit as st

from src.metrics import COLUMNS  # frozen column contract, never retyped
```
Note the dual-import fallback in `src/metrics.py` lines 13-28 (`try: from src... except ImportError: from ...`) exists only for `python src/metrics.py` direct-run; helpers.py does NOT need it (pages import as `from src.metrics import ...` under repo-root `sys.path` bootstrap — see Shared Patterns).

**Frozen-byte passthrough** — move/extend `dashboard/pages/04_results.py` lines 30-41 verbatim shape, binary mode per RESEARCH.md Pattern 2:
```python
# dashboard/pages/04_results.py:30-41 (current text-mode source to adapt)
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
```
New helper (RESEARCH.md Pattern 2, `src/metrics.py:32-38` COLUMNS 14-col contract):
```python
def scoreboard_csv_bytes(path: str = "results/comparison.csv") -> bytes:
    with open(path, "rb") as f:       # binary read preserves frozen bytes exactly
        raw = f.read()
    header = raw.split(b"\n", 1)[0].decode("utf-8").split(",")
    assert header == COLUMNS, "stale artifact: header != COLUMNS"
    return raw
```

**Ranking pattern** — copy `dashboard/pages/04_results.py` lines 44-47 exactly (stable rank-column sort, never argsort):
```python
def holdout_ranking(rows):
    """Holdout rows ordered by the CSV rank column (stable: ties keep row order)."""
    holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
    return sorted(holdout, key=lambda r: int(r["rank"]))
```

**Verdict TXT pattern** — mirror `notebooks/05_comparison.ipynb` cell 5 verbatim logic (relative ordering only, `%.2f` costs):
```python
# notebook 05 cell 5 (verified this session):
costs = {r["controller"]: float(r["cost"]) for r in holdout}
assert costs["ga_fuzzy"] < costs["onoff"], costs
assert costs["ga_fuzzy"] < costs["pid"], costs
assert ranked[0]["controller"] == "ga_fuzzy", [r["controller"] for r in ranked]
print("holdout: GA %.2f < on/off %.2f AND GA < PID %.2f" % (costs["ga_fuzzy"], costs["onoff"], costs["pid"]))
print("verdict: GA < on/off AND GA < PID on holdout — METR-02 HOLDS")
```
`verdict_text(rows)` formats: winner + margins + per-term `iae_T/iae_H/energy/cost` for all four holdout controllers + provenance line `train_seed=7 / holdout_seed=21 / weights 1.0/1.0/0.01` (weights locked at `src/metrics.py:30` `W1, W2, W3 = 1.0, 1.0, 0.01`; weathers at `src/metrics.py:43-44`). Reads CSV rows + `results/ga_optimized_params.json` metadata only; never imports `compare`/`evolve`/`genetic_algorithm`.

**PNG byte pattern** — canonical order from RESEARCH.md Pattern 1 (probe-verified `\x89PNG` magic, ~27 KB at dpi=150):
```python
import io
import streamlit as st
import matplotlib.pyplot as plt

@st.cache_data
def figure_png_bytes(build_key: str, dpi: int = 150) -> bytes:
    fig = build_figure(build_key)      # rebuild from frozen/src inputs, explicit colors
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)                        # mandatory — without this the download is empty
    return buf.getvalue()
```
`@st.cache_data` decorator shape copies `dashboard/pages/01_model_sim.py:28-36` (`@st.cache_data def cached_weather`) and `dashboard/pages/02_controllers.py:46-64` (`@st.cache_data def run_all_four`). The stub in `tests/test_dashboard.py:35-43` passes `cache_data` through as identity, so cached helpers stay headless-safe.

**Explicit light-figure colors** — Streamlit theme does NOT restyle matplotlib; every figure builder sets explicit face/ink colors (RESEARCH.md Pitfall 1). Keep default `C0..` series colors on light grounds; set `fig.patch`/`ax` facecolors, tick/label/legend colors, `grid(alpha=0.3)` per existing page idiom (e.g. `01_model_sim.py:74`, `02_controllers.py:81`).

**Error handling pattern** — copy page guard shape `dashboard/pages/04_results.py:52-56` / `03_ga_explorer.py:34-39`:
```python
try:
    rows = load_scoreboard()
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen scoreboard unreadable: %s" % exc)
    st.stop()
```
Helpers raise `ValueError("frozen scoreboard unreadable: %s" % exc)` on `OSError` (04_results.py:35-36); pages catch and `st.error` + `st.stop()`.

---

### `dashboard/pages/01_model_sim.py` (MOD) (component, request-response)

**Analog:** itself — thin wiring target, +1 PNG download button.

**Current figure block** (`01_model_sim.py:69-85`) — figure is built inline then `st.pyplot(fig)`:
```python
fig, ax = plt.subplots(3, 1, figsize=(10, 9))
ax[0].plot(hours, T_trace, label="inside T")
...
fig.suptitle("Simulated greenhouse plant - 24h open-loop (slider duties)")
fig.tight_layout()
st.pyplot(fig)
```
**Wiring to add** (thin only — no `def`, no `savefig`; RESEARCH.md MIME table):
```python
st.download_button("Download chart (PNG)", data=figure_png_bytes("model_sim"),
                   file_name="model_sim_chart.png", mime="image/png")
```
Figure-builder `def`s for PNG export live in helpers, parameterized by page-supplied inputs (rebuild from already-available traces — never recompute science). Canonical order: `savefig(buf)` BEFORE `st.pyplot(fig)`; `buf.seek(0)` before returning bytes.

---

### `dashboard/pages/02_controllers.py` (MOD) (component, request-response)

**Analog:** itself — thin wiring target, +1 PNG download button.

**Cached-run pattern** (`02_controllers.py:46-64`) stays untouched — the PNG builder takes the already-available `(hours, runs)` outputs passed from the page:
```python
@st.cache_data
def run_all_four(T_sp, RH_sp, seed):
    path = resolve_weather(seed)
    ...
    for name, ctl in steps:
        T_h, RH_h, U_h = run_closed_loop(ctl, path, n=1440, T_sp=T_sp, RH_sp=RH_sp)
        runs[name] = (T_h, RH_h, U_h)
```
**Figure block** (`02_controllers.py:74-99`): 3×1 shared-x T/RH/heater-duty figure + `st.pyplot(fig)`. Add one PNG button (`file_name="controllers_traces.png"`, `mime="image/png"`). Never import `compare` in helpers or pages (Pitfall 5).

---

### `dashboard/pages/03_ga_explorer.py` (MOD) (component, request-response)

**Analog:** itself — thin wiring target, +2 PNG buttons, ZERO new defs (hard audit rule).

**Zero-def constraint** (`tests/test_dashboard.py:198-201`):
```python
src03 = pages.get("03_ga_explorer.py", "")
for line in src03.splitlines():
    s = line.strip()
    assert not s.startswith("def "), (fname, s)
    assert not s.startswith("class "), (fname, s)
```
All figure-builder `def`s for the convergence fig (`03_ga_explorer.py:52-63`) and MF before/after fig2 (`03_ga_explorer.py:69-90`) go in helpers, parameterized by the selectbox value passed as an argument (`extra = st.selectbox(...)` at line 67 stays on the page). Add 2 PNG buttons (convergence + MF). Keep `load_optimized_mfs` loader usage (line 24, 31) and `schema_version == 2` assert (lines 37-39).

---

### `dashboard/pages/04_results.py` (MOD) (component, request-response)

**Analog:** itself — wiring target: CSV + TXT + PNG buttons.

**Existing assets to reuse in place** (`04_results.py:24-27` constants; `:30-47` readers; `:62-74` verdict block; `:79-104` scoreboard figure):
```python
CSV_PATH = "results/comparison.csv"
ORDER = ["onoff", "pid", "fuzzy", "ga_fuzzy"]
DISPLAY = {"onoff": "on/off", "pid": "PID", "fuzzy": "hand fuzzy", "ga_fuzzy": "GA fuzzy"}
WEATHERS = ["train-seed7", "holdout-seed21"]
```
```python
# 04_results.py:67-74 verdict block (TXT mirrors this):
winner = ranked[0]["controller"]
cost = {r["controller"]: float(r["cost"]) for r in ranked}
beats = cost["ga_fuzzy"] < cost["onoff"] and cost["ga_fuzzy"] < cost["pid"]
st.success("Verdict: %s ranks #1 on holdout" % DISPLAY[winner])
```
**Buttons to add** (RESEARCH.md MIME + filename contract):
```python
st.download_button("Download scoreboard (CSV)", data=scoreboard_csv_bytes(),
                   file_name="comparison.csv", mime="text/csv")
st.download_button("Download verdict (TXT)", data=verdict_text(rows),
                   file_name="holdout_verdict.txt", mime="text/plain")
st.download_button("Download chart (PNG)", data=figure_png_bytes("results"),
                   file_name="results_scoreboard.png", mime="image/png")
```
`load_scoreboard`/`holdout_ranking` stay on the page (tests import them: `test_results_helper` at `tests/test_dashboard.py:116-129` calls `mod.load_scoreboard()` + `mod.holdout_ranking(rows)`); helpers expose byte builders that reuse the same asserts (`== COLUMNS`, `len(rows) == 8`).

---

### `tests/test_dashboard.py` (MOD) (test, N/A)

**Analog:** itself — extend `_stub_streamlit` in the SAME commit as first page use of `download_button`.

**Stub pattern** (`tests/test_dashboard.py:26-73`): `_Stub.__getattr__` returns `_noop` (returns `None`) for unknown attrs — `download_button` is safe at import even unstubbed, but RESEARCH.md Wave 0 requires an explicit entry for forward-compat. Copy the adjacent `selectbox`/`slider` entry shape:
```python
# tests/test_dashboard.py:58-64 (shape to copy for download_button entry)
if name == "selectbox":
    def sb(label, options, index=0, *a, **k):
        try:
            return list(options)[index]
        except Exception:
            return None
    return sb
```
Suggested minimal entry following the same style:
```python
if name == "download_button":
    def dl(label, *a, **k):
        return None
    return dl
```
**Headless export assertions** (RESEARCH.md Validation Architecture → new test fns or helpers' `__main__` self-check):
- CSV bytes `== open('results/comparison.csv','rb').read()`, header `== COLUMNS`
- PNG `figure_png_bytes(...)[:8] == b'\x89PNG\r\n\x1a\n'`
- TXT contains `ga_fuzzy`, per-term `iae_T/iae_H/energy`, seeds 7/21, weights `1.0/1.0/0.01`

---

## Shared Patterns

### Repo-root bootstrap (all dashboard files)
**Source:** `dashboard/pages/04_results.py:10-15` (identical in 01/02/03 pages + `dashboard/app.py:10-14`)
**Apply to:** `dashboard/helpers.py` (new) — same two lines so `from src.metrics import COLUMNS` resolves under Streamlit cwd:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```
Note `dashboard/app.py:12-14` uses one fewer `dirname` (it sits one level higher). Helpers.py sits at `dashboard/` level — use the app.py depth (two `dirname`s), NOT the pages depth (three).

### Thin-page / fat-helper split (headless audits)
**Source:** `tests/test_dashboard.py:174-209` (`test_source_audits`)
**Apply to:** all four page modifications + helpers.py
- No `savefig` / `plt.show` / `use("Agg")` in any page (lines 183-185)
- No absolute paths (`/home/`, `/Users/`, `C:/`, `C:\`) (lines 186-187)
- No `"w"` opens in pages — in-memory `BytesIO` only (lines 207-208)
- No top-level `def `/`class ` on 03 (lines 199-202); ALL new `def`s in helpers
- 04 keeps `== COLUMNS` + `len(rows) == 8` asserts (lines 204-206); 03 keeps `schema_version` + `== 2` (line 203)

### Frozen read-only + provenance asserts
**Source:** `src/metrics.py:30-44` (locked weights/COLUMNS/WEATHERS) + `dashboard/pages/04_results.py:39-40`
**Apply to:** helpers.py byte builders + all page wiring
```python
W1, W2, W3 = 1.0, 1.0, 0.01  # src/metrics.py:30 locked fitness weights
COLUMNS = ["controller", "weather", "rmse_T", ...]  # 14 cols, src/metrics.py:32-35
WEATHERS = [("train-seed7", "weather/weather_profile.csv"),
            ("holdout-seed21", "weather/holdout_21.csv")]  # src/metrics.py:43-44
```
Helpers read two hardcoded frozen paths only (`results/comparison.csv`, `results/ga_optimized_params.json`); `file_name` values are hardcoded literals; `data=` carries bytes, never a user path (RESEARCH.md Security Domain).

### Download-button MIME contract
**Source:** 08-RESEARCH.md MIME + filename table (no codebase analog — first `download_button` use in repo)
**Apply to:** all page wiring
| Download | `data` type | `mime` | `file_name` |
|----------|-------------|--------|-------------|
| Scoreboard CSV | `bytes` (frozen file) | `text/csv` | `comparison.csv` |
| Verdict TXT | `str` (utf-8) | `text/plain` | `holdout_verdict.txt` |
| Chart PNG | `bytes` (`\x89PNG` magic) | `image/png` | `<page>_<chart>.png` |

### Artifacts-untouched merge gate
**Source:** `tests/test_dashboard.py:212-217` (`test_artifacts_untouched`)
**Apply to:** every commit in this phase
```python
out = subprocess.run(["git", "status", "--porcelain", "results/", "weather/"],
                     capture_output=True, text=True, cwd=ROOT).stdout
tracked = [ln for ln in out.splitlines() if not ln.startswith("??")]
assert not tracked, tracked
```
Verified this session: `git status --porcelain results/ weather/` shows only `??` untracked logs, zero tracked modifications — phase must keep it that way.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.streamlit/config.toml` | config | N/A | No TOML/config analog exists in repo; greenfield sidecar. Planner uses RESEARCH.md Code Examples palette + official `[theme]` key set. No tracked-source violation — file is new, not copied. |

## Metadata

**Analog search scope:** `dashboard/`, `dashboard/pages/`, `src/`, `tests/`, `notebooks/05_comparison.ipynb` (verdict cell), `results/comparison.csv` (byte source)
**Files scanned:** 4 pages + app.py + test_dashboard.py + src/metrics.py + notebook 05 + comparison.csv
**Tracked-source gate:** all analog paths verified via `git ls-files` (dashboard/app.py, pages/01-04, src/metrics.py, tests/test_dashboard.py, notebooks/05_comparison.ipynb, results/comparison.csv all tracked). No mirror paths emitted.
**Pattern extraction date:** 2026-09-29
