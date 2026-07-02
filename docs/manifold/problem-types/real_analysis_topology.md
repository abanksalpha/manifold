# Real analysis: continuity & topology of ℝⁿ — GRE problem types

Scope: recurring theory/counterexample ("which must be true") patterns on the GRE Mathematics Subject Test for continuity, the point-set topology of ℝ and ℝⁿ, and the behavior of continuous/differentiable/integrable functions, grouped by the boundary sub-skills below. Abstract metric/general topology and sequence convergence are separate topics handled by other agents and are excluded here.

> **Orientation & honesty notes.** This is an _additional-topics_, _recognize_-tier topic: almost every item is a theory recall / counterexample question, and the dominant answer format is "which of I, II, III must be true" (or "which is false / which is a counterexample"). Difficulty is **GRE-relative** — computation-strong test-takers tend to find these among the harder items because they reward knowing theorems and their standard counterexamples rather than grinding algebra. Frequencies (common/occasional/rare) are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep, not counted statistics; no specific question numbers are cited because they are not verifiable here. A handful of facts recur so often they are worth memorizing cold: Heine–Borel, EVT/IVT, the MVT, and "continuous ⇒ integrable."

---

## ε–δ limits & continuity (the definitions)

### 1. Reading or negating the definition of limit/continuity

- **What it asks:** Identify which symbolic statement correctly expresses \(\lim_{x\to a}f(x)=L\) or "\(f\) is continuous at \(a\)," or which statement is its correct _negation_ (what "discontinuous" means).
- **Solve approach:** Track the quantifier order \(\forall\varepsilon>0\,\exists\delta>0\,\forall x\ (|x-a|<\delta \Rightarrow |f(x)-L|<\varepsilon)\); the negation flips it to \(\exists\varepsilon>0\,\forall\delta>0\,\exists x\) with the final inequality reversed. The sequential criterion (\(x_n\to a \Rightarrow f(x_n)\to f(a)\)) is an equivalent restatement commonly offered as an answer or distractor.
- **Difficulty:** medium–hard · **Frequency:** rare–occasional
- **Example stem:** "Which of the following is equivalent to the statement that \(f\) is _not_ continuous at \(a\)?"

### 2. Uniform continuity recognition

- **What it asks:** Decide whether a given function is uniformly continuous on a specified set, or which of several functions is/are uniformly continuous.
- **Solve approach:** Every continuous function on a compact set is uniformly continuous. On unbounded or open domains, unbounded slope breaks it: \(x^2\) on \(\mathbb{R}\) and \(1/x\) on \((0,1)\) are _not_ uniformly continuous, whereas \(\sin x\) and any Lipschitz / bounded-derivative function is. The key: one \(\delta\) must work simultaneously for all points.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** "On which of the following sets is \(f(x)=1/x\) uniformly continuous: \((0,1)\), \([1,\infty)\), \((0,\infty)\)?"

---

## Properties of continuous functions on ℝ and ℝⁿ

### 3. Continuity preserved by algebraic operations and composition

- **What it asks:** Given continuous (or otherwise specified) functions, decide which combinations — sum, product, quotient, \(\max/\min\), composition, \(|f|\) — must be continuous.
- **Solve approach:** Sums, products, compositions, \(|f|\), and \(\max(f,g)\) of continuous functions are continuous; a quotient is continuous wherever the denominator is nonzero. Watch the reverse-direction traps, e.g. "\(|f|\) continuous \(\Rightarrow f\) continuous" is **false** (take \(f=+1\) on \(\mathbb{Q}\), \(-1\) off).
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** "If \(f\) and \(g\) are continuous on \(\mathbb{R}\), which must be continuous: I. \(f+g\), II. \(fg\), III. \(f\circ g\)?"

### 4. Continuity of Dirichlet/Thomae-type and point-defined functions

- **What it asks:** Determine the exact set of points at which a function defined differently on the rationals and irrationals (or by a "ruler"/Thomae rule) is continuous.
- **Solve approach:** Exploit the density of both \(\mathbb{Q}\) and its complement: such a function is continuous only where its two "rules" agree in the limit. The Dirichlet function (1 on \(\mathbb{Q}\), 0 off) is nowhere continuous; \(f(x)=x\) on \(\mathbb{Q}\) and \(0\) off is continuous only at \(0\); Thomae's function is continuous exactly at the irrationals.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** "Let \(f(x)=x\) if \(x\) is rational and \(f(x)=0\) if \(x\) is irrational. At which points is \(f\) continuous?"

### 5. Continuous functions pinned down by a dense set / local sign

