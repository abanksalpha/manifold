# Integration techniques — GRE problem types

Scope: single-variable antiderivative and definite-integral techniques on the GRE Mathematics Subject Test, limited to u-substitution, integration by parts (including reduction formulas), trigonometric integrals, trigonometric substitution, partial fractions, and improper integrals & convergence; the FTC/Riemann-sum basics, applications (area, volume, arc length, average value), multivariable integrals, and series convergence tests are covered by other topics in the DAG.

---

## u-substitution

### Direct u-substitution (reverse chain rule)

- **What it asks:** Evaluate an indefinite or definite integral whose integrand is (up to a constant) `f(g(x))·g'(x)` — e.g. an inner function times its derivative, or a `1/u · u'` giving a logarithm.
- **Solve approach:** Spot the inner function `u = g(x)` whose derivative already appears; rewrite the whole integral in `u`, integrate, and back-substitute. Watch for the constant factor needed to match `du` (e.g. the `½` in `∫ x·e^(x²) dx`).
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "`∫ x / (x² + 1) dx` equals …"

### Substitution in a definite integral (change the limits)

- **What it asks:** Compute a definite integral where a substitution is needed and the bounds must be transformed (or restored) correctly.
- **Solve approach:** After choosing `u = g(x)`, convert the `x`-limits to `u`-limits with `u = g(a)`, `u = g(b)` and evaluate directly in `u` (no back-substitution needed). On this no-calculator exam the transformed bounds usually give clean values.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "`∫₀¹ x·√(1 + x²) dx` equals …"

### Symmetry shortcut (odd/even; reflection)

- **What it asks:** Evaluate a definite integral over a symmetric interval, or one that collapses under the reflection `x → a + b − x`, where recognizing structure beats computing an antiderivative.
- **Solve approach:** Over `[−a, a]`, an odd integrand gives `0` and an even one gives `2·∫₀ᵃ`; more generally use `∫ₐᵇ f(x) dx = ∫ₐᵇ f(a + b − x) dx` to add the integral to itself and cancel. Always test parity before integrating — it often turns a hard-looking integral into a one-liner.
- **Difficulty:** easy (parity) / hard (reflection variant). **Frequency:** common (parity); rare (reflection variant).
- **Example stem:** "`∫₋₂² (x³·cos x + 5) dx` equals …"

---

## Integration by parts

### Single integration by parts (LIATE choice)

- **What it asks:** Integrate a product of an algebraic factor with an exponential/trig factor, or a lone logarithm/inverse-trig function.
- **Solve approach:** Pick `u` by LIATE (log, inverse-trig, algebraic, trig, exponential) so `du` simplifies; apply `∫ u dv = uv − ∫ v du`. For `∫ ln x dx` or `∫ arctan x dx`, take `dv = dx`.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "`∫ x·e^(−x) dx` equals …"

### Cyclic parts (the integral returns)

- **What it asks:** Integrate a product like `e^(ax)·sin(bx)` or `e^(ax)·cos(bx)` where repeated by-parts reproduces the original integral.
- **Solve approach:** Apply integration by parts twice; the original integral reappears with a coefficient, so solve for it algebraically (move it to the left side). Memorizing the closed form saves time.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "`∫ e^x·sin x dx` equals …"

### Reduction formulas & Wallis-type powers

- **What it asks:** Apply (or derive) a formula that lowers the exponent of an integrand — e.g. `∫ sinⁿx dx`, `∫ xⁿ·e^x dx`, `∫ (ln x)ⁿ dx` — or evaluate a definite power integral via the resulting recursion.
- **Solve approach:** Integrate by parts once to express the `n`-integral in terms of the `(n−2)` or `(n−1)` case; iterate down to a base case. For `∫₀^(π/2) sinⁿx dx = ∫₀^(π/2) cosⁿx dx`, use the Wallis product-of-fractions result (with the extra `π/2` factor when `n` is even).
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "`∫₀^(π/2) sin⁴x dx` equals …"

---

## Trigonometric integrals

### Powers of sine and cosine

- **What it asks:** Evaluate `∫ sinᵐx·cosⁿx dx` for small nonnegative integer powers.
- **Solve approach:** If an odd power is present, peel off one factor and convert the rest with `sin²+cos²=1`, then u-substitute; if both powers are even, reduce with the half-angle identities `sin²x = (1−cos 2x)/2`, `cos²x = (1+cos 2x)/2`.
- **Difficulty:** medium. **Frequency:** occasional–common.
- **Example stem:** "`∫ sin³x·cos²x dx` equals …"

### Powers of tangent and secant

- **What it asks:** Evaluate `∫ tanᵐx·secⁿx dx`, including the standalone `∫ sec x dx`, `∫ tan x dx`, `∫ sec²x dx`.
- **Solve approach:** Save a `sec²x` (with `u = tan x`) or a `sec x·tan x` (with `u = sec x`), converting the remainder via `sec²x = 1 + tan²x`; recall the standard antiderivatives `∫ tan x dx = −ln|cos x|` and `∫ sec x dx = ln|sec x + tan x|`.
- **Difficulty:** medium. **Frequency:** occasional/rare.
- **Example stem:** "`∫ tan²x·sec²x dx` equals …"

