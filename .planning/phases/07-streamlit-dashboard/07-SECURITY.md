---
phase: "07"
slug: "streamlit-dashboard"
# status lifecycle: missing (no threat model) → verified (mitigations confirmed, threats_open: 0)
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-28"
---

# Phase 07 — Security Threat Verification

> Secure-phase audit (State B: no prior SECURITY.md; PLAN.md carries `<threat_model>` with 5 STRIDE rows).
> Short-circuit applied: threat register authored at plan time, ASVS level 1 → L1 grep-depth verification, no auditor spawned.

---

## Threat Register (from 07-PLAN.md `<threat_model>`)

| ID | STRIDE | Surface | Severity | Disposition | Verified Mitigation |
|----|--------|---------|----------|-------------|---------------------|
| T-07-01 | Tampering | Controllers/Model-Sim seed input → open() | medium | mitigate | Seeds are ints from `st.slider(1, 50)` (`01_model_sim.py:60`, `02_controllers.py:70`); mapped to fixed frozen paths (7/21) or `tempfile.mkdtemp()` with int-formatted names (`01:32`, `02:41`); never interpolates raw widget strings into paths (verified by grep) |
| T-07-02 | Tampering | Results/Controllers vs results/comparison.csv | high | mitigate | Results reads via `csv.DictReader` (`04_results.py:33`) with header == COLUMNS import (`:22`); Controllers page never imports/calls `metrics.compare()` (verified by grep — absent); per-commit `git status --porcelain results/ weather/` guard in suite blocks merges on overwrite (test_artifacts_untouched, green) |
| T-07-03 | Tampering | GA Explorer shared MF arrays | low | mitigate | All MF display goes through `load_optimized_mfs` (`03_ga_explorer.py:24`) which returns defensive deep copies (Phase-4 IN-04 fix); page code never mutates returned arrays |
| T-07-04 | Information disclosure | streamlit run launch | low | mitigate | Localhost default; no `--server.address 0.0.0.0`, no CORS disable, no absolute paths (`/home/`, `/Users/`, `C:/`) in any dashboard artifact (verified by grep — absent) |
| T-07-SC | Tampering | interpreter package set | high | mitigate | Zero new installs — imports restricted to stdlib + numpy/matplotlib/streamlit + src.* on all pages (verified); conda `python` 3.14.6 is the pinned interpreter; suite scans hold |

---

## Verification Method

- L1 grep-depth over `dashboard/app.py` + `dashboard/pages/*.py` (slider/mkdtemp/DictReader/compare/address/install/absolute-path patterns) + suite evidence (`python tests/test_dashboard.py` 7/7 green, incl. artifacts-untouched + source audits).
- No secrets, network, users, or external exec in phase scope — V2/V3/V4/V6 ASVS categories N/A per RESEARCH.md Security Domain.

---

## Accepted Risks Log

None — all 5 threats closed with implemented mitigations. (Streamlit binds localhost by default; no config hardens or weakens that in this repo.)

---

## Audit Trail

- Seed: 07-PLAN.md `<threat_model>` (plan-time, 2026-09-28)
- Verification: 2026-09-28 — all 5 threats closed, `threats_open: 0`
