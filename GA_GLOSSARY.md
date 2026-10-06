# Genetic Algorithm Glossary — Soft Computing Context

Every GA-related term used in this project, defined first in general soft
computing language, then pinned to exactly what it is here
(file, symbol, and value where applicable).

## 0. Why this is "soft computing"

Soft computing tolerates imprecision and approximation to solve problems
that are hard for exact methods. This project pairs its two flagship
families: **fuzzy logic** (reasons with linguistic grades of truth instead
of true/false) and a **genetic algorithm** (searches by evolution instead
of gradients). The fuzzy controller handles the greenhouse; the GA tunes
the fuzzy controller. No neural networks are used — that third family is
deliberately out of scope.

## 1. The GA core (src/genetic_algorithm.py)

- **Chromosome** — one complete candidate solution encoded as a vector.
  Here: a flat 62-element float vector (`CHROM_LEN = 60 + 2`).
- **Gene** — one position in the chromosome. Here: one MF center, one MF
  width, or one coupling gain (62 genes total).
- **Allele / gene value** — the number stored at a gene position. Always a
  float here (real-valued encoding, never binary strings).
- **MF groups (the 60 MF genes)** — the chromosome's first 60 genes are 6
  fuzzy groups in `ORDER` (`eT, deT, du, eH, deH, dv`), each stored as
  5 centers then 5 widths.
- **Coupling gains (the last 2 genes)** — `k_heat` and `k_vent`
  (duty-per-%RH-excess boosts). Appended after the MF genes (the D-06/A2
  extension); zero gains mean "decoupled", i.e. hand-equivalent behavior.
- **BOUNDS** — the legal box each gene lives in, e.g. eT centers in
  `[-6, 6]`, widths kept strictly above zero (because `tri()` divides by
  width). Decode clips every gene into these bounds.
- **COUPLING_BOUNDS** — gains clipped into `[0.0, 0.05]` each.
- **Population** — the set of chromosomes competing in one generation.
  Default 50 (`run_ga(population=50, ...)`).
- **Individual** — one member of the population (one 62-vector).
- **Individual 0** — the exact hand-tuned `FUZZY_MFS` encoding with zero
  gains, always present. Guarantees the GA never returns worse than hand
  fuzzy, since elitism can always keep it.
- **Fitness** — the score being minimized (lower is better). The plan
  calls it "fitness"; the code calls it `evaluate()` (`fitness` is an
  alias). Equals the locked weighted cost on the coupled path; a broken
  chromosome scores `+inf` instead of raising, so evolution never crashes.
- **Locked weights (W1, W2, W3 = 1.0, 1.0, 0.01)** — fitness is
  `1.0*IAE_T + 1.0*IAE_H + 0.01*energy`. Locked means asserted, not just
  documented: any other weights raise.
- **Generation** — one evolve-and-replace cycle. Default 50; the frozen
  artifact's history arrays are exactly 50 long (`GEN_COUNT = 50`).
- **Selection (tournament-3)** — `tournament_select` draws 3 individuals at
  random and copies the fittest. Small tournaments keep weak individuals
  occasionally alive, preserving diversity.
- **Crossover (BLX-0.5)** — `blx_alpha` picks each child gene uniformly
  from a box stretched 50% (`alpha=0.5`) beyond the parents' interval.
  Unlike single-point crossover it blends real values instead of swapping
  segments.
- **Mutation (gaussian)** — `gaussian_mutate` adds N(0,1) noise scaled per
  gene, each gene mutated with probability `p_gene = 1/62` (about one gene
  per child on average).
- **Sigma (mutation step size)** — per-gene noise scale = 10% of that
  gene's allowed range (`_sigmas()`), so wide-range and narrow-range genes
  explore proportionally.
- **Elitism-2** — the 2 fittest individuals pass unchanged into the next
  generation (`n_elite = min(2, population)`). This is what makes best
  fitness monotonically non-worsening.
- **Encode** — MF dict (+ gains) → 62-vector. Used to seed individual 0.
- **Decode (+ repair)** — 62-vector → fresh MF/gain dicts. Repair means:
  sort-and-clip centers, clip widths, clip gains. Accepts legacy len-60
  vectors (gains default to 0.0). Never returns views and never touches
  the `FUZZY_MFS` global.
- **RNG seed** — the single `np.random.default_rng(rng_seed)` owned by
  `run_ga`; every draw (init, tournament, crossover, mutation) flows
  through it, so a run is exactly reproducible. Default seed 0.
- **Initialization (jitter)** — individuals 1..49 are the hand encoding
  plus ±20% uniform jitter (`rng.uniform(-0.2, 0.2, 60)`), additive rather
  than multiplicative so the exact-0.0 ZO centers can still move; gains
  are drawn uniform over their bounds so coupling is explored from gen 0.
- **Convergence** — best fitness flattening over generations. The artifact
  records `history.best` and `history.mean` per generation; the dashboard
  replays them.
- **Exploration vs exploitation** — the GA's core tension: mutation and
  wide BLX boxes explore new regions; elitism and tournament selection
  exploit known-good ones.
- **Premature convergence** — the population collapsing onto a mediocre
  solution early. Countered here by tournament (not winner-take-all)
  selection, per-gene mutation, and the guaranteed-diverse init.
- **Train vs holdout** — evolution scores on seed-7 weather only
  (`train_weather`); the frozen seed-21 file judges generalization
  (`holdout_seed`). Both seeds are provenance labels in the JSON.
- **Schema v1 vs v2** — v1 artifacts (run-1/run-2) hold only MFs;
  v2 adds the `"coupling"` gains. The loader still accepts v1, defaulting
  gains to zero.

## 2. The fuzzy controller being tuned (src/fuzzy_controller.py)

