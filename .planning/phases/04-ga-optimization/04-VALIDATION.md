---
phase: "04"
slug: "ga-optimization"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-22"
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 04-RESEARCH.md ## Validation Architecture (2026-09-22).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert standalone scripts, pytest-compatible naming; run standalone, NOT via pytest |
| **Config file** | none — Wave 0 creates `tests/test_genetic_algorithm.py` with `__main__` runner (Phase-1/2/3 convention) |
| **Quick run command** | `python tests/test_genetic_algorithm.py` (< 30 s via tiny-budget smoke) |
| **Full suite command** | `python tests/test_greenhouse_model.py; python tests/test_baseline_controllers.py; python tests/test_fuzzy_controller.py; python tests/test_genetic_algorithm.py` |
| **Estimated runtime** | ~30 seconds (suite); full 50×50 evolution ~25 min wall (script, NOT in-suite) |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_genetic_algorithm.py`
- **After every plan wave:** Run full suite command above (no plant/baseline/fuzzy regression)
- **Before `/gsd-verify-work`:** Full suite green + `notebooks/04_ga_optimization.ipynb` nb-ok + PNG exists
- **Max feedback latency:** 60 seconds (suite); evolution script runs once (~25 min) outside the suite

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | GA-01 | T-04-01 / — | decode repair invariants (sorted, widths>0, finite) | unit | `python tests/test_genetic_algorithm.py` (test_encode_decode_roundtrip, test_decode_repair_invariants) | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | GA-02 | T-04-02 / — | fitness(hand) finite ≈ 641.5; bad chromosome → inf, never raises | unit | same file (test_fitness_matches_hand_cost, test_fitness_never_raises) | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | GA-03 | — | tiny GA (4×2 seeded) monotonic + < 30 s | smoke | same file (test_tiny_ga_monotonic) | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | GA-04 | T-04-03 / — | run_ga smoke writes schema-valid JSON | unit | same file (test_json_schema) | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 2 | GA-05 | T-04-03 / — | ga_fuzzy_step == fuzzy_step(mfs) bit-identical; holdout GA cost < on/off cost on shared fresh weather | integration | same file + notebook structural check | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 1 | GA-01/04 | T-04-04 / — | hand FUZZY_MFS bit-identical before/after GA smoke (no global mutation) | unit | same file (test_hand_mfs_untouched) | ❌ W0 | ⬜ pending |
| 04-01-07 | 01 | 2 | GA-05 | — | notebook structural nb-ok + PNG exists | manual-only | nb-ok one-liner + size check | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Critical note (research-measured):** fitness is ~99% humidity (train costs: on/off ≈502.7, hand-fuzzy ≈641.5, PID ≈643.3 — hand fuzzy LOSES to on/off). GA-05 pass criterion is RELATIVE ordering on shared holdout weather (GA cost < on/off cost), never an absolute number.

---

## Wave 0 Requirements

- [ ] `tests/test_genetic_algorithm.py` — sole test file; covers GA-01..05 + regression guards with `__main__` runner + in-body imports
- [ ] `results/` directory bootstrap (`mkdir -p` in `run_ga`; do not rely on committing empty dirs)
- [ ] `tests/conftest.py` — NOT needed (no pytest)
- [ ] Framework install — none required (zero new dependencies; no DEAP/pymoo — hand-rolled GA is the deliverable)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notebook proof (convergence + holdout comparison + MF before/after) executes headless and writes PNG | GA-05 | Notebook artifact, not assertable in-suite | Structural nb-ok one-liner (imports + Agg + PNG ref) + confirm `notebooks/04_ga_optimization.png` > 10 KB (jupyter CLI absent; evolution runs as script, notebook plots artifacts only) |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s (suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
