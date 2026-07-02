# Precalculus & functions — GRE Math Subject Test problem types

A catalog of the recurring foundational-function templates the exam uses — composition, inverses, domain/range, polynomial/rational behavior, and graph symmetry/transformations — which appear both as fast standalone items and, very often, as the first step buried inside a calculus problem.

> Scope note: This is the "relearn" precalculus feeder for the calculus area. Frequencies are GRE-relative and calibrated to a calculus-heavy exam where _pure_ precalculus is a minority of items — so "common" here means "recurs on most forms in some guise," not "a large share of the test." Derivative-of-inverse, limits/continuity of piecewise functions, and partial-fraction setup lean on these skills but are scored under neighboring calculus topics and are only cross-referenced below.

## Function composition, evaluation & functional equations

### 1. Numeric composite evaluation

- **What it asks:** Given explicit formulas for `f` and `g`, compute a composite value such as `f(g(a))` or `g(f(a))` at a specific number.
- **Approach:** Work inside-out and respect order (`f∘g ≠ g∘f`); the reversed composition is the standard distractor.
- **Difficulty & frequency:** Easy; common (usually as a sub-step of a larger problem).
- **Example stem:** "If `f(x) = x² + 1` and `g(x) = 2x − 3`, what is `f(g(2))`?"

### 2. Symbolic composition & equation-solving

- **What it asks:** Form `f(g(x))` as an expression, simplify it, or solve `f(g(x)) = c` for `x` (sometimes "for how many real `x`").
- **Approach:** Substitute and simplify; to solve, peel functions off one layer at a time or reduce to a polynomial/rational equation and count valid roots.
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** "If `f(x) = 1/(x + 1)` and `g(x) = x²`, for how many real `x` is `f(g(x)) = 1/5`?"

### 3. Function decomposition

- **What it asks:** Express a given composite `h(x)` as `f(g(x))` for suitable inner/outer functions, or recover one factor given the composite and the other.
- **Approach:** Spot the repeated inner "block"; if `h` and `g` are given, solve `h(x) = f(g(x))` for `f` by substitution `u = g(x)`.
- **Difficulty & frequency:** Medium; rare–occasional.
- **Example stem:** "If `h(x) = √(x² + 1)` and `g(x) = x² + 1`, find a function `f` with `h = f∘g`."

### 4. Functional equations

- **What it asks:** Determine `f` (or one value of `f`) from an identity that holds for all inputs — e.g. `f(x + y) = f(x) + f(y)`, `f(xy) = f(x) + f(y)`, or `f(x + y) = f(x)·f(y)`.
- **Approach:** Substitute special values (`0`, `1`, `x = y`) to pin down `f(0)`/`f(1)`, recognize the induced family (linear, logarithmic, exponential), then apply the given data point.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "A function satisfies `f(x + y) = f(x) + f(y)` for all real `x, y`, and `f(3) = 12`. What is `f(10)`?"

### 5. Self-composition, iteration & fixed points

- **What it asks:** Compute `f(f(x))` or an `n`-fold iterate, find `x` with `f(x) = x`, or detect that a function is its own inverse (an involution).
- **Approach:** Iterate carefully; solve `f(x) = x` for fixed points; recognize involutions where `f(f(x)) = x` (e.g. `f(x) = 1/x` or `f(x) = (ax + b)/(cx − a)`).
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "If `f(x) = x/(x − 1)` for `x ≠ 1`, what is `f(f(x))`?"

## Domain, range, piecewise & absolute-value functions

### 6. Largest-domain determination

- **What it asks:** Find the largest subset of `ℝ` on which a given formula defines a real-valued function.
- **Approach:** Intersect the individual constraints — denominators `≠ 0`, even-root radicands `≥ 0`, logarithm arguments `> 0` — and combine into intervals.
- **Difficulty & frequency:** Easy–medium; common.
- **Example stem:** "What is the domain of `f(x) = √(4 − x²) / ln(x)`?"

### 7. Range determination

- **What it asks:** Find the set of output values a function attains over its domain.
- **Approach:** Solve `y = f(x)` for `x` and require real solvability; or complete the square / use monotonic bounds / AM–GM; for a proper rational function, exclude the horizontal-asymptote value.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "What is the range of `f(x) = x/(x² + 1)` over the real numbers?"

### 8. Piecewise-defined evaluation & assembly

- **What it asks:** Evaluate a piecewise function at several inputs, or solve an equation across its branches (often "for how many `x`").
- **Approach:** Select the correct branch for each input; solve within each branch and keep only solutions that land in that branch's own domain.
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** "Let `f(x) = x²` for `x < 1` and `f(x) = 2x − 1` for `x ≥ 1`. For how many real `x` is `f(x) = 3`?"

### 9. Absolute-value equations, inequalities & graphs

- **What it asks:** Solve equations or inequalities involving `|·|`, count their solutions, or identify the graph of an absolute-value expression.
- **Approach:** Case-split by the sign of each argument, or interpret `|x − a|` as a distance; sketch V-shapes and count intersections.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "For how many real numbers `x` does `|x − 1| + |x + 2| = 5`?"

### 10. Greatest-integer (floor) function

- **What it asks:** Evaluate or analyze expressions containing `⌊x⌋`, solve a relation involving the floor, or count where a floor expression jumps.
- **Approach:** Write `x = n + t` with `n` an integer and `0 ≤ t < 1`, then analyze one integer window at a time.
- **Difficulty & frequency:** Medium (hard when it hides a counting subtlety); occasional.
- **Example stem:** "Let `⌊x⌋` denote the greatest integer `≤ x`. For how many real numbers `x` does `⌊x⌋ = 3x − 5`?"

