# GRE Math Subject Test — problem types by topic

A per-topic catalog of the recurring **problem types** on the GRE Mathematics
Subject Test, one file per node of the Manifold topic DAG
(`rslib/src/manifold/blueprint.json`). **519 problem types across 33 topics.**

## How this was built

One research subagent per DAG topic (Opus 4.8 Max Fast), run in parallel, each
grounded in the real recurring style of released forms (GR0568, GR8767, GR9367,
GR9768, GR1268, GR3768) plus standard prep. Honesty rules were enforced: no
fabricated question-number citations, no invented statistics, and no padding with
types that don't actually occur — difficulty/frequency labels are qualitative and
exam-relative, and every example stem is original (paraphrased, not copied).

Each file: an H1, a one-line scope note, then problem types grouped by the topic's
blueprint sub-skills. Every type carries **Name · What it asks · Solve approach ·
Difficulty + Frequency · Example stem**.

## Calculus (≈50% of exam) — 228 types

| Topic                                                        | Tier    | Wt | Types |
| ------------------------------------------------------------ | ------- | -- | ----- |
| [Precalculus & functions](precalc_functions.md)              | relearn | 4  | 19    |
| [Trigonometry](trigonometry.md)                              | relearn | 2  | 16    |
| [Coordinate geometry](coordinate_geometry.md)                | relearn | 3  | 16    |
| [Limits & continuity](limits_continuity.md)                  | relearn | 4  | 18    |
| [Differential calculus](differential_calc.md)                | relearn | 5  | 16    |
| [Applications of derivatives](applications_derivatives.md)   | relearn | 5  | 18    |
| [Integral calculus](integral_calc.md)                        | relearn | 5  | 14    |
| [Integration techniques](integration_techniques.md)          | relearn | 4  | 17    |
| [Applications of integration](applications_integrals.md)     | relearn | 3  | 14    |
| [Sequences & series](sequences_series.md)                    | relearn | 5  | 20    |
| [Multivariable differential calculus](multivariable_diff.md) | teach   | 4  | 15    |
| [Multivariable integral calculus](multivariable_int.md)      | teach   | 2  | 16    |
| [Vector calculus](vector_calc.md)                            | teach   | 2  | 14    |
| [Differential equations](differential_equations.md)          | teach   | 2  | 15    |

## Algebra (≈25% of exam) — 122 types

| Topic                                                        | Tier      | Wt | Types |
| ------------------------------------------------------------ | --------- | -- | ----- |
| [Elementary algebra](elementary_algebra.md)                  | relearn   | 3  | 18    |
| [Number theory](number_theory.md)                            | recognize | 3  | 15    |
| [Linear algebra: matrices & systems](linear_algebra_core.md) | teach     | 5  | 16    |
| [Vector spaces & linear maps](vector_spaces.md)              | teach     | 5  | 19    |
| [Eigenvalues & diagonalization](eigen.md)                    | teach     | 4  | 19    |
| [Group theory](group_theory.md)                              | recognize | 3  | 19    |
| [Rings & fields](rings_fields.md)                            | recognize | 2  | 16    |

## Additional topics (≈25% of exam) — 169 types

| Topic                                                                   | Tier      | Wt | Types |
| ----------------------------------------------------------------------- | --------- | -- | ----- |
| [Logic, sets & relations](logic_sets.md)                                | recognize | 3  | 17    |
| [Combinatorics](combinatorics.md)                                       | recognize | 3  | 17    |
| [Graph theory](graph_theory.md)                                         | recognize | 1  | 15    |
| [Algorithms](algorithms.md)                                             | recognize | 1  | 7     |
| [Probability](probability.md)                                           | recognize | 4  | 18    |
| [Statistics](statistics.md)                                             | recognize | 2  | 12    |
| [Real analysis: sequences & series](real_analysis_sequences.md)         | recognize | 3  | 15    |
| [Real analysis: continuity & topology of ℝⁿ](real_analysis_topology.md) | recognize | 2  | 16    |
| [Metric & general topology](metric_topology.md)                         | recognize | 2  | 14    |
| [Complex analysis](complex_analysis.md)                                 | recognize | 2  | 16    |
| [Geometry](geometry.md)                                                 | teach     | 1  | 15    |
| [Numerical analysis](numerical_analysis.md)                             | recognize | 1  | 7     |

> `Wt` is the topic's blueprint weight (share of exam points). `Tier`:
> `relearn` (master cold), `teach` (learn thoroughly), `recognize`
> (pattern-spot). The narrowest, rarest slices (algorithms, numerical analysis)
> intentionally have the fewest types.
