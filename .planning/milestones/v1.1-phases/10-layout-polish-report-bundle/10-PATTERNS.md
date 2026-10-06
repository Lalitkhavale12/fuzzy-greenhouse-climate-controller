# Phase 10: Layout Polish + Report Bundle - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 7 (6 modified + 1 possibly-touched)
**Analogs found:** 7 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `dashboard/helpers.py` (ADD `evidence_zip_bytes` + `ZIP_MEMBERS`) | utility (shared byte-builder module) | transform (frozen bytes in → assembled ZIP bytes out) | `dashboard/helpers.py` itself (`scoreboard_csv_bytes` lines 53-65, `fig_to_png_bytes` lines 114-119, `verdict_text` lines 74-111) | exact |
| `dashboard/pages/04_results.py` (KPI row + train/holdout tabs + expander + ZIP `download_button`) | component (page) | request-response | `dashboard/pages/04_results.py` current (`st.metric` lines 57-60, `download_button` lines 53-54/69-70/73-74, fail-closed `try/except` lines 43-49) | exact |
| `dashboard/pages/02_controllers.py` (KPI row + T/RH/energy tabs + expander) | component (page) | request-response | `dashboard/pages/02_controllers.py` current (sliders lines 67-70, `download_button`+`pyplot` lines 89-91) + `dashboard/pages/03_ga_explorer.py` `st.columns` lines 59-63 | role-match |
| `dashboard/pages/01_model_sim.py` (KPI row + provenance expander) | component (page) | request-response | `dashboard/pages/01_model_sim.py` current (`st.metric` lines 67-68, `download_button`+`pyplot` lines 90-92) | exact |
| `dashboard/pages/03_ga_explorer.py` (KPI row + expander; NO new `def`) | component (page) | request-response | `dashboard/pages/03_ga_explorer.py` current (`st.metric` lines 47-49/80-82, `st.columns` lines 59-63, fail-closed `try/except` lines 33-42) | exact |
| `dashboard/app.py` (KPI row ONLY if trivial, else untouched) | component (landing) | request-response | `dashboard/app.py` (config-then-title lines 18-20; landing-only bans in `tests/test_dashboard.py::test_page_set` lines 124-125) | role-match |
| `tests/test_dashboard.py` (stub `tabs`/`__enter__` + `test_layout_elements` + `test_evidence_zip` + audit extensions) | test | batch | `tests/test_dashboard.py` itself (`_stub_streamlit` lines 26-77, `test_export_*` lines 401-433, `test_source_audits` lines 354-389, `test_export_wiring` lines 435-460) | exact |

No new files expected. No new `def` on `03_ga_explorer.py` (audit bans `^def `/`^class ` — see `test_source_audits` lines 378-382).

## Pattern Assignments

### `dashboard/helpers.py` (utility, transform)

**Analog:** `dashboard/helpers.py` — the new `evidence_zip_bytes()` joins the three Phase-8 builders; same module, same conventions.

**Imports pattern** (lines 27-38):
```python
import copy
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np

from src.metrics import COLUMNS  # frozen column contract, never retyped
```
New need: `import zipfile` alongside `io` (both stdlib, zero new deps). Keep `ROOT`/`SCOREBOARD_PATH` convention (lines 40-41):
```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOREBOARD_PATH = os.path.join(ROOT, "results", "comparison.csv")
```

**Core byte-builder pattern — frozen raw read** (lines 53-65, `scoreboard_csv_bytes`):
```python
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
```
Copy for: notebook PNGs + GA JSON members — `open(..., "rb").read()`, never `json.dumps` re-serialization (breaks byte-stability; RESEARCH.md Alternatives Considered).

**Core byte-builder pattern — close-then-`getvalue()`** (lines 114-119, `fig_to_png_bytes`):
```python
def fig_to_png_bytes(fig, dpi=150):
    """Serialize an in-hand figure to PNG bytes (never closes the figure)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)  # mandatory — without this the download is empty
    return buf.getvalue()
```
Copy for: `evidence_zip_bytes()` — exit the `with zipfile.ZipFile(...)` block first, then `return buf.getvalue()` (or `buf.seek(0)` if passing the buffer). `download_button` serves zero bytes if the cursor is at end-of-stream (Pitfall 2).

