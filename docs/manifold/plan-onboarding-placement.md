# New-user onboarding + placement diagnostic — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** On a fresh account, route the learner into an onboarding wizard that
asks which courses they've taken, runs a short cold placement diagnostic across
the covered topics, and seeds their per-topic starting point in the DAG so known
material isn't re-taught — without touching the honest, gated Readiness score.

**Architecture:** A new Rust module `rslib/src/manifold/placement.rs` exposes
three RPCs (`GetPlacementState`, `BuildPlacementExam`, `ApplyPlacement`) on
`ManifoldService`. `BuildPlacementExam` selects cold probe cards (read-only);
`ApplyPlacement` seeds known topics by grading their unattempted skill cards Good
through Anki's normal answer path (`Learning`-kind → Independent teaching level +
FSRS memory state, never `Review`-kind), tags them `mf::placement`, and sets a
collection-config flag. A new `/manifold-onboarding` Svelte route drives the
wizard, reusing the session player's problem primitives. The home route redirects
to it until placement is completed.

**Tech Stack:** Rust (rslib), protobuf, Python (pylib bridge + Qt mediasrv),
Svelte/TypeScript (ts/), vitest, Playwright e2e. Build/test via `just`.

## Global Constraints

- Build/test only via `just` (never call ninja/scripts directly). A `.proto`
  change needs a full `just check` (codegen), not just `cargo check`.
- **No fabrication / fail loud, no silent fallbacks** (repo rule + user rule): a
  missing key/file, unknown topic id, or malformed served item raises; content
  gaps abstain honestly.
- **Readiness stays gated and untouched.** Placement answers and seeds are
  `Learning`-kind revlog entries, never `Review`-kind, so `independent_reviews`
  and the 200-review / 50%-coverage give-up rule are unaffected. This is a hard,
  tested invariant.
