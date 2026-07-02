# Complex analysis — GRE problem types

Scope: recurring complex-analysis question patterns on the GRE Mathematics Subject Test, organized by the seven boundary sub-skills below — complex arithmetic & polar/exponential form, roots of unity & De Moivre, Cauchy–Riemann/analyticity/harmonic functions, contour integrals & Cauchy's integral formula, residues, mapping/modulus loci, and identifying entire/analytic functions. Adjacent topics (real integration technique, series convergence, the Fundamental Theorem of Algebra and conjugate roots of real polynomials, general linear algebra) are handled by other topics in the DAG and excluded here.

> **Orientation & honesty notes.** Complex analysis is a _small_ slice of the exam's ~25% "additional topics" band — typically only a handful of items per form — and it sits at the **recognize** tier: questions reward knowing the right definition or formula, not long derivations. Difficulty labels are **GRE-relative**; frequency labels are qualitative judgments of how often a pattern shows up _among the complex-analysis items_ across the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep, not counted statistics. Two real conventions apply: **no calculator** (numbers are engineered to stay clean, e.g. angles are multiples of π/6 or π/4), and answers usually come out to a tidy closed form. No specific question numbers are cited, because they are not verifiable here.

---

## Complex arithmetic & polar/exponential form

### 1. Conjugate division / rectangular simplification

- **What it asks:** Simplify a quotient of complex numbers into standard form \(a+bi\), or read off its real part, imaginary part, or modulus.
- **Solve approach:** Multiply numerator and denominator by the conjugate of the denominator; \((c-di)(c+di)=c^{2}+d^{2}\) is real, so the quotient collapses to \(a+bi\). For just the modulus of a quotient, use \(|z/w|=|z|/|w|\) instead of dividing out.
- **Difficulty:** easy · **Frequency:** common (also pervasive as an embedded sub-step)
- **Example stem:** Write \(\dfrac{3+i}{1-2i}\) in the form \(a+bi\).

### 2. Powers of \(i\) (cyclic reduction)

- **What it asks:** Evaluate a large integer power of \(i\) (or a short sum of such powers).
- **Solve approach:** The powers of \(i\) cycle with period 4: \(i^{1}=i,\ i^{2}=-1,\ i^{3}=-i,\ i^{4}=1\). Reduce the exponent mod 4 and read off the value; for a run of consecutive powers, note that any four in a row sum to 0.
- **Difficulty:** easy · **Frequency:** occasional
- **Example stem:** Evaluate \(i^{2027}\).

### 3. Modulus, argument & polar form

- **What it asks:** Find the modulus \(|z|\) and/or an argument of a complex number, or rewrite it in polar/trigonometric form \(r(\cos\theta+i\sin\theta)\).
- **Solve approach:** \(|z|=\sqrt{x^{2}+y^{2}}\) and \(\theta=\operatorname{atan2}(y,x)\), placing \(\theta\) in the correct quadrant. Use \(|zw|=|z|\,|w|\) and \(\arg(zw)=\arg z+\arg w\) to combine factors without expanding.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** Write \(-1+i\sqrt{3}\) in the polar form \(r(\cos\theta+i\sin\theta)\) with \(0\le\theta<2\pi\).

### 4. Euler's formula: complex exponentials & powers

- **What it asks:** Evaluate \(e^{z}\) for a complex exponent, or an unusual power such as \(i^{\,i}\), often as a "which of these is real?" recognition item.
- **Solve approach:** Use \(e^{a+bi}=e^{a}(\cos b+i\sin b)\) and \(e^{i\theta}=\cos\theta+i\sin\theta\). For a complex power \(z^{w}\), write the base as \(re^{i\theta}\) and use \(z^{w}=e^{w\log z}\); e.g. \(i=e^{i\pi/2}\) gives \(i^{\,i}=e^{i\cdot i\pi/2}=e^{-\pi/2}\), a real number.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** The principal value of \(i^{\,i}\) is which of the following?

---

## Roots of unity & De Moivre

