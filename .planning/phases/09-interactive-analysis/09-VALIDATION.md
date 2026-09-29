---
phase: "09"
slug: "interactive-analysis"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-29"
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 09-RESEARCH.md ## Validation Architecture (2026-09-29).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-assert standalone suite (`python tests/test_dashboard.py`), stubbed Streamlit, Agg headless |
| **Config file** | none — Wave 0 extends `tests/test_dashboard.py` with 4 new tests (all helpers live in `dashboard/helpers.py`) |
| **Quick run command** | `python tests/test_dashboard.py` (~30 s incl. sim asserts) |
| **Full suite command** | All eight test files standalone + `git status --porcelain results/ weather/` clean |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python tests/test_dashboard.py` + git-status guard (tracked-clean)
- **After every plan wave:** Run full suite (all eight files)
- **Before `/gsd-verify-work`:** Full suite green + human interaction checkpoint (see Manual-Only)
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | UI-04 | T-09-01 / — | pair runner shape + delta arithmetic + rank line both sides | unit | `python tests/test_dashboard.py` (test_scenario_delta) | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | UI-04 | — | cold tick < ~6 s, warm recompute < 0.5 s | perf | timing asserts inside test_scenario_delta | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | UI-05 | T-09-02 / — | scratch deep-copies; FUZZY_MFS + mfs_opt bit-identical; widths frozen; centers ordered | unit | same file (test_scratch_purity) | ❌ W0 | ⬜ pending |
| 09-01-04 | 01 | 1 | UI-05 | — | overlay differs-on-drag (> 1e-3) + coincides-at-zero (allclose) | unit | same file (explorer curve asserts) | ❌ W0 | ⬜ pending |
| 09-01-05 | 01 | 1 | UI-05 | — | out-of-order drag clamped + warning, no exception | unit | same file (test_scratch_clamp) | ❌ W0 | ⬜ pending |
| 09-01-06 | 01 | 1 | UI-06 | T-09-03 / — | replay indexing 1/25/50 exact + readout format; no evolution imports | unit | same file (test_replay_slice) | ❌ W0 | ⬜ pending |
| 09-01-07 | 01 | 1 | UI-04/05/06 | — | source audits hold (no new def on 03, no banned tokens, no genetic_algorithm on 02/03) | static | same file (test_source_audits, extended) | ✅ | ⬜ pending |
| 09-01-08 | 01 | 1 | UI-04/05/06 | — | pages import under stub; results/+weather/ untouched | smoke | same file (existing guards) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Concrete pass criteria:** (1) suite exit 0; (2) default seeds (A=7, B=21) reproduce run_all_four values with GA < on/off AND < PID both sides; (3) zero-delta allclose + nonzero-drag deviation > 1e-3; (4) frozen baselines bit-identical pre/post drag.

---

## Wave 0 Requirements

- [ ] `tests/test_dashboard.py` — 4 new tests (scenario_delta, scratch_purity, scratch_clamp, replay_slice); ALL new `def`s in `dashboard/helpers.py`
- [ ] `tests/conftest.py` — NOT needed (no pytest)
- [ ] Framework install — none required (zero new installs); stub extension only if non-stub-safe widgets chosen (avoid)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scenario sliders re-run both sides; MF drags reshape live; replay scrubber steps generations | UI-04/05/06 | Needs browser interaction | `python -m streamlit run dashboard/app.py` → exercise both scenario sliders, drag MF centers, scrub generations (human_verify_mode: end-of-phase checkpoint) |

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
