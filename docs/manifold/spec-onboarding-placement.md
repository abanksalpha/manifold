# Spec — new-user onboarding + placement diagnostic

> **Status:** design, approved 2026-07-05. Decision log entry: **D46**
> (`alternatives.md`). Implementation plan:
> [`plan-onboarding-placement.md`](plan-onboarding-placement.md).

## 1. Problem

A brand-new Manifold learner boots straight into `/manifold` and sees Readiness
**Abstaining** with a single "study next" nudge on the root topic. The app has no
idea what the learner already knows, so it starts everyone at the DAG roots
(elementary algebra) and makes an AP-Calc-ready undergrad grind through material
they mastered years ago. There is no first-run flow, no self-report, and no
diagnostic.

This feature adds an **onboarding placement**: on a fresh account we ask which
courses the learner has taken, give a short cold diagnostic across the topics
those courses cover, and use the result to **seed** the learner's starting point
in the prerequisite DAG so known material is not re-taught — raising the
_granularity of confidence_ about where the learner stands, per topic.

## 2. Goals / non-goals

**Goals**

- On first run of a fresh collection, route the learner into an onboarding wizard
  before the home dashboard.
- Let the learner self-report completed courses (a coarse prior); map courses to
  blueprint topics.
- Serve a short, blueprint-weighted **cold** diagnostic across the reported
  topics, reusing the existing verified problem pipeline.
- Seed the learner's per-topic starting level from the diagnostic + self-report,
  writing **real** card state through Anki's normal answer path so the existing
  engine and all three scores pick it up with no parallel source of truth.
- Keep the honest, gated Readiness score **completely untouched** — it must still
  abstain until the give-up rule (≥200 independent Review-kind reviews AND ≥50%
  coverage) is met. Placement never produces an early or ungated readiness number.

**Non-goals**

- No new "placement estimate" readiness score or lowered give-up gate (explicitly
  rejected during brainstorming — honesty-first).
- No change to FSRS, scheduling, sync, or the scoring formulas.
- No adaptive item-response theory; the diagnostic is a fixed, blueprint-weighted
  sample, not a CAT.
- Mobile is out of scope for this pass (desktop-first, D31); the shared TS runs on
  Android later unchanged.

## 3. Key constraint that shapes the design

Manifold's Performance and Readiness scores count **only `Review`-kind revlog
entries** (`rslib/src/manifold/mastery.rs` §Performance). A first answer on a
_New_ card produces a **`Learning`-kind** entry — it sets the card's FSRS memory
state and its teaching level, but is **not** counted as independent-review
evidence. This is exactly what we want: placement answers (and seeds) feed
**Memory** and the **teaching-level / unlock** machinery, while the gated
**Readiness** stays abstaining until the learner has done real cold reviews. No
special handling is needed to protect the give-up rule — using the normal grade
path on New cards gives the honest behaviour for free.

## 4. User flow

```
fresh collection (no manifold history)
        │  GetPlacementState → completed=false
        ▼
/manifold  (+page.ts load) ── redirect(307) ──▶ /manifold-onboarding
                                                       │
        ┌──────────────────────────────────────────────┘
        ▼
  Phase 1  Setup      import the GRE seed deck if the collection has no skill cards
  Phase 2  Courses    "Which have you taken?" — checklist of courses → topic ids
  Phase 3  Diagnostic short cold exam over the reported topics (verified problems)
  Phase 4  Summary    per-topic map (known / shaky / new); Apply → seed + mark done
        │  ApplyPlacement(known_topic_ids) → seeds cards, sets completed=true
        ▼
/manifold  (no redirect; personalized DAG, Memory reflects seeded priors)
```

A "Retake placement" control on the home links straight to `/manifold-onboarding`
(bypasses the gate), so the flow is repeatable.

## 5. Architecture

Layered exactly like the rest of Manifold: a thin engine change in Rust exposed
over new RPCs, consumed by a new Svelte route that reuses the session player's
problem primitives.

### 5.1 Engine (Rust, `rslib/src/manifold/placement.rs` — new)

Three operations, added to `ManifoldService`:

- **`get_placement_state()` (read-only)** → `PlacementStateResponse { completed }`.
  `completed` is true when the collection config flag `manifoldOnboardingDone`
  is set, **or** the collection already carries manifold study history (any topic
  with `graded_reviews > 0`), so pre-existing users are never forced into the
  wizard.
