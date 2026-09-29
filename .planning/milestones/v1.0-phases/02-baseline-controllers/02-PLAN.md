---
phase: 02-baseline-controllers
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/onoff_controller.py
  - src/pid_controller.py
  - tests/test_baseline_controllers.py
  - notebooks/02_baselines.ipynb
  - notebooks/02_baselines.png
autonomous: true
requirements: [BASE-01, BASE-02, BASE-03]

estimate:
  tokens: 36000
  raw_tokens: 24000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "On/off controller drives heater, fan_cooler+vent, and fogger fully on/off with hysteresis around the 25 C / 70 %RH setpoints, holding prior latch state when error sits exactly on a band edge, with fewer than 350 heater switches per 24 h"
    - "PID controller returns continuous duties in [0, 1] that track the setpoints, with heater and fan_cooler never simultaneously positive (split-range by sign)"
    - "Both controllers accept current state plus setpoints as function arguments and return the exact 4-key actuator dict {heater, fan_cooler, fogger, vent}, pluggable directly into step()"
    - "A 24 h dt=60 s closed-loop run per controller on the seed-7 weather stays finite with T-IAE below 60 C-h and RH inside [0, 100] throughout"
    - "Two closed-loop runs from fresh state are bit-identical, and output dict key insertion order is always heater, fan_cooler, fogger, vent"
    - "notebooks/02_baselines.ipynb reproduces both 24 h traces by importing from src/ only and writes notebooks/02_baselines.png"
  artifacts:
    - src/onoff_controller.py
    - src/pid_controller.py
    - tests/test_baseline_controllers.py
    - notebooks/02_baselines.ipynb
    - notebooks/02_baselines.png
  key_links:
    - "controller duty dict -> step() actuator-key and [0,1] asserts in src/greenhouse_model.py"
    - "setpoints passed as fn args (25.0/70.0), never baked into modules"
    - "caller-owned controller state dicts, fresh on None, separate per run"
    - "RH read via shared relative_humidity import, never re-derived"
  prohibitions:
    - "controllers must never emit unknown actuator keys"
    - "must never add dependencies beyond numpy and the standard library"
    - "notebook must not duplicate src/ logic"
---

<objective>
Deliver the two classical baselines the GA fuzzy must beat (per D-01..D-06): a hysteresis on/off controller and a dual-loop PID controller, both proven tracking 25 C / 70 %RH on the Phase-1 plant in a 24 h closed loop, with a proof notebook feeding the Phase-6 trail.

**As a** simulation researcher, **I want to** run honest on/off and PID baselines against the greenhouse plant, **so that** the later fuzzy/GA controller has beatable benchmarks scored on the same duty-dict contract.

Purpose: Baselines are the comparison floor for the project core value; they must be honest (hysteresis per D-02, hand-tuned gains, no deliberate handicapping) and directly comparable (same loop split per D-01/D-05).
Output: Two src/ modules, one plain-assert suite, one proof notebook plus PNG.
</objective>

<execution_context>
@C:/Users/Lalit/.config/opencode/gsd-core/workflows/execute-plan.md
@C:/Users/Lalit/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/02-baseline-controllers/02-CONTEXT.md
@.planning/phases/02-baseline-controllers/02-RESEARCH.md
@.planning/phases/02-baseline-controllers/02-PATTERNS.md
@src/greenhouse_model.py
</context>

<tasks>

