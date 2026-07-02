# Combinatorics — GRE problem types

Scope: recurring **pure-counting** patterns on the GRE Mathematics Subject Test, organized by the seven boundary sub-skills below. Neighboring topics are handled by other agents and excluded here — in particular **probability, expected value, and random-variable questions are separate** (these items count outcomes, they do not assign or compute probabilities); number-theoretic counting proper and generating-function machinery also live elsewhere.

> **Honesty & orientation.** Combinatorics is an _additional-topics_, "recognize"-tier slice — a small number of standalone counting questions per form, so most types below are **occasional** or **rare** and only the basic permutation/combination/binomial patterns are **common**. Difficulty is **GRE-relative**. The **no-calculator** rule keeps every count small enough to evaluate by hand (compute \(\binom{n}{k}\) by cancellation, never full factorials). Frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep — not counted statistics — and no specific question numbers are cited because they are not verifiable here. (Plain binomial-_expansion_ coefficient extraction is shared with the elementary-algebra topic; here the emphasis is the counting/identity angle.)

---

## Permutations & combinations

### 1. Multiplication principle (staged choices)

- **What it asks:** Count the outcomes of a process built from successive independent choices — codes/plates, seatings, meal combinations, "how many numbers with property X" — where each stage has a fixed number of options.
- **Solve approach:** Multiply the options available at each stage. Watch whether repetition is allowed (with repetition each stage is independent; without repetition the pool shrinks each step). For "at least one" or a single forbidden pattern, count the complement and subtract.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** How many 3-digit numbers have all distinct digits (leading digit nonzero)?

### 2. Permutations of distinct objects (arrangements, \(nP_r\))

- **What it asks:** Count ordered arrangements of all \(n\) distinct objects, or of \(r\) chosen from \(n\) when order matters (e.g., filling ranked offices).
- **Solve approach:** All objects: \(n!\). Ordered \(r\) of \(n\): \(\dfrac{n!}{(n-r)!}=n(n-1)\cdots(n-r+1)\). The tell is that rearranging the same items gives a _different_ outcome.
- **Difficulty:** easy · **Frequency:** common
- **Example stem:** In how many ways can a president, vice-president, and treasurer be chosen from 8 distinct people?

### 3. Combinations / selections (\(\binom{n}{k}\))

- **What it asks:** Count unordered selections of \(k\) from \(n\), possibly split across categories or with certain members forced in or out.
- **Solve approach:** \(\binom{n}{k}=\dfrac{n!}{k!\,(n-k)!}\), evaluated by cancellation; use \(\binom{n}{k}=\binom{n}{n-k}\). Forced-in \(m\) members: choose the rest as \(\binom{n-m}{k-m}\). Category splits multiply the per-category combinations (e.g., "exactly 2 of type A").
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** From 6 men and 4 women, how many 4-person committees contain exactly 2 women?

### 4. Permutations with identical objects (multiset arrangements)

- **What it asks:** Count the distinguishable arrangements of a collection containing repeated identical items — the classic "arrangements of the letters of a word."
- **Solve approach:** \(\dfrac{n!}{n_1!\,n_2!\cdots n_k!}\), dividing the total \(n!\) by the factorial of each repeated group's multiplicity to quotient out indistinguishable swaps.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many distinct arrangements are there of the letters in the word BANANA?

### 5. Circular arrangements

