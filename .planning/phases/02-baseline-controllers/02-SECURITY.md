---
phase: "02"
slug: "baseline-controllers"
# status lifecycle: missing (no threat model) → verified (mitigations confirmed, threats_open: 0)
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-21"
---

# Phase 02 — Security Threat Verification

> Secure-phase audit (State B: no prior SECURITY.md; PLAN.md carries `<threat_model>`).
> Short-circuit applied: threat register authored at plan time, ASVS level 1 → L1 grep-depth verification, no auditor spawned.

---

## Threat Register (from 02-PLAN.md `<threat_model>`, lines 149-164)

| ID | STRIDE | Surface | Severity | Disposition | Verified Mitigation |
|----|--------|---------|----------|-------------|---------------------|
| T-02-01 | Tampering | onoff_step / pid_step entry | medium | mitigate | Finite-input asserts at controller entry: `src/onoff_controller.py:18-20` (`T_C`, `rh_pct`, `T_sp`, `RH_sp`, bands); `src/pid_controller.py:21-23` (+ `dt > 0`); outputs clipped every call (`pid_controller.py:33,37`); existing `step()` finite assert at `src/greenhouse_model.py:82` stays as backstop |
| T-02-02 | Tampering | controller state dicts | low | accept with control | Fresh-state-on-`None` convention (`onoff_controller.py:21`, `pid_controller.py:24`); bit-identical determinism proven by `test_controller_signatures` (suite green); rationale: local single-process harness, no cross-trust actor |
| T-02-SC | Tampering | installs (supply chain) | high | mitigate | Zero new dependencies this phase — both modules import only `numpy` (`onoff_controller.py:12`, `pid_controller.py:13`); matplotlib-Agg notebook-only, already accepted in Phase 1; no install step exists to attack |

---

## Verification Method

- L1 grep-depth over `src/onoff_controller.py` + `src/pid_controller.py` (assert/clip/import/None patterns) + suite evidence (`python tests/test_baseline_controllers.py` 7/7 green, incl. determinism + finite-run checks).
- No secrets, network, users, or external exec in phase scope — V2/V3/V4/V6 ASVS categories N/A per RESEARCH.md Security Domain.

---

## Accepted Risks Log

None beyond T-02-02 (accepted with control above — fresh-state convention + determinism test).

---

## Audit Trail

- Seed: 02-PLAN.md `<threat_model>` (plan-time, 2026-09-21)
- Verification: 2026-09-21 — all 3 threats closed, `threats_open: 0`
