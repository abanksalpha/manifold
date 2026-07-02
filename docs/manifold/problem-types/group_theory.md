# Group theory — GRE problem types

Scope: recurring group-theory question patterns on the GRE Mathematics Subject Test (the abstract-algebra slice of "additional topics," recognition tier), organized by the seven boundary sub-skills below. Rings, fields, and other ring/module structures are handled by separate agents and are excluded here.

> **Orientation & honesty notes.** Group theory is a small part of the ~25% "additional topics" section and is tested at the _recognize_ tier: definitions, one-step computations, and single-theorem applications rather than proofs. Difficulty labels are **GRE-relative**, and frequency labels are relative to _how often group-theory items appear at all_ (they are not a large share of the 66 questions). Because **no calculator is allowed**, orders, moduli, and group sizes are kept small and clean, and several items use the "which of I, II, III must be true" answer format. Frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep material, not counted statistics; no specific question numbers are cited.

---

## Groups, subgroups & order of elements

### 1. Order of a group element

- **What it asks:** Find the order of a specified element (the least positive \(k\) with \(g^{k}=e\)), typically in \(\mathbb{Z}_n\) under addition, the units mod \(n\) under multiplication, a group of roots of unity, or a small matrix group.
- **Solve approach:** Use the least-\(k\) definition. In \((\mathbb{Z}_n,+)\), the order of \(a\) is \(n/\gcd(a,n)\). For a multiplicative/units group, take successive powers until reaching the identity. For an element of a direct product, take the \(\operatorname{lcm}\) of the coordinate orders.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** In the additive group \(\mathbb{Z}_{18}\), what is the order of the element \(12\)?

### 2. Counting elements of a given order

- **What it asks:** Count how many elements of a group have a particular order (very often order 2, i.e. the self-inverse elements).
- **Solve approach:** In a cyclic group of order \(n\), the number of elements of order \(d\) is \(\varphi(d)\) when \(d\mid n\) and \(0\) otherwise. Elements of order 2 satisfy \(x=x^{-1}\). In a symmetric group, sort elements by cycle type (a product of disjoint 2-cycles has order 2) and count each type.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many elements of order 2 does \(\mathbb{Z}_2\times\mathbb{Z}_4\) contain?

### 3. Recognizing subgroups (subgroup test)

- **What it asks:** Decide which of several subsets of a group is actually a subgroup, or verify that a given subset qualifies.
- **Solve approach:** Apply the subgroup test: the subset is nonempty and closed under the operation and under inverses (equivalently \(ab^{-1}\in H\) for all \(a,b\in H\)). Confirm the identity is present; a _finite_ nonempty subset closed under the operation is automatically a subgroup. Watch for subsets missing the identity or inverses.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Which of the following subsets of \((\mathbb{Z},+)\) is a subgroup: the even integers, the odd integers, or the nonnegative integers?

---

## Cyclic groups & generators

### 4. Counting generators of a cyclic group

- **What it asks:** Count the generators of a cyclic group of order \(n\) (equivalently, its elements of order \(n\)).
- **Solve approach:** A cyclic group of order \(n\) has exactly \(\varphi(n)\) generators; in \(\mathbb{Z}_n\) these are the residues coprime to \(n\). Compute \(\varphi(n)\) from the prime factorization.
- **Difficulty:** easy · **Frequency:** occasional
- **Example stem:** How many generators does the cyclic group \(\mathbb{Z}_{12}\) have?

### 5. Deciding whether a group is cyclic

- **What it asks:** Determine whether a given group (often a direct product or a units group) is cyclic, or pick which group in a list is / is not cyclic.
- **Solve approach:** \(\mathbb{Z}_m\times\mathbb{Z}_n\) is cyclic iff \(\gcd(m,n)=1\) (then it is \(\cong\mathbb{Z}_{mn}\)); more generally, hunt for an element whose order equals the group order. A group with two distinct subgroups of the same prime order (e.g. \(\mathbb{Z}_2\times\mathbb{Z}_2\)) cannot be cyclic.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Is \(\mathbb{Z}_4\times\mathbb{Z}_6\) cyclic? If not, what is the largest order of any element?

---

## Lagrange's theorem & cosets

### 6. Lagrange divisibility constraints

