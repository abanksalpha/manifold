# Trigonometry — GRE problem types

Scope: recurring trigonometry patterns on the GRE Mathematics Subject Test — a relearn-tier precalculus prerequisite that surfaces both as occasional standalone items and, more often, as a tool inside calculus problems; neighboring topics (trig limits, trig substitution in integrals, Taylor series of sin/cos, and Euler/complex-exponential forms) are handled by other agents and excluded here.

---

## Unit circle & reference angles

### 1. Special-angle evaluation

- **What it asks:** Give the exact value of a sine, cosine, tangent (or reciprocal) at a standard angle — an integer multiple of \(\pi/6\) or \(\pi/4\).
- **Solve approach:** Read the value off the unit circle: fix the reference-angle magnitude \(\{\tfrac12,\ \tfrac{\sqrt2}{2},\ \tfrac{\sqrt3}{2}\}\) and attach the quadrant sign; reciprocal functions (\(\sec,\csc,\cot\)) invert these. This is the atomic skill under most calculus items, so speed and zero errors matter more than difficulty.
- **Difficulty:** easy · **Frequency:** common (usually embedded)
- **Example stem:** Evaluate \(\tan\!\left(\dfrac{2\pi}{3}\right)\).

### 2. Reference-angle & periodicity reduction

- **What it asks:** Evaluate a trig function at a large, negative, or non-first-quadrant angle.
- **Solve approach:** Subtract multiples of the period (\(2\pi\) for \(\sin/\cos\), \(\pi\) for \(\tan\)) to land in \([0,2\pi)\), take the reference angle to the nearest x-axis, evaluate there, and fix the sign from the quadrant (ASTC). Use even/odd symmetry \(\cos(-\theta)=\cos\theta\), \(\sin(-\theta)=-\sin\theta\) for negatives.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** Evaluate \(\tan\!\left(\dfrac{11\pi}{6}\right)\).

### 3. Period, amplitude, or range of a trig function

- **What it asks:** State the period, amplitude, or range of an \(A\sin(Bx+C)+D\)-type function, or the fundamental period of a sum such as \(\sin(2x)+\cos(3x)\).
- **Solve approach:** For a single term the period is \(2\pi/|B|\), amplitude \(|A|\), range \([D-|A|,\,D+|A|]\). For a sum of terms the fundamental period is the least common multiple of the individual periods.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** What is the period of \(f(x)=\sin(2x)+\cos(3x)\)?

---

## Trig identities (Pythagorean, sum/difference, double-angle)

### 4. Pythagorean-identity simplification

- **What it asks:** Collapse an expression to a single term or number using \(\sin^2+\cos^2=1\), \(1+\tan^2=\sec^2\), or \(1+\cot^2=\csc^2\).
- **Solve approach:** Substitute a Pythagorean form, then convert everything to \(\sin/\cos\) and cancel. The three variants and their rearrangements (e.g. \(1-\cos^2=\sin^2\)) cover essentially all cases.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** Simplify \(\dfrac{\sec^2\theta-1}{\sec^2\theta}\).

### 5. Sum/difference & double-angle evaluation

- **What it asks:** Find the exact value of a nonstandard angle, or rewrite a compound-angle expression, using \(\sin(a\pm b)\), \(\cos(a\pm b)\), or the double-angle forms.
- **Solve approach:** Split the angle into a sum/difference of special angles (e.g. \(75^\circ=45^\circ+30^\circ\)) and expand; for double angles use \(\sin2x=2\sin x\cos x\) and \(\cos2x=1-2\sin^2x=2\cos^2x-1\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Find the exact value of \(\sin 75^\circ\).

### 6. Power reduction of \(\sin^2\)/\(\cos^2\)

- **What it asks:** Rewrite an even power of sine or cosine with no powers — most often to make an integral tractable.
- **Solve approach:** Apply \(\sin^2x=\tfrac{1-\cos2x}{2}\), \(\cos^2x=\tfrac{1+\cos2x}{2}\) (a repackaged double-angle identity); over a full period the \(\cos2x\) term integrates to \(0\), leaving the constant piece.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\displaystyle\int_0^{\pi}\sin^2x\,dx\).

### 7. Harmonic addition: max/min of \(a\sin x+b\cos x\)

- **What it asks:** Find the maximum, minimum, or amplitude of a linear combination \(a\sin x+b\cos x\).
- **Solve approach:** Rewrite as \(R\sin(x+\varphi)\) with \(R=\sqrt{a^2+b^2}\); the extremes are \(\pm R\) and the range is \([-R,\,R]\). No calculus required.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** What is the maximum value of \(5\cos x-12\sin x\)?

### 8. Equivalent-expression / identity recognition