- **One source of truth.** All seeding flows through `col.grade_now` + Anki
  tags/config (undo-safe, synced by Anki's protocol). No parallel placement store.
- Seeded cards are tagged `mf::placement`; they count toward the Memory score as
  a labeled prior (approved: `accept_labeled`).
- Manifold tag scheme: `mf::topic::<id>`, `mf::skill::<id>`, `mf::tier::<tier>`.
  Collection config flag key: `manifoldOnboardingDone`.
- Follow the frozen spec: [`spec-onboarding-placement.md`](spec-onboarding-placement.md).
  Decision log entry: **D46** in `alternatives.md`.

---

## Task 1: Placement engine (proto + `placement.rs` + service wiring)

Adds the three RPCs, the read-only exam builder, and the mutating seeder. This is
the crux; it ends with `just check` green and Rust tests passing.

**Files:**

- Modify: `proto/anki/manifold.proto` (add 3 rpcs + 4 messages)
- Create: `rslib/src/manifold/placement.rs`
- Modify: `rslib/src/manifold/mod.rs` (register module)
- Modify: `rslib/src/manifold/service.rs` (impl 3 methods)
- Modify: `rslib/src/manifold/test.rs` (tests)
- Modify: `qt/aqt/mediasrv.py` (`exposed_backend_list`)

**Interfaces:**

- Consumes: `crate::manifold::blueprint::graph()`, `mastery::tag_suffix`,
  `Collection::{all_cards_for_search, grade_now, add_tags_to_notes,
  set_config_json, get_config_optional}`.
- Produces (Rust, for `service.rs`):
  - `placement::placement_completed(col: &mut Collection) -> Result<bool>`
  - `placement::build_placement_exam(col: &mut Collection, topic_ids: &[String], per_topic: u32) -> Result<Vec<SessionItem>>`
  - `placement::apply_placement(col: &mut Collection, known_topic_ids: &[String]) -> Result<u32>`
- Produces (wire): RPCs `getPlacementState`, `buildPlacementExam`,
  `applyPlacement`; messages `PlacementStateResponse { completed }`,
  `PlacementExamRequest { topic_ids, per_topic }` (returns `SessionQueueResponse`),
  `ApplyPlacementRequest { known_topic_ids }`, `ApplyPlacementResponse { seeded_cards }`.

- [ ] **Step 1: Add the proto RPCs and messages**

In `proto/anki/manifold.proto`, add the three RPCs inside `service ManifoldService`
(after `GetStudyToday`):

```proto
// Read-only: whether the learner has completed/skipped onboarding, or the
// collection already carries study history (a pre-existing user).
rpc GetPlacementState(generic.Empty) returns (PlacementStateResponse);
// Read-only: selects a short cold diagnostic (one probe per requested topic,
// level=2), reusing SessionItem. Unknown topic ids fail loudly.
rpc BuildPlacementExam(PlacementExamRequest) returns (SessionQueueResponse);
// Mutating (the first mutating manifold RPC): seeds the not-yet-attempted
// skill cards of each known topic to Independent via Anki's normal answer
// path, tags them mf::placement, and marks onboarding done. Learning-kind, so
// the readiness give-up rule is untouched.
rpc ApplyPlacement(ApplyPlacementRequest) returns (ApplyPlacementResponse);
```

Add these messages at the end of the file:

```proto
message PlacementStateResponse {
  bool completed = 1;
}

message PlacementExamRequest {
  // Blueprint topic ids to probe; empty means every topic. Validated against the
  // blueprint (unknown ids fail loudly).
  repeated string topic_ids = 1;
  // Max distinct-skill probes to draw per topic (>=1). The engine caps the total.
  uint32 per_topic = 2;
}

message ApplyPlacementRequest {
  // Topics the learner has demonstrated/asserted competence in (already includes
  // the transitive prerequisite closure, computed client-side). Their
  // not-yet-attempted skill cards are seeded to Independent.
  repeated string known_topic_ids = 1;
}

message ApplyPlacementResponse {
  // Count of skill cards seeded (graded Good + tagged mf::placement).
  uint32 seeded_cards = 1;
}
```

- [ ] **Step 2: Create `rslib/src/manifold/placement.rs`**

```rust
// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

//! Onboarding placement: a cold diagnostic + a coarse per-topic seed.
//!
//! Two read-only helpers (`placement_completed`, `build_placement_exam`) plus one
//! mutating helper (`apply_placement`) — the first place Manifold *writes*. All
//! writing flows through Anki's normal answer path (`grade_now`), tags and config,
//! so it is undo-safe and synced by Anki's own protocol.
//!
//! Seeds are graded Good on `is:new` cards, which produces `Learning`-kind revlog
//! entries: they set the card's FSRS memory state and lift its teaching level to
//! Independent (so known material is not re-taught) and feed the Memory score as a
//! labeled prior, but are NOT `Review`-kind, so the readiness give-up rule (200
//! independent reviews / 50% coverage) is left completely untouched.

use std::collections::HashMap;
use std::collections::HashSet;
use std::collections::VecDeque;

use anki_proto::manifold::SessionItem;

use crate::manifold::blueprint::graph;
use crate::manifold::mastery::tag_suffix;
use crate::prelude::*;

const TOPIC_TAG_PREFIX: &str = "mf::topic::";
const SKILL_TAG_PREFIX: &str = "mf::skill::";
const TIER_TAG_PREFIX: &str = "mf::tier::";
/// Tag marking a card whose state came from a placement seed, not real study, so
/// the prior is transparent and a future reset can find it.
const PLACEMENT_TAG: &str = "mf::placement";
/// Collection-config flag: onboarding completed or skipped.
const ONBOARDING_DONE_KEY: &str = "manifoldOnboardingDone";
/// Every probe is presented cold (Independent teaching level).
const PLACEMENT_LEVEL: u32 = 2;
/// Good rating for seeding (Anki: Again=1, Hard=2, Good=3, Easy=4).
const GOOD_RATING: i32 = 3;
/// Hard cap on probes in one diagnostic, so the exam stays short no matter how
/// many courses are reported.
pub(crate) const PLACEMENT_MAX_ITEMS: usize = 30;

/// Whether onboarding is done, or the collection already carries study history.
/// Cheap: a config read, then a single search for any studied skill card.
pub(crate) fn placement_completed(col: &mut Collection) -> Result<bool> {
    if col
        .get_config_optional::<bool, _>(ONBOARDING_DONE_KEY)
        .unwrap_or(false)
    {
        return Ok(true);
    }
    // A collection with any already-studied skill card predates onboarding.
    let studied = col.all_cards_for_search("tag:mf::skill::* -is:new")?;
    Ok(!studied.is_empty())
}

/// Selects a short, cold diagnostic: up to `per_topic` distinct skills from each
/// requested topic, weight-ordered and interleaved across topics, capped at
/// [`PLACEMENT_MAX_ITEMS`]. Read-only. Unknown topic ids fail loudly.
pub(crate) fn build_placement_exam(
    col: &mut Collection,
    topic_ids: &[String],
    per_topic: u32,
) -> Result<Vec<SessionItem>> {
    let g = graph();
    let per_topic = (per_topic.max(1)) as usize;

    let wanted: HashSet<&str> = if topic_ids.is_empty() {
        g.topics().iter().map(|t| t.id.as_str()).collect()
    } else {
        for id in topic_ids {
            if g.topic(id).is_none() {
                invalid_input!("placement exam requested unknown topic '{}'", id);
            }
        }
        topic_ids.iter().map(String::as_str).collect()
    };

    // One pass over skill cards, bucketing up to `per_topic` distinct skills per
    // wanted topic (card-id order within a topic, for stability).
    let mut by_topic: HashMap<&str, (f32, Vec<SessionItem>)> = HashMap::new();
    let mut seen_skill: HashSet<String> = HashSet::new();
    for card in col.all_cards_for_search("tag:mf::skill::*")? {
        let note = col
            .storage
            .get_note(card.note_id)?
            .or_not_found(card.note_id)?;
        let tags = &note.tags;
        let Some(topic_id) = tag_suffix(tags, TOPIC_TAG_PREFIX) else {
            continue;
        };
        if !wanted.contains(topic_id) {
            continue;
        }
        let Some(topic) = g.topic(topic_id) else {
            continue;
        };
        let Some(skill_id) = tag_suffix(tags, SKILL_TAG_PREFIX) else {
            continue;
        };
        if !seen_skill.insert(skill_id.to_string()) {
            continue; // one probe per skill
        }
        let entry = by_topic
            .entry(topic.id.as_str())
            .or_insert((topic.weight, Vec::new()));
        if entry.1.len() >= per_topic {
            continue;
        }
        let tier = tag_suffix(tags, TIER_TAG_PREFIX).unwrap_or_default().to_string();
        let skill_name = note.fields().first().map(|f| f.trim()).unwrap_or_default();
        entry.1.push(SessionItem {
            card_id: card.id.0,
            skill_id: skill_id.to_string(),
            skill_name: skill_name.to_string(),
            topic_id: topic_id.to_string(),
            topic_title: topic.title.clone(),
            tier,
            level: PLACEMENT_LEVEL,
        });
    }

    // Order topics by blueprint weight (desc, then id) and round-robin one probe
    // per topic per pass, so the exam interleaves areas rather than blocking.
    let mut topics: Vec<(&str, f32, Vec<SessionItem>)> = by_topic
        .into_iter()
        .map(|(id, (w, items))| (id, w, items))
        .collect();
    topics.sort_by(|a, b| {
        b.1.partial_cmp(&a.1)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then(a.0.cmp(b.0))
    });
    let mut queues: Vec<VecDeque<SessionItem>> =
        topics.into_iter().map(|(_, _, items)| items.into()).collect();

    let mut result = Vec::new();
    let mut progressed = true;
    while progressed && result.len() < PLACEMENT_MAX_ITEMS {
        progressed = false;
        for q in queues.iter_mut() {
            if let Some(item) = q.pop_front() {
                result.push(item);
                progressed = true;
                if result.len() >= PLACEMENT_MAX_ITEMS {
                    break;
                }
            }
        }
    }
    Ok(result)
}

/// Seeds the not-yet-attempted skill cards of each known topic to Independent and
/// marks onboarding done. Returns the number of cards seeded. Mutating.
pub(crate) fn apply_placement(
    col: &mut Collection,
    known_topic_ids: &[String],
) -> Result<u32> {
    let g = graph();
    for id in known_topic_ids {
        if g.topic(id).is_none() {
            invalid_input!("apply_placement got unknown topic '{}'", id);
        }
    }

    // `is:new` excludes any card already answered during the diagnostic, so a
    // real probe answer is never overwritten by a seed.
    let mut seed_cids: Vec<CardId> = Vec::new();
    let mut seed_nids: HashSet<NoteId> = HashSet::new();
    for topic_id in known_topic_ids {
        let search =
            format!("tag:{SKILL_TAG_PREFIX}* tag:{TOPIC_TAG_PREFIX}{topic_id} is:new");
        for card in col.all_cards_for_search(&search)? {
            seed_cids.push(card.id);
            seed_nids.insert(card.note_id);
        }
    }

    if !seed_cids.is_empty() {
        // Good on a New card: Learning-kind revlog + FSRS state -> Independent
        // teaching level (+ Memory prior), NOT Review-kind (readiness untouched).
        col.grade_now(&seed_cids, GOOD_RATING, 0)?;
        let nids: Vec<NoteId> = seed_nids.into_iter().collect();
        col.add_tags_to_notes(&nids, PLACEMENT_TAG)?;
    }

    col.set_config_json(ONBOARDING_DONE_KEY, &true)?;
    Ok(seed_cids.len() as u32)
}
```

- [ ] **Step 3: Register the module in `rslib/src/manifold/mod.rs`**

Add `placement` to the module list (keep alphabetical-ish with the others):

```rust
pub(crate) mod blueprint;
pub(crate) mod mastery;
pub(crate) mod placement;
mod service;
pub(crate) mod session;
#[cfg(test)]
mod test;
```

- [ ] **Step 4: Implement the RPCs in `rslib/src/manifold/service.rs`**

Add three methods inside `impl crate::services::ManifoldService for Collection`
(after `build_session_queue`):

```rust
    fn get_placement_state(
        &mut self,
    ) -> error::Result<anki_proto::manifold::PlacementStateResponse> {
        let completed = crate::manifold::placement::placement_completed(self)?;
        Ok(anki_proto::manifold::PlacementStateResponse { completed })
    }

    fn build_placement_exam(
        &mut self,
        input: anki_proto::manifold::PlacementExamRequest,
    ) -> error::Result<anki_proto::manifold::SessionQueueResponse> {
        let items = crate::manifold::placement::build_placement_exam(
            self,
            &input.topic_ids,
            input.per_topic,
        )?;
        Ok(anki_proto::manifold::SessionQueueResponse { items })
    }

    fn apply_placement(
        &mut self,
        input: anki_proto::manifold::ApplyPlacementRequest,
    ) -> error::Result<anki_proto::manifold::ApplyPlacementResponse> {
        let seeded_cards =
            crate::manifold::placement::apply_placement(self, &input.known_topic_ids)?;
        Ok(anki_proto::manifold::ApplyPlacementResponse { seeded_cards })
    }
```

- [ ] **Step 5: Expose the RPCs to the web in `qt/aqt/mediasrv.py`**

In `exposed_backend_list`, extend the `# ManifoldService` group (near
`get_topic_graph` / `build_session_queue`):

```python
# ManifoldService
"get_topic_graph",
"build_session_queue",
"get_study_today",
"get_placement_state",
"build_placement_exam",
"apply_placement",
```

(Keep any existing entries; only add the three new snake_case names.)

- [ ] **Step 6: Regenerate + build**

Run: `just check`
Expected: PASS — protobuf regenerates Rust trait methods, Python `manifold_pb2`,
and the TS `@generated/backend` (`getPlacementState`, `buildPlacementExam`,
`applyPlacement`); the whole workspace builds and existing checks stay green.

If codegen complains about an unimplemented trait method, confirm the three
methods in `service.rs` match the generated `ManifoldService` signatures exactly.

- [ ] **Step 7: Write the engine tests in `rslib/src/manifold/test.rs`**

Append these tests (they reuse the existing `add_skill_card` helper). They assert
selection, seeding, and the honesty invariant.

```rust
#[test]
fn placement_exam_probes_requested_topics_cold() {
    let mut col = Collection::new();
    add_skill_card(&mut col, "elementary_algebra", "ea_1", "relearn");
    add_skill_card(&mut col, "elementary_algebra", "ea_2", "relearn");
    add_skill_card(&mut col, "differential_calc", "dc_1", "relearn");

    let items = super::placement::build_placement_exam(
        &mut col,
        &["elementary_algebra".to_string()],
        1,
    )
    .unwrap();

    assert_eq!(items.len(), 1, "one probe per topic with per_topic=1");
    assert_eq!(items[0].topic_id, "elementary_algebra");
    assert_eq!(items[0].level, 2, "probes are presented cold (Independent)");
}

#[test]
fn placement_exam_unknown_topic_fails_loudly() {
    let mut col = Collection::new();
    let err = super::placement::build_placement_exam(&mut col, &["nope".to_string()], 1);
    assert!(err.is_err(), "an unknown topic id must fail, not be skipped");
}

#[test]
fn apply_placement_seeds_known_topic_without_moving_readiness() {
    let mut col = Collection::new();
    add_skill_card(&mut col, "elementary_algebra", "ea_1", "relearn");
    add_skill_card(&mut col, "elementary_algebra", "ea_2", "relearn");

    let seeded =
        super::placement::apply_placement(&mut col, &["elementary_algebra".to_string()])
            .unwrap();
    assert_eq!(seeded, 2, "both New skill cards get seeded");

    let nodes = compute_topic_graph(&mut col).unwrap();
    let ea = find(&nodes, "elementary_algebra");
    assert_eq!(ea.level_independent, 2, "seeded cards reach Independent");
    assert_eq!(ea.level_new, 0, "no card is left New");
    // The honesty invariant: seeds are Learning-kind, so they never count as
    // independent (Review-kind) evidence and never move the readiness gate.
    assert_eq!(ea.independent_reviews, 0, "seeds are not cold review evidence");
    assert!(ea.avg_recall > 0.0, "Memory reflects the seeded prior (labeled)");

    // Onboarding is now marked done.
    assert!(super::placement::placement_completed(&mut col).unwrap());
}

#[test]
fn apply_placement_leaves_already_attempted_cards_alone() {
    let mut col = Collection::new();
    let card = add_skill_card(&mut col, "elementary_algebra", "ea_1", "relearn");
    add_revlog(&mut col, &card, RevlogReviewKind::Learning, 3); // already attempted

    let seeded =
        super::placement::apply_placement(&mut col, &["elementary_algebra".to_string()])
            .unwrap();
    assert_eq!(seeded, 0, "an already-attempted card is not re-seeded (is:new only)");
}

#[test]
fn placement_state_false_on_fresh_true_after_study() {
    let mut col = Collection::new();
    assert!(!super::placement::placement_completed(&mut col).unwrap());
    let card = add_skill_card(&mut col, "elementary_algebra", "ea_1", "relearn");
    mark_due_review(&mut col, &card, 10.0, 1); // studied -> not is:new
    assert!(
        super::placement::placement_completed(&mut col).unwrap(),
        "a studied collection predates onboarding"
    );
}
```

- [ ] **Step 8: Run the engine tests**

Run: `just test-rust manifold`
Expected: PASS — all five new tests plus the existing manifold tests.

(If `just test-rust` takes no filter, run `just test-rust` and confirm the
`manifold::test::placement_*` tests pass.)

- [ ] **Step 9: Commit**

```bash
git add proto/anki/manifold.proto rslib/src/manifold/placement.rs \
  rslib/src/manifold/mod.rs rslib/src/manifold/service.rs \
  rslib/src/manifold/test.rs qt/aqt/mediasrv.py
git commit -m "feat(manifold): placement engine RPCs (exam + seed + state)"
```

---

## Task 2: Seed-deck auto-import endpoint

So onboarding on a truly fresh profile has skill cards to diagnose. Reuses the
existing importer; idempotent. If your build provisions the deck elsewhere this
becomes a no-op.

**Files:**

- Modify: `qt/aqt/mediasrv.py` (add `manifold_import_seed`, register in
  `post_handler_list`)

**Interfaces:**

- Produces: POST `/_anki/manifoldImportSeed` → `{"status":"ok","added":N,"skipped":M}`
  or `{"status":"error","detail":"..."}`.
- Consumes: `manifold/content/import_seed.py::import_seed(col)`.

- [ ] **Step 1: Add the handler in `qt/aqt/mediasrv.py`**

Add near the other `manifold_*` handlers (e.g. after `manifold_lecture`):

```python
def manifold_import_seed() -> bytes:
    """Import the GRE seed deck into the open collection (idempotent).

    Reuses manifold/content/import_seed.py so onboarding on a fresh profile has
    skill cards to diagnose. Fails loudly (surfaced as JSON) if the seed or
    blueprint files are missing; never fabricates content."""
    import importlib.util

    script = None
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "manifold" / "content" / "import_seed.py"
        if candidate.exists():
            script = candidate
            break
    if script is None:
        return json.dumps(
            {"status": "error", "detail": "import_seed.py not found"}
        ).encode("utf-8")

    spec = importlib.util.spec_from_file_location("manifold_import_seed_mod", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    added, skipped = module.import_seed(aqt.mw.col)
    return json.dumps(
        {
            "status": "ok",
            "added": sum(added.values()),
            "skipped": sum(skipped.values()),
        }
    ).encode("utf-8")
```

- [ ] **Step 2: Register it in `post_handler_list`**

```python
post_handler_list = [
    # ...existing...
    manifold_next_problem,
    manifold_lecture,
    manifold_hint,
    manifold_import_seed,
    manifold_google_sign_in,
]
```

- [ ] **Step 3: Verify the importer wiring**

Run:

```bash
just build && PYTHONPATH=out/pylib out/pyenv/bin/python - <<'PY'
import importlib.util, pathlib
p = pathlib.Path("manifold/content/import_seed.py")
spec = importlib.util.spec_from_file_location("m", p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from anki.collection import Collection
import tempfile, os
fd, path = tempfile.mkstemp(suffix=".anki2"); os.close(fd); os.unlink(path)
col = Collection(path)
added, skipped = m.import_seed(col)
print("added", sum(added.values()), "skipped", sum(skipped.values()))
col.close()
PY
```

Expected: prints `added 519 skipped 0` (the seed deck size), proving
`import_seed(col)` works against an open collection the way the endpoint calls it.

- [ ] **Step 4: Commit**

```bash
git add qt/aqt/mediasrv.py
git commit -m "feat(manifold): mediasrv endpoint to import the seed deck for onboarding"
```

---

## Task 3: Placement client library (`placement.ts`) + tests

Pure logic (course map, verdicts, prereq closure) and thin RPC wrappers.

**Files:**

- Create: `ts/lib/manifold/placement.ts`
- Create: `ts/lib/manifold/placement.test.ts`

**Interfaces:**

- Consumes (generated): `getPlacementState`, `buildPlacementExam`,
  `applyPlacement` from `@generated/backend`; `QueueItem` from `$lib/manifold/session`.
- Produces: `COURSES`, `topicsForCourses`, `verdictForTopic`, `knownTopicIds`,
  `fetchPlacementState`, `buildPlacementQueue`, `seedPlacement`, `importSeedDeck`,
  constants `KNOWN_ACCURACY`, `SHAKY_ACCURACY`, `DEFAULT_PER_TOPIC`.

- [ ] **Step 1: Write the failing tests `ts/lib/manifold/placement.test.ts`**

```ts
// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { describe, expect, it } from "vitest";

import {
    COURSES,
    knownTopicIds,
    topicsForCourses,
    verdictForTopic,
} from "./placement";

// All 33 blueprint topic ids (rslib/src/manifold/blueprint.json).
const ALL_TOPICS = [
    "elementary_algebra",
    "precalc_functions",
    "trigonometry",
    "coordinate_geometry",
    "limits_continuity",
    "differential_calc",
    "applications_derivatives",
    "integral_calc",
    "integration_techniques",
    "applications_integrals",
    "sequences_series",
    "multivariable_diff",
    "multivariable_int",
    "vector_calc",
    "differential_equations",
    "number_theory",
    "linear_algebra_core",
    "vector_spaces",
    "eigen",
    "group_theory",
    "rings_fields",
    "logic_sets",
    "combinatorics",
    "graph_theory",
    "algorithms",
    "probability",
    "statistics",
    "real_analysis_sequences",
    "real_analysis_topology",
    "metric_topology",
    "complex_analysis",
    "geometry",
    "numerical_analysis",
];

describe("course map", () => {
    it("covers every blueprint topic at least once", () => {
        const covered = new Set(COURSES.flatMap((c) => c.topicIds));
        for (const id of ALL_TOPICS) {
            expect(covered.has(id), `topic ${id} is uncovered`).toBe(true);
        }
    });

    it("maps only known topic ids", () => {
        const known = new Set(ALL_TOPICS);
        for (const c of COURSES) {
            for (const id of c.topicIds) {
                expect(known.has(id), `${c.id} maps unknown ${id}`).toBe(true);
            }
        }
    });

    it("dedupes topics across selected courses", () => {
        const calc1 = COURSES.find((c) => c.id === "calc_1")!;
        const topics = topicsForCourses([calc1.id, calc1.id]);
        expect(topics.length).toBe(new Set(topics).size);
    });
});

describe("verdicts", () => {
    it("known at >=50% probe accuracy", () => {
        expect(verdictForTopic({ answered: 2, correct: 1 }, false)).toBe(
            "known",
        );
    });
    it("shaky between 25% and 50%", () => {
        expect(verdictForTopic({ answered: 4, correct: 1 }, false)).toBe(
            "shaky",
        );
    });
    it("new below 25%", () => {
        expect(verdictForTopic({ answered: 4, correct: 0 }, false)).toBe("new");
    });
    it("self-reported but untested counts as known (labeled prior)", () => {
        expect(verdictForTopic(undefined, true)).toBe("known");
    });
    it("not reported and untested is new", () => {
        expect(verdictForTopic(undefined, false)).toBe("new");
    });
});

describe("known topic ids include the prereq closure", () => {
    it("adds a reported topic's transitive prerequisites", () => {
        // differential_calc <- limits_continuity <- {precalc_functions, trigonometry}
        const prereqs = new Map<string, string[]>([
            ["differential_calc", ["limits_continuity"]],
            ["limits_continuity", ["precalc_functions", "trigonometry"]],
            ["precalc_functions", ["elementary_algebra"]],
            ["trigonometry", ["precalc_functions"]],
            ["elementary_algebra", []],
        ]);
        const tallies = new Map([["differential_calc", {
            answered: 2,
            correct: 2,
        }]]);
        const known = knownTopicIds(["calc_1"], tallies, prereqs);
        // calc_1 maps to differential_calc (known) -> pull in its prereq chain.
        expect(known).toContain("differential_calc");
        expect(known).toContain("limits_continuity");
        expect(known).toContain("elementary_algebra");
    });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `just test-ts` (or `./ts/node_modules/.bin/vitest run ts/lib/manifold/placement.test.ts`)
Expected: FAIL — `placement.ts` does not exist yet.

- [ ] **Step 3: Implement `ts/lib/manifold/placement.ts`**

```ts
// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Onboarding placement client logic: the course -> topic map, the per-topic
 * verdict from probe results + self-report, the seed set (known topics plus the
 * transitive prerequisite closure of the reported courses), and thin wrappers
 * over the placement RPCs. Kept free of Svelte so it is unit-testable.
 */

import {
    applyPlacement,
    buildPlacementExam,
    getPlacementState,
} from "@generated/backend";

import type { QueueItem } from "$lib/manifold/session";

/** A course the learner may have taken, mapped to the blueprint topics it covers. */
export interface Course {
    id: string;
    label: string;
    topicIds: string[];
}

/** Covers all 33 blueprint topics (rslib/src/manifold/blueprint.json). The engine
 *  validates every id server-side, so a drifted id fails loudly rather than
 *  silently dropping a topic. */
export const COURSES: Course[] = [
    {
        id: "precalc",
        label: "Precalculus",
        topicIds: [
            "elementary_algebra",
            "precalc_functions",
            "trigonometry",
            "coordinate_geometry",
        ],
    },
    {
        id: "calc_1",
        label: "Calculus I (differential)",
        topicIds: [
            "limits_continuity",
            "differential_calc",
            "applications_derivatives",
        ],
    },
    {
        id: "calc_2",
        label: "Calculus II (integral & series)",
        topicIds: [
            "integral_calc",
            "integration_techniques",
            "applications_integrals",
            "sequences_series",
        ],
    },
    {
        id: "calc_3",
        label: "Calculus III (multivariable)",
        topicIds: ["multivariable_diff", "multivariable_int", "vector_calc"],
    },
    {
        id: "odes",
        label: "Differential equations",
        topicIds: ["differential_equations"],
    },
    {
        id: "linear_algebra",
        label: "Linear algebra",
        topicIds: ["linear_algebra_core", "vector_spaces", "eigen"],
    },
    {
        id: "abstract_algebra",
        label: "Abstract algebra",
        topicIds: ["group_theory", "rings_fields"],
    },
    {
        id: "number_theory",
        label: "Number theory",
        topicIds: ["number_theory"],
    },
    {
        id: "discrete",
        label: "Discrete math / combinatorics",
        topicIds: ["logic_sets", "combinatorics", "graph_theory", "algorithms"],
    },
    {
        id: "prob_stats",
        label: "Probability & statistics",
        topicIds: ["probability", "statistics"],
    },
    {
        id: "real_analysis",
        label: "Real analysis",
        topicIds: [
            "real_analysis_sequences",
            "real_analysis_topology",
            "metric_topology",
        ],
    },
    {
        id: "complex_analysis",
        label: "Complex analysis",
        topicIds: ["complex_analysis"],
    },
    { id: "geometry", label: "Geometry", topicIds: ["geometry"] },
    {
        id: "numerical",
        label: "Numerical analysis",
        topicIds: ["numerical_analysis"],
    },
];

/** Probe accuracy at/above which a tested topic counts as known. */
export const KNOWN_ACCURACY = 0.5;
/** Probe accuracy at/above which a tested topic counts as shaky (else new). */
export const SHAKY_ACCURACY = 0.25;
/** Default probes drawn per topic. */
export const DEFAULT_PER_TOPIC = 1;

const COURSE_BY_ID = new Map(COURSES.map((c) => [c.id, c]));

/** The deduped union of blueprint topics covered by the selected courses. */
export function topicsForCourses(courseIds: string[]): string[] {
    const out = new Set<string>();
    for (const id of courseIds) {
        const course = COURSE_BY_ID.get(id);
        if (course) {
            for (const t of course.topicIds) {
                out.add(t);
            }
        }
    }
    return [...out];
}

export interface ProbeTally {
    answered: number;
    correct: number;
}

export type Verdict = "known" | "shaky" | "new";

/**
 * Per-topic verdict. A tested topic is graded by probe accuracy; an untested
 * topic (all probes abstained or none drawn) falls back to self-report: reported
 * -> known (a labeled prior confirmed later by study), not reported -> new.
 */
export function verdictForTopic(
    tally: ProbeTally | undefined,
    reported: boolean,
): Verdict {
    if (!tally || tally.answered === 0) {
        return reported ? "known" : "new";
    }
    const accuracy = tally.correct / tally.answered;
    if (accuracy >= KNOWN_ACCURACY) {
        return "known";
    }
    if (accuracy >= SHAKY_ACCURACY) {
        return "shaky";
    }
    return "new";
}

/** Transitive prerequisite closure of a set of topic ids. */
function prereqClosure(
    topicIds: Iterable<string>,
    prereqsById: Map<string, string[]>,
): Set<string> {
    const out = new Set<string>();
    const stack = [...topicIds];
    while (stack.length) {
        const id = stack.pop()!;
        if (out.has(id)) {
            continue;
        }
        out.add(id);
        for (const p of prereqsById.get(id) ?? []) {
            if (!out.has(p)) {
                stack.push(p);
            }
        }
    }
    return out;
}

/**
 * The topics to seed: every topic whose verdict is `known`, plus the transitive
 * prerequisite closure of the reported courses' topics (knowing X implies its
 * prerequisites), so seeding leaves the DAG coherent and the reported topics
 * actually unlock. Shaky/new topics are left to normal teaching.
 */
export function knownTopicIds(
    reportedCourseIds: string[],
    tallies: Map<string, ProbeTally>,
    prereqsById: Map<string, string[]>,
): string[] {
    const reportedTopics = topicsForCourses(reportedCourseIds);
    const reportedSet = new Set(reportedTopics);
    const known = new Set<string>();
    for (const topicId of reportedTopics) {
        if (
            verdictForTopic(tallies.get(topicId), reportedSet.has(topicId))
                === "known"
        ) {
            known.add(topicId);
        }
    }
    // Any topic tested well even if not reported.
    for (const [topicId, tally] of tallies) {
        if (verdictForTopic(tally, reportedSet.has(topicId)) === "known") {
            known.add(topicId);
        }
    }
    return [...prereqClosure(known, prereqsById)];
}

// --- RPC wrappers -------------------------------------------------------------

const IMPORT_SEED_URL = "/_anki/manifoldImportSeed";

/** Whether onboarding is done (or the collection already has study history). */
export async function fetchPlacementState(): Promise<boolean> {
    const res = await getPlacementState({});
    return res.completed;
}

/** Build the cold diagnostic queue for the given topics, mapped to QueueItems. */
export async function buildPlacementQueue(
    topicIds: string[],
    perTopic = DEFAULT_PER_TOPIC,
): Promise<QueueItem[]> {
    const res = await buildPlacementExam({ topicIds, perTopic });
    return res.items.map((item) => ({
        cardId: item.cardId,
        skillId: item.skillId,
        skillName: item.skillName,
        topicId: item.topicId,
        topicTitle: item.topicTitle,
        tier: item.tier,
        level: item.level,
    }));
}

/** Seed the known topics and mark onboarding done; returns the seeded count. */
export async function seedPlacement(known: string[]): Promise<number> {
    const res = await applyPlacement({ knownTopicIds: known });
    return res.seededCards;
}

/** Import the GRE seed deck (idempotent). Throws loudly on failure. */
export async function importSeedDeck(): Promise<
    { added: number; skipped: number }
> {
    const res = await fetch(IMPORT_SEED_URL, {
        method: "POST",
        headers: { "Content-Type": "application/binary" },
        body: new TextEncoder().encode("{}"),
    });
    if (!res.ok) {
        throw new Error(`seed import failed: ${res.status}`);
    }
    const parsed = JSON.parse(await res.text()) as
        | { status: "ok"; added: number; skipped: number }
        | { status: "error"; detail: string };
    if (parsed.status !== "ok") {
        throw new Error(`seed import failed: ${parsed.detail}`);
    }
    return { added: parsed.added, skipped: parsed.skipped };
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-ts`
Expected: PASS — the `placement.test.ts` suite is green.

- [ ] **Step 5: Commit**

```bash
git add ts/lib/manifold/placement.ts ts/lib/manifold/placement.test.ts
git commit -m "feat(manifold): placement client logic (course map, verdicts, seed set)"
```

---

## Task 4: Onboarding route + home gate

The wizard UI, plus the home redirect and a "Retake placement" link.

**Files:**

- Create: `ts/routes/manifold-onboarding/+page.ts`
- Create: `ts/routes/manifold-onboarding/+page.svelte`
- Modify: `ts/routes/manifold/+page.ts` (gate)
- Modify: `ts/routes/manifold/+page.svelte` (Retake link)
- Modify: `qt/aqt/mediasrv.py` (`is_sveltekit_page`)

**Interfaces:**

- Consumes: `placement.ts` (all exports), `session.ts`
  (`SessionRunner`, `ServedProblem`, `Answer`, `isCorrect`, `grade`), `graph.ts`
  (`TopicNode`), `Button`, `MathText`, `mathmarkup` (`renderMath`, `mathToMarkup`).
- Produces: route `/manifold-onboarding`; home load returns
  `{ nodes, scoringConfig }` only when `completed`, else redirects.

- [ ] **Step 1: Register the route in `qt/aqt/mediasrv.py`**

In `is_sveltekit_page()`, add the route to the list:

```python
return page_name in [
    "graphs",
    "congrats",
    "manifold",
    "manifold-dashboard",
    "manifold-onboarding",
    "manifold-session",
    "card-info",
    "change-notetype",
```

- [ ] **Step 2: Create the loader `ts/routes/manifold-onboarding/+page.ts`**

```ts
// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getTopicGraph } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async () => {
    // Nodes give per-topic totals (is the deck imported?) and prereqs (for the
    // seed closure). No placement gate here — this page IS the onboarding.
    const graph = await getTopicGraph({});
    return { nodes: graph.nodes };
}) satisfies PageLoad;
```

- [ ] **Step 3: Create the wizard `ts/routes/manifold-onboarding/+page.svelte`**

```svelte
<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

The new-user onboarding wizard. Four phases: set up the deck (import if empty),
report courses taken, a short cold placement diagnostic, and a summary that seeds
the learner's starting point. It seeds real card state through the normal grade
path and never produces a readiness number (the home gate stays honest).
-->
<script lang="ts">
    import "@fontsource-variable/outfit/wght.css";
    import "@fontsource-variable/plus-jakarta-sans/wght.css";
    import "$lib/manifold/tokens.scss";

    import { getTopicGraph } from "@generated/backend";
    import { onMount } from "svelte";

    import { goto } from "$app/navigation";
    import Button from "$lib/manifold/Button.svelte";
    import type { TopicNode } from "$lib/manifold/graph";
    import { mathToMarkup, renderMath } from "$lib/manifold/mathmarkup";
    import MathText from "$lib/manifold/MathText.svelte";
    import {
        buildPlacementQueue,
        COURSES,
        importSeedDeck,
        knownTopicIds,
        type ProbeTally,
        seedPlacement,
        topicsForCourses,
        verdictForTopic,
    } from "$lib/manifold/placement";
    import {
        type Answer,
        grade,
        isCorrect,
        type ServedProblem,
        SessionRunner,
    } from "$lib/manifold/session";

    import type { PageData } from "./$types";

    export let data: PageData;

    type Phase = "setup" | "courses" | "exam" | "summary" | "applying";
    let phase: Phase = "setup";
    let nodes: TopicNode[] = data.nodes as TopicNode[];
    let setupError: string | null = null;

    const selected = new Set<string>();
    let selectedList: string[] = [];
    function toggleCourse(id: string): void {
        if (selected.has(id)) {
            selected.delete(id);
        } else {
            selected.add(id);
        }
        selectedList = [...selected];
    }

    let runner: SessionRunner | null = null;
    let served: ServedProblem | null = null;
    let examTotal = 0;
    let examDone = 0;
    const tallies = new Map<string, ProbeTally>();

    onMount(async () => {
        // Import the seed deck if this collection has no skill cards yet.
        if (!nodes.some((n) => n.total > 0)) {
            try {
                await importSeedDeck();
                nodes = (await getTopicGraph({})).nodes as TopicNode[];
            } catch (err) {
                setupError = err instanceof Error ? err.message : String(err);
                return;
            }
        }
        phase = "courses";
    });

    async function startExam(): Promise<void> {
        const topicIds = topicsForCourses(selectedList);
        if (topicIds.length === 0) {
            phase = "summary";
            return;
        }
        const queue = await buildPlacementQueue(topicIds);
        if (queue.length === 0) {
            phase = "summary";
            return;
        }
        runner = new SessionRunner(queue);
        examTotal = queue.length;
        phase = "exam";
        const res = await runner.pull();
        served = res.served;
        if (!served) {
            phase = "summary";
        }
    }

    async function answerProbe(answer: Answer): Promise<void> {
        if (!served || !runner) {
            return;
        }
        const item = served.item;
        const correct = isCorrect(served.problem, answer);
        const tally = tallies.get(item.topicId) ?? { answered: 0, correct: 0 };
        tally.answered += 1;
        if (correct) {
            tally.correct += 1;
        }
        tallies.set(item.topicId, tally);
        examDone += 1;
        await grade(item, correct); // real Learning-kind evidence for this skill
        const res = await runner.pull();
        served = res.served;
        if (!served) {
            phase = "summary";
        }
    }

    function endExamEarly(): void {
        runner?.dispose();
        phase = "summary";
    }

    // Summary rows: one per reported topic, with its verdict.
    $: reportedTopics = topicsForCourses(selectedList);
    $: byId = new Map(nodes.map((n) => [n.id, n]));
    $: summaryRows = reportedTopics.map((id) => ({
        id,
        title: byId.get(id)?.title ?? id,
        verdict: verdictForTopic(tallies.get(id), true),
    }));

    async function finish(): Promise<void> {
        phase = "applying";
        const prereqsById = new Map(nodes.map((n) => [n.id, n.prereqs]));
        const known = knownTopicIds(selectedList, tallies, prereqsById);
        await seedPlacement(known);
        await goto("/manifold");
    }

    async function skipAll(): Promise<void> {
        phase = "applying";
        await seedPlacement([]); // marks onboarding done with no seeds
        await goto("/manifold");
    }
</script>

<div class="manifold mf-page">
    <div class="mf-onb">
        <header class="mf-masthead">
            <h1 class="mf-wordmark">Manifold</h1>
        </header>

        {#if phase === "setup"}
            <section class="mf-card">
                {#if setupError}
                    <h2>Could not set up your deck</h2>
                    <p class="mf-err">{setupError}</p>
                {:else}
                    <h2>Setting up your deck…</h2>
                    <p>Loading the GRE Mathematics skill set.</p>
                {/if}
            </section>
        {:else if phase === "courses"}
            <section class="mf-card">
                <h2>Which of these have you taken?</h2>
                <p>Pick the courses you've completed. We'll test a few topics to place you, and skip re-teaching what you already know.</p>
                <ul class="mf-courses">
                    {#each COURSES as course (course.id)}
                        <li>
                            <label>
                                <input
                                    type="checkbox"
                                    checked={selected.has(course.id)}
                                    on:change={() => toggleCourse(course.id)}
                                />
                                {course.label}
                            </label>
                        </li>
                    {/each}
                </ul>
                <div class="mf-actions">
                    <Button ariaLabel="Start the placement" on:click={startExam}>
                        Start placement
                    </Button>
                    <button type="button" class="mf-link" on:click={skipAll}>Skip for now</button>
                </div>
            </section>
        {:else if phase === "exam" && served}
            <section class="mf-card">
                <div class="mf-progress" aria-label="progress">
                    {examDone} / {examTotal}
                </div>
                <p class="mf-topic">{served.problem.topic}</p>
                <div class="mf-stem"><MathText text={served.problem.stem} /></div>
                <ul class="mf-choices">
                    {#each served.problem.choices as choice (choice.id)}
                        <li>
                            <button type="button" on:click={() => answerProbe(choice.id)}>
                                <span class="mf-choice-id">{choice.id}</span>
                                <span>{@html mathToMarkup(choice.text)}</span>
                            </button>
                        </li>
                    {/each}
                </ul>
                <div class="mf-actions">
                    <button type="button" class="mf-link" on:click={() => answerProbe("dont-know")}>
                        Don't know
                    </button>
                    <button type="button" class="mf-link" on:click={endExamEarly}>
                        End placement
                    </button>
                </div>
            </section>
        {:else if phase === "summary"}
            <section class="mf-card">
                <h2>Your starting point</h2>
                {#if summaryRows.length}
                    <ul class="mf-summary">
                        {#each summaryRows as row (row.id)}
                            <li>
                                <MathText text={row.title} />
                                <span class="mf-verdict mf-verdict-{row.verdict}">{row.verdict}</span>
                            </li>
                        {/each}
                    </ul>
                    <p class="mf-note">
                        Topics marked <strong>known</strong> won't be re-taught. Your readiness
                        score stays in "mapping" until you've done enough cold reviews — placement
                        sets where you start, not a score.
                    </p>
                {:else}
                    <p>No courses selected. We'll start you at the foundations.</p>
                {/if}
                <div class="mf-actions">
                    <Button ariaLabel="Finish onboarding" on:click={finish}>
                        Go to Manifold
                    </Button>
                </div>
            </section>
        {:else if phase === "applying"}
            <section class="mf-card">
                <h2>Saving your placement…</h2>
            </section>
        {/if}
    </div>
</div>

<style lang="scss">
    .mf-page {
        min-height: 100vh;
        padding: var(--mf-space-7) var(--mf-space-6);
    }
    .mf-onb {
        max-width: 720px;
        margin-inline: auto;
    }
    .mf-wordmark {
        font-family: var(--mf-font-display);
        font-size: var(--mf-display);
        font-weight: 800;
        text-transform: uppercase;
        color: var(--mf-ink);
    }
    .mf-card {
        margin-top: var(--mf-space-6);
        padding: var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
        display: grid;
        gap: var(--mf-space-4);
    }
    .mf-courses,
    .mf-summary,
    .mf-choices {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: var(--mf-space-2);
    }
    .mf-choices button {
        display: flex;
        gap: var(--mf-space-3);
        width: 100%;
        text-align: left;
        padding: var(--mf-space-3);
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        cursor: pointer;
    }
    .mf-choices button:hover {
        background: var(--mf-hover);
    }
    .mf-choice-id {
        font-weight: 800;
    }
    .mf-actions {
        display: flex;
        gap: var(--mf-space-4);
        align-items: center;
        flex-wrap: wrap;
    }
    .mf-link {
        border: none;
        background: none;
        color: var(--mf-ink-muted);
        text-decoration: underline;
        cursor: pointer;
    }
    .mf-summary li {
        display: flex;
        justify-content: space-between;
        gap: var(--mf-space-3);
    }
    .mf-verdict {
        text-transform: uppercase;
        font-weight: 700;
        font-size: var(--mf-text-xs);
    }
    .mf-verdict-known {
        color: var(--mf-signal);
    }
    .mf-verdict-shaky {
        color: var(--mf-accent);
    }
    .mf-verdict-new {
        color: var(--mf-ink-muted);
    }
    .mf-err {
        color: var(--mf-accent);
    }
</style>
```

> Note: mirror the exact stem/choice rendering used by
> `ts/routes/manifold-session/+page.svelte` (it uses `renderMath` for the stem and
> `mathToMarkup` for choices). If `MathText` on the stem renders differently there,
> match that page so the diagnostic looks identical to a normal problem. `renderMath`
> is imported above for that adjustment.

- [ ] **Step 4: Add the home gate in `ts/routes/manifold/+page.ts`**

Replace the file body with the gated version:

```ts
// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getPlacementState, getTopicGraph } from "@generated/backend";
import { redirect } from "@sveltejs/kit";

import type { PageLoad } from "./$types";

export const load = (async () => {
    const [graph, placement] = await Promise.all([
        getTopicGraph({}),
        getPlacementState({}),
    ]);
    // A brand-new account is routed through onboarding before the dashboard.
    if (!placement.completed) {
        redirect(307, "/manifold-onboarding");
    }
    if (!graph.scoringConfig) {
        throw new Error("getTopicGraph returned no scoring config");
    }
    return { nodes: graph.nodes, scoringConfig: graph.scoringConfig };
}) satisfies PageLoad;
```

- [ ] **Step 5: Add a "Retake placement" link on the home (`ts/routes/manifold/+page.svelte`)**

Inside the `mf-today-body` div, after the "Start session" `Button`, add:

```svelte
<Button
    href="/manifold-onboarding"
    ariaLabel="Retake the placement"
>
    Retake placement
</Button>
```

- [ ] **Step 6: Build + typecheck**

Run: `just check`
Expected: PASS — svelte-check and tsc are clean; the new route builds into the
static SvelteKit output.

- [ ] **Step 7: Manual smoke (optional but recommended)**

Run: `just run`, then in the desktop shell confirm a fresh profile lands on the
onboarding wizard, the course checklist renders, a couple of probes serve and
grade, the summary shows verdicts, and "Go to Manifold" lands on the dashboard
without bouncing back. Take a screenshot of the wizard.

- [ ] **Step 8: Commit**

```bash
git add ts/routes/manifold-onboarding qt/aqt/mediasrv.py \
  ts/routes/manifold/+page.ts ts/routes/manifold/+page.svelte
git commit -m "feat(manifold): onboarding wizard route + home placement gate"
```

---

## Task 5: End-to-end test for the onboarding flow

**Files:**

- Create: `ts/tests/e2e/manifold-onboarding.test.ts`
- (Reference: run via `manifold/content/run_e2e_isolated.py`, which seeds a
  throwaway deck and drives the Playwright specs.)

**Interfaces:**

- Consumes: the running mediasrv + the `/manifold-onboarding` route from Task 4.

- [ ] **Step 1: Write the e2e spec `ts/tests/e2e/manifold-onboarding.test.ts`**

Mirror the structure of the existing `ts/tests/e2e/manifold.test.ts` (same harness,
`baseURL`, and helpers). The spec:

```ts
// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "@playwright/test";

// A freshly seeded collection has skill cards but no study history, so the home
// must redirect into onboarding.
test("fresh account is routed into onboarding and can complete it", async ({ page }) => {
    await page.goto("/manifold");
    await expect(page).toHaveURL(/manifold-onboarding/);

    // Report a course and start the placement.
    await expect(page.getByText("Which of these have you taken?"))
        .toBeVisible();
    await page.getByLabel("Calculus I (differential)").check();
    await page.getByRole("button", { name: "Start placement" }).click();

    // Answer probes until the summary appears (choices A–E or "Don't know").
    for (let i = 0; i < 30; i++) {
        const summary = page.getByText("Your starting point");
        if (await summary.isVisible().catch(() => false)) {
            break;
        }
        const dontKnow = page.getByRole("button", { name: "Don't know" });
        if (await dontKnow.isVisible().catch(() => false)) {
            await dontKnow.click();
        } else {
            break;
        }
    }

    await expect(page.getByText("Your starting point")).toBeVisible();
    await page.getByRole("button", { name: "Go to Manifold" }).click();

    // Back on the home, and it no longer bounces to onboarding.
    await expect(page).toHaveURL(/\/manifold(\/|$)/);
    await expect(page).not.toHaveURL(/onboarding/);
});
```

- [ ] **Step 2: Run the isolated e2e runner**

Run: `out/pyenv/bin/python manifold/content/run_e2e_isolated.py`
Expected: PASS — the new onboarding spec plus the existing specs. (Stock
`just test-e2e` does not seed the GRE deck, so use the isolated runner, which
does.)

- [ ] **Step 3: Commit**

```bash
git add ts/tests/e2e/manifold-onboarding.test.ts
git commit -m "test(manifold): e2e for the onboarding + placement flow"
```

---

## Task 6: Decision log, status, final gate

**Files:**

- Modify: `docs/manifold/alternatives.md` (append D46)
- Modify: `docs/manifold/status.md` (note the feature)

- [ ] **Step 1: Append decision D46 to `docs/manifold/alternatives.md`**

Add before the closing `<sub>` line (see the exact text in the spec / the
decision-log entry drafted alongside this plan). It records: the onboarding +
placement feature; the honesty-safe seeding (Learning-kind, readiness untouched);
`apply_placement` being the first mutating manifold RPC; the `mf::placement` tag +
`accept_labeled` Memory decision; and the class→topic map living in TS but
validated server-side.

- [ ] **Step 2: Note the feature in `docs/manifold/status.md`**

Add a short bullet under the current-state section pointing to
`spec-onboarding-placement.md` and this plan, and listing the new RPCs, route, and
`manifoldOnboardingDone` config flag.

- [ ] **Step 3: Final gate**

Run: `just check`
Expected: PASS — format + full build + all checks green.

- [ ] **Step 4: Commit**

```bash
git add docs/manifold/alternatives.md docs/manifold/status.md
git commit -m "docs(manifold): log D46 onboarding + placement, update status"
```

---

## Self-review

**Spec coverage:**

- Trigger/gate → Task 4 (home `+page.ts` + `get_placement_state`).
- Seed-deck setup → Task 2.
- Course self-report + map → Task 3 (`COURSES`, `topicsForCourses`), Task 4 (UI).
- Cold diagnostic → Task 1 (`build_placement_exam`), Task 4 (exam phase reusing
  `SessionRunner`).
- Seeding via real state + honesty invariant → Task 1 (`apply_placement` + tests).
- Memory-labeled prior / `mf::placement` tag → Task 1.
- Readiness untouched → Task 1 (test `apply_placement_seeds_known_topic_without_moving_readiness`).
- Prereq closure → Task 3 (`knownTopicIds`).
- Retake → Task 4 (home link, no gate on the onboarding route).
- Tests: Rust (Task 1), TS (Task 3), e2e (Task 5). Decision log (Task 6).

**Type consistency:** proto fields (`topic_ids`, `per_topic`, `known_topic_ids`,
`seeded_cards`, `completed`) map to TS camelCase (`topicIds`, `perTopic`,
`knownTopicIds`, `seededCards`, `completed`) — used consistently in `placement.ts`.
`build_placement_exam` returns `SessionQueueResponse` (reused), consumed by
`buildPlacementQueue` mapping to `QueueItem` (same shape as `buildQueue`).
`apply_placement`/`grade_now`/`add_tags_to_notes`/`set_config_json` signatures
match the existing rslib APIs.

**Placeholder scan:** none — every step carries real code or an exact command.
The one soft reference (matching the session page's math-render helper) points to
an exact existing file to copy, with the needed import already included.
