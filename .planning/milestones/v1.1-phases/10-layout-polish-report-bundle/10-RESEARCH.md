# Phase 10: Layout Polish + Report Bundle - Research

**Researched:** 2026-09-29
**Domain:** Streamlit presentation layout (metric/tabs/expander) + in-memory ZIP evidence bundle
**Confidence:** HIGH

## Summary

Phase 10 is pure composition over finished work: restyle the four existing dashboard pages with a uniform KPI-card header, targeted tabs, and provenance expanders, then add one in-memory ZIP download on the Results page assembled from Phase-8 byte builders + frozen artifacts. No new science, no new installs, no new serialization logic — every byte the ZIP carries already has a tested builder or a frozen file.

**Primary recommendation:** Put one `evidence_zip_bytes()` builder in `dashboard/helpers.py` (stdlib `zipfile` + `BytesIO`, fixed member allowlist, `ZIP_DEFLATED`), wire uniform KPI rows + locked tabs + expanders in pages as thin wiring only, and extend the existing `test_dashboard.py` stub + source audits to cover tabs/expander/ZIP headless.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Uniform KPI cards on every page header: cost + rank + IAE_T/IAE_H — the verdict visible everywhere, same cards everywhere.
- **D-02:** Targeted tabs only: Controllers gets T/RH/energy tabs; Results gets train/holdout tabs. Other pages keep their single flow.
- **D-03:** Full evidence pack: scoreboard CSV + verdict TXT + all committed notebook PNGs (01–06) + GA JSON. Built in-memory via stdlib `zipfile` (never temp files).
- **D-04:** Clean stacking: columns stack vertically, no horizontal scroll, controls stay reachable. Verified by column structure + narrow-viewport reasoning (no browser screenshots possible headless).

### the agent's Discretion
- Expander contents (provenance details) per page; card styling within the greenhouse theme; ZIP filename.
- Tab labels and ordering within the locked structure.

### Deferred Ideas (OUT OF SCOPE)
- Dark-mode variant — still gated on feedback.
- PDF bundle — still deferred (ZIP decided instead).

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-03 | Pages use metric cards, tabs, and expanders with mobile-friendly columns | Standard Stack (verified widget APIs) + Pattern 1/2/3 + narrow-viewport mechanics |
| UI-07 | Dashboard bundles exports into a one-click ZIP report | `evidence_zip_bytes` builder shape + member allowlist + ZIP validation checks |

## Project Constraints (from AGENTS.md)

- Tech: Python 3, NumPy (numerics), Streamlit (dashboard UI); Matplotlib in notebooks; CSV weather input, JSON GA params.
- Order: hand-tuned fuzzy first, GA second; dashboards last. (Phase 10 is last visual pass — restyle once.)
- Compatibility: notebooks must run against `src/` functions with no duplicated logic. (Pages likewise: thin wiring over `src/` + `helpers.py`, no duplicated math.)
- GSD workflow enforcement: phase work goes through GSD commands; no direct repo edits outside workflow.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| KPI cards / tabs / expanders / stacking | Streamlit page layer (`dashboard/pages/`) | — | Pure presentation wiring; zero compute |
| ZIP byte assembly | Shared helper (`dashboard/helpers.py`) | — | All new `def`s live here per headless-audit contract; pages only call + `download_button` |
| Scoreboard/verdict/PNG bytes | Phase-8 builders (reuse) | — | `scoreboard_csv_bytes` / `verdict_text` / `fig_to_png_bytes` already tested; ZIP composes, never re-serializes |
| Frozen inputs (CSV, GA JSON, notebook PNGs) | Read-only artifacts | — | `src/`/`results/`/`weather/` untouched; ZIP reads bytes, never recomputes |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Streamlit widgets (`metric`, `columns`, `tabs`, `expander`, `download_button`) | 1.56.0 (installed, hasattr-verified this session) | KPI rows, tabbed traces, provenance expanders, ZIP download | Native Streamlit layout primitives; theme-compatible; stub-extensible headless [VERIFIED: hasattr probe 2026-09-29] |
| stdlib `zipfile` + `io.BytesIO` | Python 3.14.6 (conda env) | In-memory evidence ZIP | Only supported in-memory bundle mechanism; zero new deps; `PK` magic + `namelist()` verifiable headless [VERIFIED: probe 2026-09-29] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Phase-8 builders (`scoreboard_csv_bytes`, `verdict_text`, `fig_to_png_bytes`, `build_results_figure`) | existing | ZIP member bytes | Always — ZIP composes these, no new CSV/TXT/PNG serialization |
| `results/comparison.csv` (8 rows, header == COLUMNS) | frozen | scoreboard CSV member + KPI values | KPI cards read loaded rows; ZIP embeds raw bytes byte-identical |
| `results/ga_optimized_params.json` (schema v2) | frozen | GA JSON member | Embed raw file bytes; never re-serialize dict (keeps byte stability) |
| `notebooks/01–06` PNGs (6 files, 93–375 KB each) | committed | chart PNG members | Read as binary from disk, `writestr` into ZIP |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `zipfile` | `shutil.make_archive`, temp-file ZIP | Temp files violate in-memory-only audit rule and risk artifact-dir writes — rejected |
| Raw file bytes for GA JSON | `json.dumps` of loaded dict | Re-serialization reorders keys/whitespace and breaks byte-stability; raw bytes preserve provenance — rejected |
| New PNG renders for ZIP | Committed notebook PNGs | Re-rendering duplicates notebook logic and breaks "examiner sees committed evidence" — rejected |

