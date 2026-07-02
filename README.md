# Manifold

Manifold is a GRE Mathematics Subject Test readiness trainer forked from
[Anki](https://apps.ankiweb.net). It keeps Anki's spaced-repetition engine (the
Rust FSRS scheduler and collection) and replaces the study surface with its own
interface: a readiness home, a topic dashboard, and a problem-player session. The
engine is shared with Anki; the user interface is proprietary to Manifold.

## The exam

Manifold targets the GRE Mathematics Subject Test, reported on the 200 to 990
scaled-score range. The syllabus is modeled as a prerequisite DAG of blueprint
topics across calculus, algebra, and the additional-topics tail, each split into
fine-grained skills that the scheduler tracks individually.

## Build and run

Manifold builds and runs through Anki's build system. From the repo root:

```
just run
```

The desktop shell boots straight into the Manifold home, with pages served by
Anki's mediasrv. To load the seed study deck into a collection, run the seed
importer with the built Python library on the path (after a build):

```
PYTHONPATH=out/pylib out/pyenv/bin/python \
    manifold/content/import_seed.py --temp
```

See [`manifold/content/README.md`](manifold/content/README.md) for the importer
and verifier, and [`docs/manifold/`](docs/manifold) for the product specs and
decision log.

## Architecture

- **Engine (shared with Anki).** A Rust RPC, `get_topic_graph`, walks every
  skill-tagged card once, reads each card's FSRS state, and rolls per-card
  retrievability up the prerequisite DAG into per-topic mastery, coverage, and
  lock state. It lives in `rslib/src/manifold/` and is declared in
  `proto/anki/manifold.proto`. The query only reads FSRS state; it never changes
  scheduling.
- **UI (proprietary).** The home, dashboard, and session screens are Svelte/TS
  pages (`ts/routes/manifold*`, `ts/lib/manifold/`) served over mediasrv. Anki's
  own chrome is hidden, so only Manifold's surfaces are shown.
- **Shell.** The Qt desktop shell (`qt/aqt/`) runs Anki as a headless engine and
  hosts the Manifold pages.
- **Skill identity.** Skills and topics ride Anki tags (`mf::topic::*`,
  `mf::skill::*`, `mf::tier::*`), so no database schema is forked.

## License and attribution

Manifold is licensed under AGPL-3.0-or-later, the same license as Anki. It is a
fork of Anki by Ankitects Pty Ltd and contributors; some Anki components are
BSD-3-Clause. Manifold reuses Anki's engine, build system, and sync protocol, and
credits the Anki project. The upstream Anki README follows below.

---

# Anki

[![Build Status](https://github.com/ankitects/anki/actions/workflows/ci.yml/badge.svg)](https://github.com/ankitects/anki/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-dev--docs.ankiweb.net-blue)](https://dev-docs.ankiweb.net)

This repo contains the source code for the computer version of
[Anki](https://apps.ankiweb.net).

## About

Anki is a spaced repetition program. Please see the [website](https://apps.ankiweb.net) to learn more.

## Getting Started

### Contributing

Want to contribute to Anki? Check out the [Contribution Guidelines](./docs/contributing.md).

For more information on building and developing, please see [Development](./docs/development.md).

#### Contributors

The following people have contributed to Anki: [CONTRIBUTORS](./CONTRIBUTORS)

### Anki Betas

If you'd like to try development builds of Anki but don't feel comfortable
building the code, please see [Anki betas](https://betas.ankiweb.net/).

## License

Anki's license: [LICENSE](./LICENSE)