**Row-reading pattern — rank column, never recompute** (lines 68-71, `holdout_ranking`):
```python
def holdout_ranking(rows):
    """Holdout rows ordered by the CSV rank column (stable: ties keep row order)."""
    holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
    return sorted(holdout, key=lambda r: int(r["rank"]))
```
Copy for: KPI card values — `kpi = next(r for r in holdout_rows if r["controller"] == "ga_fuzzy")`, then `float(kpi["cost"])`, `kpi["rank"]`, `float(kpi["iae_T"])`, `float(kpi["iae_H"])`. Never `argsort`/`compare(`/`all_metrics` on the KPI/Results path (Pitfall 3).

**Error handling pattern** (lines 55-59 + 81-86):
```python
    except OSError as exc:
        raise ValueError("frozen scoreboard unreadable: %s" % exc)
...
    if not ranked:
        raise ValueError("no holdout-seed21 rows in scoreboard")
```
Copy: `ValueError("...: %s" % exc)` on unreadable frozen inputs. Pages catch `(OSError, ValueError, AssertionError, KeyError)` → `st.error` + `st.stop()` (see `04_results.py` lines 43-49).

**Self-check pattern** (lines 351-364, `if __name__ == "__main__":`):
```python
if __name__ == "__main__":
    with open(SCOREBOARD_PATH) as _f:
        _rows = list(csv.DictReader(_f))
    with open(SCOREBOARD_PATH, "rb") as _fb:
        assert scoreboard_csv_bytes() == _fb.read()
    ...
    _png = fig_to_png_bytes(build_results_figure(_rows))
    assert _png[:4] == b"\x89PNG" and len(_png) > 1024, len(_png)
    print("helpers self-check: CSV ==, verdict substrings ok, PNG magic ok")
```
Copy: extend with `evidence_zip_bytes()` asserts (`[:2] == b"PK"`, `namelist() == ZIP_MEMBERS`) in the same block. Run: `python dashboard/helpers.py`.

**ZIP builder shape to write** (new code — RESEARCH.md Pattern 4, probe-verified):
```python
import io, zipfile
def evidence_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("comparison.csv", scoreboard_csv_bytes())
        z.writestr("holdout_verdict.txt", verdict_text(load_rows()).encode("utf-8"))
        z.writestr("results_scoreboard.png", fig_to_png_bytes(build_results_figure(rows)))
        for name in ("01_greenhouse_model.png", ..., "06_final_results.png"):
            z.writestr(name, open("notebooks/" + name, "rb").read())
        z.writestr("ga_optimized_params.json", open("results/ga_optimized_params.json", "rb").read())
    return buf.getvalue()
```
Plus single ordered `ZIP_MEMBERS` constant (10 members — see Shared Patterns / ZIP member allowlist). Member bytes come from existing builders + raw file reads only.

---

### `dashboard/pages/04_results.py` (component, request-response)

**Analog:** `dashboard/pages/04_results.py` itself — the page already owns the KPI-adjacent metric loop, all three download wirings, and the fail-closed guard.

**Imports pattern** (lines 10-22):
```python
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from src.metrics import COLUMNS  # frozen column contract, never retyped
from dashboard.helpers import (ORDER, DISPLAY, WEATHERS, holdout_ranking,
                               build_results_figure, fig_to_png_bytes,
                               scoreboard_csv_bytes, verdict_text)
```
Copy: add `evidence_zip_bytes` (and `ZIP_MEMBERS` if the page asserts the list) to the existing `dashboard.helpers` import — no new third-party imports.

**Fail-closed guard pattern** (lines 27-49):
```python
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
...
try:
    rows = load_scoreboard()
    ranked = holdout_ranking(rows)
    txt = verdict_text(rows)
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen scoreboard unreadable: %s" % exc)
    st.stop()
```
Copy: KPI row reads the already-loaded `ranked` rows — no new loading path, no new `try` block.

