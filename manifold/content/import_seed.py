# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Reproducible importer for the Manifold GRE Mathematics seed deck.

Run from the repo root, after a build so that pylib and its compiled rsbridge
backend are importable (PYTHONPATH must point at the built pylib):

    # against a specific collection (created if the file does not exist)
    PYTHONPATH=out/pylib out/pyenv/bin/python \
        manifold/content/import_seed.py /path/to/collection.anki2

    # against a throwaway temp collection (path is printed)
    PYTHONPATH=out/pylib out/pyenv/bin/python \
        manifold/content/import_seed.py --temp

`seed_deck.json` shape (authored by hand, kept in sync with the engine
blueprint at rslib/src/manifold/blueprint.json):

    {
        "deck": "GRE Mathematics",
        "note_type": "Basic",
        "skills": [
            {
                "topic_id": "differential_calc", # an existing blueprint topic id
                "skill_id": "chain_rule",        # unique slug, no spaces
                "tier": "relearn",               # must equal the topic's tier
                "name": "Chain rule"             # human-readable display
            },
            ...
        ]
    }

Each skill becomes one `Basic` note in the deck: Front = `name`,
Back = the topic's blueprint `title`, tagged with the three Manifold tags the
engine reads:

    mf::topic::<topic_id>   mf::skill::<skill_id>   mf::tier::<tier>

The importer is idempotent: a skill whose `mf::skill::<skill_id>` tag already
exists in the collection is skipped, so re-running never creates duplicates.

Before importing, a one-pass migration repairs notes whose `mf::topic::<id>` is
no longer a current blueprint topic (i.e. seeded by an older taxonomy
generation): each is re-tagged to the topic its `mf::skill::<skill_id>` now maps
to in the seed. A stale-tagged note whose skill is unknown raises rather than
being skipped or defaulted.

Nothing is mocked or faked. Every input is validated against the blueprint up
front and any inconsistency (unknown topic, wrong tier, duplicate id, missing
notetype/deck) raises immediately rather than degrading silently.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

CONTENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CONTENT_DIR.parents[1]
DEFAULT_SEED = CONTENT_DIR / "seed_deck.json"
DEFAULT_BLUEPRINT = REPO_ROOT / "rslib" / "src" / "manifold" / "blueprint.json"

TOPIC_TAG_PREFIX = "mf::topic::"
SKILL_TAG_PREFIX = "mf::skill::"
TIER_TAG_PREFIX = "mf::tier::"

# Floor on authored skills per topic, mirroring the seed-content contract.
MIN_SKILLS_PER_TOPIC = 3

# Fields required on every seed skill entry.
_REQUIRED_FIELDS = ("topic_id", "skill_id", "tier", "name")
# Fields that become tags and therefore must not contain spaces.
_TAG_FIELDS = ("topic_id", "skill_id", "tier")


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file, failing loudly if it is missing."""
    if not path.is_file():
        raise FileNotFoundError(f"required JSON file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_topic_index(blueprint: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map blueprint topic id -> topic object."""
    topics = blueprint["topics"]
    index: dict[str, dict[str, Any]] = {}
    for topic in topics:
        index[topic["id"]] = topic
    return index