<task type="tracer">
  <name>Tracer: both controllers end-to-end through step() on seed-7 weather</name>
  <files>src/onoff_controller.py, src/pid_controller.py, tests/test_baseline_controllers.py</files>
  <read_first>
    src/greenhouse_model.py (the step() actuator-key and [0,1] asserts plus the finite backstop the loop must satisfy);
    02-CONTEXT.md D-01/D-02/D-03/D-04/D-05 (loop split, hysteresis-not-threshold, independent loops, setpoints-as-args, dual-loop PID);
    02-RESEARCH.md Patterns 1-3 (probe-verified band_T=0.5/band_RH=3.0 with -0.2 C / -1.0 %RH asymmetric release, GAINS Kp_T=0.3/Ki_T=0.03/Kd_T=0/Kp_H=0.03/Ki_H=0.004/Kd_H=0, closed-loop harness shape);
    02-PATTERNS.md src/onoff_controller.py and src/pid_controller.py sections (module shape, None-fresh-state rule, np.clip discipline)
  </read_first>
  <acceptance_criteria>
    Behavior: onoff_step(20.0, 70.0, 25.0, 70.0, None) returns heater 1.0 with fan_cooler 0.0; pid_step(20.0, 70.0, 25.0, 70.0, None) returns heater greater than 0 with fan_cooler 0.0; both return exactly the keys heater, fan_cooler, fogger, vent with every duty inside [0, 1].
    Boundary (BASE-01 edge, resolved explicit): with heat latched on, onoff_step(24.5, 70.0, 25.0, 70.0, st) keeps heater 1.0 (inside band holds), and equality at the edge (error exactly 0.5) holds prior state rather than toggling.
    Test-command: python tests/test_baseline_controllers.py prints PASS test_closed_loop_24h and all checks passed.
    CLI: python tests/test_greenhouse_model.py still prints all checks passed (no plant regression).
    Source: src/onoff_controller.py defines onoff_step, src/pid_controller.py defines pid_step and GAINS, both assert np.isfinite on T_C/rh_pct/setpoints at entry.
  </acceptance_criteria>
  <action>Create src/onoff_controller.py with onoff_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, band_T=0.5, band_RH=3.0) per D-02/D-04: latch dict with heat/cool/fog bools, fresh dict on None (never a mutable default), on at wide error (eT greater than band_T, eH greater than band_RH), off at narrow asymmetric release (eT below -0.2, eH below -1.0), strict inequalities so equality holds prior state, vent mirrors the cooling bit per D-01, outputs as 0.0/1.0 literals only, no cross-compensation per D-03. Create src/pid_controller.py with GAINS dict Kp_T 0.3, Ki_T 0.03, Kd_T 0.0, Kp_H 0.03, Ki_H 0.004, Kd_H 0.0 and pid_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, gains=GAINS) per D-05: caller-owned state with iT/pT/iH/pH keys, dual positional loops, T output clipped to [-1, 1] then split by sign (positive to heater, negative magnitude to fan_cooler and vent, never both), RH output clipped to [0, 1] to fogger, conditional-integration freeze when saturated pushing further, Kd defaulting to 0. Both modules import numpy only, validate inputs with np.isfinite asserts at entry, and emit exactly the four actuator keys. Then create tests/test_baseline_controllers.py copying the Phase-1 runner and header conventions (in-body imports, sys.path prepend, __main__ PASS/FAIL runner) with the _run_closed_loop helper (init T 20.0 and w at 65 percent of wsat, per-minute interp of weather_profile.csv, daytime_solar, controller then step then append) and a single test_closed_loop_24h that runs both controllers 1440 steps, asserting finite traces, RH within [0,100], T-IAE below 60 C-h, and mutual exclusion of heater versus fan_cooler. Using the probe starting gains verbatim per the locked agent-discretion resolution (research already ran the probes; no re-tuning in this task).</action>
  <reversibility rating="costly">Actuator mapping (T-loop drives heater/fan/vent, RH-loop drives fogger only) shapes every downstream GA-fitness and comparison trace per D-01/D-05.</reversibility>
  <verify>
    <automated>python tests/test_baseline_controllers.py</automated>
    <fails_when>nonzero exit code, any line starting with FAIL, or output missing the line all checks passed</fails_when>
  </verify>
  <done>Both controllers drive step() for a full simulated day without assert or NaN, T-IAE is finite and below 60 C-h for each, and the suite is green.</done>
</task>

