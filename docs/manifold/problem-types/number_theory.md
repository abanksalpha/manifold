# Number theory — GRE problem types

Scope: elementary number-theory patterns on the GRE Mathematics Subject Test, limited to divisibility & the Euclidean algorithm, modular arithmetic & congruences, Fermat's little theorem / Euler's theorem, the Chinese remainder theorem, prime factorization / gcd / lcm, and counting divisors; the group-theoretic structure of `Z/nZ` and its unit group belongs to the abstract-algebra topics and is handled elsewhere. Number theory is a small slice of this exam, so difficulty is **GRE-relative** and **frequency labels are relative to the exam's number-theory items** (not the whole test); the no-calculator design keeps every target number clean, and no specific question numbers or counts are cited because they are not verifiable here.

---

## Divisibility & the Euclidean algorithm

### Fixed integer that always divides an expression

- **What it asks:** Given an integer-valued expression in `n` (a product of consecutive integers or a polynomial like `n³ − n`), find the largest integer that divides it for _every_ positive integer `n`, or decide which listed divisors always work.
- **Solve approach:** Factor into consecutive integers (`n³ − n = (n−1)n(n+1)`): among `k` consecutive integers one is divisible by `k`, so `k` consecutive integers are divisible by `k!`. Confirm prime-power factors separately (parity, mod 3, etc.) and pin the answer with one or two small test values of `n`.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "What is the largest integer that divides `n³ − n` for every positive integer `n`?"

### GCD via the Euclidean algorithm (and Bézout combination)

- **What it asks:** Compute `gcd(a, b)` for two specific integers, or express that gcd as an integer combination `ax + by`.
- **Solve approach:** Apply repeated division `gcd(a, b) = gcd(b, a mod b)` until the remainder is 0; the last nonzero remainder is the gcd. For a Bézout combination, back-substitute the successive remainder equations to write the gcd in terms of the originals.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "Using the Euclidean algorithm, `gcd(252, 198)` = …"

### Solvability of a linear Diophantine equation

- **What it asks:** Decide whether `ax + by = c` has integer solutions (or for which constant `c` it does), sometimes as a coin/word-problem framing.
- **Solve approach:** `ax + by = c` has integer solutions **iff** `gcd(a, b)` divides `c`; recognize this divisibility test rather than searching. When solutions exist they form the family `x₀ + (b/g)t`, `y₀ − (a/g)t`.
- **Difficulty:** medium. **Frequency:** rare–occasional.
- **Example stem:** "For which of the following values of `c` does `6x + 10y = c` have a solution in integers `x, y`?"

---

## Modular arithmetic & congruences

### Units digit of a large power

- **What it asks:** Find the last (units) digit of a large power such as `3^{1001}` or `7^{2026}`.
- **Solve approach:** The units digit is the value mod 10, which cycles with period 1, 2, or 4; list the short cycle of last digits and reduce the exponent modulo the cycle length to index into it.
- **Difficulty:** easy. **Frequency:** common.
- **Example stem:** "What is the units digit of `3^{1001}`?"

### Remainder of a large power (find the cycle length)

- **What it asks:** Find the remainder when a large power `a^k` is divided by a small modulus `m`.
- **Solve approach:** Compute successive powers of `a` mod `m` until they repeat, find the multiplicative order `d` (the cycle length), then reduce the exponent `k mod d`. Reducing the base mod `m` first keeps the arithmetic tiny.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "What is the remainder when `2^{50}` is divided by 7?"

### Last two digits of a large power (mod 100)

- **What it asks:** Find the last two digits of a large power, i.e. its value mod 100.
- **Solve approach:** Work mod 100 (or split into mod 4 and mod 25 and recombine); find the order of the base mod 100 by repeated squaring, or apply Euler's theorem with `φ(100) = 40`, then reduce the exponent. Successive squaring keeps intermediate products two-digit.
- **Difficulty:** hard. **Frequency:** rare.
- **Example stem:** "What are the last two digits of `7^{2026}`?"

### Solve a linear congruence / find a modular inverse

- **What it asks:** Find the least positive solution of `ax ≡ b (mod m)`, or the inverse of an element mod `m`.
- **Solve approach:** When `gcd(a, m) = 1`, multiply both sides by the inverse of `a` (found by inspection on the small clean moduli this exam uses, or by the extended Euclidean algorithm). If `gcd(a, m) = g > 1`, a solution exists only when `g | b`, and then there are `g` solutions mod `m`.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "What is the least positive integer `x` with `5x ≡ 3 (mod 11)`?"

### Use residues to rule out or classify (squares mod n, parity)