- **What it asks:** Count arrangements of \(n\) objects around a circle / round table, where rotations (and sometimes reflections) are considered the same.
- **Solve approach:** Fix one object to remove rotational symmetry, giving \((n-1)!\). If reflections also count as identical (a flippable bracelet/necklace), divide by 2 for \(\dfrac{(n-1)!}{2}\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** In how many ways can 6 people be seated around a round table if seatings differing only by a rotation are considered the same?

### 6. Arrangements with adjacency / separation restrictions

- **What it asks:** Count linear arrangements in which specified items must stay together, must **not** be adjacent, or must keep a fixed relative order.
- **Solve approach:** _Together:_ glue the block into one unit, arrange the units, then multiply by the block's internal arrangements. _Not adjacent:_ arrange the unrestricted items first, then drop the restricted ones into the gaps between/around them. _Fixed relative order of \(r\) items:_ divide the total by \(r!\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** In how many arrangements of the letters of PENCIL are the two vowels never next to each other?

---

## Stars-and-bars / distributing objects

### 7. Nonnegative integer solutions (stars and bars)

- **What it asks:** Count solutions in nonnegative integers to \(x_1+x_2+\cdots+x_k=n\), equivalently the ways to distribute \(n\) **identical** objects among \(k\) **distinct** recipients.
- **Solve approach:** Stars and bars: arrange \(n\) stars and \(k-1\) bars, giving \(\binom{n+k-1}{\,k-1\,}\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many solutions in nonnegative integers does \(x+y+z=10\) have?

### 8. Distributing with lower/upper bounds (constrained stars and bars)

- **What it asks:** The same identical-object distribution, but each recipient must receive at least a stated minimum (often at least one), or is subject to a cap.
- **Solve approach:** Substitute \(y_i=x_i-m_i\) to turn "\(x_i\ge m_i\)" into "\(y_i\ge 0\)," then apply stars and bars; "each \(\ge 1\)" across \(k\) parts gives \(\binom{n-1}{\,k-1\,}\). Enforce upper bounds by subtracting the over-cap cases via inclusion–exclusion.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** In how many ways can 12 identical candies be handed to 4 children so that every child gets at least one?

---

## Inclusion–exclusion

### 9. Union / "at least one" counting (including divisibility)

- **What it asks:** Count elements possessing at least one of several properties, i.e. the size of a union of overlapping sets; a frequent instance counts integers in a range divisible by at least one of several numbers.
- **Solve approach:** \(|A\cup B|=|A|+|B|-|A\cap B|\); for three sets add back the triple overlap. For divisibility, \(\#\{\le N:\,d\mid n\}=\lfloor N/d\rfloor\) and intersections use the lcm. Counting the complement ("none of the properties") is often faster.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** How many integers from 1 to 100 are divisible by 2 or by 3?

### 10. Derangements (nothing in its own place)

- **What it asks:** Count permutations of \(n\) items in which **no** item occupies its original position — the "misdelivered letters / mismatched hats" pattern.
- **Solve approach:** Inclusion–exclusion on the fixed-point events: \(D_n=n!\sum_{i=0}^{n}\dfrac{(-1)^i}{i!}\). For the small \(n\) the exam uses, just recall/compute \(D_2=1,\;D_3=2,\;D_4=9\).
- **Difficulty:** medium–hard · **Frequency:** rare
- **Example stem:** In how many ways can 4 letters be placed into 4 addressed envelopes so that no letter lands in its correct envelope?

### 11. Counting onto (surjective) functions

- **What it asks:** Count functions from one finite set **onto** another (every target value is hit) — equivalently, distributions of _distinct_ objects into distinct boxes leaving no box empty.
- **Solve approach:** Inclusion–exclusion over the missed targets: onto maps from an \(m\)-set to a \(k\)-set \(=\sum_{i=0}^{k}(-1)^i\binom{k}{i}(k-i)^m\). For tiny cases, subtract the non-onto functions directly from the total \(k^m\).
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** How many functions map a 4-element set onto a 3-element set?

---

## Pigeonhole principle

### 12. Pigeonhole guarantee (minimum to force a property)

- **What it asks:** Find the smallest number of items that **guarantees** some coincidence (two share a category, two have the same remainder, some pair sums to a target), or argue that such a coincidence must occur.
- **Solve approach:** Identify the "pigeonholes" (colors, residue classes, pairs). If more than \(k\cdot m\) objects fall into \(k\) holes, some hole holds more than \(m\); the guaranteed threshold is \(k\cdot m+1\). Worst-case reasoning ("what's the most you could pick while still failing?") pins the answer.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** A drawer holds socks of 3 colors. What is the least number you must pull to be certain of a matching pair?

---

## Recurrence relations

### 13. Counting via a recurrence

- **What it asks:** Count configurations obeying a local rule ("no two adjacent," tilings, step-climbing) by relating the size-\(n\) count to smaller cases, then evaluate a specific term (or identify the closed form).
- **Solve approach:** Build \(a_n\) from how a valid configuration of size \(n\) can end — e.g. binary strings with no two consecutive 1s, or \(1\times2\) tilings of a \(2\times n\) strip, both give \(a_n=a_{n-1}+a_{n-2}\) (Fibonacci). Iterate from base cases for a numeric answer, or solve the linear recurrence through its characteristic equation for a closed form.
- **Difficulty:** medium–hard · **Frequency:** occasional
- **Example stem:** How many binary strings of length 6 contain no two consecutive 1s?

---

## Binomial / multinomial coefficient identities

### 14. Binomial-coefficient identities and sums

- **What it asks:** Evaluate a sum of binomial coefficients, or simplify a coefficient expression, by recognizing a standard identity instead of expanding.
- **Solve approach:** Deploy the staples: \(\sum_{k}\binom{n}{k}=2^{n}\); the alternating sum \(\sum_k(-1)^k\binom{n}{k}=0\); symmetry \(\binom{n}{k}=\binom{n}{n-k}\); Pascal's rule \(\binom{n}{k}=\binom{n-1}{k-1}+\binom{n-1}{k}\); hockey-stick \(\sum_{i=r}^{n}\binom{i}{r}=\binom{n+1}{r+1}\); \(\sum_k\binom{n}{k}^2=\binom{2n}{n}\); \(\sum_k k\binom{n}{k}=n\,2^{\,n-1}\). Many drop out of substituting \(x=\pm1\) into \((1+x)^n\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Evaluate \(\binom{8}{0}+\binom{8}{1}+\cdots+\binom{8}{8}\).

### 15. Multinomial coefficient (labeled groups / trinomial term)

- **What it asks:** Count the ways to split \(n\) distinct objects into labeled groups of prescribed sizes, or find the coefficient of a specified monomial in \((x_1+\cdots+x_r)^n\).
- **Solve approach:** Use the multinomial coefficient \(\dfrac{n!}{n_1!\,n_2!\cdots n_r!}\) with \(\sum n_i=n\). In an expansion, the coefficient of the term with exponents \(n_1,\dots,n_r\) is exactly this coefficient (times any numeric factors carried on the variables).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** What is the coefficient of \(x^2y^2z^2\) in the expansion of \((x+y+z)^6\)?

---

## Counting via bijection

### 16. Lattice-path / grid-route counting

- **What it asks:** Count monotonic paths across a grid from one corner to the opposite corner using only unit right/up steps — equivalently, shortest routes through a rectangular street grid.
- **Solve approach:** A path using \(m\) right-steps and \(n\) up-steps is a length-\((m+n)\) sequence; choose which steps go up: \(\binom{m+n}{n}\). For a path forced through a checkpoint, multiply the counts of the two legs; exclude a forbidden point via the complement.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** How many shortest paths run from the bottom-left to the top-right corner of a \(4\times3\) grid of blocks?

### 17. Counting by bijection / combinatorial correspondence

- **What it asks:** Count a set by matching it one-to-one with a set of known size (subsets ↔ binary strings, selections ↔ paths), or recognize that two expressions count the same collection (a combinatorial-proof identity).
- **Solve approach:** Construct an explicit bijection to a standard object: subsets of an \(n\)-set ↔ length-\(n\) 0/1 strings \(\Rightarrow 2^n\); a selection problem ↔ an arrangement or a lattice path. To confirm an identity, argue both sides count one set two different ways.
- **Difficulty:** medium–hard · **Frequency:** rare
- **Example stem:** How many subsets does a 5-element set have, and why does that equal \(\sum_{k=0}^{5}\binom{5}{k}\)?
