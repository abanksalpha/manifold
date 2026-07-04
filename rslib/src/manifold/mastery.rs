// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

//! Per-topic mastery rollup.
//!
//! Walks the cards carrying an `mf::skill::` tag once, buckets each by its
//! note's `mf::topic::` tag, and rolls the per-card FSRS state up the blueprint
//! DAG into a [`TopicNode`] per blueprint topic. FSRS retrievability `R` is
//! read from the existing card memory state exactly as `stats/card.rs` does —
//! no FSRS parameter or interval is ever modified.
//!
//! Definitions (per blueprint topic):
//! - `total`: distinct authored skills present (skills with ≥1 card).
//! - `mastered`: skills whose mean card FSRS **stability** (days) ≥ the topic's
//!   tier stability bar (`tier_stability` — relearn/teach demand mature-level
//!   durability, recognize a lower bar). Stability, not momentary recall `R`,
//!   so mastery reflects durable learning (storage strength) and is never
//!   tripped by a single just-answered card (D25).
//! - `avg_recall` / `avg_stability`: mean `R` / stability over the topic's
//!   cards that have an FSRS memory state (both are undefined for never-studied
//!   cards, so such cards are excluded; `0.0` when none are studied).
//! - `coverage`: distinct authored skills / `expected_skills`, capped at `1.0`.
//! - `performance`: fraction of the topic's *unsupported* reviews (revlog
//!   `Review`-kind, button ≥ 1) answered with rating ≥ 2; `0.0` if there are
//!   none. Learning/Relearning attempts (support present) are excluded so the
//!   score measures cold performance, not scaffolded practice (D21).
//! - `graded_reviews`: count of all graded revlog reviews (button ≥ 1, any
//!   kind).
//! - `independent_reviews`: count of unsupported (`Review`-kind) reviews: the
//!   evidence the readiness give-up rule counts (D20).
//! - `level_*`: card counts by teaching level, competence-driven (see
//!   [`teaching_level`]): New / Guided / Independent / Revisited.
//! - `lock_state`: see [`lock_state`].

use std::collections::HashMap;

use fsrs::FSRS;
use fsrs::FSRS5_DEFAULT_DECAY;

use crate::card::CardType;
use crate::manifold::blueprint::graph;
use crate::manifold::blueprint::BlueprintGraph;
use crate::manifold::blueprint::Topic;
use crate::prelude::*;
use crate::revlog::RevlogEntry;
use crate::revlog::RevlogReviewKind;
use crate::scheduler::timing::SchedTimingToday;

const TOPIC_TAG_PREFIX: &str = "mf::topic::";
const SKILL_TAG_PREFIX: &str = "mf::skill::";
/// Anki search selecting every card whose note carries any skill tag.
const SKILL_TAG_SEARCH: &str = "tag:mf::skill::*";

/// Per-topic accumulator built during the single pass over manifold cards.
#[derive(Default)]
struct TopicAgg {
    /// skill id → FSRS stability (days) of that skill's cards that have a
    /// memory state. Present (possibly empty) for every authored skill in
    /// the topic, so its length is the topic's `total`, and its per-skill
    /// mean drives `mastered` (D25).
    skill_stabilities: HashMap<String, Vec<f32>>,
    /// Sum and count of per-card `R` over cards with a memory state.
    recall_sum: f32,
    recall_count: u32,
    /// Sum and count of FSRS stability over cards with a memory state.
    stability_sum: f32,
    stability_count: u32,
    /// All graded revlog reviews (button ≥ 1), any kind.
    graded_reviews: u32,
    /// Unsupported (`Review`-kind) reviews, and those answered with rating ≥ 2.
    /// Performance is `independent_good / independent_reviews` (D21).
    independent_reviews: u32,
    independent_good: u32,
    /// Card counts by teaching level (from `CardType`).
    level_new: u32,
    level_guided: u32,
    level_independent: u32,
    level_revisited: u32,
}

/// The numbers rolled up for a single topic.
struct Rollup {
    mastered: u32,
    total: u32,
    avg_recall: f32,
    avg_stability: f32,
    coverage: f32,
    performance: f32,
    graded_reviews: u32,
    independent_reviews: u32,
    level_new: u32,
    level_guided: u32,
    level_independent: u32,
    level_revisited: u32,
    mastered_fraction: f32,
    competent_fraction: f32,
}

