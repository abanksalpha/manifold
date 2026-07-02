# Metric & general topology — GRE problem types

Scope: recurring point-set-topology and metric-space patterns on the GRE Mathematics Subject Test — a small "recognize"-tier slice of the additional-topics 25%, dominated by abstract "which of the following is/are true" items about open/closed/compact/connected sets and about specific (often nonstandard) topologies; neighboring real-analysis continuity theory on \(\mathbb{R}/\mathbb{R}^n\) (ε–δ, sequences/series) is handled by other topics.

---

## Open & closed sets, interior, closure, boundary

### 1. Classify a subset as open, closed, both, or neither

- **What it asks:** Given an explicit subset of \(\mathbb{R}\) (or \(\mathbb{R}^n\)), decide whether it is open, closed, both (clopen), or neither.
- **Solve approach:** Check the definitions directly — open ⟺ every point has a neighborhood inside the set; closed ⟺ it contains all its limit points (equivalently, the complement is open). Keep the standard exemplars ready: half-open intervals are neither; \(\{1/n:n\in\mathbb{Z}^+\}\) is neither (missing its limit 0) but \(\{0\}\cup\{1/n\}\) is closed; \(\mathbb{Q}\) is neither; \(\varnothing\) and \(\mathbb{R}\) are clopen.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** Which of the following subsets of \(\mathbb{R}\) is closed but not open: \([0,1)\), \(\{1/n:n\in\mathbb{Z}^+\}\), \(\{0\}\cup\{1/n:n\in\mathbb{Z}^+\}\), or \(\mathbb{Q}\)?

### 2. Compute the closure, interior, or boundary (and limit points)

- **What it asks:** Find the closure \(\bar{A}\), interior \(A^\circ\), boundary \(\partial A\), or the set of limit points of a given set.
- **Solve approach:** Interior = the points of \(A\) having a neighborhood contained in \(A\); closure = \(A\) together with its limit points; boundary = \(\bar{A}\setminus A^\circ=\bar{A}\cap\overline{A^c}\). Signature cases: \(\overline{\mathbb{Q}}=\mathbb{R}\) while \(\mathbb{Q}^\circ=\varnothing\), so \(\partial\mathbb{Q}=\mathbb{R}\); the closure of \(\{1/n\}\) just adjoins the point 0.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** In \(\mathbb{R}\), the boundary of \(\mathbb{Q}\cap(0,1)\) is which set?

### 3. True/false about open/closed set operations

- **What it asks:** A "which of I, II, III is/are true" item on the axioms — which unions/intersections of open (or closed) sets stay open (or closed), plus closure/interior identities.
- **Solve approach:** Anchor to the topology axioms: arbitrary unions and _finite_ intersections of open sets are open (so an arbitrary intersection can fail — \(\bigcap_n(-\tfrac1n,\tfrac1n)=\{0\}\)); dually, arbitrary intersections and finite unions of closed sets are closed. Test each statement against a fast counterexample.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which are true? (I) An arbitrary intersection of open sets is open. (II) A finite union of closed sets is closed. (III) \(\overline{A\cup B}=\bar{A}\cup\bar{B}\).

---

## Metric spaces & completeness

### 4. Decide whether a metric space is complete

- **What it asks:** Given a metric space \((X,d)\), determine whether every Cauchy sequence in \(X\) converges to a point of \(X\).
- **Solve approach:** Hunt for a Cauchy sequence whose limit escapes \(X\): \(\mathbb{Q}\) and half-open/open intervals like \((0,1]\) are incomplete (e.g. \(1/n\to0\notin(0,1]\)), as is \(\{1/n\}\); \(\mathbb{R}^n\), closed intervals, and any closed subset of a complete space are complete. Remember completeness is a _metric_, not topological, property.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** With the usual metric, which of the following is complete: \((0,1)\), \(\mathbb{Q}\), \([0,1]\), or \(\{1/n:n\in\mathbb{Z}^+\}\)?

### 5. Decide whether a given function is a metric

- **What it asks:** Test whether a proposed distance function satisfies the metric axioms (usually the question is which axiom fails).
- **Solve approach:** Check positivity/identity of indiscernibles, symmetry, and the triangle inequality \(d(x,z)\le d(x,y)+d(y,z)\); the triangle inequality (or identity of indiscernibles) is the usual failure point — \(d(x,y)=(x-y)^2\) fails triangle, \(d(x,y)=|x^2-y^2|\) fails identity. The discrete metric (\(d(x,y)=1\) for \(x\neq y\)) is the standard "yes."
- **Difficulty:** medium · **Frequency:** rare–occasional
- **Example stem:** Which of the following defines a metric on \(\mathbb{R}\): \(|x-y|^{2}\), \(|x-y|^{1/2}\), or \(|x^{2}-y^{2}|\)?

---

## Topological spaces, bases & nonstandard topologies

### 6. Verify (or count) topologies on a set

- **What it asks:** Decide whether a given collection of subsets is a topology, or count how many of several collections (or how many distinct topologies on a small finite set) qualify.
- **Solve approach:** Check the three axioms: the collection contains \(\varnothing\) and \(X\), is closed under arbitrary unions, and is closed under finite intersections. A single missing union or intersection disqualifies it; a stray basis can be completed by taking all unions.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** For \(X=\{a,b,c\}\), which of the following collections of subsets of \(X\) is a topology?

### 7. Properties within a named nonstandard topology

