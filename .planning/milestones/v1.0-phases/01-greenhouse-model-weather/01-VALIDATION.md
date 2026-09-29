---
phase: "01"
slug: "greenhouse-model-weather"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-20"
updated: "2026-09-21"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain-assert module, pytest-compatible naming (`def test_*()`) — run standalone; pytest NOT installed |
| **Config file** | none — `tests/test_greenhouse_model.py` carries its own `if __name__ == "__main__":` runner |
| **Quick run command** | `python tests/test_greenhouse_model.py` (runs all D-04 checks, < 5s) |
| **Full suite command** | `python tests/test_greenhouse_model.py` (single test file; same command) |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_greenhouse_model.py`
- **After every plan wave:** Run `python tests/test_greenhouse_model.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | MODEL-01/02/03/04 | — | N/A (local numerics) | unit | `python tests/test_greenhouse_model.py` | ✅ | ✅ green |

| Req ID | Behavior | Test Type | Automated Command | Status |
|--------|----------|-----------|-------------------|--------|
| MODEL-01 | Coupled ODE: coupling directions hold (heater↑T/w const-RH↓; fan↓T + condensation↓w; fogger↓T↑w; vent→ambient both) | unit | `test_coupling_directions` | ✅ green |
| MODEL-01 | Bounded state, positivity, no NaN in 24h run (probe bands T[16.5,36.0], w[10.9,38.5], RH[43,100]) | unit | `test_bounded_finite_positive_24h` | ✅ green |
| MODEL-02 | Duty linearity: effect at 50% = half of effect at 100% (D-06) | unit | `test_duty_linearity` | ✅ green |
| MODEL-03 | CSV load+interp: known sine CSV reproduces T_out at midpoints within tol; RH→w mapping | unit | `test_csv_load_and_interp` | ✅ green |
| MODEL-03 | Generator is seedable: two runs, same seed → byte-identical rows | unit | `test_generator_seedability` | ✅ green |
| MODEL-04 | API contract: pure stateless step() → (T, w, rh) 3-tuple; 2 calls identical; rh∈[0,100] | unit | `test_step_api_contract` | ✅ green |
| MODEL-04 | Missing or unknown actuator keys fail fast; key order-independence (PLAN line 28) | unit | `test_actuator_key_set` | ✅ green |

*Note: the plan-phase seed listed a "steady-state settle" row for MODEL-01; the final PLAN.md verifies MODEL-01 via bounded/finite/coupling asserts only (line 42), so that row is superseded and not carried here.*

---

## Wave 0 Requirements

- [x] `tests/test_greenhouse_model.py` — the sole test file; covers MODEL-01..04 (7 checks) with the `__main__` runner so `python` alone executes it.
- [x] `tests/conftest.py` — NOT needed (pytest not installed; no shared fixtures beyond the params dict inside the test module).
- [x] Framework install — none required (zero new deps).

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated by /gsd-validate-phase on 2026-09-21 (7/7 tests green; no gaps found)