### 5. De Moivre power computation

- **What it asks:** Raise a complex number to a moderate or large integer power and give the result in \(a+bi\) or polar form.
- **Solve approach:** Convert to polar form and apply De Moivre: \(\bigl(r(\cos\theta+i\sin\theta)\bigr)^{n}=r^{n}(\cos n\theta+i\sin n\theta)\). Powers of \(1\pm i\) (modulus \(\sqrt2\), argument \(\pm\pi/4\)) are the signature case; the same identity also expands \(\cos n\theta\)/\(\sin n\theta\) in terms of \(\cos\theta,\sin\theta\).
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Evaluate \((1+i)^{12}\).

### 6. \(n\)th roots & roots of unity

- **What it asks:** Find all \(n\)th roots of a complex number (or count them), identify their geometry, or evaluate their sum/product.
- **Solve approach:** Write the number as \(re^{i\theta}\); the \(n\) roots are \(r^{1/n}\,e^{i(\theta+2\pi k)/n}\) for \(k=0,\dots,n-1\), equally spaced by \(2\pi/n\) on a circle of radius \(r^{1/n}\) (a regular \(n\)-gon). The \(n\)th roots of unity sum to 0 for \(n\ge 2\) (they are the roots of \(z^{n}-1\), whose \(z^{n-1}\) coefficient is 0).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many distinct complex solutions does \(z^{6}=1\) have, and what is their sum?

---

## Cauchy–Riemann equations & analyticity / harmonic functions

### 7. Cauchy–Riemann test for analyticity

- **What it asks:** Decide where a given function is complex-differentiable or analytic, or select which of several functions is (nowhere/everywhere) analytic.
- **Solve approach:** Write \(f=u(x,y)+i\,v(x,y)\) and test the Cauchy–Riemann equations \(u_{x}=v_{y}\), \(u_{y}=-v_{x}\). Functions built from \(\bar z\), \(\operatorname{Re}z\), \(\operatorname{Im}z\), or \(|z|\) typically fail them (analytic nowhere, or only at isolated points).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** At which points of the complex plane is \(f(z)=\bar z\) complex-differentiable?

### 8. Harmonic functions & harmonic conjugates

- **What it asks:** Verify that a real function \(u(x,y)\) is harmonic, or construct a harmonic conjugate \(v\) so that \(u+iv\) is analytic.
- **Solve approach:** Harmonic means \(u_{xx}+u_{yy}=0\) (the real/imaginary parts of any analytic function are harmonic). To build the conjugate, integrate the Cauchy–Riemann equations: from \(v_{y}=u_{x}\) integrate in \(y\), then differentiate in \(x\) and match \(v_{x}=-u_{y}\) to fix the remaining function of \(x\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Confirm that \(u(x,y)=x^{2}-y^{2}\) is harmonic and find a harmonic conjugate \(v\).

---

## Contour integrals & Cauchy's integral formula

### 9. Cauchy–Goursat theorem (closed integral of an analytic function)

- **What it asks:** Evaluate a closed contour integral whose integrand is analytic inside and on the contour (or the elementary building block \(\oint (z-a)^{n}\,dz\)).
- **Solve approach:** If the integrand is analytic on and inside the closed contour, the integral is 0 (Cauchy–Goursat). The one exception among power terms is \(\oint_{|z-a|=r}(z-a)^{-1}\,dz=2\pi i\); every other integer power \((z-a)^{n}\) integrates to 0 around a closed loop.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\oint_{|z|=1} e^{z}\,dz\).

### 10. Cauchy's integral formula (value & derivative forms)

- **What it asks:** Evaluate a contour integral of the form \(\oint \dfrac{f(z)}{(z-a)^{k}}\,dz\) with \(f\) analytic and the singular point \(a\) inside the contour.
- **Solve approach:** For a simple factor, \(\oint_{C}\dfrac{f(z)}{z-a}\,dz=2\pi i\,f(a)\); for a repeated factor use the derivative form \(\oint_{C}\dfrac{f(z)}{(z-a)^{n+1}}\,dz=\dfrac{2\pi i}{n!}\,f^{(n)}(a)\). First confirm \(a\) lies inside \(C\); if not, the integral is 0.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\oint_{|z|=2}\dfrac{e^{z}}{z-1}\,dz\).

