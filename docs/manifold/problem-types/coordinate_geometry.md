# Coordinate geometry — GRE problem types

Scope: analytic-geometry patterns on the GRE Mathematics Subject Test, limited to lines & circles, conic sections, polar coordinates/curves, and parametric curves & their slopes (including the area/arc-length computations native to polar and parametric forms); adjacent pure-calculus and algebra topics are covered by other topics in the DAG.

---

## Lines & circles

### Point-to-line distance

- **What it asks:** Compute the shortest (perpendicular) distance from a given point to a given line, or the distance between two parallel lines.
- **Solve approach:** Apply `d = |a·x₀ + b·y₀ + c| / √(a² + b²)` for line `ax + by + c = 0`; for two parallel lines, evaluate the formula using any point on one line, or take the difference of constants over `√(a²+b²)`.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The distance from the point (3, −1) to the line `4x − 3y + 2 = 0` is …"

### Circle from general form (complete the square)

- **What it asks:** Given a second-degree equation with equal `x²`/`y²` coefficients and no `xy` term, find the circle's center and radius, or determine whether the equation represents a real circle, a point, or nothing.
- **Solve approach:** Group and complete the square in `x` and `y` to reach `(x − h)² + (y − k)² = r²`; watch for a right-hand side that is zero (point) or negative (empty set).
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The graph of `x² + y² − 6x + 4y + 9 = 0` is a circle with radius …"

### Line relationships: slope, intercepts, parallel/perpendicular, intersection

- **What it asks:** Find a line's slope or intercepts, write the equation of a line through given points or parallel/perpendicular to another line, or find the intersection point of two lines.
- **Solve approach:** Use slope `m = Δy/Δx`; parallel lines share `m`, perpendicular lines satisfy `m₁·m₂ = −1`; solve the two-line system by substitution/elimination. Often embedded as a setup step in a larger problem.
- **Difficulty:** easy. **Frequency:** occasional (frequently embedded).
- **Example stem:** "Line `L` passes through (0, 4) and is perpendicular to `2x + y = 1`. Where does `L` cross the x-axis?"

### Tangency and reflection over a line

- **What it asks:** Decide whether (or for what parameter) a line is tangent to a circle, or reflect a point across a given line.
- **Solve approach:** A line is tangent to a circle exactly when the center-to-line distance equals the radius (or the line–circle system has a double root, discriminant `= 0`); to reflect a point, drop a perpendicular to the line and extend an equal distance.
- **Difficulty:** medium. **Frequency:** occasional/rare.
- **Example stem:** "For which value of `k` is the line `y = x + k` tangent to the circle `x² + y² = 8`?"

---

## Conic sections

### Identify the conic from its equation

- **What it asks:** Classify a second-degree equation as a circle, ellipse, parabola, or hyperbola (occasionally a degenerate case).
- **Solve approach:** With no `xy` term, compare the `x²` and `y²` coefficients (equal → circle; same sign, unequal → ellipse; opposite signs → hyperbola; one term missing → parabola). With an `xy` term present, use the discriminant `B² − 4AC` (`< 0` ellipse, `= 0` parabola, `> 0` hyperbola).
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The graph of `9x² − 4y² + 18x − 16y = 43` is a(n) …"

### Ellipse: center, axes, foci, eccentricity

- **What it asks:** Extract the center, semi-axes, foci, or eccentricity of an ellipse, usually after rewriting the equation in standard form.
- **Solve approach:** Complete the square to reach `(x−h)²/a² + (y−k)²/b² = 1`; then `c² = a² − b²` (with `a > b`), foci at distance `c` from center along the major axis, and eccentricity `e = c/a` (with `0 < e < 1`).
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The eccentricity of the ellipse `x²/25 + y²/9 = 1` is …"

### Hyperbola: asymptotes, foci, eccentricity

- **What it asks:** Find the asymptotes, foci, vertices, or eccentricity of a hyperbola.
- **Solve approach:** From `(x−h)²/a² − (y−k)²/b² = 1`, asymptotes are `y − k = ±(b/a)(x − h)`; `c² = a² + b²`, foci at distance `c` from center on the transverse axis, and `e = c/a > 1`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The asymptotes of the hyperbola `x²/9 − y²/16 = 1` have slopes …"

### Parabola: vertex, focus, directrix

- **What it asks:** Given a parabola, find its vertex, focus, directrix, or axis of symmetry.
- **Solve approach:** Put in the form `(x−h)² = 4p(y−k)` (or the `y`-analog); vertex is `(h, k)`, focus is a signed distance `p` from the vertex along the axis, and the directrix is the line at distance `p` on the opposite side.
- **Difficulty:** medium. **Frequency:** occasional/rare.
- **Example stem:** "The focus of the parabola `y = x²/8` is at the point …"

