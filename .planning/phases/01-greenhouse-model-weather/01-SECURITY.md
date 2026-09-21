---
phase: "01"
slug: "greenhouse-model-weather"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-09-21"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CSV file -> load_weather_profile | Untrusted file content crosses into the simulation (malformed rows, out-of-range RH, non-monotonic time) | numeric weather rows (T, RH), read-only |
| actuators dict -> step | Caller-supplied actuator keys/values cross the API boundary (missing/unknown keys, out-of-range duties) | actuator duty floats |
| weather generator output -> simulation | Generated CSV feeds the model's outdoor disturbance path | deterministic internal output (no external input) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Tampering | load_weather_profile CSV parser | high | mitigate | Fail-fast validation on load: `np.loadtxt(skiprows=1)` numeric parse, `assert np.all(np.diff(t_min) > 0)` monotonic, span `[0,1440]`, RH `[0,100]` (greenhouse_model.py:95-99) | closed |
| T-01-02 | DoS | step() Euler numerics | medium | mitigate | Euler gate `assert (X_v + k_c)*dt < 1` (greenhouse_model.py:66); w clamped at wsat via condensation sink (:80); RH clamped [0,100] (relative_humidity :44); finite asserts on state (:82-83) | closed |
| T-01-03 | Spoofing | step() actuators argument | medium | mitigate | Exact-key-set `assert set(actuators) == {heater, fan_cooler, fogger, vent}` (:63) + duty clamp [0,1] (:65) + fail-fast raise on missing/unknown keys; covered by test_actuator_key_set | closed |
| T-01-04 | Tampering | generate_weather_profile | low | accept | Deterministic internal code (std-lib numpy only), no external input crosses this function; audit visibility via seedability test | closed — accepted |
| T-01-05 | DoS | numpy.interp time interpolation | low | accept | Covered by T-01-01 load-time validation — interp only receives validated monotonic minutes | closed — accepted |
| T-01-SC | Tampering | python package installs | high | mitigate | Package-legitimacy gate satisfied pre-plan: ZERO installs; numpy 2.4.3 + matplotlib 3.10.8 already installed per RESEARCH.md package audit; no checkpoint needed | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-04 | Weather generator is deterministic internal code with no external input surface; seedability test gives audit visibility | plan (disposition accepted) | 2026-09-20 |
| AR-02 | T-01-05 | Interp operates only on data already validated by T-01-01 at load time; residual risk negligible for a local simulation | plan (disposition accepted) | 2026-09-20 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-21 | 6 | 6 | 0 | gsd-secure-phase (orchestrator, L1 grep-depth) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-21 — threats_open: 0, no blocking threats remain. Fast-path: register authored at plan time, ASVS level 1 → L1 grep-depth sufficient per short-circuit rule.