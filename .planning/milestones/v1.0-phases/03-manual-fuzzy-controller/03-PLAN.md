---
phase: 03-manual-fuzzy-controller
plan: "03"
type: execute
wave: 1
depends_on: []
files_modified:
  - src/fuzzy_controller.py
  - tests/test_fuzzy_controller.py
  - notebooks/03_fuzzy.ipynb
  - notebooks/03_fuzzy.png
autonomous: true
requirements: [FUZZ-01, FUZZ-02, FUZZ-03, FUZZ-04, FUZZ-05, FUZZ-06]
user_setup: []

estimate:
  tokens: 55000
  raw_tokens: 28000
  tasks: 3
  confidence: high

must_haves:
  truths:
    - "Cold plant (T=20, setpoint 25) charges heater duty above zero within a few closed-loop steps; hot plant (T=30) drives fan_cooler above zero; dry air (RH=50, setpoint 70) drives fogger above zero; at-setpoint call with fresh state returns all duties near zero (per D-01, FUZZ-01, FUZZ-04)"
    - "A scripted +0.5 C/min error ramp at fixed error yields a different delta-output than flat error (error-rate path is live, per-minute normalization, FUZZ-01)"
    - "tri() returns 1.0 at its center and 0.0 beyond one half-width; FUZZY_MFS carries keys eT/deT/du/eH/deH/dv with 5 centers plus 5 widths each; interior universe points fire exactly 2 MFs (FUZZ-02 per D-02)"
    - "RULES is 5x5 with cells in 0..4, equilibrium cell RULES[2,2] is 2 (ZO), ZO-rate column reads [0,1,2,3,4], damping row RULES[2,:] reads [0,1,2,3,4] (FUZZ-03 per D-02)"
    - "Centroid surface: far-cold input gives delta above +0.3, far-hot gives delta below -0.3, centered input gives delta near 0.0, and repeated identical calls are bit-identical (FUZZ-05)"
    - "On a saturating night-then-day script the conditional-integration-freeze accumulator scores strictly lower IAE than a never-freeze variant (FUZZ-02/FUZZ-05)"
    - "24 h closed-loop run (1440 x dt=60 s, seed-7 weather, T0=20 C, setpoints 25 C / 70 %RH) stays finite and bounded, T-IAE below 60 C-h, RH within [0,100], fewer than 12 setpoint crossings in the last 6 h, alternate setpoints (22/60) give a different trace, two fresh-state runs are bit-identical, NaN input raises AssertionError (FUZZ-06 per D-03)"
    - "notebooks/03_fuzzy.ipynb imports only from src/ and notebooks/03_fuzzy.png renders above 10 KB (per D-04)"
  artifacts:
    - src/fuzzy_controller.py
    - tests/test_fuzzy_controller.py
    - notebooks/03_fuzzy.ipynb
    - notebooks/03_fuzzy.png
  key_links:
    - "fuzzy_step() output dict feeds greenhouse_model.step() per minute over interpolated seed-7 weather"
    - "FUZZY_MFS named dict is the Phase-4 chromosome material (read-only at runtime)"
    - "notebook 03_fuzzy.ipynb calls fuzzy_step from src/ with no duplicated plant or inference logic"
  prohibitions:
    - never emit unknown actuator keys
    - never mutate FUZZY_MFS at runtime
    - never add dependencies
    - notebook must not duplicate src logic
  assumptions:
    - "FUZZ-01 boundary (unresolved probe edge): inputs exactly at universe min/max saturate to the edge term via input clipping in infer(); one step beyond the edge behaves identically to the edge itself — flagged, resolved by clipping contract, verified by extreme-error unit checks"
    - "FUZZ-01 precision (unresolved probe edge): 201-point centroid grid quantizes output to 0.01 duty, negligible against 0.33 C/min full-duty authority — flagged assumption, verified by determinism plus surface-threshold checks"
    - "FUZZ-02..FUZZ-06 unclassified probe edges: no hidden edge found in research; covered explicitly by the suite thresholds above (IAE bound 60, crossings below 12, monotone table asserts) — flagged, no silent drops"
---

<objective>
**As a** greenhouse-modeling engineer, **I want to** close the loop on the Phase-1 plant with a hand-tuned Mamdani fuzzy controller, **so that** the inference engine is proven stable before Phase 4's GA tunes its membership functions.

Purpose: Deliver the dual-loop velocity-form fuzzy controller per D-01 (T-loop drives heater/fan_cooler/vent with vent following cooling, RH-loop drives fogger only), the textbook diagonal 5x5 rule tables per D-02, stable 24 h tracking per D-03 (NOT beating baselines — on/off T-IAE 7.38 and PID T-IAE 1.08 are reference numbers only), and the proof notebook plus PNG per D-04. Implements the non-negotiable research verdicts: velocity/incremental form, MacVicar-Whelan diagonal table shared by both loops, MF universes T-error +-4 C / T-rate +-0.5 C per min / RH-error +-30 / RH-rate +-6 per min / delta +-0.1 per step, per-minute error-rate via (e - e_prev)/(dt/60), FUZZY_MFS named dict, T-loop accumulation on [-1,1] with sign split-range, RH-loop on [0,1] to fogger, conditional-integration freeze on both rails of both loops.