---

## Residue theorem & simple pole residues

### 11. Residue at a simple pole

- **What it asks:** Compute the residue of a function at a given simple pole.
- **Solve approach:** For a simple pole at \(a\), \(\operatorname{Res}_{z=a}f=\lim_{z\to a}(z-a)f(z)\). When \(f=p/q\) with \(q\) having a simple zero at \(a\), the shortcut \(\operatorname{Res}_{z=a}f=\dfrac{p(a)}{q'(a)}\) is fastest.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Find the residue of \(f(z)=\dfrac{z}{z^{2}+1}\) at \(z=i\).

### 12. Residue theorem for contour integrals

- **What it asks:** Evaluate a closed contour integral of a function with one or more isolated singularities inside the contour.
- **Solve approach:** Locate the poles inside \(C\), compute each residue, and apply \(\oint_{C}f\,dz=2\pi i\sum(\text{residues inside }C)\). Poles outside \(C\) contribute nothing; watch which poles the given contour actually encloses.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\oint_{|z|=3}\dfrac{z}{(z-1)(z-2)}\,dz\).

---

## Mapping / modulus questions

### 13. Modulus loci & regions in the plane

- **What it asks:** Identify the curve or region described by a modulus (or real/imaginary-part) condition on \(z\).
- **Solve approach:** Read \(|z-a|=r\) as a circle of radius \(r\) centered at \(a\), \(|z-a|<r\) as the open disk, and \(|z-a|=|z-b|\) as the perpendicular bisector of the segment \(ab\). If unsure, substitute \(z=x+iy\) and simplify to a Cartesian equation.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Describe the set of complex \(z\) satisfying \(|z-1|=|z+1|\).

### 14. Elementary mappings (\(1/z\), \(z^{2}\), linear)

- **What it asks:** Determine the image of a point, line, circle, or region under a simple map such as \(w=z^{2}\), \(w=1/z\), or \(w=az+b\).
- **Solve approach:** Track the map in polar form: \(w=z^{2}\) squares the modulus and doubles the argument; \(w=1/z\) inverts the modulus and negates the argument (and sends circles/lines to circles/lines). Testing a couple of sample points usually pins down the image.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Under the mapping \(w=1/z\), what is the image of the circle \(|z|=2\)?

---

## Identifying entire / analytic functions

### 15. Entire functions & Liouville (recognition)

- **What it asks:** Select which functions are entire (analytic on all of \(\mathbb{C}\)), or apply a recognition fact such as Liouville's theorem.
- **Solve approach:** Polynomials, \(e^{z}\), \(\sin z\), \(\cos z\) (and sums/products of these) are entire; \(\bar z\), \(|z|\), \(\operatorname{Re}z\), and anything with a denominator that vanishes are not. Recall Liouville: a bounded entire function is constant — and note that \(\sin z\), \(\cos z\) are _unbounded_ on \(\mathbb{C}\), unlike on \(\mathbb{R}\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which of \(e^{z}\), \(\bar z\), \(1/z\), and \(|z|\) is entire?

### 16. Classifying isolated singularities

- **What it asks:** Classify the singularity of a function at a point as removable, a pole (of some order), or essential.
- **Solve approach:** A finite nonzero limit of \((z-a)^{k}f(z)\) signals a pole of order \(k\); if \(f\) has a finite limit at \(a\) the singularity is removable; if no such \(k\) works (infinitely many negative Laurent terms, e.g. \(e^{1/z}\)) it is essential. Standard cues: \(\frac{\sin z}{z}\) at 0 is removable, \(\frac{1}{z^{2}}\) at 0 is a double pole.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Classify the singularity of \(f(z)=\dfrac{\sin z}{z}\) at \(z=0\).