- **What it asks:** Given a specific topology — discrete, indiscrete (trivial), cofinite (finite-complement), order, or lower-limit — identify its open/closed sets or a property (compact? connected? Hausdorff?).
- **Solve approach:** Work from each topology's basis/definition: in the discrete topology every set is open (hence clopen); in the indiscrete topology only \(\varnothing\) and \(X\) are open; in the cofinite topology the closed sets are exactly the finite sets and \(X\) (so it is compact and, on an infinite set, connected but not Hausdorff). Match the requested property to those open sets.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** In the cofinite topology on an infinite set \(X\), which of the following is true — that every infinite subset is closed, that \(X\) is compact, or that \(X\) is Hausdorff?

---

## Continuity in topological spaces

### 8. Continuity via preimages of open sets

- **What it asks:** Apply the topological definition of continuity (preimage of every open set is open) to test a map between spaces with given topologies, or to judge related true/false statements.
- **Solve approach:** Use "\(f\) is continuous ⟺ \(f^{-1}(U)\) is open for every open \(U\)" (equivalently, preimages of closed sets are closed). Edge cases resolve at once: every map _out of_ a discrete space is continuous, and every map _into_ an indiscrete space is continuous.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** If \(X\) carries the discrete topology and \(Y\) is an arbitrary topological space, which of the following must hold for every function \(f:X\to Y\)?

---

## Compactness

### 9. Decide compactness in \(\mathbb{R}^n\) (Heine–Borel)

- **What it asks:** Determine whether a given subset of \(\mathbb{R}^n\) is compact.
- **Solve approach:** In \(\mathbb{R}^n\), compact ⟺ closed and bounded (Heine–Borel). Reject anything unbounded (\(\mathbb{R}\), \([0,\infty)\), \(\mathbb{Z}\)) or not closed (\((0,1)\), \(\{1/n\}\) without its limit); accept closed bounded sets like \([0,1]\) or \(\{0\}\cup\{1/n\}\).
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** Which of the following subsets of \(\mathbb{R}\) is compact: \((0,1]\), \([0,1]\), \(\mathbb{Z}\), or \(\{1/n:n\in\mathbb{Z}^+\}\)?

### 10. True/false about compact sets

- **What it asks:** A "which is/are true" item on compactness properties and the open-cover definition.
- **Solve approach:** Anchor to the core facts: compact = every open cover has a finite subcover; a closed subset of a compact space is compact; a compact subset of a Hausdorff space is closed; the continuous image of a compact set is compact (⇒ the extreme value theorem); finite unions of compact sets are compact. Beware the trap that "closed and bounded ⇒ compact" holds only in \(\mathbb{R}^n\), not in a general metric space.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which must be true? (I) A closed subset of a compact space is compact. (II) The continuous image of a compact set is compact. (III) A closed, bounded subset of any metric space is compact.

---

## Connectedness

### 11. Decide whether a set or space is connected

- **What it asks:** Determine whether a given set (or a space with a given topology) is connected or path-connected.
- **Solve approach:** In \(\mathbb{R}\) the connected sets are _exactly_ the intervals; a set that splits into two nonempty relatively-open pieces is disconnected. \(\mathbb{Q}\) and \(\mathbb{Z}\) are totally disconnected; a union of disjoint closed intervals is disconnected. For open subsets of \(\mathbb{R}^n\), connected and path-connected coincide.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which of the following subspaces of \(\mathbb{R}\) is connected: \(\mathbb{Q}\), \([0,1]\cup[2,3]\), \([0,1]\), or \(\mathbb{Z}\)?

### 12. True/false about connectedness

- **What it asks:** A "which is/are true" item on how connectedness behaves and what it implies.
- **Solve approach:** Core facts: the continuous image of a connected set is connected (this is the topological form of the intermediate value theorem); a union of connected sets sharing a common point is connected; the closure of a connected set is connected. Directional trap: path-connected ⇒ connected, but not conversely (topologist's sine curve).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** For a continuous \(f:X\to Y\), which must be true? (I) If \(X\) is connected, then \(f(X)\) is connected. (II) If \(X\) is connected, then \(X\) is path-connected. (III) If \(f(X)\) is connected, then \(X\) is connected.

---

## Homeomorphism-invariant properties

### 13. Distinguish topological from metric properties

- **What it asks:** Identify which properties are preserved by homeomorphism (topological invariants) versus those that are only metric.
- **Solve approach:** Invariant under homeomorphism: compactness, connectedness, the Hausdorff property, and the number of connected components. Not invariant: completeness, boundedness, total boundedness, and being open/closed as a subset. Signature witness: \((0,1)\) is homeomorphic to \(\mathbb{R}\), yet \(\mathbb{R}\) is complete and unbounded while \((0,1)\) is neither.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** Which property of a metric space is preserved under homeomorphism: completeness, boundedness, compactness, or total boundedness?

### 14. Decide which spaces are homeomorphic

- **What it asks:** Determine whether two given spaces are homeomorphic, or pick out the homeomorphic pair, usually among intervals, \(\mathbb{R}\), circles, and simple figures.
- **Solve approach:** Argue "yes" by naming a bicontinuous bijection; argue "no" by exhibiting a topological invariant that differs — compactness (\([0,1]\) vs \((0,1)\)), connectedness, or a cut-point count (\(\mathbb{R}\) vs the circle \(S^1\); \([0,1)\) vs \((0,1)\), since removing an interior point disconnects but removing the endpoint does not).
- **Difficulty:** medium–hard · **Frequency:** rare–occasional
- **Example stem:** Which pair is homeomorphic: \([0,1]\) and \((0,1)\); \((0,1)\) and \(\mathbb{R}\); \([0,1)\) and \((0,1)\); or \(\mathbb{R}\) and \(S^1\)?
