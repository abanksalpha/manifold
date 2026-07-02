# Multivariable differential calculus — GRE problem types

Scope: the differential side of multivariable calculus on the GRE Mathematics Subject Test — partial derivatives (including higher/mixed), the gradient and directional derivatives, the multivariable chain rule, tangent planes and linear approximation, local extrema via the second-derivative (Hessian/discriminant) test, and Lagrange-multiplier constrained optimization; multiple integrals, line/surface integrals and the vector-calculus theorems, limits/continuity in several variables, and all single-variable calculus are covered by other topics in the DAG.

---

## Partial derivatives (including higher & mixed)

### First-order partial derivative at a point

- **What it asks:** Given `f(x, y)` (or `f(x, y, z)`), compute a first partial such as `∂f/∂x`, usually evaluated at a specific point.
- **Solve approach:** Differentiate with respect to the active variable while treating the others as constants; apply product/quotient/chain rules only to that variable, then substitute the point.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "If `f(x, y) = x²y + e^{xy}`, then `f_x(1, 0)` = …"

### Higher-order and mixed partials (Clairaut)

- **What it asks:** Compute a second-order partial (`f_xx`, `f_yy`) or a mixed partial `f_xy`, occasionally testing that the mixed partials are equal.
- **Solve approach:** Differentiate twice in sequence; for a mixed partial either order gives the same result for well-behaved `f` (Clairaut's theorem), so choose the easier order.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "If `f(x, y) = x³y² − x sin y`, then `∂²f/∂x∂y` = …"

### Verify a function satisfies a PDE (harmonic / Laplace)

- **What it asks:** Decide which function satisfies a given partial differential equation — most often Laplace's equation `f_xx + f_yy = 0` (harmonic) — or find a constant that makes it a solution.
- **Solve approach:** Compute the required second partials and substitute into the equation; for "find the constant," set the resulting combination to zero and solve.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For which value of `k` is `f(x, y) = e^{kx} cos y` a solution of `f_xx + f_yy = 0`?"

---

## Gradient & directional derivatives

### Directional derivative in a given direction

- **What it asks:** Compute the directional derivative of `f` at a point in the direction of a given vector.
- **Solve approach:** `D_u f = ∇f · û`, where `û` is the given direction **normalized to unit length**; the signature trap is using the raw vector without normalizing.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "The directional derivative of `f(x, y, z) = xyz` at `(1, 1, 1)` in the direction of `(2, 1, 2)` is …"

### Direction and rate of steepest ascent

- **What it asks:** Find the direction in which `f` increases fastest at a point, and/or the maximum rate of increase there.
- **Solve approach:** The gradient `∇f` points in the direction of steepest ascent; the maximum rate of increase equals `|∇f|`, and steepest descent is `−∇f`.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "At `(1, 2)` the function `f(x, y) = x² + y²` increases most rapidly at the rate …"

---

## Multivariable chain rule

### Chain rule along a parametrized path (`dz/dt`)

- **What it asks:** With `z = f(x, y)` and `x = x(t)`, `y = y(t)`, compute `dz/dt` (often at a specific `t`); sometimes framed as the rate of change a particle experiences while moving along a path.
- **Solve approach:** `dz/dt = f_x·(dx/dt) + f_y·(dy/dt)`; evaluate each factor and substitute the parameter value last.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "If `z = x²y` with `x = cos t` and `y = sin t`, then `dz/dt` at `t = 0` is …"

### Implicit differentiation for a partial derivative

- **What it asks:** Given a relation `F(x, y, z) = c` that defines `z` implicitly (or `F(x, y) = 0` defining `y`), find `∂z/∂x` (or `dy/dx`) at a point.
- **Solve approach:** Use `∂z/∂x = −F_x / F_z` (and `dy/dx = −F_x / F_y`), or differentiate the relation directly with the chain rule and solve for the derivative.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "If `x² + y² + z² = 3` defines `z` as a function of `x` and `y`, then `∂z/∂x` at `(1, 1, 1)` is …"

---

## Tangent planes & linear approximation

### Tangent plane to a surface

- **What it asks:** Find the equation of the tangent plane to a surface at a given point — either a graph `z = f(x, y)` or a level surface `F(x, y, z) = c`.
- **Solve approach:** For a level surface the normal is `∇F`, so the plane is `∇F·(r − r₀) = 0`; for a graph use `z − z₀ = f_x(x − x₀) + f_y(y − y₀)`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The tangent plane to the surface `z = x² + y²` at `(1, 1, 2)` is …"

### Normal vector / normal line to a surface

- **What it asks:** Find a vector normal to a surface at a point, or the (parametric) equations of the normal line there.
- **Solve approach:** The gradient `∇F` at the point is normal to the level surface `F = c`; the normal line is `r₀ + t·∇F`.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "A vector normal to the surface `x² + y² − z = 0` at `(1, 1, 2)` is …"

### Linear approximation and the total differential

- **What it asks:** Use the linearization (tangent plane) to estimate `f` near a point, or use the total differential `dz = f_x dx + f_y dy` to approximate a small change or propagate a measurement error.
- **Solve approach:** `f(x, y) ≈ f(a, b) + f_x(a, b)(x − a) + f_y(a, b)(y − b)`; for a small change, `Δz ≈ dz` evaluated at the base point.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Using differentials, the approximate change in `f(x, y) = √(x² + y²)` as `(x, y)` moves from `(3, 4)` to `(3.1, 3.9)` is …"

---

## Local extrema & the second-derivative test

### Find and classify critical points (discriminant / Hessian test)

- **What it asks:** Locate the critical point(s) of `f(x, y)` and classify each as a local maximum, local minimum, or saddle point.
- **Solve approach:** Solve `f_x = f_y = 0`; at each critical point form `D = f_xx·f_yy − (f_xy)²`. Then `D > 0` with `f_xx > 0` → min, `D > 0` with `f_xx < 0` → max, `D < 0` → saddle, `D = 0` → inconclusive.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "The critical point of `f(x, y) = x² + xy + y² − 3x` is a local …"

### Count or characterize saddle points

- **What it asks:** Determine how many critical points a function has, how many are saddle points, or which statement about them is correct.
- **Solve approach:** Apply the same test but report a count/classification; watch for functions with several critical points (e.g., cubics like `x³ − 3xy + y³`), and evaluate the discriminant at each.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "How many saddle points does `f(x, y) = x³ − 3xy + y³` have?"

### Absolute extrema on a closed region

- **What it asks:** Find the absolute maximum or minimum of `f` on a closed, bounded region (disk, rectangle, or triangle).
- **Solve approach:** Compare the values at interior critical points with the extrema on the boundary (parametrize each edge or apply Lagrange on the boundary), and include any corner points.
- **Difficulty:** hard. **Frequency:** rare (time-costly, so appears in simplified forms).
- **Example stem:** "The maximum value of `f(x, y) = x² + 2y² − x` on the disk `x² + y² ≤ 1` is …"

---

## Lagrange multipliers (constrained optimization)

### Constrained extremum via Lagrange multipliers

- **What it asks:** Find the maximum or minimum of `f(x, y)` (or `f(x, y, z)`) subject to a constraint `g = c`.
- **Solve approach:** Solve `∇f = λ∇g` together with the constraint equation; on this no-calculator exam symmetry or AM–GM often shortcuts the algebra, and comparing candidate values selects max vs. min.
- **Difficulty:** medium–hard. **Frequency:** occasional (the standard constrained-optimization pattern).
- **Example stem:** "The maximum value of `xy` subject to `x² + 4y² = 8` is …"

### Closest / farthest point via a constraint

- **What it asks:** Find the point on a curve or surface nearest to (or farthest from) a given point, or the minimum distance from a point to a constraint set.
- **Solve approach:** Minimize the **squared** distance (to avoid the radical) subject to the constraint, via Lagrange multipliers or substitution; take the square root only at the end.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "The point on the plane `x + 2y + 2z = 9` closest to the origin lies at distance … from the origin."
