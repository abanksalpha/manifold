// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

use std::collections::HashSet;

use anki_proto::manifold::TopicNode;

use super::blueprint::graph;
use super::mastery::compute_topic_graph;
use super::session::build_session_queue;
use crate::card::CardQueue;
use crate::card::CardType;
use crate::card::FsrsMemoryState;
use crate::prelude::*;
use crate::revlog::RevlogEntry;
use crate::revlog::RevlogReviewKind;

/// Adds a Basic note tagged as a manifold skill and returns its (single) card.
fn add_skill_card(col: &mut Collection, topic: &str, skill: &str, tier: &str) -> Card {
    let nt = col.get_notetype_by_name("Basic").unwrap().unwrap();
    let mut note = nt.new_note();
    note.set_field(0, format!("{topic} / {skill}")).unwrap();
    note.tags = vec![
        format!("mf::topic::{topic}"),
        format!("mf::skill::{skill}"),
        format!("mf::tier::{tier}"),
    ];
    col.add_note(&mut note, DeckId(1)).unwrap();
    col.storage
        .all_cards_of_note(note.id)
        .unwrap()
        .pop()
        .unwrap()
}

/// Gives a card an FSRS memory state with a long stability and a "just now"
/// last review, so its retrievability is ~1.0 and it counts as mastered.
fn mark_mastered(col: &mut Collection, card: &Card) {
    let mut card = card.clone();
    card.memory_state = Some(FsrsMemoryState {
        stability: 1000.0,
        difficulty: 5.0,
    });
    card.last_review_time = Some(TimestampSecs::now());
    col.storage.update_card(&card).unwrap();
}

/// Turns a freshly-added skill card into a review card that is due today, with
/// the given FSRS `stability` (days) and a last review `days_ago` in the past,
/// so its retrievability is well-defined. Anki then reads it as `is:due` and
/// not `is:new`, exactly as a genuinely-studied card would be.
fn mark_due_review(col: &mut Collection, card: &Card, stability: f32, days_ago: i64) {
    let today = col.timing_today().unwrap().days_elapsed as i32;
    let mut card = card.clone();
    card.memory_state = Some(FsrsMemoryState {
        stability,
        difficulty: 5.0,
    });
    card.ctype = CardType::Review;
    card.queue = CardQueue::Review;
    card.interval = (stability as u32).max(1);
    // Due yesterday, so it is due now by Anki's own timing.
    card.due = today - 1;
    card.last_review_time = Some(TimestampSecs::now().adding_secs(-days_ago * 86_400));
    col.storage.update_card(&card).unwrap();
}

/// Forces a card's type/queue, for building level-count fixtures directly.
fn set_card_type(col: &mut Collection, card: &Card, ctype: CardType, queue: CardQueue) {
    let mut card = card.clone();
    card.ctype = ctype;
    card.queue = queue;
    col.storage.update_card(&card).unwrap();
}

/// Adds a single revlog attempt of the given kind + button to a card, so tests
/// can exercise the unsupported (Review-kind) performance filter directly.
fn add_revlog(col: &mut Collection, card: &Card, kind: RevlogReviewKind, button: u8) {
    let entry = RevlogEntry {
        id: RevlogId(0),
        cid: card.id,
        usn: Usn(-1),
        button_chosen: button,
        interval: 0,
        last_interval: 0,
        ease_factor: 0,
        taken_millis: 0,
        review_kind: kind,
    };
    // uniquify so repeated id(0) inserts each get a fresh id.
    col.storage.add_revlog_entry(&entry, true).unwrap();
}

fn topic_sequence(items: &[anki_proto::manifold::SessionItem]) -> Vec<&str> {
    items.iter().map(|i| i.topic_id.as_str()).collect()
}

fn find<'a>(nodes: &'a [TopicNode], id: &str) -> &'a TopicNode {
    nodes
        .iter()
        .find(|n| n.id == id)
        .unwrap_or_else(|| panic!("missing topic {id}"))
}

