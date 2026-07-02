# Applications of derivatives — GRE problem types

Scope: derivative-application patterns on the GRE Mathematics Subject Test, limited to related rates; critical points with the first/second derivative tests; the Mean Value Theorem and Rolle; concavity, inflection & curve behavior read from `f'`/`f''`; applied max/min optimization; and tangent-line / linear approximation. Computing derivatives, limits, and antiderivatives/integration are covered by other topics in the DAG.

---

## Related rates

### Geometric related rates (expanding or filling solids)

- **What it asks:** Given the time-rate of one geometric quantity, find the rate of a related one for figures like an inflating sphere, an expanding circle, or a cone/trough being filled or drained.
- **Solve approach:** Write the equation relating the variables (e.g., `V = (4/3)πr³`), differentiate implicitly with respect to `t`, then substitute the instantaneous values and the known rate and solve for the unknown rate. Keep truly constant quantities fixed before differentiating (a common trap in cone problems is to eliminate one variable using similar triangles first).
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "A spherical balloon is inflated so its volume grows at `8 cm³/s`. How fast is the radius increasing when `r = 2 cm`?"

### Related rates via similar triangles or a changing angle

- **What it asks:** Find a rate involving a moving object and its shadow, or the rate of change of an angle of elevation/depression.
- **Solve approach:** Set up a proportion from similar triangles (shadow/lamppost) or a trig relation (`tan θ = opp/adj`) linking the quantities, differentiate with respect to `t`, and substitute. Distinguish the tip-of-shadow speed from the shadow-length rate.
- **Difficulty:** medium. **Frequency:** rare/occasional.
- **Example stem:** "A `6 ft` person walks away from a `15 ft` lamppost at `4 ft/s`. How fast is the tip of the shadow moving?"

---

## Critical points & first/second derivative tests

### Locate and classify local extrema

- **What it asks:** Find where a given function has a local maximum or minimum (or which value/point it is), for polynomials, rationals, or functions mixing `eˣ`, `ln`, and trig.
- **Solve approach:** Solve `f'(x) = 0` (and note where `f'` is undefined), then classify each critical point by a sign change of `f'` (first-derivative test) or the sign of `f''` (second-derivative test). On multiple choice, testing the derivative's sign just left/right of a root is fastest.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "At what value of `x` does `f(x) = x³ − 6x² + 9x + 1` have a local maximum?"

### Absolute (global) extrema

- **What it asks:** Find the largest/smallest value of a function, either on a closed interval `[a, b]` or over an unbounded domain.
- **Solve approach:** On a closed interval use the candidate test — evaluate `f` at interior critical points and at both endpoints, then compare (Extreme Value Theorem). On an unbounded domain, set `f'(x) = 0` and confirm it is a global min/max; expressions like `x + c/x` (`x > 0`) yield to the AM–GM shortcut (`x + 4/x ≥ 4`, equality at `x = 2`) without calculus.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "The maximum value of `f(x) = x³ − 3x` on `[0, 3]` is …"

### Count critical points / relative extrema

- **What it asks:** How many critical points, relative extrema, or (via `f''`) inflection points a function has.
- **Solve approach:** Differentiate and count real roots with a genuine sign change: factor the derivative, use the discriminant for a quadratic factor, or check that repeated roots do not flip sign (so they are not extrema). Answer choices are small integers, so a quick sign chart settles it.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "How many relative extrema does `f(x) = 3x⁵ − 5x³` have?"

### Parameter tuned to force a critical point or extremum

- **What it asks:** Find a constant so that `f` has a critical point (or a max/min of a given type) at a specified location, or so a stated point lies on the curve with prescribed behavior.
- **Solve approach:** Impose the conditions as equations — `f'(x₀) = 0` for a critical point, plus `f(x₀) = value` or a sign of `f''(x₀)` if the max/min type is specified — and solve for the parameter.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For what value of `k` does `f(x) = x³ + kx² + x` have a critical point at `x = 1`?"

---

## Mean value theorem (and Rolle)

### Find the `c` guaranteed by MVT/Rolle

- **What it asks:** Find the value(s) `c` in `(a, b)` with `f'(c) = (f(b) − f(a))/(b − a)` (MVT), or `f'(c) = 0` (Rolle) when `f(a) = f(b)`.
- **Solve approach:** Compute the secant slope, set `f'(c)` equal to it, and solve for `c`, keeping only roots inside the open interval.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "For `f(x) = x²` on `[1, 3]`, the value `c` satisfying the Mean Value Theorem is …"

### MVT bound on a function value or an inequality

- **What it asks:** Use a bound on `f'` to bound how much `f` can change, or to establish an inequality between `f`-values.
- **Solve approach:** Apply `f(b) − f(a) = f'(c)(b − a)` with the given bounds on `f'` to squeeze `f(b)` (e.g., `f' ≤ M` gives `f(b) ≤ f(a) + M(b − a)`). This is the standard way to prove estimates like `|sin x − sin y| ≤ |x − y|`.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "If `f` is differentiable with `f(0) = 1` and `f'(x) ≤ 2` for all `x`, what is the largest possible value of `f(3)`?"

