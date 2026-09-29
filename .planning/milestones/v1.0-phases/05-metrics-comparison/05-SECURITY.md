---
phase: "05"
slug: "metrics-comparison"
# status lifecycle: missing (no threat model) → verified (mitigations confirmed, threats_open: 0)
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-27"
---

# Phase 05 — Security Threat Verification

> Secure-phase audit (State B: no prior SECURITY.md; PLAN.md carries `<threat_model>` with 5 STRIDE rows).
> Short-circuit applied: threat register authored at plan time, ASVS level 1 → L1 grep-depth verification, no auditor spawned.

---

## Threat Register (from 05-PLAN.md `<threat_model>`)

| ID | STRIDE | Surface | Severity | Disposition | Verified Mitigation |
|----|--------|---------|----------|-------------|---------------------|
| T-05-01 | Tampering | compare() out_path write | medium | mitigate | Default `results/comparison.csv`; `makedirs` on dirname only (`src/metrics.py:192`); `open(out_path, "w")` with fixed path (`:193`); suite round-trip test pins the fixed path (green) |
| T-05-02 | Tampering | metric kernels NaN/inf input | medium | mitigate | Fail-fast asserts in every kernel: non-empty + finite histories, finite setpoints, positive dt (`:49-52`, `:81-85`); duty-dict key/range asserts + finite cost (`:111-113`, `:121`); suite NaN-injection check expects AssertionError (test_nan_failfast, green) |
| T-05-03 | Tampering | ga_optimized_params.json load | medium | mitigate | GA leg invokes `ga_fuzzy_step` + `load_optimized_mfs` schema-v2 validation only (Phase-4 T-04-01 verified); never pickle or eval (verified by grep — absent); corrupt JSON fails loud |
| T-05-04 | Tampering | supply chain (new dependency) | high | mitigate | Zero new dependencies — `src/metrics.py` imports csv/os/numpy + in-repo controllers only (`:8-28`); pandas explicitly rejected per D-02; BLOCK on high severity |
| T-05-SC | Tampering | npm/pip/cargo installs | high | mitigate | No install step in this phase; nothing to audit |

---

## Verification Method

- L1 grep-depth over `src/metrics.py` (assert/isfinite/import/pickle/eval/open/makedirs patterns) + suite evidence (`python tests/test_metrics.py` 9/9 green, incl. NaN fail-fast + CSV round-trip).
- No secrets, network, users, or external exec in phase scope — V2/V3/V4/V6 ASVS categories N/A per RESEARCH.md Security Domain.

---

## Accepted Risks Log

None — all 5 threats closed with implemented mitigations.

---

## Audit Trail

- Seed: 05-PLAN.md `<threat_model>` (plan-time, 2026-09-27)
- Verification: 2026-09-27 — all 5 threats closed, `threats_open: 0`
