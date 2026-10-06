# Phase 08: Theme + Export Foundation - Research

**Researched:** 2026-09-29
**Domain:** Streamlit theming (`config.toml`) + in-memory download exports (CSV/PNG/TXT) over frozen artifacts
**Confidence:** HIGH

## Summary

Phase 08 gives the 4-page Streamlit dashboard its greenhouse identity and its take-away plumbing: a light-greenhouse `.streamlit/config.toml` theme plus a new `dashboard/helpers.py` module of byte-builder functions (scoreboard CSV bytes, verdict TXT, per-chart PNG bytes) wired as `st.download_button`s on the pages where the content lives. Zero new installs, zero control-logic changes, frozen `results/`/`weather/` untouched.

The environment was probe-verified this session: Streamlit 1.56.0 on conda Python 3.14.6 with `download_button` present, Matplotlib 3.10.8, pandas 3.0.1. The canonical BytesIO pattern (`savefig(buf, format="png")` → `buf.seek(0)` → `download_button(data=buf, mime=...)`) was executed live and produced valid `\x89PNG` magic bytes. The theme `[theme]` key set (`base`, `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`) is confirmed against current official Streamlit docs. The hard constraint shaping every implementation choice is the headless suite `tests/test_dashboard.py`: pages may contain no `savefig`/`plt.show`/`use("Agg")`, no absolute paths, no `"w"` opens, and page 03 may contain zero top-level `def`/`class` — so ALL new Python `def`s live in `dashboard/helpers.py` and pages stay thin wiring.