- **Mamdani inference** — the fuzzy reasoning style used: rules fire with
  min-implication, outputs aggregate with max, then defuzzify. (The
  alternative, Sugeno, skips defuzzification — not used here.)
- **Linguistic variable / term** — variables like error `eT` described in
  words: NB (negative big), NS, ZO (zero), PS, PB (positive big) — 5 terms
  per variable (FUZZ-02).
- **Membership function (MF)** — the triangle mapping a crisp number to a
  0..1 degree of belonging in a term. Each MF = a **center** (peak) and a
  **width** (spread); these 120 numbers are exactly what the GA tunes.
- **Rule base (5×5)** — ~25 IF-THEN rules on the (error, error-rate) grid
  (`RULES` table, MacVicar-Whelan diagonal: output opposes both error and
  rate, i.e. pure damping on the ZO row).
- **Min-max inference** — rule firing strength = min(error-membership,
  rate-membership); the output shape is the max over all fired rules
  (`infer()`).
- **Centroid defuzzification** — the crisp output is the center of gravity
  of the aggregated shape, computed on a 201-point grid; if nothing fires,
  the output is 0.0 (zero-fire fallback).
- **Velocity / incremental form** — the controller outputs a *change* in
  duty (`du`, `dv`) added to running accumulators (`uT`, `uH`), not an
  absolute duty. This gives bumpless, integral-like behavior.
- **Dual-loop** — independent T-loop (heater/cooler/vent) and RH-loop
  (fogger only); the humidity loop is one-sided (fogger adds moisture,
  never removes it).
- **Split-range** — positive T-effort drives the heater, negative drives
  fan/cooler + vent, never both at once.
- **Anti-windup (conditional integration)** — an accumulator freezes when
  its output is saturated and still pushing further, preventing integral
  windup (same convention as the PID).
- **State dict** — `{'pT','pH','uT','uH'}` (previous errors + accumulators),
  owned by the caller; `state=None` starts fresh. The engine itself is
  stateless and pure.
- **Frozen MFs (`FUZZY_MFS`)** — the hand-tuned, module-level, read-only
  MF tables. The dashboard treats them as ground truth; the GA only ever
  sees decoded copies.
- **Scratch MFs** — deep-copied MFs with user-dragged centers, neighbor-
  clamped so ordering never breaks; the frozen baseline is never mutated.
- **Coupling boost (`apply_coupling`)** — post-step heater/vent top-up
  proportional to humidity excess (`k * max(0, rh - RH_sp)`), the A2
  mechanism shared by the fitness loop and `ga_fuzzy_step`.

## 3. Fitness language — metrics (src/metrics.py)

- **IAE (integral absolute error)** — summed |error| in degree-hours /
  %-hours. The dominant fitness terms (`iae_T`, `iae_H`).
- **ISE (integral squared error)** — squared-error integral; punishes
  large excursions harder than IAE. Reported, not in fitness.
- **RMSE** — root-mean-square error vs setpoint. Reported, not in fitness.
- **Settling time** — last minute both T (±0.5 °C) and RH (±3 %) stay in
  band; `inf` if the final step still violates (never settled).
- **Overshoot** — positive-side-only peak beyond setpoint; the cold-start
  undershoot from the 20 °C init is a transient, not overshoot.
- **Energy (duty-hours)** — sum of all four duties per step ÷ 60,
  definition locked identical to the GA's own loop.
- **Weighted cost** — the single fitness number
  (`1.0*IAE_T + 1.0*IAE_H + 0.01*energy`, lower wins).
- **Scoreboard (`results/comparison.csv`)** — 8 frozen rows: 4 controllers
  × train-seed7 / holdout-seed21, with exactly the `COLUMNS` header and a
  1..4 `rank` within each weather block. The holdout block is the verdict.
- **Holdout rank #1 / cost 114.28** — the headline: GA fuzzy beats on/off
  and PID on unseen weather.

## 4. Analysis terms (dashboard + helpers)

- **Convergence replay** — scrubbing the frozen 50-generation
  best/mean history with a slider (`replay_slice`); no live evolution.
- **Sensitivity (dcost)** — each hand eT center shifted ±0.5 in turn, full
  closed loop re-run per shift; the bar chart ranks which center matters
  most (10 runs, cached, opt-in).
- **Robustness table** — 5 controllers × seed7/seed21/seed13/heatwave/
  coldsnap: cost plus T-actuator **saturation** (% steps with heater or
  fan pinned ≥ 0.99).
- **Disturbance (heatwave/coldsnap)** — synthetic weather with mean
  shifted +6/−6 °C off seed 7, testing the controllers outside training
  conditions.
- **Pareto frontier** — energy-vs-discomfort scatter from frozen rows;
  non-dominated points (nothing beats them on both axes) joined as the
  tradeoff curve. Comfort proxy = `iae_T + iae_H`.
- **Crop health** — display heuristic (not agronomy): last-6h mean
  |T−T_sp| and |RH−RH_sp| mapped to 0..1, plus an illustrative ±1 °C
  vent-to-wall gradient and a linear day-fraction growth scale.
- **Adaptive fuzzy (FUZZ-07)** — supervisory gain `gT` on T-loop duties,
  driven up by persistent |error| (EMA > 1 °C) and relaxed when settled
  (< 0.25 °C), clamped to [0.5, 2.0]. Fixed rule base, adaptive authority.

## 5. Artifact terms

- **`ga_optimized_params.json`** — the evolved artifact: tuned MFs +
  coupling gains + fitness + train/holdout seeds + full history. The only
  data source the GA Explorer trusts.
- **Ephemeral weather** — synthetic non-7/21 profiles generated into one
  shared temp dir (`ephemeral_weather_path`), never into `weather/`.
