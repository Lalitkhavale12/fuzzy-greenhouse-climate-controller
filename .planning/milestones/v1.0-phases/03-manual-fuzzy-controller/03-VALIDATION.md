---
phase: "03"
slug: "manual-fuzzy-controller"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-21"
updated: "2026-09-21"
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 03-RESEARCH.md ## Validation Architecture (2026-09-21).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert module, pytest-compatible naming; run standalone, NOT via pytest |
| **Config file** | none — Wave 0 creates `tests/test_fuzzy_controller.py` with `__main__` runner (copy Phase-2 runner incl. `sys.path` prepend + in-body imports) |
| **Quick run command** | `python tests/test_fuzzy_controller.py` (< 10 s) |
| **Full suite command** | `python tests/test_fuzzy_controller.py` (single file; same command) |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_fuzzy_controller.py`
- **After every plan wave:** Run full suite + `python tests/test_baseline_controllers.py` + `python tests/test_greenhouse_model.py` (no plant/baseline regression)
- **Before `/gsd-verify-work`:** All three suites green + nb-ok prints `nb-ok` + `notebooks/03_fuzzy.png` > 10 KB
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | FUZZ-01 | T-03-01 / — | finite inputs asserted; NaN raises | unit | `python tests/test_fuzzy_controller.py` (test_fuzzy_signs) | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | FUZZ-01 | — | error-rate path live (ramp vs flat differ) | unit | same file (test_error_rate_live) | ✅ | ✅ green |
| 03-01-03 | 01 | 1 | FUZZ-02 | — | tri shape + FUZZY_MFS keys + 50% overlap | unit | same file (test_membership_functions) | ✅ | ✅ green |
| 03-01-04 | 01 | 1 | FUZZ-03 | — | 5x5 cells in 0..4; RULES[2,2]==2; monotone column/row | unit | same file (test_rule_table) | ✅ | ✅ green |
| 03-01-05 | 01 | 1 | FUZZ-04 | T-03-02 / — | split-range exclusion; exact 4-key dict; vent==fan | unit+integration | same file (test_output_mapping) | ✅ | ✅ green |
| 03-01-06 | 01 | 1 | FUZZ-05 | — | centroid signs/magnitudes; determinism | unit | same file (test_centroid_defuzz) | ✅ | ✅ green |
| 03-01-07 | 01 | 1 | FUZZ-02/05 | — | accumulator freeze beats never-freeze on IAE | unit | same file (test_accumulator_antiwindup) | ✅ | ✅ green |
| 03-01-08 | 01 | 2 | FUZZ-06 | T-03-01/02 / — | 24h finite/bounded; T-IAE < 60; RH in [0,100]; < 12 crossings; setpoints live; determinism; NaN raises | integration | same file (test_closed_loop_24h) | ✅ | ✅ green |
| 03-01-09 | 01 | 2 | FUZZ-06 | — | notebook structural nb-ok + PNG > 10 KB | manual-only | nb-ok one-liner + size check | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_fuzzy_controller.py` — sole test file; covers FUZZ-01..06 (9 checks above) with `__main__` runner + `sys.path` prepend + in-body imports copied from Phase 2
- [ ] `tests/conftest.py` — NOT needed (no pytest; shared `_run_closed_loop` helper lives in the test module)
- [ ] Framework install — none required (zero new dependencies)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notebook proof executes headless and writes PNG | FUZZ-06 | Notebook artifact, not assertable in-suite | Structural nb-ok one-liner (imports + Agg + PNG ref) + confirm `notebooks/03_fuzzy.png` > 10 KB (jupyter CLI absent; cells executed via python-Agg) |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-09-21 — 9/9 rows green, no gaps (validate-phase audit)
