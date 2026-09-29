# Phase 6: Milestone Notebooks - Research

**Researched:** 2026-09-28
**Domain:** Jupyter notebook proof-of-work trail (nbformat JSON authoring, headless Matplotlib, stdlib CSV/JSON artifact reads)
**Confidence:** HIGH

## Summary

Phase 6 creates two new notebooks (`05_comparison.ipynb`, `06_final_results.ipynb`) and audits the four existing ones (01–04) against a five-point uniform pattern. All four existing notebooks were read as JSON this session and audited cell-by-cell: 01, 02, and 03 pass all five uniform-pattern checks; 04 has exactly two flagged deviations (missing nbformat cell `id` fields on all six cells, and `savefig` at `dpi=100` instead of the locked `dpi=120`). The data contracts for the new notebooks are frozen and verified on disk: `results/comparison.csv` is a 14-column CSV whose holdout block already encodes the verdict (GA 114.28 < on/off 513.75 < PID 645.26), and `results/ga_optimized_params.json` is schema v2 with 50-generation history plus `coupling` gains. Headless cell execution (extract-source + `exec` under `matplotlib Agg`) was probe-verified working on notebook 01 this session, so the plan's verification strategy needs no `jupyter` CLI — structural JSON checks plus headless `python` runs suffice. Zero new dependencies: everything needed (nbformat 5.10.4, matplotlib 3.10.8, NumPy 2.4.3) is installed.

**Primary recommendation:** Copy the 01/02/03 cell shape verbatim for 05/06 (title → Agg imports → weather guard → artifact-load → plot → savefig dpi=120), fix only the two flagged 04 deviations, and build 05/06 as artifact-readers (stdlib `csv`/`json` + `src/` helpers) with no live controller re-runs.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (Scope):** Create 2 new notebooks (05, 06) + audit the existing 4 (01, 02, 03, 04) against the uniform pattern — fix only what the audit flags. Existing notebooks are otherwise sealed phase artifacts (their phases verified).
- **D-02 (05 content):** `05_comparison.ipynb` is the scoreboard made visual: loads `results/comparison.csv` (frozen 14-col contract — never recompute metrics inline), plots grouped bars per metric + cost ranking for both weathers, prints the holdout verdict (GA < on/off AND < PID). No live controller re-runs.
- **D-03 (06 content):** `06_final_results.ipynb` is the full end-to-end narrative: plant → all four controllers → holdout verdict → MF before/after → closing claim. Executive summary of the whole project; reads artifacts (CSV, JSON, PNGs) rather than recomputing where a canonical artifact exists.
- **D-04 (Uniform pattern):** Uniform pattern across all six: markdown title cell, Agg setup before pyplot, src-only imports, regen-if-absent weather guard, `savefig` committed PNG at dpi=120. The audit checks these mechanically (nb-ok structural checks); deviations in 01–04 get fixed.

### the agent's Discretion
- Plot types/arrangements within the locked contents (bar groupings, trace selections, MF overlay style); markdown narrative wording.
- Audit mechanics (structural JSON checks vs headless cell execution) and fix granularity for flagged deviations.
- PNG filenames following the `NN_name.png` convention.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

## Project Constraints (from AGENTS.md)

- **Tech:** Python 3, NumPy (numerics), Streamlit (dashboard UI). Plotting via Matplotlib in notebooks. CSV for weather input and GA params (JSON per spec). No pandas in notebooks (05-CONTEXT D-02 pandas-free hard constraint) [VERIFIED: .planning/phases/05-metrics-comparison/05-CONTEXT.md:21-22].
- **Order:** hand-tuned fuzzy first, GA second — respected read-only here via MF before/after (hand `FUZZY_MFS` = before, JSON artifact = after).
- **Compatibility:** notebooks must run against `src/` functions with no duplicated logic — 05/06 must import from `src/`, never inline metric/controller math.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROOF-01 | Six milestone notebooks, each calling into `src/` and documenting a milestone with plots (no duplicated logic) | Per-notebook audit below (01–04 verified sealed except two 04 fixes); 05/06 cell-order specs + uniform-pattern checklist; validation section with concrete structural + headless checks |

## Per-Notebook Audit (01–04 vs Uniform Pattern)