**KPI/metric pattern to refactor into uniform row** (lines 56-60):
```python
for r in ranked:
    st.metric(DISPLAY[r["controller"]],
              "cost %.2f" % float(r["cost"]),
              "rank #%s" % r["rank"])
```
Copy/replace with the uniform 4-card row (RESEARCH.md Pattern 1): one `st.columns(4)` of `st.metric` — holdout cost, rank, IAE_T, IAE_H for `ga_fuzzy` — rendered identically on all four pages. Keep `DISPLAY[...]` label mapping and `"%.2f" % float(...)` formatting.

**Download wiring pattern** (lines 53-54, 69-70, 73-74):
```python
st.download_button("Download scoreboard (CSV)", data=scoreboard_csv_bytes(),
                   file_name="comparison.csv", mime="text/csv")
...
st.download_button("Download verdict (TXT)", data=txt,
                   file_name="holdout_verdict.txt", mime="text/plain")
...
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="results_scoreboard.png", mime="image/png")
st.pyplot(fig)
```
Copy for the ZIP button (RESEARCH.md Code Examples):
```python
st.download_button("Download evidence pack (ZIP)", data=evidence_zip_bytes(),
                   file_name="greenhouse_evidence_pack.zip", mime="application/zip")
```
`file_name` literal lives on the page, never in helpers (T-08-02). MIME `application/zip`.

**Figure pattern** (line 72): `fig = build_results_figure(rows)  # single source of truth (helpers.py)` — figures built by helpers, page only `st.pyplot(fig)`. Never `savefig`/`plt.show`/`Agg` on any page (audit-banned).

---

### `dashboard/pages/02_controllers.py` (component, request-response)

**Analog:** `dashboard/pages/02_controllers.py` itself (slider + download wiring) + `03_ga_explorer.py` `st.columns` unpack pattern for the tab-unpack analog.

**Imports pattern** (lines 12-31):
```python
import functools
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np

import streamlit as st

from src.metrics import all_metrics, run_closed_loop
...
from dashboard.helpers import build_scenario_figure, fig_to_png_bytes, \
    scenario_delta
```
Copy: `sys.path`/`os.chdir` preamble is identical on all four pages — keep verbatim. Add `holdout_ranking`-adjacent KPI reads only via existing imports; no new third-party imports.

**Slider pattern** (lines 67-70):
```python
T_sp = st.slider("T setpoint (degC)", 18.0, 30.0, 25.0, 0.5)
RH_sp = st.slider("RH setpoint (%)", 50, 90, 70, 1)
seed_A = st.slider("weather seed A", 1, 50, 7, 1)
seed_B = st.slider("weather seed B", 1, 50, 21, 1)
```
Copy: sliders-only controls (audit bans `number_input`/`text_input` on 02 — `test_source_audits` lines 372-374). Tabs wrap the trace display, never the sliders.

**Tab-unpack analog** — `03_ga_explorer.py` lines 59-63 (`st.columns` unpack):
```python
ecols = st.columns(2)
eT_vals = [ecols[0].slider("eT[%d] center" % i, c - eT_gap, c + eT_gap, c, 0.1)
           for i, c in enumerate(hand_eT)]
```
Copy shape for tabs (RESEARCH.md Pattern 2):
```python
tT, tH, tE = st.tabs(["Temperature", "Humidity", "Energy"])
with tT:
    st.pyplot(temp_fig)  # figures still built by helpers, never savefig on page
```
Stub must return a sized list for `tabs` (mirror the `columns` handler) and `_Stub` needs `__enter__`/`__exit__` (Pitfall 1) — test change, same commit as the first tabbed page.

**Download + show pattern** (lines 89-91):
```python
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="controllers_traces.png", mime="image/png")
st.pyplot(fig)
```
Copy: unchanged order — serialize-then-show; figure built by `build_scenario_figure` in helpers.

**Cache pattern** (lines 45-46): `@st.cache_data` on `run_all_four` — headless stub's `cache_data` is a pass-through decorator (`test_dashboard.py` lines 35-43). Do not touch.

---

### `dashboard/pages/01_model_sim.py` (component, request-response)

**Analog:** `dashboard/pages/01_model_sim.py` itself — metric + download + pyplot tail.

