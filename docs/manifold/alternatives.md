# Manifold — decision log (alternatives)

> Every meaningful choice behind Manifold, with the alternatives we rejected and
> the price each path pays. Append-only: decisions are **superseded, never
> rewritten**. IDs are stable (`D<N>`, monotonic, never reused).
>
> Companions: umbrella [`PRD.md`](../../PRD.md) · specs in
> [`docs/manifold/`](.) · front door [`AGENTS.md`](AGENTS.md).

**Status keys:** `resolved` · `open` · `superseded by D<M>`

## Section index

| Cluster    | IDs              | Topic                                                 |
| ---------- | ---------------- | ----------------------------------------------------- |
| Product    | D1–D6, D18       | exam, user, core mechanic, review surface             |
| Engine     | D7               | the Rust change                                       |
| Platform   | D8–D10, D16–D17  | mobile, sync, UI, docs, license                       |
| Models     | D11–D13, D19–D21 | the three scores, give-up rule, score mapping, levels |
| AI & study | D14–D15          | generation, ablation feature                          |

---

### D1 — Exam: GRE Mathematics Subject Test

- **Status:** resolved
- **Chose:** the GRE Mathematics Subject Test (200–990 scale, ~66 MCQ, blueprint calc ~50% / algebra ~25% / additional ~25%, rights-only scoring since 2017).
- **Considered:** MCAT (huge fact base — flashcard-friendly, but covering it all is the dominant cost and dilutes the engine thesis); LSAT (almost no facts, so a flashcard-derived score model is genuinely hard); GMAT Focus (adaptive scoring would have to be modeled); USMLE Step 1 (pass/fail only — can't show a real scaled number).
- **Gaps / risks:**
  - Niche audience (~7,452 takers/yr, ETS 2019–2023) — small TAM, but market research found _zero_ dedicated apps, so the wedge is real.
  - GRE math is procedural, not declarative — naive flashcards are a poor fit (addressed by D3/D4/D6).

### D2 — Target user & goal

- **Status:** resolved
- **Chose:** an AP-Calc-BC-ready 1st/2nd-year undergrad (walks in knowing ~45–55% of the blueprint) targeting the **median (~676, ~50th pct)** in ~150 hours of practice.
- **Considered:** a final-year major needing light review (the assistant's first instinct — rejected once the user fixed the persona as an early undergrad who _lacks_ the upper-division material); "ace it / top decile" (rejected — the deep analysis/algebra tail does not compress in the timeframe; the ceiling is bunched in the low-90s percentiles anyway).
- **Gaps / risks:**
  - The ~150h figure is _derived_ (see [`BRAINLIFT.md`](../../BRAINLIFT.md)), not validated on real students — real-student validation is the bonus Step 4 and is **out of scope** (D11).

### D3 — Build on Anki's engine, not flashcards-as-surface

- **Status:** resolved
- **Chose:** reuse Anki's _engine_ — the FSRS scheduler, the retrieval loop (attempt → reveal → grade → reschedule), and the note/card data model — and add a teaching layer + curated content graph on top.
- **Considered:** naive Q→A flashcards (rejected — GRE math is procedural; the user explicitly rejected memorizing problem instances); rewriting the scheduler in JS/Swift (rejected — the assignment forbids it and it throws away FSRS's evidence base).
- **Gaps / risks:**
  - "Build off Anki" only counts if we change real Rust (D7), not just the Python/web screens.

### D4 — Skill-level scheduling is the schedulable unit

- **Status:** resolved
- **Chose:** the unit FSRS schedules is a per-`(user, skill)` state, where a _skill_ is a fine-grained pattern (e.g., `calc.related_rates.similar_triangles`), not a broad topic. Each skill carries its own difficulty/stability/due.
- **Considered:** schedule per literal problem instance (rejected — the student memorizes the instance — "oh, the ladder problem, answer C" — which is the exact failure that makes math flashcards useless); schedule per broad topic like "integration" (rejected — too coarse; lumps mastered and unmastered sub-skills together).
- **Gaps / risks:**
  - Requires a curated skill taxonomy (content work, D5).
  - FSRS was fit on declarative recall; applying it to skill-mastery is a modeling assumption to validate via calibration (D11).

### D5 — Content is a prerequisite DAG, tiered by depth

- **Status:** resolved
- **Chose:** model the syllabus as a prerequisite **DAG** of ~16–17 blueprint-tagged topics (each exploded into skills), taught at three depths: **relearn-to-fluency** (calculus they have), **teach-then-master** (the high-ROI new core), **recognition-only** (the hard analysis/topology/algebra tail).
- **Considered:** a flat topic list (rejected — ignores prerequisites and ROI ordering); teach everything to full depth (rejected — wrong learning science for a recognition exam, and infeasible in ~150h).
- **Gaps / risks:**
  - Authoring the DAG + skill tags + tier assignments is real, judgment-heavy content work.
  - Discrete math was a real gap in the first DAG draft — coverage must be audited against the ETS blueprint (the coverage map, assignment 7c).

### D6 — Phase 1 review surface = skill cards; AI generation deferred to Phase 2

- **Status:** superseded by D18
- **Chose:** in Phase 1 the review surface shows a **literal skill card** (front = the problem-type / skill name, e.g. "Eigenvalues via characteristic polynomial"), self-graded against the FSRS rating. Concrete problem generation is a **Phase 2** layer (D14).
- **Considered:** show generated problems from day one (rejected — needs a live model, which violates the Wednesday "no AI" rule and the "runs with AI off" hard requirement); ship templates from day one (deferred to Phase 2).
- **Gaps / risks:**
  - Self-graded recall in Phase 1 measures _confidence_, not true performance; the memory↔performance gap only becomes measurable once Phase 2 problems exist (paraphrase test, D11).

### D7 — The Rust change: mastery-by-topic query (primary) + points-at-stake queue (stretch)

- **Status:** resolved
- **Chose:** primary = a **mastery-by-topic query** RPC that walks the collection and returns, per DAG node, `{mastered_count, total, avg_recall, avg_stability, coverage}` fast enough to power the dashboard on 50,000 cards. Stretch = a **points-at-stake queue** that orders due skills by `blueprint_weight × student_weakness`. New protobuf message(s), called from Python and TS; ≥3 Rust unit tests + 1 Python integration test; undo-safe; no collection corruption.
- **Considered:** topic-aware rescheduling as the primary change (rejected as primary — higher risk to FSRS interval validity + undo; kept in spirit as the queue's weakness signal); doing the aggregation in Python/TS (rejected — too slow on 50k cards, and wouldn't be a real engine change).
- **Gaps / risks:**
  - A read/aggregation RPC is less "engine-y" than scheduler surgery — mitigated by adding the points-at-stake queue (a genuine queue-builder change) as the stretch.
  - Upstream-merge risk wherever we touch the scheduler/queue and protobuf — track touched files (assignment 7a).

### D8 — Mobile: Android via AnkiDroid

- **Status:** resolved
- **Chose:** build the phone companion on **AnkiDroid** (AGPL), which already runs Anki's Rust backend on-device — the lowest-risk path to a genuinely _shared_ engine in one week, and it carries our Rust change (D7) for free.
- **Considered:** iOS via the Rust backend over FFI (rejected for the week — signing/TestFlight + FFI glue is more risk under deadline); rewrite the scheduler in Swift/JS (rejected — forbidden, breaks the shared-engine requirement).
- **Gaps / risks:**
  - Wiring our updated Rust backend into AnkiDroid's build is non-trivial.
  - iOS users are unserved this phase.

### D9 — Sync: reuse Anki's built-in protocol via a self-hosted server

- **Status:** resolved
- **Chose:** reuse Anki's existing sync protocol with a **self-hosted sync server** (ships in `rslib`/`docs/syncserver`) — it already does two-way sync, offline-then-reconnect, and conflict handling.
- **Considered:** a custom sync layer (rejected — burns the week and risks lost/double-counted reviews); AnkiWeb cloud (rejected — can't self-host/control for a fork demo).
- **Gaps / risks:**
  - Must stand up + document the self-hosted server.
  - The conflict rule is Anki's (collection-level); we must document exactly what wins for the sync test (assignment 7b).

### D10 — UI: extend Anki's native Svelte/TS web views

- **Status:** resolved
- **Chose:** build Manifold's new surfaces (readiness dashboard + lesson/review loop) as **new mediasrv pages** in Anki's native Svelte/TS web stack, so desktop and mobile share one engine and one build.
- **Considered:** a separate SPA over HTTP (rejected — duplicates the build and diverges desktop/mobile); native Qt widgets (rejected — not shareable with the phone).
- **Gaps / risks:**
  - Ramp-up on Anki's web stack + mediasrv; styling inside Anki's shell.

### D11 — The three scores (separate, each with a range)

- **Status:** resolved
- **Chose:** show three _separate_ scores, never blended: **Memory** = FSRS recall probability `R`; **Performance** = `P(correct on a fresh exam-style item)` modeled from skill mastery + item difficulty + timing + coverage; **Readiness** = blueprint-weighted aggregate → projected scaled score (200–990) with a likely range + a confidence note. Every score is shown with its range, the % of exam covered, last-updated time, top reasons, and the give-up rule (D12).
- **Considered:** one blended "% ready" (rejected — the assignment forbids it and it's dishonest); letting Performance equal Memory (rejected — that _is_ the bridge we must build; the paraphrase test, assignment 7d, proves the gap).
- **Gaps / risks:**
  - Performance + Readiness can't be validated against real exam outcomes in a week (Step 4, **out of scope**) — we grade the _steps of the bridge_, not a final number.
  - Phase 1 has no performance signal (D6); only Memory is live until Phase 2.

### D12 — The give-up rule (abstain thresholds)

- **Status:** resolved
- **Chose:** Manifold shows **no readiness score** until **≥ 200 graded reviews AND ≥ 50% blueprint coverage**; below the line it shows what evidence is missing and the single best next thing to study, not a number.
- **Considered:** always show a number (rejected — honesty rule, automatic fail); a much higher bar (rejected — too conservative to demo in a week).
- **Gaps / risks:**
  - Thresholds are chosen, not empirically derived — revisit with data.

### D13 — Readiness → scaled-score mapping

- **Status:** resolved
- **Chose:** map blueprint-weighted **expected raw-correct** → a scaled score on 200–990 via a monotonic function **anchored on the real ETS distribution** (mean 676 ≈ 50th pct, SD 154, n=7,452, 2019–2023), with an uncertainty band derived from per-skill variance + coverage. Reported as a **range**, always.
- **Considered:** claim a precise scaled number (rejected — fabrication, automatic fail); show percentile only (rejected — the assignment wants the real scale).
- **Gaps / risks:**
  - ETS does not publish raw→scaled tables, so the mapping is an explicit _approximation_; it is uncalibrated against real outcomes (Step 4, out of scope). Honest by construction — we surface it as an estimate with a range.

### D14 — AI generation (Phase 2): live LLM → verified item bank

- **Status:** resolved
- **Chose:** when a skill is due (Phase 2, AI on), a **live LLM generates a fresh problem** for that skill → a **runtime verifier** checks it → it's **persisted to a verified item bank** (every served item is source-traced + replayable). Eval against a keyword/vector **baseline** on a ≥50-item **gold set**, with a pre-set passing cutoff and prompt-injection defenses. With AI off, the app serves the Phase-1 skill cards (D6) / the pre-seeded verified bank.
- **Considered:** deterministic parametrized templates (the user preferred runtime LLM novelty; templates retained as one allowed _generator class_ under the verifier); live-only with no bank (rejected — not offline-capable or traceable).
- **Gaps / risks:**
  - Live generation adds cost + latency; the verifier is itself an AI component needing its own eval.
  - The bank must be pre-seeded for the AI-off demo.

### D15 — Ablation study feature: interleaving

- **Status:** resolved
- **Chose:** the learning-science feature under test is **interleaving** (mixing skills across topics within a session). Pre-registered metric: accuracy on held-out mixed-topic items at equal study time. Three builds: full Manifold / interleaving-off (blocked practice) / plain unmodified Anki.
- **Considered:** successive relearning and generative variation (both deferred — interleaving has the cleanest on/off toggle and direct math-specific evidence: Rohrer & Taylor 2007, +~250% on a delayed test).
- **Gaps / risks:**
  - A one-week test means small N + a short retention interval; the result may be null — which is an acceptable, reportable outcome.

### D16 — Docs home

- **Status:** resolved
- **Chose:** keep the umbrella `PRD.md` at the repo **root** (filling the existing file); put specs, this decision log, the iterations log, the backlog, and Manifold's `AGENTS.md` front door under **`docs/manifold/`**. Do not touch Anki's root `AGENTS.md` / `CLAUDE.md` / `docs/`.
- **Considered:** everything under `docs/manifold/` (rejected — keep the PRD visible at root, matching the pre-existing empty `PRD.md`); everything at root (rejected — clutters the Anki fork root).
- **Gaps / risks:**
  - Two `AGENTS.md` files now exist (Anki's at root, Manifold's in `docs/manifold/`) — `docs/manifold/AGENTS.md` is the authority for Manifold work; note the precedence there.

### D17 — License & attribution

- **Status:** resolved
- **Chose:** AGPL-3.0-or-later for the fork, with credit to Anki (some Anki parts are BSD-3-Clause); AnkiDroid is AGPL too.
- **Considered:** n/a — assignment hard requirement.
- **Gaps / risks:**
  - Keep AGPL headers + attribution on new files; verify license compatibility for any added dependency.

### D18 — Problem-wrapper + objective grading (supersedes D6)

- **Status:** resolved (supersedes D6)
- **Chose:** Manifold never shows the raw Anki card. A problem-player wrapper presents, for each due skill, 'A problem about [skill]' with controls A-E + Don't know; correctness drives FSRS (A = correct -> Good; B-E/Don't know = miss -> Again). In the MVP no problems are generated or faked (placeholder mode); a single `getProblem` seam (`ts/lib/manifold/session.ts`) is where Phase-2 AI generation plugs in, returning real stems/choices on the same shape. The spaced-introduction / mastery / three-score pipeline runs off these correctness inputs.
- **Considered:** keeping D6 self-graded skill cards (rejected: self-grading measures confidence, not performance; objective problem correctness is the bridge).
- **Gaps / risks:**
  - placeholder correctness only exercises the pipeline, not real ability (the give-up rule + a persistent placeholder banner keep readiness honest); the ETS readiness scaled-score mapping is deferred to a calibration phase.

### D19 — Readiness raw→scaled mapping, implemented (realises D13)

- **Status:** resolved
- **Chose:** implement the deferred §4.3 map in `scoring.ts`: blueprint-weight-weighted expected performance `p̄` → percentile via a chosen normal `Φ((p̄ − p50)/σ_p)` → scaled via the ETS anchor table (piecewise-linear, normal fit in the tails), reported as a **range** with point, confidence and top drivers, rounded to the scale's 10s and clamped to 200–990. The constants (`median_raw_fraction = 0.5`, `performance_sd = 0.18`, `coverage_band_lambda = 0.1`) live in `blueprint.json` as data and are **chosen, not derived** (like the D12 thresholds). Anchors/scale flow to TS via the topic-graph RPC (`ScoringConfig`), single-sourced from the blueprint.
- **Considered:** a bare linear `p̄ → scaled` (rejected — ignores the ETS distribution); duplicating the anchor table into TS (rejected — two sources of truth); an IRT ability model (rejected — needs item difficulties + far more data, Phase 3+).
- **Gaps / risks:**
  - ETS never published raw→scaled tables, so the map is an explicit approximation, uncalibrated against real outcomes (Step 4, out of scope). Honest by construction: always a range + evidence + confidence, plus a placeholder banner while inputs are placeholder problems (spec `spec-readiness-levels.md` §7).

### D20 — Give-up evidence = independent (unsupported) attempts (refines D12)

- **Status:** resolved (refines D12)
- **Chose:** the give-up rule counts only **independent** reviews — revlog `Review`-kind attempts, made cold after a card graduates — not all graded attempts. The two thresholds are unchanged (≥ 200 independent reviews AND ≥ 50% coverage), with a `confident` tier at ≥ 600 & ≥ 80%.
- **Considered:** keep the gate on all graded attempts and only filter the displayed value (rejected — splits "enough evidence" from "the evidence that counts"; the honest bar is unsupported attempts, even though it is stricter and can move a collection back to abstaining until Review-kind attempts accrue).
- **Gaps / risks:**
  - Stricter than the old bar; a collection whose reviews are mostly Learning/Relearning will abstain longer, which is the intended, more conservative behaviour.

### D21 — Performance = unsupported (Review-kind) accuracy (refines D11)

- **Status:** resolved (refines D11)
- **Chose:** `performance` is accuracy on `Review`-kind revlog attempts only; Learning/Relearning (scaffolded) attempts are excluded. Memory is unchanged (it reads FSRS `R`, not the revlog). Each card is also labelled by a **teaching level** derived from its `CardType` (New/Learn/Review/Relearn → New/Guided/Independent/Revisited), surfaced on `SessionItem` and as per-topic counts on `TopicNode`.
- **Considered:** count all graded attempts (rejected — supported attempts inflate a score meant to measure cold performance, reintroducing the memory↔performance blur D11 exists to prevent).
- **Gaps / risks:**
  - Levels are labelled but not yet acted on: the player still renders the D18 placeholder problem regardless of level. Rendering scaffolds per level is later work.

### D22 — Unlock a topic only when its prerequisites are _mastered_ (refines D5)

- **Status:** resolved (refines D5)
- **Chose:** a topic unlocks its dependents only when it is itself `mastered` —
  its mastered fraction reaching its own **tier target** (relearn 0.9 / teach 0.8
  / recognize 0.3) — so `mastered` is the single currency for progression. The
  previous flat `unlock_mastered_fraction = 0.6` gate is removed from
  `blueprint.json` and the `Thresholds` struct; `lock_state` now gates on a
  per-topic `mastered` map (`mastery.rs`).
- **Why:** the 0.6 gate was an undocumented implementation default that sat
  _below_ the mastery bar and was not tier-aware, so (a) a dependent could open
  while a relearn/teach prerequisite was well short of mastered — under the ~80%
  criterion of the mastery-learning lever the BrainLift is built on (Insight 1) —
  and (b) a recognize-tier topic could read `mastered` (0.3) yet still fail to
  unlock its children (needed 0.6), so the badge and the unlock it granted could
  disagree. Gating on mastery aligns with mastery learning, surmountable
  desirable difficulty (Bjork), and the knowledge-foundation / cognitive-load
  case for solid prerequisites; FSRS retrievability (R) is the right quantity to
  gate on.
- **Considered:** a separate, principled "ready-to-start" threshold below mastery
  (kept as a future option — would preserve more early cross-topic interleaving
  at the cost of a second knob); leaving the flat 0.6 (rejected — under-delivers
  the mastery mechanism and contradicts the mastered badge).
- **Gaps / risks:**
  - A stricter gate opens topics more slowly, so early sessions lean harder on
    the root topics and there is less cross-topic interleaving until the first
    prerequisites are mastered — an intended trade for a solid foundation.

### D23 — Per-tier recall depth; recognition-grade mastery for the tail (refines D5/D22)

- **Status:** resolved (refines D5, D22)
- **Chose:** the per-skill recall bar for "mastered" is now **per tier**
  (`tier_recall` in `blueprint.json`): relearn/teach demand execution-grade
  recall (**0.9**), recognize a lower recognition-grade bar (**0.7**). The
  recognize-tier mastered-fraction target rises **0.3 → 0.6**, and the flat
  `thresholds.mastery_recall` is removed. Net: a recognize topic is "mastered"
  when ~60% of its skills reach recognition-grade recall, not 30% at
  execution-grade — broad and shallow, matching how the tail is actually used.
- **Why (learning science):** the recognize tier exists for _recognition_, an
  easier retrieval form than recall/execution (the retrieval-strength hierarchy;
  Bjork). The BrainLift's own math has the ~33 non-calculus questions mostly
  _guessed_, with recognition nudging the odds — which rewards broad-shallow
  coverage over narrow-deep. The old "30% at 0.9" applied an execution-grade bar
  to material we only need to recognize, and made "mastered" a near-empty claim.
  relearn/teach keep the 0.9 execution bar (fluency on the calculus core — the
  "20% that drives 80%"); teach's 0.8 fraction stays (Bloom's ~80% mastery
  criterion). Structurally safe: every recognize topic is only ever a
  prerequisite of other recognize topics, so retuning the tail never slows the
  core (verified against the blueprint DAG).
- **Considered:** raising the recognize _fraction_ while keeping the flat 0.9
  recall (rejected — piles execution-grade study onto the tail, the wrong _kind_
  of knowledge and against scope-to-median); leaving 0.3 at 0.9 (rejected — see
  above). The give-up/readiness statistical constants were deliberately left
  untouched: learning science does not set them (they need calibration), and
  dressing them in a learning-science rationale would be a "lethal mutation."
- **Gaps / risks:**
  - The recall bars (0.9 / 0.7) and the fractions are still _chosen_ defaults,
    not calibrated against outcomes (Step 4, out of scope); FSRS `R` is a recall
    proxy for "recognition depth," not a direct recognition measure.

### D24 — Teaching level is competence-driven, decoupled from CardType (refines D21)

- **Status:** resolved (refines D21)
- **Chose:** a card's teaching/scaffolding **level** (New / Guided / Independent /
  Revisited) is derived from demonstrated **competence**, not Anki's `CardType` /
  learning-steps calendar: New = never attempted; Independent = at least
  `independent_successes` (=1, in `blueprint.json`) correct retrievals (button ≥
  Good), so it is reachable the _same day_ via learning-step reps; Revisited =
  currently relearning after a lapse (`CardType::Relearn`, the one place that
  signal is correct); Guided otherwise. Shared `teaching_level` helper in
  `mastery.rs`, used by both the topic rollup and the session queue.
  **Performance / readiness evidence is unchanged** — it still counts only cold,
  unsupported `Review`-kind attempts (D20/D21).
- **Why:** level was welded to `CardType`, so "Independent" required graduation
  and was unreachable on day one — an artifact of Anki's fact-memorization
  mechanic, not a Manifold pedagogy. Two axes were tangled: _how much scaffolding
  a problem gives_ (should fade with competence, early — worked-example → faded →
  solo) and _whether an attempt is cold performance evidence_ (should lag, by
  design). Decoupling lets a motivated learner reach solo problems immediately
  (retrieval practice is the highest-utility activity; don't calendar-gate it)
  while keeping the performance signal honest.
- **Considered:** shortening Anki's learning steps so cards graduate day one
  (rejected — would let fresh-card attempts count as `Review`-kind and corrupt
  the Performance signal with what is really memory); instantaneous recall `R` as
  the competence signal (rejected — inflated to ~1 right after any review, so it
  would flag almost everything Independent); leaving levels CardType-derived
  (rejected — see above).
- **Gaps / risks:**
  - Set to **1**, not 2: a card hits its 2nd success exactly as it graduates,
    after which it is not due again for days — so a bar of 2 left "Independent"
    unreachable the same day (the original symptom). At 1, the first correct
    retrieval makes the skill's _next_ appearance (still a same-day learning
    review) Independent; a skill only shows Guided while it is being missed.
  - `independent_successes = 1` is a chosen default, not calibrated; success
    counts include massed learning-step reps, which fade _scaffolding_
    legitimately but are not durable-learning evidence (that stays on
    `Review`-kind).
  - Levels are still only labels: the player does not yet vary the problem by
    level (the D21 gap remains until Phase-2 real problems).

### D25 — Mastery = FSRS stability, per tier (supersedes D23)

- **Status:** resolved (supersedes D23)
- **Chose:** a skill is `mastered` when the mean FSRS **stability** of its cards
  reaches its tier's bar (`tier_stability`, in days: relearn/teach **21** ≈
  Anki's "mature" line, recognize **7**), replacing D23's per-tier recall bars.
  Mastery now depends on **stability and nothing else** (per tier), not
  instantaneous retrievability `R`. Topic mastery is unchanged (mastered fraction
  ≥ `tier_targets`: relearn 0.9 / teach 0.8 / recognize 0.6), and the **Memory
  score still reads `R`** (`avg_recall`); only the discrete mastered flag moved.
- **Why (learning science):** `R` is retrieval strength — volatile and ≈1 right
  after any review, so an `R ≥ 0.9` bar marked a skill "mastered" after a single
  correct answer (recency inflation). Stability is FSRS's durability estimate
  (storage strength) and only climbs through spaced, repeated successful
  retrieval (successive relearning), so a stability bar encodes durable learning
  and cannot be reached in a day. This is the "learning ≠ performance / infer
  learning from durability" principle (Soderstrom & Bjork; Bjork & Bjork). Kept
  per-tier so the scoped-to-median depth strategy (D5/D23) survives: the
  recognition tail masters at lower durability than the calculus core.
- **Scope / honesty:** `mastered` is a **memory** claim (durably remembered),
  deliberately separate from the Performance score (cold accuracy). Fine while
  problems are placeholders; if mastery should later also require demonstrated
  performance, that is a future decision. It also stays a pure engine read — the
  scheduler/FSRS is untouched (D3); we only threshold a value Anki already emits.
- **Considered:** a single uniform stability bar (rejected — discards the tier
  depth strategy); keeping `R` (rejected — recency-inflated, one tap = mastered);
  counting N cold `Review`-kind successes (viable and more literal, but stability
  already encodes spaced repeated success and is Anki-native).
- **Gaps / risks:**
  - Thresholds (21d / 7d) are chosen, not calibrated; 21d mirrors Anki's mature
    line. Because 21-day stability takes ~2 weeks of spaced success, nothing
    masters — and no new DAG topics unlock — within a day. Honest for the real
    study plan, but a same-day demo won't show mastered/unlocks.
  - Stability is FSRS's declarative-recall durability; treating it as skill
    mastery is the same modeling assumption flagged in D4/D11, to validate by
    calibration.

### D26 — `in_progress` tracks studied, not mastered (fixes D25 fallout)

- **Status:** resolved (refines D22/D25)
- **Chose:** a topic is `in_progress` (the DAG's green state) when it is studied
  but not yet mastered — `avg_stability > 0` (≥1 card with an FSRS memory state) —
  instead of `mastered_fraction > 0` (≥1 mastered skill).
- **Why:** D25 made mastery require ~21-day stability (weeks of spaced review), so
  `mastered_fraction > 0` became unreachable by same-day study. A topic therefore
  jumped straight `unlocked → mastered` and **never showed green while actively
  studied**, making the dashboard look dead (the reported "no green icons").
  Tracking "studied" restores the intended progression `unlocked` (grey) →
  `in_progress` (green) → `mastered` (violet), and reads the same FSRS-state
  signal as mastery for consistency.
- **Gaps / risks:**
  - "Studied" counts any card with a memory state (even one review) — the
    intended low bar for "you've started this topic."

### D27 — Unlock on "studied enough," not mastered (supersedes D22)

- **Status:** resolved (supersedes D22's unlock rule)
- **Chose:** a topic unlocks its dependents once each prerequisite is _studied
  enough_ — `studied_fraction ≥ unlock_studied_fraction` (0.6): at least 60% of
  its skills have an FSRS memory state (been seen) — a lower "ready to build on"
  bar, not mastery. `mastered` (the violet badge) stays the separate 21-day
  stability goal (D25) and no longer gates unlocking.
- **Why:** D22 gated unlocking on prerequisite _mastery_; once D25 made mastery a
  ~21-day-stability bar (weeks of spaced review), that combination — plus a
  single-root DAG (`elementary_algebra` is the only topic with no prereqs) —
  stranded the learner: only the root is open, its cards get worked through in one
  session, and nothing else unlocks for weeks (the observed "why did I run out of
  cards"). Learning science favours a two-threshold design: unlock on a
  _surmountable_ foundation (Bjork — desirable difficulty needs the prerequisite
  in place; Willingham/Sweller — knowledge is the foundation), keep progression
  flowing for interleaving (Rohrer, D15) and steady wins
  (motivation-follows-achievement, Hendrick), while durable _mastery_ stays the
  higher, separate bar. Gating on coverage (studied) does exactly that.
- **Considered:** unlock on first touch / `in_progress` (rejected — one card is no
  foundation, so the dependent would not be surmountable); lower the stability
  mastery bar to a few days so unlock-on-mastery is fast (rejected — re-welds
  unlocking to the badge and cheapens "mastered": 3-day retention is not durable,
  a lethal mutation of D25); leave it (rejected — unusable, stuck on 1 of 33
  topics for weeks).
- **Gaps / risks:**
  - `unlock_studied_fraction = 0.6` is chosen, not calibrated; "studied" counts a
    skill seen at least once (coverage of exposure, not depth). The scheduler
    keeps drilling the prerequisite via reviews, so the foundation continues to
    strengthen after the dependent opens.

### D28 — Unlock on the mastery-learning criterion (supersedes D27)

- **Status:** resolved (supersedes D27)
- **Chose:** a topic unlocks its dependents once each prerequisite is _competent
  enough_ — `competent_fraction ≥ unlock_competent_fraction` (0.8): at least 80%
  of its skills answered correctly (Bloom's mastery-learning criterion). A skill
  counts as competent when it reaches the Independent/Revisited teaching level
  (≥ 1 successful retrieval, D24). This is _competence now_, reachable in a
  session — distinct from durable stability-based `mastered` (D25, the violet
  badge, weeks).
- **Why:** D27 gated unlocking on _studied_ (mere exposure — 60% of skills seen),
  which is not mastery learning: it counts skills seen and even answered wrong.
  Mastery learning (Bloom, ~1σ; BrainLift Insight 1) gates advancement on
  demonstrated competence, not exposure. The trap that produced D27 was
  conflating two masteries: the _mastery-learning criterion_ (competent now,
  ~80% correct, reachable) versus _durable mastery_ (21-day stability, weeks).
  Unlocking belongs on the former; the violet badge stays the latter.
- **Considered:** unlock on durable mastery (D22 — weeks, strands the learner on
  the single root); unlock on exposure (D27 — not mastery learning); a
  lower/other competence bar.
- **Gaps / risks:**
  - While problems are placeholders, "answered correctly" is a tap on the
    placeholder A control, so the gate is only as real as the problems; it
    becomes a genuine competence gate when Phase-2 generated problems land. The
    structure (unlock on competence) is correct regardless.
  - `unlock_competent_fraction = 0.8` and the per-skill "competent = ≥ 1 success"
    bar (via `independent_successes`) are chosen, not calibrated.

### D29 — Session covers tiers in order: circles → squares → diamonds

- **Status:** resolved
- **Chose:** the session queue is now **tier-major** — it serves relearn (circle)
  topics before teach (square) before recognize (diamond). Within a tier it still
  orders by points-at-stake (`weight × weakness`) and interleaves across topics;
  a later tier never precedes an earlier one. The new-card daily budget also fills
  lower tiers first (`ordered_by_tier` + a tier-major sort before the
  `new_per_day` truncate, `session.rs`).
- **Why:** ordering was points-only (blueprint weight), so among available topics
  a high-weight teach/recognize card could be served before a relearn one. The
  intended study order is foundational-first: relearn the calculus you have, then
  teach the new core, then only recognize the tail (D5; BrainLift). Tier-major
  ordering makes coverage follow that sequence.
- **Trade-off:** tier now outranks points-at-stake _across_ tiers (a low-value
  relearn card precedes a high-value recognize card); points still orders _within_
  a tier. Interleaving (D15) now spreads topics within a tier rather than across
  all topics — a later tier is blocked until earlier tiers are served in this
  queue. The DAG unlock gate (D28) already enforces much of this; tier ordering
  makes it explicit for topics that are simultaneously available.
- **Gaps / risks:**
  - Due reviews are also tier-ordered, so a barely-due relearn review precedes a
    very-overdue recognize review; acceptable given the foundational-first intent.

### D30 — Tier display labels: Core / Target / Reach

- **Status:** resolved
- **Chose:** the UI shows the tiers as **Core** (relearn), **Target** (teach), and
  **Reach** (recognize), via `tierLabel()` in `graph.ts`, used by the DAG legend,
  the topic panel, and node aria-labels. The internal ids stay
  `relearn`/`teach`/`recognize` (blueprint keys, `mf::tier::*` tags, engine match
  arms, tests) — a display-label layer only, so no data/tag/test churn and no
  re-seed.
- **Why:** clearer, more motivating names (the foundation you have → the material
  you _target_ for the median → the tail you _reach_ for), without renaming a
  stable identifier threaded through the whole data model.
- **Gaps / risks:** internal ids and display labels now differ; `tierLabel` is
  the single mapping point. A future full rename could align them (needs a tag
  migration / re-seed).

### D45 — Firebase Google login + real-time progress mirror (extends D9)

- **Status:** resolved
- **Chose:** add **Firebase Authentication (Google)** for identity and a **Firestore
  real-time _progress mirror_** on top of the existing engine. After each graded
  answer (and on dashboard load) the client derives the three scores from
  `getTopicGraph` and writes a compact snapshot to `users/{uid}`; every signed-in
  device subscribes with `onSnapshot`, so progress updates live across a second
  desktop, the phone, and the web. The Anki collection (cards/revlog) stays the
  scheduling source of truth, still synced by Anki's own protocol (D9 unchanged).
  One shared TS layer (`ts/lib/manifold/firebase*.ts`, `progress.ts`, `sync.ts`,
  `SyncPanel.svelte`) serves desktop, Android, and web because they render the same
  Svelte pages. Project: `manifold-gre`.
- **Considered:** (a) making Firebase the scheduling backbone by mirroring review
  _events_ and replaying them into each device's collection — rejected for now: it
  re-implements Anki sync, fights FSRS's need for a consistent local SQLite, and
  risks double-counting against D9 (kept as a future option). (b) A read-only web
  dashboard as the only "mobile" surface — superseded once the AnkiDroid app was
  found already built, so the same shared code carries the mirror to the phone.
- **Sign-in per shell (Google blocks OAuth in embedded webviews):** real browser
  (web) → `signInWithPopup`; **desktop Qt webview** → a system-browser **loopback**
  (`mediasrv` `manifoldGoogleSignIn` opens the OS browser, harvests the Google ID
  token, returns it; the webview does `signInWithCredential`) — no secret/extra
  OAuth client, uses `localhost` (added to authorized domains) + the public web
  config; **Android** → native **Credential Manager** (`ManifoldPage` JS bridge,
  web client as `serverClientId`) hands the ID token to the webview.
- **Security:** owner-only Firestore rules (`request.auth.uid == userId`), strict
  schema + size caps, immutable `uid`, recent `updatedAt`. Verified against the
  emulator (real rules): real-time cross-client propagation + cross-user read/write
  denial + schema-pollution rejection all pass (5/5). Web apiKey is public by
  design (committed); no secret is required for any surface.
- **Gaps / risks:** desktop/Android Google sign-in need one interactive Google
  consent each (by design). The Android APK must be rebuilt to ship the bridge +
  bundle firebase (`bash redeploy.sh`; backend `anki/package.json` now lists
  firebase); on-device Google login is the remaining manual verification. The
  event-replay scheduling sync (option a) is deliberately not built.

---

<sub>Created with the `plan-prd` skill · maintained with `log`.</sub>