#[test]
fn empty_collection_locks_non_roots() {
    let mut col = Collection::new();
    let nodes = compute_topic_graph(&mut col).unwrap();

    assert_eq!(nodes.len(), graph().topics().len());
    for node in &nodes {
        assert_eq!(node.total, 0, "{} should have no skills", node.id);
        assert_eq!(node.mastered, 0);
        assert_eq!(node.avg_recall, 0.0);
        if node.prereqs.is_empty() {
            assert_eq!(
                node.lock_state, "unlocked",
                "root topic {} should be unlocked",
                node.id
            );
        } else {
            assert_eq!(
                node.lock_state, "locked",
                "non-root topic {} should be locked",
                node.id
            );
        }
    }
}

#[test]
fn partial_mastery_reports_in_progress() {
    let mut col = Collection::new();
    let mastered = add_skill_card(
        &mut col,
        "elementary_algebra",
        "linear_equations",
        "relearn",
    );
    add_skill_card(&mut col, "elementary_algebra", "quadratics", "relearn");
    add_skill_card(&mut col, "elementary_algebra", "inequalities", "relearn");
    mark_mastered(&mut col, &mastered);

    let nodes = compute_topic_graph(&mut col).unwrap();
    let ea = find(&nodes, "elementary_algebra");

    assert_eq!(ea.total, 3);
    assert_eq!(ea.mastered, 1);
    // The single studied card was reviewed "just now" with a long stability,
    // so its retrievability (the only one averaged) is ~1.0.
    assert!(
        (ea.avg_recall - 1.0).abs() < 0.01,
        "avg_recall = {}",
        ea.avg_recall
    );
    assert!(
        (ea.avg_stability - 1000.0).abs() < 1.0,
        "avg_stability = {}",
        ea.avg_stability
    );
    // 1/3 mastered is below the relearn target (0.9) but above zero, and a root
    // topic is always unlocked, so it is in progress.
    assert_eq!(ea.lock_state, "in_progress");
}

#[test]
fn studied_topic_is_in_progress_before_mastery() {
    let mut col = Collection::new();
    // A single studied skill with low stability (5d, below the 21d relearn bar):
    // not mastered, but studied — so the topic reads in_progress (green), never a
    // bare unlocked. Guards the regression where stability-based mastery left
    // actively-studied topics looking untouched.
    let card = add_skill_card(&mut col, "elementary_algebra", "s0", "relearn");
    mark_due_review(&mut col, &card, 5.0, 1);
    add_skill_card(&mut col, "elementary_algebra", "s1", "relearn");

    let nodes = compute_topic_graph(&mut col).unwrap();
    let ea = find(&nodes, "elementary_algebra");

    assert_eq!(ea.mastered, 0, "5d stability is below the 21d relearn bar");
    assert!(
        ea.avg_stability > 0.0,
        "the studied card gives the topic stability"
    );
    assert_eq!(
        ea.lock_state, "in_progress",
        "a studied-but-unmastered topic is in progress, not bare unlocked"
    );
}

#[test]
fn coverage_below_one_when_under_authored() {
    let mut col = Collection::new();
    // elementary_algebra expects 6 skills; author only 3.
    for skill in ["a", "b", "c"] {
        add_skill_card(&mut col, "elementary_algebra", skill, "relearn");
    }

    let nodes = compute_topic_graph(&mut col).unwrap();
    let ea = find(&nodes, "elementary_algebra");

    assert_eq!(ea.total, 3);
    assert!(
        (ea.coverage - 0.5).abs() < 1e-6,
        "coverage = {}",
        ea.coverage
    );
    assert!(ea.coverage < 1.0);
}

#[test]
fn non_root_unlocks_when_prereqs_competent() {
    let mut col = Collection::new();
    // precalc_functions unlocks once its sole prerequisite, elementary_algebra,
    // is *competent enough* — 80% of its skills answered correctly (the
    // mastery-learning criterion) — not merely seen and not durably mastered.
    let cards: Vec<Card> = ["s0", "s1", "s2", "s3", "s4"]
        .into_iter()
        .map(|s| add_skill_card(&mut col, "elementary_algebra", s, "relearn"))
        .collect();

    // 3 / 5 = 0.6 < 0.8 answered correctly -> precalc_functions stays locked.
    for card in &cards[..3] {
        add_revlog(&mut col, card, RevlogReviewKind::Review, 3);
    }
    let nodes = compute_topic_graph(&mut col).unwrap();
    assert_eq!(find(&nodes, "precalc_functions").lock_state, "locked");

    // 4 / 5 = 0.8 >= 0.8 answered correctly -> precalc_functions unlocks, even
    // though nothing is durably mastered (no stability accrued).
    add_revlog(&mut col, &cards[3], RevlogReviewKind::Review, 3);
    let nodes = compute_topic_graph(&mut col).unwrap();
    assert_eq!(find(&nodes, "elementary_algebra").mastered, 0);
    assert_eq!(find(&nodes, "precalc_functions").lock_state, "unlocked");
}