**Imports pattern** (lines 10-24):
```python
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import matplotlib.pyplot as plt

import streamlit as st

from src.greenhouse_model import step, load_weather_profile, daytime_solar, params
from src.weather_profile_generator import generate_weather_profile
from dashboard.helpers import fig_to_png_bytes
```
Copy: add `holdout_ranking`/`load`-adjacent KPI read via `dashboard.helpers` import only. Page keeps single flow — no tabs (D-02).

**Metric pattern** (lines 67-68):
```python
st.metric("inside T range", "[%.2f, %.2f] degC" % (min(T_trace), max(T_trace)))
st.metric("RH range", "[%.1f, %.1f] %%" % (min(rh_trace), max(rh_trace)))
```
Copy: existing page-level `st.metric` usage — the uniform KPI row (`st.columns(4)` + 4 `st.metric` calls, values from `load_scoreboard()` rows read-only) goes at the top of the page before this content, same call shape.

**Figure + download pattern** (lines 70-92): explicit light-figure colors inline (`fig.patch.set_facecolor("#F7FAF3")`, axes `"#FFFFFF"`, ticks `"#263023"`), then:
```python
st.download_button("Download chart (PNG)", data=fig_to_png_bytes(fig),
                   file_name="model_sim_chart.png", mime="image/png")
st.pyplot(fig)
```
Copy: provenance `st.expander` goes at the bottom (static `st.write` text only, no compute — RESEARCH.md Pattern 3). Every figure stays full-width outside columns (Pitfall 4).

---

### `dashboard/pages/03_ga_explorer.py` (component, request-response)

**Analog:** `dashboard/pages/03_ga_explorer.py` itself — metric rows, columns, fail-closed JSON guard. HARD CONSTRAINT: no new top-level `def`/`class` (audit lines 378-382).

**Fail-closed JSON guard** (lines 33-44):
```python
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
```
Copy: KPI row reads frozen rows/artifact already on the page; no new guard block, no new loader path.

**Metric + columns patterns** (lines 46-52, 59-63, 80-82):
```python
st.subheader("Elite params")
st.metric("train fitness", "%.2f" % d["fitness"])
st.metric("coupling k_heat", "%.3f" % d["coupling"]["k_heat"])
...
ecols = st.columns(2)
eT_vals = [ecols[0].slider("eT[%d] center" % i, c - eT_gap, c + eT_gap, c, 0.1)
           for i, c in enumerate(hand_eT)]
...
st.metric("surface deviation max-abs (duty units, not closed-loop cost)",
          "%.4f" % dev_max)
```
Copy: uniform KPI row at top (same 4 cards as every page); expander at bottom. All wiring inline — the audit rejects any line starting with `def `/`class ` on this page, so the KPI row must be straight-line `st.*` calls, not a helper `def` on the page (a shared `kpi_row()` helper in `helpers.py` is allowed; calling it from 03 is fine — the ban is on *defining* on 03).

**Selectbox pattern** (line 119): `extra = st.selectbox("extra group", ["deT", "du", "deH", "dv"], index=0)` — stub's `selectbox` returns `options[index]` (test lines 58-64); keep controls stub-compatible (no new widget types).

---

### `dashboard/app.py` (component landing, request-response)

**Analog:** `dashboard/app.py` itself. Planner default: pages-only (RESEARCH.md Open Question 1) — touch ONLY if the KPI row is trivial.

**Config-first pattern** (lines 16-20):
```python
import streamlit as st

st.set_page_config(page_title="Fuzzy Greenhouse Climate Controller", layout="wide")

st.title("GA-Optimized Fuzzy Greenhouse Climate Controller")
```
Constraint: `set_page_config` must precede other `st.*` calls; landing-only bans (`run_closed_loop`, `compare(`, `savefig`, `plt.show`) — `test_page_set` lines 121-125. A KPI row here would need a `load_scoreboard` read the landing currently lacks; if added, copy the `04_results.py` `load_scoreboard` + `holdout_ranking` row-lookup shape, never inline cost math.

---

### `tests/test_dashboard.py` (test, batch)

**Analog:** `tests/test_dashboard.py` itself — stub + source-scan + byte-assert conventions.

