---
phase: 04-ga-optimization
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: ["src/genetic_algorithm.py", "src/ga_fuzzy_controller.py", "tests/test_genetic_algorithm.py", "results/ga_optimized_params.json", "notebooks/04_ga_optimization.ipynb", "notebooks/04_ga_optimization.png"]
autonomous: true
requirements: [GA-01, GA-02, GA-03, GA-04, GA-05]
user_setup: []

estimate:
  tokens: 55000
  raw_tokens: 27500
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "60-D chromosome round-trips hand FUZZY_MFS values bit-identically through encode/decode"
    - "Every decoded chromosome yields sorted centers, widths strictly positive, all finite, and a completing simulation"
    - "Fitness of the hand chromosome is finite and near the hand-fuzzy weighted cost on train weather; fitness never raises (bad chromosome returns inf)"
    - "Tiny seeded GA (pop 4 x gen 2) finishes in under 30 s with best fitness monotonically non-worsening (elitism-2 holds)"
    - "Full 50 x 50 evolution writes results/ga_optimized_params.json with the frozen schema and history of length 50"
    - "ga_fuzzy_step loads the JSON and matches fuzzy_step with mfs set to decoded params exactly"
    - "On shared fresh holdout weather (seed 21), GA fuzzy weighted cost is lower than on/off weighted cost AND lower than PID weighted cost on the same shared weather (relative ordering, per-term IAE_T/IAE_H/E breakdown reported for each, no absolute threshold)"
    - "Notebook loads JSON plus history and plots only; it never runs evolution inline"
    - "Hand FUZZY_MFS global is bit-identical before and after any GA run"
  artifacts:
    - "src/genetic_algorithm.py"
    - "src/ga_fuzzy_controller.py"
    - "tests/test_genetic_algorithm.py"
    - "results/ga_optimized_params.json"
    - "notebooks/04_ga_optimization.ipynb"
    - "notebooks/04_ga_optimization.png"
  key_links:
    - "decode output dict feeds fuzzy_step mfs argument inside fitness with no global mutation"
    - "run_ga best chromosome plus history feeds results/ga_optimized_params.json schema keys"
    - "ga_fuzzy_controller load_optimized_mfs output feeds ga_fuzzy_step delegation to fuzzy_step"
    - "JSON artifact feeds notebook plots and Phase 5 and Phase 7 consumers"
    - "Duty-hours energy definition locked here must be identical in Phase 5 metrics.py"
  prohibitions:
    - "never mutate FUZZY_MFS global"
    - "never add dependencies including DEAP and pymoo"
    - "notebook must not duplicate src logic or run evolution inline"
---

<objective>
GA tunes the full fuzzy membership-function set so the GA fuzzy controller beats both baselines on fresh weather.

Purpose: This phase decides the project core value — the holdout comparison on weather the GA never saw must show GA fuzzy below both baselines on the locked weighted cost.
Output: src/genetic_algorithm.py, src/ga_fuzzy_controller.py, tests/test_genetic_algorithm.py, results/ga_optimized_params.json, notebooks/04_ga_optimization.ipynb plus PNG.
</objective>

**As a** greenhouse researcher, **I want to** evolve the fuzzy membership functions with a real-valued GA and prove the tuned controller beats both baselines on unseen weather, **so that** the intelligent controller claim holds by measurement rather than by tuning on the test set.

<execution_context>
@C:/Users/Lalit/.config/opencode/gsd-core/workflows/execute-plan.md
@C:/Users/Lalit/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/04-ga-optimization/04-CONTEXT.md
@.planning/phases/04-ga-optimization/04-RESEARCH.md
@.planning/phases/04-ga-optimization/04-PATTERNS.md
@src/fuzzy_controller.py
@src/greenhouse_model.py
@src/weather_profile_generator.py
@tests/test_fuzzy_controller.py
</context>

<tasks>