Method: each `.ipynb` opened and read as JSON this session (cell ids, source order, `savefig` args inspected verbatim); PNG existence + byte size checked on disk; headless execution probe-verified on 01 [VERIFIED: notebooks/*.ipynb read 2026-09-28].

Uniform pattern (D-04) = (1) markdown title cell first, (2) `matplotlib.use("Agg")` before `import matplotlib.pyplot as plt`, (3) src-only imports (stdlib + `src.*` + numpy/matplotlib only), (4) regen-if-absent seed-7 weather guard, (5) `savefig("notebooks/NN_name.png", dpi=120)` with PNG committed.

| Notebook | Title | Agg order | src-only imports | Weather guard | savefig dpi=120 + PNG | Verdict |
|----------|-------|-----------|------------------|---------------|----------------------|---------|
| 01_greenhouse_model (5 cells: 1 md + 4 code) | ✅ `# Simulated Greenhouse Plant (MODEL-01)` | ✅ `matplotlib.use("Agg")` line precedes pyplot import | ✅ numpy/matplotlib + `src.greenhouse_model`, `src.weather_profile_generator` + stdlib `os` | ✅ `if not os.path.exists(CSV): generate_weather_profile(CSV, seed=7)` | ✅ `dpi=120`, PNG 115,745 B on disk | **PASS — sealed, no fix** |
| 02_baselines (6 cells: 2 md + 4 code) | ✅ `# Baseline Controllers: On/Off vs PID (BASE-01..03)` | ✅ same order | ✅ + `src.onoff_controller`, `src.pid_controller` | ✅ identical guard, seed 7 | ✅ `dpi=120`, PNG 162,068 B on disk | **PASS — sealed, no fix** |
| 03_fuzzy (6 cells: 2 md + 4 code) | ✅ `# Manual Fuzzy Controller: Velocity-Form Dual Loop (FUZZ-01..06)` | ✅ same order | ✅ + `src.fuzzy_controller` (`fuzzy_step, FUZZY_MFS, LABELS`; plot cell adds `from src.fuzzy_controller import tri` — still src-only) | ✅ identical guard, seed 7 | ✅ `dpi=120`, PNG 300,491 B on disk | **PASS — sealed, no fix** |
| 04_ga_optimization (6 cells: 2 md + 4 code) | ✅ `# GA Optimization: Coupled Fuzzy Beats Both Baselines (GA-01..05)` | ✅ Agg precedes pyplot in imports cell | ✅ stdlib `json/os/tempfile` + numpy/matplotlib + six `src.*` imports incl. `W1, W2, W3` weights | ✅ seed-7 guard for train CSV; holdout uses isolated `tempfile` seed-21 path (locked design, not a deviation) | ❌ `fig.savefig("notebooks/04_ga_optimization.png", dpi=100)` — must be `dpi=120`; PNG 173,300 B on disk | **FIX 2 deviations (below)** |

### Flagged deviations (04 only — the plan's audit-fix task)

1. **F-04-01 — all six cells lack nbformat `id` fields.** 01/02/03 cells all carry `"id": "title"/"imports"/"weather"/"run"/"plot"`; every 04 cell has no `id` key. Loading 04 under nbformat 5.10.4 emits `MissingIDFieldWarning: Cell is missing an id field, this will become a hard error in future nbformat versions` [VERIFIED: probe run 2026-09-28 — warning raised on `nbformat.read` + `validate`]. Fix: assign stable ids (`title`, `imports`, `weather`, `verdict`, `verdict-note`, `plot`) matching the 01–03 naming convention. Mechanical, zero behavior change.
2. **F-04-02 — `savefig` uses `dpi=100`, pattern requires `dpi=120`.** Verbatim source tail: `fig.savefig("notebooks/04_ga_optimization.png", dpi=100)` [VERIFIED: notebooks/04_ga_optimization.ipynb plot cell]. Fix: change to `dpi=120` and regenerate the PNG (headless re-run of the plot cell). Note: regenerating re-runs the holdout proof cell too (4 × 1440-step closed loops) — deterministic (seeded), expected identical verdict numbers.
3. **F-04-03 (minor, fix opportunistically in the same edit):** duplicate `import os` — `os` is imported in the imports cell AND re-imported at the top of the weather cell (`import os` line 56). Harmless; collapse to one import while touching the file. Also 03/04 notebook metadata is `{}` (no `kernelspec`/`language_info`, unlike 01/02) — cosmetic only, NOT a uniform-pattern item; normalize only if free, never as a standalone task [ASSUMED risk if wrong: nil — kernelspec absence does not affect headless `python` execution or nbformat validation].

**Nothing else flagged.** In particular: 04's live holdout re-runs are its locked Phase-4 design (D-06/A2 relative-ordering asserts) and are NOT a D-02 violation — D-02's no-recompute rule applies to 05 only. 02/03's `saturation-note` markdown cells are narrative, not deviations.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Notebook narrative + plots | Notebooks (`notebooks/`) | — | PROOF-01 proof-of-work trail; presentation only |
| Metric/controller math | `src/` library | — | No-duplicated-logic constraint; notebooks import, never inline |
| Scoreboard data | `results/comparison.csv` (frozen artifact) | — | 05's ONLY data source; produced by Phase 5, never recomputed inline |
| GA params + history | `results/ga_optimized_params.json` (schema v2) | — | 04/06 read-only source for tuned MFs, gains, convergence history |
| Verification | Headless `python` + JSON structural checks | — | `jupyter` CLI absent — no `nbconvert` execution path exists |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nbformat | 5.10.4 [VERIFIED: env probe 2026-09-28] | Notebook JSON I/O + `validate()` for structural audit | The notebook format library itself; already installed, already the audit tool |
| matplotlib (Agg backend) | 3.10.8 [VERIFIED: env probe 2026-09-28] | All plots, headless via `matplotlib.use("Agg")` before pyplot import | Locked project tech; Agg works without display server or `jupyter` |
| NumPy | 2.4.3 [VERIFIED: env probe 2026-09-28] | Numeric support in plot cells (arange, interp, linspace) | Locked project tech; NumPy-only convention |
| stdlib `csv`, `json`, `os` | Python 3.14.6 [VERIFIED: env probe 2026-09-28] | 05 reads CSV; 06 reads CSV+JSON; weather guard | Pandas-free hard constraint (D-02) — `csv.DictReader` is the loader |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `src/metrics.py` (`COLUMNS`, weights) | repo | Column-name contract + locked weights reference | 05 asserts CSV header == `COLUMNS` before plotting; never reimplements cost |
| `src/fuzzy_controller.py` (`FUZZY_MFS`, `LABELS`, `tri`) | repo | Hand-tuned "before" MFs for 06 overlay | 06 MF before/after panel |
| `src/ga_fuzzy_controller.py` (`load_optimized_mfs`) | repo | Validated load of JSON "after" MFs | 06 MF after-curve (preferred over raw `json.load` — fail-fast schema check) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `csv` | pandas `read_csv` | REJECTED — pandas-free is a locked hard constraint (05-CONTEXT D-02); pandas 3.0.1 happens to be installed but must not be imported |
| `jupyter nbconvert --execute` | headless `python` cell extraction + `exec` | `jupyter` CLI is ABSENT [VERIFIED: `command -v jupyter` empty 2026-09-28] — nbconvert path does not exist; structural JSON checks + headless runs are the only verification |
| Re-running controllers in 05 | Reading `comparison.csv` | REJECTED — D-02 forbids recomputation; CSV is the frozen contract |

**Installation:**
```bash
# Zero new dependencies — nothing to install.
```

**Version verification:** No registry lookups needed (no new packages). Runtime versions probe-verified in-environment (see Environment Availability).

## Package Legitimacy Audit

No external packages are installed in this phase — 05/06 use only the Python standard library plus the already-installed NumPy/matplotlib/nbformat. No legitimacy gate to run; planner must add a checkpoint if any task proposes a new import beyond `{numpy, matplotlib, nbformat, csv, json, os, tempfile}` + `src.*`.

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| *(none proposed)* | — | — | No audit required |

**Packages removed due to SLOP verdict:** none.
**Packages flagged as suspicious (SUS):** none.

## 05 Plot Specification (scoreboard made visual)

**ONLY data source:** `results/comparison.csv` — 14 columns, 8 rows (4 controllers × 2 weathers) [VERIFIED: results/comparison.csv:1-9].

Frozen column contract (do not re-derive — assert header equality with `COLUMNS`):
```python
# Source: src/metrics.py:32-35 [VERIFIED: read 2026-09-28]
COLUMNS = ["controller", "weather",
           "rmse_T", "rmse_H", "iae_T", "iae_H", "ise_T", "ise_H",
           "settling_min", "overshoot_T", "overshoot_H",
           "energy", "cost", "rank"]
# controller in {"onoff","pid","fuzzy","ga_fuzzy"};
# weather in {"train-seed7","holdout-seed21"};
# rank = 1..4 by cost WITHIN each weather block (holdout block is the verdict)
```

Holdout numbers the plots must show (read from CSV at runtime, never hardcoded):
- `ga_fuzzy`: cost 114.28 (iae_T 1.66, iae_H 112.44, E 18.13), rank 1
- `onoff`: cost 513.75, rank 2; `fuzzy`: cost 644.03, rank 3; `pid`: cost 645.26, rank 4 [VERIFIED: results/comparison.csv:6-9]

Prescribed figure (arrangement within is the agent's discretion, contents are locked):
1. **Grouped bars per metric, both weathers:** one panel each for `iae_T`, `iae_H`, `energy`, and `cost` — x = controller (display order onoff, pid, fuzzy, ga_fuzzy), grouped/side-by-side by weather (train-seed7 vs holdout-seed21). Cost panel SHOULD use a log y-scale or broken axis [ASSUMED presentation choice]: GA (~110) vs the rest (500–645) collapses to unreadable on a linear scale — planner discretion, but flag it so the plot is not shipped illegible.
2. **Cost ranking panel:** horizontal barh of holdout `cost` sorted by `rank`, annotated with rank numbers 1–4. Reads the `rank` column; does not recompute ordering.
3. **Holdout verdict print cell:** loads holdout rows, asserts `cost[ga_fuzzy] < cost[onoff]` AND `cost[ga_fuzzy] < cost[pid]` (relative ordering only, mirroring 04's assert style — no absolute thresholds), prints `verdict: GA < on/off AND GA < PID on holdout — METR-02 HOLDS`.
4. Known data quirks to handle, not "fix": `settling_min` is `inf` for all 8 rows (never-settled marker per D-03 strict joint band) — do NOT plot settling as bars (inf breaks autoscale); either omit the panel or render as a text annotation "all controllers: never settled (joint ±0.5 °C / ±3 %RH band)". `overshoot_H` is 30.0 for three controllers (saturation structural note territory — 02/03 precedent). Keep panels to the four plottable metrics above [ASSUMED selection: iae_T/iae_H/energy/cost are the verdict-relevant terms; rmse/ise/overshoot stay in the CSV table print, not bars].

Suggested cell order for 05 (mirrors 01–03 shape): markdown title → imports/Agg cell → weather-guard cell (regen-if-absent seed-7 — uniform pattern item even though 05 needs no weather data; keep the guard verbatim for pattern uniformity [ASSUMED: harmless no-op when CSV exists, satisfies the mechanical audit]) → CSV-load + header-assert cell → grouped-bars plot cell → ranking + verdict cell → savefig `notebooks/05_comparison.png` dpi=120.

## 06 Narrative Cell Order + Artifact Reads

06 is the executive summary a reviewer reads first: plant → all four controllers → holdout verdict → MF before/after → closing claim. It reads artifacts, never recomputes.

Prescribed cell order (wording is the agent's discretion, order and reads are locked by D-03):

| # | Cell | Reads | Notes |
|---|------|-------|-------|
| 1 | Markdown title `# Final Results: GA-Optimized Fuzzy Wins on Holdout (PROOF-01)` | — | Must be first cell (uniform pattern item 1) |
| 2 | Imports + Agg (`matplotlib.use("Agg")` before pyplot) | `src.*` only + stdlib | `csv`, `json`, numpy, matplotlib; `from src.fuzzy_controller import FUZZY_MFS, LABELS, tri`; `from src.ga_fuzzy_controller import load_optimized_mfs` |
| 3 | Weather guard (verbatim seed-7 regen-if-absent) | `weather/weather_profile.csv` | Pattern-uniformity only; 06 needs no simulation weather |
| 4 | Load scoreboard: `csv.DictReader("results/comparison.csv")`, assert 14-col header == `COLUMNS`, print 8-row table | `results/comparison.csv` | Same loader shape as 05; assert-then-read |
| 5 | Load GA artifact: `load_optimized_mfs(JSON)` + raw `json.load` for `history`/`fitness`/`coupling`; assert `schema_version == 2` (04 precedent, lines 69–70) | `results/ga_optimized_params.json` | Schema v2 keys verified on disk: `mfs{6 groups}`, `coupling{k_heat,k_vent}`, `fitness` 107.14, `weights{w1:1,w2:1,w3:0.01}`, `history{best,mean}` 50 gens each, `train_seed` 7, `holdout_seed` 21 [VERIFIED: artifact read 2026-09-28] |
| 6 | Verdict restatement cell: holdout cost ordering print + relative asserts (GA < on/off AND GA < PID) | values from cell 4 | RESTATES the CSV verdict; never recomputes cost from histories |
| 7 | MF before/after overlays: hand `FUZZY_MFS` (before) vs `mfs_opt` (after) for `eH` at minimum, ideally all six groups in 04-style grid or a 2×3 panel | `src/fuzzy_controller.py:20-29` before-values [VERIFIED: read 2026-09-28]; JSON after-values | 03's MF panel is the before-reference precedent; 04's `ax[1,1]` eH overlay is the after precedent — 06 unifies them. Gains annotation `k_heat/k_vent = 0.05/0.05` [VERIFIED: artifact `coupling`] |
| 8 | Prior-trail montage: `plt.imread` + `imshow` the four existing PNGs (01–04) in a 2×2 axis-off panel — Agg-safe, no `IPython.display` needed | `notebooks/0{1..4}_*.png` (all exist, sizes above) | [ASSUMED technique: `imread`/`imshow` montage works headless under Agg — standard matplotlib, zero new deps; markdown `![]()` image links ALSO work for rendered viewing, but the montage keeps the verdict inside the committed PNG] |
| 9 | Closing-claim markdown: one paragraph — coupled GA fuzzy ranks #1 on unseen seed-21 holdout on the locked 1.0/1.0/0.01 cost; saturation (`settling inf`, RH 100% stretches) is structural across all controllers, not a GA defect (02/03-note precedent) | — | Must not introduce new numbers beyond cells 4–6 |
| 10 | `savefig("notebooks/06_final_results.png", dpi=120)` | — | Locked filename keeps Phase-7 embedding stable (CONTEXT integration point) |

Before/after numbers for the MF panel (hand = before, GA = after):
- Hand `eH`: centers `[-30, -15, 0, 15, 30]`, widths all `15.0` [VERIFIED: src/fuzzy_controller.py:26]; hand `eT`: centers `[-4, -2, 0, 2, 4]`, widths `2.0` [VERIFIED: src/fuzzy_controller.py:22].
- GA `eH`: centers `[-4.60, 0.19, 18.68, 32.91, 40.0]`, widths `[14.82, 7.47, 17.85, 10.04, 15.91]` [VERIFIED: results/ga_optimized_params.json `mfs.eH`]. Dramatic narrowing/shift = the visual story of optimization.

## Architecture Patterns

### Notebook Shape (all six follow 01–03)
```
cell 0:  markdown title (# ... (REQ-IDS))
cell 1:  imports — numpy → matplotlib → use("Agg") → pyplot → src.* → stdlib; print params
cell 2:  weather guard — CSV = "weather/weather_profile.csv"; regen seed 7 if absent; load + interp
cell 3+: compute-or-load → print numeric probe line
plot:    build figure → suptitle → tight_layout → savefig("notebooks/NN_name.png", dpi=120) → show/print
```

### Pattern: Artifact-Reader Cells (05/06)
**What:** Load frozen results with stdlib, assert schema, then plot. No simulation loops.
**When to use:** Any cell whose data already exists as a committed artifact.
**Example:**
```python
# Source: established repo pattern (04 JSON-load cell + csv stdlib convention)
import csv, json, os
from src.metrics import COLUMNS  # column-name contract, never retyped
CSV_PATH = "results/comparison.csv"
with open(CSV_PATH) as f:
    rows = list(csv.DictReader(f))
assert list(rows[0].keys()) == COLUMNS, "stale artifact: header != COLUMNS"
holdout = [r for r in rows if r["weather"] == "holdout-seed21"]
costs = {r["controller"]: float(r["cost"]) for r in holdout}
assert costs["ga_fuzzy"] < costs["onoff"] and costs["ga_fuzzy"] < costs["pid"]
print("verdict: GA < on/off AND GA < PID on holdout — METR-02 HOLDS")
```

### Pattern: Headless Verification Without `jupyter`
**What:** `jupyter` CLI is absent, so notebooks are verified by (a) `nbformat.read` + `validate()` structural checks on the JSON, and (b) extracting code-cell sources and `exec`-ing them under `matplotlib.use("Agg")` in a plain `python` process. Probe-verified on 01 this session (printed identical `params` dict + `T [15.97, 33.27] w [11.32, 27.43] RH [49.5, 100.0]` ranges) [VERIFIED: probe run 2026-09-28].
**When to use:** Every verify step in this phase.

### Anti-Patterns to Avoid
- **Recomputing metrics inline in 05:** rebuilding cost/IAE from histories duplicates `src/metrics.py` and risks divergence from the frozen CSV. Read the CSV.
- **Absolute paths in notebooks:** all four existing notebooks use repo-relative paths (`weather/...`, `notebooks/...`, `results/...`); 04's only exception is a `tempfile` holdout path that is intentionally ephemeral. 05/06 must use relative paths so Phase-7/dashboard reuse and CI checkout work anywhere.
- **Inline GA evolution:** 04 correctly reads history from the JSON artifact; 05/06 must never call evolution functions (hours-long runs, non-deterministic wall-clock).
- **Pandas import:** installed (3.0.1) but forbidden by D-02; `csv` module suffices for 8-row reads.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Notebook JSON validation | Custom schema checker | `nbformat.read` + `validate()` (installed 5.10.4) | Canonical spec; already emits the missing-id warning class this phase must catch |
| MF before/after curves | Custom plotting math | `tri` from `src.fuzzy_controller` + `FUZZY_MFS` (04-plot precedent) | Same function the controller uses — overlay cannot drift from engine semantics |
| Holdout verdict logic | New threshold or prose claim | Relative asserts on CSV `cost`/`rank` (04-assert precedent) | Locked bar is relative ordering only; absolutes re-litigate Phase-4 Amendment A2 |
| GA param loading in 06 | Raw `json.load` + manual indexing | `load_optimized_mfs` from `src.ga_fuzzy_controller` | Fail-fast schema validation (exact key set, len-5, widths > 0, coupling bounds) already written and tested |

**Key insight:** Every computation 05/06 needs already exists as a tested `src/` function or a frozen artifact. The notebooks are thin composition + presentation — any new math in a cell is a defect.

## Common Pitfalls

### Pitfall 1: Linear-scale cost bars hide the story
**What goes wrong:** GA cost (~110) vs rest (500–645) on one linear axis renders GA as a sliver and compresses the on/off-vs-PID difference among the top.
**Why it happens:** 6× dynamic range across one bar group.
**How to avoid:** Log-scale y-axis on the cost panel, or a dedicated ranked-horizontal-bar panel where length encodes order. Planner's discretion — but require a legibility check (GA bar distinguishable, rank labels readable).
**Warning signs:** Reviewer has to squint to find GA in the cost panel.

### Pitfall 2: `settling_min = inf` breaks bar autoscaling
**What goes wrong:** Plotting the `settling_min` column (all `inf`) yields an empty/broken axis or a matplotlib warning cascade.
**Why it happens:** Joint-band criterion is never satisfied (structural RH saturation), so Phase 5 wrote the never-settled marker for all 8 rows [VERIFIED: all `settling_min` values are `inf` in comparison.csv].
**How to avoid:** Exclude `settling_min` from bar panels; render as a one-line text annotation instead.
**Warning signs:** `RuntimeWarning: invalid value` or an all-blank subplot in the committed PNG.

### Pitfall 3: Notebook edited but PNG stale
**What goes wrong:** `.ipynb` JSON and committed `.png` diverge (e.g., F-04-02 dpi fix without PNG regeneration).
**Why it happens:** PNG is a build artifact committed beside the source; nothing rebuilds it automatically.
**How to avoid:** Every notebook-touching task ends with headless re-execution of that notebook's cells + `savefig`, and the PNG is committed in the same atomic commit. Verification re-runs cells and diffs nothing — it checks the PNG mtime/size changed consistently.
**Warning signs:** PNG byte size identical after a plot-cell edit.

### Pitfall 4: Cell ids dropped by hand-editing JSON
**What goes wrong:** F-04-01 recurs — a JSON edit that rewrites cells without `id` fields reintroduces the `MissingIDFieldWarning` (future hard error).
**Why it happens:** Hand-authoring notebook JSON (this phase's likely authoring method) easily omits `id`.
**How to avoid:** Authoring script/notebook-writer must stamp `"id"` on every cell (01–03 convention: `title/imports/weather/run/plot`); the structural check asserts id presence on all cells of all six notebooks.
**Warning signs:** `MissingIDFieldWarning` during validation.

### Pitfall 5: Duplicated metric/controller logic in cells
**What goes wrong:** A cell reimplements IAE/cost/triangular-MF inline; numbers drift from `src/` and PROOF-01's no-duplication clause fails.
**Why it happens:** Plotting convenience ("just compute it here").
**How to avoid:** Import from `src/` (`tri`, `FUZZY_MFS`, `COLUMNS`, `load_optimized_mfs`); the audit greps new cells for `def ` statements computing metrics — any match is a finding.
**Warning signs:** A `def` block in 05/06 that is not a thin loader/runner wrapper.

## Code Examples

### CSV scoreboard load + verdict (05/06 pattern)
```python
# Source: repo-established pattern (04 JSON-assert cell + stdlib csv convention)
import csv
from src.metrics import COLUMNS
with open("results/comparison.csv") as f:
    rows = list(csv.DictReader(f))
assert list(rows[0].keys()) == COLUMNS, "stale artifact: header != COLUMNS"
assert len(rows) == 8, "expected 4 controllers x 2 weathers"
```

### MF before/after overlay (06 pattern, 04-plot precedent)
```python
# Source: 04 plot cell (eH overlay) + src/fuzzy_controller.py:40-42 tri()
import numpy as np
from src.fuzzy_controller import FUZZY_MFS, tri
grid = np.linspace(-40, 40, 400)  # eH universe
for c, w in zip(FUZZY_MFS["eH"]["centers"], FUZZY_MFS["eH"]["widths"]):
    ax.plot(grid, [tri(x, c, w) for x in grid], "C0-", alpha=0.5)   # hand (before)
for c, w in zip(mfs_opt["eH"]["centers"], mfs_opt["eH"]["widths"]):
    ax.plot(grid, [tri(x, c, w) for x in grid], "C1--", alpha=0.8)  # GA (after)
```

### Structural audit check (verification harness shape)
```python
# Source: nbformat 5.10.4 API (installed) + uniform-pattern D-04 items
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

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `jupyter nbconvert --execute` for verification | Structural JSON checks + headless `exec` under Agg | This phase (CLI absent) | Verification needs no notebook server; plan accordingly |
| Cells without `id` tolerated silently | `MissingIDFieldWarning`, future hard error | nbformat 5.1.4+ posture (warning observed on 5.10.4) | F-04-01 fix is forward-compat, not cosmetic |
| 04 PNG at dpi=100 | Uniform dpi=120 | This phase (D-04 lock) | One-line fix + PNG regen |

**Deprecated/outdated:**
- `plt.show()` in headless runs: harmless under Agg (no-op) — 01–03 already include it; keep for pattern uniformity, do not strip.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `imread`/`imshow` PNG montage works headless under Agg for the 06 trail panel | 06 spec, cell 8 | Low — fallback is markdown `![]()` image links; planner can make cell 8 either/or with the montage preferred |
| A2 | Cost panel needs log/broken axis for legibility (6× range) | 05 spec | Low — purely presentational; planner's discretion already covers arrangement |
| A3 | `settling_min` text-annotation (not bars) is the right treatment | 05 spec | Low — data is uniformly `inf`; any bar attempt visibly breaks, caught by PNG review |
| A4 | Verbatim seed-7 weather guard belongs in 05/06 even though they need no simulation weather | 05/06 specs | Low — no-op when CSV exists; keeps the mechanical audit uniform (audit checks all six identically) |
| A5 | 03/04 empty notebook metadata (no kernelspec) is cosmetic and safe to leave | Audit | Low — headless `python` execution ignores kernelspec; only matters if someone opens in Jupyter, which still defaults to python3 |

## Open Questions

1. **Should F-04-03 (duplicate `import os`, empty metadata) be fixed in the same edit as F-04-01/02?**
   - What we know: All three are same-file, zero-behavior edits; sealed-artifact rule says "fix only what the audit flags."
   - What's unclear: Whether the planner counts the minor cleanup as "flagged."
   - Recommendation: This research flags all three, so the plan can scope one atomic 04-fix task covering F-04-01 (required), F-04-02 (required), F-04-03 (opportunistic, same diff). No separate task.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All cells | ✅ | 3.14.6 | — |
| NumPy | Numeric cells | ✅ | 2.4.3 | — |
| matplotlib (Agg) | All plots | ✅ | 3.10.8 | — |
| nbformat | Structural audit | ✅ | 5.10.4 | — |
| `jupyter` CLI / nbconvert | Nothing (explicitly not needed) | ❌ absent | — | Headless `python` exec + JSON checks (probe-verified) |
| `weather/weather_profile.csv` (seed 7) | Weather guard no-op | ✅ | present | Regen seed 7 via `src.weather_profile_generator` |
| `weather/holdout_21.csv` | Phase-5 artifact reference | ✅ | present | Regen seed 21 (05/06 do not need it) |
| `results/comparison.csv` | 05 + 06 | ✅ | 14 cols × 8 rows, verified | — (frozen; regen = Phase-5 rerun, out of scope) |
| `results/ga_optimized_params.json` | 04 (reread) + 06 | ✅ | schema v2, 50-gen history | — (frozen artifact) |
| pandas | Nothing (forbidden) | ✅ installed 3.0.1 but MUST NOT be imported | — | stdlib `csv` |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** `jupyter` CLI absent → fallback is the verified headless path (not a gap).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Repo plain-assert convention (`tests/test_*.py` with `__main__` runner + in-body imports — no pytest/jest config found [ASSUMED from 05-CONTEXT code-context + tests/ listing: test_baseline_controllers, test_fuzzy_controller, test_genetic_algorithm, test_greenhouse_model, test_metrics]) |
| Config file | none — see Wave 0 |
| Quick run command | `python tests/test_metrics.py` (existing suite guard — comparison.csv contract must not regress) |
| Full suite command | `python tests/test_greenhouse_model.py && python tests/test_baseline_controllers.py && python tests/test_fuzzy_controller.py && python tests/test_genetic_algorithm.py && python tests/test_metrics.py` (sequential; each file self-runs) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROOF-01 (01–04 sealed) | 4 notebooks pass 5 uniform-pattern structural checks | structural (nbformat JSON) | `python <wave0-audit>.py --nb notebooks/0[1-4]*.ipynb` (checks §Audit checklist) | ❌ Wave 0 (new audit script or inline check cells) |
| PROOF-01 (04 fixes) | 04 cells all have ids; savefig dpi=120; PNG regenerated | structural + artifact | audit script + `PNG byte-size changed && dpi string present` | ❌ Wave 0 |
| PROOF-01 (05) | 05 exists; loads CSV (header == COLUMNS, 8 rows); holdout asserts pass; PNG exists ≥50 KB | headless exec + artifact | extract-and-`exec` 05 code cells under Agg; assert `notebooks/05_comparison.png` exists | ❌ Wave 0 (notebook itself is the deliverable; harness runs it) |
| PROOF-01 (06) | 06 exists; reads CSV+JSON+4 PNGs; verdict restates; MF panel present; PNG exists ≥50 KB | headless exec + artifact | extract-and-`exec` 06 code cells under Agg; assert `notebooks/06_final_results.png` exists | ❌ Wave 0 |
| PROOF-01 (no-duplication) | No metric/controller math defined in 05/06 cells | grep audit | grep `^def \|^class ` in 05/06 code cells → only thin wrappers allowed | ❌ Wave 0 (fold into audit script) |
| METR-02 guard | `results/comparison.csv` byte-identical (05/06 never rewrite it) | regression | `fc /b` hash compare before/after phase (or `git status --porcelain results/`) | ✅ git (no new file needed) |

### Sampling Rate
- **Per task commit:** structural audit script over touched notebooks + `git status --porcelain results/` (CSV untouched)
- **Per wave merge:** headless exec of all six notebooks' code cells under Agg (04's full re-run ≈ 4 × 1440 steps + GA-history plots, seconds-scale like the 01 probe)
- **Phase gate:** Full suite green (existing 5 test files) + 6/6 notebooks pass all structural checks + 6/6 PNGs exist (each ≥50 KB: smallest current is 01 at 115 KB) + F-04-01/02/03 closed before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Notebook audit harness — either `tests/test_notebooks.py` (plain-assert, repo convention) implementing the §Audit checklist below, or documented inline structural-check cells. Covers PROOF-01 structural behaviors.
- [ ] No framework install needed (nbformat/matplotlib/numpy present); no `conftest.py` (repo uses no pytest).

### Uniform-Pattern Audit Checklist (the plan's audit task executes this per notebook × 6)
1. `nbformat.validate()` passes with zero warnings (catches F-04-01 class).
2. Cell 0 is markdown starting with `#`.
3. Every cell has a non-empty `id`.
4. Concatenated code sources: `use("Agg")` index < `import matplotlib.pyplot` index.
5. Imports restricted to `{numpy, matplotlib, nbformat?, csv, json, os, tempfile} + src.*` — no pandas, no new third-party.
6. Weather-guard substring `generate_weather_profile(CSV, seed=7)` present in 01/02/03/05/06 (04: seed-7 guard + isolated seed-21 tempfile path).
7. `savefig("notebooks/NN_name.png", dpi=120)` present verbatim (NN matches notebook number).
8. Referenced PNG exists on disk, size ≥50 KB.
9. Headless `exec` of all code cells under Agg exits 0 (04/06 may take longer — holdout loops + montage I/O — still seconds-scale).
10. 05/06 code cells contain no `def` computing metrics/MFs (thin wrappers only); 05 contains no `compare(`/`compute_metrics` recomputation calls.

## Security Domain

Required ( `security_enforcement` is not `false` in config; ASVS level 1).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No users, sessions, or credentials in this phase |
| V3 Session Management | no | Stateless headless execution only |
| V4 Access Control | no | Local repo files only; no multi-user surface |
| V5 Input Validation | yes | `load_optimized_mfs` fail-fast schema asserts (exact key set, len-5, widths > 0, finite, coupling bounds) [VERIFIED: src/ga_fuzzy_controller.py:53-75]; 05/06 assert CSV header == `COLUMNS` + `schema_version == 2` before use (fail-closed on stale artifacts) |
| V6 Cryptography | no | No crypto; JSON-only artifact loading (never pickle/eval) per `ga_fuzzy_controller` module contract |
| V14 Configuration | partial | Repo-relative paths only; no secrets; committed PNGs are build outputs, not executable content |

### Known Threat Patterns for notebook-JSON + artifact reads

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| No-inline-evolution (a cell re-running GA training inline: hours, nondeterminism, artifact overwrite) | Tampering / DoS (compute) | 05/06 cells read frozen artifacts only; `results/` guarded by `git status` regression check; never import evolution entry points in 05/06 |
| Absolute-path lock-in (notebook works only on author's machine) | — (portability defect) | Enforce repo-relative paths (`weather/`, `results/`, `notebooks/`); checklist item; 04's `tempfile` holdout path is the sanctioned ephemeral exception |
| Artifact provenance drift (stale CSV/JSON silently plotted) | Tampering (silent) | Header-assert vs `COLUMNS`, `schema_version == 2` + `population == 50 and generations == 50` asserts (04 lines 69–70 precedent) — plots never render from unvalidated inputs |
| Cell-output staleness (stored outputs in JSON contradict re-execution) | Tampering (misleading proof) | Keep code-cell `outputs: []` + `execution_count: null` (01–04 convention [VERIFIED]) — proof is the committed PNG + reproducible headless run, not embedded outputs |

## Sources

### Primary (HIGH confidence)
- `notebooks/01_greenhouse_model.ipynb`, `02_baselines.ipynb`, `03_fuzzy.ipynb`, `04_ga_optimization.ipynb` — read as JSON cell-by-cell this session (audit table evidence)
- `results/comparison.csv` — 14-col × 8-row contract + holdout verdict numbers read this session
- `results/ga_optimized_params.json` — schema v2 keys, coupling, weights, 50-gen history read this session
- `src/metrics.py:30-44` (`W1/W2/W3`, `COLUMNS`, controller/weather enums) — read this session
- `src/fuzzy_controller.py:18-29` (`LABELS`, `FUZZY_MFS` hand values) — read this session
- `src/ga_fuzzy_controller.py:37-77` (`load_optimized_mfs` validation) — read this session
- In-environment probes this session: nbformat 5.10.4, matplotlib 3.10.8, NumPy 2.4.3, Python 3.14.6, `jupyter` CLI absent, headless-exec smoke test of 01 cells green
- `.planning/phases/06-milestone-notebooks/06-CONTEXT.md`, `.planning/phases/05-metrics-comparison/05-CONTEXT.md` (D-02 pandas-free, D-04 cost+rank, frozen contract)

### Secondary (MEDIUM confidence)
- None — all load-bearing claims were verified against repo files or the live environment.

### Tertiary (LOW confidence)
- A1–A5 assumptions (presentation/robustness choices, each with a stated fallback) — flagged for planner discretion, not load-bearing.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every version probe-verified in-environment; zero new packages.
- Architecture: HIGH — cell shapes, contracts, and verification path all read from repo artifacts this session.
- Pitfalls: HIGH — derived from actual data quirks observed in the CSV/artifact (all-`inf` settling, 6× cost range, F-04-01 warning reproduced live).

**Research date:** 2026-09-28
**Valid until:** 30 days (stable: frozen artifacts, locked decisions, installed toolchain)
