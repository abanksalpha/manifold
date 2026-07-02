# Eigenvalues & diagonalization — GRE problem types

Scope: recurring eigenvalue, characteristic-polynomial, diagonalizability, and matrix-power patterns on the GRE Mathematics Subject Test, organized by the six boundary sub-skills below. Neighboring linear-algebra topics (Gaussian elimination/rank, raw determinant computation, inner products/Gram–Schmidt, general linear-map and vector-space theory, and full Markov steady-state setups) are handled by other agents and are excluded here.

> Difficulty is **GRE-relative** and frequencies are **qualitative judgments** from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep — not counted statistics, and no specific question numbers are cited. The exam is **no-calculator**, so matrices are small (2×2 or 3×3), numbers stay clean, and eigenvalues are almost always small integers.

---

## Eigenvalues & eigenvectors

### 1. Eigenvalues of an explicit small matrix

- **What it asks:** Find all eigenvalues of a given explicit 2×2 or 3×3 matrix.
- **Solve approach:** Solve \(\det(A-\lambda I)=0\). For 2×2, skip the expansion and use \(\lambda^2-(\operatorname{tr}A)\lambda+\det A=0\); for 3×3 look for an obvious integer root (or exploit a zero row/column, or triangular structure) before factoring. No-calculator design guarantees the roots come out clean.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** Find the eigenvalues of \(\begin{pmatrix}2 & 1\\ 1 & 2\end{pmatrix}\).

### 2. Find or verify an eigenvector

- **What it asks:** Given an eigenvalue, produce the corresponding eigenvector, or decide which of five listed vectors is an eigenvector (and with what eigenvalue).
- **Solve approach:** Solve the homogeneous system \((A-\lambda I)v=0\) for the eigenvector; to test a candidate \(v\), just compute \(Av\) and check whether it is a scalar multiple of \(v\) — the scalar is the eigenvalue. Testing is far faster than solving.
- **Difficulty:** easy–medium · **Frequency:** common (often a sub-step)
- **Example stem:** For \(A=\begin{pmatrix}3 & 1\\ 0 & 2\end{pmatrix}\), which of the following is an eigenvector, and what is its eigenvalue: \((1,0)\), \((1,1)\), or \((1,-1)\)?

### 3. Eigenvalue/eigenvector conceptual true–false

- **What it asks:** A "which of I, II, III must be true" item about general eigenvalue facts for an \(n\times n\) matrix.
- **Solve approach:** Keep the standard facts and their counterexamples ready: \(A\) and \(A^{\mathsf T}\) share eigenvalues (same characteristic polynomial); eigenvectors for **distinct** eigenvalues are linearly independent; but a real matrix need **not** have any real eigenvalue (rotation). Reject a false statement with one small counterexample.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which must hold for every real \(n\times n\) matrix \(A\)? I. \(A\) and \(A^{\mathsf T}\) have the same eigenvalues. II. Eigenvectors for distinct eigenvalues are linearly independent. III. \(A\) has at least one real eigenvalue.

---

## Characteristic polynomial & multiplicity

### 4. Characteristic polynomial and its invariants

- **What it asks:** Compute the characteristic polynomial of a small matrix, or read the trace/determinant/eigenvalues off a given characteristic polynomial.
- **Solve approach:** \(\det(A-\lambda I)\); for an \(n\times n\) matrix the \(\lambda^{n-1}\) coefficient is \(\pm\operatorname{tr}A\) and the constant term is \(\pm\det A\), so you can extract trace and determinant without finding the roots. Factor to get the eigenvalues.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** The characteristic polynomial of a 3×3 matrix \(A\) is \(-\lambda^{3}+5\lambda^{2}-6\lambda\). Find \(\operatorname{tr}A\) and \(\det A\).

### 5. Algebraic vs. geometric multiplicity

- **What it asks:** For a matrix with a repeated eigenvalue, find the dimension of the eigenspace (geometric multiplicity), or compare it to the algebraic multiplicity.
- **Solve approach:** Geometric multiplicity \(=\dim\ker(A-\lambda I)=n-\operatorname{rank}(A-\lambda I)\), and it always satisfies \(1\le\text{geometric}\le\text{algebraic}\). A gap (geometric < algebraic) is exactly the defect that blocks diagonalization.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** For \(A=\begin{pmatrix}2&1&0\\0&2&0\\0&0&2\end{pmatrix}\), the eigenvalue 2 has algebraic multiplicity 3. What is its geometric multiplicity?

### 6. Cayley–Hamilton: reduce powers or invert