#[test]
fn recognize_tier_masters_at_lower_stability() {
    let mut col = Collection::new();
    // metric_topology is recognize-tier: it masters at a lower stability bar
    // (7d) than the relearn/teach core (21d). Give each skill ~10d stability.
    // (number_theory used to sit here, but D27 promoted it to teach.)
    let recognize: Vec<Card> = ["m0", "m1", "m2", "m3", "m4"]
        .into_iter()
        .map(|s| add_skill_card(&mut col, "metric_topology", s, "recognize"))
        .collect();
    for card in &recognize {
        mark_due_review(&mut col, card, 10.0, 5);
    }
    // A relearn skill at the same 10d stability stays unmastered (its bar is 21d).
    let relearn = add_skill_card(&mut col, "elementary_algebra", "ea0", "relearn");
    mark_due_review(&mut col, &relearn, 10.0, 5);

    let nodes = compute_topic_graph(&mut col).unwrap();

    let mt = find(&nodes, "metric_topology");
    assert!(
        (mt.avg_stability - 10.0).abs() < 0.01,
        "avg_stability = {}",
        mt.avg_stability
    );
    // 10d ≥ the 7d recognize bar → all 5 skills mastered → clears the 0.6 target.
    assert_eq!(mt.mastered, 5);
    assert_eq!(mt.lock_state, "mastered");

    // 10d < the 21d relearn bar → nothing mastered.
    let ea = find(&nodes, "elementary_algebra");
    assert_eq!(
        ea.mastered, 0,
        "10d stability is below the relearn 21d bar, so nothing is mastered"
    );
}

#[test]
fn session_serves_only_unlocked_roots_when_fresh() {
    let mut col = Collection::new();
    // The one root topic (no prerequisites) is unlocked and contributes.
    add_skill_card(&mut col, "elementary_algebra", "ea_a", "relearn");
    add_skill_card(&mut col, "elementary_algebra", "ea_b", "relearn");
    // Non-root topics are locked on a fresh collection and must contribute none.
    add_skill_card(&mut col, "precalc_functions", "pt_a", "relearn");
    add_skill_card(&mut col, "linear_algebra_core", "la_a", "teach");

    let items = build_session_queue(&mut col, true).unwrap();

    assert_eq!(
        items.len(),
        2,
        "only the unlocked root's new cards are served"
    );
    assert!(
        items.iter().all(|i| i.topic_id == "elementary_algebra"),
        "locked topics leaked into the queue: {:?}",
        topic_sequence(&items)
    );
    // Identity is carried through for the player to render.
    assert!(items
        .iter()
        .all(|i| !i.skill_id.is_empty() && !i.skill_name.is_empty()));
}

#[test]
fn session_unlocks_dependents_after_prereq_competent() {
    let mut col = Collection::new();
    let ea: Vec<Card> = ["s0", "s1", "s2", "s3", "s4"]
        .into_iter()
        .map(|s| add_skill_card(&mut col, "elementary_algebra", s, "relearn"))
        .collect();
    add_skill_card(&mut col, "precalc_functions", "pt_a", "relearn");
    add_skill_card(&mut col, "precalc_functions", "pt_b", "relearn");

    // 3 / 5 answered correctly (0.6 < 0.8): precalc stays locked, serves no new.
    for card in &ea[..3] {
        add_revlog(&mut col, card, RevlogReviewKind::Review, 3);
    }
    let before = build_session_queue(&mut col, true).unwrap();
    assert!(
        !topic_sequence(&before).contains(&"precalc_functions"),
        "a locked dependent must not contribute: {:?}",
        topic_sequence(&before)
    );

    // 4 / 5 answered correctly (0.8): precalc_functions unlocks and contributes.
    add_revlog(&mut col, &ea[3], RevlogReviewKind::Review, 3);
    let after = build_session_queue(&mut col, true).unwrap();
    assert!(
        topic_sequence(&after).contains(&"precalc_functions"),
        "an unlocked dependent should contribute: {:?}",
        topic_sequence(&after)
    );
}

