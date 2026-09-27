---
phase: "05"
slug: "metrics-comparison"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-27"
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 05-RESEARCH.md ## Validation Architecture (2026-09-27).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert suite, pytest-compatible names, in-body imports, `__main__` runner (repo convention) |
| **Config file** | none — Wave 0 creates `tests/test_metrics.py` (no pytest/jupyter installed) |
| **Quick run command** | `python tests/test_metrics.py` |
| **Full suite command** | `python tests/test_metrics.py` + prior suites (plant, baselines, fuzzy, GA) for no-regression |
| **Estimated runtime** | ~60 seconds (8 full 24h runs in compare tests) |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_metrics.py`
- **After every plan wave:** Run full suite (all five test files, each standalone-runnable)
- **Before `/gsd-verify-work`:** Full suite green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | METR-01 | T-05-01 / — | kernels raise AssertionError on non-finite input | unit | `python tests/test_metrics.py` (test_metric_kernels_synthetic) | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | METR-01 | — | settling joint-band last-exit + inf never-settled + settled-at-0 | unit | same file (test_settling_edges) | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | METR-01 | — | energy bit-identical (==) to closed_loop_breakdown | unit | same file (test_energy_identity) | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | METR-01 | — | overshoot absolute peak beyond setpoint per channel | unit | same file (test_overshoot) | ❌ W0 | ⬜ pending |
| 05-01-05 | 01 | 2 | METR-02 | — | compare() 8 rows, frozen columns, finite (except inf settling) | integration | same file (test_compare_shape) | ❌ W0 | ⬜ pending |
| 05-01-06 | 01 | 2 | METR-02 | — | holdout GA < on/off AND < PID (strict ordering, no exact values) | integration | same file (test_holdout_ordering) | ❌ W0 | ⬜ pending |
| 05-01-07 | 01 | 2 | METR-02 | T-05-02 / — | CSV header == COLUMNS, round-trips to returned rows | integration | same file (test_csv_roundtrip) | ❌ W0 | ⬜ pending |
| 05-01-08 | 01 | 2 | METR-02 | — | train vs holdout blocks differ (wrong-file guard) | integration | same file (test_weathers_distinct) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Reference numbers (04-SUMMARY, ordering only — never assert exact):** holdout GA ≈ 114.28 < on/off ≈ 513.75 < PID ≈ 645.26. Energy identity uses exact `==` (same accumulation order ⇒ bit-identical).

---

## Wave 0 Requirements

- [ ] `tests/test_metrics.py` — sole test file; covers METR-01/02 per map above with `__main__` runner + in-body imports
- [ ] `results/comparison.csv` — generated artifact, asserted by round-trip test (not hand-written)
- [ ] `tests/conftest.py` — NOT needed (no pytest)
- [ ] Framework install — none required (zero new dependencies; pandas explicitly rejected)

---

## Manual-Only Verifications

None — all phase behaviors have automated verification. (No Phase-5 notebook per D-05; Phase 6 owns comparison plots.)

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