Output: src/fuzzy_controller.py, tests/test_fuzzy_controller.py, notebooks/03_fuzzy.ipynb, notebooks/03_fuzzy.png.
</objective>

<execution_context>
@C:/Users/Lalit/.config/opencode/gsd-core/workflows/execute-plan.md
@C:/Users/Lalit/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/03-manual-fuzzy-controller/03-CONTEXT.md
@.planning/phases/03-manual-fuzzy-controller/03-RESEARCH.md
@.planning/phases/03-manual-fuzzy-controller/03-PATTERNS.md
@src/pid_controller.py
@src/greenhouse_model.py
</context>

<tasks>

<task type="tracer">
  <name>Tracer: end-to-end velocity-form fuzzy loop — one path, plant to duties</name>
  <files>src/fuzzy_controller.py</files>
  <read_first>src/fuzzy_controller.py does not exist yet — read src/pid_controller.py (signature, asserts, state-key loop, split-range, anti-windup discipline), src/greenhouse_model.py lines 55-84 (actuator key and range contract), 03-RESEARCH.md Patterns 1-4 (FUZZY_MFS values, RULES cells, infer core, fuzzy_step body), 03-PATTERNS.md fuzzy_controller section (module-docstring and key-order conventions), 03-CONTEXT.md D-01 and D-02</read_first>
  <acceptance_criteria>Module exposes LABELS as the 5-tuple NB NS ZO PS PB; FUZZY_MFS with keys eT deT du eH deH dv each holding 5 centers and 5 widths at the probe universes (T-error +-4, T-rate +-0.5, RH-error +-30, RH-rate +-6, deltas +-0.1); RULES 5x5 diagonal table with equilibrium cell 2 and ZO-rate column [0,1,2,3,4]; fuzzy_step signature (T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, mfs=FUZZY_MFS) returning the exact 4-key dict in [0,1] with vent equal to fan_cooler; fresh-state at-setpoint call returns all duties near zero; cold start charges heater within 5 steps; 240-step smoke loop against step() stays finite with mutual exclusion held</acceptance_criteria>
  <reversibility rating="costly">Implements the D-01 dual-loop split (T owns heater/fan/vent, RH owns fogger) — every GA-fitness and comparison trace builds on this split</reversibility>
  <action>Create src/fuzzy_controller.py per D-01 and D-02: NumPy-only module with LABELS tuple, FUZZY_MFS named centers-plus-widths dict at the probe-verified universes, the MacVicar-Whelan diagonal RULES table, a triangular tri helper, a shared infer core doing input clipping to each universe then min-implication max-aggregation with a 201-point centroid and zero-fire fallback of 0.0, and fuzzy_step as the incremental dual-loop wrapper with finite-input asserts, fail-loud state-key loop over pT pH uT uH, per-minute error-rate via division by (dt/60), T accumulation on [-1,1] split-ranged by sign with vent mirroring cooling, RH accumulation on [0,1] to fogger, and conditional-integration freeze on both rails of both loops. Keep the PID module-docstring, key-order, and read-only-params conventions; never assign into the mfs arrays; no new imports beyond NumPy. Do not build metrics, weather resamplers, or positional-form output.</action>
  <verify>
    <automated>python -c "from src.fuzzy_controller import fuzzy_step, FUZZY_MFS, RULES; a,s=fuzzy_step(25.0,70.0,25.0,70.0,None); assert all(abs(d)<1e-9 for d in a.values()), a; st=None; [exec('') for _ in []]; h=[fuzzy_step(20.0,70.0,25.0,70.0,st) for _ in range(5)]; st=h[-1][1]; assert h[-1][0]['heater']>0.0; print('tracer-ok')"</automated>
    <fails_when>Exit code nonzero, or the printed line tracer-ok is absent, or any AssertionError naming heater duty or key set</fails_when>
  </verify>
  <done>Single happy path works end to end: fresh-state setpoint call holds zero, cold plant charges heat, duties satisfy the plant contract, module committed</done>
</task>