/// Computes the per-topic mastery rollup, returning one [`TopicNode`] per
/// blueprint topic in blueprint order.
pub(crate) fn compute_topic_graph(
    col: &mut Collection,
) -> Result<Vec<anki_proto::manifold::TopicNode>> {
    let graph = graph();
    let aggs = gather_topic_aggs(col)?;

    // Resolve each topic's tier bars once — the stability *depth* (days) a skill
    // must reach to count as mastered, and the mastered-fraction *breadth* the
    // topic must reach to count as mastered — failing loudly on an unknown tier.
    let mut tier_bars: HashMap<&str, (f32, f32)> = HashMap::with_capacity(graph.topics().len());
    for topic in graph.topics() {
        let (Some(stability_bar), Some(target)) = (
            graph.tier_stability().for_tier(&topic.tier),
            graph.tier_targets().for_tier(&topic.tier),
        ) else {
            invalid_input!(
                "manifold topic '{}' has unknown tier '{}'",
                topic.id,
                topic.tier
            );
        };
        tier_bars.insert(topic.id.as_str(), (stability_bar, target));
    }

    // First rollup pass: numbers (incl. mastered_fraction) for every topic. Each
    // topic counts a skill as mastered at its tier's stability bar.
    let mut rollups: HashMap<&str, Rollup> = HashMap::with_capacity(graph.topics().len());
    for topic in graph.topics() {
        let (stability_bar, _) = tier_bars[topic.id.as_str()];
        rollups.insert(
            topic.id.as_str(),
            rollup_topic(topic, aggs.get(topic.id.as_str()), stability_bar),
        );
    }

    // Mastery pass: a topic is mastered once its own mastered fraction reaches
    // its tier target, so lock state can gate a topic on whether its
    // prerequisites are themselves mastered.
    let mut mastered: HashMap<&str, bool> = HashMap::with_capacity(graph.topics().len());
    for topic in graph.topics() {
        let (_, target) = tier_bars[topic.id.as_str()];
        mastered.insert(
            topic.id.as_str(),
            rollups[topic.id.as_str()].mastered_fraction >= target,
        );
    }

    // Unlock gate: a topic's dependents open once it is *competent enough* — a
    // fraction of its skills answered correctly (the mastery-learning criterion),
    // not merely seen and not durably mastered (D28).
    let unlock_bar = graph.thresholds().unlock_competent_fraction;
    let mut competent_enough: HashMap<&str, bool> = HashMap::with_capacity(graph.topics().len());
    for topic in graph.topics() {
        competent_enough.insert(
            topic.id.as_str(),
            rollups[topic.id.as_str()].competent_fraction >= unlock_bar,
        );
    }

    // Assembly pass: derive each topic's lock state from its own mastery and
    // whether its prerequisites are competent enough, then build the response
    // nodes.
    let mut nodes = Vec::with_capacity(graph.topics().len());
    for topic in graph.topics() {
        let lock = lock_state(graph, topic, &rollups, &mastered, &competent_enough);
        let roll = &rollups[topic.id.as_str()];
        nodes.push(anki_proto::manifold::TopicNode {
            id: topic.id.clone(),
            title: topic.title.clone(),
            area: topic.area.clone(),
            tier: topic.tier.clone(),
            weight: topic.weight,
            prereqs: topic.prereqs.clone(),
            lock_state: lock.to_string(),
            mastered: roll.mastered,
            total: roll.total,
            avg_recall: roll.avg_recall,
            avg_stability: roll.avg_stability,
            coverage: roll.coverage,
            performance: roll.performance,
            graded_reviews: roll.graded_reviews,
            independent_reviews: roll.independent_reviews,
            level_new: roll.level_new,
            level_guided: roll.level_guided,
            level_independent: roll.level_independent,
            level_revisited: roll.level_revisited,
        });
    }

    Ok(nodes)
}

/// Per-topic lock state keyed by topic id, derived from the same rollup that
/// powers the dashboard. The session builder gates new cards on this so the
/// gating and the dashboard can never disagree about what is unlocked.
pub(super) fn topic_lock_states(col: &mut Collection) -> Result<HashMap<String, String>> {
    Ok(compute_topic_graph(col)?
        .into_iter()
        .map(|node| (node.id, node.lock_state))
        .collect())
}

/// The timing snapshot Manifold uses for FSRS retrievability, mirroring
/// `stats/card.rs`.
pub(super) fn current_timing(col: &mut Collection) -> Result<SchedTimingToday> {
    let today = col.timing_today()?;
    Ok(SchedTimingToday {
        days_elapsed: today.days_elapsed,
        now: TimestampSecs::now(),
        next_day_at: today.next_day_at,
    })
}

