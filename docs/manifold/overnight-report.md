# Overnight build report

Autonomous execution of `plan-buildout.md` (D26–D43) via the `oneshot` method:
parallel self-verifying subagents, per-phase, integrate + verify between phases.
Owner asleep (D35): never ask; decide + log; blockers are logged-loudly +
quarantined + skipped, never faked, never halted-on.

## Run config

- **Started:** Thu Jul 2, 2026, ~01:10 CT.
- **Model policy (D34 + owner override):** grunt/easy → `glm-5.2-max` (or auto);
  everything else / important coding → `claude-opus-4-8-thinking-max-fast`; ties → Opus.
- **Skills propagated to subagents:** `align`, `ui`, `impeccable` (UI phases),
  plus the plan's rules (no fabrication / no fallbacks / fail loudly).
- **Environment:** git `main`; `just` 1.55.1; node v25.8; python 3.14; `out/pyenv` present.

## BLOCKERS (loud — per D35: quarantined + skipped, not faked)

1. **`OPENAI_API_KEY` unset, no `.env`.** LLM content **generation** is blocked, and
   with it everything that needs the item bank (WS2 real grading, WS3 lectures, WS4
   eval, WS5 ablation data, WS6 paraphrase/calibration). **Action:** build the full
   pipeline ready-to-run; do all non-generation work now; author a modest
   _SymPy-verified_ seed bank so the loop is demonstrable AI-off; full generation
   runs the moment a rotated key lands in `.env`. **No fabricated bank.**
2. **Practice-test PDFs absent** (purged from Trash). Gold set (7f) + leakage (7e)
   are blocked until re-provided to `manifold/content/eval/heldout/`. Pipeline +
   scripts built ready; no fabricated gold set.

## Phase plan

- **P1 (now, parallel):** Anki build green · `verify.py`+`smt_check.py` · `parse_patterns.py` · repo hygiene.
- **P2:** content pipeline (generate→verify→bank) + lectures — _generation gated on key_; seed bank + full plumbing regardless.
- **P3:** WS2 wire bank + real grading + KaTeX everywhere + correct/incorrect animations.
- **P4 (parallel):** WS3 slides · WS5 interleave flag + ablation · WS6 scoring/readiness · WS8 crash/offline/bench.
- **P5:** WS4 eval (gated) · WS9 packaging (real app, no terminal) · WS10 deliverables (BRAINLIFT full sources).
- **P6 (last):** WS7 mobile + sync; integrate → `verify.sh` → code review.

## Log

- **P1 dispatched** (same-tree; files disjoint): A build [Opus], B verify.py+smt [Opus],
  C parse_patterns [GLM], D hygiene [GLM]. Evidence appended as each reports back.
- **P1-A build: GREEN ✅** (day-one risk cleared). `cargo check` + `just test-rust`
  (16/16 manifold engine tests) + `just test-py` (2/2) + `just lint` (clippy/mypy/
  ruff/eslint/svelte-check: 0 errors) all exit 0. No files changed. Env note: `rg`
  not installed (used grep) — not a blocker.
- **P1-D hygiene: DONE ✅.** `.gitignore` `# Manifold` block (`.env`, `*.env`,
  `heldout/`, `rejects.jsonl`, `*.pyc`); `.env.example` (empty key); dirs
  (`generation/`, `eval/heldout/`, `experiments/`, `tests/`) + heldout README;
  `git check-ignore .env` confirms `.env` ignored, no secret created. B (verify.py)
  - C (parse_patterns) still running.
- **P1-B verify.py: GREEN ✅ (keystone).** SymPy symbolic∧numeric gate + Z3
  (`smt_check.py`) + 28/28 pytest fixtures (accept-correct / reject-wrong /
  reject-two-correct / reject-undecidable / malformed / eigen / det / count / …).
  Deterministic, undecidable→reject, deps in gitignored `.venv`. C still running.
- **Pulled forward (non-gated throughput):** dispatched an engine subagent [Opus]
  owning `rslib/src/manifold/*` + `proto` + `blueprint.json` for **WS5 interleave
  backend flag** + **D27 tier re-cut** (both independent of content + the key).
- **P1-C parse_patterns: errored `resource_exhausted`** (GLM rate/resource, not a
  code failure) → **re-dispatched on `auto`** (grunt alt per owner routing).
- **P1-C retry: DONE ✅** — 519 pattern records (matches catalog README) → 335 KB
  `patterns.json`, full schema, unique ids/source_refs, zero nulls. **Phase 1 COMPLETE.**
- **P2 wave dispatched** (disjoint, non-gated, parallel with the engine change):
  P2a pipeline code [Opus] (`generate/build_bank/leakage/quality/crosscheck/import`,
  consumes patterns.json + verify.py; generation-RUN key-gated → fails loud, proves
  verify→bank on fixtures); P2b packaging rebrand [auto] (Briefcase Anki→Manifold,
  config only); P2c BRAINLIFT rewrite [Opus] (D30/D43 + full source library);
  P2d bench+reliability [Opus] (WS8: §10 bench + `just bench` + crash/offline).
  **Deferred:** WS6 scoring/readiness (owns `scoring.ts` + blueprint `readiness_mapping`)
  waits until the engine subagent releases `blueprint.json` (avoids collision).