<task type="tracer">
  <name>Tracer: chromosome to holdout win on a tiny budget</name>
  <files>src/genetic_algorithm.py, src/ga_fuzzy_controller.py, tests/test_genetic_algorithm.py, results/ga_optimized_params.json</files>
  <read_first>src/genetic_algorithm.py does not exist yet — create it; source of truth is 04-RESEARCH.md Architecture Patterns 1 to 4 plus Code Examples, 04-PATTERNS.md sections on src/genetic_algorithm.py and src/ga_fuzzy_controller.py, 04-CONTEXT.md D-01 to D-04, and the engine contract in src/fuzzy_controller.py lines 20 to 29 for FUZZY_MFS values, lines 40 to 48 for tri and infer clipping semantics, line 63 for the fuzzy_step mfs injection argument, and lines 65 to 89 for asserts plus emission contract; also read tests/test_fuzzy_controller.py lines 1 to 30 for the _run_closed_loop harness shape and lines 236 to 254 for the standalone runner to copy.</read_first>
  <action>Build the thinnest production-quality end-to-end slice in src/genetic_algorithm.py using NumPy only: module exposes ORDER fixed as eT, deT, du, eH, deH, dv, BOUNDS dict with per-variable center lo and hi plus w_min strictly above zero and w_max, encode taking an MF dict to a flat 60-element float array in ORDER with 5 centers then 5 widths per group, decode taking a 60-element vector back to a fresh dict of fresh arrays with per-group sort of clipped centers and clip of widths into BOUNDS and never returning views, fitness function evaluate taking a chromosome plus weather arrays and hours and returning 1.0 times IAE_T plus 1.0 times IAE_H plus 0.01 times duty-hours energy per D-01 with the full 1440-step closed loop at dt 60 reusing the _run_closed_loop shape with initial T 20.0 and w 0.65 times wsat at 20, wrapping the whole body in try-except returning positive inf on any exception, tournament_select with k 3, blx_alpha with alpha 0.5, gaussian_mutate with per-gene probability 1 over 60 and sigma 0.1 times that gene range, elitism-2 generational loop in run_ga owning a single default_rng from rng_seed with all draws through it, init population where individual 0 is the exact hand encoding and the rest are hand values times one plus uniform minus 0.2 to 0.2 then repaired, per D-02 defaults population 50 generations 50 with a smoke path at pop 4 gen 2, run_ga creating results dir with makedirs exist_ok and flushing best-so-far plus history every generation, script entry so python src/genetic_algorithm.py runs evolution without a notebook. Build src/ga_fuzzy_controller.py as a thin wrapper copying the pid_controller module and signature shape: load_optimized_mfs validating exact key set eT deT du eH deH dv with len-5 float lists widths above zero and all finite with fail-fast asserts and converting lists to arrays with lazy module-level caching, ga_fuzzy_step with signature T_C rh_pct T_sp 25.0 RH_sp 70.0 state None dt 60.0 delegating to fuzzy_step with mfs set to the loaded dict. Build tests/test_genetic_algorithm.py copying the header and __main__ runner and in-body import convention from tests/test_fuzzy_controller.py with tests test_encode_decode_roundtrip asserting hand values round-trip bit-identically, test_decode_repair_invariants asserting sorted centers widths above w_min all finite on random chromosomes plus a completing sim, test_fitness_matches_hand_cost asserting finite fitness near the hand-fuzzy train cost, test_fitness_never_raises asserting inf on a hostile chromosome, test_tiny_ga_monotonic running pop 4 gen 2 asserting best never worsens and wall under 30 s, test_json_schema running a tiny run_ga to a temp path asserting exact schema keys mfs fitness weights train_weather train_seed holdout_seed population generations rng_seed history with len-5 lists and history lengths equal to generations, test_hand_mfs_untouched snapshotting FUZZY_MFS arrays before and after the smoke and asserting bit-identical, plus a holdout smoke asserting GA cost below onoff cost on a tiny fresh-seed weather generated once to a temp path per D-03. Using hand chromosome as individual 0 per the never-worse-than-hand guarantee, using fixed operator rates only with no adaptive schedules, referencing D-01 D-02 D-03 D-04 in code comments where each is implemented.</action>
  <acceptance_criteria>Exact values honored: 60-D layout 6 groups times 5 centers plus 5 widths in ORDER eT deT du eH deH dv; tournament size 3; BLX alpha 0.5; per-gene mutation probability 1/60 with sigma 0.1 times range; elitism 2; weights w1 1.0 w2 1.0 w3 0.01; hand chromosome is individual 0; single default_rng owned by run_ga with no np.random global calls; smoke pop 4 gen 2 completes in under 30 s; JSON contains keys mfs fitness weights train_weather train_seed holdout_seed population generations rng_seed history with weights 1.0 1.0 0.01 and holdout_seed 21. Behavior assertion: python tests/test_genetic_algorithm.py exits 0.</acceptance_criteria>
  <verify>
    <automated>python tests/test_genetic_algorithm.py</automated>
    <fails_when>Non-zero exit code, any line containing FAIL, or wall time exceeding 60 s for the smoke suite.</fails_when>
  </verify>
  <done>Tiny-budget chromosome to JSON to ga_fuzzy_step to holdout-ordering slice works end-to-end and is committed with the suite green.</done>
