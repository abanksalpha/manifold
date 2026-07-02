# Algorithms — GRE problem types

Scope: the small "algorithms" slice of the GRE Mathematics Subject Test — tracing iterative procedures and flowcharts, counting loop iterations/operations, simple recursion tracing, and asymptotic growth comparison; adjacent discrete-math topics (logic, set theory, combinatorics, graph theory) and the calculus-flavored limit machinery are covered by other topics in the DAG.

> **Orientation & honesty notes.** Algorithms is a _minor, less-predictable_ corner of the exam: it lives inside the "additional topics" 25% (discrete mathematics) and typically surfaces as only a small number of items on any given form. The one pattern that genuinely recurs is **procedure/flowchart tracing** — a short program (as a flowchart or a numbered list of steps) that you dry-run to an output. Everything else here is occasional to rare, and a few "textbook CS" ideas are deliberately _not_ padded in: the exam does **not** test memorized complexities of named sorting algorithms (merge/quick/heap), and it rarely uses formal big-O notation — when growth is tested it usually appears as an informal "which grows fastest" comparison that borders the real-analysis/limits topic. Difficulty is **GRE-relative**: the logic is elementary, but off-by-one and loop-exit bookkeeping make these error-prone under time pressure, and there is **no calculator**, so numbers are engineered to stay small and clean. Frequencies below are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep — not counted statistics — and no specific question numbers are cited because they are not verifiable here.

---

## Tracing iterative procedures & flowcharts

### Flowchart / pseudocode output trace

- **What it asks:** Given a flowchart (assignment boxes, a decision diamond, a back-arrow forming a loop) or an equivalent numbered list of pseudocode steps, determine the value printed/returned when the procedure halts.
- **Solve approach:** Keep a small trace table of every variable and update it one pass at a time; the whole difficulty is the boundary, so check the exit test carefully (`<` vs `≤`, test-at-top vs test-at-bottom, and whether the counter is incremented before or after the body). Simulate to the very last iteration rather than guessing the pattern — the intended answer is usually one step off from the "obvious" one. No calculator is needed because the loop runs only a handful of times.
- **Difficulty:** medium. **Frequency:** common (this is the signature algorithms item, most prominent in the older released forms).
- **Example stem:** "A procedure sets `n = 1` and `s = 0`. While `n ≤ 4`, it replaces `s` with `s + n²` and then increases `n` by 1. What value of `s` is printed when the procedure stops?"

---

## Counting operations & loop reasoning

### Loop iteration & operation count

- **What it asks:** Determine how many times a loop body executes, or how many times a specific operation (a multiplication, comparison, or print) is performed before the procedure halts.
- **Solve approach:** Read off the counter's start, step, and exit test; for a fixed additive step the pass count is `⌊(end − start)/step⌋ + 1`, but confirm with the actual first and last counter values instead of trusting the formula (boundary conditions shift it by one). For a multiplicative step, count how many times you can multiply before crossing the bound (a `log` count). For nested loops, multiply independent pass counts or sum an arithmetic series when the inner bound depends on the outer index.
- **Difficulty:** easy–medium. **Frequency:** occasional (often the real question hidden inside a flowchart item).
- **Example stem:** "A loop sets `i = 2` and, while `i < 1000`, doubles `i` each pass. How many times is the loop body executed?"

### Identify what the procedure computes

- **What it asks:** Rather than one numeric output, recognize the general quantity a loop returns as a function of its input — e.g. that an accumulator loop computes `n!`, the sum `1 + 2 + ⋯ + n`, or `xⁿ`.
- **Solve approach:** Trace two or three small inputs to expose the pattern, then match to a closed form; the initialization is the tell (an accumulator seeded at `1` signals a product, at `0` a sum), and the update's dependence on the counter fixes the rest. This is the exam's practical stand-in for "loop-invariant" reasoning — formal invariant proofs do not appear.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "A procedure sets `p = 1`, then for `k = 1, 2, …, n` replaces `p` with `p · k`. In terms of `n`, the returned value `p` is …"

---

## Simple recursion tracing

### Recursive procedure evaluation

- **What it asks:** Given a function defined in terms of itself with a base case, compute its value at a small argument (or after a stated number of self-calls).
- **Solve approach:** Expand top-down to the base case, then substitute back up, keeping the pending calls stacked so no term is dropped. For two-term (Fibonacci-style) recursions, build a short value table upward instead of re-expanding. Verify the base case fires exactly where the definition specifies. (Deriving a _closed form_ for a recurrence leans into the sequences/discrete-math topic; here the graded skill is the mechanical unrolling.)
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "Define `f(1) = 3` and `f(n) = 2·f(n − 1) + 1` for `n > 1`. What is `f(4)`?"

---

## Asymptotic growth & big-O comparison

### Growth-rate ranking ("grows fastest")

- **What it asks:** Order several functions of `n` by how fast they grow for large arguments, or pick the one that grows fastest/slowest.
- **Solve approach:** Apply the standard hierarchy — constant ≺ `log n` ≺ powers `nᵃ` (larger `a` wins) ≺ exponentials `cⁿ` (larger base wins) ≺ `n!` ≺ `nⁿ` — and break ties by the limit of the ratio (dominant term or one L'Hôpital step). Only the dominant term matters, so no calculator is needed. (Shares a border with the limits/real-analysis topic; framed here as complexity comparison.)
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Arrange `n²`, `2ⁿ`, `n log n`, and `n!` in order of increasing rate of growth as `n → ∞`."

### Big-O running time of nested loops

- **What it asks:** Given a fragment with (possibly nested) loops, express its number of basic operations as an order of growth in the input size `n`.
- **Solve approach:** Count passes loop by loop and combine — two independent loops to `n` give `O(n)`, nesting them gives `O(n²)`, a triangular inner bound gives `n(n−1)/2 = O(n²)`, and halving the range each pass gives `O(log n)`; keep only the dominant term and drop constants.
- **Difficulty:** medium. **Frequency:** rare (explicit big-O notation is uncommon on this exam; growth is more often tested by the ranking type above).
- **Example stem:** "A loop runs `j` from 1 to `i` inside a loop that runs `i` from 1 to `n`. The total number of inner-loop steps is of order …"

---

## Basic sorting & searching operation counts

### Search / sort operation count

- **What it asks:** Count the operations (comparisons, swaps, or steps) that a simple, _explicitly described_ search or sort performs on a list of `n` items — usually a best- or worst-case count.
- **Solve approach:** Work from the procedure as written, not from a memorized algorithm name: a sequential scan of `n` items costs up to `n` comparisons; repeatedly halving a sorted list costs about `log₂ n` comparisons; a naive all-pairs pass costs `n(n−1)/2` comparisons. Derive the count by summing the per-pass work. (The exam spells out the procedure; it does not expect recall of named-sort complexities.)
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "A sorted list has 1000 entries. Using repeated halving (binary search), what is the maximum number of comparisons needed to locate a target or report it absent?"
