# Multivariable integral calculus — GRE problem types

Scope: multiple-integration patterns on the GRE Mathematics Subject Test — double integrals (Cartesian & polar), reversing the order of integration, triple integrals (cylindrical & spherical), change of variables & the Jacobian, and setting up regions of integration; line/surface integrals and the integral theorems (Green/Stokes/Divergence) are a separate vector-calculus topic.

---

## Double integrals (Cartesian & polar)

### Iterated double integral over a rectangle

- **What it asks:** Evaluate `∬_R f(x,y) dA` over a rectangle `[a,b]×[c,d]`, usually with a simple or separable integrand.
- **Solve approach:** Integrate one variable at a time (Fubini), holding the other constant; if `f(x,y) = g(x)h(y)`, split into the product of two single integrals `(∫g)(∫h)`.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "`∫₀¹ ∫₀^{π/2} x sin y \, dy \, dx` equals …"

### Double integral over a curve-bounded region (Type I / Type II)

- **What it asks:** Evaluate `∬_R f \, dA` where `R` is bounded by curves (e.g., `y = x²` and `y = x`), so the inner limits are functions of the outer variable.
- **Solve approach:** Sketch `R`; pick Type I (`dy dx`, inner limits are the top/bottom curves) or Type II (`dx dy`, inner limits are the left/right curves); get the outer constant limits from the curve intersections.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "`∬_R x \, dA`, where `R` is bounded by `y = x` and `y = x²`, equals …"

### Volume under a surface / between two surfaces

- **What it asks:** Find the volume under `z = f(x,y)` above a region, or between two surfaces `z = top` and `z = bottom`.
- **Solve approach:** Volume `= ∬_R (top − bottom) \, dA`; find the shadow region `R` from where the surfaces meet; a circular shadow usually signals a switch to polar.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "The volume of the solid under `z = 4 − x² − y²` and above the `xy`-plane is …"

### Conversion to polar coordinates

- **What it asks:** Evaluate a double integral over a disk, annulus, or sector, or with an integrand like `x²+y²` or `e^{−(x²+y²)}`, where Cartesian evaluation is awkward or impossible.
- **Solve approach:** Substitute `x = r cos θ`, `y = r sin θ`, `x²+y² = r²`, and — the step most often missed — replace `dA` with `r \, dr \, dθ`; the extra `r` frequently makes integrands such as `e^{−r²}` elementary.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "`∬_D e^{−(x²+y²)} \, dA` over the disk `x²+y² ≤ a²` equals …"

### Area of a planar region via a double integral

- **What it asks:** Express or compute the area of a region as `∬_R 1 \, dA`, often for a polar/sector region.
- **Solve approach:** Set the integrand to 1 and match the coordinate system to the region; in polar the area element is `r \, dr \, dθ`, so `area = ∬_R r \, dr \, dθ`. It collapses to a single integral of the gap between the bounding curves.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "`∬_R \, dA` over the polar region `1 ≤ r ≤ 2`, `0 ≤ θ ≤ π/2` (its area) is …"

### Symmetry / odd-integrand vanishing shortcut

- **What it asks:** Recognize — usually to skip computation — that an integral is `0` because the integrand is odd in a variable over a region symmetric in that variable.
- **Solve approach:** If `R` is symmetric about the `y`-axis and `f(−x,y) = −f(x,y)`, then `∬_R f \, dA = 0` (similarly for `y`, or for radial/central symmetry); drop the vanishing terms and integrate only the surviving even part.
- **Difficulty:** medium. **Frequency:** occasional (a time-saving GRE pattern).
- **Example stem:** "`∬_D (x³ + y) \, dA` over the disk `x²+y² ≤ 1` equals …"

### Average value (and mass / center of mass) over a region

- **What it asks:** Find the average value of `f` over `R`; a rarer applications variant gives a density and asks for mass or a center-of-mass coordinate.
- **Solve approach:** `f_avg = (1/Area(R)) ∬_R f \, dA`. For a lamina: `mass = ∬_R ρ \, dA`, `x̄ = (1/mass)∬_R x ρ \, dA` (and likewise `ȳ`); use symmetry to kill a coordinate.
- **Difficulty:** medium. **Frequency:** occasional (average value); rare (mass / center of mass).
- **Example stem:** "The average value of `f(x,y) = x + y` over the unit square `0 ≤ x ≤ 1`, `0 ≤ y ≤ 1` is …"

---

## Switching the order of integration

### Reverse the order to make the integral solvable

- **What it asks:** Evaluate an iterated integral whose inner antiderivative is nonelementary in the given order — integrands such as `e^{y²}`, `e^{x²}`, `sin x / x`, or `cos(x²)` — so the order must be swapped.
- **Solve approach:** Read the region off the given limits and sketch it, then rewrite with the order reversed so the new inner integral is elementary, and evaluate.
- **Difficulty:** medium–hard. **Frequency:** common (a signature GRE setup — nonelementary inner integrand is the tell).
- **Example stem:** "`∫₀¹ ∫_x^1 e^{y²} \, dy \, dx` equals …"