</task>

<task type="auto">
  <name>Full 50x50 evolution producing the frozen JSON artifact</name>
  <files>results/ga_optimized_params.json</files>
  <read_first>Read src/genetic_algorithm.py created by the tracer task plus 04-RESEARCH.md Pattern 4 for the frozen JSON schema, Pitfall 2 for script-not-notebook evolution with incremental flush, Open Question 1 for holdout_seed 21, and src/weather_profile_generator.py lines 15 to 26 for the generate_weather_profile call signature; confirm weather/weather_profile.csv train weather is present and never regenerate it.</read_first>
  <action>Run the full locked-budget evolution as a script per D-02 with population 50 generations 50 rng_seed 0 on the immutable train weather weather/weather_profile.csv with train_seed recorded as 7, evolution executing outside any notebook, flushing best-so-far plus history to results/ga_optimized_params.json every generation so a killed run still yields an artifact, final JSON containing exactly the frozen keys mfs with six groups each holding centers and widths len-5 float lists fitness weights w1 1.0 w2 1.0 w3 0.01 train_weather path train_seed 7 holdout_seed 21 population 50 generations 50 rng_seed 0 history with best and mean lists of length 50, then run the holdout proof once on freshly generated weather at an isolated path via generate_weather_profile with seed 21 that is never passed to fitness, scoring all four controllers on that shared holdout weather and recording the per-term breakdown IAE_T IAE_H and duty-hours energy for each, requiring the relative ordering GA cost below onoff cost AND below PID cost on that same shared holdout weather with no absolute threshold asserted anywhere per the humidity-dominance finding, recording the duty-hours energy definition verbatim in the JSON-adjacent run log for Phase 5 metrics.py reuse. Lock holdout_seed 21 permanently once this run completes. Amendment A1 (2026-09-27, user-approved D-04a): BOUNDS output-center lo/hi widened to (-1.0, 1.0) for du and dv only (bang-bang-capable authority; input universes, width bounds, rules, engine unchanged); hand chromosome stays interior and individual 0; re-run supersedes the run-1 JSON at the same path. Amendment A2 (2026-09-27, user-approved D-06): GA fuzzy alone becomes cross-coupled — implement a humidity-driven boost on heater and vent computed AFTER the untouched decoupled velocity loops (same engine, same hand MFs as base, same 4-key clipped dict contract), with the coupling gains as extra chromosome genes appended to ORDER (dimension grows 60-D to 60+G; hand-equivalent gene values = zero boost so individual 0 stays never-worse-than-hand); decode/encode/repair extend mechanically to the new genes; baselines and hand fuzzy untouched; holdout bar, weights, budget, seeds unchanged; notebook verdict and SUMMARY frame intelligent-coupled vs classical-decoupled.</action>
  <reversibility rating="costly">Holdout seed 21 anchors the core-value claim every later comparison references; changing it after this task invalidates the published generalization proof.</reversibility>
  <acceptance_criteria>Budget exact: population 50, generations 50, about 2500 evals; JSON schema keys exact with weights 1.0 1.0 0.01, train_seed 7, holdout_seed 21, history best and mean length 50; holdout bar exact: GA weighted cost below onoff weighted cost AND below PID weighted cost on the same shared seed-21 weather with per-term IAE_T IAE_H E reported for each; no absolute cost threshold in any assertion. Behavior assertion: JSON exists with the schema and the holdout ordering holds.</acceptance_criteria>
  <verify>
    <automated>python -c "import json; d=json.load(open('results/ga_optimized_params.json')); assert set(d)=={'mfs','fitness','weights','train_weather','train_seed','holdout_seed','population','generations','rng_seed','history'}; assert set(d['mfs'])=={'eT','deT','du','eH','deH','dv'}; assert all(len(d['mfs'][k]['centers'])==5 and len(d['mfs'][k]['widths'])==5 for k in d['mfs']); assert d['weights']=={'w1':1.0,'w2':1.0,'w3':0.01}; assert d['holdout_seed']==21 and d['population']==50 and d['generations']==50; assert len(d['history']['best'])==50 and len(d['history']['mean'])==50; print('json-ok')"</automated>
    <fails_when>Non-zero exit, missing key assertion, history length other than 50, or the string json-ok absent from output.</fails_when>
  </verify>
  <done>Full-budget JSON artifact exists with frozen schema and the seed-21 holdout shows GA cost below on/off cost AND below PID cost on the same shared weather.</done>