### Product-to-sum (orthogonality-style) integrals

- **What it asks:** Integrate a product of sines/cosines of different frequencies, often over a full period.
- **Solve approach:** Apply product-to-sum identities (e.g. `sin A·cos B = ½[sin(A+B) + sin(A−B)]`) to turn the product into a sum of single trig terms, then integrate termwise; over `[0, 2π]` mismatched frequencies integrate to `0`.
- **Difficulty:** medium. **Frequency:** occasional/rare.
- **Example stem:** "`∫₀^(2π) sin(3x)·cos(x) dx` equals …"

---

## Trigonometric substitution

### Radical substitution `√(a²−x²)`, `√(a²+x²)`, `√(x²−a²)`

- **What it asks:** Integrate an expression containing one of the three quadratic radicals (or its reciprocal power), where a trig substitution rationalizes the radical.
- **Solve approach:** Substitute `x = a·sin θ` for `√(a²−x²)`, `x = a·tan θ` for `√(a²+x²)`, `x = a·sec θ` for `√(x²−a²)`; simplify with a Pythagorean identity, integrate in θ, and convert back using a reference triangle.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "`∫ dx / (x² + 4)^(3/2)` equals …"

### Inverse-trig standard forms (with completing the square)

- **What it asks:** Recognize an integrand that integrates directly to `arcsin`, `arctan` (or the corresponding `ln`), sometimes after completing the square in a quadratic denominator.
- **Solve approach:** Match to `∫ dx/(x²+a²) = (1/a)·arctan(x/a)` and `∫ dx/√(a²−x²) = arcsin(x/a)`; if the denominator is a general quadratic, complete the square to `(x−h)² ± c²` first, then apply the form.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "`∫ dx / (x² + 2x + 5)` equals …"

---

## Partial fractions

### Distinct linear factors → sum of logarithms

- **What it asks:** Integrate a proper rational function whose denominator factors into distinct linear terms.
- **Solve approach:** Decompose into `A/(x−r₁) + B/(x−r₂) + …`; find the constants by the cover-up (Heaviside) method or by matching coefficients; integrate to a sum of `ln|x − rᵢ|` terms. Do polynomial long division first if the fraction is improper.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "`∫ 1 / (x² − x − 2) dx` equals …"

### Repeated factors & irreducible quadratics

- **What it asks:** Integrate a rational function whose denominator has a repeated linear factor or an irreducible quadratic factor.
- **Solve approach:** Include a term for each power of a repeated factor (`A/(x−r) + B/(x−r)²`) and a `(Bx + C)` numerator over each irreducible quadratic; the quadratic piece splits into a `ln` part (from the `u'/u` term) plus an `arctan` part (after completing the square).
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "`∫ (x + 1) / (x·(x² + 1)) dx` equals …"

---

## Improper integrals & convergence

### Evaluate a convergent improper integral

- **What it asks:** Compute an improper integral with an infinite limit or an integrand singularity inside/at the endpoint of the interval.
- **Solve approach:** Rewrite as a limit (`∫ₐ^∞ = lim_(b→∞) ∫ₐᵇ`, or split at a singularity), find the antiderivative, and evaluate the limit. Standard pieces: `∫₀^∞ e^(−ax) dx = 1/a`, `∫₁^∞ x^(−p) dx`, `∫₀¹ x^(−p) dx`.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "`∫₁^∞ 1 / x² dx` equals …"

### Convergence vs. divergence (p-test & comparison)

- **What it asks:** Decide whether one or more improper integrals converge — frequently a "which of the following converge?" multiple-select-style item.
- **Solve approach:** Use the p-integral facts (`∫₁^∞ x^(−p) dx` converges iff `p > 1`; `∫₀¹ x^(−p) dx` converges iff `p < 1`) and comparison/limit-comparison against a known p-integral or `e^(−x)`; check both the tail behavior and any interior blow-up.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "For which values of `p` does `∫₁^∞ dx / xᵖ` converge?"

### Named/parameter improper integrals (Gamma, factorial)

- **What it asks:** Evaluate an improper integral that equals a memorable closed form, most often the factorial integral.
- **Solve approach:** Recognize `∫₀^∞ xⁿ·e^(−x) dx = n!` (the Gamma function `Γ(n+1)`), derivable by repeated by-parts; related memorized values include `∫₀^∞ e^(−ax) dx = 1/a` and the Gaussian `∫₋∞^∞ e^(−x²) dx = √π`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "`∫₀^∞ x²·e^(−x) dx` equals …"

---

## Cross-cutting

### Identify or verify the antiderivative

- **What it asks:** Given `f`, pick which of five closed-form expressions is a correct antiderivative (or the value of a definite integral) — the standard multiple-choice packaging for every technique above.
- **Solve approach:** When the forward integral is awkward, differentiate each candidate answer and match to `f`, or plug a convenient value into both the integral and the choices to eliminate options; this reverse check is often faster than integrating under time pressure.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "Which of the following is equal to `∫ x·√(x + 1) dx`?"
