# Model cards: memory, performance, readiness

> Assignment section 12: one concise page each for the three scores Manifold
> reports, plus the give-up rule that governs when it refuses to project. The
> scores are separate by design and never blended into one number; each is shown
> with a range.

Every value cited here is read from the code and content, not invented:

- the engine rollup in `rslib/src/manifold/mastery.rs`,
- the score derivations in `ts/lib/manifold/scoring.ts`,
- the scale, ETS anchors, and mapping constants in
  `rslib/src/manifold/blueprint.json`.

The frozen specs are [`spec-scoring.md`](spec-scoring.md) and
[`spec-readiness-levels.md`](spec-readiness-levels.md).

## The give-up rule (shared)

Readiness emits no estimate until both conditions hold, counted over independent
(unsupported) attempts only:

- at least **200 independent reviews** summed across topics
  (`READINESS_MIN_INDEPENDENT_REVIEWS = 200`), and
- at least **50% blueprint-weighted coverage** (`READINESS_MIN_COVERAGE = 0.5`).

Below the line the app abstains and shows the missing evidence plus the single
best topic to study next; it never shows a number. Above the line the estimate is
`provisional`, and becomes `confident` at 600 independent reviews and 80%
coverage. The rule gates readiness; memory and performance display on their own
evidence and feed the gated readiness estimate. An independent review is a cold,
unsupported attempt (defined under performance, below).

---

## Memory

**Question.** Can the learner recall a practiced skill right now?

**Model.** FSRS retrievability `R`, read per card exactly as `stats/card.rs`
computes it (`current_retrievability_seconds(state, elapsed, decay)`) from the
card's stored memory state; no FSRS parameter or interval is ever modified. The
engine rolls each card's `R` up per topic into `avg_recall`, the mean `R` over
the topic's cards that have a memory state. The Memory score is the
blueprint-weight-weighted mean of `avg_recall` over topics with at least one
authored skill (`total > 0`), reported with a band equal to the lowest and
highest per-topic `avg_recall` among the contributing topics. It is a value with
a range, not a bare point.

**Evidence consumed.** Per-card FSRS memory state (stability, difficulty) and the
time elapsed since the last review. Never-studied cards have no memory state and
are excluded. Memory reads FSRS state only, not the revlog, so it is independent
of the performance signal.

**Durable mastery (separate signal).** A skill counts as `mastered` when its mean
FSRS stability reaches its tier bar (`tier_stability`: relearn and teach 21 days,
recognize 7 days), and a topic is `mastered` once its mastered fraction reaches
its tier target (`tier_targets`: relearn 0.9, teach 0.8, recognize 0.6). This
durable, stability-based mastery drives the violet badge and topic gating, and is
deliberately distinct from the momentary `R` the Memory score reports.

**Give-up rule.** The give-up rule gates readiness, not memory. Memory is shown
whenever at least one topic has a studied card and reads `null` (nothing shown)
when nothing has been studied. It never fabricates a value.

**Proof.** Calibration is the required check: a reliability chart plus Brier or
log-loss on held-out reviews (`spec-scoring.md` section 5; assignment step 1).
When Memory says 80%, about 80% should recall.

---

## Performance

**Question.** Can the learner answer a fresh, exam-style item correctly, cold?

**Model (implemented).** Per topic, performance is `independent_good /
independent_reviews`: the fraction of unsupported attempts answered correctly. The
engine counts a revlog entry as an independent review when its `review_kind` is
`Review` (not Learning or Relearning) and a button was pressed, and counts it as
good when the rating is at least 2 (Good or Easy). Learning and Relearning
attempts are scaffolded and are excluded, so the score measures cold recall, not
guided practice. The Performance score is the blueprint-weight-weighted mean of
per-topic performance over topics with at least one independent review
(`independentReviews > 0`), reported with a band of the lowest and highest
contributing per-topic values.

**Model (specified bridge).** The documented target model is a calibrated
logistic over features available without AI,
`σ(β₀ + β₁·stability + β₂·(1 − difficulty) + β₃·avg_time_z + β₄·tier)`, fit on
held-out graded items (`spec-scoring.md` section 4.2): the mastery, difficulty,
timing, and coverage bridge. Until held-out generated items exist, the cold
accuracy above is the honest performance signal. Performance is never copied from
Memory.