#[test]
fn due_cards_order_by_points_at_stake() {
    let mut col = Collection::new();
    // Highest weight (5) but freshly reviewed: R ~ 1, weakness ~ 0, points ~ 0.
    let strong = add_skill_card(&mut col, "integral_calc", "svi", "relearn");
    mark_due_review(&mut col, &strong, 1000.0, 0);
    // Low weight (3) but long overdue: weakness ~ 1, points ~ 3.
    let weak_low = add_skill_card(&mut col, "elementary_algebra", "ea", "relearn");
    mark_due_review(&mut col, &weak_low, 1.0, 100);
    // Middle weight (4) and long overdue: weakness ~ 1, points ~ 4.
    let weak_high = add_skill_card(&mut col, "precalc_functions", "pt", "relearn");
    mark_due_review(&mut col, &weak_high, 1.0, 100);

    let items = build_session_queue(&mut col, true).unwrap();

    // Every due card is served regardless of lock, ordered by weight × (1 − R).
    assert_eq!(
        topic_sequence(&items),
        ["precalc_functions", "elementary_algebra", "integral_calc"]
    );
}

#[test]
fn new_card_budget_is_respected() {
    let mut col = Collection::new();
    let budget = graph().thresholds().new_per_day as usize;
    for i in 0..budget + 4 {
        add_skill_card(&mut col, "elementary_algebra", &format!("ea{i}"), "relearn");
    }

    let items = build_session_queue(&mut col, true).unwrap();

    assert_eq!(items.len(), budget, "the daily new budget caps the queue");
    assert!(items.iter().all(|i| i.topic_id == "elementary_algebra"));
}

#[test]
fn performance_counts_only_unsupported_reviews() {
    let mut col = Collection::new();
    let card = add_skill_card(&mut col, "elementary_algebra", "s", "relearn");
    // Two unsupported (Review-kind) attempts: one good (3), one miss (1) => 0.5.
    add_revlog(&mut col, &card, RevlogReviewKind::Review, 3);
    add_revlog(&mut col, &card, RevlogReviewKind::Review, 1);
    // Supported attempts must not count toward performance or the evidence.
    add_revlog(&mut col, &card, RevlogReviewKind::Learning, 3);
    add_revlog(&mut col, &card, RevlogReviewKind::Relearning, 1);

    let nodes = compute_topic_graph(&mut col).unwrap();
    let ea = find(&nodes, "elementary_algebra");

    assert_eq!(
        ea.independent_reviews, 2,
        "only Review-kind counts as evidence"
    );
    assert_eq!(ea.graded_reviews, 4, "all graded attempts still tallied");
    assert!(
        (ea.performance - 0.5).abs() < 1e-6,
        "performance should be Review-kind only: {}",
        ea.performance
    );
}

#[test]
fn level_counts_reflect_competence() {
    let mut col = Collection::new();
    // New: never attempted (no revlog).
    add_skill_card(&mut col, "elementary_algebra", "s_new", "relearn");
    // Guided: attempted but not yet answered correctly (0 successes) — still
    // needs support.
    let guided = add_skill_card(&mut col, "elementary_algebra", "s_guided", "relearn");
    add_revlog(&mut col, &guided, RevlogReviewKind::Learning, 1);
    // Independent: one correct retrieval is enough (independent_successes = 1),
    // reachable the same day via a learning-step rep — no graduation required.
    let independent = add_skill_card(&mut col, "elementary_algebra", "s_indep", "relearn");
    add_revlog(&mut col, &independent, RevlogReviewKind::Learning, 3);
    // Revisited: currently relearning after a lapse.
    let revisited = add_skill_card(&mut col, "elementary_algebra", "s_revis", "relearn");
    add_revlog(&mut col, &revisited, RevlogReviewKind::Review, 1);
    set_card_type(&mut col, &revisited, CardType::Relearn, CardQueue::Learn);

    let nodes = compute_topic_graph(&mut col).unwrap();
    let ea = find(&nodes, "elementary_algebra");

    assert_eq!(ea.total, 4);
    assert_eq!(ea.level_new, 1);
    assert_eq!(ea.level_guided, 1);
    assert_eq!(ea.level_independent, 1);
    assert_eq!(ea.level_revisited, 1);
}