<task type="auto">
  <name>Expansion: unit contract suite proving hysteresis, signs, anti-windup, and determinism</name>
  <files>tests/test_baseline_controllers.py</files>
  <action>Add six unit checks to the tracer-created suite, following the 02-RESEARCH.md Validation Architecture Test Map and the in-body-import convention: test_onoff_hysteresis (fresh state at setpoint gives all-zero duties; T=20 latches heater 1.0; T=24.8 holds heat; T=25.5 releases; cooling mirror at T=26 gives fan and vent 1.0), test_onoff_mutual_exclusion (heater and fan_cooler never both positive across scripted latch states), test_pid_signs (cold T=20 gives heater positive and fan zero; hot T=30 gives fan positive and heater zero; dry RH=50 gives fogger positive; setpoint-at-fresh-state gives near-zero outputs), test_pid_antiwindup_improves (same gains with the conditional-integration guard bypassed versus guarded over a saturating night-to-day script show strictly lower T-IAE for the guarded variant), test_pid_integral_required (Ki zeroed variant shows droop with IAE far above the guarded PI, proving the I term is live), test_controller_signatures (25/70 versus 22/60 setpoints give different outputs; output keys exactly the four-actuator set with all duties in [0,1]; two runs from None are bit-identical proving fresh-state determinism per D-04 and BASE-03; output dict insertion order heater, fan_cooler, fogger, vent). Scalar-input edge (BASE-01 empty/single/null, resolved explicit): None state means fresh dict, and NaN inputs trip the entry finite assert rather than returning duties. Precision edge (resolved explicit): on/off duties are exact 0.0/1.0 literals and PID duties are float-wrapped np.clip results, so outputs are exact within float64 with no rounding contract beyond the [0,1] bound.</action>
  <read_first>
    tests/test_baseline_controllers.py (the tracer-created runner and _run_closed_loop helper this task extends);
    02-RESEARCH.md Validation Architecture Test Map (the seven BASE-01..03 rows this task implements) and Pitfalls 2/5/6 (windup guard, state aliasing, clipping);
    src/onoff_controller.py and src/pid_controller.py (signatures and state-dict shapes under test)
  </read_first>
  <acceptance_criteria>
    Behavior: heater switches stay below 350 per 24 h at the recommended bands; RH pins at 100 during saturated stretches without exceeding 100 (structural per D-03, not a defect).
    Test-command: python tests/test_baseline_controllers.py prints PASS for test_onoff_hysteresis, test_onoff_mutual_exclusion, test_pid_signs, test_pid_antiwindup_improves, test_pid_integral_required, test_controller_signatures, test_closed_loop_24h followed by all checks passed.
    CLI: python tests/test_greenhouse_model.py still prints all checks passed.
    Source: grep-free check via python -c asserting the file defines exactly seven test_ functions and contains __main__.
  </acceptance_criteria>
  <reversibility rating="reversible">Adds assertions only; no production behavior changes.</reversibility>
  <verify>
    <automated>python tests/test_baseline_controllers.py</automated>
    <fails_when>nonzero exit code, any line starting with FAIL, or output missing any of the seven PASS test names</fails_when>
  </verify>
  <done>All seven checks pass, the anti-windup and P-only ablations prove the integrator design, and the suite runs in under 5 seconds.</done>
</task>

<task type="auto">
  <name>Expansion: 02_baselines proof notebook plus committed PNG</name>
  <files>notebooks/02_baselines.ipynb, notebooks/02_baselines.png</files>
  <action>Build notebooks/02_baselines.ipynb per D-06 in the exact Phase-1 cell order (markdown title, imports, weather, run, plot) using the 02-PATTERNS.md notebook analog: Agg headless header importing step, load_weather_profile, daytime_solar, params, relative_humidity, wsat_g_per_kg plus onoff_step and pid_step with no duplicated plant math; weather cell regenerating the CSV with seed 7 when absent and interpolating to the 1440-step minute grid; run cell executing the closed loop twice over the identical disturbance with separate controller states (never one shared dict), setpoints 25.0 and 70.0 as function arguments, history kept as plain float and dict lists; plot cell with per-controller panels for T versus setpoint, RH versus setpoint, and duty stacks, suptitle naming both baselines, tight_layout, savefig to notebooks/02_baselines.png at dpi 120 plus plt.show(). Document the honest RH saturation in a markdown cell as the structural baseline weakness the fuzzy will exploit (per D-03, no vent-on-humid workaround). Keep gains and bands identical to the src/ defaults so notebook and suite agree.</action>
  <read_first>
    notebooks/01_greenhouse_model.ipynb (the exact cell order, weather-regenerate, interp, and savefig conventions to copy);
    02-CONTEXT.md D-04/D-06 (fixed 25 C / 70 %RH setpoints as args, notebook-plus-PNG proof shape);
    02-RESEARCH.md Code Examples closed-loop proof cell and Pitfalls 1/5 (expect RH saturation, separate states per run);
    src/onoff_controller.py and src/pid_controller.py (import names used by the notebook)
  </read_first>
  <acceptance_criteria>
    Behavior: notebook runs top-to-bottom against src/ functions and both traces match the suite numbers (T-IAE below 60 C-h each, RH within [0,100]).
    Test-command: python tests/test_baseline_controllers.py still prints all checks passed after the notebook lands.
    CLI: python -c "import json; nb=json.load(open('notebooks/02_baselines.ipynb')); src='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code'); assert 'from src.onoff_controller import' in src and 'from src.pid_controller import' in src and 'matplotlib.use' in src and '02_baselines.png' in src; print('nb-ok')" prints nb-ok.
    Source: python -c "import os; assert os.path.getsize('notebooks/02_baselines.png')>10000; print('png-ok')" prints png-ok.
  </acceptance_criteria>
  <reversibility rating="reversible">Proof artifact only; regenerable from src/ at any time.</reversibility>
  <verify>
    <automated>python -c "import json; nb=json.load(open('notebooks/02_baselines.ipynb')); src='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code'); assert 'from src.onoff_controller import' in src and 'from src.pid_controller import' in src and 'matplotlib.use' in src and '02_baselines.png' in src; print('nb-ok')"</automated>
    <fails_when>nonzero exit code or output missing the line nb-ok</fails_when>
    <automated>python -c "import os; assert os.path.getsize('notebooks/02_baselines.png')>10000; print('png-ok')"</automated>
    <fails_when>nonzero exit code, AssertionError traceback, or output missing the line png-ok</fails_when>
  </verify>
  <done>Notebook imports only from src/, executes headlessly cell by cell, and the committed PNG shows T/RH versus setpoint plus duty stacks for both baselines.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| caller→controller | Setpoints, T_C, rh_pct, and state dicts cross from harness/notebook into pure control functions; NaN or non-finite input would poison all downstream duties |
