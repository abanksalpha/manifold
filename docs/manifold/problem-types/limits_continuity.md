# Limits & continuity — GRE problem types

Scope: recurring limit- and continuity-evaluation patterns on the GRE Mathematics Subject Test, organized by the four boundary sub-skills below. Neighboring topics (derivative rules, sequences/series convergence, multivariable limits, formal ε–δ proofs) are handled by other agents and are excluded here.

---

## Limits & indeterminate forms

### 1. Removable-discontinuity limit (factor and cancel)

- **What it asks:** Evaluate a rational or factorable limit that gives 0/0 by direct substitution.
- **Solve approach:** Factor numerator and denominator, cancel the common vanishing factor, then substitute. Difference-of-squares, difference-of-cubes, and simple quadratics are the usual factorizations.
- **Difficulty:** easy · **Frequency:** occasional (more often a sub-step inside harder items than a standalone question)
- **Example stem:** Evaluate \(\lim_{x\to 3}\dfrac{x^{2}-9}{x^{2}-2x-3}\).

### 2. Conjugate / rationalizing limit

- **What it asks:** Evaluate a 0/0 or ∞−∞ limit that contains a difference of square roots.
- **Solve approach:** Multiply by the conjugate to clear the radical, cancel the resulting common factor, then take the limit. For the ∞−∞ form at infinity, the conjugate turns it into a rational form you can handle by leading-term comparison.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to\infty}\left(\sqrt{x^{2}+4x}-x\right)\).

### 3. Special trigonometric limit

- **What it asks:** Evaluate a limit built from \(\sin x / x\) or \((1-\cos x)/x\) as the argument tends to 0.
- **Solve approach:** Reduce to the standard facts \(\lim_{u\to0}\frac{\sin u}{u}=1\) and \(\lim_{u\to0}\frac{1-\cos u}{u}=0\) (equivalently \(\frac{1-\cos u}{u^{2}}\to\tfrac12\)); match arguments by scaling numerator/denominator to the same \(u\).
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to 0}\dfrac{\sin 4x}{\tan 7x}\).

### 4. The number e limit

- **What it asks:** Evaluate a limit of the form \((1+\tfrac{a}{x})^{x}\) or \((1+kx)^{1/x}\), an \(1^{\infty}\) form.
- **Solve approach:** Recognize \(\lim_{x\to\infty}(1+\tfrac{a}{x})^{x}=e^{a}\) and \(\lim_{x\to0}(1+kx)^{1/x}=e^{k}\); if disguised, take a logarithm and evaluate the resulting product limit.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to\infty}\left(1+\dfrac{3}{x}\right)^{2x}\).

### 5. Derivative in disguise (limit equals \(f'(a)\))

- **What it asks:** Evaluate a 0/0 difference-quotient limit that is secretly the definition of a derivative at a point.
- **Solve approach:** Recognize \(\lim_{h\to0}\frac{f(a+h)-f(a)}{h}=f'(a)\) (or the \(\frac{f(x)-f(a)}{x-a}\) form), identify \(f\) and \(a\), and just differentiate rather than manipulate the quotient. A signature GRE shortcut.
- **Difficulty:** medium (easy once spotted, slow if not) · **Frequency:** common
- **Example stem:** Evaluate \(\lim_{h\to 0}\dfrac{(2+h)^{10}-2^{10}}{h}\).

### 6. One-sided limits and piecewise / existence

- **What it asks:** Determine a one-sided limit, or decide whether a two-sided limit exists, for a piecewise or absolute-value function.
- **Solve approach:** Evaluate left and right limits separately at the junction; the two-sided limit exists only if they agree. Watch for sign changes in \(|x|\)-type expressions and for oscillation (e.g. \(\sin(1/x)\)) causing nonexistence.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** For \(f(x)=\dfrac{|x-2|}{x-2}\), find \(\lim_{x\to2^{-}}f(x)\) and \(\lim_{x\to2^{+}}f(x)\), and state whether \(\lim_{x\to2}f(x)\) exists.

### 7. Squeeze (sandwich) theorem

- **What it asks:** Evaluate a limit of a bounded factor times a vanishing factor, where direct/L'Hopital methods stall.
- **Solve approach:** Bound the oscillating factor (e.g. \(-1\le\sin(\cdot)\le1\)), multiply through by the vanishing magnitude, and squeeze both bounds to the same value.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to 0} x^{2}\sin\!\left(\dfrac{1}{x}\right)\).

### 8. Greatest-integer / floor-function limit

- **What it asks:** Evaluate one-sided or two-sided limits (or test continuity) of an expression involving \(\lfloor x\rfloor\).
- **Solve approach:** Treat \(\lfloor x\rfloor\) as locally constant between integers; compute left/right limits at an integer, where the floor jumps by 1, so one-sided limits typically differ.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Evaluate \(\lim_{x\to 2^{-}}\big(x-\lfloor x\rfloor\big)\) and \(\lim_{x\to 2^{+}}\big(x-\lfloor x\rfloor\big)\).

---

## Continuity & the intermediate value theorem

### 9. Solve for the constant that makes a piecewise function continuous

