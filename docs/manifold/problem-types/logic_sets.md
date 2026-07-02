# Logic, sets & relations — GRE problem types

Scope: recognition-level **discrete-foundations** patterns on the GRE Mathematics Subject Test — the "logic, set theory, relations & functions" corner of the ~25% additional-topics strand — grouped by sub-skill: propositional logic & quantifiers; set operations, Venn diagrams & cardinality; relations; functions; proof by induction; and the validity of statements about functions/sets.

> **Orientation & honesty notes.** This is a thin, "recognize"-tier slice: the ETS outline lists "logic, set theory, combinatorics, graph theory, and algorithms" together under Discrete Mathematics, so only a handful of logic/sets items appear on any one form and most types below are **occasional** or **rare** — "common" here means a reliable member of this small pool, not frequent across the whole test. Difficulty and frequency are **topic-relative qualitative judgments** drawn from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep — not counted statistics — and no specific question numbers are cited because they are not verifiable here. Two real conventions apply: **no calculator** (sets/relations are kept small enough to enumerate by hand) and the frequent **"which of I, II, III must be true"** answer format, which dominates the validity/identity types. Where a pattern overlaps a neighboring topic (pure counting of functions, inclusion–exclusion over divisibility, diagonalization proofs), it is kept brief and cross-referenced rather than duplicated here.

---

## Propositional logic, quantifiers & conditionals

### 1. Negating a quantified statement

- **What it asks:** Choose the correct negation of a statement built from quantifiers, often mixing ∀ and ∃ (frequently phrased in words: "every," "some," "no," "there exists").
- **Solve approach:** Push the negation inward, flipping each quantifier (∀↔∃) and negating the inner predicate; "for all x, P(x) → Q(x)" negates to "there exists x with P(x) and not Q(x)." Remember the negation of "all A are B" is "some A is not B" (not "no A is B").
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** What is the negation of "For every real number x there exists an integer n with n > x"?

### 2. Contrapositive, converse & inverse

- **What it asks:** Given a conditional "if P then Q," identify its contrapositive/converse/inverse, or select the choice logically equivalent to it.
- **Solve approach:** Only the contrapositive (not Q → not P) is equivalent to the original; the converse (Q → P) and the inverse (not P → not Q) are equivalent to each other but not to the original. First rewrite "P only if Q" as P → Q and "P if Q" as Q → P before comparing.
- **Difficulty:** easy · **Frequency:** occasional
- **Example stem:** Which statement is logically equivalent to "If a function is differentiable, then it is continuous"?

### 3. Equivalence of compound statements (truth tables)

- **What it asks:** Decide which compound proposition is logically equivalent to a given one, or which listed statements are mutually equivalent.
- **Solve approach:** Rewrite implications as P → Q ≡ (not P) ∨ Q, apply De Morgan (not (P ∧ Q) ≡ not P ∨ not Q) and distributivity, or just build a small truth table (≤ 3 variables → ≤ 8 rows). Two statements are equivalent iff their final columns match.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Which of the following is logically equivalent to "not (P and not Q)"?

### 4. Tautology / contradiction recognition

- **What it asks:** Determine whether a compound statement is always true (tautology), always false (contradiction), or contingent — or pick the choice that is a tautology.
- **Solve approach:** Test every truth assignment, or reason structurally (P ∨ not P is always true; (P → Q) ∧ P ∧ not Q is always false). For "which is a tautology," look for the choice whose truth-table column is all true.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Which of the following compound statements is a tautology?

### 5. Valid vs. invalid deduction

- **What it asks:** Given premises, decide which conclusion necessarily follows, or whether a stated argument is valid — classic syllogism / "which must be true" reasoning.
- **Solve approach:** Apply the valid forms — modus ponens (P → Q, P ⊢ Q), modus tollens (P → Q, not Q ⊢ not P), and chaining (P → Q, Q → R ⊢ P → R) — and reject the fallacies of affirming the consequent and denying the antecedent. A single truth assignment that satisfies the premises but not the conclusion proves invalidity.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Given "all squares are rectangles" and "some rectangles are not rhombi," which of the following must be true?