def validate_seed(seed: dict[str, Any], topics: dict[str, dict[str, Any]]) -> None:
    """Validate the seed deck against the blueprint, raising on any problem."""
    skills = seed.get("skills")
    if not skills:
        raise ValueError("seed_deck.json has no 'skills'")

    seen: set[str] = set()
    per_topic: dict[str, int] = {}
    for idx, skill in enumerate(skills):
        for field in _REQUIRED_FIELDS:
            value = skill.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f"skill #{idx} is missing/empty field {field!r}: {skill!r}")
        for field in _TAG_FIELDS:
            if " " in str(skill[field]):
                raise ValueError(
                    f"skill {skill['skill_id']!r} field {field!r} contains a space; "
                    "tag components must be lowercase_with_underscores"
                )

        topic_id = skill["topic_id"]
        topic = topics.get(topic_id)
        if topic is None:
            raise ValueError(f"skill {skill['skill_id']!r} references unknown topic {topic_id!r}")
        if skill["tier"] != topic["tier"]:
            raise ValueError(
                f"skill {skill['skill_id']!r} tier {skill['tier']!r} does not match "
                f"blueprint tier {topic['tier']!r} for topic {topic_id!r}"
            )

        skill_id = skill["skill_id"]
        if skill_id in seen:
            raise ValueError(f"duplicate skill_id {skill_id!r}")
        seen.add(skill_id)
        per_topic[topic_id] = per_topic.get(topic_id, 0) + 1

    for topic_id in topics:
        count = per_topic.get(topic_id, 0)
        if count < MIN_SKILLS_PER_TOPIC:
            raise ValueError(
                f"topic {topic_id!r} has only {count} authored skill(s); "
                f"the contract requires at least {MIN_SKILLS_PER_TOPIC}"
            )


def _tag_suffix(tag: str, prefix: str) -> str | None:
    """Return the id portion of a `<prefix><id>` tag, or None if it lacks it."""
    if tag.startswith(prefix):
        return tag[len(prefix):]
    return None


def migrate_stale_topic_tags(
    col: Any,
    valid_topic_ids: set[str],
    skill_to_topic: dict[str, str],
) -> dict[str, int]:
    """Re-tag notes whose `mf::topic::<id>` is not a current blueprint topic.

    The blueprint taxonomy evolves across generations (topics get split,
    renamed, or regrouped), so a collection seeded by an older generation can
    carry `mf::topic::<id>` tags whose id the current blueprint no longer
    defines (e.g. `calc.single_var`, `precalc_trig`, `single_var_diff`). The
    engine loudly rejects any such card — which is correct — so this migration
    repairs the drift generically: it resolves each note's stable
    `mf::skill::<skill_id>` tag against the current seed's skill_id -> topic_id
    map and rewrites the topic tag to the resolved current id. No per-legacy-id
    mapping is hardcoded; any id absent from `valid_topic_ids` is migrated.

    Runs at the top of `import_seed`, BEFORE the per-skill skip loop, because a
    stale note already carries its `mf::skill` tag and would otherwise be
    skipped there with its bad topic tag left in place.

    For every note carrying an `mf::topic::` tag:
      * a topic id already in `valid_topic_ids` is left untouched;
      * a topic id NOT in `valid_topic_ids` is resolved from the note's single
        `mf::skill::<skill_id>` tag via `skill_to_topic`, the stale tag removed
        and the resolved `mf::topic::<current_id>` added, then the note saved;
      * if such a note has no skill tag, more than one, or a skill id absent
        from `skill_to_topic` (the skill itself was renamed/removed), a
        ValueError is raised naming the note id, the stale topic tag(s), and the
        skill id. Nothing is skipped, defaulted, or deleted.

    Returns `{stale_topic_id: <notes rewritten>}`, keyed by the OLD id, so the
    caller can report e.g. `{"calc.single_var": 1, "precalc_trig": 4}`. The
    engine's unknown-topic error stays the backstop for anything not covered.
    """
    rewritten: dict[str, int] = {}
    for nid in col.find_notes(f"tag:{TOPIC_TAG_PREFIX}*"):
        note = col.get_note(nid)
        topic_ids = [
            tid for tid in (_tag_suffix(t, TOPIC_TAG_PREFIX) for t in note.tags)
            if tid is not None
        ]
        stale_ids = [tid for tid in topic_ids if tid not in valid_topic_ids]
        if not stale_ids:
            continue

        skill_ids = [
            sid for sid in (_tag_suffix(t, SKILL_TAG_PREFIX) for t in note.tags)
            if sid is not None
        ]
        stale_repr = ", ".join(repr(f"{TOPIC_TAG_PREFIX}{tid}") for tid in stale_ids)
        if len(skill_ids) != 1:
            raise ValueError(
                f"stale topic migration: note {nid} carries stale topic tag(s) "
                f"[{stale_repr}] but has {len(skill_ids)} {SKILL_TAG_PREFIX}* "
                f"tag(s) (tags={note.tags!r}); need exactly one to resolve the "
                "current topic"
            )

        skill_id = skill_ids[0]
        resolved_topic = skill_to_topic.get(skill_id)
        if resolved_topic is None:
            raise ValueError(
                f"stale topic migration: note {nid} carries stale topic tag(s) "
                f"[{stale_repr}] and skill tag {SKILL_TAG_PREFIX}{skill_id!r}, but "
                "that skill id is not in the current seed's skill_id -> topic_id "
                "map; cannot determine the current topic to rewrite to"
            )

        resolved_tag = f"{TOPIC_TAG_PREFIX}{resolved_topic}"
        for stale_id in stale_ids:
            note.remove_tag(f"{TOPIC_TAG_PREFIX}{stale_id}")
            rewritten[stale_id] = rewritten.get(stale_id, 0) + 1
        if not note.has_tag(resolved_tag):
            note.add_tag(resolved_tag)
        col.update_note(note)

    return rewritten


