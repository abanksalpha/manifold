# Vector spaces & linear maps — GRE problem types

_Scope: recurring vector-space and linear-map patterns on the GRE Mathematics Subject Test (grounded in released forms GR0568/GR8767/GR9367/GR9768/GR1268/GR3768 and standard prep). Linear algebra is a small, mostly conceptual slice of each form that rewards structural reasoning over arithmetic; items are short and no-calculator-friendly. Difficulty/frequency are relative to this exam (frequency ≈ how reliably a pattern recurs within this topic's appearances). Pure matrix computation (determinants, products, inverses) and eigenvalues/diagonalization are separate topics handled elsewhere._

## Vector spaces & subspaces

### 1. Subspace test (which subsets are subspaces)

- **What it asks:** Given several subsets of `Rⁿ` (or of a space of matrices, polynomials, or functions), decide which ones are subspaces.
- **Solve approach:** Check the three closure conditions — contains the zero vector, closed under addition, closed under scalar multiplication. Fast disqualifiers: a nonzero constant/affine condition (e.g. `x + y = 1`) fails the zero test; any nonlinear condition (products, squares, `|·|`, `max`) fails closure. A single homogeneous linear condition always passes.
- **Difficulty / Frequency:** Medium · Common
- **Example stem:** _"Which of the following subsets of `R³` is a subspace? I. `{(x,y,z): x + 2y = 0}` II. `{(x,y,z): x + 2y = 1}` III. `{(x,y,z): xy = 0}`"_

### 2. Dimension of a familiar vector space

- **What it asks:** State the dimension of a standard space — `n×n` symmetric, skew-symmetric, or trace-zero matrices; polynomials of degree `≤ n`; possibly with an extra linear constraint.
- **Solve approach:** Know the standard counts: `dim Pₙ = n+1`; all `n×n` matrices `= n²`; symmetric `= n(n+1)/2`; skew-symmetric `= n(n−1)/2`; trace-zero `= n² − 1`; upper-triangular `= n(n+1)/2`. Each independent linear constraint (e.g. `p(1) = 0`) drops the dimension by 1.
- **Difficulty / Frequency:** Easy–medium · Occasional
- **Example stem:** _"What is the dimension of the vector space of `3×3` real symmetric matrices?"_

### 3. Sum & intersection of subspaces (dimension formula)

- **What it asks:** Given two subspaces, find the dimension of their sum or intersection, or the smallest/largest possible value of one of these.
- **Solve approach:** Apply `dim(U + W) = dim U + dim W − dim(U ∩ W)`. The sum is direct iff `U ∩ W = {0}` iff `dim(U + W) = dim U + dim W`. Inside `Rⁿ`, `dim(U + W) ≤ n`, which often forces a minimum for `dim(U ∩ W)`.
- **Difficulty / Frequency:** Medium · Rare
- **Example stem:** _"`U` and `W` are subspaces of `R⁵` with `dim U = 3` and `dim W = 4`. The smallest possible value of `dim(U ∩ W)` is …"_

## Linear independence, basis & dimension

### 4. Test independence / spanning / basis of explicit vectors

- **What it asks:** Decide whether a given list of vectors is linearly independent, spans a given space, or forms a basis.
- **Solve approach:** Put the vectors as the rows (or columns) of a matrix and row-reduce: independent ⇔ a pivot in every vector's column (rank = number of vectors); they span `Rⁿ` ⇔ rank `= n`; a basis ⇔ both. For exactly `n` vectors in `Rⁿ`, nonzero determinant ⇔ basis, so any one of independence/spanning implies the other.
- **Difficulty / Frequency:** Medium · Common
- **Example stem:** _"Which of the following sets of three vectors is a basis for `R³`?"_

### 5. Parameter value forcing linear dependence

- **What it asks:** Find the value(s) of a parameter for which a set of vectors becomes linearly dependent (equivalently, fails to be a basis).
- **Solve approach:** For `n` vectors in `Rⁿ`, they are dependent exactly when the determinant of the matrix they form is `0`; set `det = 0` and solve for the parameter. Equivalently, row-reduce and force a zero row. (The question is about dependence even though a determinant does the work.)
- **Difficulty / Frequency:** Medium · Occasional
- **Example stem:** _"For which value of `k` are `(1,2,3)`, `(2,5,7)`, and `(1,3,k)` linearly dependent?"_

### 6. Dimension of a span; extract or extend a basis

- **What it asks:** Find the dimension of the span of some vectors, pick a basis from among them, or extend an independent set to a basis of the whole space.
- **Solve approach:** Row-reduce; the number of pivots is the dimension of the span, and the original vectors in the pivot positions form a basis of it. To extend, adjoin standard basis vectors and keep each one that introduces a new pivot.
- **Difficulty / Frequency:** Medium · Occasional
- **Example stem:** _"The subspace of `R⁴` spanned by `(1,1,0,0)`, `(0,1,1,0)`, and `(1,2,1,0)` has dimension …"_

### 7. Coordinates relative to a basis / change of basis

- **What it asks:** Express a vector in coordinates with respect to a nonstandard basis, or convert coordinates between two bases.
- **Solve approach:** Solve `v = c₁b₁ + … + cₙbₙ` for the coefficients (a small linear system). The change-of-basis matrix has the basis vectors as its columns; its inverse converts standard coordinates into the new basis.
- **Difficulty / Frequency:** Medium · Rare
- **Example stem:** _"In the basis `{(1,1), (1,−1)}` of `R²`, the coordinate vector of `(3,1)` is …"_

## Rank–nullity theorem

### 8. Injective / surjective from domain–codomain dimensions

- **What it asks:** For a linear map between spaces of stated dimensions (e.g. `T: R⁵ → R³`), decide which statements about being one-to-one, onto, or about the kernel must be true.
- **Solve approach:** Use `rank + nullity = dim(domain)` with `rank ≤ min(dim domain, dim codomain)`. If `dim domain > dim codomain`, the map cannot be injective (`nullity ≥ dim domain − dim codomain > 0`); if `dim domain < dim codomain`, it cannot be surjective. Injective ⇔ nullity `0`; surjective ⇔ `rank = dim codomain`.
- **Difficulty / Frequency:** Medium · Common
- **Example stem:** _"If `T: R⁵ → R³` is linear, which of the following must be true about its kernel and whether it is one-to-one or onto?"_

### 9. Compute rank and nullity of a matrix or map

- **What it asks:** Find the rank, the nullity, or the dimension of the image/kernel of an explicitly given matrix or map.
- **Solve approach:** Row-reduce: rank = number of pivots (`= dim column space = dim row space`), nullity = number of pivot-free columns; verify with `rank + nullity = number of columns`. Spotting proportional rows/columns short-cuts the count.
- **Difficulty / Frequency:** Easy–medium · Common
- **Example stem:** _"The rank of the matrix with rows `(1,2,3)`, `(2,4,6)`, `(1,1,1)` is …"_

## Column / row / null space & the four fundamental subspaces

### 10. Basis & dimension of the null space (solution space of `Ax = 0`)

- **What it asks:** Find the dimension or a basis of the solution space of a homogeneous system, or recognize that this solution set is a subspace.
- **Solve approach:** Row-reduce `A`; each free variable contributes one null-space basis vector, so `dim = (#columns) − rank`. Read off each basis vector by setting one free variable to `1` and the rest to `0`.
- **Difficulty / Frequency:** Medium · Occasional
- **Example stem:** _"The solution set of `x + y + z = 0` and `x − y = 0` in `R³` has dimension …"_

### 11. Column space & consistency of `Ax = b`

- **What it asks:** Decide for which `b` the system `Ax = b` is solvable, or how many solutions it has, in terms of rank and the column space.
- **Solve approach:** `Ax = b` is consistent ⇔ `b` lies in the column space ⇔ `rank[A] = rank[A | b]`. When consistent, the solution set is a translate of the null space: a unique solution when nullity `0`, otherwise an affine subspace of dimension `= nullity`.
- **Difficulty / Frequency:** Medium · Occasional
- **Example stem:** _"For a `3×3` matrix `A` of rank `2`, the system `Ax = b` has how many solutions (none / exactly one / infinitely many / possibly none or infinitely many)?"_

## Linear transformations & their matrices

### 12. Is the map linear?

- **What it asks:** Given a map between vector spaces, determine whether it is a linear transformation.
- **Solve approach:** Verify additivity `T(u+v) = T(u) + T(v)` and homogeneity `T(cv) = cT(v)`; note `T(0) = 0` is necessary. Common non-linear traps: a constant/affine term, squares or products of coordinates, norms or absolute values.
- **Difficulty / Frequency:** Easy–medium · Occasional
- **Example stem:** _"Which of the following maps `R² → R²` is linear? I. `(x,y) ↦ (x+1, y)` II. `(x,y) ↦ (y, x)` III. `(x,y) ↦ (x², y)`"_

### 13. Matrix of a linear transformation in given bases

- **What it asks:** Find the matrix of a linear map — often differentiation on polynomials, a rotation/reflection/projection, or a map defined by its action on basis vectors — with respect to specified bases.
- **Solve approach:** The `j`-th column is the image of the `j`-th basis vector, written in coordinates of the target basis. For `d/dx` use the monomial basis; for geometric maps recall the rotation matrix `[[cos θ, −sin θ], [sin θ, cos θ]]` and the standard reflection/projection forms.
- **Difficulty / Frequency:** Medium · Occasional
- **Example stem:** _"With respect to the basis `{1, x, x²}`, the matrix of the differentiation operator `D` on polynomials of degree `≤ 2` is …"_

### 14. Kernel & image of a concrete transformation

- **What it asks:** Identify the kernel or image (or their dimensions) of a specific transformation such as differentiation, an evaluation/integration map, or trace.
- **Solve approach:** Read the kernel off directly (e.g. `ker(d/dx)` on `Pₙ` is the constants, dimension `1`) and apply rank–nullity for the other dimension. Describe the image as the span of the images of the basis elements.
- **Difficulty / Frequency:** Medium · Occasional
- **Example stem:** _"The dimension of the kernel of the map `T(p) = p′` on polynomials of degree `≤ 3` is …"_

### 15. Geometric operators: projection and reflection identities

- **What it asks:** Use the defining algebraic identity of a projection (`T² = T`) or reflection/involution (`T² = I`), or identify such an operator from a matrix or description.
- **Solve approach:** An (orthogonal) projection is idempotent, `T² = T`; a reflection is an involution, `T² = I`; a rotation preserves lengths. Recognizing these relations lets you identify the operator or evaluate powers/`I − T` without diagonalizing (`Rⁿ = ker T ⊕ im T` for a projection, and `I − T` is also a projection).
- **Difficulty / Frequency:** Medium · Occasional/rare
- **Example stem:** _"A linear operator `P` on `Rⁿ` satisfies `P² = P` and is neither `0` nor `I`. Which of the following must be true (e.g. `I − P` is also idempotent; `im P ∩ ker P = {0}`)?"_

## Inner products, orthogonality & Gram–Schmidt

### 16. Orthogonal projection onto a line or subspace; nearest point & distance

- **What it asks:** Compute the orthogonal projection of a vector onto a line or subspace, the closest point in that subspace, or the distance from a point to it.
- **Solve approach:** Onto a single vector `u`: `proj_u(v) = (⟨v,u⟩ / ⟨u,u⟩) u`. Onto a subspace: project onto each vector of an _orthogonal_ basis and add. The distance is `‖v − proj(v)‖`, and `v − proj(v)` lies in the orthogonal complement.
- **Difficulty / Frequency:** Medium · Occasional
- **Example stem:** _"The projection of `(3,4)` onto the line spanned by `(1,1)` is …"_

### 17. Inner products: norm, angle, orthogonality, Cauchy–Schwarz

- **What it asks:** Compute a norm, an inner product or angle, find a value making two vectors orthogonal, or apply the Cauchy–Schwarz / triangle inequality (sometimes with a function inner product `∫ f g`).
- **Solve approach:** Use `⟨u,v⟩ = Σ uᵢvᵢ` (or `∫ f g`), `‖v‖ = √⟨v,v⟩`, and `cos θ = ⟨u,v⟩ / (‖u‖‖v‖)`; orthogonal ⇔ `⟨u,v⟩ = 0`; `|⟨u,v⟩| ≤ ‖u‖‖v‖` bounds the inner product.
- **Difficulty / Frequency:** Easy–medium · Occasional
- **Example stem:** _"For what value of `c` are `(1, 2, c)` and `(3, −1, 2)` orthogonal in `R³`?"_

### 18. Orthogonal complement & orthogonality of the four subspaces

- **What it asks:** Find the dimension or a description of a subspace's orthogonal complement, or use the fact that the fundamental subspaces come in orthogonal pairs.
- **Solve approach:** `dim W + dim W⊥ = n` and `(W⊥)⊥ = W`. For a matrix, the null space is the orthogonal complement of the row space, and the left null space is the orthogonal complement of the column space.
- **Difficulty / Frequency:** Medium · Rare/occasional
- **Example stem:** _"If `W` is the plane `x + y + z = 0` in `R³`, then `W⊥` is spanned by … and has dimension …"_

### 19. Orthonormal bases: Gram–Schmidt & orthogonal matrices

- **What it asks:** Produce an orthogonal/orthonormal basis from a given basis (Gram–Schmidt), or use the defining property of an orthogonal matrix.
- **Solve approach:** Gram–Schmidt: subtract off the projections onto the vectors already built, then normalize. An orthogonal matrix has orthonormal columns, satisfies `QᵀQ = I` (so `Q⁻¹ = Qᵀ`), and preserves norms and inner products.
- **Difficulty / Frequency:** Medium–hard · Rare
- **Example stem:** _"Applying Gram–Schmidt to `(1,1,0)` then `(1,0,1)`, the second orthogonal vector produced is …"_
