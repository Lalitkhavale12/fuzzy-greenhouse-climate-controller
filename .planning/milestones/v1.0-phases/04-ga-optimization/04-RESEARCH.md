# Phase 04: GA Optimization - Research

**Researched:** 2026-09-27
**Domain:** Real-valued genetic algorithms tuning Mamdani fuzzy membership functions (offline, NumPy-only)
**Confidence:** HIGH (in-repo contracts read + real timing and fitness-scale measurements on this machine; MEDIUM on GA operator lore cited from literature)

## Summary

Phase 4 tunes the six MF groups in `FUZZY_MFS` (60 continuous parameters: every center + width) with a from-scratch NumPy GA — tournament selection, BLX-α blend crossover, Gaussian mutation, elitism-2, seeded RNG — under a 50×50 budget. Fitness is the locked weighted cost `1.0*IAE_T + 1.0*IAE_H + 0.01*energy` evaluated by a full 1440-step closed loop per individual. The best chromosome is saved to `results/ga_optimized_params.json`, and `ga_fuzzy_controller.py` replays the identical velocity-form engine with those MFs.

Two measured facts dominate planning. First, one 1440-step fitness eval costs **~0.53 s on this machine** [VERIFIED: measured on this machine 2026-09-27, 3-run mean via `timeit` on `_run_closed_loop` + `fuzzy_step`], so 2500 evals ≈ **22 min wall + GA overhead ≈ ~25 min** — overnight-safe with huge margin, but too long for a notebook cell to compute live (run evolution as a script, plot from artifacts in the notebook). Second, on the training weather the fitness scale is **humidity-dominated ~99%**: measured weighted costs are on/off ≈ 502.7, hand-fuzzy ≈ 641.5, PID ≈ 643.3 [VERIFIED: measured on this machine 2026-09-27 against `weather/weather_profile.csv`], because IAE_H (~500–640 %RH·h) dwarfs IAE_T (~1–7 °C·h) and the energy term contributes ~0.1. The hand fuzzy controller currently **loses to on/off** on the locked weighted cost — the GA's win must come almost entirely from humidity tracking, and the pass criterion must be relative (beat baselines on the same holdout weather), never an absolute threshold.

**Primary recommendation:** Implement `src/genetic_algorithm.py` as a real-valued 60-D GA (BLX-0.5, tournament-3, per-gene Gaussian mutation σ≈0.1×range, elitism-2, hand-tuned chromosome seeded as individual 0), fitness via the existing `_run_closed_loop` harness with duty-hours energy, evolution executed as a standalone script writing JSON + history, and `src/ga_fuzzy_controller.py` as a thin JSON-loading wrapper over `fuzzy_step` proven in `notebooks/04_ga_optimization.ipynb` on a fresh holdout seed.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 — Tracking-first fitness:** `w1 = w2 = 1.0`, `w3 = 0.01` — temperature and humidity IAE dominate; energy is a tiebreaker. The GA chases the lowest tracking error first, thrift second.
- **D-02 — Large budget:** population 50 × 50 generations (~2500 full-sim fitness evals). Stronger optimum at longer runtime; still overnight-safe. Seeded RNG for reproducible reruns (D-12 determinism family).
- **D-03 — Holdout proof (GA-05):** Evolve on seed-7 weather, prove on a FRESH seed (e.g. seed-21): all four controllers (on/off, PID, hand fuzzy, GA fuzzy) run the holdout comparison on weather the GA never saw — the win must generalize, not memorize. — **Reversibility:** costly — the holdout seed anchors the core-value claim every later comparison references.
- **D-04 — Chromosome scope:** Full MF set: every center + width in `FUZZY_MFS`, both loops (T and RH) — largest search space, most tuning power for the 50×50 budget. Rule table and engine stay fixed (textbook table, velocity form — GA tunes shapes only, not structure).
- **D-05 — Proof shape:** Proof is `notebooks/04_ga_optimization.ipynb` + PNG, same pattern as Phases 1–3 (Agg headless, imports from `src/` only, no duplicated logic): convergence curve + holdout comparison traces (+ MF before/after plots, recommended). Feeds the Phase-6 notebook trail.

