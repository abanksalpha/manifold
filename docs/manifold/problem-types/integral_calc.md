# Integral calculus — GRE problem types

Scope: single-variable integration patterns on the GRE Mathematics Subject Test, limited to the Fundamental Theorem of Calculus (both parts), the definite integral as a limit of Riemann sums, antiderivatives/indefinite integrals of standard functions, average value of a function, and basic properties/symmetry of definite integrals. Integration _techniques_ (u-substitution, parts, trig substitution, partial fractions) and _applications_ (area between curves, volumes, arc length) are covered by separate topics in the DAG.

---

## Fundamental theorem of calculus (both parts)

### Differentiate an accumulation function (FTC-1 + chain rule)

- **What it asks:** Given `F(x) = ∫` from a constant (or a function) up to a function of `x` of some integrand, find `F'(x)` — or evaluate `F'` at a specific point.
- **Solve approach:** By FTC-1, `d/dx ∫ₐˣ f(t) dt = f(x)`; with a variable upper limit `g(x)` apply the chain rule to get `f(g(x))·g'(x)`, and for two variable limits subtract the two contributions. Do **not** try to evaluate the integral itself.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "If `F(x) = ∫₁^{x²} ln t dt`, then `F'(x) = …`"

### Extrema / monotonicity of an accumulation function

- **What it asks:** For `F(x) = ∫ₐˣ f(t) dt`, determine where `F` is increasing/decreasing, or locate its local max/min on an interval.
- **Solve approach:** Since `F'(x) = f(x)`, sign analysis of the **integrand** controls `F`: `F` increases where `f > 0`, and local extrema of `F` occur where `f` changes sign. No antiderivative of `f` is needed.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For `x ≥ 0`, `F(x) = ∫₀ˣ (t² − 4) dt` attains its minimum value at `x = …`"

### Limit of an integral (FTC-1 + L'Hôpital / Taylor)

- **What it asks:** Evaluate a limit whose numerator is a definite integral with a variable limit, divided by a power of `x` (an indeterminate `0/0` form as `x → 0`).
- **Solve approach:** Differentiate top (FTC-1) and bottom via L'Hôpital, or replace the integrand by its leading Taylor term and integrate. Recognizing `∫₀ˣ (leading term) ≈` a power of `x` is the shortcut.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "`limₓ→₀ (1/x³) ∫₀ˣ sin(t²) dt = …`"

---

## Definite integrals as limits of Riemann sums

### Recognize a limit of a sum as a definite integral

- **What it asks:** Evaluate the limit of a sum (given in sigma notation) by identifying it as a Riemann sum for some definite integral.
- **Solve approach:** Rewrite the summand to expose a factor of `1/n` (the width) and a `k/n` (the sample point), so `limₙ→∞ (1/n) Σ f(k/n) = ∫₀¹ f(x) dx`; then evaluate the resulting standard integral.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "`limₙ→∞ Σ_{k=1}^{n} n/(n² + k²) = …`"

### Definite integral from the limit-of-sums definition

- **What it asks:** Identify which sum/limit represents a given definite integral (or which integral a given left/right/midpoint sum approximates), or evaluate a simple integral straight from the definition.
- **Solve approach:** Use `Δx = (b−a)/n` and sample points `xₖ = a + kΔx`; match `Σ f(xₖ)Δx` to `∫ₐᵇ f`. Knowing `Σk = n(n+1)/2` and `Σk² = n(n+1)(2n+1)/6` lets you take the limit directly for polynomial integrands.
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "Which of the following limits is equal to `∫₀¹ eˣ dx`?"

---

## Antiderivatives & indefinite integrals of standard functions

### Evaluate a definite integral via FTC-2 (standard antiderivatives)

- **What it asks:** Compute a definite (or indefinite) integral of a standard function directly from a known antiderivative.
- **Solve approach:** Apply FTC-2, `∫ₐᵇ f = G(b) − G(a)`, using the memorized antiderivatives: powers `xⁿ`, `eˣ`, `1/x → ln|x|`, `sin`/`cos`, `sec²x → tan x`, `1/(1+x²) → arctan x`, `1/√(1−x²) → arcsin x`. Equivalently, `∫ₐᵇ g'(x) dx = g(b) − g(a)`.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "`∫₀^{1} dx/(1 + x²) = …`"