def import_seed(
    col: Any,
    seed_path: Path = DEFAULT_SEED,
    blueprint_path: Path = DEFAULT_BLUEPRINT,
) -> tuple[dict[str, int], dict[str, int]]:
    """Import the seed deck into an already-open collection.

    Returns (added_per_topic, skipped_per_topic). Skipped skills are ones whose
    mf::skill tag already exists in the collection (idempotent re-run).
    """
    seed = load_json(seed_path)
    blueprint = load_json(blueprint_path)
    topics = build_topic_index(blueprint)
    validate_seed(seed, topics)

    # Stale topic-tag migration. Runs BEFORE the per-skill skip loop below: a
    # note from an older taxonomy generation already carries its mf::skill tag
    # and would otherwise be skipped there, leaving its stale mf::topic tag to
    # trip the engine's unknown-topic error. The valid-topic set and the
    # resolution map both come from the current seed, so any tag not in the
    # current taxonomy is repaired to the topic its skill now maps to.
    skill_to_topic = {skill["skill_id"]: skill["topic_id"] for skill in seed["skills"]}
    valid_topic_ids = set(skill_to_topic.values())
    migrated = migrate_stale_topic_tags(col, valid_topic_ids, skill_to_topic)
    if migrated:
        total = sum(migrated.values())
        print(
            "Manifold stale topic-tag migration: "
            f"{total} note(s) re-tagged -> {migrated}"
        )

    deck_name = seed["deck"]
    notetype_name = seed.get("note_type", "Basic")

    deck_id = col.decks.id(deck_name)
    if deck_id is None:
        raise RuntimeError(f"could not create or find deck {deck_name!r}")
    notetype = col.models.by_name(notetype_name)
    if notetype is None:
        raise RuntimeError(f"notetype {notetype_name!r} not found in collection")

    added: dict[str, int] = {}
    skipped: dict[str, int] = {}
    for skill in seed["skills"]:
        topic_id = skill["topic_id"]
        skill_id = skill["skill_id"]

        if col.find_notes(f"tag:{SKILL_TAG_PREFIX}{skill_id}"):
            skipped[topic_id] = skipped.get(topic_id, 0) + 1
            continue

        note = col.new_note(notetype)
        note["Front"] = skill["name"]
        note["Back"] = topics[topic_id]["title"]
        note.tags = [
            f"{TOPIC_TAG_PREFIX}{topic_id}",
            f"{SKILL_TAG_PREFIX}{skill_id}",
            f"{TIER_TAG_PREFIX}{skill['tier']}",
        ]
        col.add_note(note, deck_id)
        added[topic_id] = added.get(topic_id, 0) + 1

    enable_fsrs(col, deck_id)
    return added, skipped


