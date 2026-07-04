# Template authoring guide (the swarm's contract)

You author **parametric MCQ templates** for GRE-Math **computational** skills. The
**answer is always computed by CODE (SymPy via `solver.py`), never written by you.**
You only (a) formulate the problem as a machine-solvable spec and (b) dress it
(stem prose, distractor recipes, worked solution). Changing the seed changes the
numbers, so ONE template yields unlimited correct variants.

## Working dir + interpreter

- Dir: `/Users/adambanks/Desktop/manifold/manifold/content/generation`
- Python: `.venv/bin/python` (has sympy). Run everything from that dir.

## Output: one FILE per skill, a LIST of structurally-distinct templates inside it

- Computational skill -> `templates_authored/<skill_id>.json` (filename == the
  exact `skill_id`), a **JSON array of template objects** — one element per
  structurally-distinct problem shape for that skill (see "Structural variety"
  below). A skill that genuinely supports only one shape may keep a single-object
  file (not wrapped in `[...]`); everything else should be a list.
- Genuinely NON-computational skill (proof / "which must be true" / classify /
  recognition / graph-reading / conceptual true-false with no single number-or-
  expression answer) -> `templates_authored/<skill_id>.SKIP.json` containing
  `{"skill_id": "...", "reason": "<one sentence why no machine-checkable template>"}`.
  Prefer authoring; SKIP only when you truly cannot express a single, code-computable
  scalar answer. Aim high: most "compute / evaluate / find the value" skills ARE doable.

## Structural variety (the point of this pass)

A skill that only ever tests ONE method (same op, same relationship, just different
numbers) undersells what the skill actually covers on the real exam. Your job: for
each of your assigned skills, **reason through how many genuinely distinct ways this
skill is tested**, and author one template per way you can make code-computable.

**Before adding a template, ask: is this actually a different problem, or the same
shape with renamed letters?** Genuinely distinct means at least one of:
- a different **method or theorem** applied (e.g. product rule vs. quotient rule vs.
  chain rule are 3 shapes for "differentiate", even though all are `op: diff`);
- a different **relationship or formula** within the skill (e.g. for logarithmic
  equations: `log_b(x+c)=k` vs. `log(x)+log(x+a)=k` vs. `log_b(x^2)=k` vs. a
  change-of-base numeric evaluate are 4 real shapes);