#[test]
fn session_items_carry_teaching_level() {
    let mut col = Collection::new();
    let review = add_skill_card(&mut col, "elementary_algebra", "due1", "relearn");
    mark_due_review(&mut col, &review, 1.0, 100);
    // Two successful retrievals make it Independent (competence, not graduation).
    add_revlog(&mut col, &review, RevlogReviewKind::Review, 3);
    add_revlog(&mut col, &review, RevlogReviewKind::Review, 3);
    add_skill_card(&mut col, "elementary_algebra", "new1", "relearn"); // New -> 0

    let items = build_session_queue(&mut col, true).unwrap();

    let due = items.iter().find(|i| i.skill_id == "due1").unwrap();
    assert_eq!(
        due.level, 2,
        "two successful retrievals make a card Independent"
    );
    let fresh = items.iter().find(|i| i.skill_id == "new1").unwrap();
    assert_eq!(fresh.level, 0, "a never-studied card is New");
}

#[test]
fn session_orders_by_tier_circles_then_squares_then_diamonds() {
    let mut col = Collection::new();
    // Give the later tiers *higher* points-at-stake than relearn, to prove tier
    // order trumps points: circles (relearn) still come before squares (teach)
    // before diamonds (recognize). All are due, so lock state is irrelevant.
    let relearn = add_skill_card(&mut col, "elementary_algebra", "ea", "relearn");
    mark_due_review(&mut col, &relearn, 1000.0, 0); // R ~ 1 -> near-zero points
    let teach = add_skill_card(&mut col, "linear_algebra_core", "la", "teach");
    mark_due_review(&mut col, &teach, 1.0, 100); // weak -> high points
    let recognize = add_skill_card(&mut col, "metric_topology", "mt", "recognize");
    mark_due_review(&mut col, &recognize, 1.0, 100); // weak -> high points

    let items = build_session_queue(&mut col, true).unwrap();

    assert_eq!(
        topic_sequence(&items),
        [
            "elementary_algebra",
            "linear_algebra_core",
            "metric_topology"
        ],
        "tier order (relearn -> teach -> recognize) outranks points-at-stake"
    );
}

#[test]
fn interleaving_spreads_consecutive_topics() {
    let mut col = Collection::new();
    // Interleaving ON (the WS5 default). Two overdue cards in one topic (high
    // points) and one freshly-reviewed card in another (near-zero points). A
    // pure points order would place the two same-topic cards back to back;
    // interleaving must separate them. Both topics are relearn, so tier ordering
    // does not reorder across them. The blocked (OFF) arm is the next test.
    let a_hi = add_skill_card(&mut col, "elementary_algebra", "a_hi", "relearn");
    mark_due_review(&mut col, &a_hi, 10.0, 40);
    let a_lo = add_skill_card(&mut col, "elementary_algebra", "a_lo", "relearn");
    mark_due_review(&mut col, &a_lo, 10.0, 20);
    let other = add_skill_card(&mut col, "precalc_functions", "pf", "relearn");
    mark_due_review(&mut col, &other, 1000.0, 0);

    let items = build_session_queue(&mut col, true).unwrap();

    let topics = topic_sequence(&items);
    assert_eq!(topics.len(), 3);
    assert_eq!(
        topics,
        [
            "elementary_algebra",
            "precalc_functions",
            "elementary_algebra"
        ],
        "consecutive items should come from different topics where possible"
    );
    // Sanity: the set of distinct topics is exactly the two authored.
    let distinct: HashSet<&str> = topics.iter().copied().collect();
    assert_eq!(distinct.len(), 2);
}

