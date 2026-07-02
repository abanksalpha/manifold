# Rings & fields — GRE problem types

Scope: the abstract-algebra questions on the GRE Mathematics Subject Test that concern **rings and fields** — ideals and homomorphisms, integral domains/units, zero divisors/nilpotents/idempotents, polynomial irreducibility, characteristic, and the structure of `Z/nZ` and finite fields. Group theory is a _separate_ topic and is excluded here; pure modular arithmetic / CRT lives in number theory and only appears below where it decides a ring-theoretic property.

> **Orientation & honesty notes.** Rings & fields is a smaller slice of the exam than group theory, and the items skew toward _recognition and one-line computation_ rather than proof (multiple choice, no calculator, ~2–3 min each). The genuinely recurring anchors are `Z/n` (units, zero divisors, "is it a field?"), the "order of a finite field is a prime power" fact, characteristic, and the "which of I/II/III is true" theorem screen; ideals and quotient rings appear but are rarer and harder. Difficulty is **GRE-relative**. Frequencies (common / occasional / rare) are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep — not counted statistics — and no specific question numbers are cited because they are not verifiable here.

---

## Rings, ideals & ring homomorphisms

### Ideal vs. subring recognition

- **What it asks:** Given a ring (usually `Z`, `Z[x]`, a polynomial ring, or `M_n(R)`) and several subsets, decide which is an ideal — or which is a subring that fails to be an ideal.
- **Solve approach:** Test the absorption property: an ideal must satisfy `r·a ∈ I` for _every_ `r` in the ring, not just closure under `+` and `×`. A subring can miss this (e.g. `Z ⊂ Q` is a subring but not an ideal). In `Z[x]`, "constant term `= 0`" is the ideal `(x)`; "even/odd degree" and "monic" fail closure.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Which of the following is an ideal of `Z[x]`? (the monic polynomials; the polynomials with constant term 0; the polynomials of even degree; …)"

### Quotient rings, prime & maximal ideals, and the `R/I` correspondence

- **What it asks:** Identify a quotient ring `R/I` (its size or a familiar isomorphic copy), or classify an ideal as prime and/or maximal.
- **Solve approach:** In a commutative ring with 1, `I` is **maximal ⇔ `R/I` is a field** and **prime ⇔ `R/I` is an integral domain**. Recognize the standard quotients: `R[x]/(x²+1) ≅ C`, `Z[x]/(x) ≅ Z`, `Z/(n)`. In `Z`, `(p)` is maximal, `(0)` is prime but not maximal, and `(4)` is neither (`Z/4` has zero divisors).
- **Difficulty:** medium–hard. **Frequency:** rare/occasional.
- **Example stem:** "In the ring `Z`, which ideal is prime but not maximal?" or "`R[x]/(x²+1)` is isomorphic to which field?"

### Ring homomorphisms: recognition, kernel/image, and counting

- **What it asks:** Decide which map is a ring homomorphism, use the fact that the kernel is an ideal / the image is a subring, or count the (unital) homomorphisms between two given rings.
- **Solve approach:** A ring hom preserves `+`, `×` (and `1`, on this exam). Check candidates fast: complex conjugation `C → C` and evaluation `R[x] → R`, `p ↦ p(a)` qualify; `x ↦ x²` does not (not additive). A unital hom out of `Z` is forced by `1 ↦ 1` (so exactly one `Z → Z`); a hom out of a **field** is injective (its kernel is an ideal of the field, hence `{0}` or everything).
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Which of the following is a ring homomorphism? (conjugation on `C`; `x ↦ x²` on `Z`; `n ↦ 2n` on `Z`; …)"

---

## Integral domains, fields of fractions & units

### Units of a ring (find or count)

- **What it asks:** Identify the invertible elements of a given ring, or count them.
- **Solve approach:** Match the ring to its unit group: units of `Z` are `±1`; units of `Z/n` are the residues coprime to `n` (so there are `φ(n)` of them); units of `Z[i]` are `±1, ±i`; in a field every nonzero element is a unit; in `R[x]` the units are the nonzero constants (units of `R`). Non-units that are also nonzero are exactly the zero divisors in a _finite_ commutative ring.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "How many units does the ring `Z/12` have?"

### Integral-domain ⇔ field logic (the hierarchy)

- **What it asks:** Test the implications among "commutative ring with 1," "integral domain," and "field," usually as a true/false or "which must hold" item.
- **Solve approach:** Keep the one-way chain straight: **every field is an integral domain** (fields have no zero divisors), but not conversely — `Z` is the standard counterexample. The one partial converse the exam loves: **a finite integral domain is a field**. Cancellation holds precisely in integral domains.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "Which is true? (every integral domain is a field; every field is an integral domain; a finite integral domain is a field)"

### Field of fractions recognition

- **What it asks:** Name the field of fractions of a given integral domain.
- **Solve approach:** `Frac(D)` is the smallest field containing `D`: `Frac(Z) = Q`, `Frac(F[x]) = F(x)` (rational functions), and the field of fractions of a field is itself. The construction requires `D` to be an integral domain in the first place.
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "The field of fractions of `Z[x]` is which field?"

---

## Zero divisors, nilpotents, idempotents

### Zero divisors (identify or count), especially in `Z/n`

- **What it asks:** Find the zero divisors of a ring, count them, or use "has no zero divisors" as the deciding property.
- **Solve approach:** A zero divisor is a nonzero `a` with `ab = 0` for some nonzero `b`. In `Z/n` the zero divisors are the nonzero residues sharing a factor with `n` (i.e. `gcd(a,n) > 1`), so the count is `n − φ(n) − 1`. Product rings always have them (`(1,0)(0,1) = 0`), as do matrix rings. `Z/n` has _no_ zero divisors iff `n` is prime.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "How many zero divisors are in `Z/12`?" or "Which elements of `Z/6` are zero divisors?"