- **What it asks:** Use the fact that a matrix satisfies its own characteristic (or a given) polynomial to express a high power or the inverse in terms of lower powers.
- **Solve approach:** From a relation like \(A^{2}=A+2I\), rearrange to isolate \(I\): \(A(A-I)=2I\Rightarrow A^{-1}=\tfrac12(A-I)\); to reduce \(A^{3}\), multiply the relation by \(A\) and substitute repeatedly. Every square matrix satisfies its characteristic polynomial.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** A matrix \(A\) satisfies \(A^{2}=A+2I\). Express \(A^{-1}\) in terms of \(A\) and \(I\).

---

## Diagonalizability & diagonalization

### 7. Decide whether a matrix is diagonalizable

- **What it asks:** Determine whether a given matrix is diagonalizable (over \(\mathbb{R}\) or \(\mathbb{C}\)).
- **Solve approach:** Check each **repeated** eigenvalue: diagonalizable iff geometric multiplicity equals algebraic multiplicity for every eigenvalue (equivalently, \(n\) independent eigenvectors exist). A repeated eigenvalue with a deficient eigenspace (e.g. a Jordan block) is not diagonalizable.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Is \(\begin{pmatrix}1 & 1\\ 0 & 1\end{pmatrix}\) diagonalizable over \(\mathbb{R}\)?

### 8. Distinct eigenvalues ⇒ diagonalizable (shortcut)

- **What it asks:** A conceptual/consequence question that hinges on "\(n\) distinct eigenvalues guarantees diagonalizability."
- **Solve approach:** Distinct eigenvalues give independent eigenvectors, so the matrix is automatically diagonalizable — but note that invertibility is **separate** (a distinct eigenvalue may be 0). Use this to answer without any computation.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** A real 3×3 matrix has three distinct eigenvalues. Which must be true? I. \(A\) is diagonalizable. II. \(A\) is invertible. III. \(A\) has three linearly independent eigenvectors.

### 9. Similar matrices and shared invariants

- **What it asks:** Decide which quantities are preserved under similarity \(B=P^{-1}AP\), or whether two given matrices can be similar.
- **Solve approach:** Similar matrices share characteristic polynomial, eigenvalues, trace, determinant, and rank — but **not** individual entries or eigenvectors. Mismatched trace or determinant is a quick way to prove two matrices are not similar.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** If \(A\) and \(B\) are similar, which need NOT be equal? I. \(\det A\) and \(\det B\). II. the eigenvalues of \(A\) and \(B\). III. the eigenvectors of \(A\) and \(B\).

---

## Trace & determinant from eigenvalues

### 10. Missing eigenvalue from the trace

- **What it asks:** Given all but one eigenvalue (or a symmetric relation among them) plus the trace, find the remaining eigenvalue or a combination.
- **Solve approach:** Sum of eigenvalues (with multiplicity) equals the trace. Subtract the known eigenvalues from \(\operatorname{tr}A\); combine with the determinant relation when two unknowns remain.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** A 3×3 matrix has trace 6, and two of its eigenvalues are 1 and 2. What is the third eigenvalue?

### 11. Determinant as the product of eigenvalues (and singularity)

- **What it asks:** Compute a determinant from the eigenvalues, or detect singularity via a zero eigenvalue (sometimes solving for a parameter that makes the matrix singular).
- **Solve approach:** \(\det A=\prod\lambda_i\). Hence \(A\) is singular iff \(0\) is an eigenvalue iff \(\det A=0\); the number of zero eigenvalues equals \(n-\operatorname{rank}A\). Combine with the trace relation to pin down individual eigenvalues.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** A 3×3 matrix has eigenvalues 2, 3, and \(-1\). What is \(\det A\)?

---

## Eigenvalues of special matrices

### 12. Triangular or diagonal matrix

- **What it asks:** Find the eigenvalues (or determinant) of an upper/lower triangular or diagonal matrix.
- **Solve approach:** The eigenvalues are exactly the diagonal entries — no computation needed. A corollary the exam likes: a **strictly** triangular (nilpotent) matrix has all diagonal entries 0, hence every eigenvalue is 0 even though the matrix is nonzero.
- **Difficulty:** easy · **Frequency:** common (often embedded)
- **Example stem:** Find the eigenvalues of \(\begin{pmatrix}4 & 7 & -2\\ 0 & 1 & 5\\ 0 & 0 & 3\end{pmatrix}\).

### 13. Eigenvalues of a function of A