/// FSRS retrievability `R` for a studied card, computed exactly as
/// `stats/card.rs` does (no parameter or interval is ever modified). `None`
/// for never-studied cards, which have no memory state.
pub(super) fn current_recall(fsrs: &FSRS, card: &Card, timing: &SchedTimingToday) -> Option<f32> {
    card.memory_state.map(|state| {
        let elapsed = card.seconds_since_last_review(timing).unwrap_or_default();
        fsrs.current_retrievability_seconds(
            state.into(),
            elapsed,
            card.decay.unwrap_or(FSRS5_DEFAULT_DECAY),
        )
    })
}

/// A card's teaching (scaffolding) level, competence-driven and deliberately
/// decoupled from Anki's learning-steps calendar so a solo *Independent*
/// problem is reachable the same day a skill is learned:
/// - `0` **New** — never attempted (no revlog).
/// - `3` **Revisited** — currently relearning after a lapse (`Relearn`); the
///   one place Anki's card type is the right signal.
/// - `2` **Independent** — at least `independent_successes` correct retrievals
///   (button ≥ Good), so scaffolding fades once competence is shown. Reachable
///   day-one via learning-step reps.
/// - `1` **Guided** — attempted but not yet at the independence bar.
///
/// This is the *teaching* axis only. Performance/readiness evidence is separate
/// and still counts only cold, unsupported `Review`-kind attempts (D20/D21).
pub(super) fn teaching_level(
    card: &Card,
    revlog: &[RevlogEntry],
    independent_successes: u32,
) -> u32 {
    if revlog.is_empty() {
        return 0;
    }
    if card.ctype == CardType::Relearn {
        return 3;
    }
    let successes = revlog.iter().filter(|e| e.button_chosen >= 2).count() as u32;
    if successes >= independent_successes {
        2
    } else {
        1
    }
}

/// Single read-only pass over every skill card, bucketed by topic.
fn gather_topic_aggs(col: &mut Collection) -> Result<HashMap<String, TopicAgg>> {
    let graph = graph();
    let cards = col.all_cards_for_search(SKILL_TAG_SEARCH)?;
    let timing = current_timing(col)?;
    let fsrs = FSRS::new(None)?;
    let independent_successes = graph.thresholds().independent_successes;

    let mut aggs: HashMap<String, TopicAgg> = HashMap::new();

    for card in &cards {
        let note = col
            .storage
            .get_note(card.note_id)?
            .or_not_found(card.note_id)?;
        let tags = &note.tags;

        let Some(topic_id) = tag_suffix(tags, TOPIC_TAG_PREFIX) else {
            invalid_input!(
                "manifold card {} (note {}) has an {} tag but no {} tag",
                card.id,
                card.note_id,
                SKILL_TAG_PREFIX,
                TOPIC_TAG_PREFIX
            );
        };
        if graph.topic(topic_id).is_none() {
            invalid_input!(
                "manifold card {} (note {}) references unknown topic '{}'",
                card.id,
                card.note_id,
                topic_id
            );
        }
        let Some(skill_id) = tag_suffix(tags, SKILL_TAG_PREFIX) else {
            invalid_input!(
                "manifold card {} (note {}) is missing an {} tag",
                card.id,
                card.note_id,
                SKILL_TAG_PREFIX
            );
        };

        let revlog = col.storage.get_revlog_entries_for_card(card.id)?;

        let agg = aggs.entry(topic_id.to_string()).or_default();
        // Register the skill so it counts toward `total` even if never studied.
        agg.skill_stabilities
            .entry(skill_id.to_string())
            .or_default();

        // The card's teaching level is competence-driven (see `teaching_level`),
        // not a direct read of its Anki CardType.
        match teaching_level(card, &revlog, independent_successes) {
            0 => agg.level_new += 1,
            1 => agg.level_guided += 1,
            2 => agg.level_independent += 1,
            _ => agg.level_revisited += 1,
        }

        if let (Some(state), Some(r)) = (card.memory_state, current_recall(&fsrs, card, &timing)) {
            agg.recall_sum += r;
            agg.recall_count += 1;
            agg.stability_sum += state.stability;
            agg.stability_count += 1;
            if let Some(stabilities) = agg.skill_stabilities.get_mut(skill_id) {
                stabilities.push(state.stability);
            }
        }

        for entry in revlog {
            if entry.button_chosen >= 1 {
                agg.graded_reviews += 1;
                // Only unsupported (Review-kind) attempts feed Performance and the
                // readiness give-up rule; Learning/Relearning are scaffolded.
                if entry.review_kind == RevlogReviewKind::Review {
                    agg.independent_reviews += 1;
                    if entry.button_chosen >= 2 {
                        agg.independent_good += 1;
                    }
                }
            }
        }
    }

    Ok(aggs)
}

