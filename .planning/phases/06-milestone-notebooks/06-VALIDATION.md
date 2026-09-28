---
phase: "06"
slug: "milestone-notebooks"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-28"
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 06-RESEARCH.md ## Validation Architecture (2026-09-28).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert suite, pytest-compatible names, in-body imports, `__main__` runner (repo convention; no pytest/jupyter installed) |
| **Config file** | none — Wave 0 creates `tests/test_notebooks.py` (audit harness implementing the uniform-pattern checklist) |
| **Quick run command** | `python tests/test_notebooks.py` |
| **Full suite command** | All six test files standalone (plant, baselines, fuzzy, GA, metrics, notebooks) |
| **Estimated runtime** | ~60 seconds (headless exec of six notebooks' cells under Agg) |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_notebooks.py` + `git status --porcelain results/` (comparison.csv untouched)
- **After every plan wave:** Headless exec of all six notebooks' code cells under Agg
- **Before `/gsd-verify-work`:** Full suite green + 6/6 notebooks pass structural checks + 6/6 PNGs exist (each ≥50 KB) + 04 fixes closed
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | PROOF-01 | — | audit harness passes on sealed 01–03 | structural | `python tests/test_notebooks.py` (01–03 checks) | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | PROOF-01 | — | 04 cells have ids; savefig dpi=120; PNG regenerated ≥50 KB | structural+artifact | same file (04 checks + PNG check) | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | PROOF-01 | T-06-01 / — | 05 loads CSV (header == COLUMNS, 8 rows); verdict holds; PNG ≥50 KB | headless+artifact | same file (05 checks; extract-and-exec cells) | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | PROOF-01 | T-06-01 / — | 06 reads CSV+JSON+PNGs; verdict restates; MF panel present; PNG ≥50 KB | headless+artifact | same file (06 checks; extract-and-exec cells) | ❌ W0 | ⬜ pending |
| 06-01-05 | 01 | 1 | PROOF-01 | — | no `def`/`class` metric/controller math in 05/06 cells; no pandas import anywhere | grep audit | same file (no-duplication checks) | ❌ W0 | ⬜ pending |
| 06-01-06 | 01 | 1 | METR-02 guard | — | comparison.csv byte-identical before/after (05/06 never rewrite it) | regression | `git status --porcelain results/` clean | ✅ git | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Research audit (pre-verified):** 01/02/03 PASS all 5 checks, sealed; 04 has exactly 2 required fixes (missing cell ids → MissingIDFieldWarning; savefig dpi=100 → locked 120) + 1 opportunistic cleanup (duplicate `import os`).

---

## Wave 0 Requirements

- [ ] `tests/test_notebooks.py` — audit harness implementing the 10-point uniform-pattern checklist (§Validation Architecture) + headless cell exec + PNG checks
- [ ] `tests/conftest.py` — NOT needed (no pytest)
- [ ] Framework install — none required (nbformat/matplotlib/numpy present; pandas FORBIDDEN per D-02)

---

## Manual-Only Verifications

None — all phase behaviors have automated verification (structural JSON checks + headless exec; jupyter CLI absent by design).

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