**Stub pattern to extend** (lines 33-77):
```python
class _Stub:
    def __getattr__(self, name):
        ...
        if name == "columns":
            def cols(n, *a, **k):
                n = n if isinstance(n, int) else len(n)
                return [_Stub() for _ in range(n)]
            return cols
        ...
        def _noop(*a, **k):
            return None
        return _noop

    def __call__(self, *a, **k):
        return None
```
Copy: add a `tabs` branch mirroring `columns` exactly:
```python
        if name == "tabs":
            def tabs(labels, *a, **k):
                return [_Stub() for _ in labels]
            return tabs
```
And give `_Stub` context-manager support for `with st.expander(...)` / `with tab:`:
```python
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
```
`metric`/`write` stay `_noop → None` (no return value needed).

**Byte-assert pattern to copy for `test_evidence_zip`** (lines 401-420, `test_export_scoreboard_csv` + `test_export_chart_png`):
```python
raw = helpers.scoreboard_csv_bytes()
with open(os.path.join(ROOT, "results/comparison.csv"), "rb") as f:
    frozen = f.read()
assert raw == frozen, "CSV download bytes must equal the frozen artifact"
...
png = helpers.fig_to_png_bytes(helpers.build_results_figure(rows))
assert png[:4] == b"\x89PNG", png[:8]
assert len(png) > 1024, len(png)
```
Copy shape (RESEARCH.md Headless ZIP assertions):
```python
data = helpers.evidence_zip_bytes()
assert data[:2] == b"PK", data[:8]
z = zipfile.ZipFile(io.BytesIO(data))
assert z.namelist() == helpers.ZIP_MEMBERS, z.namelist()
assert z.read("comparison.csv") == open("results/comparison.csv", "rb").read()
assert z.read("ga_optimized_params.json") == open("results/ga_optimized_params.json", "rb").read()
assert z.read("results_scoreboard.png")[:4] == b"\x89PNG"
```

**Source-scan pattern to extend** (lines 354-389, `test_source_audits`; lines 435-460, `test_export_wiring`):
```python
src = open("dashboard/pages/02_controllers.py").read()
assert "st.tabs" in src and "st.metric" in src and "st.expander" in src
assert "savefig" not in src and "plt.show" not in src
```
Extend `test_source_audits`: `st.expander` in all 4 pages; `st.tabs` in 02/04 only; `st.metric` in all 4; ban list unchanged (`Agg`/`plt.show`/`savefig`/abs-paths/`"w"`-opens). Extend `test_export_wiring` or add ZIP-button assert: `evidence_pack` + `application/zip` in `04_results` source. New `test_layout_elements`: `st.metric`/`st.columns(4)` present per page + KPI values equal frozen holdout row. Runner convention (lines 463-479): plain `test_*` functions, `PASS/FAIL` prints, `sys.exit(1)` on failure, `python tests/test_dashboard.py`.

## Shared Patterns

### Error handling (fail-closed frozen reads)
**Source:** `dashboard/helpers.py` lines 55-59; `dashboard/pages/04_results.py` lines 43-49; `dashboard/pages/03_ga_explorer.py` lines 33-42
**Apply to:** `helpers.py` new builder + all four pages' KPI reads (reuse existing guards; no new `try` blocks)
```python
except OSError as exc:
    raise ValueError("frozen scoreboard unreadable: %s" % exc)
...
except (OSError, ValueError, AssertionError, KeyError) as exc:
    st.error("Frozen scoreboard unreadable: %s" % exc)
    st.stop()
```

### KPI values from frozen rows (never recompute)
**Source:** `dashboard/helpers.py` lines 68-71 (`holdout_ranking`); `dashboard/pages/04_results.py` lines 44-46
**Apply to:** KPI row on all four pages
```python
kpi = next(r for r in holdout_rows if r["controller"] == "ga_fuzzy")
c1, c2, c3, c4 = st.columns(4)
c1.metric("GA holdout cost", "%.2f" % float(kpi["cost"]))
c2.metric("GA holdout rank", "#%s" % kpi["rank"])
c3.metric("IAE_T", "%.2f" % float(kpi["iae_T"]))
c4.metric("IAE_H", "%.2f" % float(kpi["iae_H"]))
```
Bans: `"compare("`, `"argsort"`, `"all_metrics"` on the Results/KPI path.