---

## Set operations, Venn diagrams & cardinality

### 6. Venn-diagram region cardinality (two or three sets)

- **What it asks:** From partial counts of overlapping sets (a survey-style word problem, or given |A|, |B|, |A ∪ B|), find a missing region count such as |A ∩ B|, "exactly one of," or "neither."
- **Solve approach:** Inclusion–exclusion: |A ∪ B| = |A| + |B| − |A ∩ B|; for three sets add back |A ∩ B ∩ C|. Fill the Venn diagram from the innermost overlap outward so each region is counted exactly once, then read off the requested piece. (The divisibility / "at least one property" flavor of inclusion–exclusion is covered under combinatorics.)
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Of 30 students, 18 take French and 15 take Spanish, and 5 take both. How many take neither?

### 7. Set-algebra identities & simplification

- **What it asks:** Simplify a set expression, or decide which proposed set identity holds for all sets — De Morgan, distributive, difference, symmetric difference, complement.
- **Solve approach:** Use the set laws that mirror logic: (A ∪ B)ᶜ = Aᶜ ∩ Bᶜ, A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C), and A ∖ B = A ∩ Bᶜ. To disprove a candidate identity, chase element membership or produce a tiny counterexample; a Venn diagram confirms when two expressions coincide.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** For all sets A and B, which of the following equals A ∖ (A ∖ B)?

### 8. Cardinality recognition (power sets, countability)

- **What it asks:** Recognize a cardinality fact — the number of subsets of a finite set, or whether a given set is finite, countably infinite, or uncountable.
- **Solve approach:** A set with n elements has 2ⁿ subsets. For infinite sets, recall that ℤ, ℚ, finite products, and countable unions of countable sets are countable, whereas ℝ, any nondegenerate interval, and the power set of ℕ are uncountable. (The diagonal-argument _proof_ of uncountability is an analysis-topic concern; here it is pure recognition.)
- **Difficulty:** easy (finite) / medium (countability) · **Frequency:** occasional
- **Example stem:** Which of the following is uncountable: the integers, the rationals, the finite-length binary strings, or the set of all infinite binary sequences?

---

## Relations (order & equivalence)

### 9. Testing relation properties

- **What it asks:** Given a relation — by a rule on numbers, by an explicit set of ordered pairs, or by description — decide which of reflexive / symmetric / antisymmetric / transitive it satisfies.
- **Solve approach:** Check each property against its definition on the stated set: reflexive (a R a for all a), symmetric (a R b ⇒ b R a), antisymmetric (a R b and b R a ⇒ a = b), transitive (a R b and b R c ⇒ a R c). A single counterexample removes a property; mind the small-set and empty-relation edge cases.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** On the integers, the relation a ~ b defined by "a − b is even" is which of reflexive, symmetric, and transitive?

### 10. Equivalence relations ↔ partitions

- **What it asks:** Decide whether a relation is an equivalence relation, describe its equivalence classes, or count the equivalence relations (partitions) of a small set.
- **Solve approach:** Equivalence relation ⇔ reflexive + symmetric + transitive ⇔ its classes partition the set. The number of equivalence relations on an n-element set equals the number of partitions (Bell numbers: B₁, B₂, B₃, B₄ = 1, 2, 5, 15). Congruence mod m is the archetype, with the residue classes as its equivalence classes.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many distinct equivalence relations can be defined on a 3-element set?

### 11. Partial orders & Hasse diagrams

- **What it asks:** Recognize a partial order, read a Hasse diagram, or find maximal/minimal elements, comparability, or whether an order is total.
- **Solve approach:** Partial order ⇔ reflexive + antisymmetric + transitive; "divides" on the positive integers and ⊆ on subsets are the standard models. A total (linear) order additionally requires every pair to be comparable. Distinguish maximal from maximum: an element can be maximal (nothing strictly above it) without being the greatest.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Under divisibility on the set {2, 3, 4, 6, 9}, which elements are maximal?

---

## Functions (injective/surjective, counting, composition)

### 12. Deciding injective / surjective / bijective