**Primary recommendation:** Write `.streamlit/config.toml` first (zero code, zero test surface), then `dashboard/helpers.py` with three cached byte builders (`scoreboard_csv_bytes`, `verdict_text`, `figure_png_bytes`) plus thin `download_button` wiring per page, extending the test stub for `download_button` in the same commit.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (Theme):** Light greenhouse theme via `.streamlit/config.toml`: fresh greens + earth tones, light backgrounds, charts stay readable. No dark mode, no toggle (kept out — single-theme discipline).
- **D-02 (Formats):** CSV + PNG + TXT only: scoreboard CSV (frozen bytes), per-chart PNGs (BytesIO `savefig` + `seek(0)` + explicit MIME), verdict TXT. No PDF bundle (deferred to Phase 10's ZIP decision if at all).
- **D-03 (Placement):** Downloads live where the content lives: scoreboard CSV + verdict TXT on Results, chart PNG buttons on each chart's page (Model Sim, Controllers, GA Explorer, Results).
- **D-04 (Verdict content):** Full breakdown TXT: winner + margins + per-term IAE_T/IAE_H/E breakdown for all four controllers + seeds/weights provenance (train 7, holdout 21, 1.0/1.0/0.01). Mirrors the notebook verdict cell, never recomputes beyond reading the CSV.

### Agent's Discretion
- Exact palette hex values within the greenhouse family; BytesIO helper shapes inside `dashboard/helpers.py`; button labels/placement within each page; PNG dpi for downloads.
- Chart-figure capture mechanics (rebuilding vs caching figure objects) within the no-recompute rule.

### Deferred Ideas (OUT OF SCOPE)
- Dark-mode variant — gated on user feedback, not built speculatively.
- PDF bundle — deferred; Phase 10 decides ZIP-vs-PDF only if asked.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Dashboard applies a greenhouse theme via `.streamlit/config.toml` with readable charts in light mode | `[theme]` key set verified vs official docs; palette + explicit-matplotlib-colors pattern below; human screenshot is the acceptance check (theme is invisible to the test suite) |
| UI-02 | Dashboard exports comparison results to disk — scoreboard CSV, chart PNG, and verdict summary downloads | Byte-builder shapes + MIME/filename table + `savefig`-before-`st.pyplot` ordering rule + headless magic-byte assertions below |

## Project Constraints (from AGENTS.md)

- **Tech:** Python 3, NumPy (numerics), Streamlit (dashboard UI). Matplotlib for plotting. CSV for weather input, JSON for GA params. No new libraries — zero-install constraint stands.
- **Order:** Dashboards last (this phase is dashboard-only; `src/` science is finished and frozen).
- **Compatibility:** No duplicated logic — pages/helpers reuse `src/` functions (`COLUMNS`, CSV readers, `tri`/`infer` kernels); never retype frozen contracts.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Greenhouse chrome theme (backgrounds, accents, widgets) | Streamlit config sidecar | — | `.streamlit/config.toml [theme]` is the only supported theming mechanism; zero Python impact |
| Chart readability under theme | Matplotlib figure code (helpers) | — | Streamlit theme does NOT restyle matplotlib figures — every figure needs explicit face/ink colors |
| Export byte generation (CSV/TXT/PNG) | `dashboard/helpers.py` | — | Forced by headless source audits: no `savefig`, no `def` (p03), no writes in pages |
| Download delivery (buttons, filenames, MIME) | Page files (thin wiring) | — | `st.download_button` calls are page-level UI; byte payloads come from helpers |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Streamlit | 1.56.0 [VERIFIED: probe `streamlit.__version__` this session] | Theme host + `download_button` delivery | Pinned installed ceiling; `download_button` signature introspected live |
| Matplotlib | 3.10.8 [VERIFIED: probe this session] | PNG export engine (`savefig` to `BytesIO`) | Only export renderer needed; `PdfPages` available but out of scope (no PDF) |
| Python stdlib `io`/`csv` | 3.14.6 [VERIFIED: `python --version` this session] | `BytesIO` buffers, frozen-CSV reads | No temp files, no disk writes from UI |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | 3.0.1 [VERIFIED: probe this session] | Optional CSV formatting via `DataFrame.to_csv()` | Only if convenient; stdlib `csv` already owns the scoreboard path — prefer stdlib passthrough of frozen bytes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib CSV passthrough | `pandas.to_csv()` re-render | Re-render risks byte drift from the frozen artifact; passthrough guarantees byte-identity |
| `config.toml` theme | Custom CSS injection | CSS is unsupported/fragile across versions and invisible to version guarantees; `config.toml` is the documented mechanism [CITED: docs.streamlit.io/develop/concepts/configuration/theming] |
| `BytesIO` downloads | Temp files on disk | Temp files trip the `"w"`-open audit and risk artifact-dir pollution; in-memory only |

**Installation:**
```bash
# Nothing to install. Zero-install phase — all APIs verified present in the installed env.
```

**Version verification:** `streamlit 1.56.0`, `matplotlib 3.10.8`, `pandas 3.0.1`, `python 3.14.6` — all confirmed via live probes this session (see Environment Availability). No registry lookups needed: no new packages.

## Package Legitimacy Audit

No external packages installed in this phase. **Audit result: NOT APPLICABLE — zero new installs** (locked v1.1 constraint, re-confirmed in CONTEXT.md D-boundary). Planner must reject any plan step proposing `pip/conda install`.

## Architecture Patterns

### System Architecture Diagram

```
results/comparison.csv (frozen, 8 rows) ──read-only──▶ dashboard/helpers.py ──bytes──▶ 04_results.py
        │                                                   │                    (CSV + TXT + PNG buttons)
        │ verdict mirror                                    │
        ▼                                                   ▼
notebooks/05 verdict cell (reference only)          st.download_button(data=<bytes>, mime=..., file_name=...)
                                                        ▲
page figures (01/02/03/04, rebuilt        savefig(buf) ─┘
 from src/ + frozen JSON, explicit         BEFORE st.pyplot(fig);
 light-figure colors)                      buf.seek(0); never to disk

.streamlit/config.toml ──applies at server start──▶ Streamlit chrome (sidebar, widgets, metric cards)
        ╳ does NOT touch matplotlib figures (separate explicit-color step per figure)
```

### Recommended Project Structure
```
.streamlit/
└── config.toml          # NEW — [theme] greenhouse palette (zero code)
dashboard/
├── helpers.py           # NEW — ALL new defs: scoreboard_csv_bytes, verdict_text,
│                        #         figure_png_bytes (+ small page-specific fig builders)
└── pages/
    ├── 01_model_sim.py  # MODIFIED — wiring only: +1 PNG download button
    ├── 02_controllers.py# MODIFIED — wiring only: +1 PNG download button
    ├── 03_ga_explorer.py# MODIFIED — wiring only: +2 PNG buttons, ZERO new defs
    └── 04_results.py    # MODIFIED — wiring only: CSV + TXT + PNG buttons
                         # (load_scoreboard/holdout_ranking stay; no recompute)
```

### Pattern 1: Cached byte builders in helpers, thin buttons in pages
**What:** `helpers.py` exposes pure functions returning `bytes` (or `str` for CSV/TXT); pages call them inside `st.download_button(data=...)`. Byte generation is wrapped in `@st.cache_data` so reruns don't re-render figures.
**When to use:** Every export in this phase; Phase 9/10 reuse the same shapes (scenario CSVs, ZIP bundle composes these primitives).
**Example:**
```python
# Source: probe-verified this session (signature introspected on installed 1.56.0)
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

# page wiring (thin — allowed in pages, no def/savefig):
st.download_button("Download chart (PNG)", data=figure_png_bytes("results"),
                   file_name="results_scoreboard.png", mime="image/png")
```

### Pattern 2: Frozen-byte passthrough for the scoreboard CSV
**What:** CSV download bytes are the raw file bytes of `results/comparison.csv`, never a re-render. Header is asserted `== COLUMNS` at build time (fail-closed provenance).
**When to use:** UI-02 scoreboard export; verdict TXT derives from the same rows.
```python
# Source: established page pattern dashboard/pages/04_results.py:30-41 + src/metrics.py:32-38
from src.metrics import COLUMNS  # ["controller","weather","rmse_T",...,"cost","rank"] (14 cols)

def scoreboard_csv_bytes(path: str = "results/comparison.csv") -> bytes:
    with open(path, "rb") as f:       # binary read preserves frozen bytes exactly
        raw = f.read()
    header = raw.split(b"\n", 1)[0].decode("utf-8").split(",")
    assert header == COLUMNS, "stale artifact: header != COLUMNS"
    return raw
# page: st.download_button("Download scoreboard (CSV)", data=scoreboard_csv_bytes(),
#                         file_name="comparison.csv", mime="text/csv")
```

### Pattern 3: Verdict TXT mirrors the notebook, never recomputes
**What:** `verdict_text(rows)` formats winner + margins + per-term `iae_T/iae_H/energy/cost` for all four holdout controllers + provenance line, reading only the CSV rows and `results/ga_optimized_params.json` metadata. Ranking follows the CSV `rank` column (stable sort, ties keep row order) — identical to page helper `holdout_ranking` [VERIFIED: dashboard/pages/04_results.py:44-47].
**When to use:** UI-02 verdict download on Results page.

### Anti-Patterns to Avoid
- **`savefig`/`plt.show`/`use("Agg")` in any page:** fails `test_source_audits`. All figure serialization lives in helpers.
- **Top-level `def`/`class` on 03_ga_explorer.py:** fails the audit loop (`assert not s.startswith("def ")`) [VERIFIED: tests/test_dashboard.py:199-201]. Page-03 figure builders for PNG export must live in helpers, parameterized by the selectbox value passed as an argument.
- **Recomputing ranking with `argsort`/fresh sims on Results:** fails `test_results_helper` (`"compare(" not in src`, `"argsort" not in src`). Rank comes from the CSV column only.
- **Passing a path string as `download_button(data=...)`:** downloads the literal path text. Always pass bytes/str/BytesIO content.
- **Forgetting `buf.seek(0)`:** yields a 0-byte download — the single most common corruption cause.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| App chrome theming | Custom CSS / component hacks | `.streamlit/config.toml [theme]` | Documented, version-stable mechanism [CITED: docs.streamlit.io/develop/api-reference/configuration/config.toml] |
| CSV serialization | Hand-rolled join/format | Frozen file bytes (or stdlib `csv` for derived frames) | Byte-identity with provenance artifact; edge cases (quoting, `inf` settling) already settled |
| PNG encoding | Manual raster code | `fig.savefig(buf, format="png")` | Handles dpi/fonts/antialiasing; magic-byte testable |
| Download transport | Anchor-tag HTML hacks | `st.download_button` (verified present 1.56.0) | Correct MIME/filename plumbing + headless-stubable |

**Key insight:** This phase is plumbing, not invention — every primitive (theme keys, download button, BytesIO savefig) is a long-stable official pattern. Correct bytes + MIME + filenames matter more than button styling.

## Common Pitfalls

### Pitfall 1: Streamlit theme doesn't restyle matplotlib figures
**What goes wrong:** Green-tinted app chrome with default-white charts that clash, or (worse) dark-ink-on-dark assumptions that become unreadable.
**Why it happens:** The `[theme]` table styles Streamlit chrome only; matplotlib keeps its own `rcParams` [CITED: docs.streamlit.io/develop/concepts/configuration/theming].
**How to avoid:** Set explicit `fig.patch`/`ax` facecolors, tick/label/legend colors, and grid alpha on every figure built in helpers (light-background inks). Keep default matplotlib `C0..` series colors — they are readable on light grounds.
**Warning signs:** Screenshot check shows chart background differing from app background in a bad way; green primary applied to a line color destroying contrast.

### Pitfall 2: Empty/corrupt downloads (stream position, ordering)
**What goes wrong:** 0-byte PNGs or truncated files.
**Why it happens:** Missing `buf.seek(0)` after `savefig`; calling `savefig` AFTER `st.pyplot(fig)` (mutated/closed figure); passing a path string as `data`.
**How to avoid:** Canonical order — `savefig(buf)` → `plt.close(fig)` → `buf.seek(0)` → return bytes → `download_button(data=<bytes>)`. Executed live this session: magic `\x89PNG\r\n\x1a\n`, 27 KB at dpi=150 [VERIFIED: live probe].
**Warning signs:** Headless magic-byte assertion fails; downloaded file won't open.

### Pitfall 3: Breaking the headless suite with new page code
**What goes wrong:** `tests/test_dashboard.py` goes red (import smoke, source audits, artifacts-untouched).
**Why it happens:** New `def`s/`savefig`/absolute paths/`"w"` opens added to pages; `download_button` missing from the test stub returns `None` — safe at import, but stub should still expose it for forward-compat; new widgets that execute at import with surprising return values.
**How to avoid:** ALL new `def`s in helpers; extend `_stub_streamlit` with a `download_button` entry in the SAME commit as first page use; run `python tests/test_dashboard.py` after every change; `git status --porcelain results/ weather/` must be clean.
**Warning signs:** `FAIL test_source_audits` names the offending page and token.

### Pitfall 4: Verdict drift from the notebook
**What goes wrong:** TXT says something the notebook verdict cell doesn't (different margins, recomputed costs, wrong seeds).
**Why it happens:** Recomputing instead of reading; formatting floats with different rounding than the `%.2f` convention; misquoting provenance.
**How to avoid:** Mirror notebook `05_comparison.ipynb` cell 5 logic verbatim: relative ordering asserts (`ga < on/off AND ga < pid`), `%.2f` costs, provenance `train_seed=7 / holdout_seed=21 / weights 1.0/1.0/0.01` — weights locked at [VERIFIED: src/metrics.py:30] `W1, W2, W3 = 1.0, 1.0, 0.01`, weathers locked at [VERIFIED: src/metrics.py:43-44] `("train-seed7", ...)` / `("holdout-seed21", ...)`.
**Warning signs:** TXT winner ≠ `ranked[0]` from CSV; holdout costs differ from comparison.csv row values.

### Pitfall 5: Chart-figure capture that violates no-recompute
**What goes wrong:** PNG helper re-runs closed loops or calls `compare()` to rebuild a figure, slowing pages and risking artifact writes.
**Why it happens:** Confusing "rebuild figure" (allowed — cheap re-plot from already-loaded rows/traces) with "recompute science" (banned).
**How to avoid:** Figure builders take already-available inputs (CSV rows for Results; cached `run_all_four` outputs passed from the page for Controllers; frozen JSON for Explorer). Never import `compare`/`evolve`/`genetic_algorithm` in helpers or pages.

## Code Examples

### Greenhouse `[theme]` sidecar (concrete starter palette, agent's-discretion hexes)
```toml
# Source: key set per [CITED: docs.streamlit.io/develop/api-reference/configuration/config.toml];
# hex values [ASSUMED] — planner/user may adjust within the greenhouse family.
[theme]
base = "light"
primaryColor = "#2E7D32"          # leaf green — interactive accents
backgroundColor = "#F7FAF3"       # pale greenhouse white
secondaryBackgroundColor = "#E8F0E1"  # misted-glass widget wells
textColor = "#263023"             # soil-ink body text
font = "sans serif"
```
Notes: `base = "light"` is load-bearing (single-theme discipline, no dark variant). Sidebar inherits unless `[theme.sidebar]` overrides — leave unset for uniformity. All six keys above are valid `[theme]` options on current docs; `base`/`primaryColor`/`backgroundColor`/`secondaryBackgroundColor`/`textColor`/`font` are the stable core also present since long before 1.56.0.

### CSV download (utf-8 str alternative)
```python
# Source: pattern from dashboard/pages/04_results.py:30-41; MIME per official download_button docs
st.download_button("Download scoreboard (CSV)", data=scoreboard_csv_bytes(),
                   file_name="comparison.csv", mime="text/csv")
# data may be bytes (preferred, byte-identical) or utf-8 str; mime "text/csv" is the
# explicit-MIME requirement from D-02. Never omit mime (browser sniffing varies).
```

### Verdict TXT download
```python
# Source: mirrors notebooks/05_comparison.ipynb cell 5 + page verdict block 04_results.py:62-74
st.download_button("Download verdict (TXT)", data=verdict_text(rows),
                   file_name="holdout_verdict.txt", mime="text/plain")
```

### MIME + filename contract
| Download | `data` type | `mime` | `file_name` |
|----------|-------------|--------|-------------|
| Scoreboard CSV | `bytes` (frozen file) | `text/csv` | `comparison.csv` |
| Verdict TXT | `str` (utf-8) | `text/plain` | `holdout_verdict.txt` |
| Chart PNG | `bytes` (`\x89PNG` magic) | `image/png` | `<page>_<chart>.png` (e.g. `results_scoreboard.png`) |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom CSS theme hacks | `.streamlit/config.toml [theme]` (+ `[theme.light/dark]` switchable tables on recent versions) | Stable for years; switchable tables documented current | Use config keys only; no CSS |
| `st.pyplot` only, no exports | `st.download_button(data=BytesIO...)` | Long-stable; signature on 1.56.0 introspected live (adds `width`/`shortcut` params vs older) | Pass bytes + explicit MIME; ignore newer-only params |

**Deprecated/outdated:**
- `st.experimental_*` download/caching aliases: gone — use `st.download_button` / `st.cache_data` (both verified present on 1.56.0).
- PDF export libs (reportlab/fpdf2): explicitly rejected — no PDF in this phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Palette hexes (`#2E7D32` etc.) read as "greenhouse" and keep charts readable | Code Examples | Low — cosmetic; user eyeballs screenshots and planner may adjust hexes freely |
| A2 | `download_button(data=str)` utf-8 handling + `text/csv`/`text/plain`/`image/png` MIME acceptance on 1.56.0 | Code Examples | Low — signature introspected live, but MIME rendering is browser-side; headless tests assert bytes, human click-through confirms filenames |
| A3 | PNG dpi default 150 balances crispness vs payload (~27 KB probe) | Architecture Patterns | Low — agent's discretion; raise to 200 if screenshots look soft |
| A4 | Rebuilding page figures inside helpers from passed-in rows/traces satisfies "no-recompute" | Pitfall 5 | Medium — discuss-phase owns the rebuild-vs-cache call; planner should keep builders pure functions of page-supplied inputs |

**Verified (not assumed):** env versions, `download_button` presence/signature, BytesIO-PNG magic, COLUMNS 14-col contract + locked weights + weather pairs (src/metrics.py), all page/audit rules (tests/test_dashboard.py), comparison.csv 8-row shape, `.streamlit/` + `helpers.py` absent, theme key validity (official docs).

## Open Questions

1. **Figure-capture mechanics: rebuild vs cache figure objects?**
   - What we know: Pages currently build figures inline then `st.pyplot(fig)`. Helpers must produce PNG bytes without `savefig` in pages.
   - What's unclear: Whether to (a) move figure construction into helpers returning `(fig, png_bytes)` or (b) keep construction in pages and add helpers that re-plot from passed data. Option (a) collides with the 03 zero-`def` rule only if defs land on the page — they won't; but option (b) duplicates plot code.
   - Recommendation: Option (a) — figure-builder `def`s in helpers, pages call `fig = build_x(...); st.pyplot(fig)` + `download_button(data=fig_to_png(fig))`. Planner decides; either satisfies audits.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| conda python | everything | ✓ | 3.14.6 | — |
| Streamlit | theme + downloads | ✓ | 1.56.0 (`download_button`, `tabs`, `metric` all present) | — |
| Matplotlib (+Agg) | PNG bytes | ✓ | 3.10.8 (Agg probe OK) | — |
| pandas | optional CSV | ✓ | 3.0.1 | stdlib `csv` |
| `.streamlit/` dir | theme sidecar | ✗ (absent) | — | Create it — planner adds sidecar task |
| `dashboard/helpers.py` | byte builders | ✗ (absent) | — | Create it — core phase task |
| bare `python3` + streamlit | — | ✗ | — | Never reference; use conda `python` only |

**Missing dependencies with no fallback:** none — everything needed is installed.
**Missing dependencies with fallback:** none.

## Validation Architecture

Test framework: the repo's standalone headless suite — no pytest. Command: `python tests/test_dashboard.py` (prints PASS/FAIL per check, `sys.exit(1)` on failure). Streamlit is stubbed in `sys.modules`; matplotlib forced to `Agg` by the harness — pages must never set it.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Greenhouse theme loads; charts readable | manual-only (screenshot) | `python -m streamlit run dashboard/app.py` → eyeball light theme + chart contrast | ❌ Wave 0 (sidecar absent — the phase creates it) |
| UI-02a | Scoreboard CSV downloads byte-identical | unit (headless, no browser) | `python -c "from dashboard.helpers import scoreboard_csv_bytes; b=scoreboard_csv_bytes(); assert b==open('results/comparison.csv','rb').read()"` | ❌ Wave 0 (helpers absent) |
| UI-02b | Chart PNGs download as valid PNG | unit (headless) | `python -c "from dashboard.helpers import figure_png_bytes; assert figure_png_bytes('results')[:8]==b'\x89PNG\r\n\x1a\n'"` | ❌ Wave 0 |
| UI-02c | Verdict TXT mirrors notebook (winner+margins+terms+provenance) | unit (headless) | `python -c "from dashboard.helpers import verdict_text; t=verdict_text(); assert 'ga_fuzzy' in t and 'train_seed' in t"` | ❌ Wave 0 |
| UI-01+02 | Suite stays green (imports, audits, artifacts) | regression | `python tests/test_dashboard.py` + `git status --porcelain results/ weather/` clean | ✅ exists |

### Sampling Rate
- **Per task commit:** `python tests/test_dashboard.py`
- **Per wave merge:** full suite + `git status --porcelain results/ weather/` (must show only `??` untracked, zero tracked modifications)
- **Phase gate:** Full suite green + screenshot eyeball (theme) + manual click-through of all 7 download buttons before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `dashboard/helpers.py` — `scoreboard_csv_bytes`, `verdict_text`, `figure_png_bytes` (+ page figure builders)
- [ ] `.streamlit/config.toml` — greenhouse `[theme]`
- [ ] `tests/test_dashboard.py` — extend `_stub_streamlit` with `download_button` entry in the same commit as first page use
- [ ] Headless export assertions (magic bytes `\x89PNG`, CSV header `== COLUMNS`, verdict substrings `ga_fuzzy`/`holdout`/`1.0/1.0/0.01`) — new test functions or inline asserts in helpers' `__main__` self-check

**Pass criteria:** (1) theme file parses as TOML and app boots with green chrome; (2) CSV bytes `==` frozen file bytes; (3) every PNG starts `\x89PNG`; (4) TXT contains winner `ga_fuzzy`, all four controllers' `iae_T/iae_H/energy`, seeds 7/21, weights 1.0/1.0/0.01; (5) `test_dashboard.py` all-PASS; (6) `results/`+`weather/` tracked-clean.

## Security Domain

Surface: theme sidecar (`.streamlit/config.toml`) + download byte payloads served to the browser. No auth/session/crypto in scope; no user uploads; no new dependencies.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — local academic dashboard, no users |
| V3 Session Management | no | N/A — no session state introduced this phase |
| V4 Access Control | no | N/A — frozen artifacts are public to the app |
| V5 Input Validation | yes | Downloads derive from frozen files + in-figure data only; no user-supplied paths; `file_name` values are hardcoded literals, never interpolated from widget input |
| V6 Cryptography | no | N/A — never hand-roll; none needed |

### Known Threat Patterns for Streamlit-download stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via download path | Tampering | No paths from UI — helpers read two hardcoded frozen paths (`results/comparison.csv`, `results/ga_optimized_params.json`); `data=` carries bytes, never a user path |
| MIME sniffing / content confusion | Spoofing | Explicit `mime=` on every button (`text/csv`, `text/plain`, `image/png`); no `mime=None` |
| Frozen-provenance overwrite | Tampering | In-memory `BytesIO` only; source audit bans `"w"` opens in pages; merge gate `git status results/ weather/` clean |
| Dependency supply chain | Tampering | Zero new installs — no new attack surface by construction |

## Sources

### Primary (HIGH confidence)
- Installed-env live probes (this session): `streamlit.__version__==1.56.0`, `hasattr(st,'download_button'/'tabs'/'metric')`, `download_button` full signature via `inspect`, matplotlib 3.10.8 Agg PNG probe (`\x89PNG` magic, 27 KB), pandas 3.0.1, python 3.14.6, `.streamlit/`+`helpers.py` absent
- Codebase reads: `dashboard/app.py`, `dashboard/pages/01-04` (structure, chart code, thin-wiring pattern), `tests/test_dashboard.py` (stub + all audit rules), `src/metrics.py:30-44` (locked weights, COLUMNS, weather pairs), `results/comparison.csv` (8-row frozen contract)
- v1.1 milestone research `.planning/research/SUMMARY.md` — zero-install constraint, helpers pattern, BytesIO plumbing, build order (built on, not re-researched)

### Secondary (MEDIUM confidence)
- Streamlit official docs (fetched this session): theming overview + `config.toml` reference — `[theme]` key set (`base`, `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`, …)
- Notebook `05_comparison.ipynb` cells 4–5 (via JSON probe): grouped-bar figure spec + relative-ordering verdict logic the TXT must mirror

### Tertiary (LOW confidence)
- None — no finding rests on a single unverified source.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — live introspection is ground truth; zero-install confirmed
- Architecture: HIGH — direct reads of all four pages + test suite + metrics contract
- Pitfalls: HIGH — audit rules quoted from the suite itself; PNG corruption pattern probe-executed

**Research date:** 2026-09-29
**Valid until:** 30 days (stable domain: long-stable Streamlit/matplotlib patterns, pinned env)