<task type="auto">
  <name>Expansion: plain-assert fuzzy suite covering FUZZ-01 through FUZZ-06</name>
  <files>tests/test_fuzzy_controller.py</files>
  <read_first>tests/test_fuzzy_controller.py does not exist yet — read tests/test_baseline_controllers.py in full (harness, sign tests, anti-windup comparison structure, 24 h integration asserts, standalone runner with sys.path prepend), src/fuzzy_controller.py from the tracer task, 03-RESEARCH.md Validation Architecture (9-check test map with thresholds), 03-CONTEXT.md D-03 (FUZZ-06 bar: stable tracking, baselines are reference only)</read_first>
  <acceptance_criteria>Suite file runs standalone and prints all checks passed; covers sign behavior per D-01 (cold charges heater within steps, hot drives fan, dry drives fogger, fresh at-setpoint near zero), error-rate liveness on a scripted 0.5 C per min ramp, MF shape plus 50 percent overlap, RULES equilibrium and monotone asserts, centroid thresholds (strong heat above 0.3, strong cool below -0.3, centered near 0.0) plus determinism, anti-windup freeze variant strictly improving IAE, and the 24 h integration (1440 steps, finite, T-IAE below 60, RH within [0,100], fewer than 12 crossings in last 6 h, setpoints-as-args differ, bit-identical reruns, NaN raises); no pytest or conftest dependency</acceptance_criteria>
  <action>Create tests/test_fuzzy_controller.py per D-03 following the baseline suite conventions exactly: module docstring naming FUZZ-01..06, in-body imports so the file runs in wave-0 ordering, a closed-loop helper mirroring the Phase-2 harness (T0 20.0, w0 0.65 times wsat at 20, per-minute weather interpolation with daytime_solar, controller then step then append), eight test functions for signs, error-rate liveness, membership shapes, rule table, output mapping with mutual exclusion and exact key order, centroid surface, accumulator anti-windup comparison with a never-freeze variant, and the 24 h closed-loop integration at the loose honesty bounds, plus the standalone main runner copied with its path-prepend comment. Adapt sign thresholds to velocity-form accumulation (a few steps to charge) rather than copying positional single-call expectations. Keep history as plain lists for Phase 5; do not build metrics.py here.</action>
  <verify>
    <automated>python tests/test_fuzzy_controller.py</automated>
    <fails_when>Exit code nonzero, or any line starting with FAIL appears, or the final all checks passed line is absent</fails_when>
  </verify>
  <done>Full fuzzy suite green standalone; plant and baseline suites still green alongside it</done>
</task>

<task type="auto">
  <name>Expansion: proof notebook 03_fuzzy plus committed PNG per D-04</name>
  <files>notebooks/03_fuzzy.ipynb, notebooks/03_fuzzy.png</files>
  <read_first>Read notebooks/02_baselines.ipynb notebook JSON (cell pattern: Agg imports, regen-if-absent seed-7 weather, closed-loop run, plot plus savefig at dpi 120, honest-saturation note), src/fuzzy_controller.py (LABELS, FUZZY_MFS, fuzzy_step import surface), 03-CONTEXT.md D-04 (notebook imports from src only, feeds Phase-6 trail), 03-RESEARCH.md Open Questions (trace panels plus at least one MF-shape figure)</read_first>
  <acceptance_criteria>Notebook JSON contains Agg headless setup, imports fuzzy_step FUZZY_MFS LABELS from src plus plant helpers with no duplicated plant or inference logic, regen-if-absent seed-7 weather block, single fuzzy closed-loop run printing T-IAE near the probe value of 2.79 (must stay below 60), T-vs-setpoint plus RH-vs-setpoint plus duty-stack plots with grid alpha 0.3, at least one MF-shape figure usable as the Phase-6 GA before reference, an honest note that RH pins at 100 structurally, and savefig to notebooks/03_fuzzy.png at dpi 120; PNG exceeds 10 KB</acceptance_criteria>
  <action>Build notebooks/03_fuzzy.ipynb per D-04 by adapting the 02_baselines cell pattern to a single fuzzy run: title cell documenting setpoints 25 C and 70 %RH with seed-7 weather and separate controller state, weather regen-if-absent block, run_closed_loop helper calling fuzzy_step with setpoints as args, IAE print cell, trace plus duty plus MF-shape figure cells, honest RH-saturation markdown, and savefig plus show close. Generate the PNG by executing the same plot code headlessly with the Agg backend (jupyter CLI is absent) and commit both files together. Keep all numerics in src; the notebook only orchestrates and plots.</action>
  <verify>
    <automated>python -c "import json; nb=json.load(open('notebooks/03_fuzzy.ipynb')); src='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code'); assert 'from src.fuzzy_controller import' in src and 'matplotlib.use' in src and '03_fuzzy.png' in src; print('nb-ok')"</automated>
    <fails_when>Exit code nonzero, or nb-ok is not printed, or the assert names a missing import or savefig target</fails_when>
  </verify>
  <done>Notebook structurally valid against src imports and PNG proof committed above 10 KB</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| caller→fuzzy_step | Untrusted numerics (state, setpoints, sensor readings) cross into the inference core |