- **What it asks:** For a given function — formula, arrow diagram, or map between finite sets — decide whether it is one-to-one, onto, or a bijection, sometimes contingent on the stated domain/codomain.
- **Solve approach:** Injective: f(x) = f(y) ⇒ x = y (each value hit at most once); surjective: every codomain element is attained (this depends on the _stated_ codomain); bijective: both. For two finite sets of equal size, injective ⇔ surjective ⇔ bijective. Restricting the domain can make a non-injective map injective.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** Is f: ℤ → ℤ defined by f(n) = 2n injective? Is it surjective?

### 13. Counting maps between finite sets

- **What it asks:** Count the functions, injections, or bijections from one finite set to another.
- **Solve approach:** Functions from an m-set to an n-set: nᵐ (n choices for each of the m inputs). Injections: n(n − 1)···(n − m + 1) (falling factorial), and 0 when m > n. Bijections of an n-set: n!. An injection A → B exists iff |A| ≤ |B|, a surjection iff |A| ≥ |B|. (Counting _surjections_ via inclusion–exclusion is treated under combinatorics.)
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many one-to-one functions are there from a 3-element set into a 5-element set?

### 14. Composition & inverse: which properties survive

- **What it asks:** Decide which properties are preserved under composition or inversion — "if f and g are injective, is g∘f injective?" or "if g∘f is injective, what follows about f?"
- **Solve approach:** Injective ∘ injective is injective and surjective ∘ surjective is surjective; conversely, if g∘f is injective then the inner map f is injective, and if g∘f is surjective then the outer map g is surjective. A function is invertible iff it is a bijection; find inverses by solving y = f(x) for x.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** If f: A → B and g: B → C are functions and g∘f is injective, which of the following must be true?

---

## Proof by induction

### 15. Structure of an induction proof (base case & inductive step)

- **What it asks:** Identify the correct base case, the correct inductive hypothesis/step, or what remains to be shown to complete a proof by mathematical induction — occasionally, which statement is best proved by induction.
- **Solve approach:** Recognize the template: verify the base case (usually n = 0 or 1), assume the claim for n = k, and derive it for n = k + 1. Spot a flawed argument by checking whether the step actually invokes the hypothesis and whether the base case matches the claim's starting index. (Free-response proofs never appear on this exam; you only recognize or verify a step in multiple choice.)
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** In proving that 1 + 2 + ··· + n = n(n + 1)/2 by induction, what must be established in the inductive step?

---

## Validity of logical statements about functions & sets

### 16. Image & preimage identities

- **What it asks:** Decide which set identity involving a function's image f(·) or preimage f⁻¹(·) holds for _every_ function — typically a "which of I, II, III" question.
- **Solve approach:** Preimages commute with everything: f⁻¹(C ∪ D) = f⁻¹(C) ∪ f⁻¹(D), f⁻¹(C ∩ D) = f⁻¹(C) ∩ f⁻¹(D), f⁻¹(Cᶜ) = f⁻¹(C)ᶜ. Images are weaker: f(A ∪ B) = f(A) ∪ f(B) always, but only f(A ∩ B) ⊆ f(A) ∩ f(B) in general (equality requires injectivity). Kill wrong choices with a two-points-collide example.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** For f: X → Y, which must hold for all f: I. f(A ∩ B) = f(A) ∩ f(B) for A, B ⊆ X; II. f⁻¹(C ∪ D) = f⁻¹(C) ∪ f⁻¹(D) for C, D ⊆ Y?

### 17. Closure & counterexample questions

- **What it asks:** Decide whether a property is preserved under an operation — is the union/intersection of two equivalence relations again an equivalence relation? which "must be true" statement about sets or relations actually survives?
- **Solve approach:** The exam rewards a fast counterexample on a 2- or 3-element set. Standard facts: the intersection of two equivalence relations is again an equivalence relation, but their union generally is not (transitivity fails); the intersection of transitive relations is transitive; the complement of an equivalence relation is not one. Test each candidate on the smallest set that could break it.
- **Difficulty:** medium–hard · **Frequency:** rare
- **Example stem:** If R and S are equivalence relations on a set, which of R ∩ S and R ∪ S must also be an equivalence relation?
