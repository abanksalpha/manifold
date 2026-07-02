# Elementary algebra — GRE Math Subject Test problem types

Catalog of the recurring, high-school-algebra problem templates the exam draws on — factoring/roots, inequalities, small linear systems, exponents/radicals, logarithms, and the binomial theorem — grouped by sub-skill.

> **Orientation & honesty notes.** On the Subject Test, "elementary algebra" is a small slice of standalone questions but pervasive machinery inside calculus, coordinate-geometry, and additional-topics problems, so several types below are marked _common as embedded tooling_ even when they are _occasional as a headline question_. Difficulty is **GRE-relative** (ETS warns that precalc-only questions can be among the hardest on the test). Two real conventions shape these items: **no calculator is allowed** (numbers are engineered to stay clean), and **a log written with no base means natural log (base e)** per the ETS directions. Several also appear in the "which of I, II, III is true" answer format. Frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268/GR1768, GR3768) and standard prep, not counted statistics; no specific question numbers are cited because they are not verifiable here.

---

## Factoring and the quadratic formula

### 1. Symmetric functions of the roots (Vieta's formulas)

- **What it asks:** Given a polynomial (usually quadratic or cubic) with roots satisfying some relation, find a symmetric combination of the roots (sum, product, sum of squares, sum of reciprocals) or a missing coefficient — without solving for the roots.
- **Approach:** For `ax² + bx + c`, use sum `= −b/a` and product `= c/a`; derive the rest from identities like `r² + s² = (r+s)² − 2rs` and `1/r + 1/s = (r+s)/(rs)`. For cubics use the three elementary symmetric sums. Never solve the equation.
- **Difficulty & frequency:** Easy–medium; common.
- **Example stem:** _"If r and s are the roots of `x² − 6x + 4 = 0`, then `r² + s²` = ?"_

### 2. Discriminant and the nature of the roots

- **What it asks:** Determine for which parameter values a quadratic has two real, one repeated, or no real roots — or count real vs. complex roots.
- **Approach:** Sign of the discriminant `b² − 4ac`: positive → two reals, zero → one repeated, negative → complex pair. For a "double root / tangency" condition, set `b² − 4ac = 0` and solve for the parameter.
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** _"For which values of k does `x² + kx + 9 = 0` have exactly one real solution?"_

### 3. Zero-finding for higher-degree polynomials

- **What it asks:** Factor a cubic/quartic or find its rational roots, then read off remaining roots or a requested value.
- **Approach:** Rational Root Theorem to list candidates `±(factor of constant)/(factor of leading coeff)`, test by substitution, then depress via synthetic/polynomial division to a quadratic and finish with factoring or the quadratic formula. Watch for factor-by-grouping and hidden `difference/sum of cubes`.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** _"One root of `x³ − 4x² + x + 6 = 0` is an integer. Find all three roots."_

### 4. Conjugate roots and building/counting roots (Fundamental Theorem of Algebra)

- **What it asks:** Use the FTA and conjugate-pair rules to count total roots of a polynomial, or reconstruct a polynomial (or a coefficient) from given roots.
- **Approach:** A degree-n polynomial has exactly n complex roots with multiplicity. For **real** coefficients, non-real roots occur in conjugate pairs `a ± bi`, and (for rational coefficients) quadratic-irrational roots pair as `p ± q√d`; multiply the conjugate factors to get a real quadratic factor.
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** _"A polynomial of degree 4 with real coefficients has `2 + i` and `√3` among its roots. How many of its roots are non-real?"_

### 5. Remainder and Factor Theorems

- **What it asks:** Find the remainder of a polynomial divided by `x − a`, decide whether `x − a` is a factor, or solve for a coefficient that forces divisibility.
- **Approach:** Remainder on division by `x − a` equals `p(a)`; `x − a` is a factor iff `p(a) = 0`. Substitute rather than doing long division; for an unknown coefficient, set `p(a) = 0` (or the target remainder) and solve.
- **Difficulty & frequency:** Easy; occasional.
- **Example stem:** _"For what value of c is `x − 2` a factor of `x³ − 3x² + cx − 4`?"_

---

## Polynomial and rational inequalities

### 6. Sign-analysis of a polynomial or rational inequality

- **What it asks:** Solve an inequality like `p(x) > 0` or `p(x)/q(x) ≤ 0` and report the solution set — often as an interval count, a length, or the number of integer solutions.
- **Approach:** Move everything to one side, factor numerator and denominator, mark zeros and (for rationals) undefined points on a number line, and track sign across each interval. Remember denominators are strictly excluded, and factors of even multiplicity do not flip the sign.
- **Difficulty & frequency:** Medium; occasional standalone (common embedded, e.g., "where is `f'(x) > 0`").
- **Example stem:** _"For how many integers x is `(x − 1)(x + 2)/(x − 4) ≤ 0`?"_

### 7. Absolute-value equations and inequalities

- **What it asks:** Solve an equation or inequality involving `|·|`, or identify the solution set / its geometric description.
- **Approach:** `|u| < c` ⇔ `−c < u < c`; `|u| > c` ⇔ `u < −c or u > c`; for equations split into `u = ±c` and discard extraneous cases. Read `|x − a| ≤ r` as "distance from a is at most r."
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** _"The set of real x satisfying `|2x − 3| < 5` is which interval?"_

### 8. Domain from an inequality (radicals, logs, denominators)

- **What it asks:** Determine the domain of an expression whose validity requires solving an inequality (radicand ≥ 0, log argument > 0, denominator ≠ 0).
- **Approach:** Translate the constraint into an inequality and solve it with sign analysis; intersect multiple constraints. (The broader "properties of the resulting function" belongs to the functions topic; here the graded skill is the inequality itself.)
- **Difficulty & frequency:** Easy–medium; common as embedded setup.
- **Example stem:** _"What is the largest set of real x for which `√(x² − x − 6)` is defined?"_