- a different **framing** (a word problem vs. a bare symbolic equation vs. "which of
  the following is a solution" vs. "for what value of the parameter does...");
- a different **answer_spec op** entirely (e.g. `solve` a special case AND `evaluate`
  a numeric instance of the same underlying idea).

NOT genuinely distinct (do not pad with these): renaming slot letters, swapping which
coefficient is randomized, or narrowing/widening a parameter range — that is numeric
variety, already handled by seeding one template many times.

**How many is enough?** There is no fixed quota. Reason honestly per skill:
- A narrow procedural skill (e.g. "units digit of a large power") may genuinely
  support only 3-6 distinct shapes (different mod tricks: last digit cycle, mod 10,
  mod 100, Fermat's little theorem application...). That's fine — say so.
- A skill spanning a whole method family (e.g. "evaluate a definite integral",
  "solving exponential equations", "eigenvalues of a small matrix") often supports
  15-30+ shapes. Aim high there — enumerate every distinct method/case/framing you
  can think of before you stop.
- Never invent a fake distinction just to hit a number. A reviewer (or the
  `structure_report.py` tool below) can and will catch reskins.

**Sanity-check your own work** (advisory, not a hard gate, but use it before you
declare a skill done):

```
.venv/bin/python structure_report.py templates_authored/<skill_id>.json
```

Prints the count of distinct shapes and flags any that collapsed to the same
signature (same `answer_spec.op` + same stem skeleton with numbers/slots blanked) —
a strong signal you reskinned rather than diversified. If it flags a duplicate,
either merge the two or make the wording/method genuinely different.

**Workflow for a skill that already has one template file from a prior pass:**
read the existing file, KEEP the existing template (it's already verified) as the
first element, then APPEND new structurally-distinct templates, converting the file
to a JSON array. Give each template its own unique `template_id`. Work and save
ONE SKILL AT A TIME (read -> add templates -> verify -> write) so progress persists
if you are interrupted partway through.

## Template schema (all fields)

```json
{
  "template_id": "<skill>_v1",
  "skill_id": "<exact skill_id>",
  "topic_id": "<exact topic_id>",
  "tier": "<relearn|teach|recognize>",
  "params":  { "a": {"type":"int","lo":-4,"hi":4}, "n": {"type":"choice","values":[2,3,4]} },
  "constraints": ["Ne([[a]], 0)", "Lt([[k]], [[n]])"],
  "derived":  { "rhs": "[[base]]**[[k]]" },
  "stem": "... question text with [[slots]] and math in \\( ... \\) ...",
  "answer_spec": { "op": "...", "...": "expr strings with [[slots]]" },
  "distractors": ["recipe over [[slots]] and [[answer]]", "...", "...", "...", "...", "..."],
  "solution": "worked solution text with [[slots]] and [[answer]]",
  "distractor_rationales": ["why a student picks distractor 1", "..."]
}
```

- **Slots are `[[name]]`** everywhere (stem, answer_spec strings, constraints,
  derived, distractor recipes, solution). NOT `{name}` (would collide with LaTeX).
- `params`: `int` with `lo`/`hi`, or `choice` with `values`. Seeded sampling.
- `constraints`: predicate strings over `[[slots]]` using
  `Ne/Eq/Gt/Lt/Ge/Le/Mod/And/Or` (e.g. `"Ne([[a]],0)"`, `"Eq(Mod([[b]]+[[c]],2),0)"`).
  Keep numbers clean and answers well-defined; drop degenerate samples.
- `derived`: values COMPUTED from params (SymPy) and usable in the stem (e.g. show a
  right-hand side or a factored number) while the answer stays code-computed.

## answer_spec ops (from solver.py) — the answer is whatever SymPy computes

- `{"op":"evaluate","expr":"binomial([[n]],[[k]])"}` -> a number. (Use for counting,
  arithmetic, closed forms: factorial, binomial, gcd, Mod, Rational, sqrt, pi, etc.)
- `{"op":"solve","equation":"log(x+[[c]],2)-log(x,2)=1","var":"x"}` -> real solution set.
- `{"op":"iterate","f":"[[a]]*x+[[b]]","x0":"[[x0]]","n":"[[n]]","var":"x"}` -> value after n applications.
- `{"op":"diff","expr":"[[a]]*x**3","var":"x","at":"[[x0]]","order":1}` -> derivative (drop `at` for symbolic; but MCQ answers must be a clean rational, so prefer `at`).
- `{"op":"integrate","expr":"[[a]]*x","var":"x","bounds":["[[lo]]","[[hi]]"]}` -> definite integral.
- `{"op":"limit","expr":"sin([[a]]*x)/x","var":"x","point":0}` -> limit (point may be "oo").
- `{"op":"vieta","poly":"x**3-[[s]]*x**2+...","var":"x","which":"sum|prod|sum_pairs"}`.
- `{"op":"system","equations":["[[a1]]*x+[[b1]]*y=[[c1]]","..."],"vars":["x","y"],"want":"x"}`.
- `{"op":"sum","expr":"[[r]]**k","var":"k","lo":"[[lo]]","hi":"[[hi]]"}` -> finite sum.
- `{"op":"det","matrix":[["[[a]]","[[b]]"],["[[c]]","[[d]]"]]}` -> determinant (square).
- `{"op":"trace","matrix":[[...]]}` / `{"op":"rank","matrix":[[...]]}` -> scalar.
- `{"op":"eig","matrix":[[...]],"which":"max|min|sum|prod"}` -> one real eigenvalue/invariant
  (engineer integer eigenvalues, e.g. a triangular matrix has its diagonal as eigenvalues).
- `{"op":"dblintegrate","expr":"x*y","vars":["x","y"],"bounds":[["0","[[b]]"],["0","2"]]}` ->
  iterated double/triple integral. `vars`/`bounds` are INNERMOST FIRST; an inner bound may
  reference an outer var (Type I/II regions, e.g. inner `["0","y"]`). Returns a number.

PARTIAL DERIVATIVES with the single-variable `diff` op: a partial at a point equals
substituting the OTHER variables' values first, then differentiating the remaining one.
E.g. `f_x(x0,y0)`: write `expr` as f with `y` already replaced by `[[y0]]`, `var:"x"`,
`at:"[[x0]]"`. (`f_x(x0,y0) = d/dx[f(x,y0)]|_{x0}`.)

All expr strings are plain SymPy: `**` for powers, `sqrt`, `log(x,base)`, `exp`, `sin`,
`pi`, `Rational(a,b)` (INTEGER a,b), `factorial`, `binomial`, `gcd`, `Mod`, `Abs`.
The engine requires the answer be a **clean rational** by default (set
`"require_rational": false` only for exact radicals/irrationals). **Engineer the
parameters so the answer is a clean integer/fraction** — GRE items need no calculator.

## Distractors (wrong-but-plausible)

- Give **5-6 recipe strings** over `[[slots]]` and `[[answer]]`. The engine computes
  each, DROPS any that equal the answer / another valid solution / a duplicate, and
  keeps the first 4 distinct survivors. Extra recipes are your safety margin.
- Make them **real misconceptions** (sign error, off-by-one, wrong rule, forgot a
  factor, used permutation instead of combination), not just `[[answer]]+1`. A couple
  of `[[answer]]+k` offsets are fine as backups to guarantee 4 survivors.

## Stem rules (READ TWICE — this is where wrong items sneak in)

1. **The stem prose must describe EXACTLY what `answer_spec` computes.** The code
   answer is correct by construction; if your stem asks for the 3rd derivative but the
   spec computes the 2nd, the served item is WRONG. After writing each template, re-read
   the stem and confirm a competent human solving ONLY the stem lands on the spec's answer.
2. Self-contained; never reveal the answer.
3. **All math wrapped in `\( ... \)` (inline) or `\[ ... \]` (display) LaTeX**, using
   TeX macros (`\frac{a}{b}`, `\sqrt{x}`, `x^{2}`, `\cdot`, `\pi`, `\binom{n}{k}`,
   `\begin{bmatrix}a & b \\ c & d\end{bmatrix}`). Plain words stay OUTSIDE the delimiters.
   No `$...$`, no raw Unicode math glyphs (write `\times`, `\le`, `\pi`, not the glyphs).
   Balanced `\( \)` / `\[ \]` and `{ }`.
4. If the equation/problem has MORE THAN ONE solution, ask "Which of the following is
   **a** solution ...?" (never "the solution"), and no distractor may be another valid
   solution (the engine enforces the latter for `solve`).
5. **Non-degenerate numbers.** Avoid ranges that make the problem trivial or ambiguous
   (e.g. a point where the function value equals the derivative). Vary widely.

## STOP CONDITION (loop until this passes for EVERY file you wrote)

```
.venv/bin/python verify_template.py templates_authored/<skill_id>.json
```

Checks EVERY template in the file (a list is checked element-by-element) and must
print `ALL PASS` (each instantiates 40 variants and requires >=20 clean, **>=12
distinct stems** (real number-variety within that one shape; aim for >=20), 5 distinct
choices each, no leftover `[[slots]]`, and — crucially — every shown answer equals a
FRESH SymPy computation of the spec). It also prints a non-blocking `STRUCTURE:` line
for a multi-template file. If it FAILs, fix the offending template (too few distinct
stems -> WIDEN the parameter ranges / add a `choice` dimension; bad constraints -> too
few clean instances; colliding distractors -> add more/better recipes; leftover slot
-> a `[[name]]` with no matching param/derived) and re-run. Do NOT stop until every
file prints `ALL PASS`.

VARIETY (required): choose parameter ranges WIDE enough that the template yields many
visibly-different problems — aim for >=20 distinct stems out of 40. A single small
parameter (e.g. one int in 1..8) is too narrow; combine several params or widen ranges.

## Hard rules

- Only create/edit files under `templates_authored/` for YOUR assigned skills.
- Do NOT edit `solver.py`, `templates.py`, `serve_live.py`, `seed_templates.py`,
  `structure.py`, `structure_report.py`, the gold examples, or any other shared file.
  Do NOT run `build_template_bank.py`.
- No fabrication: if a skill truly has no code-computable scalar answer, SKIP it
  honestly; never fake a passing template. Likewise never pad a skill's shape count
  with reskins just to look thorough — `structure_report.py` and a reviewer will catch it.
- If an existing single-object file already works, DO NOT delete or break it while
  adding more — keep it as element 0 of the new array.

## Reference files to read first

- `seed_templates.py` — 7 working templates (copy their shape).
- Gold examples (all pass verify_template): `templates_authored/combinations_selections_binom_n_k.json`,
  `direct_determinant_computation_22_33.json`, `number_of_positive_divisors_from_the_factorization.json`,
  `tangent_line_equation_or_slope_at_a_point.json`.
- A worked multi-shape example: `templates_authored/compose_a_trig_function_with_an_inverse_trig_functio.json`
  (3 structurally-distinct compositions: sin(arccos), cos(arcsin), tan(arcsin)).
- `solver.py` (op reference + fail-loud semantics), `templates.py` (engine: params,
  constraints, derived, distractor guarding, require_rational).