**Installation:** None. Zero new installs (locked). Bare `python3` lacks streamlit — all verification runs under the conda env python that has Streamlit 1.56.0.

**Version verification:** `st 1.56.0` via `import streamlit; st.__version__`; `metric/columns/tabs/expander/download_button/slider/selectbox/dataframe/success/warning/error/stop/subheader/pyplot/cache_data/set_page_config/button` all `hasattr → True` [VERIFIED: probe 2026-09-29]. Conda python `3.14.6`. Six notebook PNGs present (01_greenhouse_model, 02_baselines, 03_fuzzy, 04_ga_optimization, 05_comparison, 06_final_results).

## Package Legitimacy Audit

No external packages installed in this phase. `zipfile`/`io`/`csv`/`json` are Python stdlib (no registry, no postinstall surface). All other code reuses already-installed, already-audited Streamlit/NumPy/Matplotlib/pandas from prior phases.

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| (none) | — | — | No installs; audit not applicable |

**Packages removed due to SLOP verdict:** none.
**Packages flagged as suspicious (SUS):** none.

## Architecture Patterns

### System Architecture Diagram

```
frozen inputs ──► helpers.py (sole new-def home) ──► pages 01–04 (thin wiring) ──► browser
     │                        │                              │
comparison.csv ──► scoreboard_csv_bytes ──┐                  ├── KPI row (metric × columns)
comparison.csv ──► verdict_text ──────────┼─► evidence_zip_bytes ──► download_button (Results, MIME application/zip)
notebooks/*.png ─► read bytes ────────────┤         │
ga_optimized_params.json ─► read bytes ───┘         │
rows ──► build_results_figure ──► fig_to_png_bytes ─┘ (chart PNG member reuses live figure builder)
```

Data flows one way: frozen bytes in, assembled ZIP bytes out. No writes to `results/`/`weather/`, no recompute, no user-supplied paths.

### Recommended Project Structure

```
dashboard/
├── helpers.py        # ADD: evidence_zip_bytes (+ optional kpi_row helper); all new defs here
├── app.py            # TOUCH (only if landing needs KPI row — else untouched)
├── pages/
│   ├── 01_model_sim.py   # ADD: KPI row + provenance expander; keep single flow
│   ├── 02_controllers.py # ADD: KPI row + T/RH/energy tabs + expander
│   ├── 03_ga_explorer.py # ADD: KPI row + expander; NO new top-level defs (audit bans def on 03)
│   └── 04_results.py     # ADD: KPI row + train/holdout tabs + expander + ZIP download_button
```