- **Engine: DONE ✅.** WS5 = new `SessionQueueRequest{optional bool interleave=1}`
  (default-on, preserves the `{}` TS caller), threaded service.rs→session.rs
  (interleaved vs blocked-by-topic; points-at-stake + tier order intact). D27 tiers
  promoted. `just test-rust` + `just test-py` exit 0; new interleave tests + pylib
  RPC test added. Files: proto, service.rs, session.rs, blueprint.json, test.rs,
  test_manifold.py.
- **INTEGRATION TODO (for P6):** `just check` is red only on non-owned items — run
  a `just fmt` pass for pre-existing-unformatted `mastery.rs`/`blueprint.rs` (red at
  HEAD), format `manifold/content/**` generated code, and ensure `.venv`/generated
  artifacts are excluded from minilints/prettier. Not blocking; clean at integrate.
- **WS6 scoring dispatched** [Opus] (blueprint released): non-gated readiness
  upgrades (D29 target selector / log hours-to-target / residue ceiling / 7 display
  fields / lapse→confidence) + `readiness_mapping` in blueprint + `ScoringConfig`
  proto + spec §5.1 (D26). Calibration + paraphrase deferred (need real attempt data).
- **P2b packaging: DONE ✅.** Briefcase rebrand Anki→Manifold in
  `qt/installer/app/pyproject.toml` (project/formal name, bundle `com.manifold`,
  plain description); TOML parses; single-file diff. **Icon TODO (owner):** no
  Manifold icon asset exists — left on Anki's with a TODO (no fabricated binary);
  supply an icon for the final branded build. P2a/P2c/P2d/WS6 still running.
- **P2c BRAINLIFT: DONE ✅.** Evolved SPOV (maturity = drillable recognition
  library; recognition not authorship; exceptional tail ~98% drillable + named
  residue) + target ladder + honest ceiling; **44 sources** (year/venue/effect
  size/evidence-tier) woven into the DOK tree; `ui` scan clean (0 em dashes /
  marketing); no fabricated citations (judgment calls flagged). P2a/P2d/WS6 running.
- **P2a pipeline: DONE ✅.** 7 files; deterministic verify→bank path works (3
  hand-solved seed items banked w/ passing `verifier_report`; wrong/malformed
  rejected loudly); `generate.ts`/`crosscheck.ts`/`quality_judge.ts` fail loudly on
  missing key (no fabrication); `leakage_check.py` blocks loudly on absent PDFs;
  `import_bank.py` loads verified items as synced tagged notes. A **3-item verified
  `item_bank.json`** exists → unblocks WS2.
- **P3/WS2 dispatched** [Opus, align+ui+impeccable]: session player reads the
  verified bank, real grading via `correct_index`, KaTeX everywhere, correct/
  incorrect animations (`Confetti.svelte`) + explanation reveal; skills w/o a
  verified item show an honest "content pending" state (NO fake gradeable
  placeholder). Disjoint from WS6 (scoring.ts) + P2d (bench).
- **WS6 scoring: DONE ✅.** Target selector (median 680 / strong 800 / exceptional
  860) + logarithmic hours-to-target + residue ceiling (caps projections at 955) +
  lapse→confidence + `lastUpdated`; 7 honest fields, never a bare number; constants
  ride blueprint→`ScoringConfig` proto (single source). **`ets_anchors` replaced with
  a CITED current table** (ETS Guide to Use of Scores 2025; Math 2021–2024,
  n=5,180, mean 680, SD 161) — anchor bug resolved honestly (ripple: median→690).
  spec §5.1 fixed (D26). `check:svelte` clean, `vitest` 21/21 (suite 35/35),
  `just test-rust` 553/553, `cargo check --features native-tls` green. Isolated bare
  `cargo check` shows a tokio feature-unification artifact in unrelated stock files
  (green under real features/test build) — integration-safe.
- **WS10 docs dispatched** [auto]: README (exam-at-top + both-app build +
  architecture + Anki credit), LICENSE (AGPL-3.0), model-cards (memory/performance/
  readiness + give-up), extend why-rust/touched-files. Disjoint from WS2 + P2d.
- **P2d bench + reliability: DONE ✅.** `just bench` (50k): `get_topic_graph` p50
  355 / p95 418 / worst 475 ms (within dashboard budgets); `build_session_queue`
  p50 436 / p95 498 / worst 577 ms. Peak RSS 189 MiB. `crash_loop.py` PASS (20/20
  SIGKILL mid-write, 0 corruption, ~28.6k reviews). `offline.py` PASS (Memory/
  Performance/Coverage produced with network + `OPENAI_API_KEY` blocked). 4 §10
  actions (button/sync/cold-start/paint) not headless-measurable → listed, not faked.
