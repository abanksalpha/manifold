# Manifold GRE Math seed content

This folder holds the seed study content for Manifold, the GRE Mathematics
Subject Test trainer forked from Anki, plus a reproducible importer and a
functional check. It only adds content; it never touches the Rust engine, the
blueprint, or any other part of the app.

Files:

- `seed_deck.json` — the authored skill set: one entry per fine-grained GRE
  skill, covering every topic in the engine blueprint.
- `import_seed.py` — opens an Anki collection and turns each skill into a
  `Basic` note tagged for the Manifold engine.
- `verify_seed.py` — imports the deck into a fresh temporary collection and
  asserts the `get_topic_graph` RPC returns sane data.

## How it ties into the engine

The engine (`rslib/src/manifold/`) layers a GRE-Math skill DAG on top of
ordinary Anki notes using three tags per note. The DAG itself lives in
`rslib/src/manifold/blueprint.json` (33 topics, each with an `id`, `title`,
`area`, `tier`, `weight`, `expected_skills`, and `prereqs`). A "skill" is just
an Anki note carrying:

- `mf::topic::<topic_id>` — the blueprint topic the skill belongs to.
- `mf::skill::<skill_id>` — the skill's unique slug.
- `mf::tier::<tier>` — the topic's tier (`relearn`, `teach`, or `recognize`).

Tag components are lowercase, use underscores, and contain no spaces.
`get_topic_graph` buckets cards by their `mf::topic::` tag, counts distinct
`mf::skill::` ids as the topic's `total`, and rolls FSRS state up the
prerequisite DAG into per-topic mastery and lock state.

## `seed_deck.json` shape

```json
{
    "deck": "GRE Mathematics",
    "note_type": "Basic",
    "skills": [
        {
            "topic_id": "differential_calc",
            "skill_id": "chain_rule",
            "tier": "relearn",
            "name": "Chain rule"
        }
    ]
}
```

Each skill becomes one note: `Front` is `name`, `Back` is the topic's blueprint
`title`. Every blueprint topic is covered, the calculus core topics are
authored up to their `expected_skills` so coverage is realistic, and every
topic has at least three skills. The importer validates every entry against
`blueprint.json` (topic must exist, `tier` must match the topic's blueprint
tier, `skill_id` must be unique) and fails loudly on any mismatch.

## Running the importer

The importer uses the real Anki Python API, so `pylib` and its compiled
`rsbridge` backend must be importable. After a build (`just build` or
`just check`), the built library is under `out/pylib` and the project's
virtualenv interpreter is at `out/pyenv/bin/python`. From the repo root:

```bash
# import into a specific collection (created if the .anki2 file is absent)
PYTHONPATH=out/pylib out/pyenv/bin/python \
    manifold/content/import_seed.py /path/to/collection.anki2

# or import into a throwaway temp collection (its path is printed)
PYTHONPATH=out/pylib out/pyenv/bin/python \
    manifold/content/import_seed.py --temp
```

The script ensures the `GRE Mathematics` deck exists, adds a `Basic` note for
each skill, and prints a per-topic summary of notes added. It is idempotent:
a skill whose `mf::skill::<skill_id>` tag is already present is skipped, so
re-running never creates duplicates.

## Verifying

`verify_seed.py` is the functional check. It builds a fresh empty collection
with pylib's own test factory, imports the deck, calls `get_topic_graph`, and
asserts that (a) every topic's `total` matches the authored skill count,
(b) root topics are `unlocked`, and (c) a deep topic with unmastered
prerequisites (`metric_topology`) is `locked`.

```bash
PYTHONPATH=out/pylib ANKI_TEST_MODE=1 out/pyenv/bin/python \
    manifold/content/verify_seed.py
```
