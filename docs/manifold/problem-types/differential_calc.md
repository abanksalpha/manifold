# Differential calculus — GRE problem types

Scope: single-variable differentiation _mechanics_ on the GRE Mathematics Subject Test — the derivative from the limit definition, the product/quotient/chain rules, implicit differentiation, and derivatives of standard functions (trig, exp, log, inverse). Downstream _applications_ (related rates, optimization, curve sketching / increasing-decreasing / concavity, and the mean-value theorem) are handled by other topics in the DAG and are deliberately excluded here.

---

## Derivative from the limit definition

### Limit disguised as a derivative

- **What it asks:** A limit written as `lim_{h→0} [f(a+h) − f(a)] / h` or `lim_{x→a} [f(x) − f(a)] / (x − a)` is given, and you must recognize it as `f'(a)` for a familiar `f` and evaluate.
- **Solve approach:** Don't attack the limit directly — pattern-match it to the definition, read off `f` and `a`, differentiate `f` by rule, and substitute `a`. Special values like `lim_{h→0}(e^h − 1)/h = 1` and `lim_{x→0} sin x / x = 1` are the same trick in miniature.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "`lim_{h→0} [ln(2 + h) − ln 2] / h` equals …"

### First-principles computation / correct difference quotient

- **What it asks:** Compute `f'(x)` (or `f'(a)`) straight from the definition, or select which limit expression correctly represents the derivative of a given `f`.
- **Solve approach:** Form `[f(x+h) − f(x)] / h`, expand, cancel the `h`, then take `h→0`; for the "which expression" variant, check both the `h→0` and `x→a` forms.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "Using the definition of the derivative, `f'(2)` for `f(x) = 1/x` is …"

### Differentiability vs. continuity (solve for the constants)

