// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

//! Onboarding placement: a cold diagnostic + a coarse per-topic seed.
//!
//! Two read-only helpers ([`placement_completed`], [`build_placement_exam`])
//! plus one mutating helper ([`apply_placement`]) — the first place Manifold
//! *writes*. All writing flows through Anki's normal answer path
//! ([`Collection::grade_now`]), tags and config, so it is undo-safe and synced
//! by Anki's own protocol.
//!
//! Seeds are graded Good on `is:new` cards, which produces `Learning`-kind
//! revlog entries: they set the card's FSRS memory state and lift its teaching
//! level to Independent (so known material is not re-taught) and feed the
//! Memory score as a labeled prior, but are NOT `Review`-kind, so
//! `independent_reviews` and the readiness give-up rule (200 independent
//! reviews / 50% coverage) are left completely untouched.

use std::collections::HashMap;
use std::collections::HashSet;
use std::collections::VecDeque;

use anki_proto::manifold::SessionItem;

use crate::manifold::blueprint::graph;
use crate::manifold::mastery::tag_suffix;
use crate::prelude::*;
use crate::search::SortMode;

const TOPIC_TAG_PREFIX: &str = "mf::topic::";
const SKILL_TAG_PREFIX: &str = "mf::skill::";
const TIER_TAG_PREFIX: &str = "mf::tier::";
/// Tag marking a card whose state came from a placement seed, not real study,
/// so the prior is transparent and a future reset can find it.
const PLACEMENT_TAG: &str = "mf::placement";
/// Collection-config flag: onboarding completed or skipped.
const ONBOARDING_DONE_KEY: &str = "manifoldOnboardingDone";
/// Collection-config value: the Google account uid that currently owns this
/// collection's Manifold progress, so a different account signing in on this
/// device triggers a fresh start rather than inheriting the previous progress.
const OWNER_UID_KEY: &str = "manifoldOwnerUid";
/// Every probe is presented cold (the Independent teaching level).
const PLACEMENT_LEVEL: u32 = 2;
/// Good rating for seeding. `grade_now` takes the 0-indexed CardAnswer.Rating
/// (Again=0, Hard=1, Good=2, Easy=3); Good matches the session grade path.
const GOOD_RATING: i32 = 2;
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

/// Selects a short, cold diagnostic: up to `per_topic` distinct skills from
/// each requested topic, weight-ordered and interleaved across topics, capped
/// at [`PLACEMENT_MAX_ITEMS`]. Read-only. Unknown topic ids fail loudly.
pub(crate) fn build_placement_exam(
    col: &mut Collection,
    topic_ids: &[String],
    per_topic: u32,
) -> Result<Vec<SessionItem>> {
    let g = graph();
    let per_topic = per_topic.max(1) as usize;

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

    // One pass over the not-yet-attempted skill cards, bucketing up to
    // `per_topic` distinct skills per wanted topic (card-id order, for stability).
    // `is:new` only: a probe is always an untested skill, so answering it produces
    // a Learning-kind revlog and can never push Review-kind evidence into the
    // readiness gate — even on the Retake path, which bypasses the home gate.
    let mut by_topic: HashMap<&str, (f32, Vec<SessionItem>)> = HashMap::new();
    let mut seen_skill: HashSet<String> = HashSet::new();
    for card in col.all_cards_for_search("tag:mf::skill::* is:new")? {
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
        let tier = tag_suffix(tags, TIER_TAG_PREFIX)
            .unwrap_or_default()
            .to_string();
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
    let mut queues: Vec<VecDeque<SessionItem>> = topics
        .into_iter()
        .map(|(_, _, items)| items.into())
        .collect();

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

/// Seeds the not-yet-attempted skill cards of each known topic to Independent
/// and marks onboarding done. Returns the number of cards seeded. Mutating.
pub(crate) fn apply_placement(col: &mut Collection, known_topic_ids: &[String]) -> Result<u32> {
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
        let search = format!("tag:{SKILL_TAG_PREFIX}* tag:{TOPIC_TAG_PREFIX}{topic_id} is:new");
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

    // App-state flag, not user content: write it outside the undo history so an
    // undo of the seed grades can't silently clear "onboarding done".
    col.set_config_json(ONBOARDING_DONE_KEY, &true, false)?;
    Ok(seed_cids.len() as u32)
}

/// Binds the collection to a Google account, returning whether local Manifold
/// progress was reset because a *different* account signed in on this device.
///
/// The collection is a single local store, not per-account storage, so:
/// - an unclaimed collection is claimed by the first account without a reset,
///   so an existing user is not wiped on upgrade (its current progress becomes
///   that account's);
/// - the same account signing in again is a no-op;
/// - a different account deletes the local Manifold deck and clears the
///   onboarding flag, so onboarding reseeds a fresh deck and re-runs placement.
///   This is a fresh start, not a merge: progress not already synced to the
///   previous account's server is not preserved locally.
///
/// App-state config, not user content, so the owner/flag writes stay out of the
/// undo history. Fails loudly on an empty uid rather than claiming anonymously.
pub(crate) fn claim_account(col: &mut Collection, uid: &str) -> Result<bool> {
    if uid.trim().is_empty() {
        invalid_input!("claim_account requires a non-empty account uid");
    }
    match col.get_config_optional::<String, _>(OWNER_UID_KEY) {
        Some(ref owner) if owner.as_str() == uid => Ok(false),
        Some(_) => {
            let nids = col.search_notes("tag:mf::*", SortMode::NoOrder)?;
            if !nids.is_empty() {
                col.remove_notes(&nids)?;
            }
            col.set_config_json(ONBOARDING_DONE_KEY, &false, false)?;
            col.set_config_json(OWNER_UID_KEY, &uid, false)?;
            Ok(true)
        }
        None => {
            col.set_config_json(OWNER_UID_KEY, &uid, false)?;
            Ok(false)
        }
    }
}
