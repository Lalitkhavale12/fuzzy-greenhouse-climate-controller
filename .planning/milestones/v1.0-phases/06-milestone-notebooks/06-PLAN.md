---
phase: 06-milestone-notebooks
plan: '01'
type: execute
wave: 1
depends_on: []
files_modified:
- tests/test_notebooks.py
- notebooks/04_ga_optimization.ipynb
- notebooks/04_ga_optimization.png
- notebooks/05_comparison.ipynb
- notebooks/05_comparison.png
- notebooks/06_final_results.ipynb
- notebooks/06_final_results.png
autonomous: true
requirements:
- PROOF-01
estimate:
  tokens: 55000
  raw_tokens: 27500
  tasks: 3
  confidence: low
must_haves:
  truths:
  - Six notebooks open front-to-back (01 plant, 02 baselines, 03 fuzzy, 04 GA,
    05 scoreboard, 06 verdict) and every one executes headless under Agg with exit 0
  - 05 scoreboard plots grouped bars for iae_T, iae_H, energy and cost plus a holdout
    cost ranking, all read from results/comparison.csv, with the printed holdout verdict
    GA below on/off AND below PID per D-02
  - 06 narrative restates the locked holdout ordering from the CSV, shows hand vs GA
    membership-function overlays, and closes with the project claim per D-03
  - 04 carries stable cell identifiers on all six cells and its PNG is regenerated at
    the uniform dpi per D-01 and D-04
  - results/comparison.csv is byte-identical before and after the phase
  - When two holdout costs compare equal, the ranking panel follows the CSV rank column
    with CSV row order as tiebreak (stable, specified output order)
  artifacts:
  - tests/test_notebooks.py
  - notebooks/04_ga_optimization.ipynb
  - notebooks/04_ga_optimization.png
  - notebooks/05_comparison.ipynb
  - notebooks/05_comparison.png
  - notebooks/06_final_results.ipynb
  - notebooks/06_final_results.png
  key_links:
  - 05/06 CSV loader asserts header equality with COLUMNS before any plot renders
  - 06 GA panel loads tuned curves through load_optimized_mfs fail-fast validation
  - Every notebook edit lands with its regenerated PNG in the same atomic commit
  prohibitions:
  - never recompute metrics in 05/06 cells (read comparison.csv)
  - never import pandas
  - never run evolution inline
  - never rewrite comparison.csv
  flagged_assumptions:
  - PROOF-01 adjacency: if two membership-function centers coincide exactly, the overlay
    draws both curves independently (no merge logic); visual overlap is acceptable
  - PROOF-01 empty: an empty holdout row filter is treated as a corrupt artifact and must
    fail loudly via assert, never render an empty figure
---

<objective>
**As a** project reviewer, **I want to** click through six notebooks with plots that prove the GA-optimized fuzzy controller beats both baselines on holdout, **so that** the proof-of-work trail is complete and reproducible end-to-end from src/.

Purpose: Finish PROOF-01 — audit-fix notebook 04 per D-01, create the 05 scoreboard visual per D-02 and the 06 end-to-end narrative per D-03, all under the D-04 uniform pattern, with zero new dependencies and zero writes to frozen artifacts.
Output: tests/test_notebooks.py audit harness, fixed 04 notebook + regenerated PNG, new 05/06 notebooks + committed PNGs. See Artifacts this phase produces.
</objective>

<execution_context>
@C:/Users/Lalit/.config/opencode/gsd-core/workflows/execute-plan.md
@C:/Users/Lalit/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/06-milestone-notebooks/06-CONTEXT.md
@.planning/phases/06-milestone-notebooks/06-RESEARCH.md
@.planning/phases/06-milestone-notebooks/06-PATTERNS.md
</context>

<tasks>