**Evidence consumed.** Unsupported revlog entries only (`review_kind == Review`),
with `button_chosen` for correctness. It ignores FSRS `R`, which is precisely why
it can diverge from Memory.

**Give-up rule.** Independent reviews are the evidence the give-up rule counts, so
a topic contributes to readiness only once it has cold attempts. Performance is
the per-topic signal readiness aggregates; it reads `null` when no topic has an
independent review.

**Proof.** The paraphrase test: for 30 skills, author 2 reworded items each and
compare card recall against reworded accuracy (`spec-scoring.md` section 5;
assignment 7d). If the gap is near zero, performance is echoing memory rather than
measuring a new bridge; the gap is reported honestly.

---

## Readiness

**Question.** What would the learner score today, and how sure is the app?

**Model.** Computed in `scoring.ts` from the topic graph and the blueprint scale:

1. **Weighted-mean cold performance.** `p̄` is the blueprint-weight-weighted mean
   of per-topic performance over topics with at least one independent review.
2. **Performance to percentile.** `percentile = Φ((p̄ − 0.5) / 0.18)`, using
   `median_raw_fraction = 0.5` and `performance_sd = 0.18` from the blueprint
   `readiness_mapping` block. These are chosen, tunable constants, not derived
   from student outcomes.
3. **Percentile to scaled.** The blueprint `ets_anchors` table is treated as a
   monotone piecewise-linear curve from percentile to scaled score; beyond the
   outer anchors it falls back to the normal fit `680 + 161·Φ⁻¹(percentile)`. The
   result is rounded to the nearest 10 and clamped to the 200 to 990 scale.

The anchors and distribution are sourced from the ETS GRE Guide to the Use of
Scores (2025), Table 2A, Mathematics, test-takers 2021 to 2024 (n = 5,180, mean
680, SD 161). ETS does not publish raw-to-scaled tables, so step 2 is an explicit
approximation, documented here and in `spec-readiness-levels.md` (decision D19).

**Range and ceiling.** Readiness is always a range, never a bare scalar. The band
half-width is `0.1·(1 − coverage) + 0.12·lapse + 0.5·(perf_high − perf_low)`
(`coverage_band_lambda = 0.1`, `lapse_band_lambda = 0.12`): it widens as coverage
falls and as graduated knowledge proves fragile, where `lapse` is the Revisited
share of graduated cards. The point and both ends are mapped through the same
curve and capped at the promised ceiling. Manifold withholds a maturity residue
of 3 deep-proof items and 35 scaled points at the top, so it never projects above
`990 − 35 = 955`.

**Target selector.** The blueprint defines a target ladder, each rung with its
scaled band; the app reports the gap and the estimated study hours to reach each:

| Target      | Point | Band       |
| ----------- | ----- | ---------- |
| Median      | 680   | 660 to 700 |
| Strong      | 800   | 780 to 820 |
| Exceptional | 860   | 840 to 880 |

Hours to a target follow a convex logarithmic curve,
`H(s) = 12·(exp((s − 560) / 120) − 1)` (`hours_scale = 12`, `scaled_floor = 560`,
`points_per_log_hour = 120`), so each further scaled point costs more hours than
the last.

**Evidence consumed.** The per-topic cold-performance aggregates, coverage, and
teaching-level counts (Independent and Revisited, for the lapse rate) from the
topic graph, plus the static scale, anchors, and mapping constants from
`blueprint.json`. No live model call sits on the readiness path.

**Give-up rule.** The shared rule applies directly: no estimate below 200
independent reviews and 50% coverage. Above the line, readiness carries seven
honest fields and never a lone number: point, range, percent covered, confidence
(`provisional` or `confident`), last updated, drivers (the top weak,
heavily-weighted topics), and the give-up state itself.

**Proof.** The mapping method is written down (this card and
`spec-readiness-levels.md` section 4). There is no code path that emits a bare
readiness number; a fabricated or unattributable readiness number is an automatic
fail under the assignment (`ASSIGN.md` sections 4 and 11), which is why the
residue, the cited anchors, and the give-up rule are all enforced in code.
