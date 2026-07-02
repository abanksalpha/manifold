# Sequences & series — GRE problem types

Scope: recurring sequence- and series-convergence patterns on the GRE Mathematics Subject Test, organized by the eight boundary sub-skills below. Neighboring topics (function limits / L'Hopital, integration techniques, and formal real-analysis convergence — ε–N proofs, lim sup/inf, uniform convergence, Fourier series) are handled by other agents and are excluded here.

---

## Limits of sequences

### 1. Closed-form sequence limit

- **What it asks:** Find \(\lim_{n\to\infty} a_n\) for a sequence given by an explicit algebraic formula (rational in \(n\), roots, or a difference of roots).
- **Solve approach:** Compare leading powers of \(n\) by dividing through by the highest power; for a difference of square roots multiply by the conjugate; a bounded factor times a vanishing factor tends to 0.
- **Difficulty:** easy · **Frequency:** common (often a sub-step feeding a convergence test)
- **Example stem:** Evaluate \(\lim_{n\to\infty}\dfrac{\sqrt{4n^{2}+n}}{3n-1}\).

### 2. Recursive / nested-radical limit (fixed point)

- **What it asks:** A sequence is defined by \(a_1\) and \(a_{n+1}=f(a_n)\) (often a nested radical or an averaging recursion); find its limit.
- **Solve approach:** Assume the sequence converges (monotone and bounded), pass to the limit so \(L=f(L)\), solve for \(L\), and discard the root inconsistent with the sign/range of the terms.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** If \(a_1=\sqrt{2}\) and \(a_{n+1}=\sqrt{2+a_n}\), find \(\lim_{n\to\infty} a_n\).

### 3. Transcendental & growth-rate sequence limit

- **What it asks:** Evaluate a limit involving \((1+\tfrac{x}{n})^{n}\), \(n^{1/n}\), or a ratio of factorials, exponentials, and powers.
- **Solve approach:** Use \((1+\tfrac{a}{n})^{n}\to e^{a}\) and \(n^{1/n}\to 1\); apply the growth ordering \(\ln n \ll n^{p} \ll a^{n} \ll n! \ll n^{n}\); take logarithms for \(1^{\infty}\) forms.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\lim_{n\to\infty}\left(1+\dfrac{2}{n}\right)^{n}\) and \(\lim_{n\to\infty}\dfrac{2^{n}}{n!}\).

### 4. nth-term (divergence) test

- **What it asks:** Decide whether a series diverges because its terms fail to approach 0, or recognize that \(a_n\to 0\) is necessary but not sufficient for convergence.
- **Solve approach:** If \(\lim_{n\to\infty} a_n \neq 0\) (or does not exist), the series diverges immediately; note the converse fails (the harmonic series has terms \(\to 0\) yet diverges).
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** Which of the following diverge by inspection of their terms: \(\sum \dfrac{n}{2n+1}\), \(\sum \cos\!\left(\tfrac{1}{n}\right)\), \(\sum \dfrac{1}{n}\)?

---

## Geometric & telescoping series

### 5. Infinite geometric series sum

- **What it asks:** Sum an infinite geometric series (given a first term and ratio, or in \(\sum\) form), or find the parameter range for convergence; includes repeating decimals.
- **Solve approach:** Converges iff \(|r|<1\), with sum \(\dfrac{a}{1-r}\) where \(a\) is the first term actually present; align the starting index carefully. A repeating decimal is a geometric series in powers of \(10^{-k}\).
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** Evaluate \(\sum_{n=0}^{\infty}\dfrac{3}{4^{n}}\), and express \(0.\overline{27}\) as a fraction.

### 6. Telescoping series sum

- **What it asks:** Sum a series whose terms collapse after a partial-fraction split.
- **Solve approach:** Decompose the term into \(f(n)-f(n+k)\), write the partial sum \(S_N\), cancel the interior terms, and take \(\lim_{N\to\infty} S_N\) of what survives.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\sum_{n=1}^{\infty}\dfrac{1}{n(n+1)}\).

### 7. Arithmetic–geometric sum (\(\sum n x^{n}\))