- **PERF LEAD (integration TODO):** `build_session_queue` ~500ms p95 on 50k is the
  once-per-session planner (per-card advance is client O(1)); worth an engine
  optimization pass.
- **INTEGRATION BUG:** D27 tier re-cut (`blueprint.json`) mismatches
  `seed_deck.json` per-skill `tier` tags → `import_seed()` fails. **Fix dispatched
  [auto]** — reconcile (prefer deriving tier from blueprint = single source). WS2 +
  WS10 still running.
- **Tier-mismatch fix: DONE ✅** — 85 skills re-tagged recognize→teach in
  `seed_deck.json` (drift-guard + bench's tier consumer kept intact; blueprint =
  source of truth). `import_seed` 519 notes exit 0; `verify_seed` PASS.
- **WS10 docs: DONE ✅** — README (exam-first, both-app build, architecture, Rust
  section, Anki credit), LICENSE verified AGPL-3.0, `model-cards.md` (3 scores +
  give-up, numbers from code), why-rust/touched-files extended; `ui` scan clean.
- **P3/WS2 session player: DONE ✅** — bank-backed real problems, grading by
  `correct_index` (placeholder gone), honest content-pending for uncovered skills
  (no fake grading), typeset math, D38 confetti/quiet-cue + solution+distractor
  reveal, New-skill prequestion→worked-solution→cold. `check:typescript/svelte/
  eslint` pass, vitest 96/96, session e2e PASS, `ui` scan clean. Uses the repo's
  **MathJax** seam (repo standard; `ui` allows "or equivalent") — accepted.
  Pre-existing `manifold.test.ts` strict-mode selector (4× "not yet measured") →
  folded into the dashboard-UI task.

### Phases 1–3 COMPLETE (all non-gated core landed). Remaining:

- **Dashboard readiness UI dispatched** [Opus, align+ui+impeccable]: render WS6's
  target selector + 7 honest fields + residue ceiling on `/manifold`; fix the
  `manifold.test.ts` strict-mode selector.
- **Then:** final integration pass — `just fmt` (pre-existing-unformatted
  `mastery.rs`/`blueprint.rs` + `content/**`), exclude `.venv`/generated from lints,
  `verify.sh`/`just check` green, code-review gate.
- **GATED (owner action):** content generation at scale (needs `OPENAI_API_KEY` in
  `.env`); gold set + leakage eval (needs practice PDFs in `heldout/`).
- **LAST:** WS7 mobile + sync (D31).

## Integration

- **Dashboard readiness UI: DONE ✅** — honest instrument panel: abstain state
  (give-up gate progress bars + study-next, no number) below the line; projected
  range+point + ETS gauge (residue zone hatched) + median/strong/exceptional target
  selector + log hours-to-target + drivers + confidence + last-updated above.
  MathJax typeset. Strict-mode e2e fixed (scoped to the Performance card).
  `check:typescript/svelte/eslint` pass, `ui` scan clean, `ALL MANIFOLD E2E SPECS
  PASSED`. (Dashboard edits need `just build` to show in the compiled bundle.)
- **All non-gated feature work COMPLETE.** Integration pass dispatched [Opus]:
  `just fix-fmt` + `just fix-lint`, exclude `.venv`/generated artifacts from
  minilints/prettier/dprint, `just build` (compile bundle), `just check` + full e2e
  to green (honest reds documented, not faked); then a code-review gate.
- **INTEGRATION: GREEN ✅.** `just check` exit 0 (clippy/cargo-test/dprint/clang-
  format/eslint/prettier/svelte-check/vitest/mypy/ruff/pytest/minilints/complexipy/
  cargo-format all pass); all 3 Manifold e2e specs PASS. Fixed a real rebrand bug
  (installer bundle path `Anki.app`→`Manifold.app`); excluded `.venv`/generated from
  dprint+minilints; formatted pre-existing-unformatted `mastery.rs`/`blueprint.rs`;
  added a copyright header. `verify.sh` conflicts with the repo `just` toolchain
  (system python/yarn, would scan `.venv`) → deferred to `just check` (authoritative).
  No logic changed to force green.
- **Code-review gate dispatched** [Opus, readonly] against the plan (D26–D43) +
  ASSIGN ACs + no-fabrication rules. **WS7 mobile spike dispatched** [Opus]: assess
  Android toolchain, attempt rslib cross-compile, document the AnkiDroid + sync path;
  report blockers loudly, **no faked phone build** (D31 fallback = ship the green
  ≤70% desktop).
- **Code-review gate: DONE ✅.** **No honesty MUST-FIX** — gates fail loud, grading
  by `correct_index`, readiness never bare, no committed secrets, `verify.py` sound,
  engine read-only/cold-evidence. **1 MUST-FIX:** `session.ts` imports
  gitignored+untracked `item_bank.json` → clean clone can't build. SHOULD-FIX:
  README says KaTeX (ships MathJax); no explicit undo test (7a); choice-button aria
  hides content. NITs: `ets_anchors` inline citation; 3-item bank vs ≥1200 AC
  (gated); answered-before-grade tally.
