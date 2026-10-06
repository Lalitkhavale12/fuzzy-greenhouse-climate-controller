---
phase: "10"
slug: "layout-polish-report-bundle"
# status lifecycle: missing (no threat model) → verified (mitigations confirmed, threats_open: 0)
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-29"
---

# Phase 10 — Security Threat Verification

> Secure-phase audit (State B: no prior SECURITY.md; two PLANs carry `<threat_model>` blocks totaling 9 STRIDE rows).
> Short-circuit applied: threat registers authored at plan time, ASVS level 1 → L1 grep-depth verification, no auditor spawned.

---

## Threat Register (from 10-01/02-PLAN.md `<threat_model>` blocks)

| ID | STRIDE | Surface | Severity | Disposition | Verified Mitigation |
|----|--------|---------|----------|-------------|---------------------|
| T-10-01 | Tampering | evidence_zip_bytes member names | low | mitigate | Fixed `ZIP_MEMBERS` flat-basename allowlist, 10 members, no directories or dot-dot segments (`dashboard/helpers.py:53-57`); test asserts exact namelist (green) |
| T-10-02 | Tampering | results/ and weather/ artifacts | medium | mitigate | In-memory BytesIO only; zero write-mode opens under results/ or weather/ (all opens are `rb` reads — verified by read); artifacts-untouched test + git-status clean gate (green) |
| T-10-03 | Spoofing | ZIP provenance (CSV/JSON/PNG members) | medium | mitigate | Raw `rb.read()` bytes for notebook PNGs + GA JSON (`:79-83`), never `json.dumps` re-serialization; headless asserts byte-equality against frozen files (green); KPI/verdict read the CSV rank column, never recomputed |
| T-10-04 | Denial of service | ZIP build memory | low | accept | Members total under ~2 MB; single on-demand build with no caching; rationale documented, no further action |
| T-10-05 | Spoofing | KPI cards on 01/02/03 | medium | mitigate | Values read from the frozen holdout rows via the rank column only; layout asserts check equality with the frozen ga_fuzzy row (green); never argsort/compare/all_metrics on the KPI path (verified by grep — absent from KPI code) |
| T-10-06 | Tampering | page source (new widgets) | low | mitigate | Source audits extended for tabs/expander placement with the ban list unchanged; 03 keeps zero new top-level defs (green) |
| T-10-07 | Denial of service | narrow-viewport usability | low | accept | Stacking discipline (figures full-width outside columns, KPI row max 4 narrow text cards) plus structural source-scan; no browser rendering available headless, reasoning-only verification locked by D-04 |
| T-10-SC | Tampering | installs (npm/pip/cargo) ×2 plans | high | mitigate | Zero new installs — stdlib zipfile/io only; no install step exists to attack |

---

## Verification Method

- L1 grep-depth over `dashboard/helpers.py` + `dashboard/pages/*.py` (ZIP_MEMBERS/writestr/rb.read/argsort/compare/KPI patterns) + suite evidence (`python tests/test_dashboard.py` 17/17 green, incl. evidence_zip + layout + artifacts-untouched checks).
- No secrets, network, users, or external exec in phase scope — V2/V3/V4/V6 ASVS categories N/A per RESEARCH.md Security Domain.

---

## Accepted Risks Log

- AR-01: T-10-04 accepted — ZIP build memory bounded (~2 MB, on-demand, uncached).
- AR-02: T-10-07 accepted — narrow-viewport proof is structural reasoning only (no browser available headless).

---

## Audit Trail

- Seed: 10-01/02-PLAN.md `<threat_model>` blocks (plan-time, 2026-09-29)
- Verification: 2026-09-29 — all 9 threats closed, `threats_open: 0`
