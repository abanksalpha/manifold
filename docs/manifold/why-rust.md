# Why the mastery-by-topic query belongs in Rust

> One-page note for assignment 7a. The primary Rust change is the mastery-by-topic
> rollup, which shipped as the `get_topic_graph` RPC (returning `TopicGraphResponse`
> / `TopicNode`); the PRD and spec-engine call the same query `mastery_by_topic`
> (PRD section 8.4, spec-engine section 5.1; renamed on implementation). This note
> argues why that rollup runs inside `rslib`, not in Python or TypeScript, and the
> claim is borne out by the latency benchmark in `manifold/bench/bench_mastery.py`.

## The load it carries

The Readiness dashboard reads from exactly one source, the `get_topic_graph` RPC
(the PRD's "the dashboard reads only from `mastery_by_topic`, one RPC", PRD section
8.9; same query, renamed). It sits behind two latency targets measured on the
shared 50,000-card reference deck: dashboard first load p95 < 1 s, and dashboard
refresh p95 < 500 ms, with no frame block over 100 ms (PRD section 7). The query is
a single pass over the skill-tagged cards that buckets each by topic through the
in-memory DAG and rolls up per node into `{mastered, total, avg_recall,
avg_stability, coverage}`, plus the topic's lock state and a placeholder-era
performance count (PRD section 8.4; spec-engine section 5.1). It is hot (every
dashboard open and refresh) and latency-bound. The benchmark confirms the budget:
in a representative run on a 50,000-card collection the RPC measured p50 ~0.33 s
and p95 ~0.36 s (`manifold/bench/bench_mastery.py`), inside both targets.
spec-engine section 3 names exactly this as the work that must not cross the
Python/TS boundary per request.

## What crossing the boundary would cost

The TS frontend reaches the engine over POST requests, and Python reaches it
through the `pylib` rsbridge binding (root `AGENTS.md`, "Protobuf and IPC"). If the
rollup ran on the TS or Python side, the engine would first have to hand per-card
FSRS memory state and elapsed time for up to 50,000 cards across that boundary,
then a managed-language loop would recompute retrievability per card before any
average could be formed. That duplicates logic that already lives in Rust, and a
Python/JS loop over 50k items will not hold p95 < 1 s. The design rule is explicit:
"nothing recomputes per-card in Python/TS" (PRD section 8.4; spec-engine section
5.1).

## What Rust already gives us, in process

The rollup reuses Anki's existing in-process FSRS retrievability, the open SQLite
collection, and an aggregation pattern Anki already uses:

- `rslib/src/stats/card.rs` computes FSRS retrievability in process as
  `FSRS::new(None).unwrap().current_retrievability_seconds(state, seconds, decay)`
  from the card's `memory_state`, elapsed seconds, and decay. `mastery_by_topic`
  calls the same function per card.
- `rslib/src/stats/graphs/retrievability.rs` is the direct precedent: it iterates
  `self.cards`, calls `current_retrievability_seconds` per card, and rolls up
  `sum_by_card`, `average`, and a per-note HashMap in one Rust pass. The mastery
  query is the same loop with a topic bucket instead of a note bucket.
- `rslib/src/storage/card/mod.rs` already exposes the iteration primitives the
  query uses: `compute_topic_graph` selects the skill-tagged cards with
  `Collection::all_cards_for_search("tag:mf::skill::*")` and reads each card's note
  and revlog through the open `SqliteStorage` that `rslib/src/collection/mod.rs`
  wraps. So the query runs against the already-open collection with no new table and
  no schema change (spec-engine section 7).

The DAG is only about 17 nodes, so bucketing is trivial and the pass is O(n) in
cards (spec-engine section 7). Keeping it in Rust holds 50,000 retrievability
computations off the IPC channel and off the UI thread.

## Why it has to be Rust for the grade, not just for speed

The assignment is explicit twice. The unbreakable rule: "Make a real change
inside Anki's Rust code, not just the Python screens" (ASSIGN section 2). The
grading line: "Rust change and how well it fits Anki, 20%", with the hard limit
"No real Rust change: 50% maximum" (ASSIGN section 11). A dashboard rollup
reimplemented in Python or TS would not be a Rust change at all, so it would fail
that requirement by definition regardless of speed. Putting the rollup in
`rslib/src/manifold/mastery.rs` (the `compute_topic_graph` function behind the
`get_topic_graph` RPC) is also what lets the change ship to both shells for free,
because desktop and AnkiDroid run the same `rslib` (PRD section 8.1). The query is
covered by four Rust unit tests in `rslib/src/manifold/test.rs` and a Python
integration test in `pylib/tests/test_manifold.py`, meeting D7's ">=3 Rust unit
tests + 1 Python test" bar.

## The interleave flag rides the same engine

A second, smaller engine change lives in Rust for the same reasons. The
study-feature ablation adds an `interleave` flag to `build_session_queue`: a new
`SessionQueueRequest` field in `proto/anki/manifold.proto`, threaded through
`service.rs` into `session.rs`, which orders the already-due queue either
interleaved across topics or blocked by topic while keeping the points-at-stake
and tier ordering intact. It belongs in `rslib` because it reads the same
in-process card and DAG data the rollup does, so no per-card data crosses the
Python or TypeScript boundary, and because a change in `rslib` ships to desktop
and AnkiDroid from one source (PRD section 8.1). Like the rollup it only reorders
what is already due and never changes FSRS state, so undo and sync stay intact.

## Touched upstream files (merge difficulty)

- New module `rslib/src/manifold/` (`mod.rs`, `mastery.rs`, `service.rs`,
  `blueprint.rs`, `test.rs`) plus a `pub mod manifold;` registration in
  `rslib/src/lib.rs`: additive, low merge friction.
- `proto/anki/manifold.proto` (new `ManifoldService`) and the generated
  `pylib/_backend.py` / TS `@generated/backend` surfaces: a new `.proto` needs a
  full `just check`, and future upstream proto changes could conflict, so this is
  the line most likely to need a merge fix.
- No changes to the scheduler, storage schema, or sync: the query is read-only
  aggregation over existing cards, which is what keeps undo and sync untouched
  (PRD section 8.3; spec-engine, "Storage choice").

See [`touched-files.md`](touched-files.md) for the full per-file merge-risk list.