---

## Polar coordinates & polar curves

### Polar ↔ rectangular conversion

- **What it asks:** Convert a point or an equation between polar and Cartesian coordinates, or evaluate `(r, θ)` for a curve.
- **Solve approach:** Use `x = r cos θ`, `y = r sin θ`, `r² = x² + y²`, `tan θ = y/x`; to convert an equation, multiply/substitute strategically (e.g., multiply by `r` to turn `r = 2 cos θ` into `x² + y² = 2x`).
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "In rectangular coordinates, the polar equation `r = 4 sin θ` is …"

### Recognize a polar curve

- **What it asks:** Match a polar equation to its graph, or identify the shape (circle, line, cardioid, limaçon, rose, lemniscate).
- **Solve approach:** Recognize standard families: `r = a` (circle), `r = a cos θ`/`a sin θ` (circle through the origin), `r = a ± b cos θ` (cardioid/limaçon), `r = a cos(nθ)` (rose with `n` or `2n` petals), `r² = a² cos 2θ` (lemniscate); use symmetry and a few sample angles to confirm.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The polar graph of `r = 1 + cos θ` is which of the following curves?"

### Area enclosed by a polar curve

- **What it asks:** Find the area bounded by one or more polar curves, a single petal, or the region inside one curve and outside another.
- **Solve approach:** Integrate `A = ½ ∫ r² dθ` over the correct θ-limits; for a petal, find where `r = 0` to set limits; for "inside one/outside another," subtract the two `½∫r²` integrals over the overlap interval, using intersection angles found by setting the curves equal.
- **Difficulty:** medium–hard. **Frequency:** occasional (a signature analytic-geometry integral on this exam).
- **Example stem:** "The area enclosed by one petal of `r = 2 cos(2θ)` is …"

### Slope and tangents of a polar curve

- **What it asks:** Find the slope `dy/dx` of a polar curve at a given angle, or the tangent-line directions at the pole.
- **Solve approach:** With `x = r cos θ`, `y = r sin θ`, use `dy/dx = (r' sin θ + r cos θ) / (r' cos θ − r sin θ)`; at the pole (`r = 0`), the tangent directions are the angles θ where `r = 0`.
- **Difficulty:** medium–hard. **Frequency:** rare/occasional.
- **Example stem:** "The slope of the curve `r = 1 + cos θ` at `θ = π/2` is …"

---

## Parametric curves & their slopes

### Slope of a parametric curve at a point

- **What it asks:** Find `dy/dx` for a curve given as `x = x(t)`, `y = y(t)` at a specified parameter value or point.
- **Solve approach:** Compute `dy/dx = (dy/dt) / (dx/dt)` and substitute the parameter value; if given a point, first solve for the matching `t`.
- **Difficulty:** easy–medium. **Frequency:** common (a core recurring calculus-flavored pattern).
- **Example stem:** "For `x = t² , y = t³ − t`, the slope of the curve at `t = 2` is …"

### Tangent lines, horizontal/vertical tangents, concavity

- **What it asks:** Write a tangent line to a parametric curve, locate points with horizontal or vertical tangents, or determine concavity.
- **Solve approach:** Horizontal tangents where `dy/dt = 0` (and `dx/dt ≠ 0`); vertical tangents where `dx/dt = 0` (and `dy/dt ≠ 0`); concavity from `d²y/dx² = (d/dt(dy/dx)) / (dx/dt)`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The curve `x = t² − 4t , y = t³ − 3t` has a vertical tangent at `t = …`"

### Arc length of a parametric or polar curve

- **What it asks:** Set up or evaluate the length of a parametric curve over a parameter interval, or of a polar curve.
- **Solve approach:** Parametric: `L = ∫ √((dx/dt)² + (dy/dt)²) dt`; polar: `L = ∫ √(r² + (dr/dθ)²) dθ`. On this no-calculator exam the integrand usually simplifies to a perfect square or a standard antiderivative.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The length of the curve `x = cos t , y = sin t` for `0 ≤ t ≤ π` is …"

### Eliminate the parameter / identify the Cartesian curve

- **What it asks:** Remove `t` to obtain a Cartesian equation, or identify the shape and orientation traced by a parametric pair.
- **Solve approach:** Solve one equation for `t` and substitute, or exploit an identity (e.g., `cos²t + sin²t = 1`) to combine; note the traced range/direction imposed by the parameter domain.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The parametric curve `x = 2 cos t , y = 3 sin t`, `0 ≤ t ≤ 2π`, traces which curve?"
