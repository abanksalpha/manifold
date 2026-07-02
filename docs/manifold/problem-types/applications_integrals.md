# Applications of integration — GRE problem types

Scope: single-variable applications of the definite integral on the GRE Mathematics Subject Test — area between curves, volumes of revolution (disks/washers/shells), volumes by cross-section, arc length & surface area of revolution, and accumulation-type problems (net change, displacement/distance, average value); the integration _techniques_, improper integrals, and all multivariable integrals are covered by other topics in the DAG. On this no-calculator exam these questions reward picking the computation-light route (symmetry, geometry, an integrand engineered to a perfect square, or just the right set-up) over grinding an antiderivative.

---

## Area between curves

### Area between two curves (integrate in x)

- **What it asks:** Find the area of the region enclosed by two curves `y = f(x)` and `y = g(x)`, often after first locating their intersection points.
- **Solve approach:** Set `f = g` for the limits, then integrate `∫ (top − bottom) dx`; split the integral where the curves swap order, and use symmetry to halve the work when the region is even about an axis.
- **Difficulty:** easy–medium. **Frequency:** common (the most likely single representative of this topic).
- **Example stem:** "The area of the region bounded by `y = x²` and `y = 2x` is …"

### Area by horizontal strips (integrate in y)

- **What it asks:** Find the area of a region that is far cleaner to describe as `x = f(y)`, where vertical strips would need to be split into several pieces.
- **Solve approach:** Rewrite the boundaries as functions of `y` and integrate `∫ (right − left) dy` between the `y`-limits; recognizing that `dy` beats `dx` is the whole trick.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Find the area enclosed by the parabola `x = y²` and the line `x = y + 2`."

### Definite integral evaluated as a geometric area

- **What it asks:** Evaluate a definite integral whose integrand is a semicircle, a line, or an absolute value — quickly, without antidifferentiating.
- **Solve approach:** Recognize the graph (`√(r² − x²)` is a semicircle, `|x|` gives triangles) and use elementary area formulas; drop odd-function pieces integrated over a symmetric interval.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "`∫₋₃³ √(9 − x²) dx = …`"

### Choose the correct integral set-up for a region

- **What it asks:** Given a described or sketched region, select which integral expression (among the answer choices) computes its area or volume — a recurring ETS presentation for this whole topic.
- **Solve approach:** Match limits, the order of subtraction, and the variable of integration to the region; eliminate choices with wrong bounds, a reversed top/bottom, or the wrong `dx`/`dy`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Which of the following integrals gives the area of the region bounded by `y = ln x`, `y = 0`, and `x = e`?"

---

## Volumes of revolution

### Disk/washer volume about a coordinate axis

- **What it asks:** Find the volume of the solid formed when a plane region is revolved about the x- or y-axis.
- **Solve approach:** `V = π ∫ (R_outer² − R_inner²)` integrating along the axis of revolution; when the region touches the axis there is no inner radius (a solid disk). Keep radii as functions of the integration variable.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "The region under `y = √x` from `x = 0` to `x = 4` is revolved about the x-axis. Find the volume."

### Shell-method volume

- **What it asks:** Find a volume of revolution in the case where slicing parallel to the axis (cylindrical shells) is much easier than washers.
- **Solve approach:** `V = 2π ∫ (radius)(height) d·`; use it when revolving a region given as `y = f(x)` about the y-axis, so you avoid solving for `x`. Choosing shells vs. washers is the decision being tested.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The region bounded by `y = x²`, `y = 0`, and `x = 1` is revolved about the y-axis. Find the volume."

### Revolution about a line other than an axis

- **What it asks:** Find the volume when the axis of revolution is a line such as `y = k` or `x = k` rather than a coordinate axis.
- **Solve approach:** Replace each radius by its _distance to that line_ (e.g., outer radius `= k − f(x)`); otherwise proceed by washers or shells as usual. The trap is forgetting to shift the radius.
- **Difficulty:** medium–hard. **Frequency:** rare.
- **Example stem:** "The region between `y = x` and `y = x²` is revolved about the line `y = 2`. Find the volume."