- **What it asks:** Choose which of five expressions equals a given trig expression (or which stated identity is false).
- **Solve approach:** Convert every option to \(\sin/\cos\) and simplify, or collapse double-angle pieces; e.g. \(1-\cos2x=2\sin^2x\) and \(\sin2x=2\sin x\cos x\) reduce many ratios to \(\tan x\) or \(\cot x\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which of the following equals \(\dfrac{1-\cos 2x}{\sin 2x}\)?

---

## Solving trigonometric equations

### 9. Factorable trig equation on an interval

- **What it asks:** Find all solutions, or count the solutions, of an equation that is polynomial in one trig function, on \([0,2\pi)\) (or \([0^\circ,360^\circ)\)).
- **Solve approach:** Treat the trig function as a variable, factor (or use the quadratic formula), then back out each angle on the interval — recalling that each value of \(\sin\) or \(\cos\) in \((-1,1)\) gives two angles per period. Watch endpoint inclusion/exclusion.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many solutions does \(2\cos^2x+\cos x-1=0\) have on \([0,2\pi)\)?

### 10. Equation requiring an identity to reduce

- **What it asks:** Solve or count solutions of an equation that mixes different angles or functions, including "where do these two curves intersect?"
- **Solve approach:** First apply an identity to write everything in one function and one angle — e.g. replace \(\cos2x\) via a double-angle form, or divide \(\sin x=\cos x\) to get \(\tan x=1\) — then finish as in type 9.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** On \([0,2\pi)\), how many times do the graphs of \(y=\sin x\) and \(y=\cos x\) intersect?

---

## Inverse trig functions

### 11. Compose a trig function with an inverse trig function

- **What it asks:** Rewrite a composition such as \(\cos(\arcsin x)\) or \(\sec(\arctan x)\) as an algebraic expression in \(x\).
- **Solve approach:** Set \(\theta\) equal to the inner inverse function, draw the implied right triangle (or use \(\sin^2+\cos^2=1\)), and read off the requested ratio; keep the sign consistent with the inverse function's range.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Express \(\sec(\arctan x)\) as an algebraic expression in \(x\).

### 12. Principal value / range of an inverse trig function

- **What it asks:** Evaluate an inverse trig function, or an inverse-of-a-trig composition like \(\arcsin(\sin\theta)\), respecting the principal range.
- **Solve approach:** Recall ranges \(\arcsin\in[-\tfrac\pi2,\tfrac\pi2]\), \(\arccos\in[0,\pi]\), \(\arctan\in(-\tfrac\pi2,\tfrac\pi2)\); for \(\arcsin(\sin\theta)\) return the reflected/co-terminal angle inside the range, not \(\theta\) itself.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\arcsin\!\left(\sin\dfrac{5\pi}{6}\right)\).

### 13. Derivative of an inverse trig function

- **What it asks:** Differentiate an inverse trig function, often composed with an inner function.
- **Solve approach:** Use \(\tfrac{d}{dx}\arcsin x=\tfrac{1}{\sqrt{1-x^2}}\), \(\tfrac{d}{dx}\arctan x=\tfrac{1}{1+x^2}\), \(\tfrac{d}{dx}\text{arcsec}\,x=\tfrac{1}{|x|\sqrt{x^2-1}}\), applying the chain rule to the inner function.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Find \(\dfrac{d}{dx}\,\arctan(\sqrt{x})\).

### 14. Integral yielding an inverse trig function

- **What it asks:** Evaluate an integral whose antiderivative is \(\arcsin\) or \(\arctan\), sometimes after scaling or completing the square.
- **Solve approach:** Match \(\int\frac{dx}{1+x^2}=\arctan x\) and \(\int\frac{dx}{\sqrt{1-x^2}}=\arcsin x\); with constants use \(\int\frac{dx}{a^2+x^2}=\tfrac1a\arctan\tfrac xa\); complete the square when the denominator is a general quadratic.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\displaystyle\int_0^{2}\dfrac{dx}{4+x^2}\).

---

## Law of sines & law of cosines

### 15. Law of cosines for a missing side or angle

- **What it asks:** Given two sides and the included angle (SAS) or all three sides (SSS) of a triangle, find the remaining side or an angle.
- **Solve approach:** Apply \(c^2=a^2+b^2-2ab\cos C\); solve for the side directly, or rearrange to \(\cos C=\frac{a^2+b^2-c^2}{2ab}\) for an angle. Pure triangle-solving is uncommon on this exam, so expect friendly special-angle inputs.
- **Difficulty:** easy–medium · **Frequency:** rare
- **Example stem:** Two sides of a triangle have lengths \(3\) and \(7\) and meet at a \(120^\circ\) angle; find the third side.

### 16. Law of sines & triangle area with an included angle

- **What it asks:** Use \(a/\sin A=b/\sin B\) to find a missing side or angle, or compute a triangle's area from two sides and the included angle.
- **Solve approach:** Set up the law-of-sines ratio for the given ASA/AAS data; for area use \(\text{Area}=\tfrac12ab\sin C\). The area form is the more likely of the two to appear on this exam.
- **Difficulty:** easy–medium · **Frequency:** rare
- **Example stem:** Find the area of a triangle with sides \(8\) and \(5\) enclosing a \(30^\circ\) angle.
