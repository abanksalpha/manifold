# Geometry — GRE problem types

Scope: classical Euclidean plane and solid geometry on the GRE Mathematics Subject Test — triangle relations, circle theorems, polygon angles, areas/perimeters, solid surface areas/volumes, and 3D metric geometry; coordinate/analytic geometry (lines, conics, polar/parametric, and the distance formula in the plane and in 3-space) is a separate topic and is excluded here.

> **Orientation & honesty notes.** Pure classical geometry is a _small_ slice of this exam: a handful of standalone questions plus frequent use as embedded tooling inside calculus, trigonometry, and coordinate-geometry problems (a related-rates cone, an optimization box, a triangle set up for an integral). So several entries below are marked _common as tooling_ even when _rare/occasional as a headline question_. Difficulty is **GRE-relative**, and the test is **no-calculator**, so numbers are engineered to stay clean (Pythagorean triples, tidy radicals, `30-60-90` / `45-45-90` triangles). Frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep, not counted statistics; no specific question numbers are cited because they are not verifiable here.

---

## Triangle geometry

### Special right triangles (30-60-90 and 45-45-90)

- **What it asks:** Use the fixed side ratios of a 30-60-90 or 45-45-90 triangle to find a missing length, a height, or an exact trig value — often as a step inside a larger figure or a calculus setup.
- **Solve approach:** Memorize `1 : √3 : 2` (30-60-90) and `1 : 1 : √2` (45-45-90); drop an altitude to split an equilateral triangle into two 30-60-90's (height `= (√3/2)·side`) or cut a square along its diagonal into two 45-45-90's. Recognize the ratio instead of re-deriving with the Pythagorean theorem.
- **Difficulty:** easy. **Frequency:** common (pervasive as tooling).
- **Example stem:** "In a right triangle the hypotenuse is 10 and one acute angle is 30°. The length of the shorter leg is …"

### Similar triangles and proportional segments

- **What it asks:** Recognize that two triangles are similar and use proportional sides to find a missing length; occasionally to compare their areas.
- **Solve approach:** Detect similarity by AA (parallel lines, a shared angle, or a nested triangle), write the ratio of corresponding sides, and solve the proportion. Recall that similar figures have areas in the ratio `k²`, where `k` is the linear scale factor.
- **Difficulty:** easy–medium. **Frequency:** occasional standalone (common embedded, e.g. related rates).
- **Example stem:** "A 6-foot person standing 12 feet from a lamppost casts a 4-foot shadow. How tall is the lamppost?"

### General triangle area and metric relations

- **What it asks:** Find the area, a side, or an angle of a non-right triangle from mixed given data (two sides and the included angle, three sides, an angle–side pair).
- **Solve approach:** Pick the matching tool — `area = ½·base·height`, `area = ½·a·b·sin C`, or Heron's `√(s(s−a)(s−b)(s−c))`; use the law of cosines `c² = a² + b² − 2ab·cos C` for a side/angle and the law of sines for angle–side pairs. Right triangles reduce to the Pythagorean theorem, and an equilateral triangle has area `(√3/4)·s²`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "A triangle has sides of length 5 and 8 with a 60° angle between them. Its area is …"

### Angle relationships and angle chasing

- **What it asks:** Find an unknown angle from angle-sum, isosceles, exterior-angle, or parallel-line (transversal) relationships in a figure.
- **Solve approach:** Chain the basic rules: a triangle's angles sum to `180°`, base angles of an isosceles triangle are equal, an exterior angle equals the sum of the two remote interior angles, and a transversal of parallel lines gives equal alternate/corresponding angles (and supplementary co-interior angles).
- **Difficulty:** easy–medium. **Frequency:** rare standalone (occasional embedded).
- **Example stem:** "Lines `AB` and `CD` are parallel; a transversal meets `AB` at 50°. The corresponding angle at `CD` is …"

---

## Circle theorems

### Inscribed and central angles (including Thales' semicircle)

- **What it asks:** Relate inscribed angles, central angles, and their intercepted arcs; the signature special case is that an angle inscribed in a semicircle is a right angle.
- **Solve approach:** A central angle equals its intercepted arc, and an inscribed angle is half its intercepted arc — so inscribed angles subtending the same arc are equal, and a triangle inscribed in a circle with a diameter as one side is right-angled. Combine with the isosceles triangles formed by two radii.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Points `A`, `B`, `C` lie on a circle with `AB` a diameter. If arc `BC` measures 70°, then angle `BAC` is …"

### Chords, secants, tangents, and power of a point

- **What it asks:** Find a segment length from the products formed by chords, secants, or tangents to a circle, or the length of a tangent drawn from an external point.
- **Solve approach:** Apply power of a point: intersecting chords give `a·b = c·d`; two secants give `(whole)·(external) = (whole)·(external)`; a tangent–secant pair gives `t² = (whole)·(external)`. A tangent is perpendicular to the radius at its point of contact, so tangent-length problems often pair with the Pythagorean theorem.
- **Difficulty:** medium. **Frequency:** rare–occasional.
- **Example stem:** "Two chords of a circle intersect; one is divided into segments of length 3 and 8, the other into a segment of length 4 and an unknown `x`. Find `x`."

### Arc length and sector area