## Inverse and one-to-one functions

### 11. Compute an inverse function

- **What it asks:** Produce a formula for `f⁻¹`, most often for a linear-fractional (Möbius) function `(ax + b)/(cx + d)` or a simple radical/exponential form.
- **Approach:** Set `y = f(x)`, solve algebraically for `x`, then rename; state any domain/range restriction. For Möbius forms, clear the denominator and isolate.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "If `f(x) = (2x + 1)/(x − 3)`, what is `f⁻¹(x)`?"

### 12. Inverse value at a point (no full inversion)

- **What it asks:** Compute `f⁻¹(a)` for one specific `a` without inverting the whole function.
- **Approach:** Solve `f(x) = a` directly; confirm the function is one-to-one so the preimage is unique.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "If `f(x) = x³ + x + 1`, find `f⁻¹(3)`."

### 13. One-to-one / monotonicity / invertibility determination

- **What it asks:** Decide whether a function is one-to-one (injective), on what interval it becomes invertible, or which of several listed functions is invertible.
- **Approach:** Horizontal-line test; strict monotonicity implies one-to-one (often checked via the sign of `f'`); restrict the domain to a single monotonic branch.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "On which of the following intervals is `f(x) = x² − 4x` invertible?"

> Cross-reference: the derivative-of-inverse pattern `(f⁻¹)'(b) = 1/f'(a)` (Inverse Function Theorem) recurs frequently on released forms but is scored as a differential-calculus item; it builds directly on types 11–13.

## Polynomial & rational functions and asymptotes

### 14. Asymptotes of a rational function

- **What it asks:** Identify the vertical, horizontal, and/or slant (oblique) asymptotes — and sometimes removable holes — of a rational function.
- **Approach:** Vertical asymptotes at denominator zeros not cancelled by the numerator; horizontal from degree comparison (numerator degree `<` denominator → `y = 0`; equal → ratio of leading coefficients; numerator one higher → slant asymptote via long division); a cancelled factor gives a hole, not an asymptote.
- **Difficulty & frequency:** Easy–medium; common.
- **Example stem:** "Which horizontal and vertical asymptotes does the graph of `f(x) = (2x² + 3)/(x² − 1)` have?"

### 15. Polynomial roots via factor & remainder theorems

- **What it asks:** Use the remainder theorem (remainder of `p(x) ÷ (x − a)` equals `p(a)`), the factor theorem, or reconstruct/identify a polynomial from given roots or values.
- **Approach:** Evaluate `p(a)` for remainders; `(x − a)` is a factor iff `p(a) = 0`; build `p(x) = c·∏(x − rᵢ)` and fix `c` from one data point.
- **Difficulty & frequency:** Medium; occasional–common.
- **Example stem:** "When `p(x) = x³ − 2x + k` is divided by `(x − 2)`, the remainder is `5`. What is `k`?"

### 16. Counting real roots / intersections

- **What it asks:** Determine the number of distinct real roots of a polynomial, the split between real and non-real roots, or the number of intersection points of two curves.
- **Approach:** Factor, use the discriminant, apply sign changes / the Intermediate Value Theorem, or sketch; recall that non-real roots of a real polynomial come in conjugate pairs (so parity constrains the real-root count).
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "How many distinct real roots does `p(x) = x⁴ − 5x² + 4` have?"

### 17. Roots–coefficients relationships (Vieta)

- **What it asks:** Relate symmetric functions of the roots (sum, product, sum of squares) to the coefficients without actually solving.
- **Approach:** For monic `p(x) = xⁿ + aₙ₋₁xⁿ⁻¹ + … + a₀`, the sum of roots is `−aₙ₋₁` and the product is `(−1)ⁿ a₀`; combine these for symmetric expressions like `r² + s² = (r + s)² − 2rs`.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** "If `r` and `s` are the roots of `x² − 6x + 10`, what is `r² + s²`?"

> Overlap: this also belongs to the algebra / theory-of-equations topic; listed here because it attaches to polynomial functions.

## Transformations & symmetry

### 18. Graph transformations

- **What it asks:** Given a graph or formula, identify the effect of shifts, reflections, and stretches, or match a transformed equation to its graph.
- **Approach:** Read `y = a·f(b(x − h)) + k`: `h` shifts horizontally, `k` vertically; `−f(x)` reflects over the x-axis and `f(−x)` over the y-axis; `a` and `b` scale (vertically and horizontally).
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** "The graph of `y = f(x)` is shown. Which equation shifts it right by 2 and reflects it across the x-axis?"

### 19. Even/odd symmetry & periodicity

- **What it asks:** Classify a function as even, odd, or neither, or use symmetry/periodicity to deduce a value or simplify an expression.
- **Approach:** Even ⇔ `f(−x) = f(x)` (y-axis symmetry); odd ⇔ `f(−x) = −f(x)` (origin symmetry, forcing `f(0) = 0`); apply parity rules to sums/products; use `f(x + p) = f(x)` to reduce large arguments. Frequently invoked to collapse a symmetric definite integral to `0`.
- **Difficulty & frequency:** Easy–medium; occasional–common.
- **Example stem:** "If `f` is odd and `f(2) = 5`, what is `f(−2) + f(0)`?"
