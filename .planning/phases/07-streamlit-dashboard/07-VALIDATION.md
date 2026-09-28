---
phase: "07"
slug: "streamlit-dashboard"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-28"
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 07-RESEARCH.md ## Validation Architecture (2026-09-28).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert suite, pytest-compatible names, in-body imports, `__main__` runner (repo convention; no pytest; conda `python` interpreter) |
| **Config file** | none — Wave 0 creates `tests/test_dashboard.py` (import smoke with stubbed `streamlit` + headless compute asserts) |
| **Quick run command** | `python tests/test_dashboard.py` |
| **Full suite command** | All seven test files standalone (plant, baselines, fuzzy, GA, metrics, notebooks, dashboard) |
| **Estimated runtime** | ~60 seconds (controllers helper ~1.37 s measured) |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_dashboard.py`
- **After every plan wave:** Run full suite (all seven test files)
- **Before `/gsd-verify-work`:** Full suite green + human screenshot checkpoint (see Manual-Only)
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | PROOF-02 | — | 4 pages present, numbered order, app.py landing-only | structural | `python tests/test_dashboard.py` (test_page_set) | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | PROOF-02 | — | every page imports under stubbed streamlit (no browser) | unit | same file (test_pages_import) | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | PROOF-02 | T-07-01 / — | run_all_four: shared weather, GA < on/off AND < PID on seed-21, wall < 30 s | unit | same file (test_controllers_helper) | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | PROOF-02 | — | results helper: 8 rows, header == COLUMNS, rank follows CSV | unit | same file (test_results_helper) | ❌ W0 | ⬜ pending |
| 07-01-05 | 01 | 1 | PROOF-02 | — | explorer helper: schema v2, 6 MF groups len-5, history.best len 50 | unit | same file (test_explorer_helper) | ❌ W0 | ⬜ pending |
| 07-01-06 | 01 | 1 | PROOF-02 | T-07-02 / — | no writes to results/ or weather/ during helper runs | unit | same file (test_artifacts_untouched) | ❌ W0 | ⬜ pending |
| 07-01-07 | 01 | 1 | PROOF-02 | — | static audits: no Agg/show/savefig under dashboard/, no absolute paths, no pandas/evolution imports on Results page | grep audit | same file (static checks) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `dashboard/app.py` + `dashboard/pages/` (4 pages) — the deliverable; import-smoke needs files to exist
- [ ] `tests/test_dashboard.py` — all PROOF-02a–g checks per map above
- [ ] `tests/conftest.py` — NOT needed (no pytest)
- [ ] Framework install — none required (Streamlit 1.56.0 already on the project interpreter; zero new installs)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App renders all four pages; sliders re-run and charts update live | PROOF-02 | Needs a browser — not automatable headless | `python -m streamlit run dashboard/app.py`, screenshot-review all four pages + drag setpoint/seed sliders (human_verify_mode: end-of-phase checkpoint) |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
