# Plan: per-skill bank buildout (content swarm) + gold-set eval

Status: proposed (awaiting budget go-ahead for the full generation run)
Owner: Manifold
Last updated: 2026-07-03

## Goal

Kill the live (AI-on) runtime hot path. Today `teach` is served from a
pre-vetted bank while `relearn` + `recognize` are generated **live** per review
(slow, and every review is an API round-trip that can abstain). Replace that with
a **deep, pre-vetted bank of 30 verified items per skill across all 519 skills**,
then flip the serve path to bank-first. Runtime becomes instant, correct, and
AI-off. Parametric templates come after, for the high-volume recompute topics.

In parallel (and firewalled), stand up a **real-GRE gold-set eval** that scores
our blind solver against the held-out ETS forms' official answer keys and the
human `P+` baseline — external validity the current `ai_card_check.py` lacks.

## Scale (measured from `seed_deck.json`)

519 skills, 33 topics, 3 tiers. **Tier is a per-topic property** (each topic is
entirely one tier), which fixes each topic's generation strategy.

| tier        | topics | skills | served today                        |
| ----------- | -----: | -----: | ----------------------------------- |
| `teach`     |     13 |    214 | pre-vetted bank (`teach_bank.json`) |
| `relearn`   |     11 |    186 | **live** (to be banked)             |
| `recognize` |      9 |    119 | **live** (to be banked)             |

Buildout gap = the **305 `relearn`+`recognize` skills** on the live path (plus
topping `teach` up from target 3 → 30). Per-topic skill counts range 7–20.

## Decisions (locked with owner)

- **One focused unit of work per skill** (519), dispatched in topic-batched
  waves. See "Delegation model" for worker-vs-agent mechanics.
- **30 vetted items per skill** (`--target 30`).
- **Strong, non-Opus model.** (Owner: "need not use Opus 4.8 but make it good.")
- **Gate unchanged:** an item is banked only if it passes `verify.py`
  (SymPy/Z3/brute, no LLM) AND the deterministic arithmetic re-check AND the
  blind cross-solve (`independent_solve.py`). Same gate `ai_card_check.py` measures.
- **Sequencing:** validate the solver on the gold set → pilot wave → full waves
  → templates.
- **Held-out firewall:** generation never sees the 5 ETS forms (auto-zero risk).

## What already exists (reuse, don't reinvent)

- `serve_live.py` — `next_problem(skill)`: generate (`OPENAI_MODEL`) → `verify` →
  arithmetic re-check → blind cross-solve (`gpt-4o`) → serve iff all agree. The
  per-item vetting loop, already parallel-candidate aware.
- `build_teach_bank.py` — per-skill, **resumable** (append-only jsonl),
  concurrent, coverage-first builder that drives `next_problem` to a target and
  records gaps. **This is the harness template**; it is currently teach-only,
  target 3.
- `verify.py`, `independent_solve.py`, `leakage_check.py`, `build_bank.py`,
  `import_bank.py` — correctness, cross-solve, leakage/near-dup, deterministic
  bank assembly, and import into the collection.

## Architecture: the per-skill swarm harness

New `build_skill_bank.py`, a generalization of `build_teach_bank.py`:

- **Unit of work = one skill.** Each skill has an independent generation loop,
  its own quota (30), and its own gap record — the literal "focused per skill".
- **Selection:** `--tiers`, `--topics`, `--skill`, `--limit` (default: all tiers,
  or `relearn,recognize` to fill only the gap).
- **Resumable:** append each confirmed item to a shard jsonl; a re-run loads it
  and only tops up skills below target. Crash-safe.
- **Disjoint outputs (swarm independence):** items written to **per-topic shard
  files** so parallel waves/agents never write the same file. Aggregated at the
  end into `item_bank.json`.
- **Budget caps:** `--max-calls-per-skill` (exists) **plus** a new global
  `--max-total-calls` ceiling so a wave cannot overspend. `--dry-run` prints the
  work plan (skills × remaining quota, est. calls/cost) with **no** API spend.
- **Concurrency:** `ThreadPoolExecutor` across skills within a wave; waves are
  topic-batched.
- **Aggregate + final sweep:** merge shards → run `leakage_check` (reference +
  self near-dup) → write the bank → coverage report.
- **Flip to bank-first:** extend `serve_live` routing so `relearn`/`recognize`
  serve from the bank when present, else keep the honest live/abstain path.

## Delegation model: "one subagent per skill"

Two mechanisms, very different cost. Both keep one focused unit per skill.

