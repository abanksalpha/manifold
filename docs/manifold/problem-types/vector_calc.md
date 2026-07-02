# Vector calculus — GRE problem types

Scope: recurring vector-calculus patterns on the GRE Mathematics Subject Test — the div/curl operators, line and surface integrals, and the integral theorems — organized by the seven boundary sub-skills below. Honest caveat: the two-dimensional material (div/curl computation, line integrals, conservative fields/potential functions, Green's theorem) genuinely recurs, whereas the three-dimensional theorems (surface integrals, flux, Stokes, divergence) are on the standard syllabus but appear rarely and only as short, basic applications, since full surface-integral computations are too long for a no-calculator timed test. Neighboring topics (gradients/directional derivatives, tangent planes, plain multiple integrals, curve/surface parametrization as its own skill, Jacobian changes of variables) are handled by other agents and are excluded here.

---

## Div/curl computations

### 1. Divergence of a vector field

- **What it asks:** Compute \(\nabla\cdot\mathbf{F}=P_x+Q_y+R_z\) for a given field, usually at a specific point.
- **Solve approach:** Add the three matching partials; the result is a scalar. Substitute the point last. A zero result flags a solenoidal/incompressible field, which is sometimes the actual multiple-choice question.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** For \(\mathbf{F}=(x^{2}y,\; yz,\; xz^{2})\), find \(\nabla\cdot\mathbf{F}\) at \((1,1,1)\).

### 2. Curl of a vector field

- **What it asks:** Compute \(\nabla\times\mathbf{F}\) for a given 2D or 3D field, often to then decide whether the field is irrotational.
- **Solve approach:** Expand the formal determinant with rows \((\mathbf{i},\mathbf{j},\mathbf{k})\), \((\partial_x,\partial_y,\partial_z)\), \((P,Q,R)\); the result is a vector. In 2D only the \(\mathbf{k}\)-component \(Q_x-P_y\) survives — this is exactly the Green's-theorem integrand. Curl \(=\mathbf 0\) marks an irrotational field.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** Compute \(\nabla\times\mathbf{F}\) for \(\mathbf{F}=(y,\,-x,\,z)\).

### 3. Operator identities and type-checking

- **What it asks:** A conceptual "which expression is identically zero" (or "which is even defined") item built from grad, div, and curl.
- **Solve approach:** Memorize the two vanishing identities \(\nabla\cdot(\nabla\times\mathbf{F})=0\) and \(\nabla\times(\nabla f)=\mathbf 0\), and note \(\nabla\cdot(\nabla f)=\nabla^{2}f\) (the Laplacian, not generally zero). Type-check the rest: grad sends scalar→vector, div sends vector→scalar, curl sends vector→vector, so a composite like \(\nabla\times(\nabla\cdot\mathbf F)\) is meaningless and can be eliminated on sight.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which of the following is identically zero for every smooth field \(\mathbf F\) and scalar \(f\): (I) \(\nabla\cdot(\nabla\times\mathbf F)\), (II) \(\nabla\times(\nabla f)\), (III) \(\nabla\cdot(\nabla f)\)?

---

## Line integrals of scalar & vector fields

### 4. Work integral by direct parametrization

- **What it asks:** Evaluate the work integral \(\int_C \mathbf{F}\cdot d\mathbf{r}\) of a vector field along an explicitly given curve.
- **Solve approach:** Parametrize the curve \(\mathbf r(t)\), \(t\in[a,b]\), and reduce to \(\int_a^b \mathbf F(\mathbf r(t))\cdot\mathbf r'(t)\,dt\). Standard parametrizations: a segment \(\mathbf r(t)=(1-t)\mathbf A+t\mathbf B\); a circle \(\mathbf r(t)=(a\cos t,\,a\sin t)\). Always check first whether \(\mathbf F\) is conservative — if so, switch to a potential function (type 7) instead of grinding the integral.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Evaluate \(\int_C \mathbf{F}\cdot d\mathbf{r}\) for \(\mathbf{F}=(y,\,x^{2})\) along the segment from \((0,0)\) to \((1,2)\).

### 5. Scalar line integral (arc-length form)

- **What it asks:** Evaluate \(\int_C f\,ds\) for a scalar function along a curve, e.g. the mass of a wire of given linear density, or an arc length itself.
- **Solve approach:** Use \(\int_C f\,ds=\int_a^b f(\mathbf r(t))\,\lVert\mathbf r'(t)\rVert\,dt\); the speed factor \(\lVert\mathbf r'(t)\rVert\) is what distinguishes this from the work integral. Arc length is the special case \(f=1\). Orientation does not matter for \(ds\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\int_C (x+y)\,ds\), where \(C\) is the quarter circle \(x^{2}+y^{2}=4\) in the first quadrant.

---

## Conservative fields & potential functions (path independence)

### 6. Test whether a field is conservative

- **What it asks:** Decide whether a given field is conservative, or find the constant/parameter value that makes it so.
- **Solve approach:** On a simply connected domain, a 2D field \((P,Q)\) is conservative iff \(P_y=Q_x\); a 3D field is conservative iff \(\nabla\times\mathbf F=\mathbf 0\). For a "for what \(a\)" item, set the mixed partials equal and solve. Trap to know: \(\mathbf F=(-y,x)/(x^{2}+y^{2})\) is curl-free yet not conservative because its domain (the plane minus the origin) is not simply connected.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** For which value of \(a\) is \(\mathbf{F}=(ax y,\; x^{2}+y)\) conservative?

### 7. Evaluate a line integral via a potential function

- **What it asks:** Evaluate \(\int_C \mathbf{F}\cdot d\mathbf{r}\) for a conservative field, typically along an awkward or unspecified path between two endpoints.
- **Solve approach:** Apply the Fundamental Theorem for line integrals: if \(\mathbf F=\nabla f\), then \(\int_C \mathbf F\cdot d\mathbf r=f(\text{end})-f(\text{start})\), independent of path. Recover \(f\) by partial integration — integrate \(P\) in \(x\), differentiate the result in \(y\) to match \(Q\), and pin down the remaining function of \(y\). The ugly path is a distractor once you spot conservativity.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Evaluate \(\int_C \mathbf{F}\cdot d\mathbf{r}\) for \(\mathbf{F}=(2xy,\,x^{2})\) along any path from \((0,0)\) to \((2,3)\).

### 8. Closed-loop integral of a conservative field

- **What it asks:** Evaluate (or reason about) \(\oint_C \mathbf{F}\cdot d\mathbf{r}\) around a closed curve, exploiting path independence.
- **Solve approach:** If \(\mathbf F\) is conservative, the start and end coincide, so \(\oint_C\mathbf F\cdot d\mathbf r=0\) — recognize it and answer instantly without integrating. Contrapositive is a common conceptual hook: a nonzero closed-loop integral proves the field is not conservative.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** If \(\mathbf{F}=\nabla f\) is continuous on the plane, what is \(\oint_C \mathbf{F}\cdot d\mathbf{r}\) around the unit circle traversed once?

---

## Green's theorem

### 9. Green's theorem to evaluate a closed line integral

- **What it asks:** Evaluate \(\oint_C (P\,dx+Q\,dy)\) around a positively oriented closed curve by converting to a double integral.
- **Solve approach:** Use \(\oint_C P\,dx+Q\,dy=\iint_D (Q_x-P_y)\,dA\). The item is usually engineered so \(Q_x-P_y\) collapses to a constant, giving answer \(=(\text{constant})\times\text{area}(D)\). Watch orientation: a clockwise curve flips the sign.
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Evaluate \(\oint_C (y^{2}\,dx + x^{2}\,dy)\), where \(C\) is the boundary of the square \([0,1]\times[0,1]\) taken counterclockwise.

### 10. Area enclosed via Green's theorem

- **What it asks:** Find the area enclosed by a parametrized closed curve using the line-integral area formula.
- **Solve approach:** Apply \(A=\tfrac12\oint_C (x\,dy-y\,dx)\) (equivalently \(\oint x\,dy\) or \(-\oint y\,dx\)). Substituting an ellipse \(x=a\cos t,\,y=b\sin t\) yields \(A=\pi ab\) quickly. Useful when only the boundary curve, not the region, is given.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Use a line integral to find the area enclosed by the ellipse \(x=3\cos t,\; y=2\sin t\).

---

## Surface integrals & flux

### 11. Flux of a vector field through a surface

- **What it asks:** Evaluate a flux integral \(\iint_S \mathbf{F}\cdot\mathbf{n}\,dS\) through an open surface (a plane piece, a graph \(z=g(x,y)\), or one face of a solid).
- **Solve approach:** For a graph oriented upward, \(\iint_S \mathbf F\cdot\mathbf n\,dS=\iint_D \mathbf F\cdot(-g_x,-g_y,1)\,dA\). Exploit symmetry when possible (a constant or radial field through a symmetric surface often reads off directly). On this exam these appear only in short, low-computation form.
- **Difficulty:** medium–hard · **Frequency:** rare
- **Example stem:** Find the flux of \(\mathbf{F}=(0,0,z)\) upward through the part of the plane \(z=1\) lying over the unit disk.

### 12. Scalar surface integral / surface area

- **What it asks:** Evaluate \(\iint_S f\,dS\) over a surface, or compute a surface area (the \(f=1\) case).
- **Solve approach:** For a parametrization \(\mathbf r(u,v)\), \(dS=\lVert\mathbf r_u\times\mathbf r_v\rVert\,du\,dv\); for a graph \(z=g(x,y)\), \(dS=\sqrt{1+g_x^{2}+g_y^{2}}\,dA\). Because these integrals are lengthy, the exam favors surfaces where the integrand simplifies dramatically.
- **Difficulty:** medium–hard · **Frequency:** rare
- **Example stem:** Compute the area of the part of the plane \(z=2x+2y\) lying above the unit square \([0,1]\times[0,1]\).

---

## Stokes' theorem

### 13. Stokes' theorem (boundary line integral ↔ curl flux)

- **What it asks:** Relate \(\oint_C \mathbf{F}\cdot d\mathbf{r}\) around a closed space curve to \(\iint_S (\nabla\times\mathbf{F})\cdot\mathbf{n}\,dS\) over a surface it bounds, converting whichever side is harder.
- **Solve approach:** Apply \(\oint_C \mathbf F\cdot d\mathbf r=\iint_S(\nabla\times\mathbf F)\cdot\mathbf n\,dS\), valid for any surface \(S\) with boundary \(C\). Compute the curl first; when it is simple or constant, choose a convenient flat capping surface so the flux is trivial. When it appears here, the curl is deliberately clean.
- **Difficulty:** hard · **Frequency:** rare
- **Example stem:** Using Stokes' theorem, evaluate \(\oint_C \mathbf{F}\cdot d\mathbf{r}\) for \(\mathbf{F}=(-y,\,x,\,z)\), where \(C\) is the unit circle \(x^{2}+y^{2}=1\) in the plane \(z=0\), oriented counterclockwise.

---

## Divergence (Gauss) theorem

### 14. Flux through a closed surface via the divergence theorem

- **What it asks:** Evaluate the outward flux \(\oiint_S \mathbf{F}\cdot\mathbf{n}\,dS\) through a closed surface by converting to a volume integral.
- **Solve approach:** Apply \(\oiint_S \mathbf F\cdot\mathbf n\,dS=\iiint_E \nabla\cdot\mathbf F\,dV\) for the solid \(E\) enclosed by \(S\). Signature shortcut: the position field \(\mathbf F=(x,y,z)\) has \(\nabla\cdot\mathbf F=3\), so its outward flux equals \(3\cdot\text{Volume}(E)\) (e.g. \(4\pi r^{3}\) through a sphere of radius \(r\)). This turns an intractable surface integral into an easy volume computation.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Find the outward flux of \(\mathbf{F}=(x,\,y,\,z)\) through the sphere of radius \(2\) centered at the origin.