</task>

<task type="auto">
  <name>Proof notebook with convergence plus holdout plus MF plots</name>
  <files>notebooks/04_ga_optimization.ipynb, notebooks/04_ga_optimization.png</files>
  <read_first>Read notebooks/03_fuzzy.ipynb cell structure for the 6-cell markdown title plus imports plus weather-load plus closed-loop plus honest-note plus plot-and-save pattern, 04-PATTERNS.md notebook section for the Agg headless import order and the anti-leakage holdout path rule, and 04-CONTEXT.md D-05 for the proof shape; reference results/ga_optimized_params.json produced by the prior task as the only data source.</read_first>
  <action>Author notebooks/04_ga_optimization.ipynb following the Phase 1 to 3 notebook pattern per D-05 with Agg headless set before pyplot import, imports from src only covering greenhouse_model step load_weather_profile daytime_solar params relative_humidity wsat_g_per_kg plus weather generator plus onoff pid fuzzy and ga_fuzzy controllers, train weather loaded never regenerated with a guard that generates only if the CSV is missing at seed 7, holdout weather generated once at the isolated seed-21 path and never passed to fitness, closed-loop runner copied from the established pattern with T and w init 20.0 and 0.65 times wsat at 20 and setpoints as function args, cells loading the JSON artifact plus history and plotting convergence curves of best and mean per generation plus holdout 4-controller traces of GA versus onoff versus PID versus hand fuzzy on the fresh seed plus MF before and after overlays with per-term breakdown IAE_T IAE_H and energy printed in a verdict cell asserting relative ordering GA below on/off AND below PID on the same shared weather only, saving notebooks/04_ga_optimization.png and committing both files, with no evolution call and no duplicated engine logic in any cell.</action>
  <acceptance_criteria>Notebook contains imports from src/genetic_algorithm or ga_fuzzy_controller or results JSON load, matplotlib Agg headless, reference to 04_ga_optimization.png, no run_ga with population 50 in any executed cell; PNG exists beside the notebook; holdout verdict cell asserts relative ordering GA below onoff AND below PID on the same shared weather with per-term IAE_T/IAE_H/E breakdown and no absolute threshold. Behavior assertions: structural check prints nb-ok and PNG check passes.</acceptance_criteria>
  <verify>
    <automated>python -c "import json; nb=json.load(open('notebooks/04_ga_optimization.ipynb')); src='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code'); assert 'from src.ga_fuzzy_controller import' in src and 'matplotlib.use' in src and '04_ga_optimization.png' in src; assert 'run_ga(population=50' not in src; print('nb-ok')"</automated>
    <fails_when>Non-zero exit, nb-ok absent, or any assert naming a missing import, missing Agg setup, missing PNG reference, or a forbidden inline full-budget evolution call.</fails_when>
  </verify>
  <done>Notebook executes headless against src functions, plots from saved artifacts only, and the committed PNG exists.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| researcher-disk to ga_fuzzy_controller | Hand-edited JSON artifact crosses into the controller at load time |