def enable_fsrs(col: Any, deck_id: Any) -> bool:
    """Enable FSRS collection-wide and reschedule; return whether it changed.

    The Manifold engine derives per-skill mastery from each card's FSRS memory
    state (see rslib/src/manifold/mastery.rs). Without FSRS those states are
    never populated, so every topic's mastered fraction stays 0 and the
    prerequisite DAG can never unlock past its roots. Enabling FSRS keeps a
    freshly seeded collection consistent with that assumption. Idempotent: a
    no-op when FSRS is already on.
    """
    from anki.decks import UpdateDeckConfigs, UpdateDeckConfigsMode

    snapshot = col.decks.get_deck_configs_for_update(deck_id)
    if snapshot.fsrs:
        print("FSRS already enabled.")
        return False

    request = UpdateDeckConfigs()
    request.target_deck_id = deck_id
    current_id = snapshot.current_deck.config_id
    request.configs.append(
        next(
            (c.config for c in snapshot.all_config if c.config.id == current_id),
            snapshot.all_config[0].config,
        )
    )
    request.mode = UpdateDeckConfigsMode.UPDATE_DECK_CONFIGS_MODE_NORMAL
    request.fsrs = True
    request.fsrs_reschedule = True
    request.new_cards_ignore_review_limit = snapshot.new_cards_ignore_review_limit
    request.apply_all_parent_limits = snapshot.apply_all_parent_limits
    request.limits.CopyFrom(snapshot.current_deck.limits)
    col.decks.update_deck_configs(request)
    print("FSRS enabled and cards rescheduled.")
    return True


def print_summary(
    added: dict[str, int],
    skipped: dict[str, int],
    topics: dict[str, dict[str, Any]],
) -> None:
    """Print notes added (and skipped) per topic, in blueprint order."""
    print("Manifold seed import summary (notes added per topic):")
    total_added = 0
    total_skipped = 0
    for topic_id in topics:
        a = added.get(topic_id, 0)
        s = skipped.get(topic_id, 0)
        suffix = f"  (skipped {s} already present)" if s else ""
        print(f"  {topic_id:<20} +{a}{suffix}")
        total_added += a
        total_skipped += s
    print(f"Total: {total_added} note(s) added, {total_skipped} skipped (already present).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import the Manifold GRE Math seed deck.")
    parser.add_argument(
        "collection",
        nargs="?",
        help="path to a .anki2 collection (created if the file does not exist)",
    )
    parser.add_argument(
        "--temp",
        action="store_true",
        help="operate on a fresh throwaway temp collection instead of a path",
    )
    parser.add_argument("--seed", default=str(DEFAULT_SEED), help="path to seed_deck.json")
    parser.add_argument(
        "--blueprint",
        default=str(DEFAULT_BLUEPRINT),
        help="path to the engine blueprint.json (for validation)",
    )
    args = parser.parse_args(argv)

    if args.temp and args.collection:
        parser.error("pass either a collection path or --temp, not both")
    if not args.temp and not args.collection:
        parser.error("provide a collection path, or --temp for a throwaway collection")

    # Imported lazily so the module's functions can be reused (e.g. by
    # verify_seed.py) against an already-open collection without importing anki.
    from anki.collection import Collection

    if args.temp:
        fd, path = tempfile.mkstemp(suffix=".anki2")
        os.close(fd)
        os.unlink(path)
        print(f"Using temp collection: {path}")
    else:
        path = args.collection

    col = Collection(path)
    try:
        added, skipped = import_seed(col, Path(args.seed), Path(args.blueprint))
        topics = build_topic_index(load_json(Path(args.blueprint)))
        print_summary(added, skipped, topics)
    finally:
        col.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