---

## Systems of linear equations

### 9. Solving a small linear system

- **What it asks:** Solve a 2- or 3-variable linear system for a variable or for a linear combination of the unknowns, frequently as an intermediate step feeding a later computation.
- **Approach:** Elimination or substitution; when only a combination like `x + y` is wanted, add/subtract the equations to get it directly instead of solving fully. Clean coefficients signal a fast elimination.
- **Difficulty & frequency:** Easy; occasional standalone (common as a sub-step).
- **Example stem:** _"If `2x + 3y = 7` and `x − y = 1`, then `x + y` = ?"_

### 10. Parameter conditions for consistency

- **What it asks:** Find the parameter value(s) making a linear system have no solution, a unique solution, or infinitely many.
- **Approach:** Two lines are parallel (no/infinite solutions) when coefficient ratios match; equivalently a `2×2` system fails to have a unique solution exactly when the coefficient determinant `ad − bc = 0`. Then check the constant terms to separate "no solution" from "infinitely many." (Full rank/`n×n` treatment is the linear-algebra topic.)
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** _"For which k does `{ x + 2y = 3, 2x + ky = 6 }` have infinitely many solutions?"_

---

## Laws of exponents and radicals

### 11. Simplifying and evaluating exponential/radical expressions

- **What it asks:** Reduce a product/quotient/power of powers to a single value or simplest form, possibly with fractional or negative exponents.
- **Approach:** Apply `aᵐ·aⁿ = aᵐ⁺ⁿ`, `(aᵐ)ⁿ = aᵐⁿ`, `a⁻ⁿ = 1/aⁿ`, and `a^(1/n) = ⁿ√a`; rewrite radicals as fractional exponents and combine over a common base. Factor bases into primes when bases differ.
- **Difficulty & frequency:** Easy; common (pervasive as tooling).
- **Example stem:** _"`(8^(2/3) · 4^(−1/2))` = ?"_

### 12. Solving exponential equations

- **What it asks:** Solve for x in an equation where the unknown sits in an exponent.
- **Approach:** Get a common base and equate exponents (`a^{f(x)} = a^{g(x)} ⇒ f = g`); if two terms with the same base-power appear, substitute `u = aˣ` to get a quadratic. Otherwise take logs. No-calculator design keeps the target exponent an integer or simple fraction.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** _"Solve `4ˣ − 5·2ˣ + 4 = 0` for all real x."_

### 13. Rationalizing, radical conjugates, and nested radicals

- **What it asks:** Simplify an expression with radicals in a denominator, a sum/difference of radicals, or a nested radical.
- **Approach:** Multiply by the conjugate to clear `√` from a denominator (using `(√a − √b)(√a + √b) = a − b`); for `√(a ± 2√b)` seek `√x ± √y` with `x + y = a`, `xy = b`. Keep an eye out for telescoping under the radical.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** _"Written without radicals in the denominator, `1/(√3 − √2)` equals what?"_

---

## Logarithm laws and equations

### 14. Log-law manipulation and evaluation

- **What it asks:** Combine or split logarithms and evaluate an expression, sometimes requiring a change of base.
- **Approach:** Use `log(xy) = log x + log y`, `log(x/y) = log x − log y`, `log(xᵏ) = k·log x`, and change of base `log_a b = (ln b)/(ln a)`. **Trap:** on this exam an unspecified-base `log` means base e, so don't assume base 10.
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** _"If `log₂ 3 = a`, express `log₂ 24` in terms of a."_

### 15. Solving logarithmic equations

- **What it asks:** Solve for x in an equation containing one or more logarithms.
- **Approach:** Consolidate to a single log, rewrite in exponential form (`log_b y = c ⇒ y = b^c`), solve the resulting polynomial, then **discard extraneous roots** that make any original argument non-positive.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** _"Find all real x with `log(x) + log(x − 3) = 1`."_

---

## Binomial theorem expansion

### 16. Extracting a specific term or coefficient

- **What it asks:** Find the coefficient of a given power (or a specific term) in an expansion of `(a + b)ⁿ`.
- **Approach:** General term `C(n, k)·a^{n−k}·b^{k}`; set the resulting power equal to the target and solve for k, then evaluate the binomial coefficient and any numeric factors. Compute `C(n,k)` by cancellation, not full factorials.
- **Difficulty & frequency:** Medium; occasional.
- **Example stem:** _"What is the coefficient of `x³` in the expansion of `(2x − 1)⁵`?"_

### 17. The constant / power-independent term

- **What it asks:** In an expansion like `(x + 1/x)ⁿ` or `(x² − 1/x)ⁿ`, find the term that does not depend on x (or a specified power).
- **Approach:** Write the general term, collect the net exponent of x as a linear function of k, set it to 0 (or the target), solve for k, and evaluate. If no integer k works, no such term exists.
- **Difficulty & frequency:** Medium; occasional (staple of prep material).
- **Example stem:** _"Find the constant term in the expansion of `(x + 2/x)⁶`."_

### 18. Sums of coefficients and binomial identities

- **What it asks:** Evaluate a sum of binomial coefficients or the sum of all coefficients of an expansion.
- **Approach:** Substitute convenient values into `(1 + x)ⁿ`: `x = 1` gives `Σ C(n,k) = 2ⁿ` (sum of all coefficients of a polynomial is its value at 1), and `x = −1` gives the alternating sum `= 0` for `n ≥ 1`. Recognize Pascal's-triangle relations like `C(n,k) = C(n,n−k)`.
- **Difficulty & frequency:** Medium; rare–occasional.
- **Example stem:** _"What is the sum of all the coefficients in the expansion of `(3x − 2)⁴`?"_