fn rollup_topic(topic: &Topic, agg: Option<&TopicAgg>, mastery_stability: f32) -> Rollup {
    let mut mastered = 0;
    let mut total = 0;
    let mut avg_recall = 0.0;
    let mut avg_stability = 0.0;
    let mut performance = 0.0;
    let mut graded_reviews = 0;
    let mut independent_reviews = 0;
    let mut level_new = 0;
    let mut level_guided = 0;
    let mut level_independent = 0;
    let mut level_revisited = 0;

    if let Some(agg) = agg {
        total = agg.skill_stabilities.len() as u32;
        mastered = agg
            .skill_stabilities
            .values()
            .filter(|stabs| {
                !stabs.is_empty()
                    && stabs.iter().sum::<f32>() / stabs.len() as f32 >= mastery_stability
            })
            .count() as u32;
        if agg.recall_count > 0 {
            avg_recall = agg.recall_sum / agg.recall_count as f32;
        }
        if agg.stability_count > 0 {
            avg_stability = agg.stability_sum / agg.stability_count as f32;
        }
        // Performance is unsupported-only: good Review-kind / total Review-kind.
        if agg.independent_reviews > 0 {
            performance = agg.independent_good as f32 / agg.independent_reviews as f32;
        }
        graded_reviews = agg.graded_reviews;
        independent_reviews = agg.independent_reviews;
        level_new = agg.level_new;
        level_guided = agg.level_guided;
        level_independent = agg.level_independent;
        level_revisited = agg.level_revisited;
    }

    let coverage = if topic.expected_skills > 0 {
        (total as f32 / topic.expected_skills as f32).min(1.0)
    } else {
        0.0
    };
    let mastered_fraction = if total > 0 {
        mastered as f32 / total as f32
    } else {
        0.0
    };
    // Competence = skills answered correctly: cards at the Independent or
    // Revisited level (≥ 1 successful retrieval). Drives the mastery-learning
    // unlock gate (D28), separate from durable, stability-based mastery.
    let competent_fraction = if total > 0 {
        (level_independent + level_revisited) as f32 / total as f32
    } else {
        0.0
    };

    Rollup {
        mastered,
        total,
        avg_recall,
        avg_stability,
        coverage,
        performance,
        graded_reviews,
        independent_reviews,
        level_new,
        level_guided,
        level_independent,
        level_revisited,
        mastered_fraction,
        competent_fraction,
    }
}

/// Lock state for a topic:
/// - `mastered` when its own mastered fraction reaches its tier target;
/// - otherwise `locked` unless every prerequisite is *competent enough* — at
///   least `unlock_competent_fraction` of its skills answered correctly (root
///   topics have none, so they always clear this gate);
/// - a studied-but-unmastered topic (`total > 0` and some card has an FSRS
///   memory state, i.e. `avg_stability > 0`) is reported as `in_progress`.
///
/// Unlocking gates on the mastery-learning criterion — *competent enough*, at
/// least `unlock_competent_fraction` of the prerequisite's skills answered
/// correctly (D28) — not durable mastery. Durable mastery (D25) takes weeks of
/// stability, so gating progression on it stranded the learner on the single
/// root topic; competence-now is reachable in a session or two and is what
/// "learn it before you build on it" actually means. `mastered` (the violet
/// badge) stays the separate 21-day-stability goal.
fn lock_state(
    graph: &BlueprintGraph,
    topic: &Topic,
    rollups: &HashMap<&str, Rollup>,
    mastered: &HashMap<&str, bool>,
    competent_enough: &HashMap<&str, bool>,
) -> &'static str {
    if mastered[topic.id.as_str()] {
        return "mastered";
    }
    let prereqs_satisfied = graph
        .prereqs(&topic.id)
        .unwrap_or_default()
        .iter()
        .all(|prereq| competent_enough[prereq.as_str()]);
    if !prereqs_satisfied {
        return "locked";
    }
    let roll = &rollups[topic.id.as_str()];
    if roll.total > 0 && roll.avg_stability > 0.0 {
        "in_progress"
    } else {
        "unlocked"
    }
}

pub(super) fn tag_suffix<'a>(tags: &'a [String], prefix: &str) -> Option<&'a str> {
    tags.iter().find_map(|tag| tag.strip_prefix(prefix))
}