| notebook→src | Notebook passes weather-derived floats into the controller each minute |
| future-GA→FUZZY_MFS | Phase 4 will pass mutated MF copies; the dict must survive aliasing intact |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-03-01 | Tampering | fuzzy_step entry (T_C, rh_pct, setpoints, dt) | high | mitigate | Finite-float asserts on every numeric input at entry per V5; suite NaN test asserts AssertionError; plant step() finite assert backstops at src/greenhouse_model.py:82 |
| T-03-02 | Tampering | infer() universe handling | medium | mitigate | Clip error and error-rate inputs to MF universes before fuzzification so edge terms saturate; zero-fire fallback returns 0.0 hold instead of NaN |
| T-03-03 | Tampering | accumulator outputs (uT, uH) | medium | mitigate | np.clip every accumulation every call (T on [-1,1], RH on [0,1]) plus conditional-integration freeze on both rails of both loops; 24 h integration test feeds outputs into step() directly |
| T-03-04 | Tampering | caller-owned state dicts | medium | mitigate | Fresh-state-on-None convention (never a mutable default), fail-loud key loop over pT pH uT uH, bit-identical determinism test guards cross-run aliasing |
| T-03-05 | Tampering | FUZZY_MFS module dict | medium | mitigate | Read-only convention documented in the module docstring: only index into mfs arrays, never assign; GA passes mutated copies rather than writing in place |
| T-03-SC | Tampering | npm/pip/cargo installs | high | mitigate | Zero new dependencies this phase (NumPy plus Matplotlib already accepted in Phase 1; scikit-fuzzy explicitly rejected); no legitimacy checkpoint needed with an empty install set |
</threat_model>

<verification>
1. python tests/test_fuzzy_controller.py prints all checks passed (FUZZ-01..06 behaviors, < 60 s)
2. python tests/test_baseline_controllers.py still green (no baseline regression)
3. python tests/test_greenhouse_model.py still green (no plant regression)
4. nb-ok structural one-liner prints nb-ok for notebooks/03_fuzzy.ipynb
5. notebooks/03_fuzzy.png exists above 10 KB
6. No new packages installed; notebook imports resolve only to src/ plus stdlib plus numpy plus matplotlib
</verification>

<success_criteria>
Hand-tuned velocity-form Mamdani controller tracks 25 C / 70 %RH stably for 24 h on seed-7 weather (T-IAE below 60 honesty bound, fewer than 12 crossings in last 6 h, finite and bounded), emits the exact 4-key duty dict the GA and metrics phases consume, and proves it via suite plus notebook plus PNG with zero new dependencies
</success_criteria>

<output>
Create `.planning/phases/03-manual-fuzzy-controller/03-PLAN-SUMMARY.md` when done
</output>

## Artifacts this phase produces

| Symbol / File | Kind | Defined in | Consumed by |
|---------------|------|------------|-------------|
| src/fuzzy_controller.py | file | this phase | tests, notebook, Phase 4 GA, Phase 5 metrics |
| LABELS = (NB, NS, ZO, PS, PB) | constant | src/fuzzy_controller.py | infer(), RULES indexing, notebook MF plots |
| FUZZY_MFS (keys eT, deT, du, eH, deH, dv; 5 centers + 5 widths each) | named param dict | src/fuzzy_controller.py | fuzzy_step default; Phase 4 chromosome material (read-only) |
| RULES 5x5 MacVicar-Whelan diagonal table | constant | src/fuzzy_controller.py | infer() consequent lookup, both loops |
| tri(x, c, w) | function | src/fuzzy_controller.py | infer() fuzzification |
| infer(e, de, EC, EW, DC, DW, OC, OW, lo, hi, n=201) | function | src/fuzzy_controller.py | fuzzy_step T-loop ([-1,1]) and RH-loop ([0,1]) |
| fuzzy_step(T_C, rh_pct, T_sp=25.0, RH_sp=70.0, state=None, dt=60.0, mfs=FUZZY_MFS) | function | src/fuzzy_controller.py | tests, notebook, Phase 4 fitness loop |
| controller state dict {pT, pH, uT, uH} | data shape | src/fuzzy_controller.py | caller-owned per run; None means fresh |
| 4-key duty dict {heater, fan_cooler, fogger, vent} in [0,1], vent == fan_cooler | data shape | src/fuzzy_controller.py | greenhouse_model.step(), Phase 5 scoring |
| tests/test_fuzzy_controller.py (8 checks: signs, error-rate, MFs, rules, mapping, centroid, anti-windup, 24 h) | file | this phase | phase gate, regression |
| notebooks/03_fuzzy.ipynb | file | this phase | Phase-6 notebook trail |
| notebooks/03_fuzzy.png | file | this phase | proof plot (traces + duties + MF shapes) |
</artifacts>