<task type="tracer">
  <name>Tracer: audit harness plus 04 uniform-pattern fixes, verified end-to-end</name>
  <files>tests/test_notebooks.py, notebooks/04_ga_optimization.ipynb, notebooks/04_ga_optimization.png</files>
  <read_first>
    tests/test_metrics.py (191 lines: docstring + in-body imports + __main__ runner convention to copy),
    notebooks/04_ga_optimization.ipynb (6 cells lacking identifiers, savefig dpi literal, duplicate stdlib import),
    notebooks/01_greenhouse_model.ipynb (identifier convention title/imports/weather/run/plot),
    06-RESEARCH.md Validation Architecture + 10-item Uniform-Pattern Audit Checklist + F-04-01/02/03,
    06-PATTERNS.md harness section + 04-fix section,
    06-CONTEXT.md D-01 per the agent's discretion on audit mechanics and D-04 per the uniform pattern
  </read_first>
  <action>Build tests/test_notebooks.py as a plain-assert suite in the test_metrics.py shape (module docstring naming PROOF-01, in-body imports, per-check probe prints, verbatim __main__ runner with repo-root sys.path prepend, runnable via python tests/test_notebooks.py with no pytest config) implementing the 10-item checklist across all six notebooks: nbformat validate warning-free, cell 0 markdown starting with hash title, every cell carrying a non-empty identifier, Agg-use index preceding pyplot import index, import allowlist of numpy/matplotlib/csv/json/os/tempfile plus src modules only, seed-7 weather-guard substring present, savefig path plus dpi literal present, PNG on disk at least 50 KB, headless exec of all code cells under Agg exiting 0, and no metric or membership math defined inside 05/06 cells with 05 making no recomputation calls. Then apply the three same-file 04 fixes per D-01: stamp identifiers title, imports, weather, verdict, verdict-note, plot on the six cells; change the plot-cell savefig dpi literal from 100 to 120; collapse the duplicate os import to the imports cell only. Regenerate notebooks/04_ga_optimization.png by headless re-execution (deterministic seeded holdout loops, expect identical verdict numbers) and commit notebook plus PNG atomically. Touch nothing in 01/02/03 (sealed, audit must pass untouched) and write nothing under results/.</action>
  <verify>
    <automated>python tests/test_notebooks.py</automated>
    <fails_when>Nonzero exit, any FAIL line, or missing all-checks-passed print</fails_when>
    <automated>python tests/test_metrics.py</automated>
    <fails_when>Nonzero exit — comparison.csv contract regressed</fails_when>
    <automated>git status --porcelain results/</automated>
    <fails_when>Any output line — frozen artifacts must stay untouched</fails_when>
  </verify>
  <acceptance_criteria>All six cells of 04 carry identifiers; savefig literal reads dpi=120; 04 PNG byte size differs from the pre-fix 173300 B and is at least 50 KB; harness passes for notebooks 01-04; metrics suite green; results/ clean.</acceptance_criteria>
  <done>Harness exists and passes on the sealed notebooks, 04 deviations F-04-01/02/03 are closed with a fresh PNG, and the full headless verification path is proven before any new notebook is authored.</done>
  <reversibility rating="reversible">Notebook-only edits plus one new test file; git revert restores all three files with no src/ impact.</reversibility>
</task>

<task type="auto">
  <name>Task 2: 05 scoreboard notebook reading the frozen CSV</name>
  <files>notebooks/05_comparison.ipynb, notebooks/05_comparison.png</files>
  <read_first>
    notebooks/01_greenhouse_model.ipynb (5-cell shape: title, imports/Agg, weather guard, run, plot plus savefig tail),
    results/comparison.csv (14-column header contract, 8 rows, holdout block GA 114.28 below on/off 513.75 and PID 645.26),
    src/metrics.py (COLUMNS contract lines 32-35),
    06-RESEARCH.md 05 Plot Specification + Pitfalls 1-3 + artifact-reader pattern,
    06-PATTERNS.md 05 section (cell order, bar display order, cost-panel scaling note),
    06-CONTEXT.md D-02 per scoreboard made visual with no live re-runs and D-04 per uniform pattern
  </read_first>
  <action>Author notebooks/05_comparison.ipynb with every cell carrying a stable identifier and code-cell outputs left empty with null execution counts, following the 01 cell shape per D-02 and D-04: markdown title cell naming the comparison milestone; imports cell with numpy, matplotlib Agg setup before pyplot, stdlib csv/os, weather-profile generator, and the COLUMNS contract import from src.metrics (stdlib csv loader only, the tabular library forbidden by 05-CONTEXT D-02 is never imported); verbatim regen-if-absent seed-7 weather-guard cell; CSV-load cell asserting the header equals COLUMNS and row count equals 8; grouped-bar plot cell with panels for iae_T, iae_H, energy and cost using controller display order onoff, pid, fuzzy, ga_fuzzy grouped by both weathers, cost panel on a log y-scale, settling rendered as a text annotation rather than bars since every value is the never-settled marker, and the rank column read directly without recomputing order; holdout verdict cell asserting relative ordering only (GA cost below on/off AND below PID on holdout-seed21) and printing the METR-02 verdict line; closing savefig cell writing notebooks/05_comparison.png at the locked dpi literal with tight layout. No cell defines new functions or types computing metrics and no cell calls the Phase-5 scoreboard builder or per-history metric kernels. Execute headless under Agg, commit notebook plus PNG atomically.</action>
  <verify>
    <automated>python tests/test_notebooks.py</automated>
    <fails_when>Nonzero exit or any FAIL line — 05 structural checks included</fails_when>
    <automated>python -c "import os; s=os.path.getsize('notebooks/05_comparison.png'); assert s>=51200, s; print('05-png-ok', s)"</automated>
    <fails_when>AssertionError or missing 05-png-ok print — PNG absent or under 50 KB</fails_when>
  </verify>
  <acceptance_criteria>05 notebook has 7 cells with cell 0 markdown title; concatenated sources contain the Agg-before-pyplot order, the seed-7 guard substring, and the savefig path with the locked dpi literal; headless exec prints the 8-row load and the holdout verdict; PNG exists at 50 KB or larger; results/ still clean.</acceptance_criteria>
  <done>05 scoreboard notebook exists, reads only the frozen CSV, plots all four locked panels plus ranking, prints the relative holdout verdict, and ships a committed PNG.</done>
  <reversibility rating="reversible">Two brand-new files; deleting them restores the prior tree exactly.</reversibility>