- **What it asks:** Given the eigenvalues of \(A\), find the eigenvalues of \(A^{k}\), \(A^{-1}\), \(A+cI\), or a polynomial \(p(A)\).
- **Solve approach:** If \(Av=\lambda v\) then \(A^{k}v=\lambda^{k}v\), \(A^{-1}v=\lambda^{-1}v\), \((A+cI)v=(\lambda+c)v\), and \(p(A)v=p(\lambda)v\) — same eigenvector, transformed eigenvalue. Apply the map to each eigenvalue. A GRE staple.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** The eigenvalues of \(A\) are \(2\) and \(-3\). What are the eigenvalues of \(A^{2}-I\)?

### 14. Real symmetric matrices

- **What it asks:** A property or consequence question about a real symmetric (or given orthogonally diagonalizable) matrix.
- **Solve approach:** Real symmetric ⇒ all eigenvalues are real, eigenvectors for distinct eigenvalues are orthogonal, and the matrix is always (orthogonally) diagonalizable — even with repeated eigenvalues. These often let you reject "complex eigenvalue" or "not diagonalizable" distractors immediately.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which must be true of a real symmetric matrix? I. all eigenvalues are real. II. it is diagonalizable. III. eigenvectors for distinct eigenvalues are orthogonal.

### 15. Projections and idempotents

- **What it asks:** Find the eigenvalues, trace, or rank of an idempotent matrix (\(A^{2}=A\)), e.g. a projection.
- **Solve approach:** \(A^{2}=A\) forces every eigenvalue to satisfy \(\lambda^{2}=\lambda\), so \(\lambda\in\{0,1\}\); the multiplicity of 1 equals the rank, and \(\operatorname{tr}A=\operatorname{rank}A\). Idempotents are automatically diagonalizable.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** \(A\) is a 4×4 matrix with \(A^{2}=A\) and rank 3. List its eigenvalues with multiplicities and give \(\operatorname{tr}A\).

### 16. Orthogonal and rotation matrices

- **What it asks:** Count real eigenvalues of, or find the eigenvalues/determinant of, a rotation or orthogonal matrix.
- **Solve approach:** Orthogonal matrices have every eigenvalue on the unit circle (\(|\lambda|=1\)) and \(\det=\pm1\). A 2×2 rotation by \(\theta\) has eigenvalues \(e^{\pm i\theta}=\cos\theta\pm i\sin\theta\), which are non-real for \(0<\theta<\pi\), so it has no real eigenvector.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many real eigenvalues does \(\begin{pmatrix}\cos\theta & -\sin\theta\\ \sin\theta & \cos\theta\end{pmatrix}\) have when \(0<\theta<\pi\)?

### 17. Rank-one and structured matrices

- **What it asks:** Find the eigenvalues of an all-ones matrix, a matrix of the form \(aI+bJ\), or a rank-one outer product \(uv^{\mathsf T}\).
- **Solve approach:** A rank-one \(uv^{\mathsf T}\) has one nonzero eigenvalue \(v^{\mathsf T}u\) (eigenvector \(u\)) and \(0\) with multiplicity \(n-1\). The all-ones \(J_n\) has eigenvalues \(n\) (once) and \(0\) (\(n-1\) times); then \(aI+bJ\) shifts these to \(a+nb\) and \(a\) via the "function of \(A\)" rule.
- **Difficulty:** medium–hard · **Frequency:** rare–occasional
- **Example stem:** Find the eigenvalues of the 3×3 matrix all of whose entries equal 2.

---

## Matrix powers via diagonalization

### 18. Compute a high power via diagonalization

- **What it asks:** Compute \(A^{n}\) (a specific power, a general \(n\), or one entry) for a small non-diagonal matrix.
- **Solve approach:** Diagonalize \(A=PDP^{-1}\Rightarrow A^{n}=PD^{n}P^{-1}\), where \(D^{n}\) just raises the eigenvalues to the \(n\). For a 2×2 upper-triangular matrix with distinct diagonal entries you can write the power directly. Trace/determinant of \(A^n\) follow from \(\lambda_i^{\,n}\) without forming the matrix.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** For \(A=\begin{pmatrix}1 & 2\\ 0 & 3\end{pmatrix}\), find \(A^{n}\).

### 19. Long-run behavior via the dominant eigenvalue

- **What it asks:** Determine \(\lim_{n\to\infty}A^{n}\) (or the limiting direction of \(A^{n}v\)) from the eigenvalues.
- **Solve approach:** In the eigenbasis, \(A^{n}\) scales each component by \(\lambda_i^{\,n}\): if every \(|\lambda_i|<1\) the powers tend to the zero matrix; the eigenvalue of largest modulus (the dominant eigenvalue) controls growth/decay and the limiting direction. (Full stochastic-matrix steady-state problems are a neighboring topic.)
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** If every eigenvalue \(\lambda\) of a matrix \(A\) satisfies \(|\lambda|<1\), what is \(\lim_{n\to\infty}A^{n}\)?