| fitness hot loop to simulator | Repaired but untrusted chromosome-derived MF dict crosses into fuzzy_step and greenhouse_model step per eval |
| notebook to JSON artifact | Saved JSON and history cross into plotting cells |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-04-01 | Tampering | load_optimized_mfs in src/ga_fuzzy_controller.py | high | mitigate | Fail-fast asserts on load: exact key set eT deT du eH deH dv, len-5 float lists, widths above zero, all finite; reject before any simulation starts; covered by test_json_schema in tests/test_genetic_algorithm.py |
| T-04-02 | Tampering | decode in src/genetic_algorithm.py | high | mitigate | Mandatory clip plus sort repair on every decode: sort clipped centers, clip widths into w_min above zero and w_max; decode allocates fresh arrays so the FUZZY_MFS global is never touched; covered by test_decode_repair_invariants and test_hand_mfs_untouched |
| T-04-03 | Tampering | fitness in src/genetic_algorithm.py | medium | mitigate | try-except boundary returning positive inf on any exception so one bad chromosome cannot kill the 25-minute run; finiteness assert on cost before return; covered by test_fitness_never_raises |
| T-04-04 | Tampering | pickle or eval on artifact path | medium | mitigate | JSON-only via stdlib json in both producer and consumer; no pickle, no npy allow_pickle, no eval or exec on file contents; notebook never executes artifact contents |
| T-04-05 | Repudiation | RNG and seed bookkeeping | medium | mitigate | Single default_rng owned by run_ga with all draws through it, no np.random globals; train_seed, holdout_seed 21, and rng_seed recorded in JSON; holdout weather on an isolated path generated once at proof time and never passed to fitness |
| T-04-SC | Tampering | npm/pip/cargo installs | high | mitigate | No new dependencies: NumPy-only src convention; Package Legitimacy Audit in 04-RESEARCH.md is intentionally empty; planner adds no install task and any added package triggers a blocking human checkpoint |
</threat_model>

<verification>
Full suite green in order: python tests/test_greenhouse_model.py then python tests/test_baseline_controllers.py then python tests/test_fuzzy_controller.py then python tests/test_genetic_algorithm.py; JSON schema check prints json-ok; notebook structural check prints nb-ok with notebooks/04_ga_optimization.png present; holdout comparison on the same shared seed-21 weather shows GA weighted cost below on/off weighted cost AND below PID weighted cost with per-term IAE_T, IAE_H, and duty-hours energy reported for each and no absolute threshold.
</verification>

<success_criteria>
GA-01 holds with 60-D round-trip plus repair invariants; GA-02 holds with locked weights 1.0, 1.0, 0.01 and inf-on-exception fitness; GA-03 holds with tournament-3, BLX-0.5, per-gene gaussian mutation, elitism-2, and monotonic tiny-GA smoke under 30 s; GA-04 holds with frozen-schema JSON plus length-50 history; GA-05 holds with bit-identical ga_fuzzy_step delegation and relative holdout win over on/off AND over PID on the same shared weather; notebook plus PNG committed with no inline evolution and no duplicated src logic.
</success_criteria>

<output>
Create `.planning/phases/04-ga-optimization/04-01-SUMMARY.md` when done
</output>

## Artifacts this phase produces

| Symbol | Kind | Location |
|--------|------|----------|
| ORDER | constant, fixed decode order eT deT du eH deH dv | src/genetic_algorithm.py |
| BOUNDS | constant, per-variable center lo/hi plus w_min above zero plus w_max | src/genetic_algorithm.py |
| encode | function, MF dict to flat 60-element float vector | src/genetic_algorithm.py |
| decode | function, 60-element vector to fresh repaired MF dict with sort plus clip | src/genetic_algorithm.py |
| evaluate / fitness | function, chromosome plus weather to 1.0 IAE_T plus 1.0 IAE_H plus 0.01 duty-hours energy with try-except to inf | src/genetic_algorithm.py |
| tournament_select | function, tournament size 3 | src/genetic_algorithm.py |
| blx_alpha / crossover | function, BLX alpha 0.5 blend | src/genetic_algorithm.py |
| gaussian_mutate / mutate | function, per-gene probability 1/60 sigma 0.1 times range | src/genetic_algorithm.py |
| run_ga | function plus script entry, population 50 generations 50 rng_seed 0, owns single default_rng, individual 0 is hand encoding, makedirs results, per-generation flush | src/genetic_algorithm.py |
| load_optimized_mfs | function, validates exact key set, len-5 lists, widths above zero, all finite | src/ga_fuzzy_controller.py |
| ga_fuzzy_step | function, signature T_C rh_pct T_sp RH_sp state dt delegating to fuzzy_step with loaded mfs | src/ga_fuzzy_controller.py |
| test_encode_decode_roundtrip | test | tests/test_genetic_algorithm.py |
| test_decode_repair_invariants | test | tests/test_genetic_algorithm.py |
| test_fitness_matches_hand_cost | test | tests/test_genetic_algorithm.py |
| test_fitness_never_raises | test | tests/test_genetic_algorithm.py |
| test_tiny_ga_monotonic | test, pop 4 gen 2 under 30 s | tests/test_genetic_algorithm.py |
| test_json_schema | test | tests/test_genetic_algorithm.py |
| test_hand_mfs_untouched | test, regression guard | tests/test_genetic_algorithm.py |
| mfs | JSON key, six groups each centers and widths len-5 float lists | results/ga_optimized_params.json |
| fitness | JSON key, best scalar cost | results/ga_optimized_params.json |
| weights | JSON key, w1 1.0 w2 1.0 w3 0.01 | results/ga_optimized_params.json |
| train_weather | JSON key, weather/weather_profile.csv | results/ga_optimized_params.json |
| train_seed | JSON key, 7 | results/ga_optimized_params.json |
| holdout_seed | JSON key, 21 locked | results/ga_optimized_params.json |
| population | JSON key, 50 | results/ga_optimized_params.json |
| generations | JSON key, 50 | results/ga_optimized_params.json |
| rng_seed | JSON key, 0 | results/ga_optimized_params.json |
| history | JSON key, best and mean lists of length 50 | results/ga_optimized_params.json |
| notebooks/04_ga_optimization.ipynb | proof notebook, plots from artifacts only | notebooks/04_ga_optimization.ipynb |
| notebooks/04_ga_optimization.png | committed plot | notebooks/04_ga_optimization.png |
| duty-hours energy definition | locked definition, sum of duties duty-hours, must be identical in Phase 5 metrics.py | run log plus notebook verdict cell |

