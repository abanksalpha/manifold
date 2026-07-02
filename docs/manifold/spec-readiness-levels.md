# Spec: Readiness score + card-level labels

> Two buildable-now increments that need **no problem generation**: (1) finish the
> readiness score — the `E[raw] → ETS-scaled` mapping that `spec-scoring.md` §4.3
> left "design locked, unbuilt" — and (2) label every card by its **level**
> (New / Learn / Review / Relearn) and surface it. The two share one mechanism:
> the card's maturity is both the teaching-support signal and the honesty filter
> for the performance evidence readiness consumes. Companions:
> [`spec-scoring`](spec-scoring.md) (the frozen score design, D11–D13),
> [`spec-engine`](spec-engine.md) (the aggregates), [`AGENTS.md`](AGENTS.md).
> **Status:** design; unbuilt. Proposes **D19–D21**.
>
> **Authority:** implementation spec, later than the frozen `spec-scoring.md`. It
> _implements_ D13 and _refines_ D11/D12; where it diverges from the frozen spec
> the divergence is called out and logged as a decision, per
> [`AGENTS.md`](AGENTS.md).

## 1. The problem this fills

The pipeline already computes Memory, Performance and coverage per topic and runs
the give-up gate, but it dead-ends at `calibration-pending`: there is no code path
that turns the evidence into a scaled readiness number, because the `E[raw] →
scaled` mapping (`spec-scoring.md` §4.3, D13) was deferred. Separately, the
teaching design keys every scaffold decision off a card's maturity, but the
session queue exposes only card _identity_, never its state, and nothing counts a
card's level or shows it. Both gaps are closable today, without generating a
single problem, and closing them together is cheap because they read the same card
state.

## 2. Goals & non-goals

**Goals**

- Implement the readiness mapping so the dashboard shows a **scaled range** (never
  a bare number), with its evidence, confidence and drivers (D11, D13).
- Make the performance evidence readiness consumes **honest by construction**:
  only _unsupported_ attempts count (revlog `review_kind == Review`).
- Derive a **level** for every card from its `CardType` and surface it in the
  session queue and on the dashboard.

**Non-goals**

- Generating, authoring or rendering any slide content — no worked examples, faded
  completions, pretests or self-explanation prompts. The A–E placeholder problem
  (D18) is unchanged. Levels are _labelled_, not yet _acted on_.
- Calibrating the mapping against real student outcomes (Step 4 bonus, out of
  scope — D11, D13).
- Exposing a variance-based band that would need a new per-skill variance field
  (the band is derived from data already on the wire; see §4.3).

## 3. Grounding (what is already in place)

- `mastery.rs` computes per-topic `performance` (fraction of graded reviews rated
  ≥ 2) and `graded_reviews`, and rolls FSRS `R` into `avg_recall` (Memory).
- `scoring.ts` computes the weighted means, coverage and the give-up gate, then
  emits `abstaining` | `calibration-pending`.
- `blueprint.json` already carries the full readiness scale as data, currently
  parsed but unused (`#[allow(dead_code)]` in `blueprint.rs`): `scale`
  `{200, 990}`, `distribution` `{mean 676, sd 154, n 7452}`, and the 15-point
  `ets_anchors` table `(scaled, percentile_below)`.
- The revlog stamps every attempt with `review_kind` (`Learning`, `Review`,
  `Relearning`, …) via Anki's normal answering path, so supported and unsupported
  attempts are already distinguishable with no new plumbing.
- `CardType` (`New`, `Learn`, `Review`, `Relearn`) is on every card and read
  cheaply in `build_session_queue`, which already holds the full `Card`.

## 4. Feature A — the readiness score

### 4.1 The honest input: independent performance

Redefine the performance evidence to count **only unsupported attempts** — revlog
entries with `review_kind == Review`. Learning and Relearning attempts (support
present: teaching and re-teaching) are visible to the scheduler but **excluded**
from the score. This is what makes the number honest the moment real items exist:
an attempt only counts once the learner faces the skill cold.

- `mastery.rs`: split the revlog fold so `performance` and the readiness evidence
  count `Review`-kind entries only. Memory (`avg_recall`) is unaffected — it reads
  FSRS `R`, not the revlog. (Refines D11's Performance definition → **D21**.)
- The give-up gate's evidence count becomes the count of **independent attempts**,
  not all graded attempts (refines D12 → **D20**). Rationale: evidence _for a
  readiness number_ must be unsupported-performance evidence; a learning-step tap
  is engagement, not exam evidence. Tradeoff: a collection can drop from
  `calibration-pending` back to `abstaining` until enough `Review`-kind attempts
  accrue. This is the correct, more conservative behavior.

### 4.2 The mapping (`E[raw] → scaled`, D13)

Implemented in `scoring.ts` (where the other scores live), reading the scale,
distribution and anchors sourced from `blueprint.json` (see §6 for how they reach
TS). Steps:

1. **Weighted-mean expected performance.** Over topics with ≥ 1 independent
   attempt, `p̄ = Σ_t (weightₜ · perf̂ₜ) / Σ_t weightₜ`, `p̄ ∈ [0,1]`. Blueprint
   `weight` stands in for `Qₜ` (questions per topic): a topic's share of exam
   points _is_ its share of questions, so the `Σ weight·perf̂·Q / Σ weight·Q`
   of §4.3 collapses to this weighted mean. (Approximation logged in **D19**.)
2. **Performance → percentile.** The one genuinely chosen step (ETS never
   publishes raw→scaled tables — D13). Model the population percentile as
   `Φ((p̄ − p50) / σ_p)`, anchored so the **median test-taker (50th pct ≈ scaled
   680)** corresponds to an expected blueprint-weighted raw fraction `p50`, with
   `σ_p` set so ±1σ of performance spans ≈ ±1 SD of the scale. Proposed, tunable,
   _chosen not derived_ (like the D12 thresholds): `p50 = 0.50`, `σ_p = 0.18`.
   Store both in `blueprint.json` under a new `readiness_mapping` block so they are
   data, not code.
3. **Percentile → scaled.** Treat `ets_anchors` as a monotone piecewise-linear
   curve `percentile → scaled`; interpolate between anchors, and beyond the outer
   anchors fall back to the normal fit `scaled = 676 + 154 · Φ⁻¹(percentile)`.
   Clamp to the effective range (~380–960) and round to the nearest 10 (the real
   scale's granularity).

### 4.3 Uncertainty band + confidence

- **Band.** Compute a performance interval `[p_lo, p_hi] = p̄ ± (spread + λ·(1 −
  coverage))`, where `spread` comes from the per-topic `perf̂` min/max already in
  `MetricEstimate.low/high`, and the coverage penalty widens the band as coverage
  falls (`λ` tunable, in `readiness_mapping`). Map `p_lo`, `p_hi` through the same
  §4.2 curve to get `scaledLow`, `scaledHigh`. The point is `p̄` mapped; the range
  is the pair. **No bare number is ever emitted** — the display is always the pair
  plus the point (D13, AC 4).
- **Confidence** uses the `spec-scoring.md` §10 tiers directly:
  `provisional` at ≥ 200 independent attempts & ≥ 50% coverage; `confident` at
  ≥ 600 & ≥ 80%. New constants `READINESS_CONFIDENT_REVIEWS = 600`,
  `READINESS_CONFIDENT_COVERAGE = 0.8` beside the existing two.

### 4.4 States + rendering

Extend the `Readiness` union in `scoring.ts` with a third state, replacing
`calibration-pending` as the "gate met" branch:

```ts
| {
    state: "projected";
    scaledPoint: number;      // rounded to 10
    scaledLow: number;
    scaledHigh: number;
    coverage: number;
    independentReviews: number;
    confidence: "provisional" | "confident";
    drivers: StudyNext[];     // top weak, high-weight topics dragging the score
  }
```

- Gate flow: below the line → `abstaining` (unchanged: missing evidence +
  study-next); at/above → `projected`.
- The home readiness cell renders `projected` as, e.g., **"Projected 540–600
  (point 570) · confidence provisional · 47% covered · driver: sequences &
  series"** — the required shape from `spec-scoring.md` §4.3, never a lone scalar.
- `calibration-pending` is retired once `projected` lands (it existed only because
  the mapping was unbuilt). Placeholder honesty is handled instead by a banner
  overlaid on `projected`, not by withholding the number (§7, confirmed).

## 5. Feature B — card-level labels

### 5.1 The level scheme

A card's level is a pure function of its `CardType`; no new stored state, no tag.

| Level | `CardType` | Name        | Meaning                             | Counts for Performance? |
| ----- | ---------- | ----------- | ----------------------------------- | ----------------------- |
| 0     | `New`      | New         | never attempted; first encounter    | no                      |
| 1     | `Learn`    | Guided      | in learning steps; support present  | no                      |
| 2     | `Review`   | Independent | graduated; attempted cold           | **yes**                 |
| 3     | `Relearn`  | Revisited   | lapsed from Review; being re-taught | no                      |

The "counts for Performance" column is exactly the §4.1 filter, so the label and
the honesty filter are the _same distinction_ surfaced twice. The
New/Learn/Review/Relearn backbone is fixed; the display names (New / Guided /
Independent / Revisited) are settled.

### 5.2 Where it is computed and surfaced

- **Backend.** `build_session_queue` maps `card.ctype` to a `level` and puts it on
  each `SessionItem` (§6). `compute_topic_graph` additionally tallies per-topic
  level **counts** (how many of a topic's cards are New / Guided / Independent /
  Revisited) onto `TopicNode`, for the dashboard.
- **Frontend.** The session player shows a small, quiet level badge per item
  (read-only; it does **not** change what the slide renders — placeholder A–E
  stays). The dashboard shows the per-topic level distribution so the learner can
  see how much of each topic has reached Independent.

### 5.3 Why label now, before rendering scaffolds

Labelling is the groundwork the teaching layer will later act on, and it pays off
immediately on its own: it drives the honest Performance filter (§4.1), it makes
the give-up evidence legible ("you have N Independent attempts"), and it gives the
dashboard a real mastery-progression view — all with zero generated content.

## 6. Data model / proto changes

All require a full `just check` (proto rebuild), not just `cargo check`.

- `SessionItem`: add `uint32 level` (+ optionally the raw `card_type`).
- `TopicNode`: add `independent_reviews` (the `Review`-kind count) and four level
  counts (`level_new`, `level_guided`, `level_independent`, `level_revisited`;
  keyword-safe field names for the New / Guided / Independent / Revisited levels).
  `graded_reviews` becomes `Review`-kind-only per §4.1 (or is superseded by
  `independent_reviews`; pick one to avoid two names for one idea — see D21).
- Scoring constants reach TS via the topic-graph response: add a `ScoringConfig`
  message (scale, distribution, `ets_anchors`, `readiness_mapping`) sourced from
  `blueprint.json`, so the anchors have a **single source of truth** in Rust and
  are not duplicated in `scoring.ts`. (Alternative considered: a generated TS
  constant module; rejected to avoid divergence.)
- `blueprint.json`: add `readiness_mapping { median_raw_fraction, performance_sd,
  coverage_band_lambda }` and stop marking the scale/anchors `dead_code`.

## 7. Honesty & placeholder mode (the hard constraint)

We are **not generating slides**, so every attempt — even `Review`-kind — is a tap
on the placeholder A–E problem, not a solved exam item. The `review_kind` filter
makes the number _structurally_ honest (only unsupported attempts count) but
cannot make placeholder taps _meaningful_. Per the standing no-fabrication rule
and D18's persistent placeholder banner:

- The mapping is implemented and computes `projected` now (the pipeline the user
  asked for), but while the app is in **placeholder mode** the readiness cell must
  carry the D18 placeholder banner / an explicit "inputs are placeholder problems"
  note, so a computed range is never presented as a validated score.
- The moment real generated items feed `Review`-kind attempts (Phase 2, D14), the
  _same_ code becomes honest with no change — the banner clears and the number
  stands on real evidence. Nothing is hidden and nothing is faked in between: a
  range, its evidence, its confidence and its placeholder provenance are all shown.

This is the honest-by-construction stance of D13, extended with an explicit
placeholder flag rather than a withheld number.

## 8. Acceptance criteria

1. Readiness renders a **scaled range + point + coverage + confidence + drivers**,
   never a bare number, above the give-up line; below it, missing evidence +
   study-next as before (D11, D12, D13).
2. Performance and the readiness evidence count **only `Review`-kind attempts**;
   Learning/Relearning attempts never move the score. Memory is unchanged.
3. The `E[raw] → scaled` mapping uses the `blueprint.json` ETS anchors and its
   `readiness_mapping` constants, and the approximation is documented (D13 AC 6,
   D19).
4. Every `SessionItem` carries a `level`; the dashboard shows per-topic level
   counts. The label is derived from `CardType`, stored nowhere.
5. In placeholder mode the readiness range is shown with an explicit placeholder
   provenance; the same code path produces an unflagged number once real items
   feed `Review` attempts (no code change required — §7).
6. `just check` passes (proto rebuild, Rust + TS lints, e2e updated).

## 9. Decisions & alternatives (proposed)

- **D19 — readiness raw→scaled approximation.** Weighted-mean independent
  performance → percentile via `Φ((p̄ − p50)/σ_p)` → scaled via the ETS anchor
  curve; `p50`, `σ_p`, `λ` are chosen constants in `blueprint.json`. _Considered:_
  a bare linear `p̄ → scaled` (rejected — ignores the anchor distribution); an IRT
  ability model (rejected — needs item difficulties + far more data, Phase 3+).
- **D20 — give-up evidence = independent attempts** (refines D12). _Considered:_
  keep the gate on all graded attempts and only filter the _value_ (rejected —
  splits "enough evidence" from "the evidence that matters"; the honest bar is
  unsupported attempts, even though it is stricter).
- **D21 — Performance = unsupported (`Review`-kind) accuracy** (refines D11).
  _Considered:_ count all graded attempts (rejected — supported attempts inflate a
  score meant to measure cold performance, reintroducing the memory↔performance
  blur D11 exists to prevent).

These append to [`alternatives.md`](alternatives.md) and get an "Overrides" line in
[`AGENTS.md`](AGENTS.md); this spec does not edit the frozen `spec-scoring.md`.

## 10. Out of scope (now), tracked

- Rendering any level's slide content (pretests, worked examples, faded
  completions, self-explanation prompts) — needs authored/generated content, a
  later spec.
- A variance-based band (needs a per-skill variance field on the wire) — the
  coverage + spread band (§4.3) is the interim.
- Calibrating `p50`/`σ_p`/`λ` against real outcomes (Step 4 bonus — D11, D13).

## 11. Product phasing

- **Now (no generation):** §4 readiness mapping + §5 level labels + §7 placeholder
  guard. Ships a real range and a real mastery-level view off placeholder inputs.
- **Phase 2 (generation, D14):** real items feed `Review` attempts; the placeholder
  banner clears; readiness stands on honest evidence with no code change.
- **Phase 3:** calibration chart + tuning the mapping constants against collected
  data; the teaching layer starts _acting on_ the labels (rendering scaffolds).

---

<sub>Implementation spec for D11–D13 + card levels · maintained with `log`.</sub>
