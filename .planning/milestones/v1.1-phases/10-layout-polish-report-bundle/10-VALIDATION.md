---
phase: "10"
slug: "layout-polish-report-bundle"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-29"
updated: "2026-09-29"
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 10-RESEARCH.md ## Validation Architecture (2026-09-29).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert standalone suite (`python tests/test_dashboard.py`), stubbed Streamlit, Agg headless |
| **Config file** | none — Wave 0 extends the stub (`tabs` list + `__enter__/__exit__`) and adds `test_layout_elements` + `test_evidence_zip` |
| **Quick run command** | `python tests/test_dashboard.py` |
| **Full suite command** | All eight test files standalone + `git status --porcelain results/ weather/` clean |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_dashboard.py` + git-status guard (tracked-clean)
- **After every plan wave:** Run full suite (all eight files)
- **Before `/gsd-verify-work`:** Full suite green + human layout/ZIP checkpoint (see Manual-Only)
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | UI-03 | — | KPI row all 4 pages; values equal frozen holdout row | source-scan + import | `python tests/test_dashboard.py` (test_layout_elements) | ✅ | ✅ green |
| 10-01-02 | 01 | 1 | UI-03 | — | tabs in 02/04 only; pages import under extended stub | source-scan + import | same suite (tabs checks) | ✅ | ✅ green |
| 10-01-03 | 01 | 1 | UI-03 | — | expander per page; ban list unchanged (no savefig/show/Agg) | static | same suite (test_source_audits, extended) | ✅ | ⬜ pending |
| 10-01-04 | 01 | 1 | UI-03 | — | narrow stacking (no pyplot in columns; no columns(3+) on figures) | structural | same suite (stacking checks) | ✅ | ✅ green |
| 10-01-05 | 01 | 1 | UI-07 | T-10-01 / — | ZIP PK magic + exact 10-member namelist + CSV/JSON == frozen + PNG magic | unit | same suite (test_evidence_zip) | ✅ | ✅ green |
| 10-01-06 | 01 | 1 | UI-07 | — | ZIP button wired (filename + application/zip on Results) | source-scan | same suite (wiring checks) | ✅ | ✅ green |
| 10-01-07 | 01 | 1 | UI-03/07 | — | full suite green + artifacts untouched | regression | all eight suites + git-status clean | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Pass criteria:** suite prints `all checks passed`; ZIP `[:2]==b"PK"`, exact 10-member namelist, CSV/JSON byte-identical, PNG magic; all pages import under stub; results/+weather/ git-clean.

---

## Wave 0 Requirements

- [ ] Extend `_stub_streamlit`: `tabs` → list-of-`_Stub` (mirror columns handler); `_Stub.__enter__/__exit__` → self (same commit as tabbed pages)
- [ ] New `test_layout_elements` + `test_evidence_zip` in `tests/test_dashboard.py`
- [ ] Extend `test_source_audits` allow/ban lists for tabs/expander/ZIP
- [ ] Framework install — none required (zero new installs)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| KPI cards/tabs/expanders render readably; narrow viewport stacks cleanly; ZIP downloads and opens | UI-03/UI-07 | Needs browser + eyeballs | `python -m streamlit run dashboard/app.py` → review all four pages + narrow window + click ZIP (human_verify_mode: end-of-phase checkpoint) |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-09-29 — 7/7 rows green + dashboard suite 17/17 (validate-phase audit; layout/ZIP interaction remains human-side)
