# Manifold engine benchmark

`bench_mastery.py` measures the latency of the `get_topic_graph` engine RPC, the
single query behind the readiness dashboard (see
[`../../docs/manifold/why-rust.md`](../../docs/manifold/why-rust.md)). It builds a
collection the size of the shared 50,000-card reference deck by scaling the
authored seed skills, gives a realistic fraction of cards an FSRS memory state so
the per-card retrievability rollup is exercised, then times the RPC across many
runs and prints p50, p95, and worst-case latency.

## Run

From the repo root, after a build (so the built pylib and rsbridge are
importable), the same way the seed importer/verifier run:

```bash
PYTHONPATH=out/pylib out/pyenv/bin/python manifold/bench/bench_mastery.py
```

Flags (all optional): `--cards` (default 50000), `--runs` (default 50),
`--warmup` (default 3), `--studied-fraction` (default 0.8), `--seed`
(default 1234). Run with `--help` for details.

## What it prints

The script reports the build (card count and how many carry an FSRS state), a
sanity line confirming the RPC sees the deck, then the timing:

```
get_topic_graph latency over 50 runs on 50000 cards:
  p50   :   328.52 ms
  p95   :   361.97 ms
  worst :   414.77 ms
```

Those figures are from one representative run on the development machine and will
vary by hardware; the point is that the rollup over 50,000 cards stays inside the
dashboard's sub-second first-load budget. The numbers are measured from the real
backend RPC over an on-disk collection, never synthesized.