### Rewrite / match the swapped iterated integral (setup only)

- **What it asks:** Select the iterated integral, with the order of integration reversed, that equals a given one — often without evaluating.
- **Solve approach:** Convert the given limits into a description of the region, then re-express it with the other variable outer: new constant outer limits from the region's extent, new inner limits from the boundary curves; match to the choices.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Reversing the order of integration, `∫₀¹ ∫_{√x}^1 f(x,y) \, dy \, dx` equals which of the following?"

---

## Triple integrals (cylindrical & spherical)

### Volume of a solid via a triple integral (Cartesian)

- **What it asks:** Find the volume of a solid bounded by planes/surfaces as `∭_E 1 \, dV`.
- **Solve approach:** Project the solid onto a coordinate plane for the outer two limits, take the top/bottom surfaces for the inner limit, and integrate 1; choose the integration order that keeps limits simplest.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The volume of the solid bounded by `x = 0`, `y = 0`, `z = 0`, and `x + y + z = 1` is …"

### Cylindrical coordinates for axially symmetric solids

- **What it asks:** Integrate over a solid with circular symmetry about an axis — cylinders, paraboloids, cones — for a volume or a triple integral of `f`.
- **Solve approach:** Use `x = r cos θ`, `y = r sin θ`, `z = z` with `dV = r \, dz \, dr \, dθ`; `x²+y² = r²` and the `r` factor tame the circular cross-sections; integrate `z` first between the bounding surfaces.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The volume of the solid bounded below by `z = x² + y²` and above by `z = 4` is …"

### Spherical coordinates for balls & cones

- **What it asks:** Integrate over a ball, spherical shell, or a region between a cone and a sphere, or integrate a radially symmetric `f` over such a region.
- **Solve approach:** Use `ρ, φ, θ` with `dV = ρ² sin φ \, dρ \, dφ \, dθ`; a cone `z = √(x²+y²)` becomes `φ = π/4` and a sphere `x²+y²+z² = a²` becomes `ρ = a`; a radial integrand `f(ρ)` separates from the `φ` and `θ` integrals.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "`∭_B (x²+y²+z²) \, dV` over the ball `x²+y²+z² ≤ a²` equals …"

---

## Change of variables & the Jacobian

### Compute a Jacobian determinant

- **What it asks:** Given a transformation `x = x(u,v)`, `y = y(u,v)` (or a three-variable version, including the polar/cylindrical/spherical maps), compute the Jacobian `∂(x,y)/∂(u,v)`.
- **Solve approach:** Form the matrix of first partials and take its determinant; this returns `r` for polar and `ρ² sin φ` for spherical. Note which direction is asked — `∂(x,y)/∂(u,v)` versus its reciprocal `∂(u,v)/∂(x,y)`.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "For `x = u² − v²`, `y = 2uv`, the Jacobian `∂(x,y)/∂(u,v)` is …"

### Evaluate a double integral via a linear / affine change of variables

- **What it asks:** Evaluate `∬_R f \, dA` over a slanted region — a parallelogram bounded by lines like `x + y = c` and `x − y = c` — where a substitution rectangularizes the region or the integrand.
- **Solve approach:** Choose `u, v` (e.g., `u = x + y`, `v = x − y`) so `R` becomes a rectangle; rewrite `f` in `u, v`, multiply by `|∂(x,y)/∂(u,v)|`, and integrate over the simple `uv`-rectangle.
- **Difficulty:** hard. **Frequency:** occasional/rare.
- **Example stem:** "With `u = x + y`, `v = x − y`, the integral `∬_R (x + y)² \, dA` over the region `0 ≤ x+y ≤ 2`, `0 ≤ x−y ≤ 2` becomes …"

---

## Setting up regions of integration

### Identify the region from given limits

- **What it asks:** Given an iterated integral, identify or sketch the region of integration (or choose the matching picture).
- **Solve approach:** Translate the outer constant limits and inner variable limits into inequalities, graph the bounding curves, and determine which side of each curve the limits select.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The region of integration for `∫₀¹ ∫_{x²}^{x} f(x,y) \, dy \, dx` is …"

### Set up the iterated integral for a described region

- **What it asks:** Given a region described in words or by a sketch, write the correct iterated integral with its limits — frequently the answer itself, not just a step.
- **Solve approach:** Choose Type I vs Type II by which order avoids splitting the region; read the outer constant range from the region's extent and the inner limits from the bounding curves; split into a sum of integrals if the boundary description changes partway.
- **Difficulty:** medium. **Frequency:** occasional/common.
- **Example stem:** "Which iterated integral gives `∬_R f \, dA` for the triangle with vertices `(0,0)`, `(1,0)`, `(1,1)`?"