### Agent's Discretion
- Selection flavor (tournament vs roulette), crossover flavor (single-point vs blend), mutation sigma schedule (fixed per PROJECT.md — no adaptive rates), elitism count (1–2 per spec), exact fresh holdout seed value.
- Chromosome encode/decode mapping details within the full-MF-set scope; fitness evaluation harness shape (reuse `_run_closed_loop` family).
- Proof-notebook cell layout and plot arrangement within the D-05 pattern.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (PROJECT.md out-of-scope also binds: dynamic/adaptive GA with self-tuning population or adaptive mutation rates — fixed operators suffice [VERIFIED: .planning/PROJECT.md:38-41].)

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GA-01 | Chromosome encodes MF center/width params as real-valued or binary vector | 60-D real-valued encoding (6 vars × 10), decode order + validity repair (§ Architecture Pattern 1) |
| GA-02 | Fitness = `w1*IAE_T + w2*IAE_H + w3*energy` via full sim, lower better | Locked weights; duty-hours energy definition; `_run_closed_loop` harness reuse (§ Pattern 2); measured scale table below |
| GA-03 | Tournament/roulette selection, single-point/blend crossover, gaussian mutation, elitism 1–2 | Prescriptive operator choices: tournament-3, BLX-0.5, σ≈0.1×range, elitism-2 (§ Pattern 3) |
| GA-04 | Best chromosome saved to `results/ga_optimized_params.json` | JSON schema contract (§ Pattern 4); `results/` dir does not exist yet — Wave 0 gap |
| GA-05 | GA fuzzy controller uses same engine, loads MFs from JSON | Thin wrapper over `fuzzy_step(mfs=…)` with schema validation (§ Pattern 4); holdout protocol with fresh seed |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| GA evolution loop (selection/crossover/mutation) | `src/genetic_algorithm.py` (pure NumPy, offline) | — | Spec deliverable; no new deps (NumPy-only convention) |
| Fitness evaluation (closed-loop sim) | `src/` harness reuse (`greenhouse_model.step` + `fuzzy_controller.fuzzy_step`) | — | No duplicated logic (project constraint); identical dynamics to notebooks |
| Tuned parameters artifact | `results/ga_optimized_params.json` | — | Handoff consumed by Phase 5 (metrics) and Phase 7 (dashboard) — schema stability matters |
| GA fuzzy controller | `src/ga_fuzzy_controller.py` (thin loader + same `(state,setpoint)->(duties,state)` signature) | — | Phase 5 must score it identically to other controllers |
| Proof (convergence + holdout + MF plots) | `notebooks/04_ga_optimization.ipynb` (imports `src/`, plots from saved artifacts) | — | D-05 pattern; 25-min evolution must NOT run inside a notebook cell |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| NumPy | 2.4.3 [VERIFIED: measured `numpy.__version__` on this machine 2026-09-27] | Chromosome vectors, seeded RNG (`default_rng`), MF array ops | Project tech constraint (AGENTS.md); whole `src/` is NumPy-only; GA loop is ~100 lines — no framework needed |
| Python stdlib `json` | 3.14.6 [VERIFIED: measured `python --version` on this machine 2026-09-27] | `ga_optimized_params.json` read/write | Spec mandates JSON artifact; never pickle (see Security) |
| Matplotlib (Agg, headless) | 3.10.8 [VERIFIED: measured on this machine 2026-09-27] | Notebook convergence / holdout / MF plots + committed PNG | D-05 proof pattern used by Phases 1–3 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Jupyter (nbformat/nbclient present) | present [VERIFIED: `import jupyter, nbformat, nbclient` → `nb-ok` on this machine 2026-09-27] | Notebook proof execution | Phase-6 trail; notebook must load artifacts, not re-run evolution |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled NumPy GA | DEAP / pymoo / scikit-opt | Rejected: violates NumPy-only `src/` convention; GA-03 requires the operators implemented in `genetic_algorithm.py` (the implementation IS the deliverable); zero-dependency keeps notebooks reproducible. Do not add. |
| Real-valued chromosome | Binary/Gray encoding | Rejected: spec allows both, but real-valued avoids Hamming cliffs and decode quantization on 60 continuous params; BLX crossover is designed for real-coded GAs (Eshelman & Schaffer 1993 [CITED: https://rdrr.io/cran/adana/man/blxa.html]). Use real-valued. |
| Single-point crossover | BLX-α blend | Use BLX-0.5: single-point on a 60-D real vector swaps coordinate blocks without interpolation — disruptive with no benefit on continuous spaces; blend operators were designed for exactly this case and compared favorably on continuous tasks [CITED: https://www.cs.york.ac.uk/rts/docs/GECCO_2003/papers/2724/27241576.pdf]. |

**Installation:** none — zero new dependencies. (`pip list` shows no pytest; the plain-assert standalone suite convention already handles that [VERIFIED: tests/*.py headers state "runs standalone because pytest is not installed"].)

**Version verification:** NumPy 2.4.3, Python 3.14.6, Matplotlib 3.10.8 — all confirmed on this machine 2026-09-27 via imports (no registry lookup needed; nothing is installed by this phase).

## Package Legitimacy Audit

No external packages are installed by this phase (NumPy-only per project constraint). Audit table is intentionally empty — there is nothing to verify, and the planner must NOT add a dependency-install task.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| *(none)* | — | — | — | — | — | — |

**Packages removed due to SLOP verdict:** none.
**Packages flagged as suspicious (SUS):** none.

## Architecture Patterns

### System Architecture Diagram

```
seed-7 weather CSV ──► fitness(chromosome) ──► decode ──► MF dict ──►┐
                         ▲                                          │
                    best-per-gen                                fuzzy_step(T,rh,…,mfs) ×1440
                    history log                                     │ + greenhouse_model.step
                         │                                          ▼
                    ┌────┴─────────────────────────────────► (IAE_T, IAE_H, energy)
                    │                                               │
GA loop (50×50):    │                                         w1·+#w2·#+w3·# ──► scalar fitness
tournament-3 → BLX-0.5 → gaussian mutate → repair → elitism-2       │
                    │                                               │
                    ▼                                               │
results/ga_optimized_params.json (+ history) ◄──────────────────────┘
         │
         ▼
ga_fuzzy_controller.py ──► holdout weather (fresh seed) ──► 4-controller comparison ──► notebook PNG
```

Data-flow direction: weather + chromosome → closed-loop sim → scalar fitness → selection → next generation; the artifact JSON is the only coupling to `ga_fuzzy_controller.py` and downstream phases.

### Recommended Project Structure
```
src/
├── genetic_algorithm.py   # encode/decode+repair, fitness, operators, run_ga()  (NEW, GA-01..03)
├── ga_fuzzy_controller.py # load JSON -> mfs dict -> fuzzy_step wrapper          (NEW, GA-05)
├── fuzzy_controller.py    # READ-ONLY engine (never mutated in place)            (exists)
├── greenhouse_model.py    # step(), load_weather_profile()                       (exists)
└── weather_profile_generator.py  # generate_weather_profile(out, seed)           (exists)
results/
└── ga_optimized_params.json      # handoff artifact (code must mkdir -p)        (NEW, GA-04)
tests/
└── test_genetic_algorithm.py     # plain-assert suite, fast-budget GA smoke     (NEW)
notebooks/
└── 04_ga_optimization.ipynb + .png  # plots from saved artifacts only           (NEW, D-05)
```

### Pattern 1: Real-valued 60-D chromosome with validity repair
**What:** Chromosome is a flat `np.ndarray` of length 60 = 6 MF groups × (5 centers + 5 widths), decoded in fixed key order `["eT","deT","du","eH","deH","dv"]` [ASSUMED ordering — planner's choice, but it must be fixed and documented; the key set itself is verified below]. Decode builds **fresh dicts with copied arrays** (never views into shared state). Repair after crossover/mutation: (1) sort each center array ascending, (2) clip centers to the variable's universe, (3) clip widths to `[w_min, w_max]` with `w_min > 0`.
**When to use:** Every decode — operators routinely produce unordered centers and non-positive widths.
**Why:** `infer()` clips inputs to `[EC[0], EC[-1]]` [VERIFIED: src/fuzzy_controller.py:47-48] — quote: `mu_e = np.array([tri(np.clip(e, EC[0], EC[-1]), c, w) for c, w in zip(EC, EW)])` — so unsorted centers silently corrupt the clipping interval; and `tri()` divides by `w` [VERIFIED: src/fuzzy_controller.py:40-42] — quote: `return float(np.clip(1.0 - abs(float(x) - c) / w, 0.0, 1.0))` — so `w = 0` raises `ZeroDivisionError` and `w < 0` inverts the triangle. Repair-then-evaluate is the standard practice for evolved fuzzy partitions (operators must be followed by a repair guaranteeing coverage [CITED: http://74.207.227.126/sites/ericantonelo.com/files/2005_calvo_cira.pdf]).
**Chromosome dimensionality proof:** `FUZZY_MFS` has exactly the six keys with 5 centers + 5 widths each [VERIFIED: src/fuzzy_controller.py:20-29] — quote:
```
"eT":  {"centers": np.array([-4., -2., 0., 2., 4.]),       "widths": np.full(5, 2.0)},
"deT": {"centers": np.array([-0.5, -0.25, 0., 0.25, 0.5]), "widths": np.full(5, 0.25)},  # C/min
"du":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},  # duty/step
"eH":  {"centers": np.array([-30., -15., 0., 15., 30.]),   "widths": np.full(5, 15.0)},
"deH": {"centers": np.array([-6., -3., 0., 3., 6.]),       "widths": np.full(5, 3.0)},   # %RH/min
"dv":  {"centers": np.array([-0.1, -0.05, 0., 0.05, 0.1]), "widths": np.full(5, 0.05)},
```
Universe bounds for repair derive from these hand spans (e.g. eT centers clip to [-4,4] widened by a margin such as ±50% [ASSUMED margin — planner fixes the exact padding]; `RULES` is fixed and untouched [VERIFIED: src/fuzzy_controller.py:31-37]).

**Example:**
```python
# Source: pattern derived from src/fuzzy_controller.py structures (Read this session)
ORDER = ["eT", "deT", "du", "eH", "deH", "dv"]
BOUNDS = {  # (center_lo, center_hi, w_min, w_max) per variable [ASSUMED paddings]
    "eT": (-6.0, 6.0, 0.2, 6.0), "deT": (-0.75, 0.75, 0.025, 0.75),
    "du": (-0.15, 0.15, 0.005, 0.15), "eH": (-40.0, 40.0, 1.5, 40.0),
    "deH": (-9.0, 9.0, 0.3, 9.0), "dv": (-0.15, 0.15, 0.005, 0.15),
}
def decode(chrom):
    mfs, i = {}, 0
    for k in ORDER:
        c = np.sort(np.clip(chrom[i:i+5], *BOUNDS[k][:2])); i += 5
        w = np.clip(chrom[i:i+5], BOUNDS[k][2], BOUNDS[k][3]); i += 5
        mfs[k] = {"centers": np.array(c), "widths": np.array(w)}
    return mfs  # fresh dict, fresh arrays — FUZZY_MFS global never touched
```

### Pattern 2: Fitness harness = `_run_closed_loop` reuse + duty-hours energy
**What:** Fitness decodes the chromosome, runs the identical 1440-step closed loop as the test suites (weather interpolated to 1-min, `dt=60.0`, initial `T=20.0, w=0.65*wsat(20)`), accumulates `IAE_T = Σ|T−T_sp|/60`, `IAE_H = Σ|RH−RH_sp|/60`, `E = Σ_steps Σ_actuators duty/60` (duty-hours), returns `1.0*IAE_T + 1.0*IAE_H + 0.01*E`.
**When to use:** Every fitness call; the same function (parameterized by weather arrays + `mfs`) serves evolution, holdout, and notebook comparisons.
**Scale reference (locked weights; lower better) — measured on training weather this session [VERIFIED: measured on this machine 2026-09-27]:**

| Controller | IAE_T (°C·h) | IAE_H (%RH·h) | E (duty-h) | Weighted cost |
|------------|-------------|--------------|-----------|---------------|
| on/off | 7.38 | 495.22 | 13.77 | **≈502.7** ← bar to beat |
| hand fuzzy | 2.68 | 638.77 | 9.43 | ≈641.5 |
| PID | 1.08 | 642.07 | 9.60 | ≈643.3 |

Consequences the planner must encode: (a) humidity is ~99% of fitness — T-IAE and energy differences are rounding noise at these weights (locked D-01, not re-litigated); (b) hand fuzzy currently *loses* to on/off — the GA must recover on/off-like humidity authority (bang-bang fogger/vent switching) while keeping T tight; (c) pass criterion must be *relative* (GA cost < on/off cost < PID/hand-fuzzy on the same holdout weather), never an absolute number, because absolute scale is weather-dependent.
**Energy definition rationale:** sum-of-duties duty-hours is the simplest choice consistent with `step()`'s actuator contract (`{"heater","fan_cooler","fogger","vent"}` duties in [0,1] [VERIFIED: src/greenhouse_model.py:58-65]) and with the controller emission contract (all duties in [0,1] [VERIFIED: src/fuzzy_controller.py:87-89] — quote: `heat, cool = (u, 0.0) if u > 0 else (0.0, -u)` … `return ({'heater': heat, 'fan_cooler': cool, 'fogger': v, 'vent': cool}, st)`). A power-weighted alternative (P_h=100, P_fan=200, P_fog=20 W/m³ [VERIFIED: src/greenhouse_model.py:16-29]) is [ASSUMED] viable but vent has no power param and Phase 5 `metrics.py` must agree — planner must lock one definition and keep Phase 5 identical (recommend sum-of-duties).

### Pattern 3: Fixed operators for the 60-D continuous space
**What:** Tournament selection (size 3), BLX-0.5 blend crossover (per-gene uniform pick in `[min−α·d, max+α·d]`, α=0.5), per-gene Gaussian mutation (each gene mutated independently with prob ≈1/60, σ≈0.1× that gene's allowed range), elitism-2 (copy best 2 unchanged), all draws from `np.random.default_rng(seed)`; fixed rates throughout (no adaptation — PROJECT.md out-of-scope).
**When to use:** The whole 50×50 run; log best/mean per generation for the convergence plot.
**Why these values [ASSUMED unless cited]:** tournament-3 is the standard middle ground (size 2 drifts, 5+ converges prematurely on multimodal landscapes); BLX-0.5 is the canonical real-coded operator (Eshelman & Schaffer 1993 [CITED: https://rdrr.io/cran/adana/man/blxa.html]) and blend-class operators were built for continuous spaces where point crossovers only shuffle coordinates [CITED: https://www.cs.york.ac.uk/rts/docs/GECCO_2003/papers/2724/27241576.pdf]; σ≈0.1×range with ~1 mutation per chromosome per generation is the textbook starting point for 50–100-D continuous GAs; elitism-2 matches the spec's "top 1-2" and, combined with seeding individual 0 as the hand-tuned chromosome, *guarantees* the GA never returns worse than hand fuzzy. Population init: individual 0 = exact hand `FUZZY_MFS` encoding, remaining 49 = hand values × (1 + U(−0.2, 0.2)) then repaired [ASSUMED spread — planner fixes exact value; ±20% keeps the search in the stable-tracking neighborhood proven by Phase 3].

### Pattern 4: JSON artifact schema + thin controller wrapper
**What:** `run_ga()` writes `results/ga_optimized_params.json` with this schema (extra keys allowed, listed keys required):
```json
{"mfs": {"eT": {"centers": [5 floats], "widths": [5 floats]}, "deT": {...}, "du": {...}, "eH": {...}, "deH": {...}, "dv": {...}},
 "fitness": 0.0, "weights": {"w1": 1.0, "w2": 1.0, "w3": 0.01},
 "train_weather": "weather/weather_profile.csv", "train_seed": 7, "holdout_seed": 21,
 "population": 50, "generations": 50, "rng_seed": 0,
 "history": {"best": [50 floats], "mean": [50 floats]}}
```
`ga_fuzzy_controller.py` exposes `load_optimized_mfs(path)` (validates: exact key set, len-5 float lists, widths>0, all finite — fail-fast asserts per project convention) and `ga_fuzzy_step(T_C, rh_pct, T_sp, RH_sp, state, dt)` which lazily loads once and delegates to `fuzzy_step(..., mfs=_MFS)` [VERIFIED injectable: `fuzzy_step` signature ends `mfs=FUZZY_MFS` — src/fuzzy_controller.py:63]. Same `(duties, state)` signature as every other controller so Phase 5 scores it identically.
**When to use:** Schema is frozen at Phase 4 — Phase 5 (`metrics.py`) and Phase 7 (dashboard GA explorer) consume it.

### Anti-Patterns to Avoid
- **Evolving inside the notebook:** a 25-min cell will time out, lose the kernel, or tempt a shrunk budget that invalidates D-02. Evolve via script; notebook loads JSON + history and plots only.
- **Mutating the `FUZZY_MFS` global:** module docstring mandates read-only ("never mutated — Phase 4 GA passes mutated copies" [VERIFIED: src/fuzzy_controller.py:11-13]). Decode must allocate; a single in-place write poisons every later comparison in the process.
- **Holdout leakage:** any read of holdout weather (or its seed's RNG stream) before the final comparison invalidates GA-05. Generate holdout with `generate_weather_profile(out_path, seed=...)` [VERIFIED: src/weather_profile_generator.py:15-17] only at proof time, on a path never passed to fitness.
- **Absolute fitness thresholds:** weather-dependent and humidity-dominated (see scale table) — assert relative ordering on shared weather instead.
- **Adaptive schedules:** PROJECT.md explicitly out-of-scopes self-tuning population/mutation — fixed operators are a compliance matter, not just taste.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| GA framework (selection/crossover/mutation infra) | DEAP / pymoo dependency | ~100-line NumPy GA in `genetic_algorithm.py` | GA-03 requires the operators implemented in-repo; NumPy-only `src/` convention; zero-dep reproducibility for notebooks |
| Seeded RNG | `random` module / `np.random.seed()` global | `np.random.default_rng(seed)` per run, seed stored in JSON | Global seeding is process-fragile; `default_rng` streams are isolated and reproducible (D-12 determinism family); generator already uses it [VERIFIED: src/weather_profile_generator.py:18] — quote: `rng = np.random.default_rng(seed)` |
| Weather interpolation in fitness | Custom resampler | `np.interp(hours, t_min, T_out)` pattern from test harnesses | Byte-identical dynamics to Phases 1–3 proofs; `_run_closed_loop` in tests interpolates 15-min CSV rows to 1-min steps [VERIFIED: tests/test_fuzzy_controller.py:11-30] |
| Triangular MF math | Custom MF shapes (Gaussian/bell) | Existing `tri()` + `infer()` via `fuzzy_step(mfs=…)` | Engine fixed per D-04; tuning shapes means tuning center/width params, not replacing the function |

**Key insight:** The only thing Phase 4 invents is the 60-D encode/decode + GA loop; plant dynamics, inference math, harness loop, and weather generation all exist and must be reused verbatim so every number stays comparable across phases.

## Common Pitfalls

### Pitfall 1: Humidity dominance surprises the pass criterion
**What goes wrong:** Plan asserts "GA beats baselines on temperature" or an absolute cost number; GA improves T-IAE 2.68→1.0 (a real win) yet weighted cost barely moves because IAE_H ≈ 640 dominates.
**Why it happens:** Locked w1=w2=1.0 with IAE_H ~100× IAE_T in magnitude (measured table above).
**How to avoid:** Relative pass criterion on shared holdout weather: `cost(GA) < cost(onoff) < …`; report per-term breakdown (IAE_T, IAE_H, E) in the notebook so the T-win is visible even when humidity decides the total.
**Warning signs:** Any plan sentence with an absolute cost threshold.

### Pitfall 2: Notebook-timeout evolution
**What goes wrong:** 25-min evolution cell dies mid-run; no JSON, no history, phase unverifiable.
**Why it happens:** 0.53 s/eval × 2500 ≈ 22 min + overhead [VERIFIED: measured], far beyond comfortable notebook cell lifetimes.
**How to avoid:** `genetic_algorithm.py` runnable as a script (`python src/genetic_algorithm.py --pop 50 --gen 50 --seed …` or equivalent entry) writing JSON + history incrementally (flush best-so-far each generation so a killed run still yields an artifact); notebook cells only load + plot. Keep a tiny-budget smoke path (pop 4 × gen 2) for tests.
**Warning signs:** Notebook containing `run_ga(population=50, ...)` in an executed cell.

### Pitfall 3: Degenerate MFs (zero/negative widths, unordered centers)
**What goes wrong:** `ZeroDivisionError` (w=0 in `tri`), inverted triangles (w<0), or silently shifted clipping intervals (unsorted centers vs `infer`'s `[EC[0], EC[-1]]` clip).
**Why it happens:** Blend crossover + Gaussian mutation know nothing about MF semantics.
**How to avoid:** Mandatory repair-on-decode (Pattern 1) + a unit test decoding random chromosomes (assert sorted centers, widths ≥ w_min, all finite, sim completes).
**Warning signs:** `decode` without `np.sort`/`np.clip`; fitness NaN crashes instead of penalized returns.

### Pitfall 4: Unpenalized fitness exceptions break the run
**What goes wrong:** One bad chromosome raises inside generation 3; the whole 25-min run dies.
**Why it happens:** `fuzzy_step`/`step` fail-fast on NaN and out-of-range duties (asserts [VERIFIED: src/fuzzy_controller.py:65-70; src/greenhouse_model.py:62-67]).
**How to avoid:** `try/except` inside fitness → return `inf` (or a large penalty) on any exception; add an assertion counter logged per generation. Never let fitness raise.
**Warning signs:** Bare `fitness()` call in the hot loop without exception guard.

### Pitfall 5: In-place aliasing of MF arrays
**What goes wrong:** `decode` returns views into the chromosome or the global; mutation later corrupts saved "best" or the hand baseline mid-run.
**Why it happens:** NumPy slicing views + mutable dict-of-arrays.
**How to avoid:** `np.array(...)` copies on every decode; `copy.deepcopy`-equivalent when snapshotting best; test asserts hand `FUZZY_MFS` arrays are bit-identical before/after a GA smoke run.
**Warning signs:** `mfs[k] = {"centers": chrom[i:i+5], …}` without copy.

### Pitfall 6: RNG indiscipline breaks reproducibility (D-12)
**What goes wrong:** Rerun with the same seed gives a different JSON; holdout claim unreproducible.
**Why it happens:** Unseeded draws, `np.random.seed` global clobbered by another import, or weather regenerated with a different seed mid-experiment.
**How to avoid:** Single `default_rng(rng_seed)` owned by `run_ga`; all operator draws through it; record `rng_seed`, `train_seed`, package versions in JSON; train weather file treated as immutable input (never regenerate seed-7 weather during the phase).
**Warning signs:** Any `np.random.*` global-API call in new code.

## Code Examples

### Fitness harness (reuse of `_run_closed_loop` shape)
```python
# Source: adapted from tests/test_fuzzy_controller.py:11-30 (Read this session)
def evaluate(chrom, T_out_hr, w_out_hr, hours, T_sp=25.0, RH_sp=70.0):
    from src.greenhouse_model import step, daytime_solar, params, relative_humidity, wsat_g_per_kg
    from src.fuzzy_controller import fuzzy_step
    try:
        mfs = decode(chrom)  # Pattern 1: repaired fresh dict
        T, w = 20.0, 0.65 * wsat_g_per_kg(20.0)
        st, iae_T, iae_H, E = None, 0.0, 0.0, 0.0
        for i, h in enumerate(hours):  # 1440 steps, dt=60.0
            rh = relative_humidity(w, T)
            act, st = fuzzy_step(T, rh, T_sp, RH_sp, st, 60.0, mfs)
            T, w, rh = step(60.0, act, (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"])), T, w)
            iae_T += abs(T - T_sp) / 60.0
            iae_H += abs(rh - RH_sp) / 60.0
            E += sum(act.values()) / 60.0  # duty-hours
        cost = 1.0 * iae_T + 1.0 * iae_H + 0.01 * E
        assert np.isfinite(cost)
        return cost
    except Exception:
        return float("inf")  # Pitfall 4: never raise out of fitness
```

### BLX-0.5 crossover + tournament-3 + Gaussian mutation
```python
# Source: operator structure per Eshelman & Schaffer 1993 BLX-alpha
# [CITED: https://rdrr.io/cran/adana/man/blxa.html]; sizes [ASSUMED] per §Pattern 3
def tournament_select(pop, fit, rng, k=3):
    idx = rng.choice(len(pop), size=k, replace=False)
    return pop[idx[np.argmin(fit[idx])]].copy()

def blx_alpha(p1, p2, rng, alpha=0.5):
    d = np.abs(p1 - p2)
    lo = np.minimum(p1, p2) - alpha * d
    hi = np.maximum(p1, p2) + alpha * d
    return rng.uniform(lo, hi)  # repair/clip applied in decode()

def gaussian_mutate(child, rng, p_gene=1.0/60.0, ranges=None):
    mask = rng.random(child.size) < p_gene
    child[mask] += rng.normal(0.0, 1.0, mask.sum()) * ranges[mask]
    return child  # ranges = 0.1 * (center_hi - center_lo) per gene [ASSUMED]
```

### Seeded evolution entry + incremental artifact
```python
# Source: project conventions (seeded determinism D-12; atomic artifacts)
def run_ga(population=50, generations=50, rng_seed=0, train_weather="weather/weather_profile.csv"):
    rng = np.random.default_rng(rng_seed)
    pop = init_population(rng, population)  # [0] = hand encoding, rest ±20% [ASSUMED]
    ...  # elitism-2 generational loop; flush JSON (best + history) every generation
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Binary/Gray chromosome for MF params | Real-valued chromosome + blend crossover | 1990s (Eshelman & Schaffer 1993) | No quantization/Hamming cliffs on continuous params; GA-01 allows both — use real-valued |
| Roulette-wheel selection | Tournament selection (size 2–5) | 1990s–2000s practice | Constant selection pressure, no fitness-scaling pathology on minimization with ~500-scale costs |
| Hand-tuned fuzzy only | GA-tuned MF shapes, fixed rules | This phase (MATLAB's fuzzy tuner uses GA methods for MF params [CITED: https://www.mathworks.com/help/fuzzy/fuzzy-inference-system-tuning.html]) | Rules stay textbook; shapes carry the optimization |

**Deprecated/outdated:**
- Single-point crossover on real vectors: shuffles coordinate blocks without interpolation — superseded by blend/SBX operators for continuous spaces.
- Adaptive/self-tuning GA rates: explicitly out-of-scope per PROJECT.md — do not implement regardless of literature appeal.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | BLX-0.5 / tournament-3 / σ≈0.1×range / elitism-2 suit this 60-D space (textbook defaults, not tuned here) | Pattern 3 | Low — any reasonable fixed operator converges given 50×50 + hand seeding; planner may swap flavors within discretion |
| A2 | ±20% hand-value init spread; BOUNDS paddings (±50% beyond hand spans); p_gene=1/60 | Patterns 1, 3 | Low — repair clips extremes; smoke test validates stability |
| A3 | Sum-of-duties duty-hours energy; Phase 5 must use the identical definition | Pattern 2 | Medium — cross-phase mismatch would silently shift comparisons; planner must lock and propagate |
| A4 | Holdout seed 21 (CONTEXT's example) | Pattern 4 / Validation | Low — any fresh seed works; but the chosen value is costly-reversible once published |
| A5 | ~25-min wall clock extrapolates from 0.53 s/eval (GA overhead small) | Pitfall 2 | Low — even 2× overhead stays overnight-safe |
| A6 | `weather/weather_profile.csv` is the seed-7 training weather (per CONTEXT canonical refs) | Pattern 2 | Medium — if it is a different seed, "evolve on seed-7" needs a regeneration step; planner should verify provenance before evolving |

## Open Questions

1. **Exact holdout seed value**
   - What we know: Must be fresh (never seen by fitness); CONTEXT suggests e.g. 21; generator is one call: `generate_weather_profile(out_path, seed=…)` [VERIFIED: src/weather_profile_generator.py:15-26].
   - What's unclear: Final pick (agent's discretion).
   - Recommendation: Lock `holdout_seed=21`, holdout path outside `weather/` training set (e.g. `weather/holdout_seed21.csv` [ASSUMED path]), record in JSON, never change after first holdout run.

2. **Full 50×50 vs. staged budget**
   - What we know: D-02 locks 50×50 (~25 min, safe).
   - What's unclear: Whether executor hardware matches this machine's 0.53 s/eval.
   - Recommendation: Planner adds a first task measuring per-eval time on the execution machine and aborts/re-plans only if >5× slower (then reduce generations, never population breadth first — [ASSUMED] prioritization).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All `src/` | ✓ | 3.14.6 | — |
| NumPy | GA + sim | ✓ | 2.4.3 | — |
| Matplotlib (Agg) | Notebook PNGs | ✓ | 3.10.8 | — |
| Jupyter/nbformat/nbclient | Proof notebook | ✓ | present | — |
| pytest | Test runs | ✗ | — | Plain-assert standalone convention (established in tests/*.py headers) |
| `results/` directory | GA-04 artifact | ✗ | — | Wave 0: code must `mkdir -p` (see Validation) |
| Streamlit | — (Phase 7, not this phase) | ✗ (broken: `google.protobuf` missing) | — | Irrelevant now; flag for Phase 7 |

**Missing dependencies with no fallback:** none for this phase.
**Missing dependencies with fallback:** pytest → standalone `python tests/test_*.py` (existing convention).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Plain-assert standalone scripts (no pytest — not installed); `python tests/test_X.py`, exit 1 on failure |
| Config file | none — see Wave 0 |
| Quick run command | `python tests/test_genetic_algorithm.py` (<30 s via tiny-budget smoke) |
| Full suite command | `python tests/test_greenhouse_model.py; python tests/test_baseline_controllers.py; python tests/test_fuzzy_controller.py; python tests/test_genetic_algorithm.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GA-01 | Encode hand MFs → decode → bit-identical MFs; random chromosomes decode to sorted centers, widths ≥ w_min, all finite | unit | `python tests/test_genetic_algorithm.py` (test_encode_decode_roundtrip, test_decode_repair_invariants) | ❌ Wave 0 |
| GA-02 | Fitness(hand chromosome) is finite and ≈ hand-fuzzy weighted cost (~641.5 on train weather); fitness never raises (bad chromosome → inf) | unit | same file (test_fitness_matches_hand_cost, test_fitness_never_raises) | ❌ Wave 0 |
| GA-03 | Tiny GA (pop 4 × gen 2, seeded) converges monotonically (elitism: best never worsens), finishes <30 s | smoke | same file (test_tiny_ga_monotonic) | ❌ Wave 0 |
| GA-04 | `run_ga` smoke writes schema-valid JSON (exact key set, len-5 lists, widths>0, finite; history lengths = generations) | unit | same file (test_json_schema) | ❌ Wave 0 |
| GA-05 | `ga_fuzzy_step` loads JSON, matches `fuzzy_step(mfs=…)` bit-identically; holdout run: GA cost < onoff cost on shared fresh weather (relative ordering, structural `nb-ok + png-ok` for the notebook) | integration + notebook-proof | `python tests/test_genetic_algorithm.py` + notebook structural check | ❌ Wave 0 |
| Regression | Hand `FUZZY_MFS` bit-identical before/after GA smoke (no global mutation) | unit | same file (test_hand_mfs_untouched) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python tests/test_genetic_algorithm.py`
- **Per wave merge:** full suite command above
- **Phase gate:** Full suite green + `notebooks/04_ga_optimization.ipynb` executes headless with committed PNG before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_genetic_algorithm.py` — covers GA-01..05 + regression guards above
- [ ] `results/` directory bootstrap (`mkdir -p` in `run_ga`; do not commit empty dir reliance)
- [ ] Framework install: none (standalone convention; no pytest)
- [ ] Baselines reference on train weather: on/off 7.38 / PID 1.08 / hand-fuzzy 2.68 T-IAE (from CONTEXT; T-IAE + energy reproduced this session, full IAE_H table in §Pattern 2)

## Security Domain

Surface: local pure functions + JSON artifact + notebook. No network, no credentials, no user input, no elevated execution. ASVS L1 posture is proportionally minimal, but the four applicable patterns must be planned as tasks, not assumed.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local offline computation; no users or sessions |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Single-user academic artifact; file permissions default |
| V5 Input Validation | **yes** | `load_optimized_mfs`: assert exact key set/lengths/finite/widths>0; `decode`: clip+sort repair; fitness exception→inf |
| V6 Cryptography | no | No secrets; RNG is reproducibility-seed, not security-seed |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| NaN poisoning via crafted JSON (e.g. hand-edited `centers: [NaN,…]` → silent sim corruption; `fuzzy_step` asserts would kill a 25-min run mid-loop) | Tampering | Schema-validate on load (finite/widths>0/key-set asserts, fail-fast at load time, never in the hot loop); fitness `try/except → inf` as second layer |
| Unsafe deserialization (pickle/npy `allow_pickle` on the artifact path) | Tampering | JSON-only via stdlib `json` (no `pickle`, no `eval`, no `exec` on file contents); notebook never executes artifact contents |
| RNG seed confusion (train/holdout seed swap or unseeded run silently invalidates the GA-05 generalization claim) | Repudiation | Single `default_rng(rng_seed)` owned by `run_ga`; `train_seed`/`holdout_seed`/`rng_seed` recorded in JSON; holdout file on an isolated path generated once |
| Supply chain (new optimizer dependency typosquat / postinstall risk) | Tampering | No new dependencies — NumPy-only; planner must reject any task adding a package |

## Sources

### Primary (HIGH confidence)
- `src/fuzzy_controller.py:20-89` (Read this session) — FUZZY_MFS values, RULES table, `tri`/`infer`/`fuzzy_step` semantics, read-only convention
- `src/greenhouse_model.py:16-65` (Read this session) — params incl. actuator powers, actuator-key contract, duty bounds
- `src/weather_profile_generator.py:15-26` (Read this session) — `generate_weather_profile(out_path, seed)` + `default_rng(seed)` pattern
- `tests/test_fuzzy_controller.py:11-30`, `tests/test_baseline_controllers.py:11-30` (Read this session) — `_run_closed_loop` harness shape, determinism/NaN conventions
- This-machine measurements 2026-09-27: 0.53 s/eval (timeit, n=3); IAE/energy scale table; Python 3.14.6 / NumPy 2.4.3 / Matplotlib 3.10.8 / jupyter-present / pytest-absent / `results/`-absent

### Secondary (MEDIUM confidence)
- Eshelman & Schaffer (1993) BLX-α via adana docs [CITED: https://rdrr.io/cran/adana/man/blxa.html] — blend crossover for real-coded GAs
- GECCO 2003 crossover comparison (1PX/2PX/uniform vs LX/BLX-0.5) [CITED: https://www.cs.york.ac.uk/rts/docs/GECCO_2003/papers/2724/27241576.pdf]
- Calvo CIRA-2005 fuzzy-system GA (MF param encoding + post-operator repair) [CITED: http://74.207.227.126/sites/ericantonelo.com/files/2005_calvo_cira.pdf]
- MATLAB fuzzy inference system tuning with GA methods [CITED: https://www.mathworks.com/help/fuzzy/fuzzy-inference-system-tuning.html]

### Tertiary (LOW confidence)
- Tournament-3 / σ≈0.1×range / ±20% init / BOUNDS paddings — textbook defaults from training knowledge, tagged [ASSUMED] inline; safe because elitism + hand seeding bounds the downside

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — measured versions on this machine; zero installs
- Architecture: HIGH — contracts read verbatim; fitness scale + timing measured in-situ
- Pitfalls: HIGH for scale/timeout/validity risks (measured or code-derived); MEDIUM for operator lore (literature-cited)

**Research date:** 2026-09-27
**Valid until:** ~30 days (stable domain: textbook GA + frozen in-repo contracts; re-measure timing only if execution hardware changes)

**Project Constraints (from AGENTS.md):** Tech = Python 3 + NumPy (+ Streamlit for dashboard phases only); Matplotlib plotting in notebooks; CSV weather input, JSON GA params; hand-fuzzy-before-GA order (satisfied — Phase 3 complete); notebooks import from `src/` with no duplicated logic. No project skills registered. These are honored above (NumPy-only, no new deps, harness reuse, script-not-notebook evolution).
