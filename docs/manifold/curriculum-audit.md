# Manifold curriculum audit: coverage vs the ETS GRE Mathematics Subject Test

Scope: the 33-topic blueprint (`rslib/src/manifold/blueprint.json`) and the seed
skill deck (`manifold/content/seed_deck.json`, 519 skills) checked against the
official ETS content outline. Problem-type context from
`docs/manifold/problem-types/README.md` (519 types, one per seed skill).

Source: ETS, "GRE Subject Test Content and Structure" (Mathematics),
<https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html>
(Calculus 50%, Algebra 25%, Additional Topics 25%). Subtopic bullets quoted from
the ETS "GRE Mathematics Test Practice Book,"
<https://www.ets.org/pdfs/gre/practice-book-math.pdf>. Method note: a direct
fetch of an older ETS prepare URL returned HTTP 404, so the split and the
subtopic list below were read from the ETS content-structure page and the ETS
practice-book text returned by search, not from memory. The two ETS artifacts
agree.

## (a) Topic coverage

Every ETS-listed subtopic maps to at least one blueprint topic. No ETS subtopic
is unrepresented.

| ETS area (weight) | ETS subtopics                                                                                                                                  | Manifold topics                                                                                                                                                                                                                                                                                               |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Calculus (50%)    | differential and integral calculus of one and of several variables; connections with coordinate geometry, trigonometry, differential equations | `precalc_functions`, `trigonometry`, `coordinate_geometry`, `limits_continuity`, `differential_calc`, `applications_derivatives`, `integral_calc`, `integration_techniques`, `applications_integrals`, `sequences_series`, `multivariable_diff`, `multivariable_int`, `vector_calc`, `differential_equations` |
| Algebra (25%)     | elementary algebra                                                                                                                             | `elementary_algebra`                                                                                                                                                                                                                                                                                          |
|                   | linear algebra: matrix algebra, systems, vector spaces, linear transformations, characteristic polynomials, eigenvalues and eigenvectors       | `linear_algebra_core`, `vector_spaces`, `eigen` (holds "Characteristic polynomial and its invariants")                                                                                                                                                                                                        |
|                   | abstract algebra and number theory: group theory, rings and modules, field theory, number theory                                               | `group_theory`, `rings_fields`, `number_theory`                                                                                                                                                                                                                                                               |
| Additional (25%)  | introductory real analysis: sequences and series, continuity, differentiability, integrability, topology of R and Rⁿ                           | `real_analysis_sequences`, `real_analysis_topology`                                                                                                                                                                                                                                                           |
|                   | discrete math: logic, set theory, combinatorics, graph theory, algorithms                                                                      | `logic_sets`, `combinatorics`, `graph_theory`, `algorithms`                                                                                                                                                                                                                                                   |
|                   | other topics: general topology, geometry, complex variables, probability and statistics, numerical analysis                                    | `metric_topology`, `geometry`, `complex_analysis`, `probability`, `statistics`, `numerical_analysis`                                                                                                                                                                                                          |

Findings:

- Coverage is complete at the topic level. Every ETS subtopic has a home.
- Area assignment follows ETS's own grouping: `trigonometry` and
  `coordinate_geometry` are filed under calculus, which matches ETS listing them
  as calculus "connections," not as separate areas.
- One ETS phrase has no dedicated skill: modules (ETS says "rings and modules").
  `rings_fields` covers ideals, quotient rings, fields, and finite fields but no
  module skill. Modules are rarely tested on released forms, so this is a minor
  gap, not a real hole.
- One topic sits below the ETS content line: `precalc_functions`. ETS assumes
  precalculus rather than scoring it as a bucket (it does note precalculus-level
  questions can be among the hardest). Keeping it as a `relearn` foundation is
  reasonable for a trainer, but its weight counts inside the calculus 50% (see b).
- Nothing else is out of scope. All 33 topics fall inside the ETS outline.

## (b) Weight sanity

Blueprint weights sum to exactly 100 and split exactly to the ETS ratio.

| Area       | Topics | Weight sum | Share | ETS target |
| ---------- | ------ | ---------- | ----- | ---------- |
| calculus   | 14     | 50         | 50%   | 50%        |
| algebra    | 7      | 25         | 25%   | 25%        |
| additional | 12     | 25         | 25%   | 25%        |
| total      | 33     | 100        | 100%  | 100%       |

Within-area emphasis is defensible against released forms:

