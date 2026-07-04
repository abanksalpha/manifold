# Manifold — results & evidence report

Every number here is measured by a re-runnable script over real content; nothing is
fabricated. Where the honest measurement needs data a one-week build cannot gather
(longitudinal student reviews, real practice-test scores), the deliverable is the
harness + methodology + an explicit limitation, per ASSIGN §9 ("we grade the steps of
the bridge, not a made-up final number"). Exam: **GRE Mathematics Subject Test** (scaled
200–990).

Reproduce (from the repo root):

```
set -a && source .env && set +a   # OPENAI_API_KEY, for the generation-based checks
V=manifold/content/generation/.venv/bin/python
$V manifold/content/generation/leakage_check.py --bank manifold/content/generation/teach_bank.json --reference manifold/content/eval/heldout --self
$V manifold/content/eval/ai_card_check.py --count 30 --drafts-per-skill 2
PYTHONPATH=out/pylib out/pyenv/bin/python manifold/experiments/ablation_interleave.py
$V manifold/content/eval/calibration.py
$V manifold/content/eval/paraphrase.py
just bench                        # engine latency on a 50k deck
out/pyenv/bin/python manifold/content/run_e2e_isolated.py   # browser e2e
just check                        # format + build + all unit/integration tests
```

Result JSON is written under `manifold/content/eval/results/` and
`manifold/experiments/`.

---

## 1. Rust engine change (ASSIGN §7a, grading 20%)

A real change inside Anki's Rust engine (`rslib/src/manifold/`): a **mastery-by-topic
query** and a **points-at-stake session queue** with an **interleave** toggle, over the
prerequisite-DAG blueprint. New protobuf (`proto/anki/manifold.proto`), called from
Python (`pylib`) and TypeScript (`@generated/backend`).

- Tests: `rslib/src/manifold/test.rs` (engine unit tests incl. interleave + tier order)
  - a Python round-trip test (`pylib/tests/test_manifold.py`); undo-safety tested
    (read-only RPCs add no undo entry; a graded review undoes byte-for-byte).
- Read-only over FSRS: the scheduler and intervals are untouched (D3); the engine only
  reads FSRS state. Ships to both desktop and (cross-compiled) Android from one source.
- Files touched + merge-difficulty note: `docs/manifold/touched-files.md`,
  `docs/manifold/why-rust.md`. Verified green by `just check` and `just test-rust`.

## 2. Three scores, ranges, give-up rule (ASSIGN §4, §9, grading 20%)

Memory / Performance / Readiness are reported **separately, each as a range**, never one
blended number (`ts/lib/manifold/scoring.ts`; dashboard `ts/routes/manifold/`). Model
cards: `docs/manifold/model-cards.md`.

- **Memory** = FSRS retrievability R per skill (`mastery.rs`).
- **Performance** = correctness on COLD, freshly generated exam-style items (revlog
  `Review`-kind attempts only, D20/D21) — never the practiced card wording.
- **Readiness** = blueprint-weighted performance mapped to an ETS-anchored scaled
  **range**, with the give-up rule: below the evidence line it shows the gate progress +
  the single best next study, never a bare number (honest-by-construction). ETS anchors
  are a cited current table (ETS Guide to Use of Scores; Math 2021–2024).

### 2a. Memory-model calibration (ASSIGN §9 step 1) — `manifold/content/eval/calibration.py`

Data-agnostic calibration harness: reliability diagram + Brier + log loss + ECE/MCE from
`(predicted_R, outcome)` pairs. Plug in the app's real revlog (`--revlog pairs.json`) to
calibrate Manifold's memory model on real data.

- **Honest limit:** a one-week build has no logged longitudinal student reviews, so there
  is no real held-out review set yet. Reported instead: (a) the harness, ready for real
  data; (b) a clearly-labelled FSRS-style forgetting **simulation** — noisy predictor
  ECE ≈ **0.037**, Brier ≈ 0.198; a perfectly-calibrated control ECE ≈ **0.006** (the
  harness detects the difference). This is a harness plausibility check, NOT a
  measurement on real students. Externally, FSRS is calibrated on public
  multi-million-review benchmarks (open-spaced-repetition/srs-benchmark) — cited, not
  re-derived.

## 3. AI checking & safety (ASSIGN §7e, §7f, Friday baseline, grading 15%)

### 3a. Leakage screen (§7e) — CLEAN — `leakage_check.py`

Lexical (shingle/Jaccard/containment, no LLM) screen of the bank's stem+choices against
all **5 real held-out ETS forms** (in gitignored `eval/heldout/`; 2 are scanned image
PDFs, OCR'd to sidecars). The screen now **fails loud** on a no-text PDF (a scanned form
was silently dropped before — a false "clean"; fixed). Result: the **246-item bank is
CLEAN** against all 5 forms + no internal near-duplicates. Leaked test data is an
auto-zero; this proves none.

### 3b. AI card check + simpler-baseline (§7f + the Friday "beat a simpler method") — `ai_card_check.py`

Pre-declared cutoff (fixed before the run): **serve an item only if it passes BOTH
`verify.py` (deterministic SymPy/Z3) AND an independent blind cross-solve.** Ran the real
pipeline on **60 drafts** across 30 sampled live-tier skills:

| outcome                                     | count |
| ------------------------------------------- | ----- |
| correct + useful (verify ✓ + cross-solve ✓) | 18    |
| wrong — caught by verify                    | 8     |
| wrong — caught by cross-solve               | 11    |
| needs curation (no machine-checkable check) | 8     |
| malformed draft (regenerated in prod)       | 15    |

Of 37 well-formed drafts, **19 (51%) were wrong** and every one was caught by the gate.

- **Simpler baseline** = "ship every well-formed generated draft, no checker": would ship
  **19 wrong items (51%)**.
