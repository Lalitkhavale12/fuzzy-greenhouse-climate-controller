---
phase: "01"
slug: "greenhouse-model-weather"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-20"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain-assert module, pytest-compatible naming (`def test_*()`) — run standalone; pytest NOT installed |
| **Config file** | none — Wave 0 creates `tests/test_greenhouse_model.py` with `if __name__ == "__main__":` runner |
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
| 01-01-01 | 01 | 1 | MODEL-01 | — | N/A (local numerics) | unit | `python tests/test_greenhouse_model.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Task IDs finalized when 01-PLAN.md lands; rows below mirror the RESEARCH.md requirement→test map.*

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODEL-01 | Coupled ODE: coupling directions hold (heater↑T/w const-RH↓; fan↓T; fogger↓T↑w; vent→ambient both) | unit | `python tests/test_greenhouse_model.py` | ❌ Wave 0 |
| MODEL-01 | Bounded state, positivity, no NaN in 24h run | unit | `python tests/test_greenhouse_model.py` | ❌ Wave 0 |
| MODEL-01 | Plausible steady-state: with fixed weather, state settles (\|dT\|<ε, \|dw\|<ε) | unit | `python tests/test_greenhouse_model.py` | ❌ Wave 0 |
| MODEL-02 | Duty linearity: effect at 50% = half of effect at 100% (D-06) | unit | `python tests/test_greenhouse_model.py` | ❌ Wave 0 |
| MODEL-03 | CSV load+interp: known sine CSV reproduces T_out at midpoints within tol | unit | `python tests/test_greenhouse_model.py` | ❌ Wave 0 |
| MODEL-03 | Generator is seedable: two runs, same seed → identical rows | unit | `python tests/test_greenhouse_model.py` | ❌ Wave 0 |
| MODEL-04 | API contract: step(dt, actuators, weather) → (T, w) tuple; stateless (2 calls, no state leak) | unit | `python tests/test_greenhouse_model.py` | ❌ Wave 0 |

---

## Wave 0 Requirements

- [ ] `tests/test_greenhouse_model.py` — the sole test file; covers MODEL-01..04 (7 checks). Create with the `__main__` runner so `python` alone executes it.
- [ ] `tests/conftest.py` — NOT needed (pytest not installed; no shared fixtures beyond the params dict inside the test module).
- [ ] Framework install — none required (zero new deps).

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending