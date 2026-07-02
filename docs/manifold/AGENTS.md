# Manifold — agent orientation

> Manifold is an AGPL fork of Anki that retargets its spaced-repetition **engine**
> into a GRE Mathematics Subject Test trainer (desktop + Android) for an
> AP-Calc-BC-ready undergrad, and reports three _honest, separate_ scores (memory,
> performance, readiness) with ranges and a give-up rule. **Current state:**
> planning complete (PRD + 5 specs + decision log written); **no implementation
> yet** — the repo is a fresh upstream Anki clone. First code = get Anki building +
> a trivial Rust change live on desktop and Android.

This file is the front door for **Manifold** work. (The repo root `AGENTS.md` /
`CLAUDE.md` are upstream **Anki's** — defer to them for build mechanics and the
`just` recipes; defer to _this_ file for what Manifold is building and why.)

## Source of truth (read in this order)

1. **This file** — current Manifold state.
2. **Decision log** ([`alternatives.md`](alternatives.md)) — latest non-superseded
   entry wins (D1–D30).
3. **Iterations log** — _not created yet_; add `docs/manifold/design-iterations.md`
   on the first test-/feedback-driven change.
4. **PRD / specs** ([`../../PRD.md`](../../PRD.md) + `spec-*.md`) — _original intent,
   written before implementation._ Superseded wherever a later decision or an
   "Overrides" entry below says so. **When a spec and a decision conflict, the
   decision wins** — do not defer to the PRD.

## Overrides since the plan

_Record current truth as it diverges from the PRD/specs, newest first._

- **Tier display labels: Core / Target / Reach** (`graph.ts` `tierLabel`, D30).
  The UI shows relearn→Core, teach→Target, recognize→Reach (DAG legend, topic
  panel, aria-labels); internal ids (blueprint keys, `mf::tier::*` tags, engine,
  tests) are unchanged — display-only, no re-seed.
- **Session covers tiers in order** (`session.rs`, D29). The queue is tier-major:
  relearn (circle) → teach (square) → recognize (diamond); within a tier it orders
  by points-at-stake and interleaves across topics, and the new-card budget fills
  lower tiers first. Tier outranks points across tiers (points still orders within
  a tier).