- **`build_placement_exam(topic_ids, per_topic)` (read-only)** →
  `SessionQueueResponse` (reuses `SessionItem`). Selects up to `per_topic` skill
  cards from each requested blueprint topic, forces `level = 2` (cold,
  Independent presentation), orders by blueprint weight interleaved across
  topics, and caps the total at `PLACEMENT_MAX_ITEMS`. Unknown topic ids fail
  loudly. This only reads/selects cards — it never mutates.
- **`apply_placement(known_topic_ids)` (mutating — the first mutating manifold
  RPC)** → `ApplyPlacementResponse { seeded_cards }`. For each known topic, finds
  its **not-yet-attempted** skill cards (`is:new`), grades them **Good** through
  `col.grade_now` (Anki's normal answer path → `Learning`-kind revlog + FSRS
  state → teaching level Independent), tags their notes `mf::placement` for
  transparency/reset, and finally sets `manifoldOnboardingDone = true`. Directly
  answered probe cards are already `is:new`-excluded, so they are never
  re-seeded.

`known_topic_ids` is expected to already include the transitive prerequisite
closure of the known topics (computed client-side, §5.3), so seeding leaves the
DAG coherent: a learner who reports Calculus II also has its Calculus I
prerequisites seeded, so the reported topics actually unlock.

### 5.2 Bindings + serving (mediasrv)

- New RPCs added to `exposed_backend_list` in `qt/aqt/mediasrv.py`:
  `get_placement_state`, `build_placement_exam`, `apply_placement`.
- New custom POST handler `manifold_import_seed` (in `post_handler_list`) that
  imports the seed deck into the open collection by reusing
  `manifold/content/import_seed.py::import_seed(aqt.mw.col)` — no new import
  logic, idempotent, fails loudly if the seed/blueprint files are missing.
- `"manifold-onboarding"` added to `is_sveltekit_page()` so the route loads in the
  webview and in-app navigation stays in-webview.

### 5.3 UI (Svelte/TS)

- **`ts/lib/manifold/placement.ts` (new)** — pure, unit-tested logic:
  - `COURSES`: the course → topic-id map (§6).
  - `topicsForCourses(courseIds)` → the set of blueprint topic ids covered.
  - `verdictForTopics(...)` → per-topic verdict `known | shaky | new` from probe
    accuracy + self-report, and `knownTopicIds(...)` = the seed set including the
    transitive prerequisite closure over the reported/known topics.
  - thin wrappers over the three new RPCs and `manifoldImportSeed`.
- **`ts/routes/manifold-onboarding/+page.svelte` + `+page.ts` (new)** — the four
  phase wizard. The diagnostic phase reuses `SessionRunner`, `fetchProblem` /
  `pull`, `isCorrect`, and `grade` from `ts/lib/manifold/session.ts` in a lean
  cold player (stem + 5 choices + "Don't know", no lecture/scaffold/hints,
  progress bar, quit-anytime). Answering a probe calls the existing `grade` →
  `gradeNow`. Reuses `Button`, `Meter`, `MathText`, `mathmarkup` components.
- **Home gate** — `ts/routes/manifold/+page.ts` also calls `getPlacementState`;
  when `!completed` it `redirect(307, "/manifold-onboarding")`. A "Retake
  placement" link is added to the home masthead/Today section.

## 6. Course → topic map

Covers all 33 blueprint topics; each topic belongs to at least one course. The
map lives in `placement.ts`; `build_placement_exam` validates every id against
the blueprint and fails loudly on drift.

| Course                          | Blueprint topic ids                                                                     |
| ------------------------------- | --------------------------------------------------------------------------------------- |
| Precalculus                     | `elementary_algebra`, `precalc_functions`, `trigonometry`, `coordinate_geometry`        |
| Calculus I (differential)       | `limits_continuity`, `differential_calc`, `applications_derivatives`                    |
| Calculus II (integral & series) | `integral_calc`, `integration_techniques`, `applications_integrals`, `sequences_series` |
| Calculus III (multivariable)    | `multivariable_diff`, `multivariable_int`, `vector_calc`                                |
| Differential equations          | `differential_equations`                                                                |
| Linear algebra                  | `linear_algebra_core`, `vector_spaces`, `eigen`                                         |
| Abstract algebra                | `group_theory`, `rings_fields`                                                          |
| Number theory                   | `number_theory`                                                                         |
| Discrete math / combinatorics   | `logic_sets`, `combinatorics`, `graph_theory`, `algorithms`                             |
| Probability & statistics        | `probability`, `statistics`                                                             |
| Real analysis                   | `real_analysis_sequences`, `real_analysis_topology`, `metric_topology`                  |
| Complex analysis                | `complex_analysis`                                                                      |
| Geometry                        | `geometry`                                                                              |
| Numerical analysis              | `numerical_analysis`                                                                    |