### Count real roots of an equation

- **What it asks:** Determine how many real solutions an equation `f(x) = 0` has (a recurring GRE flavor).
- **Solve approach:** Use `f'` to find where `f` increases/decreases, then combine monotonicity with sign changes and limits (Intermediate Value Theorem) to count crossings; equivalently, Rolle bounds it — between consecutive real roots of `f` there is a root of `f'`, so if `f'` has `k` real roots, `f` has at most `k + 1`. A strictly monotonic function has at most one root.
- **Difficulty:** medium. **Frequency:** occasional (recurring flavor).
- **Example stem:** "How many real solutions does `x³ + 3x + 1 = 0` have?"

---

## Concavity, inflection & curve sketching from f'/f''

### Intervals of increase/decrease and concavity

- **What it asks:** State where `f` is increasing/decreasing, or where it is concave up/down.
- **Solve approach:** Build a sign chart for `f'` (increasing where `f' > 0`, decreasing where `f' < 0`) and for `f''` (concave up where `f'' > 0`, concave down where `f'' < 0`), splitting the line at the zeros of each.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "On what interval is `f(x) = x³ − 3x²` concave up?"

### Inflection points

- **What it asks:** Find the inflection point(s) of `f`.
- **Solve approach:** Solve `f''(x) = 0` (and where `f''` is undefined), then confirm `f''` actually changes sign there; a double root of `f''` that keeps its sign is not an inflection point.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The `x`-coordinate of the inflection point of `f(x) = x³ − 6x² + 5x` is …"

### Deduce `f`'s behavior from the graph or sign of `f'` (or `f''`)

- **What it asks:** Given the graph or a sign table of `f'` (occasionally `f''`), determine where `f` has a local max/min, is increasing, or is concave up; or match a function to its derivative's graph.
- **Solve approach:** Translate directly: `f` increases where `f' > 0`; a local max is where `f'` changes `+ → −`; concavity of `f` follows the sign of `f''`, i.e., the slope/rise of the `f'` graph. Zeros of `f'` are candidate extrema, not automatically zeros of `f`.
- **Difficulty:** medium. **Frequency:** occasional/rare.
- **Example stem:** "The graph of `f'` is shown. At which labeled point does `f` attain a local minimum?"

---

## Applied optimization (max/min word problems)

### Geometric / cost optimization with a constraint

- **What it asks:** Maximize or minimize a quantity (area, volume, surface area, material, cost, or time) subject to a constraint, e.g., a box of largest volume, a fixed-perimeter enclosure, or a minimal-material can.
- **Solve approach:** Write the objective, use the constraint to reduce it to one variable, differentiate and solve `f' = 0`, verify it is the intended max/min (second-derivative test or endpoint/domain check), and read off the requested value. Watch whether the answer wants the optimal input or the optimal objective value.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "An open-top box is formed by cutting equal squares from the corners of a `12 in` square sheet and folding up the sides. What cut length maximizes the volume?"

### Minimum distance / closest point

- **What it asks:** Find the point on a curve or line closest to a given point (or the minimum distance itself).
- **Solve approach:** Minimize the squared distance `D²(x)` to avoid the radical, differentiate and solve; alternatively use the geometric fact that the shortest segment meets the curve/line perpendicularly.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "What point on the parabola `y = x²` is closest to the point `(0, 3)`?"

---

## Tangent-line / linear approximation

### Tangent-line equation or slope at a point

- **What it asks:** Find the tangent line to `y = f(x)` at a given point, or a feature of it (slope, `y`-intercept, or where it meets an axis).
- **Solve approach:** Slope is `f'(x₀)`; use point-slope form `y − f(x₀) = f'(x₀)(x − x₀)`. For an implicitly defined curve, differentiate implicitly to get `dy/dx` at the point.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "Find the equation of the line tangent to `y = eˣ` at `x = 0`."

### Tangent with a prescribed condition

- **What it asks:** Find point(s) where the tangent is horizontal, has a specified slope, is parallel/perpendicular to a given line, or passes through a given external point.
- **Solve approach:** For a slope condition, solve `f'(x) = m`. For "tangent through an external point," write the tangent at an unknown `x`, require it to pass through the point, and solve the resulting equation (often a double-root / discriminant condition).
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The tangent line to `y = x²` that passes through `(0, −1)` touches the curve at `x = …`"

### Linear approximation / differentials

- **What it asks:** Estimate a numerical value (a root, power, or trig value) or a small change/error in a quantity.
- **Solve approach:** Use `L(x) = f(a) + f'(a)(x − a)` with a convenient base point `a`, or `dy = f'(x) dx` for a change; pick `a` where `f(a)` and `f'(a)` are easy.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "Use a linear approximation to estimate `(1.02)¹⁰`."

### Newton's method iteration

- **What it asks:** Carry out one or two steps of Newton's method, or identify the value it approaches.
- **Solve approach:** Apply `xₙ₊₁ = xₙ − f(xₙ)/f'(xₙ)`, the `x`-intercept of the tangent line at `xₙ`.
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "Starting from `x₀ = 2`, one step of Newton's method applied to `f(x) = x² − 3` gives `x₁ = …`"