- Calculus: the top weights (5) sit on `differential_calc`,
  `applications_derivatives`, `integral_calc`, and `sequences_series`.
  Single-variable calculus plus foundations and series carry 40 of the 50 points;
  multivariable, vector calculus, and differential equations carry 10. That
  matches the exam's tilt toward single-variable calculus and series.
- Algebra: linear algebra (`linear_algebra_core` 5, `vector_spaces` 5, `eigen` 4,
  = 14 of 25) outweighs abstract algebra (`group_theory` 3, `rings_fields` 2,
  = 5) and `number_theory` (3). ETS lists these as co-equal bullets, but released
  forms test linear algebra more heavily than abstract algebra, so the tilt is
  justified.
- Additional: `probability` (4) is the largest, then real analysis and the
  discrete core (3 each); `graph_theory`, `algorithms`, `geometry`, and
  `numerical_analysis` sit at 1 each. That tracks how rare those slices are on
  released forms.

One nit: `precalc_functions` at weight 4 outweighs several genuine calculus
topics (`trigonometry` 2, `coordinate_geometry` 3, `applications_integrals` 3,
`multivariable_int` 2, `vector_calc` 2, `differential_equations` 2). Since
precalculus is not an ETS scored bucket, 4 of the calculus 50 points go to
pre-requisite material.

## (c) Skills: assignment and gaps

Structural checks (script over both files):

- All 519 seed skills carry a `topic_id` that exists in the blueprint. No
  orphans, and every topic has skills.
- Seed skill tier matches its topic's blueprint tier for all 519 skills (0
  mismatches).
- Seed skill counts per topic match the problem-type counts in the README
  exactly (14 to 20 per topic; 7 each for `algorithms` and `numerical_analysis`).

`expected_skills` is stale relative to the deck. The blueprint's
`expected_skills` totals 147 (3 to 8 per topic), but the deck now holds 519 (14
to 20 per topic). `mastery.rs` computes `coverage = authored_skills /
expected_skills`, capped at 1.0 (blueprint.rs field; mastery.rs line 389). Once
the full deck is authored, coverage saturates at 1.0 for every topic and stops
discriminating. The floor is met everywhere, which is good, but the number no
longer reflects real breadth. Note the separate generated-bank artifact
`coverage_report.json` still uses `expected_skills` meaningfully: it flags
`metric_topology` as below floor with 0 verified items, so that topic has no
verified questions in the generated bank yet.

A few skills look loosely placed. All are correct on content; none is wrong:

- `trigonometry` holds "Derivative of an inverse trig function" and "Integral
  yielding an inverse trig function." Those are differential and integral
  calculus skills, and `integration_techniques` already carries "Inverse-trig
  standard forms." Either move them, or keep them as a deliberate inverse-trig
  cluster.
- "Average value of a function" appears in both `integral_calc` and
  `applications_integrals`; a tangent-line skill appears in both
  `differential_calc` and `applications_derivatives`. Minor duplication, fine as
  reinforcement, worth deduping if skill identity is meant to be unique.

Internal doc drift (not an ETS issue): the problem-types README labels
`number_theory`, `group_theory`, and `combinatorics` as "recognize," but the
blueprint and the seed deck mark all three "teach." The blueprint is the source
of truth; the README table is stale.

Not verified: I did not hand-check all 519 skills for mathematical correctness.
The items above are spot findings, not an exhaustive per-skill review.

## (d) Prioritized corrections

1. Reconcile `expected_skills` with the real deck (high; it drives the mastery
   coverage signal). Either raise each topic's `expected_skills` to reflect the
   authored counts, or redefine `coverage` so it does not saturate.
2. Author verified `metric_topology` items so it clears the coverage floor in the
   generated bank (medium; currently 0 verified items).
3. Fix the problem-types README tiers for `number_theory`, `group_theory`, and
   `combinatorics` to "teach" to match the blueprint (low; doc only).
4. Reassign or intentionally keep the two calculus skills parked under
   `trigonometry`, and dedupe the "average value" and tangent-line skills across
   the two calculus pairs (low).
5. Consider trimming `precalc_functions` weight from 4 toward 2 or 3 so
   pre-requisite material does not consume ETS calculus points (optional).
6. Optionally add a modules skill to `rings_fields` for full ETS-list fidelity
   (low; rarely tested).

Bottom line: coverage is complete and the weights match the ETS 50/25/25 split to
the point. The real work is internal bookkeeping (stale `expected_skills`, the
`metric_topology` content gap, and README tier labels), not curriculum gaps
against ETS.
