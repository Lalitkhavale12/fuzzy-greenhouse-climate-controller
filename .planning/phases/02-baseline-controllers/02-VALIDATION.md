---
phase: "02"
slug: "baseline-controllers"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-21"
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 02-RESEARCH.md ## Validation Architecture (2026-09-21).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert module, pytest-compatible naming; run standalone, NOT via pytest |
| **Config file** | none — Wave 0 creates `tests/test_baseline_controllers.py` with `__main__` runner (copy Phase-1 runner incl. `sys.path` prepend) |
| **Quick run command** | `python tests/test_baseline_controllers.py` (< 5 s) |
| **Full suite command** | `python tests/test_baseline_controllers.py` (single file; same command) |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_baseline_controllers.py`
- **After every plan wave:** Run full suite + `python tests/test_greenhouse_model.py` (no plant regression)
- **Before `/gsd-verify-work`:** Both suites green + notebook executes headless + PNG exists
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | BASE-01 | T-02-01 / — | duties clipped [0,1]; unknown keys never emitted | unit | `python tests/test_baseline_controllers.py` (test_onoff_hysteresis) | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | BASE-01 | — | heater/fan mutual exclusion | unit | same file (test_onoff_mutual_exclusion) | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | BASE-02 | T-02-01 / — | finite inputs asserted; NaN cannot propagate | unit | same file (test_pid_signs) | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | BASE-02 | — | anti-windup guard present, guarded IAE_T strictly lower | unit | same file (test_pid_antiwindup_improves) | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | BASE-02 | — | I term live (P-only ablation shows large droop) | unit | same file (test_pid_integral_required) | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | BASE-03 | T-02-02 / — | setpoints as fn args; exact key set; fresh-state determinism | unit | same file (test_controller_signatures) | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 2 | BASE-01/02/03 | — | 24h closed-loop runs assert/NaN-free; T-IAE < 60 °C·h; RH in [0,100] | integration | same file (test_closed_loop_24h) | ❌ W0 | ⬜ pending |
| 02-01-08 | 01 | 2 | BASE-01/02 | — | notebook executes headless, PNG written | manual-only | `jupyter nbconvert --execute notebooks/02_baselines.ipynb` + PNG exists | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_baseline_controllers.py` — sole test file; covers BASE-01..03 (8 checks above) with `__main__` runner + `sys.path` prepend copied from Phase 1
- [ ] `tests/conftest.py` — NOT needed (no pytest; shared `_run_closed_loop` helper lives in the test module)
- [ ] Framework install — none required (zero new dependencies)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notebook proof executes headless and writes PNG | BASE-01/02 | Notebook artifact, not assertable in-suite | `jupyter nbconvert --to notebook --execute notebooks/02_baselines.ipynb --output /tmp/02_exec.ipynb`, then confirm `notebooks/02_baselines.png` exists |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