| controller→plant | Duty dict crosses into step(), which fail-fasts on unknown keys and out-of-range duties |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-02-01 | Tampering | onoff_step / pid_step entry | medium | mitigate | assert np.isfinite on T_C, rh_pct, and setpoints at controller entry; existing step() finite assert at src/greenhouse_model.py:82 stays as backstop |
| T-02-02 | Tampering | controller state dicts | low | accept with control | Fresh-state-on-None convention plus bit-identical determinism test in test_controller_signatures; rationale: local single-process harness, no cross-trust actor |
| T-02-SC | Tampering | installs (supply chain) | high | mitigate | Zero new dependencies this phase (numpy/matplotlib already accepted in Phase 1); no install step exists to attack |
</threat_model>

<verification>
Per-task commits run python tests/test_baseline_controllers.py; wave merge additionally runs python tests/test_greenhouse_model.py; phase gate requires both suites green plus the notebook structural check printing nb-ok and notebooks/02_baselines.png larger than 10 KB before verify-work.
</verification>

<success_criteria>
onoff_controller.py toggles with hysteresis, pid_controller.py tracks with continuous duties, both close the loop on the plant toward 25 C / 70 %RH through the shared 4-key duty contract, and the proof notebook reproduces both runs from src/ with a committed PNG.
</success_criteria>

<output>
Create `.planning/phases/02-baseline-controllers/02-01-SUMMARY.md` when done
</output>

## Artifacts this phase produces

File paths: src/onoff_controller.py, src/pid_controller.py, tests/test_baseline_controllers.py, notebooks/02_baselines.ipynb, notebooks/02_baselines.png.
Functions: onoff_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, band_T=0.5, band_RH=3.0) returning (actuator dict, state); pid_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, gains=GAINS) returning (actuator dict, state); test helper _run_closed_loop; seven test_ functions (test_onoff_hysteresis, test_onoff_mutual_exclusion, test_pid_signs, test_pid_antiwindup_improves, test_pid_integral_required, test_controller_signatures, test_closed_loop_24h).
Dict shapes: on/off state {heat: bool, cool: bool, fog: bool}; PID state {iT: float, pT: float-or-None, iH: float, pH: float-or-None}; module constant GAINS {Kp_T, Ki_T, Kd_T, Kp_H, Ki_H, Kd_H}; actuator command {heater, fan_cooler, fogger, vent} with duties in [0, 1] in that insertion order.
Notebook cells: markdown title, imports, weather, run (two closed loops), plot plus saturation note.

## Flagged assumptions (specless probe edges)

All seven BASE-01..03 probe edges were unresolved, handled as follows. Five are resolved explicitly by acceptance criteria above (no silent drops): boundary (strict-inequality latch holds prior state on exact band equality); adjacency/equality (heater versus cooler decided by sign split, never both, plus mutual-exclusion test); empty/single/null (None state means fresh dict, NaN trips the entry assert); ordering (actuator dict insertion order fixed heater, fan_cooler, fogger, vent); precision (0.0/1.0 literals for on/off, float-wrapped np.clip for PID, [0,1] the only rounding contract). Two remain explicit assumptions: (A1) RH pinning at 100 percent for long stretches is accepted as structural and honest per D-03 rather than a tuning defect, since the fogger authority overwhelms the T-slaved moisture sinks; (A2) Kd=0 for both loops leaves any small filtered-D overshoot improvement on the table as a non-blocking Phase-5 follow-up, since the I term carries tracking per the P-only ablation.