</task>

<task type="auto">
  <name>Task 3: 06 end-to-end narrative plus phase gate</name>
  <files>notebooks/06_final_results.ipynb, notebooks/06_final_results.png</files>
  <read_first>
    notebooks/04_ga_optimization.ipynb (artifact-load cell, relative-assert verdict cell, eH overlay plot precedent),
    results/ga_optimized_params.json (schema v2 keys, coupling gains 0.05/0.05, 50-generation history),
    src/fuzzy_controller.py (LABELS, hand FUZZY_MFS centers and widths, tri helper),
    src/ga_fuzzy_controller.py (load_optimized_mfs fail-fast validation),
    06-RESEARCH.md 06 Narrative Cell Order + before/after numbers + assumption A1 montage fallback,
    06-PATTERNS.md 06 section (10-cell order, GA-artifact load shape, verdict restatement, montage technique),
    06-CONTEXT.md D-03 per full narrative reading artifacts and D-04 per uniform pattern
  </read_first>
  <action>Author notebooks/06_final_results.ipynb with stable cell identifiers and empty code-cell outputs per D-03 and D-04 in the locked 10-cell order: markdown title Final Results naming the holdout win; imports plus Agg cell pulling csv/json/os, numpy/matplotlib, hand membership tables with labels and the triangular helper from src.fuzzy_controller, the optimized loader from src.ga_fuzzy_controller, and COLUMNS from src.metrics (no evolution entry points imported anywhere); verbatim seed-7 weather-guard cell; CSV scoreboard cell asserting header equality and 8 rows then printing the table; GA-artifact cell asserting schema version 2 with 50-by-50 population/generations then loading tuned curves through the validated loader and printing schema, fitness and coupling; verdict-restatement cell reprinting holdout costs from the CSV cell values with relative asserts only and no cost recomputation; membership before/after overlay cell plotting hand curves solid against GA curves dashed for eH at minimum using the shared triangular helper with the gains annotation; prior-trail montage cell compositing the four existing PNGs in a 2-by-2 axis-off panel via image read calls with markdown image links as fallback if headless compositing fails; closing-claim markdown cell stating the coupled GA fuzzy rank-1 holdout result on the locked weights and the structural saturation note without introducing new numbers; savefig cell writing notebooks/06_final_results.png at the locked dpi literal. Execute headless under Agg, commit notebook plus PNG atomically, then run the phase gate: harness over all six notebooks, all five existing suites sequentially, and the results/ cleanliness check.</action>
  <verify>
    <automated>python tests/test_notebooks.py</automated>
    <fails_when>Nonzero exit or any FAIL line — all six notebooks gated</fails_when>
    <automated>python tests/test_greenhouse_model.py && python tests/test_baseline_controllers.py && python tests/test_fuzzy_controller.py && python tests/test_genetic_algorithm.py && python tests/test_metrics.py</automated>
    <fails_when>Nonzero exit from any suite file — use the Phase-05 proven per-file commands verbatim</fails_when>
    <automated>git status --porcelain results/</automated>
    <fails_when>Any output line — 05/06 must never rewrite frozen artifacts</fails_when>
  </verify>
  <acceptance_criteria>Harness passes 6 of 6 notebooks; all five suites green; 06 headless exec prints the 8-row table, schema v2 load line, restated verdict, and overlay confirmation; 06 PNG exists at 50 KB or larger with the locked filename; results/ clean.</acceptance_criteria>
  <done>06 narrative exists as the reviewer-first page, all six notebooks pass the uniform audit, the full suite is green, and PROOF-01 is demonstrably complete.</done>
  <reversibility rating="reversible">Two brand-new files; deleting them restores the prior tree exactly.</reversibility>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| artifact→notebook | CSV/JSON reads cross from frozen build outputs into executable cells — validated before use |