- **What it asks:** Show an equation has no integer solutions, or classify which integers are representable, by looking at residues — typically using that squares are limited mod 3, 4, or 8.
- **Solve approach:** Reduce the whole equation modulo a well-chosen small number and use the restricted residue set (a square is `0` or `1` mod 3 and mod 4; `0, 1, 4` mod 8) to reach a contradiction or to count cases. Choose the modulus that most tightly constrains the offending term.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "For how many pairs of integers `(x, y)` is `x² − 3y² = 2`?"

---

## Fermat's little theorem / Euler's theorem

### Reduce a prime-modulus power with Fermat's little theorem

- **What it asks:** Evaluate `a^k mod p` for a prime `p`, often with a large exponent, or recognize the value of `a^{p−1}` or `a^{p}` mod `p`.
- **Solve approach:** For prime `p` with `p ∤ a`, Fermat gives `a^{p−1} ≡ 1 (mod p)`, so reduce the exponent modulo `p − 1`; also `a^{p} ≡ a (mod p)` for every `a`. Then finish with a small residual power.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "What is the remainder when `3^{100}` is divided by 101?"

### Reduce a composite-modulus power with Euler's theorem

- **What it asks:** Evaluate `a^k mod m` for a composite modulus `m` with `gcd(a, m) = 1`, using Euler's totient.
- **Solve approach:** Compute `φ(m)` from the factorization via `φ(∏ pᵢ^{eᵢ}) = ∏ pᵢ^{eᵢ−1}(pᵢ − 1)`; since `a^{φ(m)} ≡ 1 (mod m)`, reduce the exponent modulo `φ(m)` and evaluate the small remaining power. (Requires `gcd(a, m) = 1`.)
- **Difficulty:** medium–hard. **Frequency:** rare–occasional.
- **Example stem:** "What is the remainder when `2^{1000}` is divided by 21?"

---

## Chinese remainder theorem

### Smallest integer satisfying simultaneous remainder conditions

- **What it asks:** Find the smallest positive integer (or the general form) leaving prescribed remainders under several pairwise-coprime moduli, sometimes framed as a counting/word problem.
- **Solve approach:** Solve the congruences two at a time by substitution (write `x = m₁k + r₁`, force it into the next congruence, solve for `k`); with coprime moduli the CRT guarantees a unique solution mod the product `∏ mᵢ`. On this exam checking the answer choices against each condition is often fastest.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "What is the smallest positive integer that leaves remainder 1 when divided by 3, remainder 2 when divided by 5, and remainder 3 when divided by 7?"

---

## Prime factorization, gcd & lcm

### The gcd · lcm = product relation

- **What it asks:** Given three of the four quantities among two numbers, their gcd, and their lcm, find the missing one — or combine gcd/lcm facts about `a` and `b`.
- **Solve approach:** Use `gcd(a, b) · lcm(a, b) = a · b`. Alternatively read gcd/lcm off the prime factorizations (gcd takes the min exponent of each prime, lcm the max).
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "If `gcd(a, b) = 6`, `lcm(a, b) = 72`, and `a = 24`, then `b` = …"

### Highest power of a prime dividing a factorial (Legendre) / trailing zeros

- **What it asks:** Find how many trailing zeros `n!` has, or the largest exponent `k` with `p^k | n!`.
- **Solve approach:** Legendre's formula sums the quotients `⌊n/p⌋ + ⌊n/p²⌋ + ⌊n/p³⌋ + …`. Trailing zeros of `n!` are governed by the number of factors of 5 (fives are scarcer than twos), so count powers of 5.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "How many consecutive zeros does `100!` end in?"

---

## Counting divisors

### Number of positive divisors from the factorization

- **What it asks:** Count the positive divisors of a given integer (or of a number presented in factored form).
- **Solve approach:** Factor into primes `N = ∏ pᵢ^{eᵢ}`; the number of positive divisors is `∏ (eᵢ + 1)`, since each prime's exponent is chosen independently from `0` to `eᵢ`.
- **Difficulty:** easy–medium. **Frequency:** common.
- **Example stem:** "How many positive divisors does 360 have?"

### Sum of the divisors from the factorization

- **What it asks:** Compute the sum of all positive divisors of an integer (or recognize the multiplicative divisor-sum function).
- **Solve approach:** For `N = ∏ pᵢ^{eᵢ}`, the divisor sum factors as `∏ (pᵢ^{eᵢ+1} − 1)/(pᵢ − 1)` (each factor is the geometric series `1 + pᵢ + … + pᵢ^{eᵢ}`); for a small number, list and add the divisors directly.
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "What is the sum of all the positive divisors of 12?"