- **Review-fixes dispatched** [Opus]: un-ignore + stage `item_bank.json`
  (clean-clone build), README KaTeX→MathJax, choice content in aria name,
  `ets_anchors` `source`, explicit undo-safety Rust test (7a); re-verify `just check`
  - e2e. Mobile spike still running.
- **WS7 mobile spike: DONE (honest) ⚠️.** The make-or-break part **SUCCEEDED**:
  the shared `rslib` (carrying the Manifold change) cross-compiles for
  `aarch64-linux-android` (NDK r29 + cargo-ndk + target present; artifact
  `target/aarch64-linux-android/debug/libanki.rlib`, real ARM64; the `tokio io-util`
  error is a desktop-identical feature quirk, `--features tokio/io-util` fixes it,
  no files edited). **Blocked:** no Java runtime + no AnkiDroid app/JNI bridge in
  the repo → no `.so`/APK, and the 7b sync test was **not run and is not claimed**.
  `docs/manifold/mobile-status.md` has the toolchain table + exact finish path.
  **D31 fallback stands: ship the green ≤70% desktop build.** No fake APK/sync/pass.
- **Review-fixes: DONE ✅.** All 6 applied; `just check` exit 0; Manifold e2e PASS
  via `run_e2e_isolated.py`; `item_bank.json` now tracked (staged, not committed).
  MUST-FIX (clean-clone bank) resolved; README→MathJax; a11y choice aria + plain-text
  math; **7a undo tests added** (read-only RPCs add no undo entry; graded review
  undoes byte-for-byte); `ets_anchors` citation; answered-tally fix.
- **KNOWN RESIDUAL (documented, not blocking):** stock `just test-e2e` launcher
  seeds only prefs (not the GRE deck), so the session spec looks empty there;
  Manifold e2e runs green via `manifold/content/run_e2e_isolated.py`. Morning option:
  make the e2e launcher seed the deck.

## FINAL STATUS (morning)

- **Desktop build: COMPLETE · GREEN · REVIEWED.** `just check` exit 0; all Manifold
  e2e pass (isolated seeder); honesty verified end-to-end (no fabrication; gates
  fail loud; readiness never a bare number; no committed secrets; `verify.py` sound;
  engine read-only + cold-evidence + undo-tested). **No `git commit` was made** —
  changes are staged/on-disk for your review.
- **GATED on you (2 actions):** (1) rotate + drop `OPENAI_API_KEY` into `.env` → run
  content generation at scale (pipeline ready; today = a 3-item verified seed bank);
  (2) re-provide practice PDFs to `manifold/content/eval/heldout/` → gold set (7f) +
  leakage (7e). Both fail loud until then; nothing faked.
- **Mobile:** the shared `rslib` cross-compiles for Android (the make-or-break
  part); a full APK + two-way sync needs Java + an AnkiDroid checkout — exact steps
  in `mobile-status.md`. Per D31 the shippable artifact tonight is the desktop app.

## Morning follow-up (owner running the pipeline)

- `.env` created + key loaded. Sanity gen (`--limit 20` → 60 drafts): build_bank
  verified 29/60; rejects = pipeline_error 11 (generator bug), undecidable 16,
  no_correct 2, multiple_correct 1, wrong_answer 1. Verifier working (bad answers
  caught, nothing faked); the sanity run did its job — found a fixable generator bug
  before the full run.
- **Generator fix + full run dispatched** [Opus]: fix `generate.ts` to emit only
  `verify.py`-supported, locally-validated `check` blocks (kill pipeline_error) and
  route conceptual patterns to smt/curated (cut undecidable); confirm on the
  20-sample (pipeline_error=0, higher yield), then the full run (519×3) + build_bank
  → full `item_bank.json`; then `just build` + `just run`.
- **REVERSAL — owner directive (D44): on-the-fly generation, NO item bank.** Runtime
  pivots to live generate → SymPy-verify → serve + in-memory prefetch + honest
  abstain (offline/no-key/verify-fail). `verify.py` stays in the loop (no
  fabrication). The generated bank is **deprecated as the runtime source**
  (`generate.ts` + `verify.py` reused for the live path; `build_bank.py` stays a
  dev/eval tool only). **Lectures stay pre-authored** (the exception). Drops AC23
  (AI-off) + the <100ms first-serve target — the owner's explicit, repeated call.
  Pivot dispatched [Opus]: `serve_live.py` + mediasrv endpoint + `session.ts` rewire
  - un-track bank + e2e test double.
- **Generator fix + full run: DONE ✅ (bank now dev/eval-only per D44).** Fixed
  `generate.ts` (pipeline_error 11→0; undecidables cut) + added
  `validate_candidates.py` (local trusted-verify gate → `needs_curation.jsonl`). Full
  1557-draft run banked **927 verified** across 32/33 topics (only `metric_topology`
  = 0, proof-heavy → honestly curated, not faked); rejects honest (undecidable 286,
  no_correct 49, multiple_correct 28, wrong_answer 21, near_dup 2; pipeline_error 0).
  **Under D44 the bank is not the runtime source**, but the prompt/DSL fix **carries
  into the on-the-fly path** (`serve_live` reuses generate.ts) → better live yield,
  still verified. **QUALITY LEAD:** generations lean on stated-value `numeric`/`equiv`
  checks vs recomputed `det`/`rank`/`eigen`; nudge the (now live) generator toward
  data-carrying checks for stronger verification.