### Nilpotent and idempotent elements

- **What it asks:** Find (or count) the elements with `a^k = 0` (nilpotent) or `a² = a` (idempotent) in a given ring, most often `Z/n` or a matrix ring.
- **Solve approach:** In `Z/n`, nilpotents are the multiples of the radical `rad(n)` (the product of the distinct primes dividing `n`), giving `n / rad(n)` of them; idempotents number `2^(k)` where `k` is the count of distinct prime factors (by CRT). In matrix rings, nilpotents are the matrices with all eigenvalues 0 and idempotents are the projections.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The nilpotent elements of `Z/8` are which set?" or "How many idempotents does `Z/6` have?"

---

## Fields & polynomial irreducibility

### Polynomial irreducibility test

- **What it asks:** Decide whether a given polynomial is irreducible over `Q`, `R`, `C`, or a finite field (or count its roots / factors there).
- **Solve approach:** Choose the tool for the field: **Eisenstein's criterion** and the **rational root theorem** for `Q`; over any field a degree-2-or-3 polynomial is irreducible **iff it has no root** in that field; over `C` everything factors into linears, over `R` into linears and irreducible quadratics. Beware that irreducibility is field-dependent — e.g. `x²+1` is irreducible over `R` and `F_3` but factors over `C` and over `F_5`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Is `x³ − 3x + 3` irreducible over `Q`?" (Eisenstein at `p = 3`.)

### Building a field as `F[x]/(f)`

- **What it asks:** Recognize that quotienting a polynomial ring by an irreducible polynomial produces a field, and give (or use) its size.
- **Solve approach:** `F_p[x]/(f)` is a field **iff `f` is irreducible** over `F_p`, and it then has `p^(deg f)` elements. So constructing a field of order `p^n` means finding an irreducible `f` of degree `n`; a reducible modulus instead yields zero divisors.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For which polynomial `f` is `F_2[x]/(f)` a field with 4 elements?"

---

## Characteristic of a ring

### Characteristic computation

- **What it asks:** Compute the characteristic of a given ring or field, or use the constraint that a field's characteristic is 0 or prime.
- **Solve approach:** The characteristic is the least `n > 0` with `n·1 = 0` (else 0): `char(Z/n) = n`, `char(Z) = char(Q) = char(R) = char(C) = 0`, and `char(R × S) = lcm(char R, char S)`. A **field's characteristic is 0 or a prime**, and a finite field of order `p^n` has characteristic `p`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The characteristic of the ring `Z/4 × Z/6` is …"

---

## Finite fields & `Z/nZ` structure

### `Z/n` is a field / integral domain ⇔ `n` is prime

- **What it asks:** Determine for which `n` the ring `Z/n` is a field (equivalently, an integral domain), or pick the field out of a list of `Z/n`.
- **Solve approach:** `Z/n` is a field ⇔ integral domain ⇔ **`n` is prime** (the two conditions coincide because `Z/n` is finite). For composite `n`, any proper factor gives a zero divisor.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "Which of `Z/4`, `Z/6`, `Z/7`, `Z/9` is a field?"

### Order of a finite field must be a prime power

- **What it asks:** Decide which numbers can be the number of elements of a finite field, or reason from a field's given size.
- **Solve approach:** A finite field has exactly `p^n` elements for a prime `p` and `n ≥ 1`, and for each prime power there is one such field up to isomorphism. So a proposed order works iff it is a prime power — `6, 10, 12, 15` cannot occur; `4, 8, 9, 25, 27` can.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "Which of the following cannot be the number of elements of a field? (9, 15, 25, 27)"

### Multiplicative structure of a finite field

- **What it asks:** Use the fact that the nonzero elements of a finite field form a cyclic group — count solutions of `x^k = 1`, generators, or elements of a given order.
- **Solve approach:** For a field of order `q`, the group `F_q^×` is cyclic of order `q − 1`; hence `x^k = 1` has exactly `gcd(k, q−1)` solutions, the number of generators is `φ(q−1)`, and every element satisfies `x^q = x`. (The deeper cyclic-group counting itself belongs to the group-theory topic; here it is the field's structure that is tested.)
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "In the field with 16 elements, how many `x` satisfy `x³ = 1`?"

---

## Identifying ring/field axioms & counterexamples

### Classify the structure ("which of these is a field / ring / domain?")

- **What it asks:** From a list of concrete sets-with-operations, pick the one that is a field (or a ring, or an integral domain), i.e. spot which axiom the others miss.
- **Solve approach:** Screen against the usual failure modes: no multiplicative identity (`2Z`), missing inverses (`Z` is not a field), zero divisors (`Z/6`, `M_n`), non-commutativity (`M_n`), or not closed under an operation. `Q`, `R`, `C`, and `Z/p` are the go-to fields.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "Which of the following is a field? (`Z`, `2Z`, `Z/8`, `Q`)"

### Theorem screen & counterexamples (the "I / II / III" format)

- **What it asks:** Given several general statements about rings, integral domains, or fields, select which are true — the exam's signature multi-statement format, where the wrong options are baited with near-true claims.
- **Solve approach:** Keep the standard counterexamples loaded: "every integral domain is a field" is **false** (`Z`); "`Z/p` is a field for every integer `p > 1`" is **false** (needs `p` prime); "the characteristic of an integral domain is 0 or prime" is **true**; "a finite integral domain is a field" is **true**. Evaluate each numbered statement independently, then match the answer set.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "Which are true? I. Every finite integral domain is a field. II. Every integral domain is a field. III. `Z/n` is a field for every integer `n > 1`."