- **Unlock on the mastery-learning criterion** (`mastery.rs` / `blueprint.json`,
  D28, supersedes D27/D22). A topic opens its dependents once each prerequisite is
  _competent enough_ — `competent_fraction ≥ unlock_competent_fraction` (0.8): 80%
  of its skills answered correctly (≥1 success = Independent level). Competence now
  (Bloom's criterion), reachable in a session — not mere exposure (D27) and not
  durable mastery (D25, weeks). `mastered` (violet) stays the separate 21-day goal;
  while problems are placeholders "correct" = pressing A, so the gate is only as
  real as the problems.
- **`in_progress` (DAG green) = studied, not mastered** (`mastery.rs`, D26). A
  topic turns green when any card has an FSRS memory state (`avg_stability > 0`),
  not when it has a mastered skill — because D25's stability mastery takes weeks,
  so gating green on mastery hid all active study. Progression: unlocked (grey) →
  in_progress (green) → mastered (violet).
- **Mastery = FSRS stability, per tier** (`mastery.rs` / `blueprint.json`, D25,
  supersedes D23). A skill is mastered when its mean FSRS stability reaches its
  tier bar (`tier_stability`: relearn/teach 21d ≈ Anki "mature", recognize 7d),
  not a recall-`R` threshold — so mastery reflects durable learning (storage
  strength) and can't be tripped by one just-answered card. Topic mastery still
  needs mastered-fraction ≥ `tier_targets` (relearn 0.9 / teach 0.8 / recognize
  0.6). The Memory score still reads `R`; only the mastered flag (the violet
  badge) moved to stability. Scheduler/FSRS untouched (D3) — we only read it.
- **Teaching level is competence-driven, not CardType** (`mastery.rs` /
  `session.rs`, D24). A card's level (New/Guided/Independent/Revisited) now comes
  from demonstrated competence — Independent = ≥ `independent_successes` (1)
  correct retrieval, reachable the same day — instead of Anki's learning-steps
  graduation. Revisited still uses `CardType::Relearn` (relearning after a lapse).
  Performance/readiness evidence is unchanged: still cold `Review`-kind attempts
  only (D20/D21).
- **Readiness score implemented + card levels** (`spec-readiness-levels.md`,
  D19–D21). The give-up gate now emits a `projected` ETS-anchored scaled **range**
  (the `calibration-pending` state is retired), mapping blueprint-weighted
  unsupported performance → scaled via the blueprint's ETS anchors + a
  `readiness_mapping` block (D19). Performance and the give-up evidence count
  **only unsupported (revlog `Review`-kind) attempts** (D20/D21); Memory is
  unchanged. Every card carries a **teaching level** from its `CardType`
  (New/Guided/Independent/Revisited) on `SessionItem`, with per-topic level counts
  on `TopicNode`. Scoring constants now ride the topic-graph RPC (`ScoringConfig`),
  so `TopicGraphResponse` has two fields and **pylib no longer unwraps it**: call
  `col._backend.get_topic_graph().nodes`, not `get_topic_graph()`. While problems
  are placeholders, the readiness range shows with a placeholder banner (honest by
  construction), never a bare number.
- Blueprint/DAG expanded **17 → 33 topics**, re-grounded to the ETS 50/25/25 split
  plus a released form (GR3768): calculus, linear algebra, abstract algebra,
  analysis/topology and discrete math are split finer, and `geometry` + `statistics`
  are now their own nodes. Topic ids changed accordingly and `seed_deck.json` was
  re-tagged/extended to keep ≥3 skills per topic. `spec-engine`'s "~17 nodes" is
  illustrative and now reads 33.
- PRD/D6 said Phase-1 = self-graded skill cards -> now the full loop runs through a
  problem-wrapper with objective correctness grading and placeholder problems (see
  D18). UI is proprietary (Anki chrome hidden; app boots into the Manifold home).
  Engine adds `get_topic_graph` (D7's mastery query, implemented).

## Stack

- **Engine:** Rust (`rslib`) — FSRS scheduler + collection; Manifold adds a
  mastery-by-topic query + points-at-stake queue (D7).
- **Bindings:** `pylib` (Python) + the TS `@generated/backend`; new protobuf in
  `proto/anki/manifold.proto`.
- **UI:** Anki's native Svelte/TS web views as new mediasrv pages (D10).
- **Desktop:** Qt shell. **Mobile:** Android via AnkiDroid (D8). **Sync:** Anki's
  protocol, self-hosted server (D9). **License:** AGPL-3.0-or-later, credit Anki
  (D17).

## Where things are

- `PRD.md` (root) — umbrella product contract.
- `docs/manifold/spec-engine.md` — Rust change + skill/DAG data model + review unit.
- `docs/manifold/spec-scoring.md` — the three scores + give-up rule + readiness map.
- `docs/manifold/spec-mobile-sync.md` — AnkiDroid companion + sync + conflict rule.
- `docs/manifold/spec-ai-generation.md` — Phase-2 generation + verifier + eval.
- `docs/manifold/spec-study-feature.md` — interleaving + the 3-build ablation.
- `docs/manifold/alternatives.md` — the decision log.
- `mf_blueprint.json` (to be authored) — DAG edges, blueprint weights, ETS table.

## Conventions that bite

- **Build via `just`** (see root `AGENTS.md`); a new `.proto` needs a full
  `just check`, not just `cargo check`.
- **Decision log is append-only** — supersede, never rewrite; IDs `D<N>` monotonic.
- **No fabricated readiness numbers, ever** — readiness is gated behind the give-up
  rule and always a range (D11, D12); automatic fail otherwise.
- **No live model on the runtime review path** — the app must run AI-off (D6, D14).
- **Skill/topic identity rides Anki tags** (`mf::topic::*`, `mf::skill::*`,
  `mf::tier::*`); no synced schema fork (D7).
- **Honesty/no-fallback:** let missing data fail loudly + abstain; don't paper over
  gaps with a number (mirrors the user's standing rule).
- **Don't edit the frozen PRD/specs to track drift** — log a new decision +
  an "Overrides" line here instead.

## Current focus

1. **Get Anki building from source** + a trivial Rust change visible on desktop
   _and_ Android (the day-one risk, D8; assignment "Get Anki Building First").
2. Author the **DAG/blueprint** + a seed GRE-math skill deck (D5).
3. Land the **mastery-by-topic** RPC + Memory score for the Wednesday build (D7, D11).

---

<sub>Maintained with the `log` skill.</sub>
