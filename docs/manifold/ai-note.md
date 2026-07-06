# AI note: what Manifold built, why, and what it skipped

> Assignment Friday deliverable: "A short note on what AI you built, why, and
> what you skipped," plus "every AI output traces back to a named source." This
> note covers the **generation** side (the LLMs that author and check content).
> The **scoring** models (memory, performance, readiness) are AI-free and are
> documented separately in [`model-cards.md`](model-cards.md).

## The one rule that shapes every choice

**No LLM is ever trusted for correctness.** An AI may propose the _structure_ of a
problem or explain a method in prose, but the _answer a learner is graded against_
is always produced or confirmed by code, never taken on a model's say-so. This is
why a wrong model, a hallucination, or a prompt injection cannot put a wrong
answer in front of a learner (see [Safety](#safety-prompt-injection), below).

Concretely, the runtime answer path is AI-free for every computational skill:
`templates.py::instantiate` draws fresh numbers per review and computes the answer
with SymPy (`solver.py`), so the stem and the answer are rendered from the same
parameters and cannot disagree. The LLM only appears off to the side: authoring
templates, checking them, and tutoring, each behind a code gate.

## What AI we built

Five LLM roles, each named, scoped, and gated:

1. **Template author** (`template_author.py`) — offline. Proposes a parametric
   template (params, a stem with `[[slots]]`, a machine-solvable `answer_spec`,
   distractor recipes). It **never supplies an answer**. Every proposal must pass
   `templates.validate` (instantiate N seeds and confirm each shown answer equals a
   fresh SymPy recompute) and `templates.check_faithfulness` (an independent blind
   solver must reach the code-computed answer from the rendered stem) or it is
   rejected. This authored the ~2,900-template bank across ~580 skills.
2. **Live generator** (`serve_live.py::_make_openai_generator`) — the fallback for
   a non-teach skill that has no template yet, and the engine that built the older
   `teach_bank.json`. Writes a draft item; the draft is served only if it passes
   `verify.py` (deterministic SymPy/Z3) **and** the deterministic arithmetic
   stem-check **and** an independent blind cross-solve. Otherwise it retries or
   abstains honestly.
3. **Independent blind cross-solver** (`independent_solve.py`) — a _different_
   model (its own `MANIFOLD_SOLVE_MODEL` knob) that solves a candidate from **only
   the stem and the choices**; it never sees the claimed answer, solution, or
   correct index. Its vote is re-matched to the choices by SymPy value-matching, so
   even its output is not trusted verbatim. This closes the "the check just restates
   the generator's own answer" hole.
4. **Hint tutor** (`hint.py`) — the runtime, student-facing "ask a question"
   affordance. Gives one Socratic nudge toward the method. It is deliberately
   **not** given the correct index or the worked solution, so it cannot leak the
   answer even if its wording slips, and an output guard blocks any hint that names
   a lettered choice (see Safety).
5. **Lecture authors** (`build_lectures.py`, `build_gap_lectures.py`) — offline.
   Author one grounded LaTeX lecture per teach skill: `build_lectures.py` walks
   through a _verified_ banked item; `build_gap_lectures.py` handles the conceptual
   skills the template engine cannot express, grounded in standard mathematics with
   a named, openly-licensed citation. Bodies pass the same display-LaTeX gate the
   problems use.

## Why we built it this way

- **Keep AI out of the answer path.** Raw generation is unreliable: the AI card
  check measured ~51% of well-formed live drafts as _wrong_ (see
  [`results.md`](results.md) §3b). Deterministic templates + a SymPy verifier turn
  that into a correctness guarantee instead of a hope.
- **Two independent judges, not one.** A single model that both writes and confirms
  correlates its own errors. Splitting authoring from an independent blind solver
  (and putting SymPy under both) removes that correlation.
- **Traceability.** Every served item carries a `source_ref` naming its place in
  the GRE-math curriculum taxonomy; every template names its `skill_id`/`topic_id`;
  every gap lecture names an open-licensed reference. No AI output is served
  without a named source and a code-checked answer.
- **Tutoring at scale, honestly.** The hint tutor follows the retrieval-practice
  evidence in [`../../BRAINLIFT.md`](../../BRAINLIFT.md): it nudges toward the
  method and refuses to hand over the result, so it supports recall rather than
  short-circuiting it.

## What we skipped (and why)

- **No model on the graded answer path.** Answers come from SymPy (templates) or a
  code gate (live). With AI switched off, readiness/memory/coverage still compute
  (scoring is fully deterministic) and every templated or banked skill still
  serves; only the few untemplated non-teach skills abstain ("needs AI") instead of
  live-generating. We did not build a static all-tier cache to make those few serve
  offline, and we say so rather than papering over it.
- **No source-text ingestion / RAG.** Templates are authored from the taxonomy, not
  scraped from copyrighted textbooks; gap lectures cite open sources only. This is
  both a copyright decision and a security one: there is no untrusted source corpus
  for an attacker to poison.
- **No multi-turn conversational agent.** The tutor is a single-hint affordance, not
  a chatbot, so there is no long dialogue to steer off course.
- **No auto-expanding corpus.** The bank is authored and reviewed, not grown at
  runtime by the model.

## Safety: prompt injection

The reviewer flagged that prompt-injection resistance was not evidenced. It now is,
in code, tests, and a re-runnable eval ([`results.md`](results.md) §3d,
`manifold/content/eval/results/prompt_injection.json`).

- **Primary defense (architectural).** The answer path is AI-free: a hidden
  instruction in a skill label or a source cannot change a template's answer,
  because the answer is `solver.solve_spec` of the `answer_spec`, recomputed by
  SymPy. For live items, `verify.py` + the arithmetic stem-check + the blind
  cross-solve reject any hijacked-wrong item. Measured: 72 real template attacks →
  **0 corrupted answers**.
- **Secondary defense (prose paths).** `prompt_safety.py` adds `wrap_untrusted`
  (labelled delimiter fences with break-out neutralization), `screen_for_injection`
  (flags control phrases like "ignore previous instructions"), and
  `screen_for_answer_leak` (an output guard on the hint path). The hint tutor now
  fences the student's question, prior turns, and the stem/choices; screens the
  question; and — because it is never given the answer key — turns any answer-leaking
  hint into an honest abstain rather than serving it. Measured: 15 real hint-guard
  invocations (5 with real `gpt-4o-mini` calls) → **0 answer leaks**. The same fencing
  hardens the offline lecture and template authors as defense-in-depth.
- **Live generation under injection.** Section B feeds hidden instructions into the
  live generator's skill name and runs the real verify + blind cross-solve gate:
  6 attempts, 4 verified items served, **0 wrong served** (the gate rejects any
  hijacked-wrong item; exact per-run counts vary with model output).
- **Honest limit.** The output guard is an English-pattern heuristic; the
  architectural answer-path defense (templates + verify), not the prose guard, is
  the guarantee. A maximally oblique numeric hint is not provably caught, so the
  guard hardens rather than replaces the AI-free answer path.

## How the AI is checked (evals)

All re-runnable; artifacts under `manifold/content/eval/results/`. See
[`results.md`](results.md) for the numbers and the exact commands (`just eval`,
`just eval-ai`).

| Check                              | Script                      | What it proves                                                                   |
| ---------------------------------- | --------------------------- | -------------------------------------------------------------------------------- |
| Leakage / copyright                | `leakage_report.py`         | The served content (5,973 items) is clean against all 5 held-out ETS forms       |
| AI card quality + gate             | `ai_card_check.py`          | The verify+cross-solve gate catches the wrong drafts naive generation would ship |
| Beat a simpler method              | `baseline_retrieval.py`     | Verified generation vs keyword (TF-IDF) and vector (embedding) retrieval         |
| Prompt injection                   | `prompt_injection_check.py` | Injected inputs cannot corrupt an answer or exfiltrate one via the tutor         |
| Paraphrase (memory vs performance) | `paraphrase.py`             | Performance items are genuinely reworded, not the memorized card                 |

## Generation model cards

Each card lists the role, the model knob, what text goes into the prompt (and
whether it is trusted), what the model returns, the code gate on that output, and
what the model is deliberately **not** told.

### Template author

- **Role / when.** Propose a parametric template. Offline authoring only.
- **Model.** `MANIFOLD_AUTHOR_MODEL` (OpenAI-compatible).
- **Prompt inputs.** `skill_name`, `topic_id` — server-curated from
  `seed_deck.json` (trusted). No source text.
- **Returns.** Template structure: params, stem, `answer_spec`, distractor recipes.
  **Never an answer.**
- **Gate.** `templates.validate` (SymPy recompute over many seeds) +
  `templates.check_faithfulness` (independent blind solver agreement); else
  rejected. Provenance (`skill_id`/`topic_id`/`tier`) is owned by code, not the model.
- **Not told.** Nothing to withhold — it never sees or sets an answer.

### Live generator

- **Role / when.** Draft an item for an untemplated non-teach skill; build the
  legacy teach bank. Fallback path only.
- **Model.** `OPENAI_MODEL` (default `gpt-4o`).
- **Prompt inputs.** `skill_name`/`skill_id`/`topic_id`/`tier`/`difficulty` —
  server-owned (trusted); no external text.
- **Returns.** A draft (stem, choices, correct choice, solution, machine-checkable
  `check`).
- **Gate.** `verify.verify` (SymPy/Z3) + `_arithmetic_stem_check` +
  `independent_solve.check_agreement`; served only if all agree, else retry/abstain.
- **Not told.** N/A (it writes the draft; correctness is re-derived, not trusted).

### Independent blind cross-solver

- **Role / when.** Second, independent judge of a candidate item (authoring +
  live gate).
- **Model.** `MANIFOLD_SOLVE_MODEL` (default `gpt-4o`), `MANIFOLD_SOLVE_SAMPLES`
  votes.
- **Prompt inputs.** The rendered **stem and choices only**.
- **Returns.** A chosen answer, re-matched to the choices by SymPy value-matching.
- **Gate.** Its vote only counts via the deterministic value match; disagreement
  rejects the item.
- **Not told.** The claimed answer, the worked solution, the correct index, or the
  distractor rationales — so it cannot rubber-stamp the generator.

### Hint tutor

- **Role / when.** One Socratic nudge, at runtime, when a learner asks.
- **Model.** `MANIFOLD_HINT_MODEL` or `OPENAI_MODEL` (default `gpt-4o`).
- **Prompt inputs.** Stem, choices, the student's typed question, prior turns —
  all **untrusted**, now delimiter-fenced via `prompt_safety.wrap_untrusted` and
  screened for injection.
- **Returns.** One method-nudge (LaTeX-typeset), at most three sentences.
- **Gate.** `screen_for_answer_leak` on the output: a hint that reveals the answer
  or a lettered choice becomes an honest abstain, never a served leak. Never a
  canned/fabricated hint.
- **Not told.** The correct index and the worked solution — withheld by
  construction, so a leak cannot originate here.

### Lecture authors

- **Role / when.** One grounded lecture per teach skill. Offline.
- **Model.** `OPENAI_MODEL` (default `gpt-4o`).
- **Prompt inputs.** For `build_lectures.py`: a _verified_ banked item's
  stem/solution/correct answer (fenced). For `build_gap_lectures.py`: the
  `skill_name`/`topic_id` and a hardcoded, openly-licensed citation string (fenced).
- **Returns.** A LaTeX lecture body (method, when-to-use, worked walk-through,
  takeaway).
- **Gate.** The display-LaTeX validator (`serve_live._validate_display_latex`);
  a malformed body regenerates. Anchored to a verified item, never to invented math.
- **Not told.** No withholding needed; it teaches an already-verified item or a
  cited standard result.