- **What it asks:** Use an agreement or value hypothesis on a dense set (or at a single point) to force a global conclusion — a value at an irrational, or that \(f\) keeps its sign near a point.
- **Solve approach:** A continuous function is determined by its values on any dense set, so two continuous functions that agree on \(\mathbb{Q}\) agree everywhere; and if \(f\) is continuous with \(f(a)>0\), then \(f>0\) on a whole neighborhood of \(a\). These are staple "which must be true" facts.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** "If \(f\) is continuous on \(\mathbb{R}\) and \(f(x)=0\) for every rational \(x\), then \(f(\sqrt{2})=\) ?"

### 6. Existence of a limit / continuity at the origin in ℝ² (path test)

- **What it asks:** Decide whether \(\lim_{(x,y)\to(0,0)}f(x,y)\) exists — hence whether \(f\) can be made continuous there — for a rational expression that is \(0/0\) at the origin.
- **Solve approach:** Evaluate along several paths (\(y=0\), \(x=0\), \(y=mx\), \(y=x^2\)); if two paths give different values, the limit does not exist. Agreement along all straight lines does _not_ prove existence, but a single mismatch disproves it — which is what these items are built to exploit.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** "Does \(f(x,y)=\dfrac{xy}{x^{2}+y^{2}}\) have a limit as \((x,y)\to(0,0)\)?"

---

## Topology of ℝ and ℝⁿ (open, closed, compact, connected)

### 7. Classify a concrete subset of ℝ or ℝⁿ

- **What it asks:** Decide whether a described set is open, closed, both (clopen), or neither, and whether it is bounded, compact, and/or connected.
- **Solve approach:** In \(\mathbb{R}^n\), compact \(\Leftrightarrow\) closed and bounded (Heine–Borel); test "closed" by whether the set contains all its limit/boundary points and "open" by whether every point has a ball inside the set. Classic traps: \(\mathbb{Q}\cap[0,1]\) is neither open nor closed (so not compact), and \(\{1/n : n\in\mathbb{N}\}\) becomes compact only once the limit \(0\) is adjoined.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** "Which of the following subsets of \(\mathbb{R}^{2}\) is compact: an open disk, a closed disk, a line, or \(\{(x,y):xy=1\}\)?"

### 8. Set-operation and limit-point properties in ℝⁿ

- **What it asks:** Identify which set operations preserve openness/closedness/compactness, or reason about closures, interiors, limit points, and nested sets.
- **Solve approach:** Arbitrary unions and finite intersections of open sets are open (dually for closed); a finite union of compacts is compact and _any_ intersection of compacts is compact; a nested sequence of nonempty compact sets has nonempty intersection (Cantor). Keep "closed" and "bounded" distinct, and remember an infinite intersection of open sets need not be open (\(\bigcap_n(-\tfrac1n,\tfrac1n)=\{0\}\)).
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** "Which must be true? I. An infinite intersection of open sets is open. II. A nested sequence of nonempty closed and bounded subsets of \(\mathbb{R}\) has a common point. III. A finite union of closed sets is closed."

---

## Continuous images of compact & connected sets (EVT, IVT)

### 9. Extreme Value Theorem and its failure without compactness

- **What it asks:** Determine which conclusions (bounded; attains a maximum/minimum) must hold for a continuous function on a given domain, or pick the domain on which the guarantee fails.
- **Solve approach:** A continuous function on a compact set — a closed bounded interval in \(\mathbb{R}\) — is bounded and attains both its max and min. Drop compactness and it can fail: \(1/x\) on \((0,1]\) is unbounded; \(x\) on \((0,1)\) is bounded but attains neither extremum; \(\arctan x\) on \(\mathbb{R}\) has a supremum it never reaches.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** "\(f\) is continuous on the open interval \((0,1)\). Which must be true: I. \(f\) is bounded; II. \(f\) attains a maximum value?"

### 10. Continuous image of a compact/connected set

