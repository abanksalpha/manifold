# Numerical analysis — GRE problem types

Scope: the small set of numerical-methods patterns on the GRE Mathematics Subject Test, organized by the five boundary sub-skills below — root-finding (bisection & Newton), numerical integration (trapezoidal & Simpson) & error behavior, polynomial interpolation (Lagrange, existence/uniqueness), fixed-point iteration & convergence, and basic order-of-accuracy reasoning; the underlying calculus (derivatives, definite integrals, Taylor error) is graded under other topics in the DAG.

> **Orientation & honesty note.** Numerical analysis is one of the _rarest_ content slices on this exam — a given released form typically carries at most one such question, and some carry none. Accordingly, almost every type below is marked **rare**; the one relative exception is Newton's method, the single most likely appearance. Difficulty is **GRE-relative**, and since **no calculator is allowed** the numbers are always engineered to stay clean (one hand iteration, small integer nodes, powers of two). Frequencies are qualitative judgments across the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep — not counted statistics — and no specific question numbers are cited because they are not verifiable here.

---

## Root-finding: bisection & Newton's method

### 1. Newton's method — one iteration by hand

- **What it asks:** Given \(f\), a starting guess \(x_0\), and (implicitly) that you know the update rule, compute the next iterate \(x_1\) — occasionally \(x_2\), or the value of \(x_1\) as an approximation to a specific root (e.g. \(\sqrt{2}\)).
- **Solve approach:** Apply \(x_{1}=x_{0}-\dfrac{f(x_{0})}{f'(x_{0})}\): differentiate once, evaluate \(f\) and \(f'\) at \(x_0\), and simplify. The arithmetic is deliberately clean; the only trap is recalling the formula (it's \(-f/f'\), not \(+\)) and computing \(f'\) correctly.
- **Difficulty:** easy–medium · **Frequency:** occasional (the most common numerical-analysis item on this exam)
- **Example stem:** For \(f(x)=x^{2}-2\) with \(x_{0}=1\), one step of Newton's method gives \(x_{1}=\;?\)

### 2. Bisection — error bound & number of steps

- **What it asks:** Given a sign change of a continuous \(f\) on \([a,b]\), determine the bracketing interval after \(n\) steps, the guaranteed error after \(n\) steps, or the number of steps needed to locate the root within a stated tolerance.
- **Solve approach:** Each step halves the bracket, so after \(n\) steps the interval has length \((b-a)/2^{n}\) (and the midpoint is within \((b-a)/2^{n+1}\) of the root). To meet a tolerance \(\varepsilon\), solve \((b-a)/2^{n}<\varepsilon\), i.e. \(n>\log_{2}\!\big((b-a)/\varepsilon\big)\); on this exam the numbers make \(2^{n}\) land cleanly.
- **Difficulty:** easy–medium · **Frequency:** rare
- **Example stem:** \(f\) is continuous with a sign change on \([0,2]\). After 3 bisection steps, the root is guaranteed to lie in an interval of what length?

---

## Numerical integration: trapezoidal & Simpson's rule

### 3. Trapezoidal or Simpson approximation of a definite integral

- **What it asks:** Approximate \(\int_a^b f\,dx\) with the trapezoidal rule or Simpson's rule, given either \(f\) or a short table of values, using a small number of subintervals.
- **Solve approach:** Trapezoidal with step \(h\): \(\tfrac{h}{2}\big[f_0+2f_1+\cdots+2f_{n-1}+f_n\big]\). Simpson (\(n\) even): \(\tfrac{h}{3}\big[f_0+4f_1+2f_2+4f_3+\cdots+4f_{n-1}+f_n\big]\) — remember the \(4,2,4,\ldots\) alternation and the \(h/3\) (vs. \(h/2\)) factor. Evaluate at the nodes and combine; values are chosen so the sum is exact and quick.
- **Difficulty:** medium · **Frequency:** rare/occasional
- **Example stem:** Estimate \(\int_{1}^{3}\dfrac{1}{x}\,dx\) using the trapezoidal rule with two subintervals.

### 4. Quadrature error order & polynomial exactness

- **What it asks:** A conceptual item about how good a rule is: for which polynomial degrees it is _exact_, how its error depends on a derivative of \(f\), or how the error scales with the step size.
- **Solve approach:** Recall the exactness ladder — the trapezoidal rule is exact for degree \(\le 1\) (error \(\propto f''\), composite error \(O(h^{2})\)); Simpson's rule is exact for degree \(\le 3\) (error \(\propto f^{(4)}\), composite error \(O(h^{4})\)). The "one degree higher than expected" exactness of Simpson (cubics, not just quadratics) is the classic tested fact.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Simpson's rule integrates \(\int_a^b p(x)\,dx\) exactly for every polynomial \(p\) of degree at most what?

---

## Polynomial interpolation (Lagrange)

### 5. Interpolating polynomial — existence, uniqueness & construction

- **What it asks:** How many polynomials of degree \(\le n\) pass through \(n+1\) given points (an existence/uniqueness question), or actually build/evaluate that interpolant at a point.
- **Solve approach:** Through \(n+1\) points with distinct \(x\)-values there is _exactly one_ polynomial of degree \(\le n\) (existence and uniqueness). To construct it, use the Lagrange form \(p(x)=\sum_i y_i L_i(x)\) with \(L_i(x)=\prod_{j\ne i}\frac{x-x_j}{x_i-x_j}\), or just fit undetermined coefficients — for the small \(n\) on this exam, solving a tiny linear system is usually fastest.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** How many polynomials of degree at most 2 pass through \((0,1)\), \((1,3)\), and \((2,7)\)?

---

## Fixed-point iteration & convergence conditions

### 6. Fixed-point iteration — convergence condition

- **What it asks:** Whether the iteration \(x_{n+1}=g(x_n)\) converges to a fixed point \(p\) (where \(p=g(p)\)), which of several reformulations \(x=g(x)\) will converge, or at what rate.
- **Solve approach:** Near a fixed point the iteration is a contraction — and thus converges for a starting guess close enough — exactly when \(|g'(p)|<1\); it diverges when \(|g'(p)|>1\). Convergence is linear with asymptotic rate \(|g'(p)|\) (and faster than linear if \(g'(p)=0\)).
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** \(p\) is a fixed point of \(g\) with \(g'(p)=\tfrac12\). Does \(x_{n+1}=g(x_n)\) converge to \(p\) for \(x_0\) near \(p\), and how fast?

---

## Basic error / order-of-accuracy reasoning

### 7. Convergence order & order-of-accuracy comparison

- **What it asks:** A cross-method conceptual item: identify or rank the order of convergence/accuracy of these methods, or predict the factor by which error shrinks when the step size is halved.
- **Solve approach:** Hold the standard orders in memory — bisection is linear (error \(\times\tfrac12\) per step), Newton is quadratic (order 2) for a simple root, the composite trapezoidal rule is \(O(h^{2})\), and composite Simpson is \(O(h^{4})\). Halving \(h\) then cuts trapezoidal error by \(\approx 4\) and Simpson error by \(\approx 16\); a higher order means faster error decay.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Halving the step size reduces the trapezoidal-rule error by a factor of about 4; by about what factor does it reduce Simpson's-rule error?