## Source coverage audit

| Source | Item | Covered by |
|--------|------|------------|
| GOAL | GA tunes MFs so GA fuzzy beats both baselines | Tracer holdout smoke plus full-run holdout ordering plus notebook 4-controller verdict |
| REQ GA-01 | 60-D real-valued chromosome with centers plus widths | Tracer encode/decode plus repair tests |
| REQ GA-02 | Fitness w1 IAE_T plus w2 IAE_H plus w3 energy via full sim | Tracer fitness plus hand-cost test plus duty-hours lock |
| REQ GA-03 | Tournament plus blend crossover plus gaussian mutation plus elitism | Tracer operators plus tiny-GA monotonic smoke |
| REQ GA-04 | Best chromosome saved to results/ga_optimized_params.json | Full-run task with frozen schema plus flush |
| REQ GA-05 | Same engine loading JSON params, proven on holdout | ga_fuzzy_step bit-identical delegation plus seed-21 holdout ordering |
| RESEARCH P1 | 60-D decode order plus sort/clip repair | Tracer decode plus repair invariants test |
| RESEARCH P2 | Harness reuse plus duty-hours energy plus relative-only bar | Fitness plus energy lock plus holdout ordering, no absolute threshold |
| RESEARCH P3 | Tournament-3, BLX-0.5, sigma 0.1 range, elitism-2, hand individual 0, single default_rng | Tracer operators plus run_ga init |
| RESEARCH P4 | Frozen JSON schema plus thin wrapper plus holdout seed 21 | Full-run JSON plus load_optimized_mfs validation plus isolated holdout path |
| CONTEXT D-01 | Weights 1.0 1.0 0.01 | Fitness implementation |
| CONTEXT D-02 | Budget 50 x 50 seeded | Full-run task |
| CONTEXT D-03 | Evolve seed-7, prove fresh seed 21 | Holdout smoke plus full-run holdout plus costly reversibility flag |
| CONTEXT D-04 | Full MF set both loops, rules and engine fixed | 60-D scope, no RULES change |
| CONTEXT D-05 | Notebook plus PNG from src only | Notebook task |

## Flagged assumptions (specless probe, all 7 items unresolved)

- GA-01 adjacency: when two decoded centers are exactly equal or just touch, decode keeps both after sort with no merge or dedup; equal centers simply yield overlapping triangles. Flagged, not silently dropped.
- GA-01 empty: empty, single-element, or null chromosome input is rejected by the len-60 assert in encode/decode and fitness maps it to inf rather than a partial result. Flagged, not silently dropped.
- GA-01 ordering: decode ORDER eT deT du eH deH dv is fixed and documented, and per-group centers are always stored ascending after repair; equal centers keep input-relative stability through a stable sort. Flagged, not silently dropped.
- GA-02, GA-03, GA-04, GA-05 unclassified: probe returned no classified edge beyond the three GA-01 items above; each requirement is covered by its named tests and the relative-ordering bar, and any further edge discovered during execution must be surfaced in the SUMMARY rather than assumed. Flagged, not silently dropped.