- **What it asks:** Identify what a continuous function _must_ map an interval or compact set onto (a "which could/couldn't be the range" item).
- **Solve approach:** Continuity sends compact to compact and connected to connected, so the continuous image of a closed bounded interval \([a,b]\) is again a closed bounded interval (or a single point) — never an open, half-open, or unbounded interval. Combining both facts, the image of \([a,b]\) is exactly some \([m,M]\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** "If \(f:[0,1]\to\mathbb{R}\) is continuous, which of the following could _not_ be its range: \([0,1]\), \(\{2\}\), \((0,1)\), \([-1,3]\)?"

### 11. Intermediate Value Theorem and the fixed-point corollary

- **What it asks:** Use continuity to guarantee a root/solution in an interval, count guaranteed sign changes, or apply the \([0,1]\to[0,1]\) fixed-point result.
- **Solve approach:** If \(f\) is continuous on \([a,b]\) and \(y\) lies between \(f(a)\) and \(f(b)\), some \(c\in[a,b]\) has \(f(c)=y\); opposite endpoint signs force a root. Corollary: any continuous \(f:[0,1]\to[0,1]\) has a fixed point, proved by applying the IVT to \(g(x)=f(x)-x\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** "For every continuous \(f:[0,1]\to[0,1]\), which must have a solution: (A) \(f(x)=0\), (B) \(f(x)=x\), (C) \(f(x)=1\)?"

---

## Differentiability & the Mean Value Theorem (theory)

### 12. Mean Value / Rolle consequences and derivative-sign facts

- **What it asks:** Draw a "which must be true" conclusion from a differentiability + derivative hypothesis: a point of prescribed slope, a bound on \(f\), monotonicity, or constancy.
- **Solve approach:** The MVT supplies \(c\) with \(f'(c)=\dfrac{f(b)-f(a)}{b-a}\); consequences include \(f'\equiv0\Rightarrow f\) constant, \(f'>0\Rightarrow f\) strictly increasing, and \(|f'|\le M\Rightarrow |f(x)-f(y)|\le M|x-y|\) (a Lipschitz bound). Rolle's theorem is the case \(f(a)=f(b)\).
- **Difficulty:** medium · **Frequency:** occasional–common
- **Example stem:** "If \(f\) is differentiable on \(\mathbb{R}\) with \(f(0)=0\) and \(f'(x)\le 2\) for all \(x\), what is the largest possible value of \(f(3)\)?"

### 13. Differentiability vs continuity and pathological counterexamples

- **What it asks:** Test the precise logical relationship among "continuous," "differentiable," and "continuously differentiable," usually by asking which statement is false or which function serves as a counterexample.
- **Solve approach:** Differentiable \(\Rightarrow\) continuous, but never the converse (\(|x|\) at \(0\)). Know the standard pathologies: \(x^{2}\sin(1/x)\) (extended by \(0\)) is differentiable everywhere but its derivative is discontinuous at \(0\); a Weierstrass-type function is continuous everywhere yet differentiable nowhere; \(x^{1/3}\) has a vertical tangent at \(0\).
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** "Which must be true? I. Differentiable at \(a\) implies continuous at \(a\). II. Continuous at \(a\) implies differentiable at \(a\). III. If \(f\) is differentiable everywhere, \(f'\) is continuous."

---

## Riemann integrability criteria

### 14. Which functions are Riemann integrable

- **What it asks:** Decide whether a bounded function on \([a,b]\) is Riemann integrable, or which of several functions is/are integrable.
- **Solve approach:** Continuous \(\Rightarrow\) integrable; monotone \(\Rightarrow\) integrable; bounded with only finitely many (more generally, measure-zero) discontinuities \(\Rightarrow\) integrable. Boundedness is required, and the Dirichlet function (1 on \(\mathbb{Q}\), 0 off) is the canonical _non_-integrable example — its upper sums are \(1\) and lower sums \(0\) on every partition.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** "Which is Riemann integrable on \([0,1]\): I. a step function, II. the Dirichlet function, III. a bounded function with a single jump discontinuity?"

### 15. Integral-of-a-continuous-function theory (FTC recognition)

- **What it asks:** Identify the true statements about \(F(x)=\int_a^x f(t)\,dt\), or about how integrability relates to continuity and differentiability.
- **Solve approach:** If \(f\) is continuous, then \(F\) is \(C^{1}\) with \(F'=f\) (Fundamental Theorem). If \(f\) is merely integrable, \(F\) is still continuous (Lipschitz when \(f\) is bounded) but need not be differentiable where \(f\) jumps. "Integrable" does not imply "continuous," and \(F'=f\) at a point requires \(f\) continuous there.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** "If \(f\) is Riemann integrable on \([0,1]\) and \(F(x)=\int_0^x f\), which must be true: (A) \(F\) is continuous, (B) \(F\) is differentiable, (C) \(F'=f\) everywhere?"

---

## True/false & counterexample items (cross-cutting)

### 16. Match the property to its canonical counterexample

- **What it asks:** A multi-statement (I/II/III) item where each choice is decided by whether you can produce or reject the standard counterexample — spanning continuity, differentiability, compactness, connectedness, and integrability at once.
- **Solve approach:** Carry a compact counterexample bank and test each statement against it: \(|x|\) (continuous, not differentiable), \(x^{2}\sin(1/x)\) (differentiable, not \(C^{1}\)), Dirichlet (nowhere continuous, not integrable), \(1/x\) on \((0,1)\) (continuous, unbounded, not uniformly continuous), \(\{1/n\}\) (bounded, not closed), and two disjoint intervals / the topologist's sine curve (connectedness edge cases). A single counterexample kills a "must be true."
- **Difficulty:** hard · **Frequency:** common (the dominant format for this topic)
- **Example stem:** "Which is/are true? I. Every bounded function on \([0,1]\) is Riemann integrable. II. A continuous bijection \([0,1]\to[0,1]\) is monotonic. III. A continuous function on a bounded subset of \(\mathbb{R}\) is bounded."