### Download-button wiring (filename + MIME on page)
**Source:** `dashboard/pages/04_results.py` lines 53-54/69-70/73-74; MIME inventory in `tests/test_dashboard.py` lines 441-451
**Apply to:** ZIP button on `04_results.py`
```python
st.download_button("Download evidence pack (ZIP)", data=evidence_zip_bytes(),
                   file_name="greenhouse_evidence_pack.zip", mime="application/zip")
```
Existing 9-button inventory (do not disturb): `comparison.csv`/`text/csv`, `holdout_verdict.txt`/`text/plain`, `results_scoreboard.png`/`image/png` (04); `model_sim_chart.png` (01); `controllers_traces.png` (02); `ga_convergence.png`, `ga_convergence_replay.png`, `ga_mfs.png`, `ga_explorer_response.png` (03). `total == 9` assert in `test_export_wiring` line 459 must become 10.

### ZIP member allowlist (fixed, flat basenames)
**Source:** RESEARCH.md Code Examples (no existing ZIP code — new constant in `helpers.py`)
**Apply to:** `helpers.py` (`ZIP_MEMBERS` + `evidence_zip_bytes`) and `test_evidence_zip` (`namelist() == ZIP_MEMBERS`)
```python
ZIP_MEMBERS = ["comparison.csv", "holdout_verdict.txt", "results_scoreboard.png",
               "01_greenhouse_model.png", "02_baselines.png", "03_fuzzy.png",
               "04_ga_optimization.png", "05_comparison.png", "06_final_results.png",
               "ga_optimized_params.json"]
```
Flat basenames only (no directories, no `../` — ZIP-slip guard). Notebook PNG filenames verified on disk: `01_greenhouse_model.png` (115745 B), `02_baselines.png` (162068 B), `03_fuzzy.png` (300491 B), `04_ga_optimization.png` (216183 B), `05_comparison.png` (93470 B), `06_final_results.png` (375141 B). Total members < ~2 MB — single on-demand build, no caching.

### Page preamble + audit bans (all pages)
**Source:** all four pages lines 10-18 (`sys.path` + `os.chdir` preamble); `tests/test_dashboard.py` lines 362-389
**Apply to:** every page edit in this phase
- Keep `sys.path.insert` + `os.chdir` preamble verbatim.
- Never: `use("Agg")`, `plt.show`, `savefig`, absolute paths (`/home/`, `/Users/`, `C:/`, `C:\`), `"w"`-mode `open` in pages (BytesIO-only), `def `/`class ` on `03_ga_explorer.py`, `compare(`/`evolve`/`genetic_algorithm` on 02/03.
- Figures: full-width `st.pyplot(fig)` outside columns; KPI row max 4 narrow text cards (stacks vertically when narrow — D-04 reasoning-only verification).

### Provenance expander (static text)
**Source:** RESEARCH.md Pattern 3 (no existing expander code — new on all four pages)
**Apply to:** bottom of each page (contents at agent's discretion)
```python
with st.expander("Provenance"):
    st.write("Scoreboard: results/comparison.csv (8 rows, frozen). Seeds 7/21, weights 1.0/1.0/0.01.")
```
Static text only, no compute. Requires the `_Stub.__enter__/__exit__` test extension or `test_pages_import` fails with `AttributeError: __enter__`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| *(none)* | — | — | Every Phase-10 change composes existing builders/widgets: `evidence_zip_bytes` joins `scoreboard_csv_bytes`/`verdict_text`/`fig_to_png_bytes`; `st.tabs`/`st.expander` follow the `st.columns` unpack + `with`-block shapes already stubbed; ZIP asserts follow `test_export_*` byte-compare conventions. Planner should use RESEARCH.md Patterns 1-4 + Code Examples for the new-code shapes. |

## Metadata

**Analog search scope:** `dashboard/` (app.py, helpers.py, pages/01-04), `tests/test_dashboard.py`, `results/` (comparison.csv, ga_optimized_params.json), `notebooks/*.png`
**Files scanned:** 9 (7 code + 2 frozen artifacts + 6 PNGs verified present)
**Tracked-source gate (#3645):** all 9 code/artifact analog paths verified via `git ls-files` (all tracked, non-empty); no mirror/capability paths emitted
**Pattern extraction date:** 2026-09-29