#[test]
fn interleave_off_serves_blocked_by_topic() {
    let mut col = Collection::new();
    // Same fixture as the interleaving test, but with the toggle OFF. Blocked
    // practice must serve one topic's cards back-to-back (a topic drained before
    // the next), the exact opposite of the spread above — while still ordering
    // topics and within-topic items by points-at-stake.
    let a_hi = add_skill_card(&mut col, "elementary_algebra", "a_hi", "relearn");
    mark_due_review(&mut col, &a_hi, 10.0, 40);
    let a_lo = add_skill_card(&mut col, "elementary_algebra", "a_lo", "relearn");
    mark_due_review(&mut col, &a_lo, 10.0, 20);
    let other = add_skill_card(&mut col, "precalc_functions", "pf", "relearn");
    mark_due_review(&mut col, &other, 1000.0, 0);

    let items = build_session_queue(&mut col, false).unwrap();

    let topics = topic_sequence(&items);
    assert_eq!(topics.len(), 3);
    assert_eq!(
        topics,
        [
            "elementary_algebra",
            "elementary_algebra",
            "precalc_functions"
        ],
        "with interleaving off, a topic is exhausted before the next (blocked)"
    );
    // The higher-points elementary_algebra topic (weakest cards) still leads,
    // and its two cards are contiguous rather than split by the other topic.
    let distinct: HashSet<&str> = topics.iter().copied().collect();
    assert_eq!(distinct.len(), 2);
}

#[test]
fn read_only_rpcs_add_no_undo_entry() {
    let mut col = Collection::new();
    // A studied collection, so both RPCs have real work: a due review card
    // (performance evidence) plus an unlocked new skill under a root topic.
    let review = add_skill_card(&mut col, "elementary_algebra", "s_review", "relearn");
    mark_due_review(&mut col, &review, 5.0, 3);
    add_revlog(&mut col, &review, RevlogReviewKind::Review, 3);
    add_skill_card(&mut col, "elementary_algebra", "s_new", "relearn");

    // Baseline after set-up. Adding the notes above is itself undoable, so the
    // stack is non-empty by design; the point of this test is that the *RPCs*
    // add nothing to it and mutate no row.
    let can_undo_before = col.can_undo().cloned();
    let last_step_before = col.undo_status().last_step;
    let cards_before = col.storage.get_all_cards();

    // The two Manifold RPCs, exactly as service.rs invokes them, in both queue
    // modes. Each returns real data, proving it genuinely read the collection.
    let nodes = compute_topic_graph(&mut col).unwrap();
    assert!(
        nodes.iter().any(|n| n.total > 0),
        "the topic graph should reflect the studied skills"
    );
    let interleaved = build_session_queue(&mut col, true).unwrap();
    let blocked = build_session_queue(&mut col, false).unwrap();
    assert!(!interleaved.is_empty() && !blocked.is_empty());

    // Read-only: no undo entry was pushed, the counter did not advance, and
    // every card row is unchanged.
    assert_eq!(
        col.can_undo().cloned(),
        can_undo_before,
        "a read-only RPC must not push an undoable op"
    );
    assert_eq!(
        col.undo_status().last_step,
        last_step_before,
        "the undo counter must not advance on a pure read"
    );
    assert_eq!(
        col.storage.get_all_cards(),
        cards_before,
        "no card may change when only reading the topic graph or queue"
    );
}

#[test]
fn graded_review_still_undoes_correctly() {
    let mut col = Collection::new();
    let card = add_skill_card(&mut col, "elementary_algebra", "graded", "relearn");
    let before = col.storage.get_card(card.id).unwrap().unwrap();
    // Adding the note is the only op on the stack so far.
    assert_eq!(col.can_undo(), Some(&Op::AddNote));

    // A normal graded review — the exact path the session player takes
    // (`gradeNow` -> `grade_now`), rating the card Good (2).
    col.grade_now(&[card.id], 2).unwrap();

    // Grading is a real, undoable mutation: it records a GradeNow op on top of
    // the stack and moves the card off its New state.
    assert_eq!(col.can_undo(), Some(&Op::GradeNow));
    let after = col.storage.get_card(card.id).unwrap().unwrap();
    assert_ne!(after, before, "grading must change the card");

    // Undo pops exactly that op, restores the card byte-for-byte, and leaves the
    // earlier history intact — Manifold's grading rides Anki's normal undo.
    col.undo().unwrap();
    let restored = col.storage.get_card(card.id).unwrap().unwrap();
    assert_eq!(restored, before, "undo must restore the pre-review card");
    assert_eq!(
        col.can_undo(),
        Some(&Op::AddNote),
        "undo must consume only the GradeNow op, keeping prior history"
    );
}