- **What it asks:** Sum a series of the form \(\sum n\,x^{n}\) (occasionally \(\sum n^{2}x^{n}\)) for \(|x|<1\).
- **Solve approach:** Differentiate the geometric identity \(\sum_{n\ge 0} x^{n}=\dfrac{1}{1-x}\) term by term to get \(\sum_{n\ge 1} n\,x^{n}=\dfrac{x}{(1-x)^{2}}\); substitute the given ratio.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Evaluate \(\sum_{n=1}^{\infty}\dfrac{n}{2^{n}}\).

---

## Integral test & p-series

### 8. p-series recognition

- **What it asks:** Determine convergence of \(\sum 1/n^{p}\), or recognize a disguised p-series inside an algebraic term.
- **Solve approach:** \(\sum 1/n^{p}\) converges iff \(p>1\); reduce an algebraic term to its leading power of \(n\) to read off the effective \(p\) (e.g. \(1/\sqrt{n}\) is \(p=\tfrac12\), divergent).
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** Which converge: \(\sum \dfrac{1}{n^{3/2}}\), \(\sum \dfrac{1}{\sqrt{n}}\), \(\sum \dfrac{1}{n}\)?

### 9. Integral test application (log-type series)

- **What it asks:** Determine convergence of a positive, decreasing series whose antiderivative is accessible, typically \(\sum 1/\big(n(\ln n)^{p}\big)\).
- **Solve approach:** For \(f\) positive and eventually decreasing, \(\sum f(n)\) and \(\int^{\infty} f\) converge together; substitute \(u=\ln n\), giving \(\int du/u^{p}\), which diverges for \(p\le 1\) and converges for \(p>1\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Determine whether \(\sum_{n=2}^{\infty}\dfrac{1}{n\ln n}\) converges.

---

## Comparison & limit-comparison tests

### 10. Convergence by comparison / limit-comparison

- **What it asks:** Classify a positive series with rational or algebraic terms by comparing it to a p-series or geometric series.
- **Solve approach:** Read off the leading-order behavior and limit-compare with \(1/n^{p}\), where \(p=\deg(\text{denominator})-\deg(\text{numerator})\); a finite nonzero limit means the two series share convergence behavior.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Determine whether \(\sum_{n=1}^{\infty}\dfrac{n+3}{n^{3}+2n+1}\) converges.

### 11. "Which of the following converge?" (I/II/III sort)

- **What it asks:** A Roman-numeral item lists several series; select which converge (or which converge absolutely). This is the signature series format on the exam.
- **Solve approach:** Triage each series with the cheapest applicable tool — nth-term, geometric, p-series, comparison, alternating, or ratio — rather than forcing one method on all three.
- **Difficulty:** medium–hard · **Frequency:** common
- **Example stem:** Which converge? (I) \(\sum \dfrac{(-1)^{n}}{n}\); (II) \(\sum \dfrac{1}{n^{2}}\); (III) \(\sum \dfrac{n}{n+1}\).

---

## Ratio & root tests

### 12. Ratio test (factorial / exponential series)

- **What it asks:** Determine convergence of a series whose terms mix factorials, exponentials, and powers.
- **Solve approach:** Compute \(L=\lim_{n\to\infty}\left|\dfrac{a_{n+1}}{a_n}\right|\); \(L<1\) converges, \(L>1\) diverges, \(L=1\) is inconclusive (switch tests). Factorials and exponentials make the ratio simplify cleanly.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Determine whether \(\sum_{n=1}^{\infty}\dfrac{2^{n}}{n!}\) converges (and try \(\sum \dfrac{n^{2}}{2^{n}}\)).

### 13. Root test (\((\,\cdot\,)^{n}\) forms)

- **What it asks:** Determine convergence when the nth term is itself an nth power, so an nth root simplifies it.
- **Solve approach:** Compute \(L=\lim_{n\to\infty}\big(|a_n|\big)^{1/n}\) and apply the same decision rule as the ratio test; best when \(a_n=(b_n)^{n}\) or \(n\) sits in the exponent.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Determine whether \(\sum_{n=1}^{\infty}\left(\dfrac{n}{2n+1}\right)^{n}\) converges.

---

## Alternating series & error bound

### 14. Alternating series: convergence, absolute vs conditional

- **What it asks:** Decide whether an alternating series converges and, if so, whether the convergence is absolute or conditional.
- **Solve approach:** Alternating series test: if the magnitudes decrease monotonically to 0, the series converges. Then test \(\sum |a_n|\): if that also converges the series is absolutely convergent, otherwise conditionally convergent.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Classify \(\sum_{n=1}^{\infty}\dfrac{(-1)^{n}}{\sqrt{n}}\) as absolutely convergent, conditionally convergent, or divergent.

### 15. Alternating series error bound

- **What it asks:** Bound the truncation error of a convergent alternating series, or find how many terms achieve a target accuracy.
- **Solve approach:** For an alternating series with terms decreasing to 0, \(|S-S_N|\le a_{N+1}\), the first omitted term; solve \(a_{N+1}\le \varepsilon\) for \(N\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many terms of \(\sum_{n=1}^{\infty}\dfrac{(-1)^{n+1}}{n}\) guarantee a partial sum within \(0.01\) of the total?

---

## Radius & interval of convergence

### 16. Radius & interval of convergence

- **What it asks:** Find the radius of convergence \(R\) of a power series \(\sum c_n (x-a)^{n}\), and sometimes the full interval including endpoint behavior.
- **Solve approach:** Apply the ratio (or root) test to get \(R\) from \(\lim |c_{n+1}/c_n|\) or \(\lim |c_n|^{1/n}\); then test each endpoint \(x=a\pm R\) separately, since each reduces to a numerical series. Watch the special cases \(R=0\) (\(\sum n!\,x^{n}\)) and \(R=\infty\) (\(\sum x^{n}/n!\)).
- **Difficulty:** medium (radius) to hard (endpoint tests) · **Frequency:** common
- **Example stem:** Find the interval of convergence of \(\sum_{n=1}^{\infty}\dfrac{(x-2)^{n}}{n\,3^{n}}\).

---

## Taylor & Maclaurin series (Lagrange remainder)

### 17. Standard Maclaurin recall → derivative or coefficient

- **What it asks:** Use a memorized Maclaurin series to extract a specific Taylor coefficient or a high-order derivative value \(f^{(k)}(0)\).
- **Solve approach:** Match the function to a known series (\(e^{x}\), \(\sin x\), \(\cos x\), \(\tfrac{1}{1-x}\), \(\ln(1+x)\), \(\arctan x\)); the coefficient of \(x^{k}\) equals \(f^{(k)}(0)/k!\), so \(f^{(k)}(0)=k!\cdot(\text{coefficient})\).
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** For \(f(x)=\ln(1+x)\), find \(f^{(5)}(0)\).

### 18. Taylor coefficient of a product / composite

- **What it asks:** Find the coefficient of a given power of \(x\) in the series of a product or composition of standard functions.
- **Solve approach:** Substitute into or multiply the known series and collect only the target power — never repeated differentiation. Examples: \(e^{x^{2}}=\sum x^{2n}/n!\), \(x\sin x\), \(e^{x}\cos x\).
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Find the coefficient of \(x^{4}\) in the Maclaurin series of \(e^{x^{2}}\).

### 19. Numerical series summed via a known series

- **What it asks:** Evaluate a convergent numerical series by recognizing it as a standard Taylor series evaluated at a specific point.
- **Solve approach:** Match the general term to \(e^{x}\), \(\sin x\), \(\cos x\), \(\ln(1+x)\), or \(\arctan x\) at a chosen \(x\); e.g. \(\sum 1/n! = e\), \(\sum (-1)^{n-1}/n = \ln 2\), \(\sum (-1)^{n}/(2n+1)=\pi/4\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\sum_{n=0}^{\infty}\dfrac{(-1)^{n}}{2n+1}\).

### 20. Lagrange remainder error bound

- **What it asks:** Bound the error of an nth-degree Taylor approximation on an interval, or find the degree needed for a stated accuracy, using Taylor's theorem.
- **Solve approach:** \(R_n(x)=\dfrac{f^{(n+1)}(c)}{(n+1)!}(x-a)^{n+1}\) for some \(c\) between \(a\) and \(x\); bound \(|f^{(n+1)}|\) by its maximum \(M\) on the interval to get \(|R_n|\le \dfrac{M\,|x-a|^{n+1}}{(n+1)!}\).
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** Estimate the maximum error when \(\cos x\) is approximated by \(1-\tfrac{x^{2}}{2}\) for \(|x|\le 0.5\).
