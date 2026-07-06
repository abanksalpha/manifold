# Manifold

Manifold is a study app for the **GRE Mathematics Subject Test**, forked from
[Anki](https://apps.ankiweb.net). It runs on desktop and on Android from one
shared engine, and it reports three separate scores, each with a range: memory
(can the learner recall a practiced skill), performance (can the learner answer a
fresh exam-style item cold), and readiness (what they would score today, or a
refusal when the evidence is too thin).

Manifold keeps Anki's spaced-repetition engine, the Rust FSRS scheduler and
collection, and replaces the study surface with its own interface: a readiness
home, a topic dashboard, and a problem-player session. The engine is shared with
Anki; the user interface is proprietary to Manifold.

## The exam

The GRE Mathematics Subject Test is reported on the 200 to 990 scaled-score
range. Manifold models the official syllabus as a prerequisite DAG of blueprint
topics across calculus, algebra, and the additional-topics tail, each split into
fine-grained skills the scheduler tracks individually and each weighted by its
share of exam points.

## Build and run

Both apps share one Rust engine (`rslib`); the Manifold change lives inside it,
so desktop and Android build from the same source.

### Desktop

Manifold builds and runs through Anki's build system. From the repo root:

```
just run
```

The desktop shell boots straight into the Manifold home, with pages served by
Anki's mediasrv. Use `just run-optimized` for a release-optimized build, and
`just check` to format and run the full build and checks. To load the seed study
deck into a temporary collection (after a build):

```
PYTHONPATH=out/pylib out/pyenv/bin/python \
    manifold/content/import_seed.py --temp
```

See [`manifold/content/README.md`](manifold/content/README.md) for the importer
and verifier.

### Android

The Android companion is built on
[AnkiDroid](https://github.com/ankidroid/Anki-Android), which already runs Anki's
Rust backend on device, so the same `rslib` (carrying the Manifold change) ships
to the phone without a rewrite. The build path, cross-compiling `rslib` for
Android and loading the GRE deck in an AnkiDroid shell, is set out in the buildout
plan ([`docs/manifold/plan-buildout.md`](docs/manifold/plan-buildout.md), WS7 and
WS9) and [`docs/manifold/spec-mobile-sync.md`](docs/manifold/spec-mobile-sync.md).
Mobile is sequenced last in that plan (decision D31); when it is absent from a
checkout, the desktop app stands on its own.

## Architecture

Manifold layers onto Anki without forking the scheduler or the synced database
schema. It adds read-only aggregation in Rust and a new set of web pages, then
derives three scores on top.

- **Engine (shared Rust, `rslib/src/manifold/`).** A read-only RPC,
  `get_topic_graph`, walks every skill-tagged card once, reads each card's FSRS
  state, and rolls per-card retrievability up the prerequisite DAG into per-topic
  mastery, coverage, teaching-level counts, and lock state. A companion
  `build_session_queue` RPC orders the due queue by points at stake, with an
  interleave flag. Both are declared in `proto/anki/manifold.proto`. Neither
  changes FSRS parameters or scheduling; they only read state, which keeps undo
  and sync intact.
- **Bindings (`pylib/`).** `pylib` and its `rsbridge` expose the engine to
  Python; `_backend.py` provides the snake_case RPC methods, and the same
  contract reaches TypeScript through the generated backend module.
- **Web UI (`ts/`, proprietary).** The home, dashboard, and session screens are
  Svelte/TypeScript pages (`ts/routes/manifold*`, `ts/lib/manifold/`) served over
  mediasrv, with all mathematics typeset through the repo's MathJax build. Anki's
  own chrome is hidden, so only Manifold's surfaces are shown.
- **Desktop shell (`qt/aqt/`).** The Qt shell runs Anki as a headless engine and
  hosts the Manifold pages.
- **Three scores (`ts/lib/manifold/scoring.ts`).** Memory (FSRS recall),
  performance (cold Review-kind accuracy), and readiness (an ETS-anchored scaled
  range) are derived separately from the topic graph, each with a range, never
  blended into one number. Readiness refuses to answer below a stated give-up
  line of at least 200 independent reviews and 50% coverage. See
  [`docs/manifold/model-cards.md`](docs/manifold/model-cards.md).
- **Template-first, AI-free answer path.** The review loop serves problems from
  deterministic parametric templates whose numbers are drawn per review and whose
  answer is computed by SymPy (`solver.py`), never asserted by a model; untemplated
  teach skills fall back to a pre-vetted, verified bank. No model call sits on the
  graded answer path, so a wrong model or a prompt injection cannot serve a wrong
  answer, and both apps still produce a score with AI switched off. Content authoring
  and the Socratic hint tutor are the only LLM roles, each behind a code gate — see
  [`docs/manifold/ai-note.md`](docs/manifold/ai-note.md).
- **Skill identity.** Skills and topics ride Anki tags (`mf::topic::*`,
  `mf::skill::*`, `mf::tier::*`), so no synced database schema is forked.

## The Rust change

The required engine change and its rationale are written up in
[`docs/manifold/why-rust.md`](docs/manifold/why-rust.md): why the mastery rollup
belongs in Rust rather than Python or TypeScript, backed by the latency
benchmark. Every upstream Anki file Manifold modified, with a per-file
merge-difficulty note, is listed in
[`docs/manifold/touched-files.md`](docs/manifold/touched-files.md). The product
specs and the decision log live in [`docs/manifold/`](docs/manifold).

## Evidence and results

Every graded claim is backed by a re-runnable script (`just eval`, `just eval-ai`,
`just demo-sync`, `just bench`); the consolidated report is
[`docs/manifold/results.md`](docs/manifold/results.md), and the generation AI is
written up in [`docs/manifold/ai-note.md`](docs/manifold/ai-note.md). Committed
result artifacts live under `manifold/content/eval/results/`. They cover the Rust
change; the three ranged scores + give-up rule; the leakage screen (5,973 served
items clean against all five held-out ETS forms); the AI card check and the
keyword/vector-search baseline; prompt-injection resistance (0 corrupted answers,
0 hint leaks); the interleaving study-feature ablation; memory-model calibration;
and the paraphrase test. Two-way sync is demonstrated desktop-to-desktop through the
self-hosted sync server, transcript at
[`docs/manifold/sync-demo.log`](docs/manifold/sync-demo.log). Where an honest
measurement needs data a one-week build cannot gather (longitudinal student
reviews), or a live-API artifact needs a valid key the current `.env` lacks, the
deliverable is the harness plus an explicit limitation, never a fabricated number.
The phone companion is partial: the shared Rust engine cross-compiles for Android,
but a full APK plus on-device sync is not delivered — see
[`docs/manifold/mobile-status.md`](docs/manifold/mobile-status.md).

## License and attribution

Manifold is a fork of Anki by Ankitects Pty Ltd and contributors, and it keeps
Anki's license: AGPL-3.0-or-later. The repository [`LICENSE`](./LICENSE) is
Anki's own license notice, left unchanged; some Anki components are BSD-3-Clause
(see [`CONTRIBUTORS`](./CONTRIBUTORS)). Manifold reuses Anki's engine, build
system, and sync protocol, and credits the Anki project. The upstream Anki README
follows below.

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