### Pattern 1: Uniform KPI row (every page header)
**What:** One `st.columns(4)` row of `st.metric` cards — holdout cost, rank, IAE_T, IAE_H for GA fuzzy (or winner) — rendered identically on all four pages, values read from already-loaded rows (Results/Controllers) or `load_scoreboard()` rows (Model Sim/GA Explorer, read-only CSV read).
**When to use:** Top of every page, before any page-specific content.
**Example:**
```python
# Source: Streamlit docs (st.metric / st.columns); values from frozen rows
kpi = next(r for r in holdout_rows if r["controller"] == "ga_fuzzy")
c1, c2, c3, c4 = st.columns(4)
c1.metric("GA holdout cost", "%.2f" % float(kpi["cost"]))
c2.metric("GA holdout rank", "#%s" % kpi["rank"])
c3.metric("IAE_T", "%.2f" % float(kpi["iae_T"]))
c4.metric("IAE_H", "%.2f" % float(kpi["iae_H"]))
```

### Pattern 2: Targeted tabs (locked structure only)
**What:** Controllers page wraps its three trace groups in `st.tabs(["Temperature", "Humidity", "Energy"])`; Results page wraps scoreboard views in `st.tabs(["Train", "Holdout"])`. Other pages keep single flow — no tabs elsewhere.
**When to use:** Exactly the two locked pages; tab labels/order are agent's discretion.
**Example:**
```python
# Source: Streamlit docs (st.tabs); unpack pattern
tT, tH, tE = st.tabs(["Temperature", "Humidity", "Energy"])
with tT:
    st.pyplot(temp_fig)  # figures still built by helpers, never savefig on page
```