- **What it asks:** Find the parameter value(s) so that a piecewise-defined function is continuous (sometimes also differentiable) at a junction point.
- **Solve approach:** Set the one-sided limits equal to each other and to the defined value at the seam; solve for the unknown. For a differentiability version, also match the one-sided derivatives.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** For what value of \(c\) is \(f(x)=\begin{cases}cx+1,& x\le 1\\ x^{2}+2,& x>1\end{cases}\) continuous at \(x=1\)?

### 10. Classify the discontinuity

- **What it asks:** Identify the type of discontinuity (removable, jump, or infinite) of a given function at a point.
- **Solve approach:** Compare the two one-sided limits and the function value: equal finite one-sided limits ⇒ removable; unequal finite ⇒ jump; a one-sided limit that is \(\pm\infty\) ⇒ infinite (vertical asymptote).
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Classify the discontinuities of \(f(x)=\dfrac{x^{2}-x}{x^{2}-1}\).

### 11. Intermediate Value Theorem: guaranteed root / sign change

- **What it asks:** Use continuity to conclude that an equation has at least one solution in an interval, or to count/locate sign changes.
- **Solve approach:** Confirm continuity on \([a,b]\), evaluate the function at the endpoints, and invoke the IVT when the values straddle the target (e.g. opposite signs guarantee a root). Combine with monotonicity to argue uniqueness or count roots.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Show that \(x^{3}-4x+1=0\) has a solution in the interval \((0,1)\).

### 12. Continuity versus differentiability (conceptual)

- **What it asks:** A true/false or "which must hold" item about the logical relationship between continuity and differentiability.
- **Solve approach:** Apply the one-way implication: differentiable ⇒ continuous, but not conversely (corners like \(|x|\), cusps, or vertical tangents are continuous yet non-differentiable). Use a standard counterexample to reject the false direction.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which statements about \(f(x)=|x-1|\) at \(x=1\) are true: (I) continuous there, (II) differentiable there, (III) \(\lim_{x\to1}f(x)\) exists?

---

## L'Hopital's rule

### 13. Direct L'Hopital on 0/0 or ∞/∞

- **What it asks:** Evaluate an indeterminate quotient of the form 0/0 or ∞/∞ that resists simple algebra.
- **Solve approach:** Confirm the indeterminate form, differentiate numerator and denominator separately, and re-evaluate; iterate if still indeterminate. A short Taylor expansion is often faster for repeated 0/0 cases.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** Evaluate \(\lim_{x\to 0}\dfrac{e^{x}-1-x}{x^{2}}\).

### 14. Log-transform for \(1^{\infty}\), \(0^{0}\), \(\infty^{0}\)

- **What it asks:** Evaluate an indeterminate power form where both base and exponent vary.
- **Solve approach:** Set \(L=\lim\), take \(\ln L=\lim(\text{exponent}\cdot\ln(\text{base}))\), convert the resulting 0·∞ into a quotient, apply L'Hopital, then exponentiate to recover \(L\).
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to 0^{+}} x^{\,x}\).

### 15. Growth-rate hierarchy comparison

- **What it asks:** Determine the limit of a ratio comparing logarithmic, polynomial, and exponential growth at infinity.
- **Solve approach:** Apply the ordering \(\ln x \ll x^{p} \ll e^{x}\) (for \(p>0\)): the faster-growing function dominates, so the ratio tends to 0 or ∞ accordingly. L'Hopital confirms the standard cases (e.g. \((\ln x)/x\to0\), \(x^{n}/e^{x}\to0\)).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to\infty}\dfrac{(\ln x)^{2}}{x}\).

---

## Limits at infinity & horizontal asymptotes

### 16. Rational-function end behavior (degree rule)

- **What it asks:** Find a limit at \(\pm\infty\) of a rational function, or identify its horizontal asymptote.
- **Solve approach:** Compare degrees of numerator and denominator: lower-over-higher ⇒ 0; equal ⇒ ratio of leading coefficients; higher-over-lower ⇒ \(\pm\infty\) (no horizontal asymptote). Equivalently divide through by the highest power of \(x\).
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** Evaluate \(\lim_{x\to\infty}\dfrac{3x^{2}-5x+2}{6x^{2}+x-4}\).

### 17. Limits at infinity with radicals (sign care)

- **What it asks:** Evaluate a limit at \(+\infty\) or \(-\infty\) of a quotient containing \(\sqrt{\text{polynomial}}\).
- **Solve approach:** Divide by the highest power of \(x\), pulling it inside the radical as \(\sqrt{x^{2}}=|x|\); track the sign carefully, since \(|x|=-x\) when \(x\to-\infty\), which flips the answer relative to the \(+\infty\) case.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to-\infty}\dfrac{\sqrt{9x^{2}+1}}{2x+3}\).

### 18. Transcendental end behavior / horizontal asymptotes

- **What it asks:** Find a limit at infinity involving exponential, inverse-trig, or similar transcendental functions, or identify the associated horizontal asymptote.
- **Solve approach:** Use known end behavior: \(e^{-x}\to0\) and \(e^{x}\to\infty\) as \(x\to\infty\); \(\arctan x\to\pm\tfrac{\pi}{2}\); \(\tanh x\to\pm1\). For mixed expressions, factor out the dominant term first.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{x\to\infty}\arctan(x)\) and \(\lim_{x\to\infty}\dfrac{1+e^{-x}}{2-e^{-x}}\).
