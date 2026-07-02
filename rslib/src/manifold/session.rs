// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

//! Read-only session-queue builder.
//!
//! Decides which skill cards to serve next and in what order, enforcing the
//! prerequisite DAG. It only ever *reads*: current FSRS retrievability, Anki's
//! own due/new classification (`is:due` / `is:new`, so the timing math is never
//! reimplemented), the per-topic lock states (shared with the dashboard via
//! [`topic_lock_states`]) and the static blueprint. It never mutates a card,
//! its scheduling, or the queue, so it is undo-safe by construction. Grading
//! still flows through Anki's normal answering path, so FSRS reschedules
//! exactly as before.
//!
//! Ordering (tier-major — cover circles/relearn before squares/teach before
//! diamonds/recognize, D29):
//! - **Due** cards (already introduced) are served first, regardless of lock;
//!   within a tier they order by *points-at-stake* =
//!   `blueprint_weight(topic) × weakness`, where `weakness = 1 − R`.
//! - **New** cards follow, drawn only from topics the DAG has `unlocked` or put
//!   `in_progress` (locked and mastered topics contribute none), capped at
//!   `thresholds.new_per_day`; the budget fills lower tiers first, then within a
//!   tier the highest blueprint weight.
//! - Within each tier both phases are interleaved across topics, so consecutive
//!   items come from different topics where possible while honouring
//!   points-at-stake; a later tier never precedes an earlier one.

use std::collections::HashMap;
use std::collections::VecDeque;

use anki_proto::manifold::SessionItem;
use fsrs::FSRS;

use crate::manifold::blueprint::graph;
use crate::manifold::mastery::current_recall;
use crate::manifold::mastery::current_timing;
use crate::manifold::mastery::tag_suffix;
use crate::manifold::mastery::teaching_level;
use crate::manifold::mastery::topic_lock_states;
use crate::prelude::*;

/// Skill cards already studied and due now, by Anki's own timing.
const SKILL_DUE_SEARCH: &str = "tag:mf::skill::* is:due";
/// Skill cards never studied, by Anki's own classification.
const SKILL_NEW_SEARCH: &str = "tag:mf::skill::* is:new";

const TOPIC_TAG_PREFIX: &str = "mf::topic::";
const SKILL_TAG_PREFIX: &str = "mf::skill::";
const TIER_TAG_PREFIX: &str = "mf::tier::";

/// A served item plus the priority that ordered it. `points` is only used while
/// building the queue; the response carries the [`SessionItem`] alone.
struct Candidate {
    item: SessionItem,
    points: f32,
}

/// The skill identity read off a card's note.
struct SkillRef {
    topic_id: String,
    skill_id: String,
    tier: String,
    skill_name: String,
}

/// Builds the ordered session queue. Read-only: see the module docs.
pub(crate) fn build_session_queue(col: &mut Collection) -> Result<Vec<SessionItem>> {
    let lock_states = topic_lock_states(col)?;
    let timing = current_timing(col)?;
    let fsrs = FSRS::new(None)?;
    let thresholds = graph().thresholds();

    // Due cards: all of them, regardless of lock, ordered by points-at-stake.
    let mut due = Vec::new();
    for card in col.all_cards_for_search(SKILL_DUE_SEARCH)? {
        let skill = read_skill(col, &card)?;
        let topic = topic_weight_title(&card, &skill.topic_id)?;
        // Unknown recall (a card with no FSRS memory state, e.g. imported from
        // SM-2) is treated as fully at risk rather than hidden.
        let weakness = current_recall(&fsrs, &card, &timing)
            .map(|r| (1.0 - r).clamp(0.0, 1.0))
            .unwrap_or(1.0);
        let revlog = col.storage.get_revlog_entries_for_card(card.id)?;
        let level = teaching_level(&card, &revlog, thresholds.independent_successes);
        due.push(candidate(&card, skill, topic, topic.0 * weakness, level));
    }

    // New cards: only from unlocked / in-progress topics (prerequisite gating),
    // capped at the daily budget, in tier-then-weight order (see the sort below).
    let mut new = Vec::new();
    for card in col.all_cards_for_search(SKILL_NEW_SEARCH)? {
        let skill = read_skill(col, &card)?;
        let unlocked = matches!(
            lock_states.get(&skill.topic_id).map(String::as_str),
            Some("unlocked") | Some("in_progress")
        );
        if !unlocked {
            continue;
        }
        let topic = topic_weight_title(&card, &skill.topic_id)?;
        let revlog = col.storage.get_revlog_entries_for_card(card.id)?;
        let level = teaching_level(&card, &revlog, thresholds.independent_successes);
        // A never-studied skill has no recall, so its whole weight is at stake.
        new.push(candidate(&card, skill, topic, topic.0, level));
    }
    // Introduce new cards in tier order too, so the daily budget fills circles
    // (relearn) before squares (teach) before diamonds (recognize).
    new.sort_by(|a, b| {
        tier_rank(&a.item.tier)
            .cmp(&tier_rank(&b.item.tier))
            .then_with(|| order_by_points(a, b))
    });
    new.truncate(thresholds.new_per_day as usize);

    let mut items = ordered_by_tier(due);
    items.extend(ordered_by_tier(new));
    Ok(items.into_iter().map(|c| c.item).collect())
}

/// Weight and title of a card's blueprint topic (static reference data).
fn topic_weight_title(card: &Card, topic_id: &str) -> Result<(f32, &'static str)> {
    let Some(topic) = graph().topic(topic_id) else {
        invalid_input!(
            "manifold card {} references unknown topic '{}'",
            card.id,
            topic_id
        );
    };
    Ok((topic.weight, topic.title.as_str()))
}