---

## Volumes by cross-section

### Volume by known cross-sections

- **What it asks:** A solid has a given base region and cross-sections perpendicular to an axis that are all a fixed shape (squares, semicircles, or equilateral triangles); find its volume.
- **Solve approach:** `V = ∫ A(x) dx`, writing the cross-section area `A(x)` in terms of the base's width `s(x)` — squares `s²`, semicircles `πs²/8`, equilateral triangles `(√3/4)s²`. The work is expressing `s(x)` from the base curves.
- **Difficulty:** medium. **Frequency:** occasional/rare.
- **Example stem:** "A solid has base the disk `x² + y² ≤ 1`, and every cross-section perpendicular to the x-axis is a square. Find its volume."

---

## Arc length & surface area of revolution

### Arc length with a perfect-square integrand

- **What it asks:** Find the length of a curve `y = f(x)` on an interval `[a, b]`.
- **Solve approach:** `L = ∫ √(1 + (y′)²) dx`; exam curves are chosen so `1 + (y′)²` is a perfect square (classic cases like `y = (2/3)x^{3/2}` or `y = (eˣ + e⁻ˣ)/2`), collapsing the root to something elementary.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Find the length of `y = (2/3)x^{3/2}` from `x = 0` to `x = 3`."

### Surface area of a surface of revolution

- **What it asks:** Find (or identify the integral for) the area of the surface generated by revolving a curve about an axis.
- **Solve approach:** `S = ∫ 2π(radius) √(1 + (y′)²) dx`, where the radius is the distance from the curve to the axis; the same perfect-square simplification as arc length keeps it hand-computable, and often you only need to select the correct set-up.
- **Difficulty:** hard. **Frequency:** rare.
- **Example stem:** "The curve `y = √x`, `0 ≤ x ≤ 1`, is revolved about the x-axis. Which integral gives the area of the resulting surface?"

---

## Accumulation & related single-variable applications

### Displacement vs. total distance from velocity

- **What it asks:** Given a velocity `v(t)`, find the net displacement or the total distance traveled over a time interval.
- **Solve approach:** Displacement `= ∫ v dt`; total distance `= ∫ |v| dt`, so find where `v` changes sign and split the integral. Distinguishing the two is the entire point of the question.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "A particle moves with velocity `v(t) = t² − 4` for `0 ≤ t ≤ 3`. Find the total distance it travels."

### Average value of a function

- **What it asks:** Find the average (mean) value of a function `f` on an interval `[a, b]`.
- **Solve approach:** `f_avg = (1/(b − a)) ∫ₐᵇ f dx`; occasionally paired with the Mean Value Theorem for integrals, i.e. finding a `c` where `f(c)` equals that average.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The average value of `f(x) = sin x` on `[0, π]` is …"

### Accumulated net change from a rate

- **What it asks:** Given a rate of change, find the total accumulated quantity, or the final value given an initial value.
- **Solve approach:** Net change `= ∫ (rate) dt` by the Fundamental Theorem; the final value is the initial value plus that integral. The skill is reading the applied setup as a definite integral of a rate.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "Water flows into a tank at a rate of `r(t) = 3t` liters/min for `0 ≤ t ≤ 4`. How many liters accumulate?"

### Area or volume as a function of a parameter

- **What it asks:** A region or solid depends on a parameter `a`; find the parameter that yields a specified area/volume, or the value that maximizes/minimizes it — a signature "combine two topics" twist.
- **Solve approach:** Write the area/volume as an integral, evaluate it to a formula in `a`, then solve the resulting equation or differentiate and set the derivative to zero. The integral is only the first half of the problem.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "For `b > 0`, the region bounded by `y = bx − x²` and the x-axis has area 36. Find `b`."