1. **Harness worker per skill (recommended default).** The strong model is the
   OpenAI **generator** inside the pipeline (bump `OPENAI_MODEL` to a good model
   for the build). Each skill is an independent worker in the swarm. Cheapest,
   deterministic, fully verifiable, reuses the proven pipeline.
2. **Cursor Task agent per skill.** A literal LLM subagent (Sonnet/GPT-5-class,
   non-Opus) per skill. Adds agent-reasoning cost on top of the generation cost
   and is 519× orchestration. Its extra value is real only where per-skill
   _curation_ helps (low-yield proof-y `recognize` skills). **Recommend reserving
   this for the low-yield tail**, not all 519.

Recommendation: **hybrid** — harness workers with a strong generator model for
the bulk; Task agents only for skills the harness leaves below target.

## Guardrails (non-negotiable)

1. **Leakage firewall.** Generation workers/agents never receive the held-out
   forms. Only the (separate) gold-set transcription touches them; its output
   stays gitignored under `eval/heldout/`.
2. **Every item passes `verify` AND arithmetic re-check AND cross-solve** before
   banking. No "probably correct" is ever written.
3. **Fail loud, no fabrication** (standing rule): a skill that can't reach target
   is recorded in the gaps file, never faked.

## Cost model + pilot results (measured 2026-07-03)

Instrumented pilot — generator `gpt-4o-mini`, cross-solve `gpt-4o` ×2, real API,
one computational and one proof-heavy skill:

| skill (tier)                               |   items | gen calls | solve calls | api/item | $/item\* |
| ------------------------------------------ | ------: | --------: | ----------: | -------: | -------: |
| Vieta / symmetric functions (`relearn`)    |     5/5 |        15 |          22 |      7.4 |  ~$0.017 |
| ideal-vs-subring recognition (`recognize`) | **0/5** |        41 |           0 |        — |        — |

\*list-price token estimate; the `gpt-4o` cross-solve dominates.

**Headline finding.** The deterministic `verify` gate machine-checks
_computational_ items but **not proof/recognition items** — the proof-heavy
`recognize` skill banked **zero** while burning 41 generator calls (verify:
`undecidable` / `no_correct`). A blind 519×30 run would spend real money on the
~119 `recognize` skills and still leave them empty. So segment the buildout:

| segment                                           | skills | bankable via this pipeline? | est. @30/skill |
| ------------------------------------------------- | -----: | --------------------------- | -------------: |
| computational (`relearn` + computational `teach`) |   ~370 | yes, high yield             |      ~$150–200 |
| proof / recognition (`recognize` + proof `teach`) |   ~150 | **no** (verify can't prove) |    wasted here |

Harness verified end-to-end: generated 2/2 real verify+cross-solved Vieta items
and resumed with 0 calls on re-run.

**Revised recommendation.** Bank the computational skills now (cheap, high-yield,
retires the live path for the bulk). Route proof/recognition skills to
**parametric templates where a machine check can be engineered**, or to
**curation** — the one place a per-skill Task agent earns its cost — never
brute-force generation against a gate that structurally cannot pass them.

## Phases / milestones

1. **M1 (now):** plan doc + harness built + verified; small real pilot measures
   yield/cost/time.
2. **M2 — budget gate:** extrapolate pilot → 519×30; owner approves spend +
   mechanism (harness vs hybrid) + generator model.
3. **M3 — gold-set eval:** transcribe held-out items (start GR9367), score solver
   vs ETS key + human `P+`. Validates the gate the whole bank depends on.
4. **M4 — full waves:** topic-batched buildout of the 305 live skills (+ top up
   teach to 30) → merged bank → final leakage sweep → flip serve to bank-first.
5. **M5 — templates:** parametric generators for high-volume recompute topics
   (`det`/`rank`/`eigen`/`antiderivative`/brute) → infinite, deterministic.
6. **M6:** extend gold set to remaining forms; refresh all eval numbers.

## Risks

- **Cost at scale** → pilot-first, hard `--max-total-calls` cap, resumable waves.
- **Low yield on proof-y `recognize` skills** → honest gaps + optional Task-agent
  curation for the tail; templates where a machine check exists.
- **Leakage** → firewall + final `leakage_check` reference sweep before serving.
- **Duplicate/low-variety items** → `leakage_check --self` near-dup screen.

## Open decisions (budget gate)

- Approve the **computational buildout** spend (~$150–200, resumable waves) and
  start now?
- Generator model: keep `gpt-4o-mini` (measured above) or bump to `gpt-4o` for
  higher quality/yield at higher cost?
- Proof/recognition segment: templates vs curated Task-agents — decide after the
  computational bank lands (it does not block it).