## 7. Verdict + seeding policy

Per in-scope topic, from the probe results `{answered, correct}` and whether its
course was self-reported:

- **known** — `answered ≥ 1` and `correct/answered ≥ 0.5`; OR self-reported and
  every probe abstained (untested-by-report, a labeled prior). → **seed to
  Independent**.
- **shaky** — `answered ≥ 1` and `0.25 ≤ correct/answered < 0.5`. → **not
  seeded** (taught normally, flagged for review in the summary).
- **new** — everything else. → not seeded.

`knownTopicIds` = **the transitive prerequisite closure of the `known` topics**
(topics with verdict `known`, which includes reported-but-untested ones) —
knowing X implies its prerequisites, so the DAG stays coherent after seeding. A
reported topic that tested `shaky`/`new` is not `known`, so neither it nor its
prerequisites are force-seeded. Seeds are graded Good (Independent) and tagged
`mf::placement`.

Thresholds (`KNOWN_ACCURACY = 0.5`, `SHAKY_ACCURACY = 0.25`, `per_topic = 1`,
`PLACEMENT_MAX_ITEMS = 30`) are constants, tunable in one place.

## 8. Honesty safeguards (repo rules)

- **Readiness untouched.** Seeds and probe answers on New cards are `Learning`-kind,
  never `Review`-kind, so `independent_reviews` stays 0 and the give-up gate is
  unaffected. A dedicated engine test asserts `independent_reviews == 0` while
  `level_independent > 0` after seeding.
- **Memory is a labeled prior.** Seeded cards contribute to the Memory score
  (they carry FSRS state) as a self-asserted, probe-confirmed prior (approved
  choice `accept_labeled`). They are tagged `mf::placement` so the summary can
  label them and a future reset can find them.
- **No fabrication / fail loud.** The diagnostic serves only verified problems;
  content gaps **abstain** and the topic is treated as untested (no fake item).
  Unknown topic ids, missing seed files, and malformed served items all raise.
- **Real state, one source of truth.** All seeding flows through `col.grade_now`
  and Anki tags/config — undo-safe and synced by Anki's own protocol; no parallel
  placement store.
- **First mutating manifold RPC.** `apply_placement` is the first manifold RPC
  that writes; `get_placement_state`, `build_placement_exam`, and the whole
  mastery/session path stay read-only. Logged in D46.

## 9. Data / wire contracts

New proto (`proto/anki/manifold.proto`):

```proto
service ManifoldService {
  // ...existing...
  rpc GetPlacementState(generic.Empty) returns (PlacementStateResponse);
  rpc BuildPlacementExam(PlacementExamRequest) returns (SessionQueueResponse);
  rpc ApplyPlacement(ApplyPlacementRequest) returns (ApplyPlacementResponse);
}

message PlacementStateResponse { bool completed = 1; }

message PlacementExamRequest {
  repeated string topic_ids = 1;   // validated against the blueprint
  uint32 per_topic = 2;            // >=1; total capped by the engine
}

message ApplyPlacementRequest {
  repeated string known_topic_ids = 1;  // includes prereq closure (client-side)
}

message ApplyPlacementResponse { uint32 seeded_cards = 1; }
```

`build_placement_exam` reuses `SessionQueueResponse { repeated SessionItem }`.
Collection config key: `manifoldOnboardingDone` (bool).

## 10. Testing strategy

- **Rust (`rslib/src/manifold/test.rs`)** — exam selection (per-topic cap, level=2,
  unknown-id error), seeding (New cards graded + tagged, already-attempted cards
  untouched, `seeded_cards` count, config flag set), and the honesty invariant
  (`independent_reviews == 0`, `level_independent > 0`, unlock advances after
  seeding). Reuses `add_skill_card` / `add_revlog`.
- **pylib (`pylib/tests/test_manifold.py`)** — RPC round-trips via `col._backend`.
- **TS (vitest, `ts/lib/manifold/placement.test.ts`)** — course→topic map covers
  all 33 topics, verdict thresholds, prereq-closure seed set.
- **e2e** — fresh seeded collection: home redirects to onboarding → pick courses →
  answer a couple of probes → summary → apply → home no longer redirects
  (`manifold/content/run_e2e_isolated.py`).
- **Final gate** — `just check` green.

```
```
