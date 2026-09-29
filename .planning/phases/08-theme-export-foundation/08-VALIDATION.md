---
phase: "08"
slug: "theme-export-foundation"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-29"
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 08-RESEARCH.md ## Validation Architecture (2026-09-29).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert standalone suite (`python tests/test_dashboard.py`), pytest-style names, stubbed streamlit |
| **Config file** | none — Wave 0 creates `dashboard/helpers.py` + `.streamlit/config.toml`, extends `tests/test_dashboard.py` |
| **Quick run command** | `python tests/test_dashboard.py` |
| **Full suite command** | All eight test files standalone (plant, baselines, fuzzy, GA, metrics, notebooks, dashboard) |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_dashboard.py` + `git status --porcelain results/ weather/` (tracked-clean)
- **After every plan wave:** Run full suite
- **Before `/gsd-verify-work`:** Full suite green + theme screenshot eyeball + all download buttons click-verified
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | UI-01 | — | theme TOML parses; app boots green | manual-only | screenshot eyeball (`python -m streamlit run dashboard/app.py`) | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | UI-02 | T-08-01 / — | CSV bytes == frozen file bytes | unit | headless `scoreboard_csv_bytes()` assert | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | UI-02 | — | every PNG starts `\x89PNG` | unit | headless `figure_png_bytes()` magic assert | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 1 | UI-02 | — | TXT has winner+margins+terms+provenance | unit | headless `verdict_text()` substring asserts | ❌ W0 | ⬜ pending |
| 08-01-05 | 01 | 1 | UI-01/02 | T-08-02 / — | suite green, audits hold, artifacts untouched | regression | `python tests/test_dashboard.py` + git-status clean | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Pass criteria:** (1) theme parses + app boots green; (2) CSV bytes `==` frozen; (3) PNGs start `\x89PNG`; (4) TXT has `ga_fuzzy`, all four `iae_T/iae_H/energy`, seeds 7/21, weights 1.0/1.0/0.01; (5) dashboard suite all-PASS; (6) results/+weather/ tracked-clean.

---

## Wave 0 Requirements

- [ ] `dashboard/helpers.py` — `scoreboard_csv_bytes`, `verdict_text`, `figure_png_bytes` (+ page figure builders); ALL new `def`s live here
- [ ] `.streamlit/config.toml` — greenhouse `[theme]` (new dir at repo root)
- [ ] `tests/test_dashboard.py` — extend `_stub_streamlit` with `download_button`; new export assertions
- [ ] Framework install — none required (zero new installs)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Greenhouse theme loads; charts readable in light mode | UI-01 | Theme invisible to headless suite | `python -m streamlit run dashboard/app.py` → eyeball chrome + chart contrast (human_verify_mode: end-of-phase checkpoint) |
| All download buttons serve correct files | UI-02 | Needs browser clicks | Click each download button on all four pages; verify filenames + contents |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
