# Real analysis: sequences & series — GRE problem types

Scope: recurring real-analysis patterns about sequences and series on the GRE Mathematics Subject Test, organized by the seven boundary sub-skills below; point-set/metric topology and continuity theory are separate topics, and the mechanical numeric-series convergence tests (ratio, root, comparison, integral, alternating) live under the calculus "series" topic, so they are excluded here.

> **Orientation & honesty notes.** This is an _additional-topics, recognize-tier_ slice: only a handful of questions per form, and the dominant format is the true/false **"which of the following must be true"** item (often numbered I/II/III), so most types below are recognition/counterexample items rather than long computations. Difficulty is **GRE-relative** and the exam is **no-calculator**, so numeric answers stay clean. Frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep, not counted statistics; no specific question numbers are cited because they are not verifiable here. Real recurring patterns only.

---

## Suprema, infima & completeness of ℝ

### 1. Supremum / infimum of an explicit set

- **What it asks:** Given a concretely described set of reals (often indexed by one or two integers), find its supremum or infimum, or decide whether the extremum is attained (i.e., is a max/min).
- **Solve approach:** Separate the "candidate value" from "attainment": push the index to its extreme to locate the bound, then check whether any element equals it. A supremum that is never reached (e.g., an infimum of 0 for strictly positive terms) is the classic trap; watch for sets defined by a strict inequality where the bound is a limit point but not a member.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** For \(S=\{\tfrac1m+\tfrac1n : m,n\in\mathbb{Z}^{+}\}\), determine \(\sup S\) and \(\inf S\), and state whether each is attained.

### 2. Completeness / least-upper-bound property recognition

- **What it asks:** A true/false item asking which property characterizes the completeness of ℝ, or which statement holds in ℝ but fails in ℚ.
- **Solve approach:** Pin the least-upper-bound (completeness) axiom: _every nonempty subset bounded above has a supremum in ℝ_. Reject distractors that confuse it with the Archimedean property or density of ℚ (both true in ℚ too). The standard witness that ℚ is not complete is \(\{x\in\mathbb{Q}:x^2<2\}\), which is bounded above but has no rational supremum.
- **Difficulty:** medium–hard · **Frequency:** rare–occasional
- **Example stem:** Which of the following holds for ℝ but **not** for ℚ? (I) the Archimedean property; (II) every nonempty subset bounded above has a least upper bound; (III) between any two elements there is another.

---

## Convergent & Cauchy sequences

### 3. Evaluate the limit of an explicit real sequence

- **What it asks:** Compute \(\lim_{n\to\infty}a_n\) for a sequence given by a closed formula (rational in \(n\), a root difference, or a standard indeterminate form).
- **Solve approach:** Use the tool matching the form: divide by the dominant power for rational expressions; multiply by the conjugate for differences of roots; reduce to known limits such as \(n^{1/n}\to1\), \((1+\tfrac{a}{n})^{n}\to e^{a}\), and \(n\sin(1/n)\to1\). (Computational overlap with calculus; here it is framed as a sequence.)
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{n\to\infty}\left(\sqrt{n^{2}+n}-n\right)\).

### 4. Cauchy-sequence / completeness recognition

- **What it asks:** A true/false item on what "Cauchy" implies, typically testing that in ℝ the Cauchy and convergent notions coincide, and separating Cauchy from merely "consecutive terms get close."
- **Solve approach:** Hold two facts: in ℝ, _convergent ⇔ Cauchy_ (completeness), and _every convergent sequence is Cauchy_ always. Reject the common trap that \(|a_{n+1}-a_n|\to0\) implies Cauchy — the partial sums of the harmonic series are the standard counterexample. Bounded does **not** imply Cauchy (use \((-1)^n\)).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which must be true for a real sequence \(\{a_n\}\)? (I) if \(\{a_n\}\) is Cauchy it converges; (II) if \(\{a_n\}\) converges it is Cauchy; (III) if \(|a_{n+1}-a_n|\to0\) then \(\{a_n\}\) is Cauchy.

---

## Monotone & bounded sequence theorems

### 5. Limit of a recursively defined (monotone-bounded) sequence