### Recover a function from its derivative + initial condition

- **What it asks:** Given `f'(x)` (or `f''`) together with a value like `f(a)`, find `f` or a specific value `f(b)`.
- **Solve approach:** Antidifferentiate to get the general form with a `+C`, then use the given point to solve for `C`; evaluate as needed. (Antiderivative-of-standard-function skill, not a differential-equations method.)
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "If `g'(x) = 3√x` and `g(0) = 2`, then `g(4) = …`"

### Integrate absolute-value / piecewise integrands

- **What it asks:** Evaluate a definite integral whose integrand is `|·|`, a piecewise-defined function, or something (like `√(x²)`) that must be split by sign.
- **Solve approach:** Break the interval at the points where the integrand changes formula/sign, integrate each piece with the correct expression, and add. A sketch confirms which branch applies on each subinterval.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "`∫_{-1}^{2} |x| dx = …`"

---

## Average value of a function

### Compute the average value of a function

- **What it asks:** Find the average (mean) value of a continuous function over a closed interval.
- **Solve approach:** Apply `f_avg = (1/(b−a)) ∫ₐᵇ f(x) dx`; reduce to a standard antiderivative evaluation, and use symmetry when the interval is symmetric.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The average value of `f(x) = sin x` on `[0, π]` is …"

### Mean Value Theorem for integrals

- **What it asks:** Use or recognize the guarantee that a continuous `f` attains its average value: there exists `c ∈ [a, b]` with `∫ₐᵇ f = f(c)(b − a)`.
- **Solve approach:** Compute the average value, then identify the point(s) `c` where `f(c)` equals it (solve `f(c) = f_avg`); or recognize the statement as a true/false conceptual claim about continuity.
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "If `∫₀⁴ f = 12` for a continuous `f`, some `c` in `[0, 4]` must satisfy `f(c) = …`"

---

## Basic properties & symmetry of definite integrals

### Odd/even symmetry shortcut

- **What it asks:** Evaluate an integral over a symmetric interval `[−a, a]` where the integrand splits into odd and even parts.
- **Solve approach:** Odd terms integrate to `0` over `[−a, a]`; even terms give `2∫₀ᵃ`. Spotting odd factors (odd powers, `sin`, `x·even`) collapses much of the integrand instantly — usually the intended fast path.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "`∫_{-1}^{1} (x³ + sin x + 2) dx = …`"

### Linearity & interval additivity with given values

- **What it asks:** Combine or split integrals using given numeric values of related integrals (rather than computing from a formula).
- **Solve approach:** Use `∫(αf + βg) = α∫f + β∫g`, `∫ₐᵇ = ∫ₐᶜ + ∫ᶜᵇ`, and `∫ₐᵇ = −∫ᵇₐ` to assemble the requested quantity from the pieces provided.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "If `∫₁⁴ f = 7` and `∫₁² f = 3`, then `∫₂⁴ (2f) = …`"

### Bounding / comparing integrals without computing

- **What it asks:** Decide which of two integrals is larger, or bound an integral between two numbers, when it can't (or needn't) be evaluated in closed form.
- **Solve approach:** Use monotonicity/comparison: if `f ≤ g` on `[a, b]` then `∫f ≤ ∫g`; bound the integrand by its min and max to get `m(b−a) ≤ ∫f ≤ M(b−a)`. Compare pointwise on the interval (e.g., which of `x²`, `x³` is larger on `[0,1]`).
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Which is larger: `∫₀¹ e^{x²} dx` or `∫₀¹ e^{x³} dx`?"

### Reflection ("king's") property

- **What it asks:** Evaluate an integral that is intractable directly but collapses under the substitution that reflects the interval, `∫₀ᵃ f(x) dx = ∫₀ᵃ f(a − x) dx`.
- **Solve approach:** Add the integral to its reflected copy so the integrand simplifies to a constant (often `1`), giving `2I = ∫₀ᵃ 1 dx`; solve for `I`. Classic for symmetric `sin`/`cos` or `tan`-power ratios.
- **Difficulty:** hard. **Frequency:** rare.
- **Example stem:** "`∫₀^{π/2} dx / (1 + (tan x)^{√2}) = …`"