- **What it asks:** Compute the length of an arc, the area of a sector or circular segment, or the perimeter of a region bounded by circular arcs.
- **Solve approach:** Take the corresponding fraction of the whole circle: arc `= (θ/360°)·2πr` (or `rθ` in radians) and sector area `= (θ/360°)·πr²` (or `½r²θ`); a circular segment is the sector minus the triangle formed by the two radii. Mind degrees versus radians.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "A sector of a circle of radius 6 has central angle 60°. Its area is …"

---

## Polygon angle sums and regular polygons

### Interior and exterior angle sums

- **What it asks:** Find an interior or exterior angle, or the number of sides `n`, of a (usually regular) polygon.
- **Solve approach:** Interior angles sum to `(n−2)·180°`, so each interior angle of a regular `n`-gon is `(n−2)·180°/n`; exterior angles always sum to `360°`, so each is `360°/n`. Set up the relevant equation and solve for the unknown.
- **Difficulty:** easy–medium. **Frequency:** rare–occasional.
- **Example stem:** "Each interior angle of a regular polygon measures 150°. How many sides does it have?"

### Regular-polygon measurements (area, apothem, diagonals)

- **What it asks:** Find the area, apothem, side length, or number of diagonals of a regular polygon, or relate it to its inscribed or circumscribed circle.
- **Solve approach:** Use `area = ½·apothem·perimeter`; split the polygon into `n` congruent isosceles triangles from the center (central angle `360°/n`) and get the apothem via special-triangle or trig ratios. The number of diagonals is `n(n−3)/2`.
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "A regular hexagon has side length 2. Its area is …"

---

## Areas and perimeters of plane figures

### Areas and perimeters of plane figures (composite / shaded regions)

- **What it asks:** Compute the area or perimeter of a standard figure (triangle, rectangle, parallelogram, trapezoid, circle) or of a composite or shaded region assembled from several such pieces.
- **Solve approach:** Decompose the region into standard pieces and add or subtract their areas (a shaded region is typically the outer shape minus a hole); keep the core formulas ready (trapezoid `= ½(b₁+b₂)·h`, circle `= πr²`). Exploit symmetry to avoid heavy computation.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "A circle of radius 2 is removed from a 6-by-6 square. The area of the region that remains is …"

### Inscribed and circumscribed plane figures

- **What it asks:** Relate the dimensions or areas of one figure inscribed in or circumscribed about another (a square in a circle, a circle in a square, a triangle in a circle).
- **Solve approach:** Find the measurement shared by the two figures — a diagonal that is a diameter, a radius that is an apothem, a side that is a chord — express both areas through it, and take the ratio. A square inscribed in a circle has diagonal `= 2r`; a circle inscribed in a square has diameter `= side`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "A square is inscribed in a circle of radius `r`. The ratio of the square's area to the circle's area is …"

---

## Surface areas and volumes of solids

### Volume and surface area of standard solids

- **What it asks:** Compute the volume or surface area of a prism, cylinder, cone, pyramid, or sphere, or recover a dimension from a given volume or area.
- **Solve approach:** Know the formulas cold: cylinder `V = πr²h`; cone `V = ⅓πr²h`; sphere `V = (4/3)πr³`, surface `= 4πr²`; prism `V = (base area)·h` and pyramid `V = ⅓(base area)·h`. For a cone's lateral surface use slant height `ℓ = √(r²+h²)`. Check which faces are actually included (open versus closed solid).
- **Difficulty:** easy–medium. **Frequency:** occasional (common embedded in calculus).
- **Example stem:** "A cone has base radius 3 and height 4. Its total surface area is …"

### Scaling laws for area and volume

- **What it asks:** Determine how area or volume changes when a figure or solid is scaled, or compare two similar solids — a frequent conceptual trap.
- **Solve approach:** Under a linear scale factor `k`, lengths scale by `k`, areas and surface areas by `k²`, and volumes by `k³`. Read it backwards too: a volume ratio of `8 : 1` means a linear ratio of `2 : 1`. Set up the ratio directly rather than recomputing every dimension.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "If the radius of a sphere is tripled, its volume is multiplied by …"

### Inscribed / circumscribed solids and cross-sections

- **What it asks:** Relate a solid inscribed in or circumscribed about another (a sphere in a cube, a cylinder in a cone, a cone in a sphere), or identify/measure a plane cross-section of a solid.
- **Solve approach:** Locate the dimension that couples the two solids (a sphere inscribed in a cube has diameter `= edge`; a sphere circumscribing a cube has diameter `= space diagonal`), then form the requested volume or surface ratio. For cross-sections, picture the intersection — a plane parallel to a cone's base gives a circle, one through the apex gives a triangle.
- **Difficulty:** medium–hard. **Frequency:** rare–occasional.
- **Example stem:** "A sphere is inscribed in a cube of edge 2. The ratio of the sphere's volume to the cube's volume is …"

---

## 3D distance and solid geometry

### Diagonals, distances, and angles in solids

- **What it asks:** Find the space diagonal or a face diagonal of a rectangular box, the distance between two vertices, or an angle between diagonals, edges, or faces of a solid.
- **Solve approach:** Face diagonal `= √(a²+b²)`; space diagonal of a box `= √(a²+b²+c²)` (a two-step Pythagorean theorem). For an angle, build a right triangle inside the solid — e.g. a space diagonal, its projection on the base, and a vertical edge — and finish with trig. (The distance formula in coordinate 3-space belongs to the coordinate-geometry topic.)
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "A rectangular box has edge lengths 1, 2, and 2. The length of its longest interior diagonal is …"