- **What it asks:** Given a recursion such as \(a_{n+1}=f(a_n)\) (nested radical, averaging, or rational iteration) with a starting value, find \(\lim a_n\).
- **Solve approach:** Justify existence via the Monotone Convergence Theorem — show the sequence is monotone and bounded (usually by induction) — then take limits of both sides and solve the fixed-point equation \(L=f(L)\), discarding roots outside the sequence's range.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Let \(a_1=\sqrt{2}\) and \(a_{n+1}=\sqrt{2+a_n}\). Find \(\lim_{n\to\infty}a_n\).

### 6. Monotone Convergence Theorem, must-be-true form

- **What it asks:** A recognition item on exactly which hypotheses force a monotone sequence to converge (and that neither monotonicity nor boundedness alone suffices).
- **Solve approach:** State the theorem precisely: _a monotone sequence converges iff it is bounded_ (an increasing sequence converges iff bounded above). Reject "monotone ⇒ convergent" with \(a_n=n\), and "bounded ⇒ convergent" with \((-1)^n\); a bounded monotone sequence is the case that must converge.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which must be true of a monotonically increasing real sequence \(\{a_n\}\)? (I) it converges; (II) it converges iff it is bounded above; (III) it is bounded.

---

## Bolzano–Weierstrass

### 7. Convergent-subsequence existence (Bolzano–Weierstrass)

- **What it asks:** Recognize that every bounded real sequence has a convergent subsequence, or identify the subsequential limits of a concrete bounded-but-divergent sequence.
- **Solve approach:** Invoke Bolzano–Weierstrass for the existence claim (boundedness is the only hypothesis needed). To list subsequential limits of an oscillating sequence, split by the periodic/parity pattern of the index and take each branch's limit; the set of these values is exactly the set of subsequential limits.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** The sequence \(a_n=(-1)^n\dfrac{n}{n+1}\) does not converge. To what values do its convergent subsequences converge, and which theorem guarantees such a subsequence exists?

---

## limsup / liminf

### 8. Compute limsup, liminf & the set of subsequential limits

- **What it asks:** For an oscillating sequence, evaluate \(\limsup a_n\) and \(\liminf a_n\) (equivalently the largest and smallest subsequential limits).
- **Solve approach:** Identify the subsequential limits by parity or period; \(\limsup\) is their supremum and \(\liminf\) their infimum. Convergence corresponds to \(\limsup=\liminf\). A damped oscillation like \((-1)^n(1+\tfrac1n)\) still has \(\pm1\) as its extreme subsequential limits.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** Find \(\limsup_{n\to\infty}a_n\) and \(\liminf_{n\to\infty}a_n\) for \(a_n=(-1)^n\left(1+\tfrac1n\right)\).

### 9. limsup / liminf relations, true-false

- **What it asks:** A must-be-true item on inequalities and identities involving limsup/liminf of one or two sequences.
- **Solve approach:** Keep the reliable facts: \(\liminf a_n\le\limsup a_n\) always; \(a_n\) converges iff \(\liminf a_n=\limsup a_n\); and the subadditive bound \(\limsup(a_n+b_n)\le\limsup a_n+\limsup b_n\). Reject equalities that fail for products or sums (test with \(a_n=(-1)^n\), \(b_n=(-1)^{n+1}\)).
- **Difficulty:** hard · **Frequency:** rare
- **Example stem:** For bounded real sequences \(\{a_n\},\{b_n\}\), which must be true? (I) \(\liminf a_n\le\limsup a_n\); (II) \(\limsup(a_n+b_n)=\limsup a_n+\limsup b_n\); (III) \(\{a_n\}\) converges iff \(\liminf a_n=\limsup a_n\).

---

## Uniform vs pointwise convergence of function sequences/series

### 10. Pointwise limit and test for uniform convergence

- **What it asks:** For a sequence of functions \(f_n\) on an interval, find the pointwise limit and decide whether the convergence is uniform.
- **Solve approach:** Compute \(f(x)=\lim_n f_n(x)\) pointwise, then test \(\sup_x|f_n(x)-f(x)|\to0\) for uniformity. Two fast disqualifiers: a discontinuous pointwise limit of continuous \(f_n\) cannot be uniform, and a "moving bump" whose peak height stays bounded away from 0 breaks uniformity.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** For \(f_n(x)=x^{n}\) on \([0,1]\), identify the pointwise limit and state whether \(f_n\) converges uniformly on \([0,1]\).