- **On-the-fly pivot: DONE ✅ (D44 live).** Runtime generates each problem live:
  `serve_live.py` (generate → verify → serve, ~3 retries, then honest ABSTAIN:
  `no_key`/`offline`/`unverified_after_retries`); `manifoldNextProblem` mediasrv
  endpoint (shells to the gen venv, keeps SymPy/Z3 out of the Anki runtime);
  `session.ts` fetches live + prefetches next, **no `item_bank.json` import**;
  abstain is a first-class UI state (Try again / Skip). Bank un-tracked as runtime
  source (dev/eval only). Verified: key → live VERIFIED item; no key → ABSTAIN; all
  3 e2e green via a hermetic fixture double (verify.py still in loop).
  **RUN NOTE:** launch with the key in the env — `set -a && source .env && set +a`
  then `just run` — or the app abstains (by design).

## Reality check + repairs (owner testing the live app)

- **Owner hit constant abstain.** Live probe of 8 skills: **7 verified** (often only
  after burning retries), 1 abstain. Root causes: (a) generator emits malformed
  drafts ("missing stem") that waste retries; (b) over-uses `numeric` checks →
  non-numeric skills (piecewise/domain, trig special angles, conceptual) fail
  `no_correct`/`undecidable`; (c) the session **dead-ends** on a failed skill instead
  of skipping to one that verified. My pivot e2e used a **fixture double**, so I never
  measured real per-skill yield — owned.
- **App-fix dispatched** [Opus]: port generate.ts's fixed prompt/DSL + draft
  validation into `serve_live` (kill wasted retries); bump retries + **stronger live
  model** + better check-type selection (exact `equiv` for radicals/fractions);
  **session skip-ahead** (defer low-yield skills to curation, always serve a verified
  problem, never a dead-end). Verified with a REAL ~15-skill probe (easy + hard),
  not a fixture.
- **Curriculum verify was STUCK** (~1h, no output) → re-dispatched a leaner, bounded
  audit [Opus]. The GLM per-skill lesson pass fires once it lands (~10-concurrent
  waves — the platform cap, not 500 at once).
- **Curriculum audit: DONE ✅ — curriculum is SOUND.** 33 topics cover the ETS
  outline (only "modules" lacks a dedicated skill, rarely tested); weights exactly
  50/25/25. Real issues are INTERNAL bookkeeping: `expected_skills` (147) stale vs
  the deck → mastery `coverage` saturates at 1.0; problem-types README mislabels 3
  tiers (D27); `metric_topology` 0 verified. (`curriculum-audit.md`; fixes queued.)
- **GLM lesson pass LAUNCHED (post-verification):** 10× GLM 5.2 Max at once (max
  concurrency), sharded over all banked skills; each authors a best-possible
  **typeset (LaTeX)** lesson per skill anchored to a verified item (dev/eval bank
  used at author-time). Disjoint outputs `manifold/content/lessons/shard_k.json`;
  session-wiring follows the app-fix. GLM may rate-limit → retry failed shards.
- **CRITICAL — verifier hole (two independent confirmations).** Shard 3 (19/40) and
  shard 6 (12/40) each found that ~30-47% of "verified" bank items have a
  mathematically WRONG marked answer. Root cause, confirmed structurally
  (`verify.py` only checks the stem is non-empty, never solves it) and by the bank
  (`verifier_report.math: null`; degenerate `check.expr` echoing `correct_index`):
  **"verified" = check↔label consistency / structurally-valid MCQ, NOT stem↔answer
  correctness.** The live path uses the same gate → it can serve wrong "verified"
  problems. This violates no-fabrication at the core; owned (verify was built as a
  consistency gate; cross-solve was only planned for the non-computable tail).
  Upside: lesson shards independently re-solve + REFUSE wrong items, so they double
  as a full bank audit — harvest every shard's blocked-list = the regenerate set.
- **FIX (top priority, right after the serve_live yield rework lands):** (1)
  verify/build must **REJECT** `math:null` / degenerate-echo checks, not pass them;
  (2) add an **independent stem-solve gate** (a strong model solves the stem blind →
  must agree with the label); (3) **stronger generation model**; (4) re-verify
  everything so live serve + lessons stand only on truly-correct items. Both shards'
  A/B question → **fix the gate, do NOT author the wrong ones.**