- **What it asks:** Given a piecewise function with unknown constants, find the values making it differentiable (or merely continuous) at the seam; or decide whether a given function is differentiable at a point.
- **Solve approach:** Impose continuity (match the two pieces' values) _and_ match the one-sided derivatives at the break, then solve the system. Recall the standard failures — corners (`|x|`), cusps (`x^{2/3}`), and vertical tangents (`x^{1/3}`) are continuous but not differentiable.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For which `a`, `b` is `f(x) = x²` (for `x ≤ 1`) and `ax + b` (for `x > 1`) differentiable at `x = 1`?"

---

## Product & quotient rules

### Product/quotient rule at a point (table of values)

- **What it asks:** Given numeric values of `f`, `f'`, `g`, `g'` at a point, compute `(fg)'` or `(f/g)'` there (sometimes stacked with the chain rule).
- **Solve approach:** Apply `(fg)' = f'g + fg'` or `(f/g)' = (f'g − fg') / g²` and substitute the tabulated numbers; no symbolic work needed.
- **Difficulty:** easy. **Frequency:** occasional.
- **Example stem:** "If `f(1) = 2`, `f'(1) = 3`, `g(1) = −1`, `g'(1) = 4`, then `(fg)'(1) = …`"

### Symbolic product/quotient derivative

- **What it asks:** Differentiate a product or quotient of elementary functions symbolically, then simplify or evaluate.
- **Solve approach:** Apply the rule, factor the common piece, and simplify carefully — most of the difficulty is bookkeeping/algebra rather than calculus.
- **Difficulty:** easy–medium. **Frequency:** common (often embedded in a larger problem).
- **Example stem:** "`d/dx [ x² / cos x ]` equals …"

---

## Chain rule

### Nested composite derivative

- **What it asks:** Differentiate a composition `f(g(x))` — often two or three layers deep such as `sin(√(x² + 1))` — possibly evaluated at a point.
- **Solve approach:** Differentiate outside-in, multiplying each layer's derivative and carrying the inner argument unchanged until its turn.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "`d/dx cos(e^{3x})` equals …"

### Chain rule with an abstract or tabulated inner function

- **What it asks:** With `f`, `g` given abstractly or by a table, find `(f∘g)'(a)`, or differentiate a construction like `F(x) = f(x²)`.
- **Solve approach:** Use `(f∘g)'(a) = f'(g(a))·g'(a)`; locate the inner value `g(a)` first, then read `f'` at that value.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "If `h(x) = f(x²)` and `f'(4) = 5`, then `h'(2) = …`"

---

## Implicit differentiation

### Implicit `dy/dx` (and slope at a point)

- **What it asks:** Given an implicit relation `F(x, y) = c`, find `dy/dx`, usually evaluated at a specified point on the curve.
- **Solve approach:** Differentiate both sides in `x`, treating `y` as `y(x)` (every `y`-term picks up a `y'` via the chain rule), collect the `y'` terms, solve for `y'`, and substitute the point.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "If `x² + xy + y² = 7`, then `dy/dx` at `(1, 2)` is …"

### Tangent / normal line and horizontal-or-vertical tangents (implicit)

- **What it asks:** Write the tangent (or normal) line to an implicit curve at a point, or find where its tangent is horizontal or vertical.
- **Solve approach:** Get the slope by implicit differentiation; the tangent is horizontal where the numerator of `y'` vanishes and vertical where the denominator vanishes; finish with point-slope form (normal slope is the negative reciprocal).
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The tangent line to `x² + y² = 25` at `(3, 4)` is …"

### Second derivative by implicit differentiation

- **What it asks:** Find `d²y/dx²` for an implicit relation, sometimes at a specific point.
- **Solve approach:** Differentiate the `y'` expression again implicitly, then substitute the earlier `y'` back in and simplify using the original equation.
- **Difficulty:** medium–hard. **Frequency:** rare/occasional.
- **Example stem:** "If `x² − y² = 1`, then `d²y/dx²` in terms of `x`, `y` is …"

---

## Derivatives of standard functions (trig, exp, log, inverse)

### Standard-function derivative recall

- **What it asks:** Differentiate a function built from the standard library — `tan`, `sec`, `a^x`, `log_a`, `arcsin`, `arctan`, etc. — and often evaluate.
- **Solve approach:** Know the derivative table cold (e.g. `d/dx arctan x = 1/(1 + x²)`, `d/dx a^x = a^x ln a`) and combine it with the chain/product rules as needed.
- **Difficulty:** easy–medium. **Frequency:** common (frequently embedded).
- **Example stem:** "`d/dx arctan x` at `x = 1` equals …"

### Logarithmic differentiation (`x^x`-type)

- **What it asks:** Differentiate a variable-base / variable-exponent function such as `x^x`, `x^{sin x}`, or `(sin x)^x`, or a large product/quotient where taking logs is cleaner.
- **Solve approach:** Take `ln` of both sides, differentiate implicitly (`y'/y = …`), then multiply back by `y`. This is the standard route for a base and exponent that both vary.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "If `y = x^x` for `x > 0`, then `y'(1) = …`"

### Derivative of an inverse function, `(f⁻¹)'(b)`

- **What it asks:** Given `f` (and typically that `f(a) = b`), find the derivative of the inverse at `b` — without ever computing `f⁻¹` explicitly.
- **Solve approach:** Use `(f⁻¹)'(b) = 1 / f'(a)` where `f(a) = b`; find the matching `a` (often by inspection), compute `f'(a)`, and reciprocate.
- **Difficulty:** medium. **Frequency:** occasional–common.
- **Example stem:** "If `f(x) = x³ + x + 1` and `g = f⁻¹`, then `g'(1) = …`"

### Higher-order / `n`th-derivative pattern

- **What it asks:** Find a high-order derivative or a general formula for `f^{(n)}`, exploiting a cyclic or predictable pattern (trig cycles, `e^{ax}`, `1/(1 − x)`, `ln x`).
- **Solve approach:** Compute the first few derivatives, detect the period or formula, and extrapolate — for `sin`/`cos` reduce the order mod 4.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The 50th derivative of `sin x` is …"

### Clean-simplifying derivative (identity collapse)

- **What it asks:** Differentiate an intimidating-looking expression that collapses, via an identity, to something tidy — and recognize the clean result.
- **Solve approach:** Differentiate honestly and expect trig/log identities to cancel terms (e.g. `d/dx ln(sec x + tan x) = sec x`); if the algebra explodes, suspect a simplification you're missing.
- **Difficulty:** medium–hard. **Frequency:** rare/occasional.
- **Example stem:** "`d/dx ln(sec x + tan x)` equals …"

### Tangent line to an explicit curve

- **What it asks:** Write the tangent line to `y = f(x)` at a point, or locate where the tangent is horizontal, for `f` built from standard functions.
- **Solve approach:** Compute `f'`, evaluate at the point for the slope, and use point-slope form; set `f'(x) = 0` for horizontal tangents. (This is the geometric meaning of the derivative — distinct from the related-rates/optimization applications covered elsewhere.)
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "The line tangent to `y = x·e^x` at `x = 0` is …"