| notebook JSON→headless runner | Notebook JSON is parsed and exec-run — schema-validated, stdlib/src imports only |
| repo→Phase-7 embed | Committed PNGs become downstream dashboard inputs — stable filenames, build outputs only |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-06-01 | Tampering | 05/06 artifact reads | high | mitigate | Fail-closed asserts before plotting: CSV header equality with COLUMNS plus 8-row count, JSON schema version 2 with 50-by-50 run shape, validated loader for tuned curves; results/ guarded by clean-tree check per D-02 per 06-RESEARCH.md Security Domain |
| T-06-02 | Tampering | notebook cell outputs | medium | mitigate | Code-cell outputs stay empty with null execution counts per 01-04 convention; proof is the committed PNG plus reproducible headless run, never embedded outputs |
| T-06-03 | Tampering / Denial of service | 05/06 compute scope | high | mitigate | Artifact-reader cells only; no evolution entry points imported in 05/06; no inline training runs; no writes under results/ per D-02 and D-03 |
| T-06-04 | Information disclosure | notebook paths | low | accept | Repo-relative paths enforced on all six notebooks; the single ephemeral temporary-directory holdout path in 04 is locked Phase-4 design and never copied into 05/06 |
| T-06-SC | Tampering | installs | high | mitigate | Zero new dependencies — stdlib plus installed numpy/matplotlib/nbformat plus src only; any task proposing another import gets a blocking human checkpoint per 06-RESEARCH.md Package Legitimacy Audit |
</threat_model>

<verification>
Harness green on all six notebooks; all five existing suites green sequentially; both new PNGs plus the regenerated 04 PNG present at 50 KB or larger; results/ tree clean; no frozen-artifact bytes changed.
</verification>

<success_criteria>
PROOF-01 holds: six notebooks each calling into src/ with plots, 04 audit deviations closed, 05 visualizes the frozen scoreboard with the relative holdout verdict, 06 narrates plant through controllers to verdict with before/after overlays, and every notebook passes the uniform-pattern audit headless.
</success_criteria>

<output>
Create `.planning/phases/06-milestone-notebooks/06-01-SUMMARY.md` when done
</output>

## Artifacts this phase produces

| File | New / Modified | Produced by | Contents |
|------|----------------|-------------|----------|
| tests/test_notebooks.py | new | Tracer task | Plain-assert audit harness implementing the 10-item uniform-pattern checklist over all six notebooks |
| notebooks/04_ga_optimization.ipynb | modified (audit fixes F-04-01 cell identifiers, F-04-02 dpi literal, F-04-03 duplicate import only) | Tracer task | Same six cells and numbers, identifiers stamped, uniform dpi |
| notebooks/04_ga_optimization.png | modified (regenerated at uniform dpi) | Tracer task | Fresh PNG committed atomically with the notebook |
| notebooks/05_comparison.ipynb | new | Task 2 | Scoreboard notebook reading results/comparison.csv only per D-02 |
| notebooks/05_comparison.png | new | Task 2 | Committed grouped-bar plus ranking figure at uniform dpi |
| notebooks/06_final_results.ipynb | new | Task 3 | End-to-end narrative reading CSV, JSON schema v2 and existing PNGs per D-03 |
| notebooks/06_final_results.png | new | Task 3 | Committed verdict plus overlay plus montage figure at uniform dpi |