- **Shard 5 completed 40/40 but is CONTAMINATED.** Unlike shards 3/6 it did not
  independently re-solve; it authored lessons anchored to wrong-verified items
  (rendered the item's wrong final value with a "sound method"). So a "complete"
  shard is LESS trustworthy than one that blocked. **ALL lesson shards must be
  re-validated against the fixed math gate** (re-solve each anchor; drop/redo
  wrong-anchored lessons) before any wiring. Nothing shipped yet (lessons are files
  only), so no live harm. (Shard 8 also left stray `_shard8_*.py` helpers to clean.)

## Verifier hole: CONFIRMED at the code level + FIX SHIPPED (runtime)

- **Confirmed by reading `verify.py`, not just the shards.** The mechanism is exact:
  `verify.verify()` proves _check<->choice_ consistency (exactly one choice matches the
  item's own `check`, and it is the claimed one). For the **recompute** check types
  (`det`/`rank`/`eigen`/`count`+brute/`prob_exact`+brute/`antiderivative`/`smt`) ground
  truth is derived from a spec, so a pass is strong. But for the **stated-value** types
  (`numeric`/`equiv`) `check.expr` **is the answer the generator asserts** (the prompt
  literally says "expr is the ANSWER ITSELF"), so the SymPy pass is **tautological
  w.r.t. the stem** — a model that miswrites its own problem passes. The live smoke
  test bore this out: **every** VERIFIED item used `check=numeric`. Multiple shards
  (3/6/8/9) independently re-solved and found ~30-47% stem-wrong. Real hole.
- **FIX SHIPPED — independent blind cross-solve gate (D32 gate 5), now on the runtime
  path.** New `independent_solve.py`: a different/stronger model (`gpt-4o`) solves the
  assembled item **blind** (stem + 5 choices only; no `solution`/`check`/`correct_index`/
  rationales), votes `MANIFOLD_SOLVE_SAMPLES` (default 2) times, and must reach a
  consensus that **matches** `correct_index`. Wired into `serve_live.py` **after**
  `verify.verify()` passes and **before** serve: verified-but-not-cross-solved =>
  rejected, try another; solver unavailable/garbled => honest **abstain**, never a
  silent pass (user rule). Applied to **all** verified items, not just numeric/equiv —
  a real run flagged an `eigen` item too (matrix didn't match its stem), so scoping to
  the tautological types alone would miss cases. `verify.py` stays LLM-free and
  unchanged (its 28 tests still pass); the gate is a separate module, mirroring the
  existing `crosscheck.ts` semantics exactly.
- **Evidence (not assertions).** New `test_independent_solve.py` (17 tests) + existing
  verify suite = **45/45 green** (hermetic, injected/fixture solver). Real-key spot
  check on bank items: `nth_term_divergence_test` (a shard-8 blocker) => solver picked
  a different choice both times => **correctly not served**; a genuine
  characteristic-polynomial / count item => agreed. CLI proof (how mediasrv calls it,
  doubles only, no real key): happy path => `ok` with `independent_solve` recorded
  ("2/2 blind solves agree"); `always_wrong` solver => `abstain`
  (`unverified_after_retries`, detail = independent_solver_disagreed). e2e kept green
  via a `trust_label` solver double (`solve_fixtures.e2e.json`, wired in
  `run_e2e_isolated.py`).
- **Honest consequences.** (1) **Live yield drops** — the earlier "7/8 served" counted
  tautologically-verified (sometimes wrong) items; honest yield < fake yield, by
  design. Cost/latency ~2-3 model calls per served problem (generate + verify +
  solve×2); prefetch hides the latency. (2) The gate reduces but does not _eliminate_
  wrong-serve risk (correlated LLM errors); disagreement is the trustworthy DROP
  signal, and some correct items get dropped (acceptable: lowers yield, never teaches
  wrong math). (3) The strong recompute types remain the rigorous core; cross-solve is
  the independent second opinion that must concur.
- **Bank audit RUNNING (for the lessons, not the runtime).** `crosscheck.ts` over all
  927 `item_bank.json` items (`--samples 2 --model gpt-4o`, ~15 min) => `bank_crosssolve.jsonl`.
  Next: keep only `crosscheck.agreed==true` as the trustworthy **anchor set**, emit the
  disagreed set as the **regenerate list**, then re-validate every lesson shard's anchor
  against it (drop/redo wrong-anchored lessons; shard 5 is contaminated; **shard 4 file
  is missing** — re-run). Bank stays dev/eval + lesson-anchor only (D44: runtime is live).

## Lesson pass COMPLETE (all 10 shards) + cross-shard consensus on the hole

- **All 10 shards done: 317 lessons / 401 verified skills.** Each shard independently
  loaded the bank, took its `i % 10 == k` slice of sorted distinct skills, and authored
  LaTeX lessons anchored to a verified item. Three distinct behaviors emerged when a
  shard hit a "verified" item whose stem/answer don't line up — and the split _is_ the
  audit:
  - **Refused (honest, fewer authored):** 3→21, 9→21, 8→23, 4→23, 6→28. Blocked the
    wrong items (12-19 each), authored only the clean ones.
  - **Corrected-and-taught (authored ~40, overrode the bank):** 0→41, 1→40, 2→40, 7→40.
    For ~8-14 items each they taught a HAND-RECOMPUTED value instead of the bank's wrong
    one (e.g. avg of x^2 on [1,3] = 13/3 not 8/3; total distance of 3t-12 = 48 not 96).
  - **Trusted the bank (CONTAMINATED):** 5→40. Did not re-solve; some lessons teach the
    bank's wrong answer.
- **Consensus: 9 of 10 shards independently found ~30-47% of "verified" items are
  stem-wrong.** Different model (GLM 5.2 Max), different method (re-derive by hand /
  sympy) than my gpt-4o cross-solve, same conclusion. This is overwhelming, independent
  confirmation of the tautological-verifier hole — and validates the cross-solve fix.
- **Consequence — every shard's lessons need re-validation against the cross-solve
  survivor set (`item_bank.verified.json`), not just shard 5:**
  - _Corrected-and-taught_ lessons (0/1/2/7) anchor a DISAGREED item and teach GLM's
    _unverified_ re-derivation — honest of GLM, but still not a verify+cross-solve
    anchor. Re-anchor each to a survivor item (or mark the skill uncovered).
  - _Contaminated_ (5): drop/redo the wrong ones.
  - _Refused_ (3/4/6/8/9): honest but incomplete; author the missing skills from
    survivors where one exists.
    Plan: after the bank audit + filter land, keep lessons whose anchor survived and
    teaches the verified answer; re-author the rest from the survivor set; skills with no
    survivor stay an honest gap until regenerated. (A follow-up GLM pass, seeded from the
    survivor set only.)

## App-fix landed (live yield + session skip-ahead) — verified WITH the gate on top

- **`db94c008` (Fix live yield + session skip-ahead) completed** and its `serve_live.py`
  changes were already on disk when I added the cross-solve gate, so my gate layered
  cleanly on top (confirmed: `independent_solve.check_agreement` at `serve_live.py:884`;
  its `session.ts`/`+page.svelte` skip-ahead are separate files). Its results: real
  15-skill live probe **73%→87% served**, the `det`-with-no-`matrix` **crash fixed**,
  non-served skills are now honest `needs_curation` **defers** not dead-ends, and the
  session **skips past** abstaining skills with a small prefetch buffer + an honest
  "N skills pending content" note (never a wall, never a fake item).
- **Synergy with the gate:** the cross-solve gate rejects more candidates (verified but
  disagreed), which the skip-ahead + honest-defer UI already handles gracefully — so the
  added correctness costs yield/latency, never a dead-end or wrong content. (Latency: the
  gate adds ~1-2 solve calls per verified candidate; `MANIFOLD_SOLVE_SAMPLES` tunes it,
  prefetch hides it, and the mediasrv cap degrades to an honest timeout defer.)
- **Combined verification:** 45/45 venv tests green on the merged `serve_live.py`;
  isolated e2e re-run (key unset, doubles only) **ALL 3 SPECS PASS** — home, dashboard,
  and session (generate→verify→**cross-solve**→serve→grade, plus the honest-abstain
  path). So the merged runtime (gate + skip-ahead + solver double) is green offline.

## OWNER CLARIFICATION (2026-07-02): teach = bank, everything else = on the fly

The owner stopped a full 927-item bank cross-solve mid-run and clarified the true model,
which supersedes the earlier flat "no bank at all" reading of D44:

- **TEACH ("new") skills → a pre-generated, 100%-working bank.** New material must be
  correct and carries the lectures, so those problems are vetted ahead of time: every
  banked item passes BOTH verify.py AND the independent blind cross-solve. Scope: the
  **214 teach-tier skills only**.
- **relearn + recognize → on the fly**, generated live at review (serve_live), never
  banked. "DO NOT generate ANYTHING for any other problems."

**Actions taken:**

1. **Killed** the 927-item bank cross-solve + its filter (wasteful under this model);
   the old all-tier `item_bank.json` is deprecated and will be dropped once teach is up.
   The obsolete `bank_crosssolve.jsonl` / `filter_crosssolve` / `revalidate_lessons`
   artifacts are superseded.
2. **Fixed a generator waste bug:** the model often returns !=4 `distractor_rationales`
   (non-correctness feedback text), which was discarding otherwise-valid items and
   burning the retry budget. Now normalized to 4 (pad honestly / trim); correctness is
   still fully decided by verify + cross-solve. Helps the live app's yield too.
3. **Building the teach bank** (`build_teach_bank.py`, running): 214 teach skills, aim
   > =1 verified+cross-solved item each (coverage-first, resumable, crash-safe append to
   > `teach_bank.items.jsonl`). Some teach skills are inherently conceptual (PDE/Laplace
   > verification, tangent-plane, steepest-ascent) and honestly abstain (`needs_curation`)
   > — those are reported in `teach_bank_gaps.jsonl`, never faked. Budget ~3k calls / ~1h.

## Gate hardening: value-matching (owner caught a broken served item)

Owner hit a live item "evaluate (2*3)+(4^2)-(sqrt(16)/2)" whose true answer is **20**,
which was **not even among the 5 choices** (18/24/19/22/16). Diagnosis + fix:

- **It was a STALE item** — generated before the cross-solve gate landed (~12:00) and
  cached in the session's prefetch buffer from the earlier run. The current gate rejects
  it (reproduced: all 5 label variants -> agreed=False). A session reload pulls
  freshly-gated problems.
- **Real gap found + fixed:** the gate trusted the solver's _chosen_index_, but gpt-4o
  force-picks the nearest option when the true answer is absent. Upgraded
  `independent_solve` so the solver returns its **computed_answer** and we match THAT to
  the choices ourselves (SymPy, loose numeric tol + symbolic equivalence, index
  fallback if unparseable). So "the true answer isn't any choice" is now a decisive
  reject. Added an explicit `-1` "none" answer too. 49/49 tests green (incl. a test that
  the computed value overrides a lazy matching index).
- **Honest limit:** the blind solver is itself an LLM (gpt-4o) and _miscomputes some
  arithmetic_ (it returned 18/22/19 for that stem, not a stable 20). So cross-solve is
  not a perfect oracle. The teach-bank build **rejects** such unstable items rather than
  banking them (bad generations -> gaps, never wrong content), which keeps the bank
  clean. Max rigor for purely computational items would be a deterministic check that
  encodes the _computation_ (not the claimed answer) so verify.py recomputes from the
  stem — noted as a follow-up option.
- **Rebuilt the teach bank from scratch with the upgraded gate** (the prior 63-skill/52-item
  run used the weaker index-only gate; cleared for integrity). First skills confirm 1/1;
  running, will report coverage + gaps.

## LaTeX rendering fix (owner: "typeset everything in latex already")

Owner saw the worked-solution panel showing **raw** LaTeX/Unicode (`\frac{\(sqrt\){16}}{2}`,
`.`/mid-dot, superscript `2`) instead of typeset math, while the stem rendered fine.

- **Root cause (a content/format mismatch, not missing code):** the render pipeline
  (`mathmarkup.ts` -> `MathText.svelte`) expects the **plain ASCII** grammar the bank uses
  (`2*3`, `4^2`, `sqrt(16)`, `1/9`) and converts THAT to LaTeX. The stem, choices, and
  solution all go through it. The stem rendered because it was ASCII; the generator wrote
  the _solution_ and _rationales_ as raw LaTeX + Unicode, which `mathToMarkup` can't
  convert, so `MathText` fell back to showing the source. The generation prompt never
  constrained the format of the stem/solution/rationale text.
- **Fix:** the prompt now requires the stem, solution, and every rationale to use the SAME
  plain ASCII grammar as the choices — no LaTeX commands, no Unicode math glyphs — so
  `mathToMarkup` typesets all of it uniformly. Verified on fresh generations: an
  order-of-operations item and an eigen item both came back CLEAN ASCII (a
  contamination scan for `\frac`/`\sqrt`/`\(`/mid-dot/superscripts/radical found nothing)
  and still verified + cross-solved.
- **Folded into the teach-bank restart** (value-matching gate + ASCII-clean text), so every
  banked solution renders. (The earlier value-gate run's items were cleared since their
  solution text predated this fix.) A session reload serves typeset problems.

## Teach bank BUILT + runtime routing WIRED

- **Bank built: 178/214 teach skills** (178 items), each verify.py-passed AND
  independently cross-solved AND ASCII-clean. **36 conceptual skills are honest gaps**
  (vector_spaces 6, group_theory 6, linear_algebra_core 5, eigen 4, complex_analysis/
  multivariable_diff/differential_equations 3 each, ...) — proof/"which must be true"/
  isomorphism-class skills that cannot be a machine-checkable MCQ. Not faked.
  (`teach_bank.json`; gaps in `teach_bank_gaps.jsonl`.) The concurrency-8 run segfaulted
  in z3-heavy group theory at 139/214; resumed at concurrency 3 to completion.
- **Runtime routing wired in `serve_live.py`:** a teach-tier skill is served from
  `teach_bank.json` (no live call, item already verified+cross-solved); every other tier
  generates on the fly; a teach skill absent from the bank returns an honest
  `content_pending` abstain (the session already skips + shows "N skills pending"). Tests
  and e2e keep the live double (routing is bypassed when fixtures/an injected generator
  are present). Verified: 49/49 unit tests, hermetic routing check (banked -> served from
  bank with no API; unbanked teach -> content_pending), and **all 3 e2e specs PASS**.
- **Owner skipped the gap-handling question** -> proceeding: the 36 conceptual gaps stay
  `content_pending` (honest, not live-generated, not faked) until curated/reclassified.

**Next:** (a) DONE — runtime routing — teach skills serve from `teach_bank.json`,
all other tiers stay on-the-fly; (b) re-anchor the lectures to the teach bank; (c) delete
the old 927 all-tier bank + dead cross-solve artifacts; (d) offer to deepen the teach
bank beyond 1/skill if the owner wants more per-skill variety (more spend).