### 11. Which conclusions survive pointwise (vs uniform) convergence

- **What it asks:** A true/false item on which properties transfer to the limit when \(f_n\to f\) only pointwise — continuity, interchange with the integral, or interchange with the derivative.
- **Solve approach:** Recall that uniform convergence is what licenses "limit is continuous" and \(\lim\int f_n=\int\lim f_n\); pointwise alone guarantees none of these. Keep a counterexample ready: \(f_n(x)=nx(1-x^2)^n\) on \([0,1]\) has \(f_n\to0\) pointwise yet \(\int_0^1 f_n\,dx\to\tfrac12\neq0\).
- **Difficulty:** hard · **Frequency:** occasional
- **Example stem:** Suppose continuous \(f_n\to f\) pointwise on \([0,1]\). Which must be true? (I) \(f\) is continuous; (II) \(\int_0^1 f_n\to\int_0^1 f\); (III) neither need hold without uniform convergence.

### 12. Uniform convergence of a function series (Weierstrass M-test)

- **What it asks:** Decide whether a series of functions \(\sum f_n(x)\) converges uniformly on a given set.
- **Solve approach:** Apply the Weierstrass M-test: if \(|f_n(x)|\le M_n\) for all \(x\) and \(\sum M_n<\infty\), the series converges uniformly (and absolutely). Trigonometric numerators bounded by 1 over a \(1/n^2\) tail are the canonical "yes" case; a geometric series on an interval reaching the radius of convergence is the canonical "no."
- **Difficulty:** medium–hard · **Frequency:** rare–occasional
- **Example stem:** Does \(\displaystyle\sum_{n=1}^{\infty}\frac{\cos(nx)}{n^{2}}\) converge uniformly on ℝ, and what test settles it?

---

## True/false property statements about sequences (& series)

### 13. "Which must be true" implication grid (bounded / monotone / convergent / Cauchy)

- **What it asks:** The signature Roman-numeral item asking which logical implications among the core sequence properties always hold.
- **Solve approach:** Fix the one-way implications — convergent ⇒ bounded, convergent ⇔ Cauchy (in ℝ), monotone+bounded ⇒ convergent — and knock out the false converses with standard witnesses: \((-1)^n\) (bounded, not convergent), \(a_n=n\) (monotone, not bounded), \((-1)^n/n\) (convergent, not monotone).
- **Difficulty:** medium–hard · **Frequency:** occasional (the defining format for this topic)
- **Example stem:** If a real sequence \(\{a_n\}\) converges, which must be true? (I) it is bounded; (II) it is monotonic; (III) it is Cauchy.

### 14. Counterexample selection

- **What it asks:** Choose, from five candidate sequences, the one satisfying a specified combination of properties (e.g., bounded and non-monotonic yet convergent, or bounded yet divergent).
- **Solve approach:** Translate the property list into quick filters and test the small stock of standard sequences: \((-1)^n\), \((-1)^n/n\), \(1/n\), \(n\), \(\sin n\). Match each candidate against every clause; the answer is the sequence passing all of them.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which of the following sequences is bounded and convergent but not monotonic? (choices include \(1/n\), \((-1)^n\), \((-1)^n/n\), \(n/(n+1)\), \((-1)^n n\)).

### 15. Series-property recognition (theory, true-false)

- **What it asks:** A must-be-true item on the logical relationships governing convergence of numeric series — the necessary-condition test, and absolute vs conditional convergence.
- **Solve approach:** Hold the core facts: \(\sum a_n\) converges \(\Rightarrow a_n\to0\) (necessary, not sufficient), absolute convergence \(\Rightarrow\) convergence, but not conversely. Reject "\(a_n\to0\Rightarrow\sum a_n\) converges" with the harmonic series; know that a conditionally convergent series can be rearranged to any sum (Riemann rearrangement) as the standard "hard" distractor.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** Which must be true? (I) if \(\sum a_n\) converges then \(a_n\to0\); (II) if \(a_n\to0\) then \(\sum a_n\) converges; (III) if \(\sum|a_n|\) converges then \(\sum a_n\) converges.
