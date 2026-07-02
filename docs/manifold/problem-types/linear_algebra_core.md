# Linear algebra: matrices & systems — GRE problem types

Scope: the _matrix and linear-system_ mechanics of linear algebra on the GRE Mathematics Subject Test — Gaussian elimination / RREF, matrix arithmetic and inverses, determinants and their properties, solvability and the Invertible Matrix Theorem, and the equation `Ax = b`. **Eigenvalues / eigenvectors / characteristic polynomials** and **vector spaces / basis / dimension / linear independence as an abstract topic** are separate DAG nodes handled by other agents and are excluded here (rank and the invertibility conditions below touch them only as far as solving systems requires). Difficulty is GRE-relative and there is **no calculator**, so entries and answers are engineered to stay clean; frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep, not counted statistics, and no specific question numbers are cited.

---

## Gaussian elimination & RREF

### Solve a small linear system

- **What it asks:** Solve a 2- or 3-variable linear system for one unknown, all unknowns, or a linear combination of them — often as a subresult that feeds a later computation.
- **Solve approach:** Elimination/substitution, or row-reduce the augmented matrix. When only a combination like `x + y + z` is wanted, add/subtract equations to produce it directly rather than solving fully; clean coefficients signal a fast elimination.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "If `x + y + z = 6`, `x − y + 2z = 5`, and `2x + y − z = 1`, then `z = …`"

### Parameter-dependent solvability (unique / none / infinitely many)

- **What it asks:** For a system whose coefficients or constants contain a parameter, decide for which value(s) it has a unique solution, no solution, or infinitely many.
- **Solve approach:** Row-reduce carrying the parameter. A square system fails to be _unique_ exactly when the coefficient determinant is `0`; at those values inspect the augmented column (a pivot in the last column ⇒ inconsistent / no solution, otherwise a free variable ⇒ infinitely many). Watch for a row reducing to `[0 … 0 | c]`.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "For which value of `k` does `{ x + 2y = 1, 3x + ky = 2 }` have no solution?"

### Rank / echelon form of a matrix

- **What it asks:** Find the rank of a given matrix, or equivalently the number of independent equations / pivots, sometimes to report the dimension of the solution set.
- **Solve approach:** Row-reduce to (reduced) row-echelon form and count nonzero rows (pivots). Spotting a row that is a scalar multiple or sum of others drops the rank without full reduction.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "What is the rank of the matrix with rows `(1, 2, 3)`, `(2, 4, 6)`, `(1, 0, 1)`?"

---

## Matrix operations & inverses

### Matrix multiplication and non-commutativity

- **What it asks:** Compute a product `AB` (or a single requested entry), or recognize that matrix multiplication is not commutative (`AB ≠ BA` in general).
- **Solve approach:** Row-of-`A` times column-of-`B`; for one entry, compute only the needed row·column dot product instead of the whole product. Check conformability of dimensions first.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "For `A = [[1, 2], [0, 1]]` and `B = [[1, 0], [3, 1]]`, the `(1, 2)` entry of `AB` is …"

### Powers of a structured matrix

- **What it asks:** Compute `Aⁿ` (or a specific power) for a matrix with special structure — a shear/triangular matrix, a rotation, a diagonal matrix, or one that is nilpotent, idempotent, or an involution.
- **Solve approach:** Compute `A²` first and look for a pattern: `A² = I` (involution), `A² = 0` (nilpotent), `A² = A` (idempotent), or a clean recurrence. A rotation by `θ` raised to the `n` is rotation by `nθ`; a diagonal matrix powers entrywise.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "If `A = [[1, 1], [0, 1]]`, then `Aⁿ = …`"

### Inverse of a 2×2 matrix (and when it exists)

- **What it asks:** Compute the inverse of a 2×2 matrix, or determine whether/when a given matrix is invertible.
- **Solve approach:** For `[[a, b], [c, d]]` the inverse is `1/(ad − bc) · [[d, −b], [−c, a]]`; it exists iff `ad − bc ≠ 0`. For 3×3, use row reduction of `[A | I]` or the adjugate over the determinant.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "The inverse of `[[2, 1], [5, 3]]` is …"

### Identities that hold for all matrices (true/false)

- **What it asks:** Identify which algebraic statement is valid for all (square/invertible) matrices — frequently in a "which of I, II, III" format — testing transpose, inverse, and commutativity rules.
- **Solve approach:** Know the standard identities `(AB)ᵀ = BᵀAᵀ`, `(AB)⁻¹ = B⁻¹A⁻¹` (order reverses), `(Aᵀ)⁻¹ = (A⁻¹)ᵀ`; disprove the tempting false ones — `AB = BA`, `(A + B)² = A² + 2AB + B²`, `(AB)⁻¹ = A⁻¹B⁻¹` — with a quick 2×2 counterexample.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "Which of the following holds for all invertible `n×n` matrices `A`, `B`? I. `(AB)⁻¹ = B⁻¹A⁻¹` II. `(A + B)² = A² + 2AB + B²` III. `(Aᵀ)ᵀ = A`"

### Trace value and properties