- **What it asks:** Use "\(|H|\) divides \(|G|\)" (and "element order divides \(|G|\)") to decide which subgroup or element orders are possible, or to draw a conclusion about a group of given order.
- **Solve approach:** Apply Lagrange: every subgroup order and every element order divides \(|G|\); consequently \(a^{|G|}=e\) and any group of prime order is cyclic. Remember the converse fails — a divisor of \(|G|\) need not be a subgroup order (\(A_4\), order 12, has no subgroup of order 6).
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** A group has order 15. Which of these could be the order of one of its elements: 2, 3, 5, or 6?

### 7. Cosets & index

- **What it asks:** Count or list the (left or right) cosets of a subgroup, or use the index \([G:H]=|G|/|H|\).
- **Solve approach:** The distinct cosets partition \(G\) into \(|G|/|H|\) blocks of equal size \(|H|\); build representatives by translating \(H\). In an abelian group left and right cosets coincide.
- **Difficulty:** medium · **Frequency:** occasional (usually embedded in Lagrange reasoning)
- **Example stem:** In \(\mathbb{Z}_{12}\), how many distinct cosets does the subgroup \(\{0,4,8\}\) have, and what are they?

---

## Normal subgroups & quotient groups

### 8. Recognizing normal subgroups

- **What it asks:** Decide whether a given subgroup is normal, or identify which subgroups of a group are normal.
- **Solve approach:** \(H\trianglelefteq G\) iff \(gHg^{-1}=H\) for all \(g\) (equivalently \(gH=Hg\)). Automatic cases: any subgroup of an abelian group, any subgroup of index 2, the kernel of a homomorphism, and the center. A standard non-normal example is a 2-element subgroup \(\langle(1\,2)\rangle\) in \(S_3\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which subgroups of \(S_3\) are normal?

### 9. Identifying a quotient group's structure

- **What it asks:** Determine the structure (order, and which known group) of a quotient \(G/N\).
- **Solve approach:** \(|G/N|=|G|/|N|\); then identify the group of that order from its element orders (is it cyclic?). Quotients of abelian groups are abelian, and \(\mathbb{Z}/m\mathbb{Z}\cong\mathbb{Z}_m\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** In \(G=\mathbb{Z}_4\times\mathbb{Z}_2\), let \(N=\langle(2,0)\rangle\). To which group is \(G/N\) isomorphic?

---

## Homomorphisms & isomorphism theorems

### 10. Counting homomorphisms between groups

- **What it asks:** Count the group homomorphisms from one (usually cyclic) group to another.
- **Solve approach:** A homomorphism out of \(\mathbb{Z}_m\) is determined by the image of a generator, which must be an element whose order divides \(m\); the number of homomorphisms \(\mathbb{Z}_m\to\mathbb{Z}_n\) is \(\gcd(m,n)\). From \(\mathbb{Z}\), any target element works, giving \(|G|\) homomorphisms \(\mathbb{Z}\to G\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many group homomorphisms are there from \(\mathbb{Z}_6\) to \(\mathbb{Z}_9\)?

### 11. Kernel, image & the first isomorphism theorem

- **What it asks:** Compute a homomorphism's kernel or image, or use \(G/\ker\varphi\cong\operatorname{im}\varphi\) to identify a structure.
- **Solve approach:** The kernel is a normal subgroup, and \(\varphi\) is injective iff the kernel is trivial; in the finite case \(|\operatorname{im}\varphi|=|G|/|\ker\varphi|\). Recognize standard maps: \(\det\) on invertible matrices, the sign map \(\operatorname{sgn}\colon S_n\to\{\pm1\}\), and reduction \(\mathbb{Z}\to\mathbb{Z}_n\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** For the sign homomorphism \(\operatorname{sgn}\colon S_4\to\{1,-1\}\), what is the kernel, and what is its order?

### 12. Isomorphic or not? (distinguishing invariants)

- **What it asks:** Decide whether two groups are isomorphic, or select which groups in a list are (pairwise) isomorphic.
- **Solve approach:** Compare invariants preserved by isomorphism: order, abelian-or-not, cyclic-or-not, the multiset of element orders, the count of elements of each order, and the number of subgroups. One differing invariant proves non-isomorphism (e.g. \(\mathbb{Z}_4\) vs \(\mathbb{Z}_2\times\mathbb{Z}_2\): only one has an element of order 4).
- **Difficulty:** medium · **Frequency:** common
- **Example stem:** Are \(\mathbb{Z}_8\), \(\mathbb{Z}_4\times\mathbb{Z}_2\), and \(\mathbb{Z}_2\times\mathbb{Z}_2\times\mathbb{Z}_2\) pairwise non-isomorphic? Justify with a single invariant.

---

## Permutation & symmetric groups (cycle notation)

### 13. Order of a permutation from cycle type

- **What it asks:** Find the order of a permutation given in cycle or two-line notation.
- **Solve approach:** Write it as a product of disjoint cycles; the order is the \(\operatorname{lcm}\) of the cycle lengths. Fixed points are 1-cycles and don't affect the answer.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** What is the order of the permutation \((1\,2\,3)(4\,5)\) in \(S_5\)?

### 14. Permutation products & inverses in cycle notation

- **What it asks:** Multiply two permutations, compute an inverse, or rewrite a permutation as a product of disjoint cycles (or of transpositions).
- **Solve approach:** Compose by tracking where each point goes, then read off the disjoint-cycle form; invert a cycle by reversing its entries. A \(k\)-cycle factors into \(k-1\) transpositions. Fix (and state) whether you compose left-to-right or right-to-left.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Express the inverse of the 4-cycle \((1\,2\,3\,4)\) in cycle notation.

### 15. Parity, transpositions & the alternating group

- **What it asks:** Determine whether a permutation is even or odd, compute its sign, or apply a fact about \(A_n\).
- **Solve approach:** The sign is \((-1)^{(\text{number of transpositions})}\); a \(k\)-cycle is even iff \(k\) is odd (it needs \(k-1\) transpositions). Sign is multiplicative (\(\operatorname{sgn}\) is a homomorphism), and \(A_n\) — the even permutations — is a normal subgroup of index 2 with \(|A_n|=n!/2\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Is the permutation \((1\,2\,3\,4\,5)(6\,7)\) even or odd?

---

## Classifying small groups & recognizing (non)group structures

### 16. Classifying groups of small order

- **What it asks:** Identify all groups of a given small order up to isomorphism, or state the possible structures.
- **Solve approach:** Use the standard facts: order \(p\) (prime) \(\Rightarrow\) cyclic \(\mathbb{Z}_p\); order \(p^2\Rightarrow\) abelian (\(\mathbb{Z}_{p^2}\) or \(\mathbb{Z}_p\times\mathbb{Z}_p\)); order \(2p\Rightarrow\) cyclic \(\mathbb{Z}_{2p}\) or dihedral \(D_p\); and the smallest nonabelian group is \(S_3\cong D_3\) of order 6. Distinguish candidates by their element-order counts.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Up to isomorphism, how many groups of order 6 are there, and what are they?

### 17. Direct products & finite abelian group classification

- **What it asks:** Use the structure theorem to count or identify the abelian groups of a given order, or to simplify a direct product.
- **Solve approach:** Every finite abelian group is a product of cyclic groups of prime-power order; the number of abelian groups of order \(n\) is the product, over the prime powers \(p^{a}\) exactly dividing \(n\), of the partition counts \(p(a)\). Use \(\mathbb{Z}_m\times\mathbb{Z}_n\cong\mathbb{Z}_{mn}\) when \(\gcd(m,n)=1\) (CRT) to merge or split factors.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many abelian groups of order 72 are there up to isomorphism?

### 18. Recognizing (non)group structures / which axiom fails

- **What it asks:** Decide whether a given set with an operation is a group (which of several is / is not), or identify which axiom fails.
- **Solve approach:** Check the four axioms — closure, associativity, identity, inverses. Common failures: missing inverses (all integers under \(\times\); nonzero integers under \(\times\)), not closed (odd integers under \(+\)), a non-associative operation, or no identity. For reference, \(\{\pm1\}\) and the nonzero rationals are groups under \(\times\), while \(\mathbb{Z},\mathbb{Q},\mathbb{R}\) are groups under \(+\).
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Under ordinary multiplication, which of these is a group: the nonzero integers, the nonzero rationals, or all integers?

### 19. General group-property assertions ("which must be true")

- **What it asks:** A true/false or "which of I, II, III must hold" item about general properties of groups.
- **Solve approach:** Apply core theorems and keep standard counterexamples ready: a subgroup of an abelian group is abelian and a subgroup of a cyclic group is cyclic (true); every group of even order has an element of order 2 (true); if \(x^2=e\) for all \(x\) then \(G\) is abelian (true); but "any two groups of the same order are isomorphic" is false (\(\mathbb{Z}_4\) vs \(\mathbb{Z}_2\times\mathbb{Z}_2\)). Nonabelian counterexamples usually come from \(S_3\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Which must be true for every finite group \(G\): (I) the order of each element divides \(|G|\); (II) \(G\) is abelian; (III) if \(|G|\) is even, \(G\) has an element of order 2?
