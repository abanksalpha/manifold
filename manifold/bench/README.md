# Manifold engine benchmark

`bench_mastery.py` measures the latency of the Manifold engine RPCs on a deck the
size of the shared 50,000-card reference deck, and labels each number with the
speed target it proxies from the assignment (ASSIGN.md section 10). It builds the
collection by scaling the authored seed skills, gives a realistic fraction of
cards an FSRS memory state (and a smaller fraction a due-review state), then times
each RPC across many runs and prints p50, p95, and worst case.

Two actions are backed by a real engine RPC today, so both are measured:

- **`get_topic_graph`** is the single query behind the readiness dashboard (see
  [`../../docs/manifold/why-rust.md`](../../docs/manifold/why-rust.md)). It
  proxies **dashboard first load** (target p95 < 1 s) and **dashboard refresh**
  (target p95 < 500 ms).
- **`build_session_queue`** is the read-only planner that picks and orders the
  next skill cards to serve. It proxies **next card after grading** (target p95 <
  100 ms).

The script also reports peak process RSS on the deck (section 10: memory use on
50,000 cards) and lists the section 10 actions it cannot measure honestly from
the engine layer in a headless run (button-press ack, sync, cold start,
per-frame paint), with the reason for each, rather than inventing a number.

## Run

From the repo root, after a build (so the built pylib and rsbridge are
importable), either use the one-command recipe:

```bash
just bench
```

or run it directly, the same way the seed importer/verifier run:

```bash
PYTHONPATH=out/pylib out/pyenv/bin/python manifold/bench/bench_mastery.py
```

Flags (all optional): `--cards` (default 50000), `--runs` (default 50),
`--warmup` (default 3), `--studied-fraction` (default 0.8), `--due-fraction`
(default 0.02, must be <= `--studied-fraction`), `--seed` (default 1234). Run
with `--help` for details. `just bench` forwards any extra arguments, for example
`just bench --runs 100`.

## What it prints

The script reports the build (card count, how many carry an FSRS state, how many
are due), a sanity line confirming both RPCs see the deck, then the per-action
timing, memory, and the honest coverage notes:

```
Engine RPC latency over 50 runs each on 50000 cards (section 10 actions, p50/p95/worst):
  get_topic_graph
    p50   :   328.52 ms
    p95   :   361.97 ms
    worst :   414.77 ms
    (best :   315.10 ms)
    proxies dashboard first load: target p95 < 1000 ms, engine p95 361.97 ms (within the engine-layer budget)
    proxies dashboard refresh: target p95 < 500 ms, engine p95 361.97 ms (within the engine-layer budget)
  build_session_queue
    p50   :   ...
```

Those figures are illustrative and vary by hardware. The comparison against each
target is the engine-layer contribution only: the full end-to-end action also
includes the web/IPC round trip and rendering, which this script does not measure
and does not claim. Every timing is measured from the real backend RPC over an
on-disk collection, never synthesized.