- **What it asks:** Compute a trace, or use trace properties such as linearity and `tr(AB) = tr(BA)` / invariance under similarity.
- **Solve approach:** Trace = sum of diagonal entries; it is linear (`tr(cA + B) = c·tr(A) + tr(B)`) and cyclic (`tr(AB) = tr(BA)`), so `tr(AB) − tr(BA) = 0` regardless of the matrices. (Trace as the _sum of eigenvalues_ is developed in the eigenvalues topic.)
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "If `A` is `4×4` with `tr(A) = 5`, then `tr(3A + 2I) = …`"

---

## Determinants & cofactor expansion (and properties)

### Direct determinant computation (2×2, 3×3)

- **What it asks:** Evaluate the determinant of a specific numeric 2×2 or 3×3 matrix.
- **Solve approach:** 2×2 is `ad − bc`. For 3×3 use cofactor (Laplace) expansion along the row or column with the most zeros, or the Sarrus diagonal rule; creating a zero with one row operation first can shorten the arithmetic.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "The determinant of `[[1, 2, 0], [0, 3, 1], [2, 0, 1]]` is …"

### Determinant transformation rules

- **What it asks:** Given `det(A)` (and maybe `det(B)`), compute the determinant of a related matrix — `det(cA)`, `det(AB)`, `det(A⁻¹)`, `det(Aᵀ)`, or `det(Aᵏ)`.
- **Solve approach:** Apply `det(cA) = cⁿ·det(A)` for `n×n` (the exam's favorite trap), `det(AB) = det(A)·det(B)`, `det(A⁻¹) = 1/det(A)`, `det(Aᵀ) = det(A)`, `det(Aᵏ) = det(A)ᵏ`.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "If `A` is a `3×3` matrix with `det(A) = 4`, then `det(2A) = …`"

### Effect of row/column operations and special rows

- **What it asks:** Determine how the determinant changes under a row/column operation, or evaluate a determinant made easy (often `0`) by a structural feature.
- **Solve approach:** Swapping two rows multiplies the determinant by `−1`; scaling a row by `c` multiplies it by `c`; adding a multiple of one row to another leaves it unchanged. A zero row, two equal/proportional rows, or a row that is a linear combination of others forces `det = 0`; a triangular matrix's determinant is the product of its diagonal.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "If `B` is obtained from a `3×3` matrix `A` by swapping two rows and then doubling one row, then `det(B) = …` (in terms of `det(A)`)."

### Parameter that makes a matrix singular (solve det = 0)

- **What it asks:** Find the value(s) of a variable appearing in a matrix's entries that make it non-invertible (singular).
- **Solve approach:** Write the determinant as a function of the parameter, set it equal to `0`, and solve. (The special case where the parameter is `λ` subtracted along the diagonal — `det(A − λI) = 0` — is the _characteristic equation_ and belongs to the eigenvalues topic.)
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "For which value(s) of `x` is `[[x, 2], [8, x]]` not invertible?"

---

## Solvability of linear systems & the invertible matrix theorem

### Invertible Matrix Theorem equivalences

- **What it asks:** Identify which condition is equivalent to (or implies) an `n×n` matrix `A` being invertible, usually in a "which of the following" list.
- **Solve approach:** Recall the equivalence chain: `A` invertible ⇔ `det(A) ≠ 0` ⇔ `rank(A) = n` ⇔ `Ax = 0` has only the trivial solution ⇔ `Ax = b` has a unique solution for every `b` ⇔ the columns (and rows) are linearly independent / span. Any one of these implies all the others.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For an `n×n` matrix `A`, which of the following is/are equivalent to `A` being invertible? I. `det(A) ≠ 0` II. `Ax = 0` has only `x = 0` III. the rows of `A` are linearly dependent"

### Homogeneous systems & nontrivial solutions

- **What it asks:** Decide when a homogeneous system `Ax = 0` has a nonzero solution, or for what parameter value it does.
- **Solve approach:** A square homogeneous system has a nontrivial solution iff `det(A) = 0` (equivalently `rank < n`); a system with **more unknowns than equations** always has a nontrivial solution. To find the parameter, set the coefficient determinant to `0`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For which value of `a` does `{ ax + y = 0, x + ay = 0 }` have a solution other than `(0, 0)`?"

---

## Matrix equations Ax = b

### Solve Ax = b using the inverse (and consistency)

- **What it asks:** Solve `Ax = b` for `x` (with `A` invertible), or express the solution / decide whether a solution exists.
- **Solve approach:** When `A` is invertible the unique solution is `x = A⁻¹b`; computationally it is usually faster to row-reduce `[A | b]` than to build `A⁻¹`. If `A` is singular, `Ax = b` is consistent only when `b` is compatible with the reduced rows (no `[0 … 0 | nonzero]` row).
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "If `A` is invertible and `Ax = b`, then `x = …` (in terms of `A` and `b`)."

### Solve a matrix equation for an unknown matrix

- **What it asks:** Solve for an unknown matrix `X` in a relation such as `AX = B`, `XA = B`, or `AXB = C`, given the other (invertible) matrices.
- **Solve approach:** Multiply by the appropriate inverse **on the correct side**, since order matters: `AX = B ⇒ X = A⁻¹B`; `XA = B ⇒ X = BA⁻¹`; `AXB = C ⇒ X = A⁻¹CB⁻¹`.
- **Difficulty:** medium. **Frequency:** occasional/rare.
- **Example stem:** "If `A` and `B` are invertible and `AXB = I`, then `X = …`"