### Pattern 3: Provenance expander (per page)
**What:** One `st.expander("Provenance / how to reproduce")` per page with 3–6 lines: frozen file names + seeds + weights + notebook pointer. Static text only, no compute.
**When to use:** Bottom of each page (agent's discretion on contents).
**Example:**
```python
# Source: Streamlit docs (st.expander)
with st.expander("Provenance"):
    st.write("Scoreboard: results/comparison.csv (8 rows, frozen). Seeds 7/21, weights 1.0/1.0/0.01.")
```

### Pattern 4: In-memory ZIP builder (helpers.py)
**What:** `evidence_zip_bytes()` assembles the fixed member list with `zipfile.ZIP_DEFLATED` into a fresh `BytesIO`, returns `buf.getvalue()`. Member bytes come from existing builders (CSV/TXT/PNG-live) + raw file reads (notebook PNGs, GA JSON). No parameters for paths or member selection — fixed allowlist.
**When to use:** Called once by the Results page; result passed straight to `st.download_button(..., mime="application/zip")`.
**Example:**
```python
# Source: stdlib zipfile docs; probe-verified PK magic + namelist 2026-09-29
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

### Anti-Patterns to Avoid
- **New `def` on 03_ga_explorer / `savefig`/`plt.show`/`Agg` on any page:** breaks `test_source_audits` — put all logic in `helpers.py`.
- **`"w"`-mode opens or writes into `results/`/`weather/`:** breaks `test_artifacts_untouched` — ZIP is `BytesIO`-only.
- **Recomputing ranking or verdict on pages:** ranking follows the CSV `rank` column, verdict follows rank-1 identity — never `argsort`/`compare(`.
- **Multi-column grids for charts:** max 2 columns; charts go full-width stacked so narrow viewports never h-scroll.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ZIP assembly | Custom archive format / manual byte concat | stdlib `zipfile` + `BytesIO` | Central-directory structure, compression, and corrupt-archive edge cases |
| CSV/TXT/PNG serialization for ZIP | New formatters | Phase-8 `scoreboard_csv_bytes` / `verdict_text` / `fig_to_png_bytes` | Already magic-byte + byte-identical tested; duplicates drift |
| KPI/rank computation | Inline cost math on pages | Frozen CSV `rank` column + `holdout_ranking` | Recomputation risks contradicting the frozen verdict |
| Responsive layout | Custom CSS/JS breakpoints | `st.columns` vertical stacking + single-column chart flow | Streamlit stacks columns vertically in narrow viewports natively; custom CSS is fragile across versions |

**Key insight:** The ZIP is a pure function over frozen bytes — every hard problem (CSV formatting, verdict wording, PNG encoding) was already solved and tested in Phase 8. The only new code is the member list + `ZipFile` wrapper.

## Common Pitfalls

### Pitfall 1: Headless stub can't handle tabs/expander/metric-context
**What goes wrong:** Current `_Stub.__getattr__` returns `_noop → None` for `tabs`/`expander`/`metric`; pages doing `tT, tH, tE = st.tabs([...])` (unpack of `None`) or `with st.expander(...)` (`None` has no `__enter__`) crash at import, failing `test_pages_import`.
**Why it happens:** Stub predates layout widgets; `columns` got a bespoke handler but `tabs`/`expander` didn't.
**How to avoid:** Extend the stub in the same commit as the first tabbed page: `tabs` returns `[_Stub() …]` sized to the labels arg (mirror the `columns` handler); give `_Stub` `__enter__`/`__exit__` returning self so `with st.expander` / `with tab:` work; `metric`/`write` stay `_noop → None`.
**Warning signs:** `TypeError: cannot unpack non-iterable NoneType` or `AttributeError: __enter__` in `test_pages_import`.

### Pitfall 2: Empty ZIP download (BytesIO cursor)
**What goes wrong:** `download_button` serves zero bytes because the buffer was never rewound.
**Why it happens:** `ZipFile.close()` leaves the cursor at end-of-stream; passing the `BytesIO` object (or `getvalue()` before close) yields empty/truncated data.
**How to avoid:** Canonical close-then-`getvalue()` shape: exit the `with ZipFile(...)` block first, then `return buf.getvalue()` (or `buf.seek(0)` if passing the buffer). Headless assert: `data[:2] == b"PK"` and `len > 1024`.
**Warning signs:** ZIP downloads but OS reports "archive is empty/corrupt".

### Pitfall 3: KPI cards recompute instead of reading frozen rows
**What goes wrong:** A page recomputes cost/rank inline and disagrees with the frozen verdict (e.g., different weights), or calls `compare(`/`all_metrics` on the Results path.
**Why it happens:** Copy-pasting metric code instead of reading the loaded rows.
**How to avoid:** KPI values come only from `holdout_ranking(rows)` / row dict lookups; add `"compare("`, `"argsort"`, `"all_metrics"` to the Results-page source audit if the suite doesn't already cover the new lines.
**Warning signs:** Verdict on one page differs from `holdout_verdict.txt` in the ZIP.

### Pitfall 4: Wide layout breaks narrow viewports
**What goes wrong:** Side-by-side chart columns or 4-wide KPI grids force horizontal scroll on a narrow/examiner-laptop viewport.
**Why it happens:** `st.columns(3+)` holding figures, or charts with fixed wide `figsize` inside columns.
**How to avoid:** KPI row is max 4 narrow text cards (acceptable; Streamlit stacks them vertically when narrow); every figure lives full-width outside columns; assert headless: no `st.pyplot` call indented inside a `with col` block (source scan), figures use existing `figsize` values.
**Warning signs:** Any new `st.columns(3)` or columns wrapping `st.pyplot`.

### Pitfall 5: ZIP member drift (names/bytes silently change)
**What goes wrong:** ZIP contains a renamed member, a missing PNG, or re-serialized JSON that no longer matches the committed artifact.
**Why it happens:** Hand-typed member names; `json.dumps` instead of raw bytes.
**How to avoid:** Single `ZIP_MEMBERS` constant (ordered list) in `helpers.py`; notebook PNGs + GA JSON embedded as raw `open(..., "rb").read()`; headless test asserts exact `namelist()` + CSV-member `== frozen bytes` + GA-member `== frozen bytes`.
**Warning signs:** `namelist()` order differs between runs; JSON member fails `json.loads` equality with file.

## Code Examples

### In-memory ZIP + download button (canonical)
```python
# Source: stdlib zipfile docs + Streamlit st.download_button docs; magic verified 2026-09-29
# helpers.py
import io, zipfile
ZIP_MEMBERS = ["comparison.csv", "holdout_verdict.txt", "results_scoreboard.png",
               "01_greenhouse_model.png", "02_baselines.png", "03_fuzzy.png",
               "04_ga_optimization.png", "05_comparison.png", "06_final_results.png",
               "ga_optimized_params.json"]
def evidence_zip_bytes():
    ...  # as Pattern 4; returns bytes starting with b"PK"
# 04_results.py (thin wiring only)
st.download_button("Download evidence pack (ZIP)", data=evidence_zip_bytes(),
                   file_name="greenhouse_evidence_pack.zip", mime="application/zip")
```

### Headless ZIP assertions
```python
# Source: established test_dashboard.py conventions (magic-byte + byte-identical style)
data = helpers.evidence_zip_bytes()
assert data[:2] == b"PK", data[:8]
z = zipfile.ZipFile(io.BytesIO(data))
assert z.namelist() == helpers.ZIP_MEMBERS, z.namelist()
assert z.read("comparison.csv") == open("results/comparison.csv", "rb").read()
assert z.read("ga_optimized_params.json") == open("results/ga_optimized_params.json", "rb").read()
assert z.read("results_scoreboard.png")[:4] == b"\x89PNG"
```

### Headless layout assertions (source scan, survives the stub)
```python
# Source: test_source_audits convention in tests/test_dashboard.py
src = open("dashboard/pages/02_controllers.py").read()
assert "st.tabs" in src and "st.metric" in src and "st.expander" in src
assert "savefig" not in src and "plt.show" not in src
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-chart PNG downloads only (Phase 8) | + one-click ZIP evidence pack | This phase (UI-07) | Examiners leave with one file |
| Bare metrics + sequential charts | Uniform KPI rows + targeted tabs + expanders | This phase (UI-03) | Presentation-grade, mobile-usable |

**Deprecated/outdated:**
- Temp-file ZIP via `shutil.make_archive`: rejected — violates in-memory-only audit.
- PDF bundle: deferred per CONTEXT.md — ZIP decided instead.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Streamlit stacks `st.columns` vertically (no h-scroll) in narrow viewports on 1.56.0 — from docs/training, not probe-verified headless | Narrow-viewport mechanics | Low — layout still correct on desktop; mitigation is stacking discipline + headless source-scan, which holds regardless |
| A2 | ZIP filename choice (`greenhouse_evidence_pack.zip` suggested) is agent's discretion and examiner-acceptable | Code Examples | Negligible — rename is one literal on the page |

## Open Questions

1. **KPI on app.py landing?**
   - What we know: D-01 says "every page header" — the four numbered pages clearly; landing is ambiguous.
   - What's unclear: Whether examiners count `app.py` as a "page".
   - Recommendation: Put the KPI row on all four numbered pages; add to `app.py` only if trivial (landing has no loaded rows — needs a `load_scoreboard` read). Planner decides; default to pages-only.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Streamlit (+ metric/columns/tabs/expander/download_button) | UI-03, UI-07 wiring | ✓ | 1.56.0 | — |
| Python stdlib `zipfile`/`io` | ZIP builder | ✓ | 3.14.6 (conda) | — |
| Matplotlib (`savefig`→BytesIO) | chart PNG member | ✓ | 3.10.8 (per v1.1 research) | — |
| Notebook PNGs 01–06 | ZIP members | ✓ | 6 files on disk | — |
| `results/comparison.csv` + `ga_optimized_params.json` | ZIP members + KPIs | ✓ | 8-row CSV, schema v2 | — |
| Browser screenshots | narrow-viewport proof | ✗ | — | Column-structure source scan + stacking reasoning (locked D-04) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** browser rendering → headless structural asserts (locked).

## Validation Architecture

Test framework: standalone headless suite `tests/test_dashboard.py` (plain-assert, pytest-compatible names, `python tests/test_dashboard.py`). No framework install; stubbed-streamlit import smoke + source audits + artifact guards.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| UI-03 | KPI row on all 4 pages (cost+rank+IAE_T/IAE_H) | source-scan + stub import | `python tests/test_dashboard.py` (new `test_layout_elements`: `st.metric`/`st.columns(4)` present per page; KPI values equal frozen holdout row) | ❌ Wave 0 (new asserts) |
| UI-03 | Targeted tabs (Controllers T/RH/energy; Results train/holdout; no tabs elsewhere) | source-scan + stub import | same suite (`st.tabs` in 02/04 only; pages import under extended stub) | ❌ Wave 0 |
| UI-03 | Expander per page; no savefig/show/Agg; no new defs on 03 | source-scan | existing `test_source_audits` extended (`st.expander` in all 4; ban list unchanged) | ❌ Wave 0 (extend) |
| UI-03 | Narrow stacking (no h-scroll) | structural source-scan | same suite (no `st.pyplot` inside `with col`; no `columns(3+)` wrapping figures) | ❌ Wave 0 |
| UI-07 | ZIP magic + member list + byte-identical CSV/JSON + PNG magic | unit (bytes) | same suite (new `test_evidence_zip`: `PK` magic, `namelist()==ZIP_MEMBERS`, CSV/JSON `==` frozen, PNG `89 50 4E 47`) | ❌ Wave 0 |
| UI-07 | ZIP button wired (filename + `application/zip`) | source-scan | same suite (`evidence_pack` + `application/zip` in 04_results) | ❌ Wave 0 |
| Regression | Full suite green + artifacts untouched | suite + git gate | `python tests/test_dashboard.py` then `git status --porcelain results/ weather/` clean | ✅ exists |

### Sampling Rate
- **Per task commit:** `python tests/test_dashboard.py`
- **Per wave merge:** full suite + `git status --porcelain results/ weather/` clean
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Extend `_stub_streamlit`: `tabs` → list-of-`_Stub` (mirror `columns` handler); `_Stub.__enter__/__exit__` → self (for `with` blocks)
- [ ] New `test_layout_elements` + `test_evidence_zip` in `tests/test_dashboard.py` (shapes above)
- [ ] Extend `test_source_audits` allow/ban lists for tabs/expander/ZIP (no new bans expected)
- [ ] Framework install: none (stdlib + installed env only)

Pass criteria: suite prints `all checks passed`; ZIP `[:2]==b"PK"`, exact 10-member namelist, CSV/JSON members byte-identical to frozen files, PNG member magic `b"\x89PNG"`; all four pages import under the stub; `results/`+`weather/` git-clean.

## Security Domain

Surface: ZIP byte builder + layout wiring code. No network, no user-supplied paths, no new deps, no secrets. ASVS L1 scope only.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A (local academic dashboard, no users) |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | Fixed ZIP member allowlist; no user-controlled paths/weights; page sliders keep existing bounds |
| V6 Cryptography | no | N/A (ZIP unencrypted evidence pack; `ZIP_DEFLATED` is compression, not crypto — never hand-roll) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| ZIP-slip / path traversal on extract | Tampering | Fixed `writestr` names (no directories, no `../`); members are flat basenames from `ZIP_MEMBERS` constant |
| Artifact overwrite via download path | Tampering | In-memory `BytesIO` only; `file_name` literals live on pages; never `"w"`-open under `results/`/`weather/` (audit-guarded) |
| Provenance spoofing (ZIP disagrees with frozen files) | Spoofing | CSV/JSON/PNG members byte-compared to frozen files in tests; ranking/verdict read from CSV, never recomputed |
| Zip-bomb / memory blowup | Denial of service | Members total < ~2 MB (6 PNGs + CSV + JSON + 1 rendered PNG); single on-demand build, no caching of ZIP bytes needed |

## Sources

### Primary (HIGH confidence)
- Installed-env hasattr probe 2026-09-29: Streamlit 1.56.0 all layout/download APIs present; stdlib `zipfile.ZIP_DEFLATED` present; conda python 3.14.6
- Direct code reads: `dashboard/helpers.py` (byte builders, IN-03/WR-01 patterns), `dashboard/app.py`, `pages/01–04` (current layout, wiring), `tests/test_dashboard.py` (stub shape, audit bans, export conventions)
- Direct artifact reads: `results/comparison.csv` (8-row header sample), `results/ga_optimized_params.json` (keys + schema v2), `notebooks/*.png` (6 files, sizes)
- In-memory ZIP probe 2026-09-29: `PK` magic + `namelist()` round-trip verified

### Secondary (MEDIUM confidence)
- Streamlit official docs knowledge: `st.metric`/`st.columns`/`st.tabs`/`st.expander`/`st.download_button(data=bytes, mime=…)` semantics (consistent with installed API surface)
- Python stdlib docs knowledge: `zipfile.ZipFile(writestr)` + `BytesIO.getvalue()` close-then-read shape (probe-confirmed)

### Tertiary (LOW confidence)
- Narrow-viewport column-stacking behavior (A1, flagged for reasoning-only verification per D-04)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — hasattr-verified on installed 1.56.0 + zero new installs.
- Architecture: HIGH — direct reads of all pages/helpers/tests; ZIP is composition of tested builders.
- Pitfalls: HIGH — stub gap identified from actual stub source; ZIP cursor/member-drift guards probe-verified.

**Research date:** 2026-09-29
**Valid until:** 30 days (stable domain: pinned Streamlit, stdlib, frozen artifacts)