- **Manifold (gated)**: ships **0 wrong** (by construction — the gate rejects all 19).
- This is the "AI beats a simpler method" comparison: verification+cross-solve prevents a
  51% wrong-content rate that naive generation would ship. It also honestly shows raw
  generation quality is mediocre (~49% well-formed drafts correct), which is exactly why
  the verify + cross-solve gate and the session's honest skip-ahead exist.
- Every AI output traces to a named source (the skill's curriculum place, `source_ref`);
  correctness is proven by the LLM-free verifier, never taken on the model's say-so.

## 4. Study feature — interleaving ablation (ASSIGN §8, grading 15%) — `experiments/ablation_interleave.py`

Feature: **interleaving** confusable topics within a session. Hypothesis (declared
ahead): interleaving raises accuracy on new mixed-topic questions at equal study time
(Rohrer 2020 RCT d=0.83; Brunmair & Richter 2019 math g=0.34; see `BRAINLIFT.md`).

Three builds, measured on the real engine queue (topic-switch rate = fraction of adjacent
items from a different topic):

| build                                        | topic-switch rate | mean same-topic run |
| -------------------------------------------- | ----------------- | ------------------- |
| 1. full app (interleave ON)                  | **1.000**         | 1.0                 |
| 2. feature ablated (interleave OFF, blocked) | **0.062**         | 15.7                |
| 3. plain Anki (native order)                 | 0.782             | 1.3                 |

The engine flag demonstrably produces the mixing the hypothesis relies on (ON mixes every
adjacent pair; OFF blocks into ~16-long same-topic runs).

- **Honest limit:** the learning OUTCOME (delayed-test accuracy at equal study time) needs
  real learners studying under each build; not fabricated. Declared primary metric +
  equal-budget protocol are documented in the harness for when learners are available.

## 5. Paraphrase test (ASSIGN §7d) — `manifold/content/eval/paraphrase.py`

Manifold separates memory (FSRS recall) from performance (cold new item), so a performance
item is never the memorized wording. Generation-side measurement over the bank's multiple
verified items per skill (real paraphrases): **36 skills, 96 paraphrase pairs**, mean
pairwise lexical similarity **0.099** (low = genuinely reworded, not the same card twice),
**100%** of pairs below the distinctness threshold, and every item verify-passed +
cross-solved (the idea survives rewording with a correct, checkable answer).

- **Honest limit:** the learner-side number 7d ultimately wants — a student's recall on a
  card vs accuracy on reworded items, and the gap — needs real per-student data. Manifold
  logs both channels (memory = FSRS R; performance = cold Review-kind correctness), so the
  pipeline exists; the gap awaits real learners.

## 6. Coverage map (§7c), benchmark (§7h), crash/offline (§7g)

- **Coverage (§7c):** the dashboard shows percent of blueprint topics covered; below the
  give-up line the app abstains from a readiness number.
- **Benchmark (§7h):** `just bench` (`manifold/bench/bench_mastery.py`) measures real
  engine RPC latency on a **50,000-card** deck (30 runs, this machine):
  `get_topic_graph` **p50 355 / p95 360 / worst 361 ms** (within the dashboard-load < 1 s
  and refresh < 500 ms budgets); `build_session_queue` **p50 423 / p95 444 / worst 488 ms**
  — this is the once-per-session planner (built at session start), and the per-card advance
  after grading walks the built list client-side in O(1), so the < 100 ms next-card target
  is met there. Peak RSS **173 MiB** on 50k. Actions not honestly measurable headless
  (button ack, sync, cold start, paint) are listed by the script, not invented.
- **Crash/offline (§7g):** `manifold/tests/crash_loop.py` — 20/20 SIGKILL mid-review, 0
  corrupted collections. `manifold/tests/offline.py` — with the network + `OPENAI_API_KEY`
  blocked, the readiness/memory/coverage scores still compute (AI-off scoring is
  deterministic) and live problem generation degrades to an honest abstain.

## 7. Desktop + phone, one engine, sync (ASSIGN §3, §7b, grading 10%) — PARTIAL, honest

- **Desktop:** complete — forked Anki builds from source, the Manifold engine change is
  live, the session player + dashboard run, an installer is produced (`just check` green;
  browser e2e green).
- **Shared engine → Android:** the make-or-break part works — `rslib` (carrying the
  Manifold change) cross-compiles for `aarch64-linux-android` (the Rust target and
  `cargo-ndk` are installed; the overnight run produced a real ARM64 artifact).
- **NOT done (honest):** a full phone APK + verified two-way sync (§7b) is not delivered.
  It needs an Android NDK (not present in this environment), an AnkiDroid checkout + Java/
  Gradle, and a device/emulator to verify sync — none available here. Exact finish path:
  `docs/manifold/mobile-status.md`, `docs/manifold/sync.md`.
- **Grade impact (stated plainly):** ASSIGN's hard limit "no phone companion that shares
  the engine and syncs: 70% maximum" applies until the APK + sync are finished. The
  desktop is the shippable artifact today.

## 8. What we do NOT claim (honesty ledger)

- No calibrated readiness on real students (no longitudinal data) — harness + FSRS
  external calibration + honest simulation only.
- No interleaving learning-OUTCOME result (no learners) — mechanism measured, outcome
  experiment designed.
- No per-question scoring against the real ETS forms — their PDF math extracts garbled
  (`(A) 9 2` for −9/2), so the forms serve the leakage screen (clean), not question-level
  performance scoring; the held-out forms are **never served**, only used for leakage.
- No phone APK / two-way sync (toolchain unavailable) — 70% cap acknowledged.
- Readiness is never shown as a bare number; a thinly-evidenced reading renders greyer and
  a withheld one abstains (auto-fail avoided by construction).