fn candidate(
    card: &Card,
    skill: SkillRef,
    topic: (f32, &str),
    points: f32,
    level: u32,
) -> Candidate {
    Candidate {
        item: SessionItem {
            card_id: card.id.0,
            skill_id: skill.skill_id,
            skill_name: skill.skill_name,
            topic_id: skill.topic_id,
            topic_title: topic.1.to_string(),
            tier: skill.tier,
            level,
        },
        points,
    }
}

/// Reads the topic, skill, tier and display name off a card's note, failing
/// loudly if any piece of the skill identity is missing.
fn read_skill(col: &mut Collection, card: &Card) -> Result<SkillRef> {
    let note = col
        .storage
        .get_note(card.note_id)?
        .or_not_found(card.note_id)?;
    let tags = &note.tags;
    let Some(topic_id) = tag_suffix(tags, TOPIC_TAG_PREFIX) else {
        invalid_input!(
            "manifold card {} (note {}) is missing a {} tag",
            card.id,
            card.note_id,
            TOPIC_TAG_PREFIX
        );
    };
    let Some(skill_id) = tag_suffix(tags, SKILL_TAG_PREFIX) else {
        invalid_input!(
            "manifold card {} (note {}) is missing a {} tag",
            card.id,
            card.note_id,
            SKILL_TAG_PREFIX
        );
    };
    let Some(tier) = tag_suffix(tags, TIER_TAG_PREFIX) else {
        invalid_input!(
            "manifold card {} (note {}) is missing a {} tag",
            card.id,
            card.note_id,
            TIER_TAG_PREFIX
        );
    };
    let skill_name = note.fields().first().map(|f| f.trim()).unwrap_or_default();
    if skill_name.is_empty() {
        invalid_input!(
            "manifold card {} (note {}) has an empty Front field",
            card.id,
            card.note_id
        );
    }
    Ok(SkillRef {
        topic_id: topic_id.to_string(),
        skill_id: skill_id.to_string(),
        tier: tier.to_string(),
        skill_name: skill_name.to_string(),
    })
}

/// Order by descending points-at-stake, then ascending card id for stability.
fn order_by_points(a: &Candidate, b: &Candidate) -> std::cmp::Ordering {
    b.points
        .partial_cmp(&a.points)
        .unwrap_or(std::cmp::Ordering::Equal)
        .then(a.item.card_id.cmp(&b.item.card_id))
}

/// Tier study order: relearn (circle) → teach (square) → recognize (diamond).
/// An unknown tier sorts last so it can never jump ahead of a known tier.
fn tier_rank(tier: &str) -> u8 {
    match tier {
        "relearn" => 0,
        "teach" => 1,
        "recognize" => 2,
        _ => 3,
    }
}

/// Orders a phase tier-major (D29): group by tier, interleave across topics
/// within each tier, then concatenate relearn → teach → recognize so a later
/// tier never precedes an earlier one. Interleaving still spreads consecutive
/// items across topics *within* a tier.
fn ordered_by_tier(candidates: Vec<Candidate>) -> Vec<Candidate> {
    let mut by_tier: [Vec<Candidate>; 4] = [Vec::new(), Vec::new(), Vec::new(), Vec::new()];
    for candidate in candidates {
        by_tier[tier_rank(&candidate.item.tier) as usize].push(candidate);
    }
    by_tier.into_iter().flat_map(interleave).collect()
}

/// Spreads consecutive items across topics while honouring points-at-stake.
///
/// Each topic's items are queued in points order; the server then repeatedly
/// takes the highest-points item whose topic differs from the one just served,
/// only repeating a topic when nothing else remains. When every item is from a
/// distinct topic this reduces to a pure points-descending order.
fn interleave(candidates: Vec<Candidate>) -> Vec<Candidate> {
    let mut ordered = candidates;
    ordered.sort_by(order_by_points);

    let mut groups: Vec<VecDeque<Candidate>> = Vec::new();
    let mut index: HashMap<String, usize> = HashMap::new();
    for candidate in ordered {
        let topic = candidate.item.topic_id.clone();
        let slot = *index.entry(topic).or_insert_with(|| {
            groups.push(VecDeque::new());
            groups.len() - 1
        });
        groups[slot].push_back(candidate);
    }

    let mut result = Vec::new();
    let mut last_topic: Option<String> = None;
    loop {
        // Prefer a different topic than the last served; fall back to any.
        let pick = pick_group(&groups, last_topic.as_deref(), true)
            .or_else(|| pick_group(&groups, last_topic.as_deref(), false));
        let Some(slot) = pick else {
            break;
        };
        let candidate = groups[slot].pop_front().expect("non-empty group");
        last_topic = Some(candidate.item.topic_id.clone());
        result.push(candidate);
    }
    result
}

/// Index of the group whose head has the highest points (ties broken by card
/// id). When `differ` is set, groups matching `last_topic` are skipped.
fn pick_group(
    groups: &[VecDeque<Candidate>],
    last_topic: Option<&str>,
    differ: bool,
) -> Option<usize> {
    let mut best: Option<usize> = None;
    for (slot, group) in groups.iter().enumerate() {
        let Some(head) = group.front() else {
            continue;
        };
        if differ && last_topic == Some(head.item.topic_id.as_str()) {
            continue;
        }
        let better = match best {
            None => true,
            Some(b) => {
                order_by_points(head, groups[b].front().expect("non-empty group"))
                    == std::cmp::Ordering::Less
            }
        };
        if better {
            best = Some(slot);
        }
    }
    best
}
